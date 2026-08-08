#!/usr/bin/env python3
"""STEP 02 — road↔road candidate gap maps (see that the close gaps are real noding gaps).

For a spread of the closest road-component gaps, draw a zoomed map: the two road components (orange =
the stub, dark = its neighbour / backbone) and the proposed connector (red dashed). A noding gap looks
like two road ends that almost touch; a real break looks like a river/water span. Run:
python3 research/road_road_connect/02_candidates_map.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from shapely.geometry import LineString

from _trace import OUT, ROOT, Tracer
from rr_core import closest_connectors, load_network, road_components

T = Tracer("02_candidates", "STEP 02 — Road↔road candidate gap maps")
nodes, edges, xy = load_network()
road, ids, comps, comp_of = road_components(edges)
conns = closest_connectors(ids, xy, comps, comp_of)
T.kv("non-backbone road components", len(conns))

# sample across the gap range so the maps show both near-touches and the boundary of plausibility
buckets = [("≤ 10 m", 0, 10), ("10–50 m", 10, 50), ("50–150 m", 50, 150),
           ("150–500 m", 150, 500), ("500 m–1 km", 500, 1000)]
sample = []
for lab, lo, hi in buckets:
    band = [c for c in conns if lo <= c["gap_m"] < hi]
    band = sorted(band, key=lambda c: -c["size"])[:2]      # 2 largest stubs per band
    for c in band:
        sample.append((lab, c))
T.kv("candidate maps to render", len(sample))


def line(c):
    return LineString([xy[c["from_node"]], xy[c["to_node"]]])


# ---------------------------------------------------------------- overview
T.stage("Overview — where the closest road gaps are")
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(nodes.crs)
close = [c for c in conns if c["gap_m"] <= 150]
fig, ax = plt.subplots(figsize=(11, 9))
boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
road.plot(ax=ax, color="#cfcfcf", linewidth=0.3, zorder=1)
if close:
    gpd.GeoSeries([line(c) for c in close], crs=nodes.crs).plot(ax=ax, color="#d62728",
                                                                linewidth=1.2, zorder=4)
ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
ax.legend(handles=[Line2D([0], [0], color="#d62728", lw=2, label=f"{len(close)} gaps ≤ 150 m"),
                   Line2D([0], [0], color="#cfcfcf", lw=2, label="roads")],
          loc="lower left", fontsize=8, title="road↔road noding gaps")
ax.set_title(f"Road↔road gaps ≤ 150 m ({len(close)} of {len(conns)} non-backbone components)")
p = OUT / "02_overview.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Overview — the ≤150 m road-road gaps (red); these are cross-segment noding gaps")

# ---------------------------------------------------------------- per-candidate zooms
T.stage("Per-candidate zooms — is it a noding gap or a real break?")
for rank, (lab, c) in enumerate(sample, 1):
    a = xy[c["from_node"]]; b = xy[c["to_node"]]
    pad = max(c["gap_m"] * 4, 400)
    ext = (min(a[0], b[0]) - pad, max(a[0], b[0]) + pad, min(a[1], b[1]) - pad, max(a[1], b[1]) + pad)
    win = (slice(ext[0], ext[1]), slice(ext[2], ext[3]))
    src = road[road["from"].map(comp_of) == c["comp"]]
    fig, ax = plt.subplots(figsize=(8, 7))
    road.cx[win].plot(ax=ax, color="#9a9a9a", linewidth=0.8, zorder=1)        # all road in view
    src.cx[win].plot(ax=ax, color="#ff7f0e", linewidth=1.8, zorder=2)         # the stub component
    gpd.GeoSeries([line(c)], crs=nodes.crs).plot(ax=ax, color="#d62728", linewidth=2.0,
                                                 linestyle="--", zorder=4)
    ax.scatter(*a, s=55, c="#ff7f0e", edgecolor="k", zorder=5, label=f"stub end (comp {c['comp']})")
    ax.scatter(*b, s=55, c="#1f77b4", edgecolor="k", zorder=5,
               label=f"neighbour ({'backbone' if c['to_backbone'] else 'comp '+str(c['to_comp'])})")
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.legend(loc="lower left", fontsize=8)
    ax.set_title(f"#{rank} [{lab}]  comp {c['comp']} ({c['size']} nodes) — gap {c['gap_m']:,.1f} m")
    p = OUT / f"02_cand_{rank:02d}_comp{c['comp']}.png"
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
    T.image(p, f"#{rank} [{lab}] comp {c['comp']}, {c['size']} nodes, gap {c['gap_m']:,.1f} m")

T.note("If the dashed connector closes a visible break between two aligned road ends, it is a noding "
       "gap to weld. If it spans a river/water, that tolerance is too high. Pick the tolerance where "
       "the gaps stop looking like a road-end mismatch.")
T.done()
