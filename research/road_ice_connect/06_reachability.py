#!/usr/bin/env python3
"""STEP 06 — backbone reachability vs tolerance (road + ice only).

The decisive evidence that short proximity links cannot connect the ice network: applying BOTH ice↔ice
and road↔ice at a common tolerance, how many of the 931 ice nodes ever reach the road backbone? Even at
10 km it is only ~2% — the ice is genuinely fragmented and the big Barrow system (55 km out) never chains
in. Run: python3 research/road_ice_connect/06_reachability.py
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from _trace import OUT, Tracer
from bridge_core import load_network, mode_node_ids

T = Tracer("06_reachability", "STEP 06 — Ice → road-backbone reachability vs tolerance")
nodes, edges, xy = load_network()
ice = edges[edges["type"] == "IceRoad"]
iids = np.array(sorted(set(ice["from"]).union(ice["to"])))
road = edges[edges["type"] == "Road"]
rids = np.array(sorted(set(road["from"]).union(road["to"])))
# backbone = largest road component (raw); plus road↔road weld would only grow it slightly, so raw is fine
gr = nx.Graph(); gr.add_nodes_from(rids.tolist()); gr.add_edges_from(zip(road["from"], road["to"]))
rcomps = sorted(nx.connected_components(gr), key=len, reverse=True)
rcomp_of = {n: i for i, c in enumerate(rcomps) for n in c}
N_ICE = len(iids)


def reach(T_m):
    """Ice nodes connected to the road backbone after ice↔ice + road↔ice at tolerance T_m."""
    G = nx.Graph(); G.add_nodes_from(iids.tolist())
    G.add_edges_from(zip(ice["from"], ice["to"]))
    it = cKDTree(xy[iids])
    for a, b in it.query_pairs(T_m):                       # ice↔ice within T
        G.add_edge(int(iids[a]), int(iids[b]))
    rt = cKDTree(xy[rids]); d, idx = rt.query(xy[iids])
    G.add_nodes_from(("R", rc) for rc in range(len(rcomps)))
    for k, inode in enumerate(iids):                       # road↔ice within T (to that road's component)
        if d[k] <= T_m:
            G.add_edge(int(inode), ("R", rcomp_of[int(rids[int(idx[k])])]))
    if ("R", 0) not in G:
        return 0
    comp = nx.node_connected_component(G, ("R", 0))
    return sum(1 for n in iids if n in comp)


grid = [250, 500, 1000, 2000, 3000, 5000, 7500, 10000]
rows = [{"tol_km": t / 1000, "ice_nodes_reaching_backbone": reach(t),
         "pct": round(100 * reach(t) / N_ICE, 1)} for t in grid]
df = pd.DataFrame(rows)
T.show(df, "ice nodes reaching the road backbone vs tolerance", n=len(df))
T.note(f"Ceiling ~{df['pct'].max():.0f}% even at 10 km: of {N_ICE} ice nodes, only "
       f"{int(df['ice_nodes_reaching_backbone'].max())} ever reach the backbone. The big Barrow system "
       "(728 nodes, 55 km from the Dalton) never chains in — short proximity links cannot connect the "
       "ice network to the road backbone. Raising the tolerance buys almost nothing.")

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.plot(df["tol_km"], df["pct"], "-o", color="#17becf")
for x, y in zip(df["tol_km"], df["pct"]):
    ax.text(x, y + 0.4, f"{y:.0f}%", ha="center", fontsize=8)
ax.set_ylim(0, 100); ax.set_xlabel("ice↔ice + road↔ice tolerance (km)")
ax.set_ylabel("% of ice nodes reaching the road backbone")
ax.set_title("Ice → road-backbone reachability is capped at ~2% — the ice network is genuinely fragmented")
p = OUT / "06_reachability.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Reachability vs tolerance — flat ~2% ceiling; short links can't connect the ice to the backbone")
df.to_csv(OUT / "reachability.csv", index=False)
T.done()
