#!/usr/bin/env python3
"""Four zoomed insets, each showing one synthetic connector in context.

One representative edge per type — RoadConnector, IceRoadRoadTransfer,
AirRoadTransfer, BargeRoadTransfer — zoomed tight enough that the connector reads
as a LINE, with the surrounding line-haul edges (colored by mode) so you can see
exactly which two modes it joins. Writes outputs/final_network_plots/connector_insets.png.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[3]
EDGES = ROOT / "final_network" / "network_joined_edges" / "network_joined_edges.shp"
BOUNDARY = ROOT / "data" / "boundary.geojson"
OUT = ROOT / "outputs" / "final_network_plots" / "connector_insets.png"

COLOR = {
    "Road": "#555555", "Waterway": "#1560a8", "IceRoad": "#12aebd", "Air": "#8452b8",
    "RoadConnector": "#ff7f0e", "IceRoadConnector": "#b5a800",
    "BargeRoadTransfer": "#d62728", "BargeIceRoadTransfer": "#e377c2",
    "IceRoadRoadTransfer": "#2ca02c", "AirRoadTransfer": "#7b3f00",
}
LINEHAUL = {"Road", "Waterway", "IceRoad", "Air"}
MODE_LABEL = {"Road": "Road", "IceRoad": "IceRoad", "Waterway": "Barge", "Air": "Air"}
LW = {"Road": 1.2, "Waterway": 1.8, "IceRoad": 2.2, "Air": 1.6}

# (type, human caption, fee note); one inset each, in this order
PANELS = [
    ("RoadConnector", "welds two road segments", "friction-weighted as Road (no transfer fee)"),
    ("IceRoadRoadTransfer", "ice road ↔ road handoff", "transfer fee $0.022/gal"),
    ("AirRoadTransfer", "air ↔ road handoff", "transfer fee $0.025/gal"),
    ("BargeRoadTransfer", "barge ↔ road handoff", "transfer fee $0.24/gal"),
]


def main() -> None:
    edges = gpd.read_file(EDGES)
    edges["len_m"] = edges.geometry.length
    boundary = gpd.read_file(BOUNDARY).to_crs(edges.crs) if BOUNDARY.exists() else None

    # modes at each node = edge_labels of the line-haul edges incident to it
    node_modes: dict[int, set] = {}
    lh = edges[edges["type"].isin(LINEHAUL)]
    for fn, tn, t in zip(lh["from"], lh["to"], lh["type"]):
        node_modes.setdefault(fn, set()).add(MODE_LABEL[t])
        node_modes.setdefault(tn, set()).add(MODE_LABEL[t])

    fig, axes = plt.subplots(2, 2, figsize=(15, 14))
    for ax, (typ, caption, fee) in zip(axes.ravel(), PANELS):
        sub = edges[edges["type"] == typ]
        pick = sub.loc[sub["len_m"].idxmax()]          # longest = most legible as a line
        cx, cy = pick.geometry.centroid.x, pick.geometry.centroid.y
        hw = max(pick["len_m"] * 2.5, 4000)            # window half-width (>= 4 km)
        ext = (cx - hw, cx + hw, cy - hw, cy + hw)

        if boundary is not None:
            boundary.plot(ax=ax, facecolor="#f7f5ef", edgecolor="#c8c1b0", linewidth=0.4, zorder=0)
        win = edges.cx[ext[0]:ext[1], ext[2]:ext[3]]   # everything in the window
        for t, g in win.groupby("type"):
            if t == typ:
                continue
            g.plot(ax=ax, color=COLOR.get(t, "#999"), linewidth=LW.get(t, 1.0),
                   alpha=0.9 if t in LINEHAUL else 0.6, zorder=2)
        # the highlighted connector + its endpoints
        gpd.GeoSeries([pick.geometry], crs=edges.crs).plot(
            ax=ax, color=COLOR[typ], linewidth=4.5, zorder=5, capstyle="round")
        xs, ys = pick.geometry.xy
        ax.scatter([xs[0], xs[-1]], [ys[0], ys[-1]], s=90, facecolor="white",
                   edgecolor="black", linewidth=1.4, zorder=6)

        a = "+".join(sorted(node_modes.get(int(pick["from"]), set()))) or "?"
        b = "+".join(sorted(node_modes.get(int(pick["to"]), set()))) or "?"
        ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"{typ} — {caption}\nendpoints: [{a}] ↔ [{b}] · {pick['len_m']/1000:.1f} km · {fee}",
                     fontsize=12, fontweight="bold", color=COLOR[typ])
        # context legend: which mode colors appear
        modes_here = [t for t in ("Road", "Waterway", "IceRoad", "Air") if t in set(win["type"])]
        h = [Line2D([0], [0], color=COLOR[m], lw=2.4, label=MODE_LABEL[m]) for m in modes_here]
        h.append(Line2D([0], [0], color=COLOR[typ], lw=3.2, label=typ))
        ax.legend(handles=h, loc="lower left", fontsize=8, frameon=True)

    fig.suptitle("Synthetic connectors in context — one representative edge per type (zoomed)",
                 fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=190, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
