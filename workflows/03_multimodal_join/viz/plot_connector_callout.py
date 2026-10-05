#!/usr/bin/env python3
"""Locator-callout figure: Alaska in the centre, four zoomed connector insets around it.

The central map shows the whole network (faint, by mode) with a numbered box at each
example's location; leader lines connect each box to its zoomed inset. One example per
type: RoadConnector, IceRoadRoadTransfer, AirRoadTransfer, BargeRoadTransfer.
Writes outputs/final_network_plots/connector_callout.png.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import ConnectionPatch, Rectangle

ROOT = Path(__file__).resolve().parents[3]
EDGES = ROOT / "final_network" / "network_joined_edges" / "network_joined_edges.shp"
BOUNDARY = ROOT / "data" / "boundary.geojson"
OUT = ROOT / "outputs" / "final_network_plots" / "connector_callout.png"

COLOR = {
    "Road": "#555555", "Waterway": "#1560a8", "IceRoad": "#12aebd", "Air": "#8452b8",
    "RoadConnector": "#ff7f0e", "IceRoadConnector": "#b5a800",
    "BargeRoadTransfer": "#d62728", "BargeIceRoadTransfer": "#e377c2",
    "IceRoadRoadTransfer": "#2ca02c", "AirRoadTransfer": "#7b3f00",
}
LINEHAUL = {"Road", "Waterway", "IceRoad", "Air"}
MODE_LABEL = {"Road": "Road", "IceRoad": "IceRoad", "Waterway": "Barge", "Air": "Air"}
LW = {"Road": 1.2, "Waterway": 1.8, "IceRoad": 2.2, "Air": 1.6}
LAND_FACE, LAND_EDGE = "#e3e3e3", "#9e9e9e"   # neutral gray basemap so colors pop

PANELS = [
    ("RoadConnector", "welds two road segments", "no transfer fee"),
    ("IceRoadRoadTransfer", "ice road ↔ road", "$0.022/gal"),
    ("AirRoadTransfer", "air ↔ road", "$0.025/gal"),
    ("BargeRoadTransfer", "barge ↔ road", "$0.24/gal"),
]
# figure-coord rects for the 4 insets (TL, TR, BL, BR) and the inner-edge anchor for leaders
INSET_POS = [
    ([0.015, 0.545, 0.265, 0.40], (1.0, 0.5)),
    ([0.720, 0.545, 0.265, 0.40], (0.0, 0.5)),
    ([0.015, 0.055, 0.265, 0.40], (1.0, 0.5)),
    ([0.720, 0.055, 0.265, 0.40], (0.0, 0.5)),
]


def _nice(x):
    import math
    exp = math.floor(math.log10(x)); f = x / 10 ** exp
    nf = 1 if f < 1.5 else 2 if f < 3.5 else 5 if f < 7.5 else 10
    return nf * 10 ** exp


def _scale_bar(ax):
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    w, h = x1 - x0, y1 - y0
    L = _nice(w * 0.25)                      # bar length in metres, rounded
    xr = x1 - 0.06 * w; xl = xr - L; yb = y0 + 0.06 * h
    ax.plot([xl, xr], [yb, yb], color="black", lw=2.5, solid_capstyle="butt", zorder=9)
    for xx in (xl, xr):
        ax.plot([xx, xx], [yb, yb + 0.013 * h], color="black", lw=2.5, zorder=9)
    label = f"{L/1000:.0f} km" if L >= 1000 else f"{L:.0f} m"
    ax.text((xl + xr) / 2, yb + 0.02 * h, label, ha="center", va="bottom",
            fontsize=8, fontweight="bold", zorder=9)


def _north_arrow(ax):
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    x = x0 + 0.93 * (x1 - x0); ytop = y0 + 0.95 * (y1 - y0); ybot = y0 + 0.86 * (y1 - y0)
    ax.annotate("", xy=(x, ytop), xytext=(x, ybot),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.8), zorder=9)
    ax.text(x, ytop, "N", ha="center", va="bottom", fontsize=9, fontweight="bold", zorder=9)


def _draw_inset(ax, edges, boundary, pick, typ, node_modes, letter, fee):
    cx, cy = pick.geometry.centroid.x, pick.geometry.centroid.y
    hw = max(pick["len_m"] * 2.5, 4000)
    ext = (cx - hw, cx + hw, cy - hw, cy + hw)
    if boundary is not None:
        boundary.plot(ax=ax, facecolor=LAND_FACE, edgecolor=LAND_EDGE, linewidth=0.4, zorder=0)
    win = edges.cx[ext[0]:ext[1], ext[2]:ext[3]]
    for t, g in win.groupby("type"):
        if t == typ:
            continue
        g.plot(ax=ax, color=COLOR.get(t, "#999"), linewidth=LW.get(t, 1.0),
               alpha=0.9 if t in LINEHAUL else 0.6, zorder=2)
    gpd.GeoSeries([pick.geometry], crs=edges.crs).plot(
        ax=ax, color=COLOR[typ], linewidth=4.5, zorder=5, capstyle="round")
    xs, ys = pick.geometry.xy
    ax.scatter([xs[0], xs[-1]], [ys[0], ys[-1]], s=80, facecolor="white",
               edgecolor="black", linewidth=1.3, zorder=6)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():                       # black inset border
        s.set_edgecolor("black"); s.set_linewidth(1.6)
    a = "+".join(sorted(node_modes.get(int(pick["from"]), set()))) or "?"
    b = "+".join(sorted(node_modes.get(int(pick["to"]), set()))) or "?"
    ax.set_title(f"{typ}\n{a} ↔ {b} · {pick['len_m']/1000:.1f} km · {fee}",
                 fontsize=10.5, fontweight="bold", color="black")
    ax.text(0.035, 0.955, f"({letter})", transform=ax.transAxes, fontsize=15,
            fontweight="bold", color="black", va="top", ha="left", zorder=8,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="black", lw=1.2))
    _scale_bar(ax); _north_arrow(ax)
    modes_here = [t for t in ("Road", "Waterway", "IceRoad", "Air") if t in set(win["type"])]
    h = [Line2D([0], [0], color=COLOR[m], lw=2.2, label=MODE_LABEL[m]) for m in modes_here]
    h.append(Line2D([0], [0], color=COLOR[typ], lw=3.0, label=typ))
    ax.legend(handles=h, loc="lower left", fontsize=7, frameon=True)
    return (cx, cy)


def main() -> None:
    edges = gpd.read_file(EDGES)
    edges["len_m"] = edges.geometry.length
    boundary = gpd.read_file(BOUNDARY).to_crs(edges.crs) if BOUNDARY.exists() else None

    node_modes: dict[int, set] = {}
    lh = edges[edges["type"].isin(LINEHAUL)]
    for fn, tn, t in zip(lh["from"], lh["to"], lh["type"]):
        node_modes.setdefault(fn, set()).add(MODE_LABEL[t])
        node_modes.setdefault(tn, set()).add(MODE_LABEL[t])

    fig = plt.figure(figsize=(17, 13))

    # central locator map
    cax = fig.add_axes([0.31, 0.13, 0.38, 0.74])
    if boundary is not None:
        boundary.plot(ax=cax, facecolor=LAND_FACE, edgecolor=LAND_EDGE, linewidth=0.6, zorder=0)
    for t in ("Road", "Waterway", "IceRoad", "Air"):
        edges[edges["type"] == t].plot(ax=cax, color=COLOR[t], linewidth=0.3, alpha=0.6,
                                       zorder=1, rasterized=True)
    xmin, ymin, xmax, ymax = edges.total_bounds
    cax.set_xlim(xmin, xmax); cax.set_ylim(ymin, ymax)
    cax.set_xticks([]); cax.set_yticks([])
    _scale_bar(cax); _north_arrow(cax)

    box_hw = 0.017 * (xmax - xmin)   # small locator box (avoid overlap)
    for i, ((pos, anchor), (typ, cap, fee)) in enumerate(zip(INSET_POS, PANELS)):
        letter = "abcd"[i]
        sub = edges[edges["type"] == typ]
        pick = sub.loc[sub["len_m"].idxmax()]
        iax = fig.add_axes(pos)
        cx, cy = _draw_inset(iax, edges, boundary, pick, typ, node_modes, letter, fee)
        # small color-coded box + matching letter on the central map
        cax.add_patch(Rectangle((cx - box_hw, cy - box_hw), 2 * box_hw, 2 * box_hw,
                                fill=False, edgecolor="black", linewidth=1.4, zorder=6))
        cax.annotate(f"({letter})", (cx + box_hw, cy + box_hw), xytext=(2, 1),
                     textcoords="offset points", fontsize=10, fontweight="bold",
                     color="black", ha="left", va="bottom", zorder=7,
                     bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8))
        # leader line from the box to the inset's inner edge
        con = ConnectionPatch(xyA=(cx, cy), coordsA=cax.transData,
                              xyB=anchor, coordsB=iax.transAxes,
                              color="black", linewidth=1.0, linestyle="--",
                              alpha=0.85, zorder=1)
        con.set_clip_on(False)
        fig.add_artist(con)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=185, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
