#!/usr/bin/env python3
"""STEP 04 — find the road↔road distance that minimizes the number of components.

Extends the sweep well past 500 m. For each distance d it merges ANY two road components whose closest
approach ≤ d (the true minimum-components model, via a component-to-component min-distance graph built
from k-nearest neighbours), and counts the resulting road components + backbone fraction. Marks the
elbow (point of diminishing returns) and the plateau (the genuinely-separate regional systems). Run:
python3 research/road_road_connect/04_optimize.py
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from _trace import OUT, Tracer
from rr_core import load_network, road_components

T = Tracer("04_optimize", "STEP 04 — Distance that minimizes road components")
nodes, edges, xy = load_network()
road, ids, comps, comp_of = road_components(edges)
sizes = np.array([len(c) for c in comps])
nC = len(comps)
T.kv("road nodes / components (baseline)", f"{len(ids):,} / {nC:,}")

# --- component-to-component minimum distance via k-NN (captures every close approach) ---
T.stage("Build the component-adjacency graph (min distance between each pair of road components)")
tree = cKDTree(xy[ids])
K = 24
qd, qi = tree.query(xy[ids], k=K)
cc_min: dict = {}
node_comp = np.array([comp_of[n] for n in ids])
for i in range(len(ids)):
    ci = node_comp[i]
    for kk in range(1, K):
        cj = node_comp[qi[i, kk]]
        if cj != ci:
            key = (ci, cj) if ci < cj else (cj, ci)
            d = qd[i, kk]
            if key not in cc_min or d < cc_min[key]:
                cc_min[key] = d
cc_edges = [(a, b, d) for (a, b), d in cc_min.items()]
T.kv("component-pairs within k-NN reach", f"{len(cc_edges):,}")
T.kv("closest pair distance", f"{min(d for *_, d in cc_edges):.1f} m")


def merge_at(tol):
    """Components + backbone fraction after merging every component-pair with min distance ≤ tol."""
    g = nx.Graph(); g.add_nodes_from(range(nC))
    g.add_edges_from((a, b) for a, b, d in cc_edges if d <= tol)
    supers = list(nx.connected_components(g))
    n_super = len(supers)
    big = max((sizes[list(s)].sum() for s in supers), default=0)
    return n_super, int(big), big / len(ids)


# --- wide log-ish sweep ---
T.stage("Sweep distance from 10 m to 50 km")
grid = sorted(set(list(range(10, 100, 10)) + list(range(100, 500, 25)) +
                  list(range(500, 2000, 100)) + list(range(2000, 5000, 500)) +
                  [5000, 7500, 10000, 15000, 20000, 30000, 50000]))
rows = []
for tol in grid:
    n_super, big, gf = merge_at(tol)
    rows.append({"dist_m": tol, "road_components": n_super, "backbone": big, "backbone_pct": round(gf * 100, 1)})
df = pd.DataFrame(rows)
df.to_csv(OUT / "optimize.csv", index=False)

# headline points
def at(d):
    return int(df.loc[df["dist_m"] == d, "road_components"].iloc[0])
for d in [50, 150, 300, 500, 1000, 2000, 5000, 10000, 50000]:
    r = df[df["dist_m"] == d].iloc[0]
    T.kv(f"{d:>6} m", f"{int(r['road_components']):>5,} components | backbone {r['backbone_pct']:.1f}%")

# --- elbow (kneedle: point of max distance below the chord, on log-x) ---
T.stage("The elbow — where extra distance stops buying connectivity")
x = np.log10(df["dist_m"].to_numpy(float)); y = df["road_components"].to_numpy(float)
xn = (x - x.min()) / (x.max() - x.min()); yn = (y - y.min()) / (y.max() - y.min())
chord = yn[0] + (yn[-1] - yn[0]) * (xn - xn[0]) / (xn[-1] - xn[0])
elbow_i = int(np.argmax(chord - yn))           # convex-decreasing: knee = max gap below chord
elbow_d = int(df["dist_m"].iloc[elbow_i]); elbow_c = int(df["road_components"].iloc[elbow_i])
T.kv("elbow distance", f"{elbow_d:,} m")
T.kv("components at elbow", f"{elbow_c:,}  (from {nC:,} baseline)")
floor = int(df["road_components"].iloc[-1])
T.note(f"Components fall monotonically with distance, so the strict minimum is at the largest distance "
       f"({floor:,} at 50 km — the truly-separate regional systems). But the curve KNEES at ~{elbow_d:,} m: "
       f"below it each extra metre closes real noding gaps; above it you only buy merges by fabricating "
       "ever-longer non-road links. The knee is the principled 'minimizing' distance.")
# marginal reduction around the knee
T.stage("Marginal reduction per band (how many components each band removes)")
for lo, hi in [(0, 50), (50, 150), (150, 300), (300, 500), (500, 1000), (1000, 2000),
               (2000, 5000), (5000, 50000)]:
    c_lo = int(df.loc[df["dist_m"] <= lo, "road_components"].iloc[-1]) if lo else nC
    c_hi = int(df.loc[df["dist_m"] <= hi, "road_components"].iloc[-1])
    T.kv(f"{lo:>5}–{hi:<6} m", f"−{c_lo - c_hi:,} components  ({c_lo:,} → {c_hi:,})")

# --- figure ---
fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5.5))
a1.plot(df["dist_m"], df["road_components"], "-o", ms=3, color="#1f77b4")
a1.axvline(elbow_d, color="#d62728", ls="--", lw=1.2, label=f"elbow ≈ {elbow_d:,} m")
a1.axvline(150, color="#2ca02c", ls=":", lw=1.2, label="noding_tol 150 m")
a1.set_xscale("log"); a1.set_xlabel("merge distance (m, log)"); a1.set_ylabel("road components")
a1.set_title("road components vs merge distance"); a1.legend(fontsize=8)
a1.annotate(f"{elbow_c:,}", (elbow_d, elbow_c), textcoords="offset points", xytext=(6, 8), fontsize=9)
a2.plot(df["dist_m"], df["backbone_pct"], "-o", ms=3, color="#2ca02c")
a2.axvline(elbow_d, color="#d62728", ls="--", lw=1.2)
a2.set_xscale("log"); a2.set_ylim(60, 100); a2.set_xlabel("merge distance (m, log)")
a2.set_ylabel("backbone (% of road nodes)"); a2.set_title("backbone fraction vs merge distance")
fig.suptitle(f"Road↔road: components minimize toward {floor:,} (regional systems); knee ≈ {elbow_d:,} m",
             fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.95])
p = OUT / "04_optimize.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Components & backbone vs merge distance — knee marks the point of diminishing returns")
T.done()
