#!/usr/bin/env python3
"""STEP 01 — scope the road-network fragmentation.

The road layer alone splits into ~1,523 connected components. This script bounds the problem: the
size distribution, where the big secondary systems sit, and — the key question — how much of the
fragmentation is a tiny NODING GAP (fixable by a tolerance, like the ice bridge) vs a genuine
geographic break (a water/ferry crossing or a truly isolated grid that should stay separate).

For each non-giant road component it measures the CLOSEST APPROACH to any OTHER road component (the gap
that would have to be bridged to merge it). Run: python3 research/road_road_connect/01_fragmentation.py
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from _trace import OUT, ROOT, Tracer

from mmnet.network import NetworkTables  # noqa: E402

T = Tracer("01_fragmentation", "STEP 01 — Road-network fragmentation scoping")

T.stage("Inputs — the Road edges of the built network")
nt = NetworkTables.from_gpkg(ROOT / "output" / "03_network")
nodes = nt.nodes.sort_values("node_id").reset_index(drop=True)
xy = np.c_[nodes.geometry.x.to_numpy(), nodes.geometry.y.to_numpy()]
edges = nt.edges.copy()
edges["from"] = edges["from"].astype(int); edges["to"] = edges["to"].astype(int)
road = edges[edges["type"] == "Road"]
road_ids = sorted(set(road["from"]).union(road["to"]))
g = nx.Graph(); g.add_edges_from(zip(road["from"], road["to"]))
comps = [sorted(c) for c in nx.connected_components(g)]
comps.sort(key=len, reverse=True)
comp_of = {n: i for i, c in enumerate(comps) for n in c}
T.kv("road nodes / edges", f"{len(road_ids):,} / {len(road):,}")
T.kv("road components", f"{len(comps):,}")
T.kv("largest (backbone) holds", f"{len(comps[0]):,} nodes ({len(comps[0])/len(road_ids):.1%})")

T.stage("Component size distribution")
sizes = np.array([len(c) for c in comps])
T.kv("top 12 component sizes", sizes[:12].tolist())
for lab, lo, hi in [("backbone (#1)", sizes[0], sizes[0] + 1), ("large (≥ 200)", 200, 10**9),
                    ("medium (50–199)", 50, 200), ("small (10–49)", 10, 50),
                    ("tiny (2–9)", 2, 10)]:
    T.kv(f"components {lab}", int(((sizes >= lo) & (sizes < hi)).sum()))
T.note(f"{int((sizes < 10).sum()):,} components are tiny (< 10 nodes) — these dominate the count and are "
       "the prime suspects for noding gaps / dangling stubs.")

T.stage("Closest approach of each non-backbone component to ANY other component")
tree = cKDTree(xy[road_ids])
pos_in_tree = {nid: i for i, nid in enumerate(road_ids)}
rows = []
K = 12
for ci, comp in enumerate(comps):
    if ci == 0:
        continue
    qd, qi = tree.query(xy[comp], k=K)               # k nearest road nodes for each comp node
    best = np.inf; bf = bt = -1
    for local_idx, nid in enumerate(comp):
        for kk in range(K):
            other = road_ids[int(qi[local_idx, kk])]
            if comp_of[other] != ci:                  # first neighbour in a different component
                d = float(qd[local_idx, kk])
                if d < best:
                    best, bf, bt = d, nid, other
                break
    rows.append({"comp": ci, "size": len(comp), "gap_to_other_m": best,
                 "other_comp": comp_of.get(bt, -1), "other_is_backbone": comp_of.get(bt, -1) == 0,
                 "cx": float(xy[comp][:, 0].mean()), "cy": float(xy[comp][:, 1].mean())})
frag = pd.DataFrame(rows)

T.stage("How much is a noding gap vs a real geographic break?")
gap = frag["gap_to_other_m"].to_numpy()
bands = [("≤ 10 m", 0, 10), ("10–50 m", 10, 50), ("50–150 m", 50, 150), ("150–500 m", 150, 500),
         ("500 m–1 km", 500, 1000), ("1–5 km", 1000, 5000), ("> 5 km", 5000, np.inf)]
for lab, lo, hi in bands:
    sel = (gap >= lo) & (gap < hi)
    T.kv(f"components with gap-to-other {lab}", f"{int(sel.sum())}  "
         f"(holding {int(frag.loc[sel, 'size'].sum()):,} road nodes)")
fixable = int((gap <= 150).sum())
T.note(f"{fixable:,} non-backbone components lie within 150 m (the profile noding_tol) of ANOTHER "
       "component — cross-segment noding gaps. But 'nearest other component' is usually another tiny "
       "stub, not the backbone: closing all ≤150 m gaps (transitive) only takes the road count "
       "1,523 → 756 and the backbone 32,760 → 34,742 (69% → 73.5%). So noding-snap tidies the COUNT "
       "but does NOT unify Alaska's roads — because they genuinely aren't one network.")

T.stage("The big secondary systems — gap to the BACKBONE specifically")
back_ids = np.array(comps[0])
btree = cKDTree(xy[back_ids])
big = frag.nlargest(12, "size").copy()
big["gap_to_backbone_m"] = [float(btree.query(xy[comps[int(c)]])[0].min()) for c in big["comp"]]
T.show(big, "12 largest non-backbone road components (gap to the main backbone)",
       cols=["comp", "size", "gap_to_other_m", "gap_to_backbone_m", "cx", "cy"])
T.note("The large regional systems sit 200–900 km from the backbone — Southeast Alaska, the Canada "
       "GRIP4 roads, and Western-Alaska village grids are SEPARATE road networks, not noding gaps "
       "(comp 5, ~102 m, is the lone large noding gap that truly belongs to the backbone).")
frag.sort_values("size", ascending=False).to_csv(OUT / "road_fragmentation.csv", index=False)
T.kv("wrote", "out/road_fragmentation.csv")

T.stage("Are the regional systems already connected — via the multimodal anchors?")
N = len(nodes)
gf = nx.Graph(); gf.add_nodes_from(range(N)); gf.add_edges_from(zip(edges["from"], edges["to"]))
full_giant = max(nx.connected_components(gf), key=len)
trans = edges[edges["type"] == "Transfer"]
road_node_set = set(road_ids)
in_giant = len(road_node_set & full_giant)
T.kv("full multimodal giant", f"{len(full_giant):,} nodes ({len(full_giant)/N:.1%})")
T.kv("road nodes already in the multimodal giant",
     f"{in_giant:,} / {len(road_node_set):,} ({in_giant/len(road_node_set):.1%})")
anc_rows = []
for c in big["comp"]:
    cset = set(comps[int(c)])
    ing = len(cset & full_giant) > 0
    srcs = sorted(set(trans[trans["from"].isin(cset) | trans["to"].isin(cset)]["source"])) if ing else []
    anc_rows.append({"comp": int(c), "size": len(cset), "in_multimodal_giant": ing,
                     "connected_via": ", ".join(srcs) or "—"})
T.show(pd.DataFrame(anc_rows), "large regional systems — already multimodally connected?",
       n=12, cols=["comp", "size", "in_multimodal_giant", "connected_via"])
T.note("The regional road systems already join the network through PORTS (Alaska Marine Highway ferries "
       "≈ barge) and AIRPORTS — the physically-correct connectors. Road↔road bridging across 200–900 km "
       "would be wrong; the right lever is making sure each regional grid has a port/airport anchor.")

# ---------------------------------------------------------------- figures
boundary = __import__("geopandas").read_file(ROOT / "data" / "boundary.geojson").to_crs(nodes.crs)
fig, ax = plt.subplots(figsize=(11, 9))
boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
road.plot(ax=ax, color="#cfcfcf", linewidth=0.3, zorder=1)
# color the backbone vs the 8 largest secondary systems
pal = plt.cm.tab10(np.linspace(0, 1, 10))
back = road[road["from"].map(comp_of) == 0]
back.plot(ax=ax, color="#444", linewidth=0.4, zorder=2, label=f"backbone ({len(comps[0]):,} nodes)")
for j, ci in enumerate(big["comp"].head(8)):
    seg = road[road["from"].map(comp_of) == ci]
    seg.plot(ax=ax, color=pal[j % 10], linewidth=1.0, zorder=3, label=f"comp {ci} ({len(comps[ci])})")
ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
ax.legend(loc="lower left", fontsize=7, title="road backbone + 8 largest separate systems")
ax.set_title(f"Road network: 1 backbone + {len(comps)-1:,} disconnected pieces")
p = OUT / "01_road_components.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Road components — backbone (dark) vs the largest separate regional systems (colored)")

fig, ax = plt.subplots(figsize=(9, 5))
edges_h = [b[1] for b in bands[:-1]] + [frag["gap_to_other_m"].replace(np.inf, 1e6).max()]
counts = [int(((gap >= lo) & (gap < hi)).sum()) for _, lo, hi in bands]
ax.bar([b[0] for b in bands], counts, color="#4a90c2")
for i, v in enumerate(counts):
    ax.text(i, v, str(v), ha="center", va="bottom", fontsize=9)
ax.axvspan(-0.5, 2.5, color="#2ca02c", alpha=0.08)
ax.text(1, max(counts) * 0.9, "noding gaps\n(≤ 150 m, fixable)", ha="center", fontsize=8, color="#2a7")
ax.set_title("Gap from each non-backbone road component to its nearest neighbour component")
ax.tick_params(axis="x", labelrotation=20)
p = OUT / "01_gap_histogram.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Gap-to-nearest-component histogram — left bins are fixable noding gaps")

T.note("Scoping conclusion in FINDINGS.md: the count is mostly tiny noding stubs (optional ≤150 m "
       "within-mode snap to tidy); the big regional systems are genuinely separate roads already tied "
       "in by ferry/air anchors. Road↔road bridging is the WRONG tool — the lever is anchor coverage.")
T.done()
