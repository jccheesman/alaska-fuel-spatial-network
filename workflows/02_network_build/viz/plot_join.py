#!/usr/bin/env python3
"""Illustrate Stage 04 — before/after: components joined to the giant by distance.

Top    — BEFORE (`output/03_network`): the giant in grey, the 65 disconnected components in red.
Bottom — AFTER  (`output/04_network_joined`): the giant in grey, the components that were JOINED
         (≤ join_components.max_dist) in green with their `Join` connector lines, and the pieces
         still disconnected in red.

Run: python3 workflows/02_network_build/viz/plot_join.py   ->  outputs/02_network_build/output/join_03_vs_04.png
"""
from __future__ import annotations

import warnings
import os
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[3]  # repo root
PROJ = ROOT / "outputs" / "02_network_build"  # mmnet project dir: engine writes PROJ/output + PROJ/reports
os.environ.setdefault("MMNET_PROJECT", str(ROOT))  # mmnet.viz basemap reads <project>/data/

from mmnet.config import load_profile
from mmnet.network import NetworkTables
from mmnet.viz import _bounds_union, _draw_basemap, _load_basemap, _stacked_fig

warnings.filterwarnings("ignore")
OUT = PROJ / "output"
CAP_KM = load_profile(Path(__file__).resolve().parents[1] / "profile.yaml").join_components.max_dist / 1000


def _prep(stem):
    nt = NetworkTables.from_gpkg(OUT / stem)
    nd, ed = nt.nodes.copy(), nt.edges.copy()
    nd["node_id"] = nd["node_id"].astype(int)
    gid = int(nd.loc[nd["is_giant"].fillna(False).astype(bool), "component"].mode().iloc[0])
    ed["from"] = ed["from"].astype(int)
    ed["in_giant"] = ed["from"].map(dict(zip(nd["node_id"], nd["component"].astype(int)))).eq(gid)
    return nd, ed, gid


nd3, ed3, g3 = _prep("03_network")
nd4, ed4, g4 = _prep("04_network_joined")
crs = nd3.crs

land, sea, coast = _load_basemap(crs)
extent = _bounds_union([nd3, ed3])
fig, axes, extent = _stacked_fig(extent, 2, width=11)

n3 = nd3["component"].nunique()
n4 = nd4["component"].nunique()
join = ed4[ed4["type"] == "Join"] if "Join" in set(ed4["type"]) else ed4.iloc[:0]

# ── BEFORE (03) ──────────────────────────────────────────────────────────────
ax = axes[0]
_draw_basemap(ax, land, sea, coast, {})
ed3[ed3["in_giant"]].plot(ax=ax, color="#c9c9c9", linewidth=0.8, zorder=3)
ed3[~ed3["in_giant"]].plot(ax=ax, color="#d73027", linewidth=2.0, zorder=5)
off3 = nd3[~nd3["is_giant"].fillna(False).astype(bool)]
ax.scatter(off3.geometry.x, off3.geometry.y, s=10, c="#d73027", zorder=6,
           edgecolor="black", linewidth=0.2)
ax.set_title(f"Before — 03_network: {n3} components  (grey = giant, red = {n3 - 1} disconnected)", fontsize=11)

# ── AFTER (04) ───────────────────────────────────────────────────────────────
ax = axes[1]
_draw_basemap(ax, land, sea, coast, {})
ed4[ed4["in_giant"]].plot(ax=ax, color="#c9c9c9", linewidth=0.8, zorder=3)
ed4[~ed4["in_giant"]].plot(ax=ax, color="#d73027", linewidth=2.0, zorder=5)
off4 = nd4[~nd4["is_giant"].fillna(False).astype(bool)]
ax.scatter(off4.geometry.x, off4.geometry.y, s=10, c="#d73027", zorder=6,
           edgecolor="black", linewidth=0.2)
# the Join connectors (green) + a ring at each joined component
if len(join):
    join.plot(ax=ax, color="#1a9850", linewidth=2.4, zorder=7)
    jx = nd4.set_index("node_id").loc[join["from"].values]
    ax.scatter(jx.geometry.x, jx.geometry.y, s=70, facecolors="none",
               edgecolors="#1a9850", linewidths=1.8, zorder=8)
ax.set_title(f"After — 04_network_joined: {n4} components  "
             f"(green = {len(join)} joined ≤ {CAP_KM:g} km, red = still disconnected)", fontsize=11)

legend = [
    Line2D([0], [0], color="#c9c9c9", lw=2.4, label="giant component"),
    Line2D([0], [0], color="#1a9850", lw=2.4, label="Stage-04 join (≤ max_dist)"),
    Line2D([0], [0], color="#d73027", lw=2.4, label="still disconnected"),
]
axes[1].legend(handles=legend, fontsize=8, loc="best", framealpha=0.9)

for ax in axes:
    if extent:
        ax.set_xlim(extent[0], extent[2]); ax.set_ylim(extent[1], extent[3])
    ax.set_aspect("equal"); ax.tick_params(labelsize=7)
fig.suptitle("Stage 04 — joining disconnected components to the giant by distance", fontsize=13)

out = OUT / "join_03_vs_04.png"
fig.savefig(out, dpi=140, bbox_inches="tight")
plt.close(fig)
print(f"03: {n3} components -> 04: {n4} components  ({len(join)} joined)")
print(f"wrote {out}")
