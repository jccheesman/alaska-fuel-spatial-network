#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_river_ice_marine_leak.py

Diagnostic map + monthly curve: where on the waterway network is a barge
blocked, and is that block physically real?

Every cell of the rasterized waterway network is sorted into one of three
states for the target month (default February, the worst case):

    navigable            barge_MM.tif has a valid friction value there
    blocked, real        blocked, and either the cell is a freshwater river
                         (where river ice belongs) or the open water around
                         it is blocked too, i.e. sea ice is doing it
    blocked, leak        blocked, on SALT water, while off-network open water
                         within PROBE_RADIUS_PX is navigable this month.
                         Nothing in the sea-ice field explains the closure.

That third class is the regression this figure exists to catch: river ice
reaching salt water through the unbounded nearest-neighbour fill in
friction_surface.extend_ice_nearest. Off-network water carries no river-ice
signal at all (the fill only ever writes to waterway cells), so a navigable
off-network pixel next to a blocked network pixel is direct evidence that sea
ice is not the cause — which is what makes this runnable against a shipped
friction stack with no access to the ice inputs.

On a correctly built stack the leak class is EMPTY. Before the river/marine
split it held 288,954 cells in February — 58% of the whole network, including
every cell in the Gulf of Alaska, the Inside Passage and around Kodiak.

Requires waterway_river_mask_150m.tif (written by 01_build_corridor_masks.py).

Usage:
    python plot_river_ice_marine_leak.py
    python plot_river_ice_marine_leak.py --month 12
    python plot_river_ice_marine_leak.py --out outputs/analysis/leak_dec.png
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import matplotlib
import numpy as np
import pyproj
import rasterio
from rasterio.windows import Window
from scipy.ndimage import binary_dilation

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from friction_surface.friction_config import FRICTION_NODATA  # noqa: E402
from friction_surface.friction_paths import (  # noqa: E402
    WATERWAY_MASK_TIF,
    WATERWAY_RIVER_MASK_TIF,
    get_friction_output_dir,
)

logger = logging.getLogger(__name__)

# Palette. Validated with the dataviz validator on the #fcfcfb surface,
# all-pairs: worst CVD dE 13.0, worst normal-vision dE 16.3, all >= 3:1
# contrast. Do not substitute by eye.
C_NAV = "#2a78d6"      # blue    — navigable
C_REAL = "#4a3aa7"     # violet  — blocked, physically real
C_LEAK = "#d03b3b"     # red     — blocked, river-ice leak
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
WATER_BG = "#dde6f0"
LAND_BG = "#f0efec"
HAIRLINE = "#e1e0d9"
AXIS = "#c3c2b7"

PROBE_RADIUS_PX = 7    # ~1 km at 150 m: how far to look for ice-free water
DECIMATE = 6           # backdrop downsample factor
ROW_CHUNK = 3000

MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November",
               "December"]

# Ports annotated on the map. Chosen to span the argument: four Gulf/SE ports
# with year-round commercial barge service, two genuinely seasonal western /
# Arctic ports, and the Yukon as the freshwater reference.
ANNOTATIONS = [
    # (lon, lat, label, dx, dy, ha)
    (-131.70, 55.35, "Ketchikan",  95, 95, "left"),
    (-135.36, 57.05, "Sitka",     -250, 90, "right"),
    (-152.40, 57.79, "Kodiak",    -140, 190, "right"),
    (-149.42, 60.05, "Seward",     -70, -180, "right"),
    (-161.76, 60.79, "Bethel",    -230, -40, "right"),
    (-156.79, 71.30, "Utqiagvik",   60, -90, "left"),
    (-153.00, 64.50, "Yukon R.",   -40, -190, "right"),
]


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_network(friction_dir: Path, month: int) -> dict:
    """Sort every waterway cell into navigable / real block / leak for `month`.

    Streams the stack in row chunks so peak memory stays in the hundreds of
    MB rather than the ~25 GB a naive full read of 12 bands would need.
    """
    mw = rasterio.open(WATERWAY_MASK_TIF)
    if not Path(WATERWAY_RIVER_MASK_TIF).exists():
        raise FileNotFoundError(
            f"{WATERWAY_RIVER_MASK_TIF} not found. Run "
            "`python workflows/01_friction_build/01_build_corridor_masks.py` "
            "— it writes the freshwater-river mask alongside the waterway mask."
        )
    rv = rasterio.open(WATERWAY_RIVER_MASK_TIF)
    height, width = mw.height, mw.width
    labels = [f"{m:02d}" for m in range(1, 13)]
    srcs = {m: rasterio.open(friction_dir / f"barge_{m}.tif") for m in labels}
    target = f"{month:02d}"
    footprint = np.ones((2 * PROBE_RADIUS_PX + 1,) * 2, bool)

    cols: dict[str, list] = {k: [] for k in
                             ("row", "col", "blocked", "seafree", "river")}
    for r0 in range(0, height, ROW_CHUNK):
        h = min(ROW_CHUNK, height - r0)
        lo = max(0, r0 - PROBE_RADIUS_PX)
        hi = min(height, r0 + h + PROBE_RADIUS_PX)
        win = Window(0, lo, width, hi - lo)
        on_network = mw.read(1, window=win) == 1
        core = slice(r0 - lo, r0 - lo + h)
        if not on_network[core].any():
            continue

        bands = {m: (srcs[m].read(1, window=win) != FRICTION_NODATA)
                 for m in labels}
        # Any cell navigable in any month is water. Cheap stand-in for the
        # LULC water mask, which this script deliberately does not require.
        nav_water = np.zeros_like(on_network)
        for m in labels:
            nav_water |= bands[m]
        off_network = nav_water & ~on_network
        # Open water near this cell that sea ice is NOT closing this month.
        sea_free = binary_dilation(off_network & bands[target],
                                   structure=footprint)
        river = rv.read(1, window=win) == 1

        rr, cc = np.nonzero(on_network[core])
        rr_win = rr + (r0 - lo)
        cols["row"].append(rr + r0)
        cols["col"].append(cc)
        cols["blocked"].append(~bands[target][rr_win, cc])
        cols["seafree"].append(sea_free[rr_win, cc])
        cols["river"].append(river[rr_win, cc])
        logger.info("classified rows %d-%d", r0, r0 + h)

    out = {k: np.concatenate(v) for k, v in cols.items()}
    out["leak"] = out["blocked"] & ~out["river"] & out["seafree"]
    out["real"] = out["blocked"] & ~out["leak"]
    out["navigable"] = ~out["blocked"]
    out["transform"] = mw.transform
    return out


def monthly_open_fractions(friction_dir: Path, cells: dict) -> dict:
    """Open share by month for the map's three regions, as built and corrected.

    "Corrected" applies the sea-ice-only rule to salt water: a marine cell
    counts as open if ice-free water sits within PROBE_RADIUS_PX of it. River
    cells keep whatever the stack says, since river ice belongs there.
    """
    rows, cols = cells["row"], cells["col"]
    transform = cells["transform"]
    inv = pyproj.Transformer.from_crs("EPSG:3338", "EPSG:4326", always_xy=True)
    lon, lat = inv.transform(transform.c + (cols + 0.5) * transform.a,
                             transform.f + (rows + 0.5) * transform.e)
    regions = {
        "gulf": (lat > 54) & (lat < 61.5) & (lon > -155) & (lon < -130),
        "west": (lon < -158) | (lat > 66),
    }
    is_river = cells["river"]

    result = {f"{k}_{w}": [] for k in ("cur", "new") for w in regions}
    for month in range(1, 13):
        sub = classify_network(friction_dir, month)
        cur = sub["navigable"]
        new = cur | (~is_river & sub["seafree"])   # the fix can only OPEN cells
        for w, sel in regions.items():
            result[f"cur_{w}"].append(100.0 * cur[sel].mean())
            result[f"new_{w}"].append(100.0 * new[sel].mean())
    return result


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def water_backdrop(friction_dir: Path) -> np.ndarray:
    """Decimated land/water backdrop from the August (least-ice) surface."""
    src = rasterio.open(friction_dir / "barge_08.tif")
    h, w = src.height // DECIMATE, src.width // DECIMATE
    out = np.zeros((h, w), bool)
    step = 600 * DECIMATE
    for r0 in range(0, h * DECIMATE, step):
        hh = min(step, h * DECIMATE - r0)
        band = src.read(1, window=Window(0, r0, w * DECIMATE, hh))
        band = (band != FRICTION_NODATA).reshape(
            hh // DECIMATE, DECIMATE, w, DECIMATE).any(axis=(1, 3))
        out[r0 // DECIMATE:r0 // DECIMATE + hh // DECIMATE] = band
    return out


def render(cells: dict, monthly: dict, backdrop: np.ndarray, month: int,
           out_path: Path) -> Path:
    plt.rcParams.update({
        "font.family": ["DejaVu Sans"], "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    })
    fig = plt.figure(figsize=(13.5, 11.6), dpi=170)
    gs = fig.add_gridspec(2, 1, height_ratios=[2.35, 1.0], hspace=0.34,
                          left=0.045, right=0.975, top=0.855, bottom=0.075)

    # --- map ---------------------------------------------------------------
    ax = fig.add_subplot(gs[0])
    ax.imshow(np.where(backdrop, 0, 1).astype(float),
              cmap=matplotlib.colors.ListedColormap([WATER_BG, LAND_BG]),
              interpolation="nearest", zorder=0)
    x, y = cells["col"] / DECIMATE, cells["row"] / DECIMATE
    for key, color, z in [("navigable", C_NAV, 3), ("real", C_REAL, 4),
                          ("leak", C_LEAK, 5)]:
        sel = cells[key]
        ax.scatter(x[sel], y[sel], s=0.45, c=color, marker="s",
                   linewidths=0, zorder=z, rasterized=True)
    ax.set_xlim(300, backdrop.shape[1]); ax.set_ylim(2680, 120)
    ax.set_axis_off()

    fwd = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3338", always_xy=True)
    t = cells["transform"]
    style = dict(fontsize=10.5, color=INK, va="center", zorder=8,
                 bbox=dict(boxstyle="round,pad=0.28", fc=SURFACE,
                           ec=HAIRLINE, lw=0.8, alpha=0.92))
    for lon, lat, label, dx, dy, ha in ANNOTATIONS:
        px, py = fwd.transform(lon, lat)
        c = (px - t.c) / t.a / DECIMATE
        r = (py - t.f) / t.e / DECIMATE
        ax.annotate(label, (c, r), (c + dx, r + dy), textcoords="data", ha=ha,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.9,
                                    shrinkA=0, shrinkB=2), **style)

    n_leak, n_total = int(cells["leak"].sum()), cells["leak"].size
    ax.text(0.0, 1.135,
            f"{MONTH_NAMES[month]}: {n_leak:,} of {n_total:,} waterway cells "
            "are blocked by river ice that is not there",
            transform=ax.transAxes, fontsize=18, color=INK,
            fontweight="bold", va="bottom")
    ax.text(0.0, 1.028,
            "Every cell of the rasterized waterway network, classified for "
            f"{MONTH_NAMES[month]}. Red cells sit on salt water, are blocked, "
            "and have ice-free open water within 1 km of them —\nnothing in "
            "the sea-ice field explains the closure. They are interior river "
            "ice copied onto the marine network by the unbounded "
            "nearest-neighbour fill in extend_ice_nearest.",
            transform=ax.transAxes, fontsize=10.8, color=INK_2, va="bottom",
            linespacing=1.55)

    handles = [
        Line2D([], [], marker="s", ls="", ms=8, mfc=C_NAV, mec="none",
               label=f"navigable  ({int(cells['navigable'].sum()):,} cells)"),
        Line2D([], [], marker="s", ls="", ms=8, mfc=C_REAL, mec="none",
               label=f"blocked, physically real  ({int(cells['real'].sum()):,})"),
        Line2D([], [], marker="s", ls="", ms=8, mfc=C_LEAK, mec="none",
               label=f"blocked, river-ice leak  ({n_leak:,})"),
    ]
    leg = ax.legend(handles=handles, loc="upper left", frameon=True,
                    fontsize=11.5, facecolor=SURFACE, edgecolor=HAIRLINE,
                    borderpad=0.8, labelspacing=0.7, handletextpad=0.7,
                    bbox_to_anchor=(0.005, 0.985))
    leg.get_frame().set_linewidth(0.8)
    for text in leg.get_texts():
        text.set_color(INK)

    # --- monthly curve -----------------------------------------------------
    ax2 = fig.add_subplot(gs[1])
    months = np.arange(1, 13)
    series = [
        (monthly["cur_gulf"], C_LEAK, "Gulf / SE — as built"),
        (monthly["new_gulf"], C_NAV, "Gulf / SE — river ice confined to rivers"),
        (monthly["new_west"], C_REAL,
         "Western + Arctic — river ice confined to rivers"),
    ]
    for values, color, label in series:
        ax2.plot(months, values, color=color, lw=2.0, solid_capstyle="round",
                 zorder=3)
        ax2.plot(months, values, "o", color=color, ms=4.2, mec=SURFACE,
                 mew=1.4, zorder=4)
        ax2.annotate(label, (12, values[-1]), (12.35, values[-1]), color=color,
                     fontsize=10.6, va="center", ha="left", fontweight="medium")
    ax2.set_ylim(-4, 112); ax2.set_xlim(0.6, 15.4)
    ax2.set_yticks([0, 25, 50, 75, 100])
    ax2.set_yticklabels(["0", "25", "50", "75", "100%"])
    ax2.set_xticks(months); ax2.set_xticklabels(list("JFMAMJJASOND"))
    ax2.grid(axis="y", color=HAIRLINE, lw=0.8, zorder=0)
    for spine in ("top", "right", "left"):
        ax2.spines[spine].set_visible(False)
    ax2.spines["bottom"].set_color(AXIS)
    ax2.tick_params(colors=MUTED, length=0, labelsize=10.5)
    ax2.text(0.0, 1.30, "Share of the waterway network navigable, by month",
             transform=ax2.transAxes, fontsize=14, color=INK,
             fontweight="bold")
    ax2.text(0.0, 1.09,
             "Confining river ice to the 24 reviewed freshwater river segments "
             "leaves the Gulf and Inside Passage open all year — matching "
             "year-round twice-weekly\nbarge service — while western and "
             "Arctic Alaska keep a real season driven by the sea-ice "
             "climatology.",
             transform=ax2.transAxes, fontsize=10.4, color=INK_2,
             linespacing=1.5)

    fig.text(0.045, 0.012,
             "Source: outputs/01_friction_build/friction_stack/barge_MM.tif · "
             f"waterway_mask_150m.tif ({n_total:,} cells, 150 m) · "
             "NWN waterways_network_ak_albers.shp",
             fontsize=9, color=MUTED)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=170, bbox_inches="tight", facecolor=SURFACE)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--month", type=int, default=2,
                        help="Month to map (default 2, the worst case).")
    parser.add_argument("--out", default="outputs/analysis/"
                                         "river_ice_marine_leak.png")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    friction_dir = Path(get_friction_output_dir())
    cells = classify_network(friction_dir, args.month)
    logger.info(
        "%s: navigable %d, blocked-real %d, blocked-leak %d",
        MONTH_NAMES[args.month], cells["navigable"].sum(),
        cells["real"].sum(), cells["leak"].sum(),
    )
    monthly = monthly_open_fractions(friction_dir, cells)
    backdrop = water_backdrop(friction_dir)
    path = render(cells, monthly, backdrop, args.month, Path(args.out))
    logger.info("wrote %s", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
