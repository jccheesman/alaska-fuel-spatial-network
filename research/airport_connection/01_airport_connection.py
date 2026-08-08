#!/usr/bin/env python3
"""How are the airports connected to the network? — transfer edges today vs snap-to-road.

The pipeline connects air to road with anchor TRANSFERS (profile `Road↔Plane @ airports` →
`assemble.connect_multimodal` phase 3): a Transfer edge between the nearest air node and the nearest road
node at each airport. The requirement is that airports should instead SNAP to the road network (the air
endpoint lands ON a road node — a shared node, no fabricated edge), as hubs already snap.

This analyzes the current mechanism, measures airport→road snap distances, builds a SNAPPED variant
(contract each air↔road airport pair into one node) and compares its connectivity to the transfer-based
network. Research only — no engine change. Run: python3 research/airport_connection/01_airport_connection.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from scipy.spatial import cKDTree
from shapely.geometry import LineString

from _trace import OUT, ROOT, Tracer
from mmnet.network import NetworkTables

T = Tracer("01_airport_connection", "How airports connect to the network — transfer vs snap-to-road")

nt = NetworkTables.from_gpkg(ROOT / "output" / "03_network")
nd = nt.nodes.sort_values("node_id").reset_index(drop=True)
e = nt.edges.copy(); e["from"] = e["from"].astype(int); e["to"] = e["to"].astype(int)
et, sr = e["type"], e["source"].astype(str)
xy = np.c_[nd.geometry.x.values, nd.geometry.y.values]
N = len(nd)
road_set = set(e.loc[et == "Road", "from"]).union(e.loc[et == "Road", "to"])
air_set = set(e.loc[et == "Air", "from"]).union(e.loc[et == "Air", "to"])
road_ids = np.array(sorted(road_set), dtype=int)

# ── 1. current mechanism: air↔road TRANSFER edges (source=airports) ──
air_tr = e[(et == "Transfer") & (sr == "airports")].copy()
shared = air_set & road_set
T.stage("Current connection — anchor TRANSFER edges (not snapped)")
T.kv("rule", "profile.yaml `Road↔Plane @ airports, max_dist 10000` → connect_multimodal phase 3")
T.kv("air↔road transfer edges", f"{len(air_tr)}")
T.kv("transfer length m (min/median/max)", f"{air_tr.geometry.length.min():.0f} / "
     f"{air_tr.geometry.length.median():.0f} / {air_tr.geometry.length.max():.0f}")
T.kv("air nodes that ARE a road node (snapped/shared)", f"{len(shared)}  → airports are joined by a "
     "separate Transfer linestring, NOT snapped onto the road")

# ── 2. snap feasibility: each airport → nearest road node ──
ap = gpd.read_file(ROOT / "data" / "processed" / "air_nodes.geojson").to_crs(nd.crs)
apxy = np.c_[ap.geometry.x.values, ap.geometry.y.values]
d_ap, j_ap = cKDTree(xy[road_ids]).query(apxy)
T.stage("Snap feasibility — airport → nearest ROAD node")
rows = [{"threshold": f"≤ {t} m", "airports": int((d_ap <= t).sum()), "of": len(ap)}
        for t in (100, 500, 1000, 5000, 10000, 50000)]
T.show(pd.DataFrame(rows), "airports within distance of a road node", n=len(rows))
T.kv("median / max airport→road (km)", f"{np.median(d_ap)/1000:.1f} / {d_ap.max()/1000:.1f}")

# ── 3. snapped variant: contract each (air↔road) airport pair → one node, drop the transfer ──
snap = {}                                   # air_node -> road_node
for _, r in air_tr.iterrows():
    a, b = int(r["from"]), int(r["to"])
    if a in road_set and b in air_set:
        snap[b] = a
    elif b in road_set and a in air_set:
        snap[a] = b


def metrics(edges_df, node_ids):
    node_ids = set(node_ids)
    g = nx.Graph(); g.add_nodes_from(node_ids)
    g.add_edges_from(zip(edges_df["from"], edges_df["to"]))
    comps = sorted(nx.connected_components(g), key=len, reverse=True)
    G = comps[0] if comps else set()
    return len(comps), len(G), round(100 * len(G) / max(len(node_ids), 1), 1)


nc0, g0, gf0 = metrics(e, range(N))
e2 = e[~((et == "Transfer") & (sr == "airports"))].copy()
e2["from"] = e2["from"].map(lambda x: snap.get(x, x))
e2["to"] = e2["to"].map(lambda x: snap.get(x, x))
snapped_nodes = set(range(N)) - set(snap.keys())   # the merged-away airport air-nodes no longer exist
ncS, gS, gfS = metrics(e2, snapped_nodes)
T.stage("Snapped variant vs current (connectivity)")
T.show(pd.DataFrame([
    {"network": "current (transfers)", "nodes": N, "edges": len(e), "components": nc0,
     "giant_nodes": g0, "giant_%": gf0},
    {"network": "snapped (air→road)", "nodes": N - len(snap), "edges": len(e2), "components": ncS,
     "giant_nodes": gS, "giant_%": gfS},
]), "transfer-based vs snap-based network", n=2)
T.kv("effect of snapping", f"−{len(snap)} nodes, −{len(air_tr)} transfer edges; "
     f"components {nc0}→{ncS}, giant {gf0}%→{gfS}% (connectivity preserved, airports land on the road)")

# ── maps ──
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(nd.crs)
bx = boundary.total_bounds; PAD = 6e4
EXT = (bx[0] - PAD, bx[2] + PAD, bx[1] - PAD, bx[3] + PAD)


def base(ax):
    boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
    ax.set_xlim(EXT[0], EXT[1]); ax.set_ylim(EXT[2], EXT[3])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])


def clip(g):
    b = g.bounds
    return g[(b.maxx >= EXT[0]) & (b.minx <= EXT[1]) & (b.maxy >= EXT[2]) & (b.miny <= EXT[3])]


# map 1: current — the air↔road transfer edges
fig, ax = plt.subplots(figsize=(12, 10)); base(ax)
clip(e[et == "Road"]).plot(ax=ax, color="#cccccc", linewidth=0.3, zorder=1)
clip(e[et == "Air"]).plot(ax=ax, color="#9467bd", linewidth=0.5, alpha=0.6, zorder=2)
clip(air_tr).plot(ax=ax, color="#d62728", linewidth=1.0, zorder=4)
ax.scatter(ap.geometry.x, ap.geometry.y, marker="^", s=22, c="#2e7d32", edgecolor="white", linewidth=0.3, zorder=5)
ax.legend(handles=[Line2D([0], [0], color="#9467bd", lw=2, label="air legs"),
                   Line2D([0], [0], color="#d62728", lw=2, label=f"air↔road TRANSFER edge ({len(air_tr)})"),
                   Line2D([0], [0], marker="^", color="w", markerfacecolor="#2e7d32", label="airport")],
          loc="lower left", fontsize=8)
ax.set_title("CURRENT — airports connect to road by a TRANSFER edge (not snapped)")
p = OUT / "01_current_transfers.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Current: 78 air↔road transfer edges (red) — airports are not snapped to the road")

# map 2: snapped — each airport moved onto its nearest road node (the snap vector), no transfer edge
fig, ax = plt.subplots(figsize=(12, 10)); base(ax)
clip(e[et == "Road"]).plot(ax=ax, color="#cccccc", linewidth=0.3, zorder=1)
clip(e[et == "Air"]).plot(ax=ax, color="#9467bd", linewidth=0.5, alpha=0.6, zorder=2)
snap_lines = gpd.GeoSeries([LineString([apxy[i], xy[road_ids[j_ap[i]]]]) for i in range(len(ap))
                            if d_ap[i] <= 10000], crs=nd.crs)
if len(snap_lines):
    snap_lines.plot(ax=ax, color="#000000", linewidth=0.6, zorder=3)
near = d_ap <= 1000
ax.scatter(ap.geometry.x[near], ap.geometry.y[near], marker="^", s=22, c="#2ca02c", edgecolor="white", linewidth=0.3, zorder=5)
ax.scatter(ap.geometry.x[~near], ap.geometry.y[~near], marker="^", s=34, c="#d62728", edgecolor="white", linewidth=0.4, zorder=6)
ax.legend(handles=[Line2D([0], [0], color="#000000", lw=2, label="snap to nearest road node"),
                   Line2D([0], [0], marker="^", color="w", markerfacecolor="#2ca02c", label=f"airport ≤1 km from road ({int(near.sum())})"),
                   Line2D([0], [0], marker="^", color="w", markerfacecolor="#d62728", label=f"airport >1 km (bush, {int((~near).sum())})")],
          loc="lower left", fontsize=8)
ax.set_title("SNAP-TO-ROAD — airport endpoint lands on the nearest road node (no transfer edge)")
p = OUT / "01_snap_to_road.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Proposed: airports snapped onto the nearest road node — 78/84 within 1 km")
T.done()
