#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_friction_stack.py

Render the friction stack as PNGs. Seasonal modes (barge) get a 12-month
grid on a shared color scale so sea/river-ice gating in shoulder months is
visually obvious, in two layouts: landscape 3x4 ({mode}_monthly_friction.png)
and portrait 6x2 ({mode}_monthly_friction_portrait.png). Overland is
season-invariant (pure terrain — no road/ice-road burn-in), so it is drawn
once as a single panel ({mode}_friction.png), not a redundant 12-month grid.
Panel size is derived from the raster aspect so the maps fill their slots.

NoData is rendered two-tone using the canonical LULC water class as the
discriminator: NoData over water (iced/unnavigable in barge mode, all
water in overland mode) draws in pale ice blue, NoData over land in
light gray — so the winter sea-ice edge doesn't visually merge with the
coastline.

No CLI args. Reads from friction_paths defaults (FRICTION_DIR env var
overrides the output dir). Writes, under {friction_outputs}/, a monthly grid
{mode}_monthly_friction.png for seasonal modes and a single-panel
{mode}_friction.png for the season-invariant overland surface.

Usage:
    python -m friction_surface.viz.plot_friction_stack
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from rasterio.enums import Resampling

from ..friction_config import (
    FRICTION_NODATA,
    LULC_WATER_CLASS,
    MODES,
    RIVER_ICE_THRESHOLD,
    SEA_ICE_THRESHOLD,
)
from ..friction_paths import RASTER_FILES, get_friction_output_dir

logger = logging.getLogger(__name__)

MONTH_NAMES = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)

# Decimated row count for the read. Full rasters are ~16.5k x 28k; at 12
# subplots per figure, reading the full grid is overkill and slow.
# ~1200 rows keeps each subplot legible at 150 dpi at the enlarged panel
# sizes without the memory cost of holding 12 full rasters.
DECIMATED_ROWS = 1200

# (filename suffix, nrows, ncols, panel width in inches). Panel height
# follows from the raster aspect, so wider panels = bigger maps.
LAYOUTS = (
    ("", 3, 4, 6.5),           # landscape: wide screens / slides
    ("_portrait", 6, 2, 8.5),  # vertical stack: paper full-page figure
)


def _read_decimated(path: Path) -> np.ma.MaskedArray:
    """Read a friction raster downsampled by row target, masked on NoData."""
    with rasterio.open(path) as src:
        scale = DECIMATED_ROWS / src.height
        out_shape = (int(src.height * scale), int(src.width * scale))
        arr = src.read(
            1, out_shape=out_shape, resampling=Resampling.average,
        ).astype(np.float32)
    return np.ma.masked_where(arr == FRICTION_NODATA, arr)


# Continuous-mode colormap. magma reversed so low friction reads pale
# yellow (easy to traverse) and high friction near-black (hard), matching
# the Weiss et al. 2018 (Nature) travel-time / accessibility convention.
# Perceptually uniform, colorblind- and grayscale-safe.
CONTINUOUS_CMAP = "magma_r"

# Two-tone NoData underlay: index 0 = land, 1 = water. Colors follow the
# NSIDC / NASA sea-ice map convention (pale blue water, neutral gray land)
# using exact ColorBrewer Blues / gray endpoints, with a wide lightness gap
# from the saturated navigable-water color below for CVD/grayscale safety.
NODATA_LAND_COLOR = "#D9D9D9"
NODATA_WATER_COLOR = "#DEEBF7"
NODATA_ALPHA = 0.6
NODATA_CMAP = ListedColormap([NODATA_LAND_COLOR, NODATA_WATER_COLOR])

# Single-value (categorical) modes fill navigable cells with a saturated
# ColorBrewer Blues blue: open water (dark blue) vs iced water (pale blue,
# NODATA_WATER_COLOR) reads intuitively per NSIDC / cmocean `ice`.
NAVIGABLE_COLOR = "#3182BD"

# What each NoData tone MEANS differs by mode, so the legend text is
# mode-specific rather than a generic "water / land".
MODE_LEGEND = {
    "barge": (
        (NODATA_WATER_COLOR,
         f"Iced / unnavigable water — ice concentration > "
         f"{SEA_ICE_THRESHOLD:g} (sea) / {RIVER_ICE_THRESHOLD:g} (river): "
         f"impassable to barge (NoData)"),
        (NODATA_LAND_COLOR, "Land — not navigable by barge (NoData)"),
    ),
    "overland": (
        (NODATA_WATER_COLOR,
         "Open water — not traversable overland (NoData)"),
        (NODATA_LAND_COLOR,
         "Impassable land — glaciers, DEM gaps (NoData)"),
    ),
}
# Fallback for any future mode without tailored text.
DEFAULT_LEGEND = (
    (NODATA_WATER_COLOR, "Water (NoData)"),
    (NODATA_LAND_COLOR, "Land (NoData)"),
)


def _read_water_mask(shape: tuple[int, int]) -> np.ndarray:
    """Decimated boolean water mask from the canonical LULC raster.

    Nearest-neighbour resampling — LULC is categorical, averaging would
    fabricate classes along the coast.
    """
    with rasterio.open(RASTER_FILES["lulc"]) as src:
        lulc = src.read(1, out_shape=shape, resampling=Resampling.nearest)
    return lulc == LULC_WATER_CLASS


def _shared_color_range(arrays: list[np.ma.MaskedArray]) -> tuple[float, float]:
    """Common (vmin, vmax) across all months so months are comparable.

    Uses the 1st and 99th percentile of pooled valid values to keep the
    scale resilient to a handful of extreme pixels (e.g. snow_ice × mountain
    × continuous-permafrost = 5 × 1.75 × 1.5 = 13.125 in the long tail).
    """
    pooled = np.concatenate([a.compressed() for a in arrays])
    if pooled.size == 0:
        return 0.0, 1.0
    vmin = float(np.percentile(pooled, 1))
    vmax = float(np.percentile(pooled, 99))
    if vmin == vmax:
        # Single-valued mode (barge water = WATER_FRICTION_BARGE on all
        # navigable pixels) — pad so imshow doesn't collapse the colormap.
        vmin, vmax = vmin - 0.1, vmax + 0.1
    return vmin, vmax


def _is_categorical(arrays: list[np.ma.MaskedArray]) -> bool:
    """True when every valid cell across all months holds one value.

    Barge friction is exactly WATER_FRICTION_BARGE wherever a barge can go
    and NoData everywhere else, so a continuous colorbar would invent a
    gradient the data does not contain. Detect that and render a solid
    navigability fill + legend instead of a colorbar.
    """
    pooled = np.concatenate([a.compressed() for a in arrays])
    return pooled.size > 0 and bool(np.allclose(pooled, pooled[0]))


def _style_for(arrays: list[np.ma.MaskedArray]):
    """Shared cmap/vmin/vmax + categorical flag for a set of friction arrays."""
    categorical = _is_categorical(arrays)
    if categorical:
        # One friction value -> solid navigable fill, no colorbar.
        cmap = ListedColormap([NAVIGABLE_COLOR])
        vmin = vmax = None
    else:
        cmap = plt.get_cmap(CONTINUOUS_CMAP).copy()
        vmin, vmax = _shared_color_range(arrays)
    # Transparent NoData so the two-tone land/water underlay shows through.
    cmap.set_bad(alpha=0.0)
    return cmap, vmin, vmax, categorical


def plot_mode(mode: str, friction_dir: Path, output_dir: Path) -> None:
    """Render friction PNG(s) for a single mode.

    Overland is season-invariant (one overland.tif), so it renders as a
    single panel; seasonal modes render a 12-month grid per layout.
    """
    # Overland: month-invariant single surface -> one panel, not a 12x grid.
    single_overland = friction_dir / "overland.tif"
    if mode == "overland" and single_overland.exists():
        arr = _read_decimated(single_overland)
        water_mask = _read_water_mask(arr.shape)
        cmap, vmin, vmax, categorical = _style_for([arr])
        _render_single(
            mode, arr, water_mask, categorical, cmap, vmin, vmax,
            output_dir / f"{mode}_friction.png",
        )
        return

    paths = [friction_dir / f"{mode}_{m:02d}.tif" for m in range(1, 13)]
    missing = [p for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing {len(missing)} files for mode {mode!r}: "
            f"first missing = {missing[0]}"
        )

    arrays = [_read_decimated(p) for p in paths]
    water_mask = _read_water_mask(arrays[0].shape)
    cmap, vmin, vmax, categorical = _style_for(arrays)

    for suffix, nrows, ncols, panel_w in LAYOUTS:
        output_path = output_dir / f"{mode}_monthly_friction{suffix}.png"
        _render_grid(
            mode, arrays, water_mask, categorical, cmap, vmin, vmax,
            nrows, ncols, panel_w, output_path,
        )


def _render_single(
    mode: str,
    arr: np.ma.MaskedArray,
    water_mask: np.ndarray,
    categorical: bool,
    cmap,
    vmin: float | None,
    vmax: float | None,
    output_path: Path,
) -> None:
    """Draw one season-invariant friction surface as a single panel."""
    aspect = arr.shape[1] / arr.shape[0]
    panel_w = 9.0
    fig, ax = plt.subplots(figsize=(panel_w, panel_w / aspect + 1.6),
                           constrained_layout=True)
    ax.imshow(water_mask, cmap=NODATA_CMAP, vmin=0, vmax=1,
              interpolation="nearest", alpha=0.6)
    if categorical:
        im = ax.imshow(arr, cmap=cmap)
    else:
        im = ax.imshow(arr, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks([])
    ax.set_yticks([])

    compressed = arr.compressed() if np.ma.is_masked(arr) else arr.ravel()
    valid_n = compressed.size
    mean_f = float(compressed.mean()) if valid_n else float("nan")

    if categorical:
        fig.suptitle(
            f"{mode.capitalize()} friction — season-invariant "
            f"(navigable = {compressed[0]:.2f}, else NoData)",
            fontsize=14,
        )
        extra_handles = [
            Patch(facecolor=NAVIGABLE_COLOR,
                  label=f"Navigable (friction = {compressed[0]:.2f})"),
        ]
    else:
        fig.suptitle(
            f"{mode.capitalize()} friction — season-invariant "
            f"(valid={valid_n / 1e3:.0f}k, mean={mean_f:.3f})",
            fontsize=14,
        )
        fig.colorbar(im, ax=ax, shrink=0.7,
                     label="friction (unitless, valid cells only)")
        extra_handles = []

    handles = extra_handles + [
        Patch(facecolor=color, alpha=NODATA_ALPHA, edgecolor="gray",
              label=label)
        for color, label in MODE_LEGEND.get(mode, DEFAULT_LEGEND)
    ]
    fig.legend(
        handles=handles, loc="lower center", ncol=len(handles),
        fontsize=10, frameon=False,
    )
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("wrote %s", output_path)


def _render_grid(
    mode: str,
    arrays: list[np.ma.MaskedArray],
    water_mask: np.ndarray,
    categorical: bool,
    cmap,
    vmin: float | None,
    vmax: float | None,
    nrows: int,
    ncols: int,
    panel_w: float,
    output_path: Path,
) -> None:
    """Draw one nrows x ncols monthly grid and save it."""
    # Panel height follows the raster aspect; the extra 1.6 in absorbs the
    # suptitle and bottom legend so panels keep their full width.
    aspect = arrays[0].shape[1] / arrays[0].shape[0]
    figsize = (ncols * panel_w, nrows * panel_w / aspect + 1.6)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize,
                             constrained_layout=True)
    last_im = None
    for idx, (month_idx, arr) in enumerate(zip(range(1, 13), arrays)):
        ax = axes.flat[idx]
        ax.imshow(water_mask, cmap=NODATA_CMAP, vmin=0, vmax=1,
                  interpolation="nearest", alpha=0.6)
        if categorical:
            last_im = ax.imshow(arr, cmap=cmap)
        else:
            last_im = ax.imshow(arr, cmap=cmap, vmin=vmin, vmax=vmax)
        compressed = arr.compressed() if np.ma.is_masked(arr) else arr.ravel()
        valid_n = compressed.size
        mean_f = float(compressed.mean()) if valid_n else float("nan")
        ax.set_title(
            f"{MONTH_NAMES[month_idx - 1]}   "
            f"valid={valid_n / 1e3:.0f}k   mean={mean_f:.3f}",
            fontsize=11,
        )
        ax.set_xticks([])
        ax.set_yticks([])

    if categorical:
        fig.suptitle(
            f"{mode.capitalize()} friction — monthly stack "
            f"(navigable = {compressed[0]:.2f}, else NoData)",
            fontsize=14,
        )
        # No colorbar for a single value; navigable class leads the legend.
        extra_handles = [
            Patch(facecolor=NAVIGABLE_COLOR,
                  label=f"Navigable by barge (friction = {compressed[0]:.2f})"),
        ]
    else:
        fig.suptitle(
            f"{mode.capitalize()} friction — monthly stack "
            f"(vmin={vmin:.2f}, vmax={vmax:.2f})",
            fontsize=14,
        )
        fig.colorbar(
            last_im, ax=list(axes.flat),
            shrink=0.6, label="friction (unitless, valid cells only)",
        )
        extra_handles = []

    handles = extra_handles + [
        Patch(facecolor=color, alpha=NODATA_ALPHA, edgecolor="gray",
              label=label)
        for color, label in MODE_LEGEND.get(mode, DEFAULT_LEGEND)
    ]
    fig.legend(
        handles=handles, loc="lower center", ncol=len(handles),
        fontsize=10, frameon=False,
    )
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("wrote %s", output_path)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    friction_dir = Path(get_friction_output_dir())
    if not friction_dir.is_dir():
        logger.error("friction directory does not exist: %s", friction_dir)
        return 2

    # Drop the PNGs next to the friction_stack/ folder so they're easy to
    # find without polluting the raster directory itself.
    output_dir = friction_dir.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    for mode in MODES:
        plot_mode(mode, friction_dir, output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
