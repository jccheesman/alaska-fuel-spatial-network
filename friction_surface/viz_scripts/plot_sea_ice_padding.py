"""Visualize the sea-ice grid padding: raw GEE export vs padded full grid.

The SNAP sea-ice medians come off GEE cropped to the (land-masked) atlas footprint —
short on the EAST of the full-Alaska friction grid. `pad_sea_ice_to_grid.py` appends
zero-columns east (0 = "no ice") to reach the reference width, a lossless insert on the
shared 150 m lattice. This makes a 3-panel figure for one month:

  1. Raw GEE export drawn on the full-grid axes  -> the empty eastern gap is visible.
  2. Padded full grid                            -> the gap is filled with 0.
  3. Schematic of the two regions                -> actual data vs appended zero-pad,
                                                    with the boundary column annotated.

Note: within the GEE footprint, open water and land are legitimately 0 too, so genuine
zeros and the pad are only distinguishable by the boundary column (drawn as a dashed
line), not by value. Reads are decimated for display; the full grid is 28,001 x 16,567.

Usage:  python friction_surface/viz/plot_sea_ice_padding.py [MM]   (default 03 = March)
"""
from __future__ import annotations
import glob
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import rasterio

HERE = Path(__file__).resolve().parent
INPUTS = HERE.parent / "friction_inputs"
SEA_ICE = INPUTS / "sea_ice"
MONTHS = {"01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
          "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"}
TARGET_WIDTH_PX = 1400  # decimated display width


def find_raw(mm: str) -> Path:
    """Raw GEE-named export for month mm, wherever it currently lives."""
    for sub in ("gee_export", "provenance", ""):
        hits = glob.glob(str(SEA_ICE / sub / f"sea_ice_median_{mm}_*.tif"))
        if hits:
            return Path(hits[0])
    raise FileNotFoundError(f"no raw GEE sea-ice export found for month {mm}")


def read_decimated(path: Path, ref_width: int):
    with rasterio.open(path) as ds:
        scale = max(1, round(ds.width / TARGET_WIDTH_PX))
        arr = ds.read(1, out_shape=(ds.height // scale, ds.width // scale)).astype("float64")
        b = ds.bounds
    return arr, (b.left, b.right, b.bottom, b.top)


def km(extent):  # metres -> km for axis labels
    return [v / 1000.0 for v in extent]


def main() -> int:
    mm = (sys.argv[1] if len(sys.argv) > 1 else "03").zfill(2)
    name = MONTHS.get(mm, mm)
    padded_path = SEA_ICE / f"sea_ice_{mm}.tif"
    raw_path = find_raw(mm)
    if not padded_path.exists():
        raise FileNotFoundError(f"padded file not found: {padded_path} (run pad_sea_ice_to_grid.py)")

    with rasterio.open(padded_path) as ds:
        full_w, full_h = ds.width, ds.height
        g_left, g_right = ds.bounds.left, ds.bounds.right
        g_bottom, g_top = ds.bounds.bottom, ds.bounds.top
        px = ds.transform.a

    padded, ext_pad = read_decimated(padded_path, full_w)
    raw, ext_raw = read_decimated(raw_path, full_w)

    # geometry of the pad
    data_right = ext_raw[1]                                  # east edge of real data
    data_cols = round((data_right - g_left) / px)
    pad_cols = full_w - data_cols

    # mask NaN for display (raw has a NaN far-west corner + masked land)
    raw_disp = np.ma.masked_invalid(raw)
    vmax = 100.0
    cmap = plt.cm.get_cmap("Blues").copy()
    cmap.set_bad("0.85")  # NaN in raw -> light grey

    full_ext_km = km([g_left, g_right, g_bottom, g_top])

    fig = plt.figure(figsize=(14, 10), constrained_layout=True)
    axd = fig.subplot_mosaic([["raw", "padded"], ["mask", "mask"]],
                             gridspec_kw={"height_ratios": [1.0, 0.9]})

    # ---- panel 1: raw GEE export on the full-grid axes ----
    ax = axd["raw"]
    im = ax.imshow(raw_disp, extent=km(ext_raw), origin="upper", cmap=cmap,
                   vmin=0, vmax=vmax, interpolation="nearest")
    ax.set_xlim(full_ext_km[0], full_ext_km[1])
    ax.set_ylim(full_ext_km[2], full_ext_km[3])
    ax.set_facecolor("white")
    ax.axvline(data_right / 1000.0, color="crimson", ls="--", lw=1.4)
    ax.annotate("no data east of here\n(atlas footprint ends)",
                xy=(data_right / 1000.0, (g_bottom + 0.72 * (g_top - g_bottom)) / 1000.0),
                xytext=(12, 0), textcoords="offset points", va="center",
                fontsize=9, color="crimson",
                arrowprops=dict(arrowstyle="->", color="crimson"))
    ax.set_title(f"1. Raw GEE export — {name} (cropped to atlas footprint)", fontsize=11)
    ax.set_ylabel("Albers northing (km)")
    fig.colorbar(im, ax=ax, shrink=0.8, label="sea-ice conc. (%)")

    # ---- panel 2: padded full grid ----
    ax = axd["padded"]
    im = ax.imshow(padded, extent=full_ext_km, origin="upper", cmap=cmap,
                   vmin=0, vmax=vmax, interpolation="nearest")
    ax.axvline(data_right / 1000.0, color="crimson", ls="--", lw=1.4)
    ax.add_patch(Rectangle((data_right / 1000.0, g_bottom / 1000.0),
                           (g_right - data_right) / 1000.0, (g_top - g_bottom) / 1000.0,
                           fill=False, edgecolor="crimson", hatch="////", lw=1.2, alpha=0.7))
    ax.set_title(f"2. Padded to full grid — east strip filled with 0", fontsize=11)
    fig.colorbar(im, ax=ax, shrink=0.8, label="sea-ice conc. (%)")

    # ---- panel 3: schematic of the two regions ----
    ax = axd["mask"]
    ax.add_patch(Rectangle((g_left / 1000.0, g_bottom / 1000.0),
                           (data_right - g_left) / 1000.0, (g_top - g_bottom) / 1000.0,
                           facecolor="#3b7dd8", alpha=0.55, edgecolor="none"))
    ax.add_patch(Rectangle((data_right / 1000.0, g_bottom / 1000.0),
                           (g_right - data_right) / 1000.0, (g_top - g_bottom) / 1000.0,
                           facecolor="0.7", alpha=0.55, edgecolor="none", hatch="////"))
    ax.axvline(data_right / 1000.0, color="crimson", ls="--", lw=1.6)
    ax.set_xlim(full_ext_km[0], full_ext_km[1])
    ax.set_ylim(full_ext_km[2], full_ext_km[3])
    ax.set_aspect("equal")
    midy = (g_bottom + 0.5 * (g_top - g_bottom)) / 1000.0
    ax.text((g_left + 0.5 * (data_right - g_left)) / 1000.0, midy,
            f"ACTUAL DATA\n(GEE atlas export)\n{data_cols:,} cols\nX ≤ {data_right:,.0f} m",
            ha="center", va="center", fontsize=10, fontweight="bold", color="white")
    ax.text((data_right + 0.5 * (g_right - data_right)) / 1000.0, midy,
            f"ZERO PAD\n(no ice)\n{pad_cols:,} cols\nappended east",
            ha="center", va="center", fontsize=10, fontweight="bold", color="0.15")
    ax.set_title(f"3. Regions — actual GEE data vs appended zero-pad "
                 f"(full grid {full_w:,} × {full_h:,})", fontsize=11)
    ax.set_xlabel("Albers easting (km)")
    ax.set_ylabel("Albers northing (km)")

    fig.suptitle(f"Sea-ice grid padding — {name}: raw GEE export vs full-grid pad",
                 fontsize=13, fontweight="bold")

    out = HERE / f"sea_ice_padding_vs_data_{mm}_{name}.png"
    fig.savefig(out, dpi=130)
    print(f"actual data: {data_cols:,} cols (X[{g_left:,.0f} → {data_right:,.0f}] m)")
    print(f"zero pad:    {pad_cols:,} cols (X[{data_right:,.0f} → {g_right:,.0f}] m)")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
