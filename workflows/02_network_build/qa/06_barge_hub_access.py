#!/usr/bin/env python3
"""Barge-hub access report: topology only, after the network is assembled.

For every barge-coded hub (delivery_method contains Barge) of the just-built
stage-03 network: does it have a barge transfer (BargeRoadTransfer /
BargeIceRoadTransfer / BargeAirTransfer) within the profile's transfer reach,
and a waterway node within that reach? With the water-class label present,
adds the hub's distance to the nearest marine pixel and its nearshore tier.

Writes reports/barge_hub_access.csv under the mmnet project directory. A hub
failing BOTH checks fails the stage UNLESS listed (by community) in
inputs/network_qc/accepted_barge_exceptions.csv — so a NEW unreachable barge
hub fails the build while known cases stay listed until fixed. No rasters are
required (the tier column is blank without the label); runs on every machine.

Usage:  python workflows/02_network_build/qa/06_barge_hub_access.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import yaml
from scipy.spatial import cKDTree

import repo_paths as rp
from friction_surface.friction_paths import WATER_CLASS_TIF

GATE_EXIT = 3
OUT_DIR = rp.NETWORK_PROJECT / "output"
REPORTS = rp.NETWORK_PROJECT / "reports"
EXCEPTIONS = rp.INPUTS / "network_qc" / "accepted_barge_exceptions.csv"
BARGE_TRANSFERS = {"BargeRoadTransfer", "BargeIceRoadTransfer", "BargeAirTransfer"}


def hub_exceptions() -> set[str]:
    if not EXCEPTIONS.exists():
        return set()
    with open(EXCEPTIONS, newline="") as fh:
        return {r["key"].strip().lower() for r in csv.DictReader(fh) if r["kind"] == "hub"}


def marine_distance_km(xs, ys):
    """Distance to the nearest marine pixel (fuel_network.geo_checks);
    NaN without the label."""
    from fuel_network.geo_checks import nearest_class_distance
    from friction_surface.friction_config import WATER_CLASS_MARINE
    wc = Path(WATER_CLASS_TIF)
    if not wc.exists():
        return [np.nan] * len(xs)
    return [nearest_class_distance(wc, x, y, WATER_CLASS_MARINE)[0]
            for x, y in zip(xs, ys)]


def tier(d):
    if np.isnan(d):
        return ""
    if d <= 2:
        return "nearshore_coastal"
    if d <= 15:
        return "nearshore_marine_15km"
    if d <= 25:
        return "borderline"
    return "inland_or_river"


def main() -> int:
    nodes_p = OUT_DIR / "03_network__nodes.gpkg"
    edges_p = OUT_DIR / "03_network__edges.gpkg"
    if not nodes_p.exists() or not edges_p.exists():
        print(f"GATE: {nodes_p} absent — run the build first")
        return GATE_EXIT
    prof = yaml.safe_load(Path(rp.NETWORK_PROFILE).read_text())
    reach = max(t["max_dist"] for t in prof.get("transfers", [])
                if "Barge" in (t.get("from_mode"), t.get("to_mode")))

    nodes = gpd.read_file(nodes_p)
    edges = gpd.read_file(edges_p)
    nodes["x"] = nodes.geometry.x
    nodes["y"] = nodes.geometry.y
    hubs = nodes[nodes.is_hub & nodes.delivery_method.astype(str).str.contains("Barge", na=False)]
    print(f"{len(hubs)} barge-coded hubs; transfer reach {reach:.0f} m")

    ww_nodes = pd.unique(pd.concat([edges.loc[edges["type"] == "Waterway", "from"],
                                    edges.loc[edges["type"] == "Waterway", "to"]]))
    nxy = nodes.set_index("node_id")[["x", "y"]]
    ww_tree = cKDTree(nxy.loc[ww_nodes].values)
    tr = edges[edges["type"].isin(BARGE_TRANSFERS)]
    tr_mid = np.array([[g.centroid.x, g.centroid.y] for g in tr.geometry]) \
        if len(tr) else np.empty((0, 2))
    tr_tree = cKDTree(tr_mid) if len(tr_mid) else None

    d_ww, _ = ww_tree.query(hubs[["x", "y"]].values)
    n_tr = [len(tr_tree.query_ball_point(p, reach + 1000)) if tr_tree else 0
            for p in hubs[["x", "y"]].values]
    mar = marine_distance_km(hubs.x.values, hubs.y.values)

    rep = pd.DataFrame({
        "hub_id": hubs.hub_id.values,
        "x": hubs.x.values, "y": hubs.y.values,
        "dist_waterway_node_km": np.round(d_ww / 1000, 2),
        "waterway_in_reach": d_ww <= reach,
        "barge_transfers_in_reach": n_tr,
        "marine_dist_km": np.round(mar, 2),
        "tier": [tier(d) for d in mar],
    })
    rep["fails"] = (~rep.waterway_in_reach) & (rep.barge_transfers_in_reach == 0)
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "barge_hub_access.csv"
    rep.sort_values(["fails", "dist_waterway_node_km"], ascending=False).to_csv(out, index=False)
    print(f"wrote {out}: {int(rep.fails.sum())} hub(s) with no barge transfer and "
          f"no waterway node within reach")

    # a NEW failure (not in the accepted-exception list) fails the stage; the
    # exception list keys by community, resolved through 02_hubs.gpkg
    hubs_gpkg = gpd.read_file(OUT_DIR / "02_hubs.gpkg", ignore_geometry=True) \
        if (OUT_DIR / "02_hubs.gpkg").exists() else None
    comm_of = (hubs_gpkg.set_index("hub_id").hub_community.to_dict()
               if hubs_gpkg is not None else {})
    excused = hub_exceptions()
    new_fail = []
    for _, r in rep[rep.fails].iterrows():
        label = str(comm_of.get(r.hub_id, "") or r.hub_id)
        if label.strip().lower() not in excused:
            new_fail.append(label)
    if new_fail:
        print(f"FAIL: NEW unreachable barge hub(s), not in {EXCEPTIONS.name}: {new_fail}")
        return 1
    print("PASS: every unreachable barge hub is a listed, accepted exception")
    return 0


if __name__ == "__main__":
    sys.exit(main())
