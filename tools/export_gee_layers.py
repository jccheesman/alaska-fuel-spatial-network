#!/usr/bin/env python3
"""Export the built network + hub triage as GEE-ready vector layers (EPSG:4326).

Reads the stage-02 build outputs and the triage worksheet, computes per-hub
reachability + distance to the nearest in-giant node (any mode) and the nearest
in-giant WATERWAY node, and writes GeoJSON layers plus a Code Editor script
scaffold under outputs/analysis/gee/.

The waterway-distance columns are the ones that test "is the snap/connect
distance too low for Alaska": an unreachable coastal hub whose nearest in-giant
marine node is, say, 8 km away cannot be joined by the 2 km connect-to-giant or
5 km barge transfer — the gap, not the geography, is the blocker.

Usage:
    python tools/export_gee_layers.py
"""
from __future__ import annotations

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

import repo_paths as rp

OUT = rp.NETWORK_PROJECT / "output"
GEE = rp.ANALYSIS / "gee"
TRIAGE = rp.ANALYSIS / "hub_triage_2026-10-15.csv"
WGS84 = 4326


def _nearest_km(pts_xy: np.ndarray, tree_xy: np.ndarray) -> np.ndarray:
    """Nearest-neighbour distance (km) from each point to a set, in projected metres."""
    if len(tree_xy) == 0 or len(pts_xy) == 0:
        return np.full(len(pts_xy), np.nan)
    d, _ = cKDTree(tree_xy).query(pts_xy, k=1)
    return np.round(d / 1000.0, 2)


def main() -> None:
    from mmnet.network import NetworkTables

    GEE.mkdir(parents=True, exist_ok=True)
    nt = NetworkTables.from_gpkg(OUT / "03_network")
    nodes = nt.nodes.copy()
    edges = nt.edges.copy()
    edges["from"] = edges["from"].astype(int)
    edges["to"] = edges["to"].astype(int)

    # giant component + per-node membership
    g = nx.Graph()
    g.add_edges_from(zip(edges["from"], edges["to"]))
    giant = max(nx.connected_components(g), key=len) if g.number_of_nodes() else set()
    nodes["node_id"] = nodes["node_id"].astype(int)
    nodes["in_giant"] = nodes["node_id"].isin(giant)

    # node coordinate table (EPSG:3338 metres) for distance maths
    nxy = np.c_[nodes.geometry.x.to_numpy(), nodes.geometry.y.to_numpy()]
    nid = nodes["node_id"].to_numpy()
    id2row = {int(i): r for r, i in enumerate(nid)}

    # waterway nodes, and the in-giant subset
    wat_ids = set(edges[edges["type"] == "Waterway"]["from"]) | set(edges[edges["type"] == "Waterway"]["to"])
    giant_xy = nxy[[id2row[i] for i in giant if i in id2row]]
    giant_wat_xy = nxy[[id2row[i] for i in (wat_ids & giant) if i in id2row]]

    # ---- hubs: centroid geometry for ALL hubs (placed or not) ----
    hubs = gpd.read_file(OUT / "02_hubs.gpkg")
    snaps = pd.read_csv(OUT / "02_hub_snaps.csv")
    hubs = hubs.merge(snaps[["hub_id", "node_id", "snap_dist_m", "status"]], on="hub_id", how="left")
    hubs["reachable"] = hubs["node_id"].map(
        lambda n: (int(n) in giant) if pd.notna(n) else False
    )
    hxy = np.c_[hubs.geometry.x.to_numpy(), hubs.geometry.y.to_numpy()]
    hubs["km_to_any_giant"] = _nearest_km(hxy, giant_xy)
    hubs["km_to_marine_giant"] = _nearest_km(hxy, giant_wat_xy)
    hubs["snap_km"] = (hubs["snap_dist_m"] / 1000).round(2)

    # a hub is a "problem" by its own build state: unplaced, merged away, or placed
    # but not in the giant. (Do NOT key off a prior triage file — hub_ids renumber
    # every build, so that list goes stale the moment the network is rebuilt.)
    st = hubs["status"].astype(str)
    hubs["is_problem"] = st.str.startswith("unplaced") | st.str.startswith("merged") | (~hubs["reachable"])
    # GEE filters compare against numbers, not booleans — emit 0/1, not True/False.
    for c in ("reachable", "is_problem"):
        hubs[c] = hubs[c].astype(int)

    keep = [
        "hub_id", "hub_kind", "hub_type", "hub_community", "delivery_method",
        "num_facilities", "total_hub_capacity", "status", "reachable", "snap_km",
        "km_to_any_giant", "km_to_marine_giant", "is_problem", "proposed_bucket",
    ]
    keep = [c for c in keep if c in hubs.columns] + ["geometry"]
    hubs_out = hubs[keep].to_crs(WGS84)
    hubs_out.to_file(GEE / "hubs_all.geojson", driver="GeoJSON")
    hubs_out[hubs_out["is_problem"] == 1].to_file(GEE / "hub_triage.geojson", driver="GeoJSON")

    # ---- network edges (mode + giant membership), reprojected ----
    edges["in_giant"] = (edges["from"].isin(giant) & edges["to"].isin(giant)).astype(int)
    ecols = [c for c in ["edge_id", "type", "source", "in_giant"] if c in edges.columns] + ["geometry"]
    ew = edges[ecols].to_crs(WGS84)
    ew.to_file(GEE / "network_edges.geojson", driver="GeoJSON")
    # the marine network alone (the layer the unreachable coastal hubs must reach)
    ew[ew["type"] == "Waterway"].to_file(GEE / "network_waterway.geojson", driver="GeoJSON")

    # ---- report ----
    print(f"wrote -> {GEE.relative_to(rp.ROOT)}/")
    for f in sorted(GEE.glob("*.geojson")):
        print(f"  {f.name:28} {f.stat().st_size/1e6:6.1f} MB")
    prob = hubs[hubs["is_problem"] == 1]
    print(f"\nproblem hubs: {len(prob)}")
    print("gap to nearest in-giant MARINE node (km) — tests the snap/connect distance:")
    print(prob["km_to_marine_giant"].describe().round(1).to_string())
    near = prob[prob["km_to_marine_giant"] <= 25]
    print(f"\n{len(near)}/{len(prob)} problem hubs are within 25 km of the marine giant "
          f"(would link if the barge/connect distance reached that far):")
    cols = [c for c in ["hub_id", "hub_community", "delivery_method", "km_to_marine_giant", "km_to_any_giant"] if c in near.columns]
    print(near.sort_values("km_to_marine_giant")[cols].head(40).to_string(index=False))


if __name__ == "__main__":
    main()
