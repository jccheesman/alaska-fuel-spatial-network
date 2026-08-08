#!/usr/bin/env python3
"""STEP 07 — North Slope ice↔road connection OPTIONS, compared with plots (road + ice only).

The big Barrow ice system is genuinely ≥38.6 km from the road backbone (no short-hop chain exists, even
through oilfield grids). This lays out every option to connect the North Slope ice↔road WITHOUT a 55 km
edge, as a 4-panel comparison + a summary table, so the strategy can be chosen from the picture:

  A — Regional 3 km (no long edge): ice↔local roads; Barrow joins its local grid, Deadhorse ice reaches
      the Dalton→Fairbanks. Nothing fabricated.
  B — Real winter route (Colville/Nuiqsut): the real seasonal corridor a short-hop route would follow;
      needs sourcing that route as data.
  C — Shortest explicit connector (≈38.6 km): one fabricated WinterRoute edge connects the giant.
  D — Hybrid: A + the one 38.6 km WinterRoute edge.

Run: python3 research/road_ice_connect/07_north_slope_options.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from shapely.geometry import LineString, Point

from _trace import OUT, ROOT, Tracer
from bridge_core import (bottleneck_path, candidate_connectors, component_graph, giant_fraction,
                         load_network, mode_node_ids, within_mode_connectors)

TOL = 3000          # regional proximity tolerance (m) for options A/D
NS = (-180000, 240000, 2120000, 2380000)   # North Slope window (EPSG:3338)

T = Tracer("07_north_slope_options", "STEP 07 — North Slope ice↔road connection options")
nodes, edges, xy = load_network()
N = len(nodes)
ice_ids, _ = mode_node_ids(edges, "IceRoad"), None
ice_ids = mode_node_ids(edges, "IceRoad")
road_ids = mode_node_ids(edges, "Road")

# ── the three proximity rules at TOL (option A / D base) ──
rr = within_mode_connectors(edges, xy, "Road", TOL)
ii = within_mode_connectors(edges, xy, "IceRoad", TOL)
ri = [(c["from_node"], c["to_node"], c["gap_m"])
      for c in candidate_connectors(edges, xy, "IceRoad", "Road") if c["gap_m"] <= TOL]
regional = rr + ii + ri

# ── the bottleneck chain (option C / D long edge) ──
meta, comps = component_graph(edges, xy, modes=("IceRoad", "Road"), max_edge_m=60000)
bn, path = bottleneck_path(meta, ("I", 0), ("R", 0))
# build the explicit WinterRoute connector(s) = the meta-path hops as straight node-to-node lines
def nearest_pair(a_key, b_key):
    from scipy.spatial import cKDTree
    A = np.array(comps[a_key]); B = np.array(comps[b_key])
    d, j = cKDTree(xy[B]).query(xy[A]); i = int(np.argmin(d))
    return int(A[i]), int(B[int(j[i])]), float(d[i])


winter = [nearest_pair(path[k], path[k + 1]) for k in range(len(path) - 1)] if path else []
T.kv("regional connectors @3 km", f"road {len(rr)} + ice {len(ii)} + ice→road {len(ri)}")
T.kv("bottleneck giant→backbone", f"{bn/1000:.1f} km via {len(winter)} hop(s)")

# ── metrics per option ──
def ice_to_road_pct(extra):
    """% of ice nodes joined to ANY road, given extra connector edges."""
    g = nx.Graph(); g.add_nodes_from(range(N))
    g.add_edges_from(zip(edges["from"], edges["to"])); g.add_edges_from((a, b) for a, b, *_ in extra)
    road_comp_ids = {next(iter(nx.node_connected_component(g, r))) for r in [road_ids[0]]}
    # ice node connected to a road = shares a component with any road node
    road_components = {frozenset(c) for c in nx.connected_components(g) if any(r in c for r in road_ids[:1])}
    # simpler: mark components containing >=1 road node
    comp_of = {}
    for ci, c in enumerate(nx.connected_components(g)):
        for n in c:
            comp_of[n] = ci
    road_comps = {comp_of[r] for r in road_ids}
    ice_on_road = sum(1 for n in ice_ids if comp_of[n] in road_comps)
    return 100 * ice_on_road / len(ice_ids)


def backbone_pct(extra):
    g = nx.Graph(); g.add_nodes_from(range(N))
    g.add_edges_from(zip(edges["from"], edges["to"])); g.add_edges_from((a, b) for a, b, *_ in extra)
    giant = max(nx.connected_components(g), key=len)
    return 100 * sum(1 for n in ice_ids if n in giant) / len(ice_ids)


nc0, gf0 = giant_fraction(edges, N)
options = {
    "A: regional 3 km": regional,
    "B: real winter route*": regional,                 # same geometry; the route itself is external data
    "C: shortest connector": winter,
    "D: hybrid (A + connector)": regional + winter,
}
rows = []
for name, extra in options.items():
    nc, gf = giant_fraction(edges, N, extra)
    longest = max((d for *_, d in extra), default=0)
    rows.append({"option": name, "new_edges": len(extra), "longest_edge_km": round(longest / 1000, 1),
                 "ice_to_roads_pct": round(ice_to_road_pct(extra)), "ice_to_backbone_pct": round(backbone_pct(extra), 1),
                 "components": nc, "giant_pct": round(gf * 100, 1),
                 "fabricated_long_edge": "no" if longest <= TOL else f"yes ({longest/1000:.0f} km)"})
tab = pd.DataFrame(rows)
T.show(tab, "North Slope connection options", n=len(tab))
tab.to_csv(OUT / "north_slope_options.csv", index=False)
T.note("* Option B uses the SAME 3 km proximity geometry shown; the real Colville/Nuiqsut winter route is "
       "external data that, once added, would let the giant chain in via short hops (no long fabricated "
       "edge). Without that data it equals A. Option A fabricates nothing; C/D add one ≈38.6 km WinterRoute "
       "edge — long, but never 55 km.")

# ───────────────────────────── 4-panel comparison map ─────────────────────────────
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(nodes.crs)
road = edges[edges["type"] == "Road"]; ice = edges[edges["type"] == "IceRoad"]
win = (slice(NS[0], NS[1]), slice(NS[2], NS[3]))


def base(ax, title):
    boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
    road.cx[win].plot(ax=ax, color="#888", linewidth=0.6, zorder=1)
    ice.cx[win].plot(ax=ax, color="#17becf", linewidth=1.0, zorder=2)
    ax.set_xlim(NS[0], NS[1]); ax.set_ylim(NS[2], NS[3])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.set_title(title, fontsize=11)


def draw(ax, conns, color, lw=1.2, ls="-"):
    if conns:
        gpd.GeoSeries([LineString([xy[a], xy[b]]) for a, b, *_ in conns],
                      crs=nodes.crs).plot(ax=ax, color=color, linewidth=lw, linestyle=ls, zorder=6)


fig, axs = plt.subplots(2, 2, figsize=(16, 11))
# A
base(axs[0, 0], f"A — regional 3 km  ({rows[0]['ice_to_roads_pct']}% ice→roads, longest ≤3 km, no long edge)")
draw(axs[0, 0], rr, "#ff7f0e"); draw(axs[0, 0], ii, "#9467bd"); draw(axs[0, 0], ri, "#d62728")
# B — real winter route corridor (annotate Nuiqsut→Kuparuk/Deadhorse)
base(axs[0, 1], "B — real winter route (Colville / Nuiqsut) — needs route data")
nuiqsut = gpd.GeoSeries([Point(-151.0, 70.22)], crs=4326).to_crs(3338)[0]
deadhorse = gpd.GeoSeries([Point(-148.44, 70.22)], crs=4326).to_crs(3338)[0]
gpd.GeoSeries([LineString([(nuiqsut.x, nuiqsut.y), (deadhorse.x, deadhorse.y)])], crs=3338).plot(
    ax=axs[0, 1], color="#2ca02c", linewidth=2.0, linestyle=":", zorder=6)
axs[0, 1].annotate("real winter ice road\n(Colville/Nuiqsut → Kuparuk)", (nuiqsut.x, nuiqsut.y),
                   textcoords="offset points", xytext=(6, 8), fontsize=8, color="#2a7")
# C — shortest explicit connector (the bottleneck chain)
base(axs[1, 0], f"C — shortest explicit connector ≈ {bn/1000:.0f} km (one WinterRoute edge)")
draw(axs[1, 0], winter, "#d62728", lw=2.4, ls="--")
# D — hybrid
base(axs[1, 1], f"D — hybrid: 3 km regional + the {bn/1000:.0f} km WinterRoute edge")
draw(axs[1, 1], rr, "#ff7f0e"); draw(axs[1, 1], ii, "#9467bd"); draw(axs[1, 1], ri, "#d62728")
draw(axs[1, 1], winter, "#d62728", lw=2.4, ls="--")
for ax in axs.flat:
    ax.legend(handles=[Line2D([0], [0], color="#17becf", lw=2, label="ice"),
                       Line2D([0], [0], color="#888", lw=2, label="road"),
                       Line2D([0], [0], color="#d62728", lw=2, label="connector")],
              loc="lower left", fontsize=7)
fig.suptitle("North Slope ice↔road — connection options (none uses a 55 km edge)", fontsize=14)
fig.tight_layout(rect=[0, 0, 1, 0.96])
p = OUT / "07_north_slope_options.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Four options A–D for connecting the North Slope ice↔road, compared")
T.done()
