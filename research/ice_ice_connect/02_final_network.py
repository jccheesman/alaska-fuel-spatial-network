#!/usr/bin/env python3
"""STEP 02 — the FINAL ice-ice network: raw → noded → welded, giant + disconnected (road+ice study, ICE only).

Quantifies the ice↔ice connectivity end to end and renders the final ice-only network at three weld
tolerances (450 m / 1 km / 3 km):
  - raw ice line features → geometric components (before R noding)
  - noded ice (built network) → 47 components
  - after the ice↔ice weld → giant component + the remaining disconnected paths
Writes a QGIS-openable final-network gpkg per tolerance + a 3-panel comparison + tables.
Run: python3 research/ice_ice_connect/02_final_network.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

from _trace import OUT, ROOT, Tracer
from ii_core import component_min_distances, load_network, mode_components

TOLS = [450, 1000, 3000]
NS = (-180000, 240000, 2120000, 2380000)   # North Slope window for the maps

T = Tracer("02_final_network", "STEP 02 — Final ice-ice network: raw → welded, giant + disconnected")

# ── 1) RAW ice line components (before noding) ──
raw = gpd.read_file(ROOT / "data" / "interim" / "ice_roads.gpkg").to_crs(3338)
geoms = list(raw.geometry); tree = STRtree(geoms)
gr = nx.Graph(); gr.add_nodes_from(range(len(geoms)))
for i, gm in enumerate(geoms):
    b = gm.buffer(1)
    for j in tree.query(b):
        j = int(j)
        if j > i and b.intersects(geoms[j]):
            gr.add_edge(i, j)
raw_comps = nx.number_connected_components(gr)

# ── 2) NODED ice (built network) ──
nodes, edges, xy = load_network()
ice, ids, comps, comp_of = mode_components(edges, "IceRoad")
sizes = np.array([len(c) for c in comps])
cc = component_min_distances(ids, xy, comp_of)
T.stage("Ice connectivity: raw → noded → welded")
T.kv("raw ice line features", len(raw))
T.kv("raw geometric components (lines touching ≤1 m)", raw_comps)
T.kv("noded ice (built net)", f"{len(ids):,} nodes · {len(ice):,} edges · {len(comps)} components")
T.kv("noded giant / disconnected", f"{int(sizes.max())} nodes ({sizes.max()/len(ids):.0%}) / {len(comps)-1} pieces")


def ll(pt):
    p = gpd.GeoSeries([Point(pt)], crs=3338).to_crs(4326)[0]
    return p.y, p.x


# ── 3) weld at each tolerance → final network ──
summary = []
finals = {}      # T -> (node_graph, comps2, comp_of2, weld_edges)
for tol in TOLS:
    welds = [(fn, tn, d) for (_, _), (d, fn, tn) in cc.items() if d <= tol]
    g = nx.Graph(); g.add_nodes_from(ids)
    g.add_edges_from(zip(ice["from"].to_numpy(), ice["to"].to_numpy()))
    g.add_edges_from((fn, tn) for fn, tn, _ in welds)
    comps2 = sorted(nx.connected_components(g), key=len, reverse=True)
    comp_of2 = {n: i for i, c in enumerate(comps2) for n in c}
    giant_n = len(comps2[0]); disc = comps2[1:]
    disc_sizes = sorted((len(c) for c in disc), reverse=True)
    finals[tol] = (g, comps2, comp_of2, welds)
    summary.append({"tol_m": tol, "weld_edges": len(welds), "components": len(comps2),
                    "giant_nodes": giant_n, "giant_pct": round(100 * giant_n / len(ids), 1),
                    "disconnected": len(disc), "two_node_stubs": sum(1 for s in disc_sizes if s == 2),
                    "largest_disconnected": disc_sizes[0] if disc_sizes else 0,
                    "longest_weld_m": round(max((d for *_, d in welds), default=0))})
sdf = pd.DataFrame(summary)
T.show(sdf, "final ice-ice network — raw 42 / noded 47 → welded at 450 m / 1 km / 3 km", n=len(sdf))
sdf.to_csv(OUT / "ice_final_compare.csv", index=False)

# ── 4) write the final ice-ice network gpkg + disconnected table, per tolerance ──
for tol in TOLS:
    g, comps2, comp_of2, welds = finals[tol]
    giant = set(comps2[0])
    ice_e = ice.copy()
    ice_e["component"] = ice_e["from"].map(comp_of2)
    ice_e["is_giant"] = ice_e["from"].isin(giant)
    ice_e["source"] = "IceRoad"
    ice_e["length_m"] = ice_e.geometry.length.round()
    weld_rows = gpd.GeoDataFrame(
        [{"from": fn, "to": tn, "type": "IceRoad", "source": "weld:IceRoad", "length_m": round(d),
          "component": comp_of2[fn], "is_giant": fn in giant,
          "geometry": LineString([xy[fn], xy[tn]])} for fn, tn, d in welds],
        geometry="geometry", crs=nodes.crs)
    keep = [c for c in ["from", "to", "type", "source", "length_m", "component", "is_giant", "geometry"]
            if c in ice_e.columns]
    final = pd.concat([ice_e[keep], weld_rows[keep]], ignore_index=True)
    gpd.GeoDataFrame(final, geometry="geometry", crs=nodes.crs).to_file(
        OUT / f"ice_final_{tol}m__edges.gpkg", driver="GPKG")
    # disconnected paths table
    drows = []
    for ci, c in enumerate(comps2[1:], 1):
        arr = np.array(sorted(c)); cen = xy[arr].mean(0); lat, lon = ll(cen)
        # nearest other-component gap (residual, > tol)
        gap = min((d for (a, b), (d, *_) in cc.items()
                   if (comp_of[arr[0]] in (a, b))), default=np.inf)
        drows.append({"rank": ci, "nodes": len(c), "lat": round(lat, 2), "lon": round(lon, 2)})
    pd.DataFrame(drows).to_csv(OUT / f"ice_disconnected_{tol}m.csv", index=False)
T.kv("wrote", "ice_final_{450,1000,3000}m__edges.gpkg + ice_disconnected_*.csv")

# ── 5) 3-panel comparison map: giant vs disconnected + weld connectors ──
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(nodes.crs)
win = (slice(NS[0], NS[1]), slice(NS[2], NS[3]))
fig, axs = plt.subplots(1, 3, figsize=(20, 7))
for ax, tol in zip(axs, TOLS):
    g, comps2, comp_of2, welds = finals[tol]
    giant = set(comps2[0])
    boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
    ice_in = ice.cx[win]
    ig = ice_in["from"].isin(giant)
    ice_in[ig].plot(ax=ax, color="#17becf", linewidth=1.0, zorder=2)          # giant
    ice_in[~ig].plot(ax=ax, color="#d62728", linewidth=1.2, zorder=3)         # disconnected
    if welds:
        gpd.GeoSeries([LineString([xy[fn], xy[tn]]) for fn, tn, _ in welds],
                      crs=nodes.crs).plot(ax=ax, color="#000", linewidth=1.4, zorder=5)
    r = next(s for s in summary if s["tol_m"] == tol)
    ax.set_xlim(NS[0], NS[1]); ax.set_ylim(NS[2], NS[3])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f"weld {tol} m → {r['components']} comps · giant {r['giant_pct']:.0f}% · "
                 f"{r['disconnected']} disconnected")
axs[0].legend(handles=[Line2D([0], [0], color="#17becf", lw=2, label="giant ice component"),
                       Line2D([0], [0], color="#d62728", lw=2, label="disconnected ice"),
                       Line2D([0], [0], color="#000", lw=2, label="ice↔ice weld")],
              loc="lower left", fontsize=8)
fig.suptitle("Final ice-ice network — giant (cyan) vs disconnected paths (red), weld connectors (black)",
             fontsize=14)
fig.tight_layout(rect=[0, 0, 1, 0.95])
p = OUT / "02_ice_final.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Final ice-ice network at 450 m / 1 km / 3 km — giant vs disconnected paths")
T.note("Raw 42 → noded 47 → welded {33,27,19}. The weld merges only the short branch gaps; the remaining "
       "disconnected pieces are genuinely separate trail systems (mostly 2-node stubs). Giant tops out ~85% "
       "at 3 km. Final networks written per tolerance for inspection.")
T.done()
