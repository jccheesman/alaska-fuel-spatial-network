#!/usr/bin/env python3
"""STEP 05 — the northern ice components, colored + labeled (road + ice only).

Shows the ice network is genuinely fragmented: the big Barrow system and the small Deadhorse piece are
SEPARATE, tens of km apart, each at a different distance from the Dalton backbone. Colors each northern
ice component and annotates its distance to the Barrow system and to the backbone.
Run: python3 research/road_ice_connect/05_northern_ice.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import Point

from _trace import OUT, ROOT, Tracer
from bridge_core import load_network

T = Tracer("05_northern_ice", "STEP 05 — Northern ice components, colored + labeled")
nodes, edges, xy = load_network()
road = edges[edges["type"] == "Road"]
rids = sorted(set(road["from"]).union(road["to"]))
gr = nx.Graph(); gr.add_nodes_from(rids); gr.add_edges_from(zip(road["from"], road["to"]))
backbone = max(nx.connected_components(gr), key=len)
back_road = np.array([n for n in rids if n in backbone])

ice = edges[edges["type"] == "IceRoad"]
iids = sorted(set(ice["from"]).union(ice["to"]))
gi = nx.Graph(); gi.add_nodes_from(iids); gi.add_edges_from(zip(ice["from"], ice["to"]))
icomps = sorted(nx.connected_components(gi), key=len, reverse=True)
giant = np.array(sorted(icomps[0]))

tb = cKDTree(xy[back_road]); tg = cKDTree(xy[giant])
ll = lambda n: gpd.GeoSeries([Point(*xy[n])], crs=3338).to_crs(4326)[0]
# northern = components whose centroid latitude > 69N
rows = []
for k, c in enumerate(icomps):
    arr = np.array(sorted(c))
    cen = gpd.GeoSeries([Point(*xy[arr].mean(0))], crs=3338).to_crs(4326)[0]
    if cen.y < 69:
        continue
    db = float(tb.query(xy[arr])[0].min())
    dg = 0.0 if k == 0 else float(tg.query(xy[arr])[0].min())
    rows.append({"comp": k, "nodes": len(c), "to_backbone_km": round(db / 1000, 1),
                 "to_barrow_km": round(dg / 1000, 1), "lat": round(cen.y, 2), "lon": round(cen.x, 2)})
tab = pd.DataFrame(rows).sort_values("nodes", ascending=False)
T.show(tab, "northern ice components (lat > 69°N)", n=len(tab))
T.note("The big Barrow system (comp 0) is 55 km from the Dalton backbone; the Deadhorse piece is 2.4 km "
       "from the backbone but 57 km from Barrow. They are SEPARATE ice systems — connecting one does not "
       "connect the other.")

# ---- map ----
ext = (-180000, 240000, 2120000, 2380000)
win = (slice(ext[0], ext[1]), slice(ext[2], ext[3]))
fig, ax = plt.subplots(figsize=(13, 8))
gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(nodes.crs).plot(
    ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
road.cx[win].plot(ax=ax, color="#bbb", linewidth=0.5, zorder=1)
road[road["from"].isin(backbone)].cx[win].plot(ax=ax, color="#222", linewidth=1.0, zorder=2)
cmap = plt.cm.tab20(np.linspace(0, 1, 20))
for i, r in enumerate(tab.itertuples()):
    seg = ice[ice["from"].isin(icomps[r.comp]) | ice["to"].isin(icomps[r.comp])].cx[win]
    col = "#17becf" if r.comp == 0 else cmap[i % 20]
    seg.plot(ax=ax, color=col, linewidth=1.6 if r.comp == 0 else 1.3, zorder=3)
    arr = np.array(sorted(icomps[r.comp])); cx, cy = xy[arr].mean(0)
    ax.annotate(f"{r.nodes}n · {r.to_backbone_km}km→bb", (cx, cy), fontsize=7,
                ha="center", color="#333")
ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
ax.set_title("Northern ice components (labels: nodes · km to the Dalton backbone). Dark = backbone road.\n"
             "Big Barrow system 55 km out; small Deadhorse piece 2.4 km out — separate systems, 57 km apart")
p = OUT / "05_northern_ice.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Northern ice components colored, labeled by node count and distance to the Dalton backbone")
T.done()
