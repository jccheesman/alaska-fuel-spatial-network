#!/usr/bin/env python3
"""Render the new network-of-record's edges by type: a statewide map + small multiples.

Two figures under outputs/final_network_plots/:
  - edge_types_statewide.png       — every edge colored by type, one legend w/ counts
  - edge_types_small_multiples.png — one panel per type, highlighted over faint context

Reads the frozen final_network edges (EPSG:3338). Everything is drawn as LINES (no
point markers): line-haul modes are visible but restrained, synthetic connectors are
bold and on top. Synthetic connectors are short (a weld/transfer spans a few hundred
metres), so they're drawn thick to read as strokes at statewide scale.
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
OUTDIR = ROOT / "outputs" / "final_network_plots"

# draw order: line-haul first (base), connectors, then transfers on top
LINEHAUL = ["Road", "Waterway", "IceRoad", "Air"]
CONNECTORS = ["RoadConnector", "IceRoadConnector"]
TRANSFERS = ["BargeRoadTransfer", "BargeIceRoadTransfer", "IceRoadRoadTransfer", "AirRoadTransfer"]
ORDER = LINEHAUL + CONNECTORS + TRANSFERS

COLOR = {
    "Road": "#3a3a3a", "Waterway": "#1560a8", "IceRoad": "#12aebd", "Air": "#8452b8",
    "RoadConnector": "#ff7f0e", "IceRoadConnector": "#b5a800",
    "BargeRoadTransfer": "#d62728", "BargeIceRoadTransfer": "#e377c2",
    "IceRoadRoadTransfer": "#2ca02c", "AirRoadTransfer": "#7b3f00",
}
# statewide linewidths — line-haul now clearly visible; connectors/transfers bold
# with a PROJECTING cap so a short segment reads as an oriented stroke, not a dot.
LW_STATE = {"Road": 0.55, "Waterway": 0.65, "IceRoad": 1.3, "Air": 0.7,
            "RoadConnector": 1.8, "IceRoadConnector": 2.6,
            "BargeRoadTransfer": 3.0, "BargeIceRoadTransfer": 3.4,
            "IceRoadRoadTransfer": 3.4, "AirRoadTransfer": 3.8}
ALPHA_STATE = {"Road": 0.85, "Waterway": 0.85, "IceRoad": 0.95, "Air": 0.7}


def _frame(ax, boundary, extent):
    if boundary is not None:
        boundary.plot(ax=ax, facecolor="#f7f5ef", edgecolor="#c8c1b0", linewidth=0.4, zorder=0)
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor("#bbb")


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    edges = gpd.read_file(EDGES)
    boundary = gpd.read_file(BOUNDARY).to_crs(edges.crs) if BOUNDARY.exists() else None
    counts = edges["type"].value_counts().to_dict()
    xmin, ymin, xmax, ymax = edges.total_bounds
    pad = 0.02 * (xmax - xmin)
    extent = (xmin - pad, xmax + pad, ymin - pad, ymax + pad)
    by = {t: edges[edges["type"] == t] for t in ORDER}

    # ---- Figure 1: statewide, all types as lines ----
    fig, ax = plt.subplots(figsize=(15, 13))
    _frame(ax, boundary, extent)
    for t in ORDER:
        g = by[t]
        if not len(g):
            continue
        cap = "round" if t in LINEHAUL else "projecting"
        g.plot(ax=ax, color=COLOR[t], linewidth=LW_STATE[t],
               alpha=ALPHA_STATE.get(t, 0.95), capstyle=cap,
               zorder=(2 if t in LINEHAUL else 5), rasterized=(t in LINEHAUL))
    handles = [Line2D([0], [0], color=COLOR[t], lw=3.0, label=f"{t} ({counts.get(t, 0):,})")
               for t in ORDER if counts.get(t)]
    ax.legend(handles=handles, loc="lower left", fontsize=10, frameon=True,
              title="edge type (count)", title_fontsize=11)
    ax.set_title("Alaska fuel network — edges by type (network-of-record, mode-based connectors)",
                 fontsize=15, fontweight="bold", loc="left")
    fig.tight_layout()
    p1 = OUTDIR / "edge_types_statewide.png"
    fig.savefig(p1, dpi=200, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {p1}")

    # ---- Figure 2: small multiples, one panel per type (lines only) ----
    # Line-haul panels stay statewide; the sparse connector/transfer panels ZOOM to
    # that type's own extent so their short segments actually read as lines.
    def _type_extent(g, min_km=120):
        x0, y0, x1, y1 = g.total_bounds
        # pad, and enforce a floor so a tightly-clustered type isn't over-zoomed
        px = max((x1 - x0) * 0.25, min_km * 1000)
        py = max((y1 - y0) * 0.25, min_km * 1000)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hw = max((x1 - x0) / 2 + px, (y1 - y0) / 2 + py)
        return (cx - hw, cx + hw, cy - hw, cy + hw)

    ncol, nrow = 5, 2
    fig, axes = plt.subplots(nrow, ncol, figsize=(24, 11))
    for ax, t in zip(axes.ravel(), ORDER):
        zoomed = t not in LINEHAUL and len(by[t])
        ext = _type_extent(by[t]) if zoomed else extent
        _frame(ax, boundary, ext)
        edges.plot(ax=ax, color="#e2ddd2", linewidth=0.2, zorder=1, rasterized=True)  # faint context
        lw = 0.7 if t in LINEHAUL else (2.2 if t in CONNECTORS else 3.0)
        by[t].plot(ax=ax, color=COLOR[t], linewidth=lw, zorder=4, capstyle="projecting")
        tag = "  [zoomed]" if zoomed else ""
        ax.set_title(f"{t}  ({counts.get(t, 0):,}){tag}", fontsize=13, fontweight="bold", color=COLOR[t])
    for ax in axes.ravel()[len(ORDER):]:
        ax.axis("off")
    fig.suptitle("Alaska fuel network — edge types (line-haul statewide; connectors/transfers zoomed to extent)",
                 fontsize=16, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    p2 = OUTDIR / "edge_types_small_multiples.png"
    fig.savefig(p2, dpi=170, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {p2}")


if __name__ == "__main__":
    main()
