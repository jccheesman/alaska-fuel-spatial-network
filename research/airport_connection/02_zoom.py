#!/usr/bin/env python3
"""Zoom panels — the difference between the CURRENT air↔road transfer and SNAP-to-road, per airport.

For a spread of airports it draws, side by side:
  • CURRENT  — the air node (▲) and the road node (●) sit apart, joined by a red Transfer edge (the gap).
  • SNAPPED  — the airport ▲ lands ON the road node; the air legs reattach there; NO transfer edge.

Reads output/03_network. Research only. Run: python3 research/airport_connection/02_zoom.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from scipy.spatial import cKDTree

from _trace import OUT, ROOT, Tracer
from mmnet.network import NetworkTables

T = Tracer("02_zoom", "Zoom — air↔road TRANSFER (current) vs SNAP-to-road, per airport")

nt = NetworkTables.from_gpkg(ROOT / "output" / "03_network")
nd = nt.nodes.sort_values("node_id").reset_index(drop=True)
e = nt.edges.copy(); e["from"] = e["from"].astype(int); e["to"] = e["to"].astype(int)
et, sr = e["type"], e["source"].astype(str)
xy = np.c_[nd.geometry.x.values, nd.geometry.y.values]
road_set = set(e.loc[et == "Road", "from"]).union(e.loc[et == "Road", "to"])
road_e, air_e = e[et == "Road"], e[et == "Air"]

ap = gpd.read_file(ROOT / "data" / "processed" / "air_nodes.geojson").to_crs(nd.crs)
ap_tree = cKDTree(np.c_[ap.geometry.x.values, ap.geometry.y.values])
name_col = "name" if "name" in ap.columns else ("code" if "code" in ap.columns else None)


def airport_label(coord):
    i = int(ap_tree.query(coord)[1])
    nm = str(ap.iloc[i][name_col]) if name_col else "airport"
    return nm.replace(" Apt", "").replace(" Airport", "")[:22]


# ── pick a spread of airports by transfer length (a few big gaps + a couple typical) ──
air_tr = e[(et == "Transfer") & (sr == "airports")].copy()
air_tr["len"] = air_tr.geometry.length
air_tr = air_tr.sort_values("len", ascending=False).reset_index(drop=True)
pick = sorted(set([0, 1, 2, len(air_tr) // 2, len(air_tr) - 5]))   # longest few + a median one
sel = air_tr.iloc[[i for i in pick if 0 <= i < len(air_tr)]].head(5)

fig, axs = plt.subplots(len(sel), 2, figsize=(10, 4.6 * len(sel)))
if len(sel) == 1:
    axs = axs.reshape(1, 2)

for r, (_, tr) in enumerate(sel.iterrows()):
    a, b = int(tr["from"]), int(tr["to"])
    rn, an = (a, b) if a in road_set else (b, a)        # road node, air node
    rxy, axy = xy[rn], xy[an]
    label = airport_label(axy)
    cx, cy = (rxy + axy) / 2
    pad = max(float(tr["len"]) * 1.6, 1500)
    win = (cx - pad, cx + pad, cy - pad, cy + pad)
    incident = air_e[(air_e["from"] == an) | (air_e["to"] == an)]

    def setup(ax):
        if len(road_e):
            road_e.cx[win[0]:win[1], win[2]:win[3]].plot(ax=ax, color="#888", linewidth=1.0, zorder=1)
        ax.set_xlim(win[0], win[1]); ax.set_ylim(win[2], win[3])
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])

    # CURRENT — transfer edge + the two separate nodes
    ax = axs[r, 0]; setup(ax)
    if len(incident):
        incident.cx[win[0]:win[1], win[2]:win[3]].plot(ax=ax, color="#9467bd", linewidth=1.4, alpha=0.8, zorder=2)
    ax.plot([rxy[0], axy[0]], [rxy[1], axy[1]], color="#d62728", linewidth=2.0, linestyle="--", zorder=3)
    ax.scatter(*rxy, s=55, c="#888", edgecolor="black", linewidth=0.5, zorder=4)
    ax.scatter(*axy, marker="^", s=90, c="#9467bd", edgecolor="white", linewidth=0.5, zorder=5)
    ax.set_ylabel(f"{label}\n(gap {tr['len']:.0f} m)", fontsize=9)
    if r == 0:
        ax.set_title("CURRENT — air↔road TRANSFER edge (red): airport off the road", fontsize=10)

    # SNAPPED — airport on the road node; air legs reattach there; no transfer edge
    ax = axs[r, 1]; setup(ax)
    if len(incident):
        for _, ie in incident.iterrows():
            other = int(ie["to"]) if int(ie["from"]) == an else int(ie["from"])
            ax.plot([rxy[0], xy[other][0]], [rxy[1], xy[other][1]], color="#9467bd", linewidth=1.4, alpha=0.8, zorder=2)
    ax.annotate("", xy=rxy, xytext=axy, zorder=3,
                arrowprops=dict(arrowstyle="->", color="#000000", lw=1.2, linestyle=":"))
    ax.scatter(*rxy, marker="^", s=110, c="#2ca02c", edgecolor="black", linewidth=0.6, zorder=5)
    if r == 0:
        ax.set_title("SNAPPED — airport lands ON the road node (no transfer edge)", fontsize=10)

fig.legend(handles=[Line2D([0], [0], color="#888", lw=2, label="road"),
                    Line2D([0], [0], color="#9467bd", lw=2, label="air leg"),
                    Line2D([0], [0], color="#d62728", lw=2, ls="--", label="air↔road transfer edge"),
                    Line2D([0], [0], marker="^", color="w", markerfacecolor="#9467bd", label="airport (off road)"),
                    Line2D([0], [0], marker="o", color="w", markerfacecolor="#888", label="road node"),
                    Line2D([0], [0], marker="^", color="w", markerfacecolor="#2ca02c", label="airport snapped onto road")],
           loc="lower center", ncol=3, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.01))
fig.suptitle("Airport connection — TRANSFER edge (left) vs SNAP-to-road (right), zoomed per airport", fontsize=13)
fig.tight_layout(rect=[0, 0.03, 1, 0.97])
p = OUT / "02_zoom_transfer_vs_snap.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Per-airport zoom: the red transfer gap (left) becomes a shared road node when snapped (right)")
T.kv("airports shown", ", ".join(airport_label(xy[int(t['to']) if int(t['from']) in road_set else int(t['from'])])
                                  for _, t in sel.iterrows()))
T.done()
