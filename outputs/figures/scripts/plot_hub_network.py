#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_hub_network.py

Hub-focused companion figures to plot_weighted_network.py: the same 12-month
weighted-edge grid (light/dark themes, Alaska land basemap, plasma per-mile
intensity with the mode-band colorbar) with the plain hub dots replaced by a
richer hub layer:

  • hubs_by_type{_dark}.{png,pdf}     — 384 hubs colored/marked by hub_type
      (Supplier vs Receiver), so supply sources stand out from receivers.
  • hubs_by_capacity{_dark}.{png,pdf} — same, plus point AREA proportional to
      tank capacity (hub_cap, gal), so large tank farms read big.

Reuses plot_weighted_network's style dict, edge loader, color norm, and
colorbar mode-band annotation so these stay visually consistent with the
weighted-network figure (which is left untouched).

No CLI args. Writes into outputs/figures/.

Usage:
    python plot_hub_network.py
"""

from __future__ import annotations

import logging
import sys

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.lines import Line2D

from plot_weighted_network import (
    LAYOUTS,
    MONTH_NAMES,
    NODES_SHP,
    OUT_DIR,
    STATES_SHP,
    STYLES,
    annotate_mode_bands,
    load_weighted_edges,
    mode_medians,
    shared_norm,
)

logger = logging.getLogger(__name__)

# Hub-type colors chosen to sit OUTSIDE the plasma edge ramp (purple->yellow)
# so hubs never blend into the backdrop, and to read on both themes.
HUB_TYPE_STYLE = {
    "Supplier": {"color": "#ff3b30", "marker": "^",
                 "label": "Supplier (fuel source)"},
    "Receiver": {"color": "#00c2ff", "marker": "o",
                 "label": "Receiver (community)"},
}

# Point-area range (pt^2) across the 12-month grid's small panels. Area is
# linear in tank capacity; a floor keeps the smallest tanks visible.
GRID_SIZE_MIN, GRID_SIZE_MAX = 3.0, 150.0
# Representative capacities (gal) to anchor the size legend.
SIZE_LEGEND_CAPS = (10_000, 100_000, 500_000, 1_500_000)


def _capacity_to_size(cap: np.ndarray, cap_min: float, cap_max: float,
                      s_min: float, s_max: float) -> np.ndarray:
    """Map tank capacity to marker area (pt^2), area proportional to capacity."""
    frac = (cap - cap_min) / (cap_max - cap_min)
    return s_min + frac * (s_max - s_min)


def _save(fig, stem, style) -> None:
    for ext in ("png", "pdf"):
        out = stem.with_suffix(f".{ext}")
        fig.savefig(out, bbox_inches="tight", facecolor=style["bg"])
        logger.info("wrote %s", out)
    plt.close(fig)


def plot_hub_grid(edges, hubs, land, norm, medians, ncols, nrows, fig_w,
                  stem, style, mode: str) -> None:
    """12-month weighted-edge grid (full network) with hubs overlaid.

    mode='type' colors/marks hubs Supplier vs Receiver; mode='capacity' also
    sizes each hub's point area by tank capacity. Edges are the full monthly
    plasma network — this IS the weighted-network figure with the hub layer
    swapped in.
    """
    cap = hubs["hub_cap_num"].to_numpy()
    cap_min, cap_max = float(np.nanmin(cap)), float(np.nanmax(cap))

    pad = 50_000
    xmin, ymin, xmax, ymax = edges.total_bounds
    w, h = xmax - xmin + 2 * pad, ymax - ymin + 2 * pad
    fig_h = fig_w / ncols / (w / h) * nrows
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(fig_w, fig_h), facecolor=style["bg"],
        gridspec_kw={"wspace": 0.01, "hspace": 0.01, "left": 0.003,
                     "right": 0.997, "top": 0.985, "bottom": 0.055},
    )
    for month, ax in enumerate(axes.flat, start=1):
        ax.set_facecolor(style["bg"])
        land.plot(ax=ax, facecolor=style["land_face"],
                  edgecolor=style["land_edge"], linewidth=0.3, zorder=0)
        sub = edges[edges[f"pass_{month:02d}"].to_numpy()]
        is_air = (sub["type"] == "Air").to_numpy()
        col = f"wt_{month:02d}"
        sub[~is_air].plot(ax=ax, column=col, cmap=style["cmap"], norm=norm,
                          linewidth=0.55, rasterized=True, zorder=1)
        sub[is_air].plot(ax=ax, column=col, cmap=style["cmap"], norm=norm,
                         linewidth=0.6, linestyle=(0, (4, 3)),
                         rasterized=True, zorder=1)
        for htype, hs in HUB_TYPE_STYLE.items():
            sel = hubs[hubs["hub_type"] == htype]
            if mode == "capacity":
                s = _capacity_to_size(sel["hub_cap_num"].to_numpy(), cap_min,
                                      cap_max, GRID_SIZE_MIN, GRID_SIZE_MAX)
            else:
                s = 16
            ax.scatter(sel.geometry.x, sel.geometry.y, s=s, c=hs["color"],
                       marker=hs["marker"], edgecolors=style["hub"],
                       linewidths=0.3, alpha=0.9, zorder=5)
        ax.set_xlim(xmin - pad, xmax + pad)
        ax.set_ylim(ymin - pad, ymax + pad)
        ax.set_aspect("equal")
        ax.set_axis_off()
        ax.text(0.02, 0.97, MONTH_NAMES[month - 1], transform=ax.transAxes,
                va="top", ha="left", fontsize=12, fontweight="bold",
                color=style["fg"])

    cbar = fig.colorbar(ScalarMappable(norm=norm, cmap=style["cmap"]),
                        ax=axes, fraction=0.015, pad=0.005)
    cbar.set_label("combined traversal intensity — friction × cost rate "
                   "($/gal·mi, log)", fontsize=10, color=style["fg"])
    cbar.ax.tick_params(labelsize=8, color=style["fg"], labelcolor=style["fg"])
    cbar.outline.set_edgecolor(style["fg"])
    annotate_mode_bands(cbar, norm, medians, style["fg"])

    handles = [
        Line2D([0], [0], marker=hs["marker"], color="none",
               markerfacecolor=hs["color"], markeredgecolor=style["hub"],
               markersize=9,
               label=f"{hs['label']} — {len(hubs[hubs['hub_type'] == ht])}")
        for ht, hs in HUB_TYPE_STYLE.items()
    ]
    if mode == "capacity":
        handles += [
            Line2D([0], [0], marker="o", color="none",
                   markerfacecolor=style["fg"], markeredgecolor=style["hub"],
                   markersize=np.sqrt(_capacity_to_size(
                       np.array([c]), cap_min, cap_max,
                       GRID_SIZE_MIN, GRID_SIZE_MAX)[0]),
                   label=f"{c / 1000:,.0f}k gal")
            for c in SIZE_LEGEND_CAPS
        ]
    fig.legend(handles=handles, loc="lower center", ncol=len(handles),
               frameon=False, fontsize=9, labelcolor=style["fg"])

    _save(fig, stem, style)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    edges = load_weighted_edges()
    nodes = gpd.read_file(NODES_SHP)
    hubs = nodes[nodes["is_hub"] == 1].copy()
    hubs["hub_cap_num"] = pd.to_numeric(hubs["hub_cap"], errors="coerce")
    states = gpd.read_file(STATES_SHP)
    land = states[states["STUSPS"] == "AK"].to_crs(edges.crs)
    land["geometry"] = land.geometry.simplify(1000)
    logger.info("%d edges, %d hubs (%s)", len(edges), len(hubs),
                dict(hubs["hub_type"].value_counts()))

    norm = shared_norm(edges)
    medians = mode_medians(edges)
    _, ncols, nrows, fig_w = LAYOUTS[0]  # landscape 4x3
    for style in STYLES.values():
        plot_hub_grid(edges, hubs, land, norm, medians, ncols, nrows, fig_w,
                      OUT_DIR / f"hubs_by_type{style['suffix']}",
                      style, mode="type")
        plot_hub_grid(edges, hubs, land, norm, medians, ncols, nrows, fig_w,
                      OUT_DIR / f"hubs_by_capacity{style['suffix']}",
                      style, mode="capacity")
    return 0


if __name__ == "__main__":
    sys.exit(main())
