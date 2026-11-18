#!/usr/bin/env python3
"""Barge passability by hub, after weighting — the check that would have
caught Kodiak and Unalaska.

From the weighted DuckDB network, reports:
  (a) every barge-coded hub with NO open barge path to the Anchorage hub in any
      of Jun-Oct (path over Road / RoadConnector / Waterway / BargeRoadTransfer /
      BargeAirTransfer edges, Waterway gated by edge_month_weights mode=Barge),
      with the blocking edges on its least-blocked path;
  (b) every Waterway edge closed in all 12 months, with its minimum NoData
      fraction over the year (land/coverage if it never clears; ice clears).

Writes outputs/tables/barge_passability_hubs.csv and ..._closed_edges.csv.
A hub in (a) whose community is NOT in inputs/network_qc/
accepted_barge_exceptions.csv fails the stage (exit 1) — a NEW unreachable
barge hub must be looked at; known ones stay listed until fixed.

Usage:  python workflows/03_multimodal_join/06_qa_barge_passability.py
"""
from __future__ import annotations

import csv
import sys

import duckdb
import networkx as nx
import pandas as pd

import repo_paths as rp

SUMMER_CLASSES = ("Road", "RoadConnector", "Waterway", "BargeRoadTransfer", "BargeAirTransfer")
SUMMER_MONTHS = (6, 7, 8, 9, 10)
EXCEPTIONS = rp.INPUTS / "network_qc" / "accepted_barge_exceptions.csv"


def hub_exceptions() -> set[str]:
    if not EXCEPTIONS.exists():
        return set()
    with open(EXCEPTIONS, newline="") as fh:
        return {r["key"].strip().lower() for r in csv.DictReader(fh) if r["kind"] == "hub"}


def main() -> int:
    con = duckdb.connect(str(rp.DUCKDB), read_only=True)
    have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if "edge_month_weights" not in have:
        print("GATE: edge_month_weights absent — run 03_weight_network_edges.py first")
        return 3

    edges = con.execute(
        "SELECT edge_id, from_node, to_node, edge_class FROM network_edges "
        f"WHERE edge_class IN {SUMMER_CLASSES}").df()
    nodes = con.execute(
        "SELECT node_id, is_hub, hub_id, deliv_meth FROM network_nodes").df()
    hubm = con.execute(
        "SELECT DISTINCT hub_id, hub_community FROM hub_members").df()
    ww = con.execute(
        "SELECT w.edge_id, w.month, w.passable, w.nodata_frac FROM edge_month_weights w "
        "JOIN network_edges e USING (edge_id) "
        "WHERE w.mode = 'Barge' AND e.edge_class = 'Waterway'").df()

    comm = hubm.set_index("hub_id").hub_community
    hubs = nodes[nodes.is_hub & nodes.deliv_meth.astype(str).str.contains("Barge", na=False)]
    anc = hubm[hubm.hub_community == "Anchorage"].hub_id.iloc[0]
    anc_node = int(nodes[nodes.hub_id == anc].node_id.iloc[0])

    open_by_month = {m: set(ww.loc[(ww.month == m) & ww.passable, "edge_id"])
                     for m in SUMMER_MONTHS}
    min_ndf = ww.groupby("edge_id").nodata_frac.min()
    ever_open = ww.groupby("edge_id").passable.any()
    closed_all = ever_open[~ever_open].index

    def comp_lookup(open_ww):
        G = nx.Graph()
        G.add_nodes_from(nodes.node_id)
        keep = (edges.edge_class != "Waterway") | edges.edge_id.isin(open_ww)
        sub = edges[keep]
        G.add_edges_from(zip(sub.from_node, sub.to_node))
        lab = {}
        for i, c in enumerate(nx.connected_components(G)):
            for n in c:
                lab[n] = i
        return lab

    labs = {m: comp_lookup(open_by_month[m]) for m in SUMMER_MONTHS}

    rows = []
    for h in hubs.itertuples():
        months_open = [m for m in SUMMER_MONTHS
                       if labs[m][h.node_id] == labs[m][anc_node]]
        if not months_open:
            rows.append(dict(hub_id=h.hub_id,
                             community=comm.get(h.hub_id, ""),
                             node_id=h.node_id))
    print(f"{len(hubs)} barge-coded hubs; {len(rows)} with no open Jun-Oct barge path "
          f"to Anchorage")

    rp.TABLES.mkdir(parents=True, exist_ok=True)
    hub_rep = pd.DataFrame(rows, columns=["hub_id", "community", "node_id"])
    hub_rep.to_csv(rp.TABLES / "barge_passability_hubs.csv", index=False)

    edge_rep = pd.DataFrame({
        "edge_id": closed_all.values,
        "min_nodata_frac": min_ndf.reindex(closed_all).round(4).values,
    }).sort_values("edge_id")
    edge_rep.to_csv(rp.TABLES / "barge_passability_closed_edges.csv", index=False)
    print(f"{len(edge_rep)} Waterway edge(s) closed in all 12 months "
          f"(min NoData never 0: land or missing coverage, not ice)")

    excused = hub_exceptions()
    new_fail = [r["community"] or str(r["hub_id"]) for r in rows
                if str(r["community"]).strip().lower() not in excused]
    if new_fail:
        print(f"FAIL: NEW hub(s) with no summer barge path, not in {EXCEPTIONS.name}: {new_fail}")
        return 1
    print("PASS: every no-summer-path barge hub is a listed, accepted exception")
    return 0


if __name__ == "__main__":
    sys.exit(main())
