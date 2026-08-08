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

`edge_class` disambiguates the legacy `Bridge` type (an mmnet topology
weld, NOT a road-over-water bridge — see bridge-edge-terminology note in
weight_network_edges.py): `weld:IceRoad` / `bridge:IceRoad->Road` provenance
becomes `IceRoadConnector` (seasonal, Jan-Mar), remaining Bridge edges become
`Weld`, every other type maps through unchanged. Networks rebuilt with the
current profile emit `IceRoadConnector` as the `type` itself (the profile's
bridge rules carry `edge_type`), so old and new exports converge on one
vocabulary.

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
DB_PATH = ROOT / "outputs" / "fuel_network.duckdb"

# Expected inventory per final_network/README.md — a changed export should
# fail loudly here, not flow silently into the weighted graph.
EXPECTED = {
    "n_nodes": 82_300,
    "n_edges": 90_921,
    "n_hubs": 384,
    "n_components": 21,
    "giant_share": 0.9965,
    "edge_types": {
        "Road": 53_795,
        "Waterway": 34_099,
        "Bridge": 1_367,
        "IceRoad": 1_248,
        "Transfer": 213,
        "Air": 154,
        "Join": 45,
    },
}


def derive_edge_class(edge_type: pd.Series, source: pd.Series) -> pd.Series:
    """Disambiguated edge class (legacy `Bridge` = topology weld).

    Legacy Bridge + ice-road provenance -> IceRoadConnector (seasonal,
    treated as IceRoad by the weighting); other Bridge -> Weld (year-round
    stitch); every other type — including the modern IceRoadConnector type
    emitted directly by rebuilds — passes through unchanged, so frozen and
    rebuilt exports share one vocabulary.
    """
    edge_class = edge_type.copy()
    is_bridge = edge_type == "Bridge"
    ice_weld = is_bridge & source.astype(str).str.contains("IceRoad", na=False)
    edge_class[is_bridge] = "Weld"
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
