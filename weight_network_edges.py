"""weight_network_edges.py

Sample the friction rasters along every final_network edge geometry and write per-(edge, month) weights.

The final_network topology is fixed (90,921 edges with real geometries), so
instead of raster-routing (least-cost cost-distance over the surface), friction
flows the other way: each edge's LineString is densified and the friction surface
is read at the sample points, giving a length-weighted mean friction per edge.

Edge type -> friction source -> rate mode (the central design table; see the
plan for rationale):

    Road      road_base.tif sampled           Road      months 1-12
    Join      road_base.tif sampled           Road      months 1-12
    IceRoad   road_base.tif x ICEROAD_TIME_PENALTY
                                              IceRoad   hard-gated to
                                                        ICE_ROAD_SEASON_MONTHS
    Waterway  barge_MM.tif sampled per month  Barge     passable iff no NoData
    Bridge    not sampled, friction 1.0       Road      months 1-12
    Air       not sampled, friction 1.0       Plane     months 1-12
    Transfer  not sampled, friction 1.0       Transfer  fees priced in Phase 3

TERMINOLOGY CAVEAT (2026-07-23): the colleague's `Bridge` type means an
mmnet topology WELD (gap-closing stitch, median ~112 m), not a physical
road-over-water bridge. Provenance (`source`) splits it: `weld:Road` /
`weld:to-giant` (1,331 edges) behave like the table row above, but
`weld:IceRoad` + `bridge:IceRoad->Road` (36 edges) belong to the ICE-ROAD
system and are re-typed here to IceRoad treatment (road_base sampled x
ICEROAD_TIME_PENALTY, IceRoad rate, hard-gated to ICE_ROAD_SEASON_MONTHS)
so they cannot provide phantom Apr-Dec connectivity into the ice-road
subnetwork. In this project "bridge" (unqualified) means the raster
burn-in concept: road pixels over water. Phase 1's load_final_network.py
should derive an `edge_class` column making the weld/bridge distinction
explicit.

road_base is NoData-free by construction (see friction_surface.compute_road_base)
so a land edge can never be accidentally severed; barge_MM keeps its NoData so
ice still blocks water edges.

Impassability rule: STRICT. Any NoData sample => the edge is impassable that
month (passable = FALSE). The length-weighted blocked fraction is logged per
edge (nodata_frac) so partial blockages are auditable.

edge_id is the 0-based row order of final_network/network_joined_edges.shp —
the same stable-id rule load_final_network.py (Phase 1) persists, so the
tables join cleanly once that lands.

Output table in fuel_network.duckdb:

    edge_month_weights(edge_id, month, mode, avg_friction, nodata_frac, passable)

90,921 edges x 12 months = 1,091,052 rows.

Friction-vs-cost separation: this module writes environmental multipliers
only. Every dollar (BASELINE_RATES_PER_GALLON_MILE, INTERMODAL_TRANSFER_FEES)
is applied downstream in Phase 3 — never here.

Usage:
    python weight_network_edges.py                 # full run, writes DuckDB
    python weight_network_edges.py --dry-run       # compute + QA, no write
    python weight_network_edges.py --months 2 7    # subset of months (smoke test)
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from shapely.geometry import LineString, MultiLineString

from friction_surface.friction_config import (
    FRICTION_NODATA,
    ICE_ROAD_SEASON_MONTHS,
    ICEROAD_TIME_PENALTY,
)
from friction_surface.friction_paths import FRICTION_OUTPUT_DIR

logger = logging.getLogger(__name__)

# Half a 150 m pixel — guarantees every traversed cell is hit at least once.
SAMPLE_SPACING_M = 75.0

EDGES_SHP = Path("final_network/network_joined_edges/network_joined_edges.shp")
DB_PATH = Path("fuel_network.duckdb")

# Edge type -> (sampling source, rate-mode key). Rate-mode keys match
# friction_costs.BASELINE_RATES_PER_GALLON_MILE so Phase 3's cost join is a
# straight lookup ("Transfer" is priced by INTERMODAL_TRANSFER_FEES instead).
EDGE_TYPE_MAP: dict[str, tuple[str | None, str]] = {
    "Road":     ("road_base", "Road"),
    "Join":     ("road_base", "Road"),
    "IceRoad":  ("road_base", "IceRoad"),
    "Waterway": ("barge",     "Barge"),
    "Bridge":   (None,        "Road"),
    "Air":      (None,        "Plane"),
    "Transfer": (None,        "Transfer"),
}


# ---------------------------------------------------------------------------
# Densification
# ---------------------------------------------------------------------------

def build_sample_arrays(
    geoms: Iterable[LineString | MultiLineString],
    owners: Iterable[int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Densify edge geometries into midpoint samples with segment lengths.

    Each geometry is segmentized at SAMPLE_SPACING_M (inserted vertices, so
    no segment exceeds 75 m and original vertices are preserved), then each
    resulting segment contributes its midpoint as the sample location and its
    length as the weight. MultiLineString parts are processed independently
    so no phantom segment spans the gap between parts.

    Args:
        geoms: edge geometries (EPSG:3338, meters).
        owners: the edge_id each geometry belongs to, parallel to geoms.

    Returns (xy, seg_len, owner):
        xy      (N, 2) float64 sample midpoints
        seg_len (N,)   float64 segment lengths in meters
        owner   (N,)   int64   edge_id per sample
    """
    xs, lens, own = [], [], []
    for edge_id, geom in zip(owners, geoms):
        if geom is None or geom.is_empty:
            continue
        parts = geom.geoms if isinstance(geom, MultiLineString) else (geom,)
        for part in parts:
            coords = np.asarray(part.segmentize(SAMPLE_SPACING_M).coords,
                                dtype=np.float64)[:, :2]
            if coords.shape[0] < 2:
                continue
            delta = np.diff(coords, axis=0)
            seg = np.hypot(delta[:, 0], delta[:, 1])
            keep = seg > 0.0
            if not keep.any():
                continue
            mid = (coords[:-1] + coords[1:]) / 2.0
            xs.append(mid[keep])
            lens.append(seg[keep])
            own.append(np.full(int(keep.sum()), edge_id, dtype=np.int64))
    if not xs:
        return (np.empty((0, 2)), np.empty(0), np.empty(0, dtype=np.int64))
    return np.concatenate(xs), np.concatenate(lens), np.concatenate(own)


# ---------------------------------------------------------------------------
# Raster sampling
# ---------------------------------------------------------------------------

def sample_raster(raster_path: str | Path, xy: np.ndarray) -> np.ndarray:
    """Read raster values at xy points (single full-band read + fancy index).

    Out-of-grid points and source-NoData/NaN pixels come back as
    FRICTION_NODATA so downstream aggregation has a single sentinel to
    test. The raster's own transform is used, so callers need not assume
    all rasters share a grid.
    """
    with rasterio.open(raster_path) as src:
        rows, cols = rasterio.transform.rowcol(src.transform, xy[:, 0], xy[:, 1])
        rows = np.asarray(rows, dtype=np.int64)
        cols = np.asarray(cols, dtype=np.int64)
        in_bounds = (
            (rows >= 0) & (rows < src.height) & (cols >= 0) & (cols < src.width)
        )
        band = src.read(1)
        src_nodata = src.nodata

    vals = np.full(xy.shape[0], FRICTION_NODATA, dtype=np.float32)
    vals[in_bounds] = band[rows[in_bounds], cols[in_bounds]]
    del band
    if src_nodata is not None:
        vals[vals == np.float32(src_nodata)] = FRICTION_NODATA
    vals[np.isnan(vals)] = FRICTION_NODATA
    return vals


def edge_weighted_stats(
    owner: np.ndarray,
    seg_len: np.ndarray,
    vals: np.ndarray,
    n_edges: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Length-weighted per-edge mean friction and NoData fraction.

    Returns (avg_friction, nodata_frac), each shape (n_edges,) float64.
    avg_friction is the mean over VALID samples only (NaN if an edge has
    none — including edges with no samples at all, whose nodata_frac is
    also set to 1.0 so the strict rule marks them impassable).
    """
    is_nd = vals == FRICTION_NODATA
    tot_len = np.bincount(owner, weights=seg_len, minlength=n_edges)
    nd_len = np.bincount(owner, weights=seg_len * is_nd, minlength=n_edges)
    valid_len = tot_len - nd_len
    fric_sum = np.bincount(
        owner, weights=seg_len * np.where(is_nd, 0.0, vals), minlength=n_edges
    )

    with np.errstate(invalid="ignore", divide="ignore"):
        avg = np.where(valid_len > 0, fric_sum / valid_len, np.nan)
        # No samples at all (empty/degenerate geometry): treat as fully
        # NoData so the strict rule (nodata_frac == 0 => passable) marks
        # the edge impassable, matching this function's contract.
        nodata_frac = np.where(tot_len > 0, nd_len / tot_len, 1.0)
    return avg, nodata_frac


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def compute_edge_month_weights(
    edges_shp: str | Path = EDGES_SHP,
    friction_dir: str | Path = FRICTION_OUTPUT_DIR,
    months: Iterable[int] = range(1, 13),
) -> pd.DataFrame:
    """Compute the full edge_month_weights frame (one row per edge-month).

    Land edges (Road/Join/IceRoad) sample the static road_base.tif once —
    their friction is month-invariant. Waterway edges sample each month's
    barge_MM.tif. Bridge/Air/Transfer are assigned friction 1.0 unsampled.
    """
    friction_dir = Path(friction_dir)
    months = sorted(months)

    edges = gpd.read_file(edges_shp)
    if edges.crs is None or edges.crs.to_epsg() != 3338:
        raise ValueError(
            f"{edges_shp} must be EPSG:3338 (Alaska Albers, meters); "
            f"got {edges.crs}"
        )
    unknown = set(edges["type"].unique()) - set(EDGE_TYPE_MAP)
    if unknown:
        raise ValueError(f"Unmapped edge types in {edges_shp}: {sorted(unknown)}")

    n_edges = len(edges)
    edge_type = edges["type"].to_numpy()
    logger.info("loaded %d edges from %s", n_edges, edges_shp)

    source = np.array([EDGE_TYPE_MAP[t][0] or "" for t in edge_type])
    rate_mode = np.array([EDGE_TYPE_MAP[t][1] for t in edge_type])

    # Bridge disambiguation (see TERMINOLOGY CAVEAT in the module
    # docstring): `Bridge` edges whose provenance is ice-road-related
    # (`weld:IceRoad`, `bridge:IceRoad->Road`) are welds within / into the
    # ice-road system, not water crossings — re-type them to IceRoad
    # treatment so they inherit the sampling, the x2.0 penalty, and the
    # Jan-Mar gate.
    ice_bridge = (edge_type == "Bridge") & edges["source"].astype(str).str.contains(
        "IceRoad", na=False
    ).to_numpy()
    if ice_bridge.any():
        source[ice_bridge] = "road_base"
        rate_mode[ice_bridge] = "IceRoad"
        logger.info(
            "re-typed %d Bridge edges with ice-road provenance to IceRoad "
            "treatment", int(ice_bridge.sum()),
        )

    # Month-invariant friction, filled per sampling group. Unsampled types
    # (Bridge/Air/Transfer) are flat 1.0 by design — bridges are engineered
    # crossings and Air is unaffected by terrain.
    static_avg = np.full(n_edges, 1.0, dtype=np.float64)
    static_ndf = np.zeros(n_edges, dtype=np.float64)

    # --- land edges: one static road_base sample -------------------------
    land_idx = np.flatnonzero(source == "road_base")
    logger.info("densifying %d land edges (Road/Join/IceRoad) ...", len(land_idx))
    xy, seg_len, owner = build_sample_arrays(
        edges.geometry.iloc[land_idx], land_idx
    )
    logger.info("sampling road_base.tif at %d points ...", len(xy))
    vals = sample_raster(friction_dir / "road_base.tif", xy)
    avg, ndf = edge_weighted_stats(owner, seg_len, vals, n_edges)
    static_avg[land_idx] = avg[land_idx]
    static_ndf[land_idx] = ndf[land_idx]
    # IceRoad rides the same surface with the seasonal time penalty. This is
    # a travel-time multiplier (environmental axis), NOT the IceRoad $ rate.
    # ice-road-provenance Bridge welds (re-typed above) are included.
    ice_mask = (edge_type == "IceRoad") | ice_bridge
    static_avg[ice_mask] *= ICEROAD_TIME_PENALTY

    # --- water edges: densify once, sample per month ---------------------
    water_idx = np.flatnonzero(source == "barge")
    logger.info("densifying %d waterway edges ...", len(water_idx))
    w_xy, w_len, w_owner = build_sample_arrays(
        edges.geometry.iloc[water_idx], water_idx
    )
    logger.info("waterway sample points: %d", len(w_xy))

    frames = []
    for month in months:
        avg_m = static_avg.copy()
        ndf_m = static_ndf.copy()

        barge_path = friction_dir / f"barge_{month:02d}.tif"
        logger.info("sampling %s ...", barge_path)
        w_vals = sample_raster(barge_path, w_xy)
        w_avg, w_ndf = edge_weighted_stats(w_owner, w_len, w_vals, n_edges)
        avg_m[water_idx] = w_avg[water_idx]
        ndf_m[water_idx] = w_ndf[water_idx]

        # Strict rule: any NoData on the line => impassable this month.
        passable = ndf_m == 0.0
        # IceRoad availability gate: road_base carries no LULC/tundra, so
        # nothing "reverts" out of season — the gate is purely seasonal.
        if month not in ICE_ROAD_SEASON_MONTHS:
            passable[ice_mask] = False

        frames.append(pd.DataFrame({
            "edge_id": np.arange(n_edges, dtype=np.int64),
            "month": np.int8(month),
            "mode": rate_mode,
            "avg_friction": avg_m,
            "nodata_frac": ndf_m,
            "passable": passable,
        }))

    return pd.concat(frames, ignore_index=True)


def qa_report(df: pd.DataFrame, edge_type: np.ndarray) -> None:
    """Print the plan's Phase 2 QA checks on the sampled weights."""
    one_month = df[df["month"] == df["month"].min()]
    typ = pd.Series(edge_type, name="type")

    road = one_month[typ.reindex(one_month["edge_id"]).to_numpy() == "Road"]
    logger.info(
        "QA Road: avg_friction min=%.3f max=%.3f (expect within [1.0, 2.625]); "
        "impassable=%d of %d",
        road["avg_friction"].min(), road["avg_friction"].max(),
        (~road["passable"]).sum(), len(road),
    )

    ice = df[(df["mode"] == "IceRoad")]
    in_season = ice[ice["month"].isin(sorted(ICE_ROAD_SEASON_MONTHS))]
    out_season = ice[~ice["month"].isin(sorted(ICE_ROAD_SEASON_MONTHS))]
    logger.info(
        "QA IceRoad: in-season avg=%.3f (expect ~slope x %.1f x permafrost, "
        "range [%.1f, %.3f]); in-season passable=%d/%d; out-of-season passable=%d "
        "(expect 0)",
        in_season["avg_friction"].mean(), ICEROAD_TIME_PENALTY,
        ICEROAD_TIME_PENALTY, 2.625 * ICEROAD_TIME_PENALTY,
        in_season["passable"].sum(), len(in_season), out_season["passable"].sum(),
    )

    water = df[df["mode"] == "Barge"]
    by_month = water.groupby("month")["passable"].mean()
    logger.info("QA Waterway passable fraction by month:\n%s",
                by_month.to_string(float_format="%.3f"))

    join = one_month[typ.reindex(one_month["edge_id"]).to_numpy() == "Join"]
    logger.info(
        "QA Join (45 edges, hand-reviewable): avg_friction min=%.3f max=%.3f, "
        "impassable=%d",
        join["avg_friction"].min(), join["avg_friction"].max(),
        (~join["passable"]).sum(),
    )


def write_to_duckdb(df: pd.DataFrame, db_path: str | Path = DB_PATH) -> None:
    """Replace edge_month_weights in fuel_network.duckdb."""
    con = duckdb.connect(str(db_path))
    try:
        con.register("edge_month_weights_df", df)
        con.execute("""
            CREATE OR REPLACE TABLE edge_month_weights AS
            SELECT
                edge_id::BIGINT       AS edge_id,
                month::TINYINT        AS month,
                mode::VARCHAR         AS mode,
                avg_friction::DOUBLE  AS avg_friction,
                nodata_frac::DOUBLE   AS nodata_frac,
                passable::BOOLEAN     AS passable
            FROM edge_month_weights_df
        """)
        n = con.execute("SELECT COUNT(*) FROM edge_month_weights").fetchone()[0]
        logger.info("wrote edge_month_weights: %d rows -> %s", n, db_path)
    finally:
        con.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Sample friction rasters along final_network edges "
                    "(Phase 2: edge_month_weights)."
    )
    ap.add_argument("--edges", default=EDGES_SHP, type=Path)
    ap.add_argument("--friction-dir", default=FRICTION_OUTPUT_DIR, type=Path)
    ap.add_argument("--db", default=DB_PATH, type=Path)
    ap.add_argument("--months", nargs="+", type=int, default=list(range(1, 13)),
                    help="Subset of months to compute (smoke tests).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Compute and print QA, but do not write to DuckDB.")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    df = compute_edge_month_weights(
        edges_shp=args.edges,
        friction_dir=args.friction_dir,
        months=args.months,
    )
    edge_type = gpd.read_file(args.edges, ignore_geometry=True)["type"].to_numpy()
    qa_report(df, edge_type)

    if args.dry_run:
        logger.info("dry run: skipping DuckDB write (%d rows computed)", len(df))
        return
    write_to_duckdb(df, args.db)


if __name__ == "__main__":
    main()
