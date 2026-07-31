"""assemble_weighted_graph.py

Phase 3 of PLAN_network_friction_integration.md: turn the ingested network
(network_nodes / network_edges, Phase 1) and the sampled friction weights
(edge_month_weights, Phase 2) into per-month edge costs and a queryable
weighted graph.

Cost model (friction-vs-cost separation preserved — rasters stay
environmental, every dollar comes from friction_costs):

    line-haul:  cost_per_gallon = (length_m / METERS_PER_MILE)
                                  x avg_friction
                                  x BASELINE_RATES_PER_GALLON_MILE[mode]
    Transfer:   cost_per_gallon = INTERMODAL_TRANSFER_FEES[(mode_a, mode_b)]
                                  ["total"]  (per gallon, distance-free)

Transfer fee keying: a Transfer edge's (mode_a, mode_b) is inferred from
the line-haul edge classes incident to its endpoints (Waterway->barge,
Road/Weld/Join->overland, IceRoad/IceRoadWeld->ice_road, Air->plane).
Current inventory: 205 barge x overland + 8 barge x ice_road — both keyed
in INTERMODAL_TRANSFER_FEES. An unkeyable pair is a hard error (the
edge-cost completeness rule: no edge type is costless).

Output table:

    edge_costs(edge_id, month, cost_per_gallon, passable)
    90,921 x 12 = 1,091,052 rows

Graph assembly: ONE nx.MultiGraph (NOT nx.Graph — final_network has 648
parallel node-pairs which a simple Graph would silently collapse; edges are
keyed by edge_id). Each edge carries a 12-slot {month: (cost, passable)}
dict; `month_view()` returns the passable subgraph for a month as a cheap
filtered view, and `hub_to_hub_costs()` runs per-month Dijkstra between
hub nodes.

The backfill of mode_specific_edges / connects_to (plan Phase 3, last step)
is STUBBED pending the hub<->facility map (Julia's) — see
backfill_facility_edges().

Usage:
    python assemble_weighted_graph.py            # build edge_costs + QA
    python assemble_weighted_graph.py --dry-run  # compute + QA, no write
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import duckdb
import networkx as nx
import numpy as np
import pandas as pd

from friction_surface.friction_costs import (
    BASELINE_RATES_PER_GALLON_MILE,
    INTERMODAL_TRANSFER_FEES,
    METERS_PER_MILE,
)

logger = logging.getLogger(__name__)

DB_PATH = Path("fuel_network.duckdb")

# edge_class -> vocabulary used by INTERMODAL_TRANSFER_FEES keys.
FEE_MODE = {
    "Waterway": "barge",
    "Road": "overland",
    "Weld": "overland",
    "Join": "overland",
    "IceRoad": "ice_road",
    "IceRoadWeld": "ice_road",
    "Air": "plane",
}


# ---------------------------------------------------------------------------
# Transfer-fee inference
# ---------------------------------------------------------------------------

def _lookup_fee(mode_a: str, mode_b: str) -> float:
    """Per-gallon transfer fee for a modal handoff, direction-insensitive.

    The fee dict is keyed directionally but a graph edge is traversed both
    ways; physical handling events are the same either direction, so the
    defined direction's total is used for both.
    """
    for key in ((mode_a, mode_b), (mode_b, mode_a)):
        if key in INTERMODAL_TRANSFER_FEES:
            return float(INTERMODAL_TRANSFER_FEES[key]["total"])
    raise KeyError(
        f"No INTERMODAL_TRANSFER_FEES entry for ({mode_a}, {mode_b}) in "
        "either direction — add one to friction_costs.py (edge-cost "
        "completeness rule: no edge is costless)."
    )


def infer_transfer_fees(edges: pd.DataFrame) -> pd.Series:
    """Per-gallon fee for each Transfer edge, keyed by incident modes.

    For each endpoint of a Transfer edge, collect the fee-modes of its
    incident line-haul edges; the handoff pair is (mode at from-side,
    mode at to-side). Endpoints with several incident modes or with no
    line-haul edge at all are hard errors — with 213 Transfer edges these
    are hand-reviewable, and guessing would misprice the mode switch.

    Returns a Series of fees indexed like the Transfer subset of `edges`.
    """
    line_haul = edges[edges["edge_class"] != "Transfer"]
    incident = pd.concat([
        pd.DataFrame({"node": line_haul["from_node"],
                      "mode": line_haul["edge_class"].map(FEE_MODE)}),
        pd.DataFrame({"node": line_haul["to_node"],
                      "mode": line_haul["edge_class"].map(FEE_MODE)}),
    ])
    node_modes = incident.groupby("node")["mode"].agg(set)

    transfers = edges[edges["edge_class"] == "Transfer"]
    fees = {}
    for edge_id, u, v in transfers[["edge_id", "from_node", "to_node"]].itertuples(
        index=False
    ):
        side_u = node_modes.get(u, set())
        side_v = node_modes.get(v, set())
        if len(side_u) != 1 or len(side_v) != 1:
            raise ValueError(
                f"Transfer edge {edge_id}: ambiguous incident modes "
                f"({sorted(side_u)} x {sorted(side_v)}) — review by hand."
            )
        fees[edge_id] = _lookup_fee(next(iter(side_u)), next(iter(side_v)))
    return pd.Series(fees, name="fee")


# ---------------------------------------------------------------------------
# edge_costs
# ---------------------------------------------------------------------------

def build_edge_costs(db_path: str | Path = DB_PATH) -> pd.DataFrame:
    """Compute the edge_costs frame (one row per edge-month).

    Line-haul rows use the Phase 2 weights (avg_friction, passable);
    Transfer rows get the inferred per-gallon fee, all months passable.
    """
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        df = con.execute("""
            SELECT w.edge_id, w.month, w.mode, w.avg_friction, w.passable,
                   e.edge_class, e.from_node, e.to_node, e.length_m
            FROM edge_month_weights w
            JOIN network_edges e USING (edge_id)
        """).df()
        edges = con.execute("""
            SELECT edge_id, from_node, to_node, edge_class FROM network_edges
        """).df()
    finally:
        con.close()

    rates = df["mode"].map(BASELINE_RATES_PER_GALLON_MILE)
    df["cost_per_gallon"] = (
        (df["length_m"] / METERS_PER_MILE) * df["avg_friction"] * rates
    )

    is_transfer = df["edge_class"] == "Transfer"
    fee_by_edge = infer_transfer_fees(edges)
    df.loc[is_transfer, "cost_per_gallon"] = (
        df.loc[is_transfer, "edge_id"].map(fee_by_edge)
    )
    logger.info(
        "transfer fees: %d edges, fee inventory %s",
        int(is_transfer.sum()) // 12,
        fee_by_edge.value_counts().to_dict(),
    )

    if df["cost_per_gallon"].isna().any():
        bad = df[df["cost_per_gallon"].isna()]
        # Impassable line-haul rows can have NaN friction (fully-blocked
        # sample set) — cost is meaningless there and the row is excluded
        # from routing by `passable` anyway.
        live_bad = bad[bad["passable"]]
        if len(live_bad):
            raise ValueError(
                f"{len(live_bad)} passable edge-months have NaN cost — "
                "first offenders:\n"
                + live_bad.head(10).to_string()
            )

    return df[["edge_id", "month", "cost_per_gallon", "passable"]]


def write_edge_costs(df: pd.DataFrame, db_path: str | Path = DB_PATH) -> None:
    """Replace edge_costs in fuel_network.duckdb."""
    con = duckdb.connect(str(db_path))
    try:
        con.register("edge_costs_df", df)
        con.execute("""
            CREATE OR REPLACE TABLE edge_costs AS
            SELECT
                edge_id::BIGINT          AS edge_id,
                month::TINYINT           AS month,
                cost_per_gallon::DOUBLE  AS cost_per_gallon,
                passable::BOOLEAN        AS passable
            FROM edge_costs_df
        """)
        n = con.execute("SELECT COUNT(*) FROM edge_costs").fetchone()[0]
        logger.info("wrote edge_costs: %d rows -> %s", n, db_path)
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def load_weighted_multigraph(db_path: str | Path = DB_PATH) -> nx.MultiGraph:
    """One MultiGraph, every edge carrying {month: (cost, passable)}.

    MultiGraph, not Graph: final_network has 648 parallel node-pairs
    (dual carriageways, braided channels, road-beside-ice-road) that a
    simple Graph would silently collapse. Edge keys are edge_id.

    Node attrs: is_hub, hub_id (hubs only). Edge attrs: edge_id,
    edge_class, length_m, month_cost={m: (cost_per_gallon, passable)}.
    """
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        nodes = con.execute("""
            SELECT node_id, is_hub, hub_id FROM network_nodes
        """).df()
        edges = con.execute("""
            SELECT edge_id, from_node, to_node, edge_class, length_m
            FROM network_edges
        """).df()
        costs = con.execute("""
            SELECT edge_id, month, cost_per_gallon, passable
            FROM edge_costs ORDER BY edge_id, month
        """).df()
    finally:
        con.close()

    month_cost: dict[int, dict[int, tuple[float, bool]]] = {}
    for edge_id, month, cost, passable in costs.itertuples(index=False):
        month_cost.setdefault(edge_id, {})[int(month)] = (
            float(cost) if cost == cost else float("nan"), bool(passable)
        )

    g = nx.MultiGraph()
    g.add_nodes_from(nodes["node_id"].to_numpy())
    hub_rows = nodes.loc[nodes["is_hub"], ["node_id", "hub_id"]]
    for node_id, hub_id in hub_rows.itertuples(index=False):
        g.nodes[node_id]["is_hub"] = True
        g.nodes[node_id]["hub_id"] = hub_id

    for edge_id, u, v, edge_class, length_m in edges.itertuples(index=False):
        g.add_edge(
            int(u), int(v), key=int(edge_id),
            edge_id=int(edge_id), edge_class=edge_class,
            length_m=float(length_m), month_cost=month_cost.get(edge_id, {}),
        )
    logger.info("assembled MultiGraph: %d nodes, %d edges",
                g.number_of_nodes(), g.number_of_edges())
    return g


def month_view(g: nx.MultiGraph, month: int) -> nx.MultiGraph:
    """Read-only subgraph view containing only edges passable in `month`."""
    def edge_ok(u, v, k):
        cost, passable = g[u][v][k]["month_cost"].get(month, (float("nan"), False))
        return passable
    return nx.subgraph_view(g, filter_edge=edge_ok)


def month_weight(month: int):
    """Dijkstra weight function for `month` (cost_per_gallon per edge).

    MultiGraph semantics: networkx hands the weight callable the keyed
    dict of ALL parallel edges between u and v ({key: attrs}), so this
    takes the cheapest passable parallel edge. Returning None tells
    networkx to ignore the connection entirely (all parallels impassable
    that month) — so this weight alone enforces seasonal gating and
    month_view() is not required for correctness in Dijkstra calls.
    """
    def weight(u, v, keyed_data):
        best = None
        for attrs in keyed_data.values():
            cost, passable = attrs["month_cost"].get(month, (None, False))
            if passable and cost == cost:  # cost==cost filters NaN
                if best is None or cost < best:
                    best = cost
        return best
    return weight


def hub_to_hub_costs(
    g: nx.MultiGraph, month: int, hub_node_ids: list[int] | None = None
) -> pd.DataFrame:
    """All-pairs hub shortest-path costs for one month.

    Runs single-source Dijkstra from each hub over the month's passable
    subgraph. Returns long-form (src_hub, dst_hub, cost_per_gallon);
    unreachable pairs are absent (callers can outer-join to flag them).
    """
    if hub_node_ids is None:
        hub_node_ids = [n for n, d in g.nodes(data=True) if d.get("is_hub")]
    # month_weight returns None for impassable connections, which networkx
    # treats as "edge absent" — no subgraph view needed.
    weight = month_weight(month)
    hub_set = set(hub_node_ids)

    rows = []
    for src in hub_node_ids:
        dist = nx.single_source_dijkstra_path_length(g, src, weight=weight)
        for dst, cost in dist.items():
            if dst in hub_set and dst != src:
                rows.append((g.nodes[src]["hub_id"], g.nodes[dst]["hub_id"], cost))
    return pd.DataFrame(rows, columns=["src_hub", "dst_hub", "cost_per_gallon"])


# ---------------------------------------------------------------------------
# Facility backfill (STUB — blocked on the hub<->facility map)
# ---------------------------------------------------------------------------

def backfill_facility_edges(*args, **kwargs):
    """Backfill mode_specific_edges / connects_to from hub shortest paths.

    BLOCKED on the hub_facility_map(hub_id, facility_id) table (Julia's
    Phase 1 step 4). Once it exists: hub_to_hub_costs() per (mode-chain,
    month) -> join hub_ids to facility_ids -> write in the existing
    mode_specific_edges / connects_to schemas so multimodal_router.py and
    tools.py keep working during the transition (plan Phase 3, last step).
    """
    raise NotImplementedError(
        "Blocked on hub_facility_map — see PLAN_network_friction_integration.md "
        "Phase 1 step 4 (Julia writes the 384-hub <-> 1,838-facility mapping)."
    )


# ---------------------------------------------------------------------------
# Driver / QA
# ---------------------------------------------------------------------------

def qa_report(df: pd.DataFrame, db_path: str | Path) -> None:
    """Cost sanity checks over the assembled edge_costs frame."""
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        classes = con.execute(
            "SELECT edge_id, edge_class FROM network_edges"
        ).df()
    finally:
        con.close()
    j = df.merge(classes, on="edge_id")
    jul = j[j["month"] == 7]
    stats = jul.groupby("edge_class").agg(
        edges=("edge_id", "count"),
        min_cost=("cost_per_gallon", "min"),
        med_cost=("cost_per_gallon", "median"),
        max_cost=("cost_per_gallon", "max"),
        passable=("passable", "mean"),
    ).round(4)
    logger.info("QA July cost per gallon by edge_class:\n%s", stats.to_string())

    zero_cost = j[(j["cost_per_gallon"] == 0) & j["passable"]]
    logger.info("QA zero-cost passable edge-months: %d (expect 0 — "
                "completeness rule)", len(zero_cost))


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Assemble per-month edge costs from Phase 1 + Phase 2 "
                    "tables (Phase 3: edge_costs + weighted graph)."
    )
    ap.add_argument("--db", default=DB_PATH, type=Path)
    ap.add_argument("--dry-run", action="store_true",
                    help="Compute and QA, but do not write edge_costs.")
    ap.add_argument("--smoke-dijkstra", action="store_true",
                    help="After writing, run a Feb-vs-Jul hub Dijkstra "
                         "smoke test on a few hubs.")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    df = build_edge_costs(args.db)
    qa_report(df, args.db)
    if args.dry_run:
        logger.info("dry run: skipping DuckDB write (%d rows computed)", len(df))
        return
    write_edge_costs(df, args.db)

    if args.smoke_dijkstra:
        g = load_weighted_multigraph(args.db)
        hubs = [n for n, d in g.nodes(data=True) if d.get("is_hub")][:5]
        for month in (2, 7):
            costs = hub_to_hub_costs(g, month, hubs)
            logger.info(
                "smoke Dijkstra month=%d from 5 hubs: %d reachable hub pairs, "
                "median cost $%.3f/gal",
                month, len(costs),
                costs["cost_per_gallon"].median() if len(costs) else float("nan"),
            )


if __name__ == "__main__":
    main()
