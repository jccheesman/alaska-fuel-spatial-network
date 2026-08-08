#!/usr/bin/env python3
"""STEP 02 — per-candidate plausibility maps.

For every ice-road component within reach of a road (gap ≤ MAP_CEILING), draw a zoomed map: the ice
component (cyan), the surrounding road network (grey), and the PROPOSED connector (red dashed) from the
chosen ice dangle to the nearest road node. An Alaska-wide overview colors candidates by gap band so you
can see which links are plausible before locking a tolerance. Run: python3 research/road_ice_connect/02_candidates_map.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from shapely.geometry import LineString

from _trace import OUT, ROOT, Tracer
from bridge_core import candidate_connectors, load_network, mode_subgraph

MAP_CEILING = 5000.0          # render a per-candidate zoom for every component within this gap (m)
BANDS = [("≤ 500 m", 500, "#2ca02c"), ("500 m–2 km", 2000, "#ff7f0e"), ("2–5 km", 5000, "#d62728")]

T = Tracer("02_candidates", "STEP 02 — Candidate connector maps (visual plausibility)")
nodes, edges, xy = load_network()
ice_g, ice_comps, _ = mode_subgraph(edges, "IceRoad")
road_edges = edges[edges["type"] == "Road"]
ice_edges = edges[edges["type"] == "IceRoad"]
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(nodes.crs)

conns = candidate_connectors(edges, xy, "IceRoad", "Road", prefer_dangle=True)
conns = [c for c in conns if c["gap_m"] <= max(MAP_CEILING, 1)]
T.kv("candidates within 5 km", len(conns))


def band_color(gap):
    for _, hi, col in BANDS:
        if gap <= hi:
            return col
    return "#9467bd"


def connector_line(c):
    return LineString([xy[c["from_node"]], xy[c["to_node"]]])


# ---------------------------------------------------------------- Alaska-wide overview
T.stage("Overview — where the candidates are, colored by gap band")
fig, ax = plt.subplots(figsize=(11, 9))
boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
road_edges.plot(ax=ax, color="#cfcfcf", linewidth=0.3, zorder=1)
ice_edges.plot(ax=ax, color="#17becf", linewidth=0.6, zorder=2)
remote = [c for c in candidate_connectors(edges, xy, "IceRoad", "Road") if c["gap_m"] > MAP_CEILING]
for c in conns:
    L = connector_line(c)
    gpd.GeoSeries([L], crs=nodes.crs).plot(ax=ax, color=band_color(c["gap_m"]), linewidth=1.6, zorder=5)
    ax.scatter(*xy[c["from_node"]], s=14, c=band_color(c["gap_m"]), zorder=6)
ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
handles = [Line2D([0], [0], color=col, lw=2, label=f"candidate {lab}") for lab, _, col in BANDS]
handles += [Line2D([0], [0], color="#17becf", lw=2, label="ice roads"),
            Line2D([0], [0], color="#cfcfcf", lw=2, label="roads")]
ax.legend(handles=handles, loc="lower left", fontsize=8, title=f"{len(conns)} candidates ≤ 5 km "
          f"({len(remote)} remote comps stay isolated)")
ax.set_title("Road ↔ ice-road candidates by gap band (connectors not to scale of map)")
p = OUT / "02_overview.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Overview — candidate connectors colored by gap band; remote ice systems left grey/isolated")

# ---------------------------------------------------------------- per-candidate zooms
T.stage("Per-candidate zooms — judge each connector by eye")
for rank, c in enumerate(conns, 1):
    comp = ice_comps[c["comp"]]
    pts = xy[comp]
    cl = connector_line(c)
    cxx = np.r_[pts[:, 0], xy[c["from_node"]][0], xy[c["to_node"]][0]]
    cyy = np.r_[pts[:, 1], xy[c["from_node"]][1], xy[c["to_node"]][1]]
    pad = max(c["gap_m"] * 1.5, 1500)
    ext = (cxx.min() - pad, cxx.max() + pad, cyy.min() - pad, cyy.max() + pad)
    win = (slice(ext[0], ext[1]), slice(ext[2], ext[3]))

    fig, ax = plt.subplots(figsize=(9, 8))
    road_edges.cx[win].plot(ax=ax, color="#9a9a9a", linewidth=0.7, zorder=1)
    ice_edges.cx[win].plot(ax=ax, color="#17becf", linewidth=1.4, zorder=2)
    gpd.GeoSeries([cl], crs=nodes.crs).plot(ax=ax, color="#d62728", linewidth=2.0,
                                            linestyle="--", zorder=4)
    ax.scatter(*xy[c["from_node"]], s=70, c="#d62728", marker="o", zorder=5, label="ice dangle (ramp)")
    ax.scatter(*xy[c["to_node"]], s=70, c="#1f77b4", marker="s", zorder=5, label="nearest road node")
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.legend(loc="lower left", fontsize=8)
    ax.set_title(f"#{rank}  comp {c['comp']} ({c['size']} nodes) — gap {c['gap_m']:,.0f} m"
                 f"  ({'dangle' if c['used_dangle'] else 'node'})")
    p = OUT / f"02_cand_{rank:02d}_comp{c['comp']}.png"
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
    T.image(p, f"Candidate #{rank} — comp {c['comp']}, {c['size']} nodes, gap {c['gap_m']:,.0f} m")

T.note("Look for connectors that cross water or jump terrain — those mark a tolerance set too high. "
       "The gap where plausible ramps end and remote routes begin is the tolerance to choose.")
T.done()
