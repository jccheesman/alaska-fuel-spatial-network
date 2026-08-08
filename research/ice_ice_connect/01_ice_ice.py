#!/usr/bin/env python3
"""STEP 01 — ice↔ice: are the 47 ice components separate trail systems or noding gaps?

Mirrors the road↔road study, within the IceRoad mode: measure the closest approach between ice
components, map the closest candidate gaps, and sweep the merge distance to find where (if anywhere) the
ice-component count knees. Run: python3 research/ice_ice_connect/01_ice_ice.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from shapely.geometry import LineString

from _trace import OUT, ROOT, Tracer
from ii_core import component_min_distances, load_network, merge_at, mode_components

T = Tracer("01_ice_ice", "STEP 01 — Ice ↔ ice connection study")
nodes, edges, xy = load_network()
ice, ids, comps, comp_of = mode_components(edges, "IceRoad")
sizes = np.array([len(c) for c in comps])
T.kv("ice nodes / components", f"{len(ids):,} / {len(comps)}")
T.kv("component sizes (top 10)", sizes[:10].tolist())
T.note("One 728-node giant + 46 small components. Unlike roads (sub-metre noding gaps), the ice network "
       "is already well-noded internally; the question is whether the SEPARATE trail systems should join.")

T.stage("Closest approach between ice components")
cc = component_min_distances(ids, xy, comp_of)
pairs = sorted(cc.items(), key=lambda kv: kv[1][0])
T.kv("component-pairs within k-NN reach", len(cc))
T.kv("closest pair distance", f"{pairs[0][1][0]:.1f} m")
prow = [{"comp_a": a, "comp_b": b, "gap_m": round(v[0], 1),
         "size_a": len(comps[a]), "size_b": len(comps[b])} for (a, b), v in pairs[:14]]
T.show(pd.DataFrame(prow), "closest 14 ice-component pairs", n=14)
gapvals = np.array([v[0] for v in cc.values()])
for lab, lo, hi in [("≤ 100 m", 0, 100), ("100–300 m", 100, 300), ("300–500 m", 300, 500),
                    ("500 m–1 km", 500, 1000), ("1–5 km", 1000, 5000), ("> 5 km", 5000, np.inf)]:
    T.kv(f"pairs with gap {lab}", int(((gapvals >= lo) & (gapvals < hi)).sum()))

# ---------------------------------------------------------------- candidate maps
T.stage("Candidate maps — the closest ice↔ice gaps")
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(nodes.crs)
cand = [(k, v) for k, v in pairs if v[0] <= 2000][:8]
for rank, ((a, b), (d, fn, tn)) in enumerate(cand, 1):
    pa, pb = xy[fn], xy[tn]
    pad = max(d * 3, 1500)
    ext = (min(pa[0], pb[0]) - pad, max(pa[0], pb[0]) + pad, min(pa[1], pb[1]) - pad, max(pa[1], pb[1]) + pad)
    win = (slice(ext[0], ext[1]), slice(ext[2], ext[3]))
    fig, ax = plt.subplots(figsize=(8, 7))
    ice.cx[win].plot(ax=ax, color="#bfe9f2", linewidth=1.0, zorder=1)
    ice[ice["from"].map(comp_of) == a].cx[win].plot(ax=ax, color="#17becf", linewidth=1.8, zorder=2)
    ice[ice["from"].map(comp_of) == b].cx[win].plot(ax=ax, color="#9467bd", linewidth=1.8, zorder=2)
    gpd.GeoSeries([LineString([pa, pb])], crs=nodes.crs).plot(ax=ax, color="#d62728", linewidth=2.0,
                                                              linestyle="--", zorder=4)
    ax.scatter(*pa, s=55, c="#17becf", edgecolor="k", zorder=5, label=f"comp {a} ({len(comps[a])})")
    ax.scatter(*pb, s=55, c="#9467bd", edgecolor="k", zorder=5, label=f"comp {b} ({len(comps[b])})")
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.legend(loc="lower left", fontsize=8)
    ax.set_title(f"#{rank}  comp {a} ↔ comp {b} — gap {d:,.0f} m")
    p = OUT / f"01_cand_{rank:02d}.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
    T.image(p, f"#{rank} comp {a} ↔ {b}, gap {d:,.0f} m")

# ---------------------------------------------------------------- distance sweep
T.stage("Distance that minimizes ice components")
grid = sorted(set(list(range(50, 500, 25)) + list(range(500, 2000, 100)) +
                  list(range(2000, 5000, 500)) + [5000, 7500, 10000, 20000, 50000]))
rows = [{"dist_m": t, **dict(zip(["ice_components", "giant", "giant_pct"],
        (lambda r: (r[0], r[1], round(r[2] * 100, 1)))(merge_at(comps, cc, t))))} for t in grid]
df = pd.DataFrame(rows); df.to_csv(OUT / "ice_optimize.csv", index=False)
for d in [100, 300, 500, 1000, 2000, 5000, 50000]:
    r = df[df["dist_m"] == d].iloc[0]
    T.kv(f"{d:>6} m", f"{int(r['ice_components']):>3} components | giant {r['giant_pct']:.0f}%")

x = np.log10(df["dist_m"].to_numpy(float)); y = df["ice_components"].to_numpy(float)
xn = (x - x.min()) / (x.max() - x.min()); yn = (y - y.min()) / (y.max() - y.min())
chord = yn[0] + (yn[-1] - yn[0]) * (xn - xn[0]) / (xn[-1] - xn[0])
elbow_i = int(np.argmax(chord - yn)); elbow_d = int(df["dist_m"].iloc[elbow_i])
gain = abs(chord - yn).max()
T.kv("elbow distance", f"{elbow_d:,} m  (knee strength {gain:.2f} — low ⇒ no sharp knee)")
T.note("The ice curve declines GRADUALLY with no sharp knee: the components are separate trail systems "
       "spread across a continuum of distances (65 m to 50 km+), not a swarm of noding gaps like roads. "
       "There is no single 'natural' merge distance; only a handful of sub-300 m pairs look like true gaps.")

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.plot(df["dist_m"], df["ice_components"], "-o", ms=3, color="#17becf")
ax.axvline(elbow_d, color="#d62728", ls="--", lw=1.2, label=f"elbow ≈ {elbow_d:,} m (weak)")
ax.set_xscale("log"); ax.set_xlabel("merge distance (m, log)"); ax.set_ylabel("ice components")
ax.set_title(f"Ice components vs merge distance (47 → {int(df['ice_components'].iloc[-1])} at 50 km; "
             "gradual, no sharp knee)")
ax.legend(fontsize=8)
p = OUT / "01_ice_optimize.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Ice components vs merge distance — gradual decline, separate trail systems")
T.note("Verdict in FINDINGS.md: ice↔ice has no noding-gap swarm to weld; keep ice components separate "
       "(they connect to the network through road via the road↔ice bridge, the next study).")
T.done()
