#!/usr/bin/env python3
"""STEP 02 — the NEW air mode's contribution to the multimodal network.

Isolates what the official flight data adds: the air↔road transfers, and a WITH-vs-WITHOUT-air comparison
of the giant — which road nodes and fuel hubs reach the network ONLY because of air ("air-only-reachable").

Run: python3 research/multimodal_network/02_air_role.py  (after 01 / a build of output/03_network)
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from _trace import OUT, ROOT, Tracer
from mmnet.network import NetworkTables

T = Tracer("02_air_role", "STEP 02 — The new air mode's contribution to the multimodal network")

nt = NetworkTables.from_gpkg(ROOT / "output" / "03_network")
nd = nt.nodes.sort_values("node_id").reset_index(drop=True)
e = nt.edges.copy()
e["from"] = e["from"].astype(int); e["to"] = e["to"].astype(int)
et, src = e["type"], e["source"].astype(str)
N = len(nd)
xy = np.c_[nd.geometry.x.values, nd.geometry.y.values]
road_ids = set(e[et == "Road"]["from"]).union(e[et == "Road"]["to"])
hubs = nd[nd["is_hub"].fillna(False).astype(bool)] if "is_hub" in nd.columns else nd.iloc[:0]
hub_nodes = set(hubs["node_id"])


def giant_of(mask):
    g = nx.Graph(); g.add_nodes_from(range(N))
    g.add_edges_from(zip(e.loc[mask, "from"], e.loc[mask, "to"]))
    comps = sorted(nx.connected_components(g), key=len, reverse=True)
    return (comps[0] if comps else set()), len(comps)


# ── air↔road transfers + air-served airports ──
air_tr = e[(et == "Transfer") & (src == "airports")]
T.stage("Air interface")
T.kv("air edges / air↔road transfers", f"{int((et=='Air').sum())} / {len(air_tr)}")
T.kv("airport anchors (air-served)", f"{len(set(air_tr['from']).union(air_tr['to']) & road_ids)} road nodes "
     "linked to the air network at airports")

# ── WITH vs WITHOUT air ──
Gw, ncw = giant_of(np.ones(len(e), bool))
Gn, ncn = giant_of(~((et == "Air") | (src == "airports")))
air_only = Gw - Gn                                   # in the giant ONLY because of air
ao_road = air_only & road_ids
ao_hub = air_only & hub_nodes


def pc(ids, G):
    return round(100 * sum(n in G for n in ids) / max(len(ids), 1), 1)


T.stage("Marginal contribution of air (with vs without)")
rows = [
    {"metric": "components", "without_air": ncn, "with_air": ncw},
    {"metric": "giant nodes", "without_air": len(Gn), "with_air": len(Gw)},
    {"metric": "road % in giant", "without_air": pc(road_ids, Gn), "with_air": pc(road_ids, Gw)},
    {"metric": "fuel hubs in giant", "without_air": sum(h in Gn for h in hub_nodes),
     "with_air": sum(h in Gw for h in hub_nodes)},
]
T.show(pd.DataFrame(rows), "with vs without the air mode", n=len(rows))
T.kv("air-only-reachable", f"{len(air_only):,} nodes join the giant ONLY via air — "
     f"incl. {len(ao_road)} road nodes and {len(ao_hub)} fuel hubs")
if ao_hub:
    names = hubs[hubs["node_id"].isin(ao_hub)]
    col = "hub_id" if "hub_id" in names.columns else "node_id"
    T.kv("fuel hubs connected only by air", ", ".join(str(v) for v in names[col].head(20)))

# ── map: the air layer + the nodes it uniquely connects ──
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(nd.crs)
bx = boundary.total_bounds; PAD = 6e4
EXT = (bx[0] - PAD, bx[2] + PAD, bx[1] - PAD, bx[3] + PAD)
fig, ax = plt.subplots(figsize=(12, 10))
boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)


def clip(g):
    b = g.bounds
    return g[(b.maxx >= EXT[0]) & (b.minx <= EXT[1]) & (b.maxy >= EXT[2]) & (b.miny <= EXT[3])]


clip(e[et.isin(["Road", "Waterway", "IceRoad"])]).plot(ax=ax, color="#cccccc", linewidth=0.3, zorder=1)
clip(e[et == "Air"]).plot(ax=ax, color="#9467bd", linewidth=0.7, zorder=3, label=f"air ({int((et=='Air').sum())})")
clip(air_tr).plot(ax=ax, color="#d62728", linewidth=0.9, linestyle="--", zorder=4, label=f"air↔road transfer ({len(air_tr)})")
if ao_road:
    aor = nd[nd["node_id"].isin(ao_road)]
    ax.scatter(aor.geometry.x, aor.geometry.y, s=14, c="#ff7f0e", zorder=5, label=f"road reachable only by air ({len(ao_road)})")
if ao_hub:
    aoh = nd[nd["node_id"].isin(ao_hub)]
    ax.scatter(aoh.geometry.x, aoh.geometry.y, marker="*", s=60, c="#d62728", edgecolor="white",
               linewidth=0.5, zorder=6, label=f"fuel hub reachable only by air ({len(ao_hub)})")
ax.set_xlim(EXT[0], EXT[1]); ax.set_ylim(EXT[2], EXT[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
ax.legend(loc="lower left", fontsize=8, title="the new air mode")
ax.set_title("What the new air data adds — the air network + the communities it uniquely connects")
p = OUT / "02_air_role.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Air's contribution: the air layer (purple), air↔road transfers (red), and air-only-reachable hubs/roads")
T.done()
