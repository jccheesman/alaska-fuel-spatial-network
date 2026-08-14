"""Stage 01 — facility consolidation (R: consolidate_facilities, network_preprocessing.R:76-144).

Co-located rows are duplicates of one physical facility (small GPS drift). Complete-linkage
hierarchical clustering cut at `dedup_tol_m` guarantees no merged cluster spans more than the
tolerance; capacities merge with max(), delivery methods union, location is the cluster centroid.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage

from ..config import Params, PipelineConfig
from ..io_readers import load_delivery_fallback, read_facilities_raw

# Defaults (used only when no profile is passed); the real values come from the RegionProfile.
ROUTABLE_MODES = ("Road", "Barge", "Plane")
_CAPACITY_COLS = [
    "gasoline_capacity", "diesel_capacity", "av_gas_capacity",
    "jet_fuel_capacity", "other_fuel_capacity", "total_capacity",
]


def filter_to_modes(value, modes=ROUTABLE_MODES) -> str:
    """Parse a delivery-method string to its in-scope atoms (R: filter_to_modes).

    Splits on ' or ' / ' and ', keeps only `modes`, returns them sorted/unique and ' or '-joined,
    or '' if nothing in scope remains.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    atoms = []
    for part in str(value).replace(" and ", " or ").split(" or "):
        a = part.strip()
        if a in modes:
            atoms.append(a)
    return " or ".join(sorted(set(atoms)))


def _max_or_nan(s: pd.Series) -> float:
    s = s.dropna()
    return float(s.max()) if len(s) else np.nan


def _first_notna(s: pd.Series):
    s = s.dropna()
    return s.iloc[0] if len(s) else None


def _clean_id(v):
    """Normalize an inventory id to a clean string (229.0 -> '229'); NA stays NA for later minting."""
    if pd.isna(v):
        return pd.NA
    if isinstance(v, float) and float(v).is_integer():
        return str(int(v))
    return str(v)


def _is_blank(dm: pd.Series) -> pd.Series:
    return dm.isna() | (dm.astype("string").str.strip() == "")


def fill_delivery_method(gdf: gpd.GeoDataFrame, fallback: gpd.GeoDataFrame,
                         max_dist_m: float = 5000.0) -> tuple[gpd.GeoDataFrame, dict]:
    """Fill facilities whose `delivery_method` is blank from a community->mode fallback layer.

    Two tiers, each recorded in a `delivery_method_source` column: (1) match the facility's
    `community_name` to a fallback community (authoritative); (2) for any still-blank facility with
    geometry, adopt the nearest fallback marker's mode when it lies within `max_dist_m`. Returns
    (gdf, stats). Region-agnostic — the fallback layer + distance are caller-supplied.
    """
    out = gdf.copy()
    blank = _is_blank(out["delivery_method"])
    out["delivery_method_source"] = np.where(blank, None, "inventory")
    stats = {"blank": int(blank.sum()), "by_name": 0, "by_nearest": 0, "remaining": int(blank.sum())}
    if not blank.any() or fallback is None or len(fallback) == 0:
        return out, stats

    # Tier 1 — community-name match.
    lookup = dict(zip(fallback["community"].astype("string").str.strip().str.upper(), fallback["method"]))
    comm = out["community_name"].astype("string").str.strip().str.upper()
    name_fill = blank & comm.isin(lookup.keys())
    out.loc[name_fill, "delivery_method"] = comm[name_fill].map(lookup).astype(object)
    out.loc[name_fill, "delivery_method_source"] = "community_name"
    stats["by_name"] = int(name_fill.sum())

    # Tier 2 — nearest fallback marker within max_dist_m.
    blank2 = _is_blank(out["delivery_method"]) & out.geometry.notna() & ~out.geometry.is_empty
    if blank2.any():
        j = gpd.sjoin_nearest(out.loc[blank2, ["geometry"]], fallback[["method", "geometry"]],
                              how="left", distance_col="_d")
        j = j[~j.index.duplicated(keep="first")]
        near = j.index[j["_d"] <= float(max_dist_m)]
        out.loc[near, "delivery_method"] = j.loc[near, "method"].astype(object).values
        out.loc[near, "delivery_method_source"] = "community_nearest"
        stats["by_nearest"] = int(len(near))

    stats["remaining"] = int(_is_blank(out["delivery_method"]).sum())
    return out, stats


def consolidate_facilities(
    raw_path: str | Path, params: Params, input_crs: int = 4326, target_crs: int = 3857,
    config: PipelineConfig | None = None,
) -> gpd.GeoDataFrame:
    """Raw inventory CSV -> deduplicated multimodal facility points (EPSG:target_crs).

    Column map, routable modes, and capacity columns come from `config` (the RegionProfile
    projection). `config` is required in practice; the bare fallbacks below only support trivial
    smoke tests and assume nothing region-specific.

    A facility is kept when it has a routable delivery_method and a total_capacity; a blank inventory
    ASTFacilityID is NOT a reason to drop it — those rows get a deterministic synthetic id
    ("SYN-<cluster_id>"). When `config.delivery_fallback` is set, blank delivery methods are first
    filled from that community->mode layer (see `fill_delivery_method`).
    """
    modes = tuple(config.routable_modes) if config and config.routable_modes else ROUTABLE_MODES
    cap_cols = config.capacity_columns if config and config.capacity_columns else _CAPACITY_COLS
    col_map = config.facility_columns if config and config.facility_columns else None

    gdf = read_facilities_raw(
        raw_path, input_crs, target_crs, column_map=col_map, numeric_cols=cap_cols,
    )

    # Optional: recover facilities whose inventory delivery_method is blank by filling it from a
    # community->mode fallback layer (profile-driven; skipped when not configured).
    if config is not None and getattr(config, "delivery_fallback", None) is not None:
        fb = config.delivery_fallback
        fallback = load_delivery_fallback(config.delivery_fallback_path(), target_crs,
                                          fb.community_col, fb.method_col)
        gdf, stats = fill_delivery_method(gdf, fallback, fb.max_dist_m)
        print(f"[consolidate] delivery_method fallback: {stats['blank']} blank -> filled "
              f"{stats['by_name']} by name + {stats['by_nearest']} by nearest "
              f"(<= {fb.max_dist_m:.0f} m); {stats['remaining']} still blank")

    # Scope to routable modes BEFORE clustering (drops Unknown/blank atoms).
    gdf["delivery_method"] = gdf["delivery_method"].map(lambda v: filter_to_modes(v, modes))
    gdf = gdf[gdf["delivery_method"] != ""].reset_index(drop=True)

    # Keep CSV (file) order through clustering + merge. File order is deterministic from the input,
    # and it makes the per-cluster first()-non-NA picks (community_name, entity_name) match R, whose
    # consolidate merges in file order. Pre-sorting by id would silently pick a different spelling
    # for multi-row (multi-tank) clusters.

    # Duplicate detection: complete-linkage, diameter-bounded at dedup_tol_m.
    coords = np.c_[gdf.geometry.x.to_numpy(), gdf.geometry.y.to_numpy()]
    if len(gdf) > 1:
        Z = linkage(coords, method="complete", metric="euclidean")
        clusters = fcluster(Z, t=float(params.dedup_tol_m), criterion="distance")
    else:
        clusters = np.array([1])
    gdf["cluster_id"] = clusters

    # Merge clusters: union delivery atoms, max() capacities, first non-NA text, centroid location.
    rows = []
    for cid, grp in gdf.groupby("cluster_id", sort=True):
        rec = {
            "cluster_id": int(cid),
            "delivery_method": filter_to_modes(" or ".join(grp["delivery_method"]), modes),
            "ast_facility_id": _first_notna(grp["ast_facility_id"]),
            "x": float(grp.geometry.x.mean()),
            "y": float(grp.geometry.y.mean()),
        }
        # Optional descriptive columns: present only when the profile maps them.
        for opt in ("community_name", "entity_name"):
            if opt in grp.columns:
                rec[opt] = _first_notna(grp[opt])
        for col in cap_cols:
            rec[col] = _max_or_nan(grp[col]) if col in grp.columns else np.nan
        rows.append(rec)

    out = pd.DataFrame(rows)
    # Keep every facility that has a mode and a capacity. A blank inventory ASTFacilityID is NOT a
    # reason to drop the facility: mint a deterministic synthetic id ("SYN-<cluster_id>") so it stays
    # identifiable downstream.
    out = out[
        (out["delivery_method"] != "")
        & out["total_capacity"].notna()
    ].reset_index(drop=True)
    out["ast_facility_id"] = out["ast_facility_id"].map(_clean_id).astype("string")
    synthetic = out["ast_facility_id"].isna()
    out.loc[synthetic, "ast_facility_id"] = "SYN-" + out.loc[synthetic, "cluster_id"].astype("string")

    gout = gpd.GeoDataFrame(
        out.drop(columns=["x", "y"]),
        geometry=gpd.points_from_xy(out["x"], out["y"]),
        crs=target_crs,
    )
    return gout.sort_values("ast_facility_id", kind="stable").reset_index(drop=True)
