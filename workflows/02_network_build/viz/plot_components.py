#!/usr/bin/env python3
"""Two-panel connectivity map of the final network (output/03_network).

Top    — THE NETWORK, colored by connected component: the giant is light grey, every OTHER
         component gets a bright distinct color, so the disconnected pieces pop.
Bottom — THE CONNECTED VERSION: only the giant component (the 98.65% core).

Run: python3 workflows/02_network_build/viz/plot_components.py   ->  outputs/02_network_build/output/components_vs_giant.png
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

from mmnet.network import NetworkTables
from mmnet.viz import _bounds_union, _draw_basemap, _load_basemap, _stacked_fig

warnings.filterwarnings("ignore")

# ── load the built network ───────────────────────────────────────────────────
nt = NetworkTables.from_gpkg(PROJ / "output" / "03_network")
nd = nt.nodes.copy()
ed = nt.edges.copy()
crs = nd.crs

nd["node_id"] = nd["node_id"].astype(int)
comp_of = dict(zip(nd["node_id"], nd["component"].astype(int)))
giant_id = nd.loc[nd["is_giant"].fillna(False).astype(bool), "component"].astype(int).mode().iloc[0]

# each edge inherits its endpoint's component (endpoints share one component for real edges)
ed["from"] = ed["from"].astype(int)
ed["comp"] = ed["from"].map(comp_of).fillna(-1).astype(int)
ed["in_giant"] = ed["comp"].eq(giant_id)

n_comp = nd["component"].nunique()
giant_frac = 100 * nd["is_giant"].fillna(False).astype(bool).mean()
non_giant_comps = sorted(c for c in nd["component"].astype(int).unique() if c != giant_id)

# a bright, cycling palette for the non-giant components
palette = plt.get_cmap("tab20")
col_of = {c: palette(i % 20) for i, c in enumerate(non_giant_comps)}

# ── basemap + figure ─────────────────────────────────────────────────────────
land, sea, coast = _load_basemap(crs)
extent = _bounds_union([nd, ed])
fig, axes, extent = _stacked_fig(extent, 2, width=11)

giant_edges = ed[ed["in_giant"]]
other_edges = ed[~ed["in_giant"]]
giant_nodes = nd[nd["is_giant"].fillna(False).astype(bool)]
other_nodes = nd[~nd["is_giant"].fillna(False).astype(bool)]

# ── PANEL A — the network, by component ──────────────────────────────────────
axA = axes[0]
_draw_basemap(axA, land, sea, coast, {})
giant_edges.plot(ax=axA, color="#c9c9c9", linewidth=0.9, zorder=3)          # giant = grey backdrop
for c, grp in other_edges.groupby("comp"):
    grp.plot(ax=axA, color=col_of.get(int(c), "#e41a1c"), linewidth=2.2, zorder=5)
# node dots for the disconnected pieces so tiny/short fragments are visible
if len(other_nodes):
    axA.scatter(other_nodes.geometry.x, other_nodes.geometry.y,
                c=[col_of.get(int(c), "#e41a1c") for c in other_nodes["component"].astype(int)],
                s=14, zorder=6, edgecolor="black", linewidth=0.3)
axA.set_title(f"The network — {n_comp} components  "
              f"(grey = giant, colors = {len(non_giant_comps)} disconnected pieces)", fontsize=11)

# ── PANEL B — the connected version (giant only) ─────────────────────────────
axB = axes[1]
_draw_basemap(axB, land, sea, coast, {})
giant_edges.plot(ax=axB, color="#1a6fc4", linewidth=1.0, zorder=4)
axB.set_title(f"The connected version — giant component only  "
              f"({giant_frac:.1f}% of nodes, {len(giant_nodes):,} nodes)", fontsize=11)

legend = [
    Line2D([0], [0], color="#1a6fc4", lw=2.4, label="giant component (connected)"),
    Line2D([0], [0], color="#e41a1c", lw=2.4, label="disconnected component"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#e41a1c",
           markeredgecolor="black", markersize=8, label="disconnected node"),
]
axA.legend(handles=legend, fontsize=8, loc="best", framealpha=0.9)

for ax in axes:
    if extent:
        ax.set_xlim(extent[0], extent[2]); ax.set_ylim(extent[1], extent[3])
    ax.set_aspect("equal"); ax.tick_params(labelsize=7)
fig.suptitle("Final multimodal network — components vs. the connected giant", fontsize=13)

out = PROJ / "output" / "components_vs_giant.png"
fig.savefig(out, dpi=140, bbox_inches="tight")
plt.close(fig)
print(f"nodes {len(nd):,}  edges {len(ed):,}  components {n_comp}  giant {giant_frac:.2f}%")
print(f"non-giant components: {len(non_giant_comps)}  (nodes outside giant: {len(other_nodes):,})")
print(f"wrote {out}")
