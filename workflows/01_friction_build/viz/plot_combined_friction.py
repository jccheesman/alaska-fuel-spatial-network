#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_combined_friction.py

Publication friction figures. Overland friction is month-invariant, so it is
drawn once (not as a redundant 12-month grid); barge navigability is seasonal
and drawn per month. Overland uses a continuous magma_r colorbar (low friction
pale, high dark, per the Weiss et al. 2018 accessibility convention); barge is a
single-valued navigability field rendered categorically (solid blue navigable
water, no colorbar). The two modes occupy very different value spaces, so each
is styled to its own data.

Reuses the exact NoData / water-mask / color-range logic and config
constants from plot_friction_stack.py so the composite is consistent
with the standalone per-mode PNGs.

No CLI args. Reads from friction_paths defaults. Writes:
  • combined_overland_barge.{png,pdf} — stacked: one overland panel on top
      (month-invariant, so no redundant 12-month grid), 12 monthly barge
      panels (3x4) beneath.
  • network_on_friction.{png,pdf}     — routed land network (road + ice-road
      edges from final_network) overlaid on the overland friction map.
All under {friction_outputs}/.

Usage:
    python -m friction_surface.viz.plot_combined_friction
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

from ..friction_paths import get_friction_output_dir
from .plot_friction_stack import (
    CONTINUOUS_CMAP,
    DEFAULT_LEGEND,
    MODE_LEGEND,
    MONTH_NAMES,
    NAVIGABLE_COLOR,
    NODATA_ALPHA,
    NODATA_CMAP,
    _read_decimated,
    _read_water_mask,
    _shared_color_range,
)

logger = logging.getLogger(__name__)

# Formal / print styling. Serif body, restrained line weights, higher DPI
# than the working plots since this is the camera-ready composite.
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Times New Roman", "Nimbus Roman"],
    "mathtext.fontset": "dejavuserif",
    "axes.linewidth": 0.6,
    "axes.edgecolor": "0.3",
    "figure.dpi": 150,
    "savefig.dpi": 300,
})


def plot_overland_barge(friction_dir: Path, output_stem: Path,
                        figsize: tuple[float, float] = (13.0, 11.5)) -> None:
    """Stacked composite: one overland panel on top, 12 monthly barge below.

    Overland is month-invariant (pure terrain — no road/ice-road burn-in), so
    its stack collapses to a single panel read from overland_01.tif. Barge is
    genuinely seasonal, so all 12 months are shown as a 3x4 grid beneath.
    """
    # --- Overland: one panel (all 12 months are identical) ---
    # Deduped stack writes a single month-invariant overland.tif (fall back to
    # the legacy per-month overland_01.tif if that is what is on disk).
    ov_path = friction_dir / "overland.tif"
    if not ov_path.exists():
        ov_path = friction_dir / "overland_01.tif"
    if not ov_path.exists():
        raise FileNotFoundError(f"overland raster missing: {ov_path}")
    ov = _read_decimated(ov_path)
    ov_water = _read_water_mask(ov.shape)
    ov_cmap = plt.get_cmap(CONTINUOUS_CMAP).copy()
    ov_cmap.set_bad(alpha=0.0)
    vmin, vmax = _shared_color_range([ov])

    # --- Barge: 12 monthly panels ---
    barge_paths = [friction_dir / f"barge_{m:02d}.tif" for m in range(1, 13)]
    missing = [p for p in barge_paths if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing {len(missing)} barge files: first = {missing[0]}"
        )
    barge_arrays = [_read_decimated(p) for p in barge_paths]
    b_water = _read_water_mask(barge_arrays[0].shape)
    b_cmap = ListedColormap([NAVIGABLE_COLOR])
    b_cmap.set_bad(alpha=0.0)

    fig = plt.figure(figsize=figsize)
    top, bot = fig.subfigures(2, 1, height_ratios=[3.9, 7.1])

    # ---- top: single centered overland map, colorbar + NoData key below ----
    top.suptitle("(a) Overland friction — identical for all 12 months",
                 fontsize=13, y=0.99)
    # Symmetric side columns keep the map centered; the colorbar and the
    # NoData key stack in the space reserved beneath it (bottom margin).
    t_axes = top.subplots(
        1, 3, gridspec_kw={"width_ratios": [0.8, 2.6, 0.8], "wspace": 0.04,
                           "top": 0.95, "bottom": 0.22},
    )
    t_axes[0].axis("off")
    t_axes[2].axis("off")
    ax_ov = t_axes[1]
    ax_ov.imshow(ov_water, cmap=NODATA_CMAP, vmin=0, vmax=1,
                 interpolation="nearest", alpha=NODATA_ALPHA)
    im = ax_ov.imshow(ov, cmap=ov_cmap, vmin=vmin, vmax=vmax)
    ax_ov.set_xticks([])
    ax_ov.set_yticks([])
    cbar = top.colorbar(im, ax=ax_ov, location="bottom",
                        shrink=0.75, pad=0.04, fraction=0.05, aspect=35)
    cbar.set_label("friction (valid cells only)", fontsize=9)
    cbar.ax.tick_params(labelsize=8)
    # Overland NoData key centered just below the colorbar.
    ov_handles = [
        Patch(facecolor=color, alpha=NODATA_ALPHA, edgecolor="gray", label=label)
        for color, label in MODE_LEGEND.get("overland", DEFAULT_LEGEND)
    ]
    top.legend(handles=ov_handles, loc="lower center", ncol=1,
               fontsize=7.5, frameon=False, bbox_to_anchor=(0.5, 0.03))

    # ---- bottom: 3x4 monthly barge grid ----
    bot.suptitle("(b) Barge friction — by month", fontsize=13, y=1.0)
    b_axes = bot.subplots(
        3, 4, gridspec_kw={"wspace": 0.05, "hspace": 0.15,
                           "top": 0.93, "bottom": 0.07},
    )
    for idx, arr in enumerate(barge_arrays):
        ax = b_axes.flat[idx]
        ax.imshow(b_water, cmap=NODATA_CMAP, vmin=0, vmax=1,
                  interpolation="nearest", alpha=NODATA_ALPHA)
        ax.imshow(arr, cmap=b_cmap)
        ax.set_title(MONTH_NAMES[idx], fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
    b_handles = [Patch(facecolor=NAVIGABLE_COLOR,
                       label="Navigable by barge (friction = 1.00)")]
    b_handles += [
        Patch(facecolor=color, alpha=NODATA_ALPHA, edgecolor="gray", label=label)
        for color, label in MODE_LEGEND.get("barge", DEFAULT_LEGEND)
    ]
    bot.legend(handles=b_handles, loc="lower center", ncol=1,
               fontsize=7.5, frameon=False)

    fig.suptitle(
        "Environmental friction stack — overland (annual) vs. monthly barge",
        fontsize=16, fontweight="bold", y=1.02,
    )

    for ext in ("png", "pdf"):
        out = output_stem.with_suffix(f".{ext}")
        fig.savefig(out, bbox_inches="tight")
        logger.info("wrote %s", out)
    plt.close(fig)


def plot_network_on_friction(friction_dir: Path, output_stem: Path,
                             figsize: tuple[float, float] = (12.0, 9.5)) -> None:
    """Overland friction basemap with the routed land network overlaid.

    Road (solid) and ice-road (dashed) edges from final_network are drawn on
    top of the overland terrain-friction surface so the actual routes are
    visible against the terrain they cross. This is the correct way to "see the
    roads": roads are edge geometries the network layer samples along, not
    anything stored in a friction raster (road_base is a full-grid road-grade
    surface, not a picture of roads).
    """
    import rasterio
    import geopandas as gpd
    from matplotlib.lines import Line2D

    ov_path = friction_dir / "overland.tif"  # month-invariant (deduped stack)
    if not ov_path.exists():
        ov_path = friction_dir / "overland_01.tif"  # legacy per-month layout
    if not ov_path.exists():
        raise FileNotFoundError(f"overland raster missing: {ov_path}")
    over = _read_decimated(ov_path)
    with rasterio.open(ov_path) as src:
        b = src.bounds
        raster_crs = src.crs
    extent = (b.left, b.right, b.bottom, b.top)
    water_mask = _read_water_mask(over.shape)
    cmap = plt.get_cmap(CONTINUOUS_CMAP).copy()
    cmap.set_bad(alpha=0.0)
    vmin, vmax = _shared_color_range([over])

    # Routed edges (already EPSG:3338); split into the two land route types.
    edges_path = (Path(__file__).resolve().parents[2] / "final_network"
                  / "network_joined_edges" / "network_joined_edges.shp")
    edges = gpd.read_file(edges_path)
    if str(edges.crs) != str(raster_crs):
        edges = edges.to_crs(raster_crs)
    roads = edges[edges["type"] == "Road"]
    ice = edges[edges["type"] == "IceRoad"]

    ROAD_C = "#1aa7ff"   # cyan-blue: pops on the orange/red land friction
    ICE_C = "#39ff14"    # lime: pops on the dark high-friction north

    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(water_mask, extent=extent, origin="upper", cmap=NODATA_CMAP,
              vmin=0, vmax=1, interpolation="nearest", alpha=NODATA_ALPHA)
    im = ax.imshow(over, extent=extent, origin="upper", cmap=cmap,
                   vmin=vmin, vmax=vmax)
    roads.plot(ax=ax, color=ROAD_C, linewidth=0.5)
    ice.plot(ax=ax, color=ICE_C, linewidth=1.3, linestyle=(0, (3, 2)))
    ax.set_xlim(b.left, b.right)
    ax.set_ylim(b.bottom, b.top)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Routed land network over overland friction",
                 fontsize=14, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, location="bottom", shrink=0.6, pad=0.03,
                        fraction=0.045, aspect=40)
    cbar.set_label("overland friction (valid cells only)", fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    handles = [
        Line2D([0], [0], color=ROAD_C, lw=1.6,
               label=f"Road edges ({len(roads):,})"),
        Line2D([0], [0], color=ICE_C, lw=1.8, linestyle=(0, (3, 2)),
               label=f"Ice-road edges ({len(ice):,})"),
    ]
    handles += [
        Patch(facecolor=color, alpha=NODATA_ALPHA, edgecolor="gray", label=label)
        for color, label in MODE_LEGEND.get("overland", DEFAULT_LEGEND)
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=8, frameon=True,
              framealpha=0.9)

    for ext in ("png", "pdf"):
        out = output_stem.with_suffix(f".{ext}")
        fig.savefig(out, bbox_inches="tight")
        logger.info("wrote %s", out)
    plt.close(fig)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    friction_dir = Path(get_friction_output_dir())
    if not friction_dir.is_dir():
        logger.error("friction directory does not exist: %s", friction_dir)
        return 2

    # Stacked overland-on-top / barge-by-month composite.
    plot_overland_barge(
        friction_dir, friction_dir.parent / "combined_overland_barge"
    )

    # Routed land network (roads + ice roads) over the overland friction basemap.
    plot_network_on_friction(
        friction_dir, friction_dir.parent / "network_on_friction"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
