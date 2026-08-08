#!/usr/bin/env python3
"""STEP 04 — the Deadhorse ice piece beside the Dalton Highway, to scale (road + ice only).

The southern ice-near-road point the user spotted is a SMALL separate ice component (~10 nodes) at
Deadhorse, 2.4 km from the Dalton Highway BACKBONE — skipped by the 500 m road↔ice tolerance. This zooms
on it with a scale bar and the 2.4 km connector drawn, confirming the near road is the backbone (not a
local grid). Run: python3 research/road_ice_connect/04_deadhorse_gap.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.lines import Line2D
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point

from _trace import OUT, ROOT, Tracer
from bridge_core import load_network, mode_node_ids

T = Tracer("04_deadhorse_gap", "STEP 04 — The Deadhorse ice piece and the Dalton backbone")
nodes, edges, xy = load_network()

# road components (raw, no weld) → the backbone is the largest; identify backbone road nodes
road = edges[edges["type"] == "Road"]
rids, _ = mode_node_ids(edges, "Road"), None
rids = sorted(set(road["from"]).union(road["to"]))
gr = nx.Graph(); gr.add_nodes_from(rids); gr.add_edges_from(zip(road["from"], road["to"]))
rcomps = sorted(nx.connected_components(gr), key=len, reverse=True)
backbone = set(rcomps[0])
back_road = np.array([n for n in rids if n in backbone])

# ice components (raw)
ice = edges[edges["type"] == "IceRoad"]
iids = sorted(set(ice["from"]).union(ice["to"]))
gi = nx.Graph(); gi.add_nodes_from(iids); gi.add_edges_from(zip(ice["from"], ice["to"]))
icomps = sorted(nx.connected_components(gi), key=len, reverse=True)

# find the ice component closest to the BACKBONE (excluding the ones already touching any road < 500 m)
tb = cKDTree(xy[back_road])
best = None
for c in icomps:
    arr = np.array(sorted(c))
    d, idx = tb.query(xy[arr]); j = int(np.argmin(d))
    gap = float(d[j])
    if 500 < gap < 10000:                       # close-but-skipped band
        if best is None or gap < best[0]:
            best = (gap, int(arr[j]), int(back_road[int(idx[j])]), c)
gap, iN, bN, comp = best
ll = lambda n: gpd.GeoSeries([Point(*xy[n])], crs=3338).to_crs(4326)[0]
T.kv("Deadhorse ice piece", f"{len(comp)} ice nodes")
T.kv("nearest BACKBONE road", f"{gap/1000:.2f} km  (ice {iN} {ll(iN).y:.2f}N {ll(iN).x:.2f}W → "
     f"backbone road {bN} {ll(bN).y:.2f}N {ll(bN).x:.2f}W)")
T.note("The near road IS the Dalton Highway backbone (largest road component). The 500 m road↔ice "
       "tolerance skipped this 2.4 km gap — a ≥2.5 km tolerance would connect this small piece.")

# ---- map, to scale ----
a, b = xy[iN], xy[bN]
pad = max(gap * 1.3, 2000)
ext = (min(a[0], b[0]) - pad, max(a[0], b[0]) + pad, min(a[1], b[1]) - pad, max(a[1], b[1]) + pad)
win = (slice(ext[0], ext[1]), slice(ext[2], ext[3]))
fig, ax = plt.subplots(figsize=(10, 8))
gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(nodes.crs).plot(
    ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
road_in_view = road.cx[win]
road_in_view[road_in_view["from"].isin(backbone)].plot(ax=ax, color="#222", linewidth=1.6, zorder=2)
road_in_view[~road_in_view["from"].isin(backbone)].plot(ax=ax, color="#e377c2", linewidth=1.2, zorder=2)
ice_comp = ice[ice["from"].isin(comp) | ice["to"].isin(comp)].cx[win]
ice_comp.plot(ax=ax, color="#17becf", linewidth=1.8, zorder=3)
gpd.GeoSeries([LineString([a, b])], crs=nodes.crs).plot(ax=ax, color="#d62728", linewidth=2.2,
                                                        linestyle="--", zorder=5)
ax.scatter(*a, s=70, c="#17becf", edgecolor="k", zorder=6)
ax.scatter(*b, s=90, c="#222", edgecolor="w", marker="s", zorder=6)
ax.annotate("Dalton Hwy (BACKBONE)", b, textcoords="offset points", xytext=(8, 6), fontsize=10)
ax.text(*(0.5 * (a + b) + [0, gap * 0.08]), f"{gap/1000:.1f} km", ha="center", color="#d62728",
        fontsize=12, fontweight="bold")
x0, y0 = ext[0] + pad * 0.3, ext[2] + pad * 0.3
ax.plot([x0, x0 + 1000], [y0, y0], color="k", linewidth=4); ax.text(x0 + 500, y0 + pad * 0.05, "1 km",
                                                                    ha="center", fontweight="bold")
ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
ax.legend(handles=[Line2D([0], [0], color="#17becf", lw=2, label=f"Deadhorse ice piece ({len(comp)} nodes)"),
                   Line2D([0], [0], color="#222", lw=2, label="Dalton Hwy (backbone)"),
                   Line2D([0], [0], color="#e377c2", lw=2, label="local oilfield grids (disconnected)"),
                   Line2D([0], [0], color="#d62728", lw=2, label=f"{gap/1000:.1f} km gap (skipped at 500 m)")],
          loc="lower left", fontsize=8)
ax.set_title(f"Deadhorse: a {len(comp)}-node ice piece sits {gap/1000:.1f} km from the Dalton backbone\n"
             "— connectable with a ≥2.5 km road↔ice tolerance (the 500 m rule skipped it)")
p = OUT / "04_deadhorse_gap.png"; fig.savefig(p, dpi=160, bbox_inches="tight"); plt.close(fig)
T.image(p, "Deadhorse ice piece 2.4 km from the Dalton backbone, to scale (1 km bar)")
T.done()
