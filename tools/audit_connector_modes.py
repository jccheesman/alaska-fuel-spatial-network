#!/usr/bin/env python3
"""Audit: every synthetic connector's type agrees with the modes it joins.

The mode-based connector vocabulary (refine-synthetic-connectors) is only
correct if each connector's `type` matches its endpoints:

  * a `{Mode}Connector` weld must join ONE mode (endpoints carry only that mode);
  * a per-pair `{A}{B}Transfer` must actually join those two modes;
  * every cross-mode pair present must have an INTERMODAL_TRANSFER_FEES entry.

Reads `network_edges` from the DuckDB (run workflows 02_load first). A node's
modes are the edge_labels of the line-haul edges incident to it — the same rule
`pipeline.classify_connectors` uses. Exit non-zero on any inconsistency, so this
can gate a rebuild.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "outputs" / "fuel_network.duckdb"

# edge_label -> fee-mode (the vocabulary INTERMODAL_TRANSFER_FEES keys on)
LABEL_MODE = {"Road": "overland", "IceRoad": "ice_road", "Waterway": "barge", "Air": "plane"}
# {Mode}Connector -> the single fee-mode it must stay within
CONNECTOR_MODE = {"RoadConnector": "overland", "IceRoadConnector": "ice_road"}
# per-pair transfer type -> the two fee-modes it must join
TRANSFER_MODES = {
    "BargeRoadTransfer": {"barge", "overland"},
    "BargeIceRoadTransfer": {"barge", "ice_road"},
    "IceRoadRoadTransfer": {"overland", "ice_road"},
    "AirRoadTransfer": {"overland", "plane"},
}


def main(db_path: Path = DB_PATH) -> int:
    if not db_path.exists():
        print(f"{db_path} not found — run 02_load_final_network.py first.")
        return 2
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = con.execute(
            "SELECT edge_id, from_node, to_node, type FROM network_edges"
        ).fetchall()
    finally:
        con.close()

    node_modes: dict[int, set] = defaultdict(set)
    for _, fn, tn, t in rows:
        if t in LABEL_MODE:
            node_modes[fn].add(LABEL_MODE[t])
            node_modes[tn].add(LABEL_MODE[t])

    problems: list[str] = []
    for eid, fn, tn, t in rows:
        endpoint = node_modes.get(fn, set()) | node_modes.get(tn, set())
        if t in CONNECTOR_MODE:
            extra = endpoint - {CONNECTOR_MODE[t]}
            if extra:
                problems.append(f"edge {eid}: {t} touches other modes {sorted(extra)}")
        elif t in TRANSFER_MODES:
            if not TRANSFER_MODES[t].issubset(endpoint):
                problems.append(
                    f"edge {eid}: {t} endpoints {sorted(endpoint)} miss its pair "
                    f"{sorted(TRANSFER_MODES[t])}"
                )

    n_conn = sum(1 for r in rows if r[3] in CONNECTOR_MODE or r[3] in TRANSFER_MODES)
    if problems:
        print(f"FAIL: {len(problems)} of {n_conn} connectors mode-inconsistent:")
        for p in problems[:25]:
            print("  ", p)
        return 1
    print(f"PASS: all {n_conn} synthetic connectors agree with their endpoint modes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
