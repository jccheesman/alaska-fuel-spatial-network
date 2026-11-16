#!/usr/bin/env python3
"""Render two friction-surface figures from the friction stack.

1. overland.tif  -> single map with colorbar, scale bar, north arrow.
2. barge_01..12  -> 4x3 grid of monthly barge passability, classified
   three ways: passable water (dark slate blue), water-but-frozen / ice
   (pale blue), and land (grey).

Reads decimated (overview) windows so the whole-Alaska rasters stay cheap.
All layers share lulc.tif's 28,001 x 16,567 EPSG:3338 grid.
"""
import numpy as np
import rasterio
from rasterio.enums import Resampling
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Rectangle

import repo_paths as rp

STACK = rp.FRICTION_STACK
OUT = rp.NETWORK_PLOTS
OUT.mkdir(parents=True, exist_ok=True)

# Decimation: target width in pixels for the read (full grid is 28,001 wide).
TARGET_W = 2400


def read_decimated(path, target_w=TARGET_W):
    """Read a raster decimated to ~target_w wide, returning (array, extent, nodata)."""
    with rasterio.open(path) as ds:
        fac = max(1, round(ds.width / target_w))
        oh, ow = ds.height // fac, ds.width // fac
        arr = ds.read(1, out_shape=(oh, ow), resampling=Resampling.average)
        b = ds.bounds
        extent = [b.left, b.right, b.bottom, b.top]
        return arr, extent, ds.nodata


def read_mask_decimated(path, target_w=TARGET_W):
    """Read a layer decimated with nearest resampling (for categorical/nodata use)."""
    with rasterio.open(path) as ds:
        fac = max(1, round(ds.width / target_w))
        oh, ow = ds.height // fac, ds.width // fac
        arr = ds.read(1, out_shape=(oh, ow), resampling=Resampling.nearest)
        b = ds.bounds
        extent = [b.left, b.right, b.bottom, b.top]
        return arr, extent, ds.nodata


def add_north_arrow(ax, x=0.93, y=0.92):
    """Simple north arrow in axes fraction coords."""
    ax.annotate(
        "N",
        xy=(x, y), xytext=(x, y - 0.08),
        xycoords="axes fraction",
        ha="center", va="center",
        fontsize=14, fontweight="bold",
        arrowprops=dict(arrowstyle="-|>", color="black", lw=2.2),
    )


def add_scalebar(ax, extent, length_m=500_000, label="500 km",
                 loc_x=0.06, loc_y=0.06):
    """Draw a simple filled scale bar in data coordinates."""
    xmin, xmax, ymin, ymax = extent
    span_x = xmax - xmin
    span_y = ymax - ymin
    x0 = xmin + loc_x * span_x
    y0 = ymin + loc_y * span_y
    h = 0.012 * span_y
    ax.add_patch(Rectangle((x0, y0), length_m, h, facecolor="black",
                           edgecolor="black", zorder=10))
    ax.text(x0 + length_m / 2, y0 + h * 2.2, label,
            ha="center", va="bottom", fontsize=10, zorder=10)


# ---------------------------------------------------------------------------
# Figure 1: overland friction surface
# ---------------------------------------------------------------------------
def fig_overland():
    arr, extent, nodata = read_decimated(STACK / "overland.tif")
    masked = np.ma.masked_equal(arr, nodata) if nodata is not None else np.ma.masked_invalid(arr)

    vmin = float(masked.min())
    vmax = float(masked.max())

    cmap = plt.get_cmap("YlOrRd").copy()
    cmap.set_bad("#e8e8e8")  # NoData (off-land / water) -> light grey

    fig, ax = plt.subplots(figsize=(13, 8))
    im = ax.imshow(masked, extent=extent, origin="upper", cmap=cmap,
                   vmin=vmin, vmax=vmax, interpolation="nearest")
    ax.set_facecolor("#e8e8e8")
    ax.set_title("Overland friction surface — Alaska", fontsize=15, pad=12)
    ax.set_xlabel("Easting (m, EPSG:3338)")
    ax.set_ylabel("Northing (m, EPSG:3338)")
    ax.ticklabel_format(style="plain")

    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Friction multiplier (dimensionless)", fontsize=11)

    add_scalebar(ax, extent)
    add_north_arrow(ax)

    fig.tight_layout()
    out = OUT / "overland_friction_surface.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}  (friction range {vmin:.3g}..{vmax:.3g})")


# ---------------------------------------------------------------------------
# Figure 2: 4x3 grid of monthly barge passability
# ---------------------------------------------------------------------------
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fig_barge_grid():
    # Read all 12 months decimated; passable = not-nodata.
    passable = []
    extent = None
    for m in range(1, 13):
        arr, ext, nodata = read_mask_decimated(STACK / f"barge_{m:02d}.tif")
        extent = ext
        p = arr != nodata if nodata is not None else ~np.isnan(arr)
        passable.append(p)
    passable = np.stack(passable)  # (12, H, W)

    # Water extent = passable in ANY month (summer-open marine + rivers).
    water_extent = passable.any(axis=0)

    # Classify per month: 0 land, 1 ice (water but frozen now), 2 passable now.
    # Colors: land grey, ice pale blue, passable dark slate blue.
    cmap = ListedColormap(["#bdbdbd", "#dCEBF5", "#2c3e6b".upper()])
    # fix hex (ListedColormap wants valid hex)
    cmap = ListedColormap(["#bdbdbd", "#d6e9f7", "#2c3e6b"])
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5], cmap.N)

    fig, axes = plt.subplots(3, 4, figsize=(16, 11))
    for i, ax in enumerate(axes.flat):
        p = passable[i]
        cls = np.zeros(p.shape, dtype=np.uint8)
        cls[water_extent & ~p] = 1  # ice / impassable water
        cls[p] = 2                   # passable water
        ax.imshow(cls, extent=extent, origin="upper", cmap=cmap, norm=norm,
                  interpolation="nearest")
        ax.set_title(MONTHS[i], fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])

    # One scale bar + north arrow on the first panel.
    add_scalebar(axes.flat[0], extent, loc_x=0.05, loc_y=0.05)
    add_north_arrow(axes.flat[3])

    # Shared legend.
    from matplotlib.patches import Patch
    legend = [
        Patch(facecolor="#2c3e6b", label="Passable water (barge)"),
        Patch(facecolor="#d6e9f7", edgecolor="#9ab", label="Ice / impassable"),
        Patch(facecolor="#bdbdbd", label="Land"),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=3, frameon=False,
               fontsize=12, bbox_to_anchor=(0.5, 0.005))

    fig.suptitle("Barge friction surface — monthly passability",
                 fontsize=16, y=0.98)
    fig.tight_layout(rect=[0, 0.04, 1, 0.96])
    out = OUT / "barge_friction_monthly_grid.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    pct = 100 * water_extent.mean()
    print(f"wrote {out}  (water-extent covers {pct:.2f}% of decimated grid)")


if __name__ == "__main__":
    fig_overland()
    fig_barge_grid()
