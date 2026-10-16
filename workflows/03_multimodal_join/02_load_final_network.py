"""load_final_network.py

Ingest the colleague's final_network shapefiles into fuel_network.duckdb as attribute tables.

Geometries stay in the shapefiles (matches the repo pattern where rasters
and vectors live on disk); DuckDB holds attributes + stable IDs only.

Stable-ID rule: `edge_id` is the 0-based row order of
final_network/network_joined_edges.shp — the SAME rule
weight_network_edges.py uses, so `network_edges` joins `edge_month_weights`
directly. This loader cross-checks the two tables when both are present.

Tables written (CREATE OR REPLACE):

    network_nodes(node_id PK, is_hub, hub_id, deliv_meth, hub_type,
                  hub_cap, snap_surf, component, is_giant, x, y)
    network_edges(edge_id PK, from_node, to_node, type, edge_class,
                  source, join_gap_m, length_m)
    hub_members(hub_id, hub_key, hub_community, hub_kind, delivery_method,
                hub_type, ast_facility_id, record_id, node_id, snap_status)
    hub_snaps(hub_id, node_id, snap_dist_m, snap_surface, status)

The last two come from final_network/hub_members.csv + hub_snaps.csv (written
by 06_export_final_network.py via mmnet.handoff since the 2026-10 export) and
are written only when those files exist beside the zips: the builder's own
answer to "which inventory records does this hub serve, what community is
it, where did it land" (closes the hub_facility_map seam of DATA_CONTRACTS §8).

Current exports carry a mode-based `type` vocabulary set by
`pipeline.classify_connectors`: within-mode welds are `{Mode}Connector`
(RoadConnector, IceRoadConnector), cross-mode handoffs are per-pair
`{A}{B}Transfer` (BargeRoadTransfer, IceRoadRoadTransfer, …). `edge_class`
is a pass-through of that `type`; it only diverges for a LEGACY frozen network,
whose generic `Bridge` welds it maps into the new vocabulary (ice-road
provenance -> IceRoadConnector, else -> RoadConnector) so old and new exports
converge on one vocabulary.

Integrity checks (hard errors, run before any write):
  - CRS is EPSG:3338 on both layers
  - every edge from/to references an existing node_id
  - node/edge counts, hub count, component count, giant share, and the
    edge-type inventory match final_network/README.md
  - if edge_month_weights exists: its edge_ids are exactly 0..n_edges-1

Usage:
    python load_final_network.py            # ingest + validate
    python load_final_network.py --dry-run  # validate only, no write
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Anchored to the repo root (two levels above workflows/03_multimodal_join/)
# so the script works from any CWD — no import-time chdir anywhere anymore.
ROOT = Path(__file__).resolve().parents[2]
FINAL_NETWORK_DIR = ROOT / "final_network"
NODES_SHP = FINAL_NETWORK_DIR / "network_joined_nodes" / "network_joined_nodes.shp"
EDGES_SHP = FINAL_NETWORK_DIR / "network_joined_edges" / "network_joined_edges.shp"
HUB_MEMBERS_CSV = FINAL_NETWORK_DIR / "hub_members.csv"
HUB_SNAPS_CSV = FINAL_NETWORK_DIR / "hub_snaps.csv"
DB_PATH = ROOT / "outputs" / "fuel_network.duckdb"

# Expected inventory per final_network/README.md — a changed export should
# fail loudly here, not flow silently into the weighted graph.
EXPECTED = {
    "n_nodes": 84_094,
    "n_edges": 93_049,
    "n_hubs": 329,
    "n_components": 4,
    "giant_share": 0.9999,
    # Mode-based connector vocabulary (refine-synthetic-connectors, 2026-09):
    # welds -> {Mode}Connector, cross-mode handoffs -> per-pair {A}{B}Transfer.
    # Re-exported 2026-10-15: phase-5 hub builder + corrected 2025 inventory +
    # 25 km connect/barge + 2 km snap-to-edge fallback (see final_network/README.md).
    "edge_types": {
        "Road": 55_539,
        "Waterway": 34_178,
        "Air": 226,
        "IceRoad": 1_248,
        "RoadConnector": 1_498,
        "IceRoadConnector": 34,
        "BargeRoadTransfer": 289,
        "BargeIceRoadTransfer": 21,
        "IceRoadRoadTransfer": 12,
        "AirRoadTransfer": 2,
        "BargeAirTransfer": 2,
    },
}


def derive_edge_class(edge_type: pd.Series, source: pd.Series) -> pd.Series:
    """Edge class in the mode-based vocabulary.

    Current exports already carry mode-based `type` values (RoadConnector,
    IceRoadConnector, per-pair *Transfer), so `edge_class` is a pass-through.
    A legacy frozen network's `Bridge` welds are mapped into the new vocabulary
    for back-compat: ice-road provenance -> IceRoadConnector (seasonal, treated
    as IceRoad by the weighting), otherwise -> RoadConnector.
    """
    edge_class = edge_type.copy()
    is_bridge = edge_type == "Bridge"
    if is_bridge.any():
        ice_weld = is_bridge & source.astype(str).str.contains("IceRoad", na=False)
        edge_class[is_bridge] = "RoadConnector"
        edge_class[ice_weld] = "IceRoadConnector"
    return edge_class


def validate(nodes: gpd.GeoDataFrame, edges: gpd.GeoDataFrame) -> None:
    """Hard integrity checks against the README-documented inventory."""
    for name, gdf in (("nodes", nodes), ("edges", edges)):
        if gdf.crs is None or gdf.crs.to_epsg() != 3338:
            raise ValueError(f"{name} layer must be EPSG:3338, got {gdf.crs}")

    errors: list[str] = []

    def check(label: str, got, want) -> None:
        if got != want:
            errors.append(f"{label}: got {got!r}, expected {want!r}")

    check("node count", len(nodes), EXPECTED["n_nodes"])
    check("edge count", len(edges), EXPECTED["n_edges"])
    check("hub count", int(nodes["is_hub"].sum()), EXPECTED["n_hubs"])
    check("component count", int(nodes["component"].nunique()),
          EXPECTED["n_components"])
    giant = round(float(nodes["is_giant"].mean()), 4)
    check("giant share", giant, EXPECTED["giant_share"])
    check("edge-type inventory", edges["type"].value_counts().to_dict(),
          EXPECTED["edge_types"])

    node_ids = set(nodes["node_id"].to_numpy())
    dangling = ~(edges["from"].isin(node_ids) & edges["to"].isin(node_ids))
    if dangling.any():
        errors.append(f"{int(dangling.sum())} edges reference missing node_ids")

    if nodes["node_id"].duplicated().any():
        errors.append("duplicate node_ids in nodes layer")

    if errors:
        raise ValueError(
            "final_network integrity check failed:\n  - " + "\n  - ".join(errors)
        )
    logger.info(
        "integrity OK: %d nodes (%d hubs, %d components, giant %.2f%%), "
        "%d edges, type inventory matches README",
        len(nodes), EXPECTED["n_hubs"], EXPECTED["n_components"],
        100 * giant, len(edges),
    )


def cross_check_edge_month_weights(con: duckdb.DuckDBPyConnection,
                                   n_edges: int) -> None:
    """Verify edge_month_weights (if present) shares the row-order edge_id rule."""
    tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if "edge_month_weights" not in tables:
        logger.info("edge_month_weights not present yet — skipping cross-check")
        return
    lo, hi, n_distinct = con.execute(
        "SELECT MIN(edge_id), MAX(edge_id), COUNT(DISTINCT edge_id) "
        "FROM edge_month_weights"
    ).fetchone()
    if (lo, hi, n_distinct) != (0, n_edges - 1, n_edges):
        raise ValueError(
            f"edge_month_weights edge_ids (min={lo}, max={hi}, "
            f"distinct={n_distinct}) do not match network_edges row order "
            f"(expected 0..{n_edges - 1}) — rerun weight_network_edges.py "
            "against the current shapefile."
        )
    logger.info("edge_month_weights cross-check OK (%d edge_ids align)", n_edges)


def load_hub_handoff(con: duckdb.DuckDBPyConnection,
                     members_csv: str | Path = HUB_MEMBERS_CSV,
                     snaps_csv: str | Path = HUB_SNAPS_CSV) -> dict:
    """Load final_network/hub_members.csv and hub_snaps.csv as DuckDB tables when present.

    Checks (hard errors): every placed or merged hub's node_id is a network_nodes row that
    carries is_hub, and the number of DISTINCT nodes the placed hubs landed on equals the
    is_hub count — the two files and the shapefile describe the same build. Returns the
    row counts written (empty when the files are absent, which an older export is)."""
    members_csv, snaps_csv = Path(members_csv), Path(snaps_csv)
    written: dict[str, int] = {}
    if not members_csv.exists():
        logger.info("no %s beside the zips (export predates the hub handoff) — skipping", members_csv.name)
        return written
    con.execute("""
        CREATE OR REPLACE TABLE hub_members AS
        SELECT hub_id::VARCHAR AS hub_id, hub_key::VARCHAR AS hub_key,
               hub_community::VARCHAR AS hub_community, hub_kind::VARCHAR AS hub_kind,
               delivery_method::VARCHAR AS delivery_method, hub_type::VARCHAR AS hub_type,
               ast_facility_id::VARCHAR AS ast_facility_id, record_id::VARCHAR AS record_id,
               node_id::BIGINT AS node_id, snap_status::VARCHAR AS snap_status
        FROM read_csv(?, header = true, all_varchar = true)""", [str(members_csv)])
    written["hub_members"] = con.execute("SELECT count(*) FROM hub_members").fetchone()[0]
    if snaps_csv.exists():
        con.execute("""
            CREATE OR REPLACE TABLE hub_snaps AS
            SELECT hub_id::VARCHAR AS hub_id, node_id::BIGINT AS node_id,
                   snap_dist_m::DOUBLE AS snap_dist_m, snap_surface::VARCHAR AS snap_surface,
                   status::VARCHAR AS status
            FROM read_csv(?, header = true, all_varchar = true)""", [str(snaps_csv)])
        written["hub_snaps"] = con.execute("SELECT count(*) FROM hub_snaps").fetchone()[0]
    # the handoff and the shapefile describe one build
    orphans = con.execute("""
        SELECT count(DISTINCT m.hub_id) FROM hub_members m
        LEFT JOIN network_nodes n ON n.node_id = m.node_id
        WHERE m.node_id IS NOT NULL AND (n.node_id IS NULL OR NOT n.is_hub)""").fetchone()[0]
    if orphans:
        raise SystemExit(f"hub_members: {orphans} hub(s) name a node_id that is not a hub node")
    landed = con.execute("SELECT count(DISTINCT node_id) FROM hub_members "
                         "WHERE snap_status = 'placed'").fetchone()[0]
    n_hub_nodes = con.execute("SELECT count(*) FROM network_nodes WHERE is_hub").fetchone()[0]
    if landed != n_hub_nodes:
        raise SystemExit(f"hub_members: {landed} distinct placed nodes vs {n_hub_nodes} hub nodes "
                         "in network_nodes — the handoff files and the shapefile are from different builds")
    logger.info("hub handoff loaded: %s", written)
    return written


def load_final_network(
    nodes_shp: str | Path = NODES_SHP,
    edges_shp: str | Path = EDGES_SHP,
    db_path: str | Path = DB_PATH,
    dry_run: bool = False,
) -> None:
    nodes = gpd.read_file(nodes_shp)
    edges = gpd.read_file(edges_shp)
    logger.info("read %d nodes, %d edges", len(nodes), len(edges))

    validate(nodes, edges)

    nodes_df = pd.DataFrame({
        "node_id": nodes["node_id"].astype("int64"),
        "is_hub": nodes["is_hub"].astype(bool),
        "hub_id": nodes["hub_id"],
        "deliv_meth": nodes["deliv_meth"],
        "hub_type": nodes["hub_type"],
        # DBF stores hub_cap as text; empty/None -> NULL
        "hub_cap": pd.to_numeric(nodes["hub_cap"], errors="coerce"),
        "snap_surf": nodes["snap_surf"],
        "component": nodes["component"].astype("int64"),
        "is_giant": nodes["is_giant"].astype(bool),
        "x": nodes.geometry.x,
        "y": nodes.geometry.y,
    })

    edges_df = pd.DataFrame({
        # Stable ID = shapefile row order (same rule as weight_network_edges)
        "edge_id": np.arange(len(edges), dtype=np.int64),
        "from_node": edges["from"].astype("int64"),
        "to_node": edges["to"].astype("int64"),
        "type": edges["type"],
        "edge_class": derive_edge_class(edges["type"], edges["source"]),
        "source": edges["source"],
        "join_gap_m": pd.to_numeric(edges["join_gap_m"], errors="coerce"),
        # EPSG:3338 is meters, so shapely length is meters
        "length_m": edges.geometry.length,
    })
    logger.info("edge_class inventory:\n%s",
                edges_df["edge_class"].value_counts().to_string())

    if dry_run:
        logger.info("dry run: skipping DuckDB write")
        return

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    try:
        cross_check_edge_month_weights(con, len(edges_df))
        con.register("nodes_df", nodes_df)
        con.register("edges_df", edges_df)
        con.execute("""
            CREATE OR REPLACE TABLE network_nodes AS
            SELECT
                node_id::BIGINT    AS node_id,
                is_hub::BOOLEAN    AS is_hub,
                hub_id::VARCHAR    AS hub_id,
                deliv_meth::VARCHAR AS deliv_meth,
                hub_type::VARCHAR  AS hub_type,
                hub_cap::DOUBLE    AS hub_cap,
                snap_surf::VARCHAR AS snap_surf,
                component::BIGINT  AS component,
                is_giant::BOOLEAN  AS is_giant,
                x::DOUBLE          AS x,
                y::DOUBLE          AS y
            FROM nodes_df
        """)
        con.execute("""
            CREATE OR REPLACE TABLE network_edges AS
            SELECT
                edge_id::BIGINT    AS edge_id,
                from_node::BIGINT  AS from_node,
                to_node::BIGINT    AS to_node,
                type::VARCHAR      AS type,
                edge_class::VARCHAR AS edge_class,
                source::VARCHAR    AS source,
                join_gap_m::DOUBLE AS join_gap_m,
                length_m::DOUBLE   AS length_m
            FROM edges_df
        """)
        n_nodes = con.execute("SELECT COUNT(*) FROM network_nodes").fetchone()[0]
        n_edges = con.execute("SELECT COUNT(*) FROM network_edges").fetchone()[0]
        logger.info("wrote network_nodes (%d rows) + network_edges (%d rows) -> %s",
                    n_nodes, n_edges, db_path)
        load_hub_handoff(con, Path(nodes_shp).parents[1] / "hub_members.csv",
                         Path(nodes_shp).parents[1] / "hub_snaps.csv")
    finally:
        con.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Ingest final_network shapefiles into fuel_network.duckdb "
                    "(Phase 1: network_nodes + network_edges)."
    )
    ap.add_argument("--nodes", default=NODES_SHP, type=Path)
    ap.add_argument("--edges", default=EDGES_SHP, type=Path)
    ap.add_argument("--db", default=DB_PATH, type=Path)
    ap.add_argument("--dry-run", action="store_true",
                    help="Validate and report, but do not write to DuckDB.")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_final_network(args.nodes, args.edges, args.db, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
