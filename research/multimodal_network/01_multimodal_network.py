#!/usr/bin/env python3
"""STEP 01 — the full Alaska multimodal network WITH the new official flight data.

Loads the engine's built network `output/03_network` — road + ice + waterway + the NEW air mode (the
official AK DOT&PF-matched flight data, now wired through the pipeline) connected by the transfer / bridge /
connect-to-giant passes — and shows the result: per-mode size, the network by mode, connectivity (giant +
per-mode % reachable), connected-vs-disconnected, and fuel-hub reachability.

Rebuild the source first if needed:  python -c "import mmnet; mmnet.run_pipeline('profile.yaml')"
Run: python3 research/multimodal_network/01_multimodal_network.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from _trace import OUT, ROOT, Tracer
from mmnet.network import NetworkTables
from mmnet.viz import _EDGE_TYPE_COLORS

MODES = ["Road", "Waterway", "IceRoad", "Air"]          # the four transport modes

T = Tracer("01_multimodal_network", "STEP 01 — Full Alaska multimodal network (with the new flight data)")

nt = NetworkTables.from_gpkg(ROOT / "output" / "03_network")
nd = nt.nodes.sort_values("node_id").reset_index(drop=True)
e = nt.edges.copy()
e["from"] = e["from"].astype(int); e["to"] = e["to"].astype(int)
et, src = e["type"], e["source"].astype(str)
N = len(nd)
xy = np.c_[nd.geometry.x.values, nd.geometry.y.values]

# ── per-mode size + connectors ──
km = (e.geometry.length / 1000.0).groupby(et).sum().round().astype(int)
T.stage("Network size — by mode")
T.kv("nodes / edges", f"{N:,} / {len(e):,}")
T.kv("edges by type", et.value_counts().to_dict())
T.kv("network length by mode (km)", {k: int(km.get(k, 0)) for k in MODES})
T.kv("connectors by source", {k: int(v) for k, v in src.value_counts().items()
                              if any(t in k for t in (":", "weld", "bridge", "shore", "ports", "airports", "barge"))})

# ── connectivity: giant + per-mode % reachable ──
g = nx.Graph(); g.add_nodes_from(range(N))
g.add_edges_from(zip(e["from"], e["to"]))
comps = sorted(nx.connected_components(g), key=len, reverse=True)
giant = comps[0] if comps else set()
nd["in_giant"] = nd["node_id"].isin(giant)


def mode_ids(t):
    s = e[et == t]
    return set(s["from"]).union(s["to"])


T.stage("Connectivity — the multimodal giant")
T.kv("components / giant", f"{len(comps)} / {len(giant):,} nodes ({len(giant)/max(N,1):.1%})")
rows = []
for m in MODES:
    ids = mode_ids(m)
    if not ids:
        continue
    ing = sum(n in giant for n in ids)
    rows.append({"mode": m, "nodes": len(ids), "in_giant": ing, "pct_in_giant": round(100 * ing / len(ids), 1)})
ev = pd.DataFrame(rows)
T.show(ev, "per-mode reachability — share of each mode's nodes in the multimodal giant", n=len(ev))

# ── fuel-hub reachability ──
hubs = nd[nd["is_hub"].fillna(False).astype(bool)] if "is_hub" in nd.columns else nd.iloc[:0]
hub_giant = int(hubs["in_giant"].sum())
T.kv("fuel hubs reachable / total", f"{hub_giant} / {len(hubs)} ({hub_giant/max(len(hubs),1):.0%}) in the giant")

# ── basemap + clip (intersection, so offshore waterway/air survive) ──
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(nd.crs)
bx = boundary.total_bounds
PAD = 6e4
EXT = (bx[0] - PAD, bx[2] + PAD, bx[1] - PAD, bx[3] + PAD)


def _base(ax):
    boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
    ax.set_xlim(EXT[0], EXT[1]); ax.set_ylim(EXT[2], EXT[3])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])


def clip(g):
    b = g.bounds
    return g[(b.maxx >= EXT[0]) & (b.minx <= EXT[1]) & (b.maxy >= EXT[2]) & (b.miny <= EXT[3])]


# ── map 1: the multimodal network by mode (air highlighted — the new data) ──
STYLE = {"Road": dict(c="#6b6b6b", lw=0.35, z=2), "Waterway": dict(c="#1f77b4", lw=0.5, z=3),
         "IceRoad": dict(c="#17becf", lw=0.7, z=4), "Air": dict(c="#9467bd", lw=0.7, z=5)}
fig, ax = plt.subplots(figsize=(12, 10)); _base(ax)
for m in MODES:
    sub = clip(e[et == m])
    if len(sub):
        sub.plot(ax=ax, color=STYLE[m]["c"], linewidth=STYLE[m]["lw"], zorder=STYLE[m]["z"])
clip(e[et == "Transfer"]).plot(ax=ax, color="#d62728", linewidth=0.8, linestyle="--", zorder=6)
clip(e[et == "Bridge"]).plot(ax=ax, color="#ff7f0e", linewidth=0.6, zorder=6)
ax.scatter(hubs.geometry.x, hubs.geometry.y, marker="*", s=12, c="black", zorder=7)
ax.legend(handles=[Line2D([0], [0], color=STYLE[m]["c"], lw=2, label=f"{m} ({int((et==m).sum())})") for m in MODES]
          + [Line2D([0], [0], color="#d62728", lw=2, ls="--", label=f"Transfer ({int((et=='Transfer').sum())})"),
             Line2D([0], [0], color="#ff7f0e", lw=2, label=f"Bridge ({int((et=='Bridge').sum())})"),
             Line2D([0], [0], marker="*", color="w", markerfacecolor="k", label=f"fuel hubs ({len(hubs)})")],
          loc="lower left", fontsize=8, title="mode (edges)")
ax.set_title("Alaska multimodal fuel network — road + ice + waterway + AIR (new flight data)")
p = OUT / "01_multimodal_by_mode.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "The full multimodal network by mode — air (purple) is the new official flight data")

# ── map 2: connected (giant) vs disconnected ──
gi = set(nd.loc[nd["in_giant"], "node_id"])
ec = clip(e).assign(_g=lambda d: d["from"].isin(gi) | d["to"].isin(gi))
fig, ax = plt.subplots(figsize=(12, 10)); _base(ax)
ec[ec["_g"]].plot(ax=ax, color="#2ca02c", linewidth=0.4, zorder=2, label=f"connected — giant ({len(giant)/N:.0%} of nodes)")
ec[~ec["_g"]].plot(ax=ax, color="#d62728", linewidth=0.9, zorder=3, label=f"disconnected ({len(comps)-1} pieces)")
ax.scatter(hubs.geometry.x, hubs.geometry.y, marker="*", s=12,
           c=np.where(hubs["in_giant"], "#2ca02c", "#d62728"), zorder=5)
ax.legend(loc="lower left", fontsize=8, title="connectivity")
ax.set_title(f"Multimodal connectivity — {len(giant)/N:.0%} of nodes in one giant; "
             f"{hub_giant}/{len(hubs)} fuel hubs reachable")
p = OUT / "01_connected_vs_disconnected.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Connected (green) vs disconnected (red) — all modes + fuel hubs")
T.done()
