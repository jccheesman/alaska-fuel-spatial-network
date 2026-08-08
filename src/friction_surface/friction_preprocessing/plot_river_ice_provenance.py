"""Plot per-pixel river-ice fill-stage provenance from the ArcGIS pipeline.

Reads the provenance_MM.tif rasters written by river_ice_full_pipeline.py
and renders a 3-panel matplotlib figure (Jan / Apr / Oct) matching the
schema of outputs/idw_validation/figures/path_b_provenance.png:
    1 = polygon-median (green)
    2 = IDW            (blue)
    3 = NN-fallback    (orange)

Designed to run inside Pro's arcgispro-py3 environment alongside the
pipeline. Uses arcpy (raster I/O + AK boundary), numpy, matplotlib, and
scipy.ndimage (display dilation). No geopandas required.

Run with Pro's Python:
    "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\scripts\\propy.bat" plot_river_ice_provenance.py
or, after `conda activate arcgispro-py3`:
    python plot_river_ice_provenance.py

Edit the Configuration block before running.
"""

import os
import arcpy
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.patches import Patch, Polygon as MplPolygon
from matplotlib.collections import PatchCollection
from scipy.ndimage import distance_transform_edt


# ---------------------------------------------------------------------------
# Configuration — edit paths to match your ArcGIS box layout
# ---------------------------------------------------------------------------
# Windows / ArcGIS Pro only (needs arcpy). Override the project root without
# editing this file via the FRICTION_LAYER_ROOT env var; the literal below is
# the fallback for the original authoring box.
PROJECT_ROOT = os.getenv("FRICTION_LAYER_ROOT", r"E:\DOE\Friction_layer\FRICTION_LAYER")

# Where river_ice_full_pipeline.py writes provenance_MM.tif and river_ice_MM.tif
OUT_DIR = os.path.join(PROJECT_ROOT, "AK_Stack_150m")

# TIGER cb_2023_us_state_500k shapefile (download once from
# https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_500k.zip
# and unzip somewhere local). Set to None to skip the AK boundary.
TIGER_SHP = os.path.join(PROJECT_ROOT, "tiger", "cb_2023_us_state_500k.shp")

# Where to save the figure
FIG_OUT = os.path.join(PROJECT_ROOT, "AK_Stack_150m",
                       "provenance_jan_apr_oct.png")

EPSG = 3338
MONTHS = [1, 4, 10]
MONTH_NAMES = {1: "January", 4: "April", 10: "October"}

# Colour scheme — matches path_b_provenance.png exactly so the two figures
# read as members of the same family.
#   index 0 = transparent (outside river mask)
#   index 1 = green       (polygon-median)
#   index 2 = blue        (IDW)
#   index 3 = orange      (NN-fallback)
CMAP_PROV = ListedColormap(["#ffffff00", "#9bd0a5", "#4b94c7", "#e07b3a"])

PROV_LABELS = {1: "polygon-median fill",
               2: "IDW interpolation",
               3: "NN-fallback (EucAllocation)"}

# River cells are 150 m, so they are sub-pixel on a statewide figure.
# Dilating display-only by N pixels makes the network visible without
# altering the underlying raster.
DISPLAY_DILATION_PX = 6


# ---------------------------------------------------------------------------
# Raster I/O via arcpy
# ---------------------------------------------------------------------------
def load_provenance_raster(month):
    """Read a provenance raster as a float numpy array (NaN outside mask)
    plus its (left, right, bottom, top) extent."""
    path = os.path.join(OUT_DIR, "provenance_{:02d}.tif".format(month))
    if not arcpy.Exists(path):
        raise FileNotFoundError(path)

    desc = arcpy.Describe(path)
    ras = arcpy.Raster(path)
    nodata = ras.noDataValue

    arr = arcpy.RasterToNumPyArray(path, nodata_to_value=0).astype("float32")
    # In the provenance raster, NoData was stored as 0 by CopyRaster
    # (see pipeline). Treat both nodata sentinel and 0 as outside-mask.
    if nodata is not None and nodata != 0:
        arr[arr == float(nodata)] = 0.0
    arr[arr == 0] = np.nan

    ext = desc.extent
    extent = (ext.XMin, ext.XMax, ext.YMin, ext.YMax)
    return arr, extent


# ---------------------------------------------------------------------------
# AK boundary via arcpy (no geopandas)
# ---------------------------------------------------------------------------
_AK_PATCHES_CACHE = None


def load_ak_boundary_patches():
    """Return a list of matplotlib.patches.Polygon for Alaska in EPSG:3338.

    Reads the TIGER shapefile via arcpy.da.SearchCursor. Projects to
    EPSG:3338 in scratch GDB, then walks each polygon part / vertex.
    Cached so repeat calls are free.
    """
    global _AK_PATCHES_CACHE
    if _AK_PATCHES_CACHE is not None:
        return _AK_PATCHES_CACHE
    if TIGER_SHP is None or not arcpy.Exists(TIGER_SHP):
        print("AK boundary skipped (TIGER_SHP not set or missing).")
        _AK_PATCHES_CACHE = []
        return _AK_PATCHES_CACHE

    scratch = arcpy.env.scratchGDB
    ak_in = os.path.join(scratch, "ak_state_in")
    ak_proj = os.path.join(scratch, "ak_state_3338")
    for fc in (ak_in, ak_proj):
        if arcpy.Exists(fc):
            arcpy.management.Delete(fc)

    # Subset to Alaska before projecting
    arcpy.analysis.Select(TIGER_SHP, ak_in, "\"STUSPS\" = 'AK'")
    arcpy.management.Project(ak_in, ak_proj, arcpy.SpatialReference(EPSG))

    patches = []
    with arcpy.da.SearchCursor(ak_proj, ["SHAPE@"]) as cursor:
        for (shape,) in cursor:
            for part in shape:
                pts = [(p.X, p.Y) for p in part if p is not None]
                if len(pts) >= 3:
                    patches.append(MplPolygon(pts, closed=True))

    print("AK boundary: {} polygon parts".format(len(patches)))
    _AK_PATCHES_CACHE = patches
    return patches


# ---------------------------------------------------------------------------
# Display dilation — copy of path_b_python_pipeline.dilate_for_display
# ---------------------------------------------------------------------------
def dilate_for_display(arr, n_px):
    """Thicken visible cells by n_px in every direction without altering
    existing values. Each empty cell within n_px of a valid cell inherits
    the value of its nearest valid cell."""
    valid = np.isfinite(arr)
    if not valid.any() or n_px <= 0:
        return arr
    dist, idx = distance_transform_edt(~valid, return_distances=True,
                                       return_indices=True)
    out = arr[tuple(idx)]
    out[dist > n_px] = np.nan
    return out


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
def style_axes(ax, ak_patches):
    if ak_patches:
        coll = PatchCollection(ak_patches, facecolor="#f7f7f7",
                               edgecolor="#7a8794", linewidth=0.6, zorder=0)
        ax.add_collection(coll)
    ax.set_axisbelow(True)
    ax.grid(True, color="#dcdfe2", linewidth=0.5, alpha=0.9, zorder=1)
    ax.set_aspect("equal")


def plot_provenance_figure(out_path):
    ak_patches = load_ak_boundary_patches()

    fig, axes = plt.subplots(1, len(MONTHS),
                             figsize=(5.5 * len(MONTHS), 8.5),
                             sharex=True, sharey=True)
    if len(MONTHS) == 1:
        axes = [axes]

    prov_norm = Normalize(0, 3)
    xlims, ylims = [], []

    for ax, month in zip(axes, MONTHS):
        arr, extent = load_provenance_raster(month)
        # Pixel counts measured BEFORE display dilation
        n_med = int(np.nansum(arr == 1))
        n_idw = int(np.nansum(arr == 2))
        n_nn = int(np.nansum(arr == 3))

        arr_disp = dilate_for_display(arr, DISPLAY_DILATION_PX)

        style_axes(ax, ak_patches)
        ax.imshow(arr_disp, extent=extent, origin="upper", cmap=CMAP_PROV,
                  norm=prov_norm, interpolation="nearest", zorder=2)

        # Compute zoom to mask extent
        rows, cols = np.where(np.isfinite(arr))
        if rows.size:
            xres = (extent[1] - extent[0]) / arr.shape[1]
            yres = (extent[3] - extent[2]) / arr.shape[0]
            xlims.append((extent[0] + cols.min() * xres,
                          extent[0] + (cols.max() + 1) * xres))
            ylims.append((extent[3] - (rows.max() + 1) * yres,
                          extent[3] - rows.min() * yres))

        ax.set_title(
            "{}\nmedian {:,}  -  IDW {:,}  -  NN {:,}".format(
                MONTH_NAMES[month], n_med, n_idw, n_nn),
            fontsize=11,
        )
        ax.set_xlabel("Easting (m, EPSG:{})".format(EPSG))
        if ax is axes[0]:
            ax.set_ylabel("Northing (m, EPSG:{})".format(EPSG))

    if xlims:
        xmin = min(x[0] for x in xlims); xmax = max(x[1] for x in xlims)
        ymin = min(y[0] for y in ylims); ymax = max(y[1] for y in ylims)
        pad_x = (xmax - xmin) * 0.04
        pad_y = (ymax - ymin) * 0.04
        for ax in axes:
            ax.set_xlim(xmin - pad_x, xmax + pad_x)
            ax.set_ylim(ymin - pad_y, ymax + pad_y)

    legend = [
        Patch(facecolor=CMAP_PROV(1 / 3), label=PROV_LABELS[1]),
        Patch(facecolor=CMAP_PROV(2 / 3), label=PROV_LABELS[2]),
        Patch(facecolor=CMAP_PROV(3 / 3), label=PROV_LABELS[3]),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=3, fontsize=10,
               frameon=True, bbox_to_anchor=(0.5, 0.03))

    fig.suptitle(
        "ArcGIS river-ice pipeline -- per-pixel fill provenance\n"
        "Pixel counts measured before display dilation "
        "({}px ~ {:.1f} km).".format(
            DISPLAY_DILATION_PX, DISPLAY_DILATION_PX * 150 / 1000.0),
        fontsize=12, y=0.99,
    )
    fig.subplots_adjust(left=0.05, right=0.98, top=0.92,
                        bottom=0.13, wspace=0.06)

    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print("Wrote {}".format(out_path))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not os.path.isdir(os.path.dirname(FIG_OUT)):
        os.makedirs(os.path.dirname(FIG_OUT))

    # Sanity: verify all needed provenance rasters exist before plotting
    missing = [m for m in MONTHS
               if not arcpy.Exists(
                   os.path.join(OUT_DIR, "provenance_{:02d}.tif".format(m)))]
    if missing:
        raise SystemExit(
            "Missing provenance_MM.tif for months: {}. "
            "Run river_ice_full_pipeline.py first.".format(missing))

    plot_provenance_figure(FIG_OUT)


if __name__ == "__main__":
    main()
