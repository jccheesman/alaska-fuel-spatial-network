"""Shared geospatial check primitives.

Small, judgment-free utilities that the QA scripts, diagnostics and skills
share instead of re-implementing: sampling a vector along a raster with the
pipeline's OWN sampler, explaining why a sample is NoData, windowed
nearest-pixel-of-class distances, grid-identity assertion, and endpoint/weld
distances. Everything is EPSG:3338 in, EPSG:3338 out; nothing here reprojects.

The sampler is fuel_network.weights (segmentize-at-75 m MIDPOINTS) — any check
that approximates sample positions instead of calling it disagrees with
workflow 03 at the pixel level (found the hard way, 2026-11-17).
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import rasterio

from fuel_network.weights import build_sample_arrays, edge_weighted_stats, sample_raster

# Dynamic World class names, index = raster value of the land-cover anchor.
DW_CLASS_NAMES = ("water", "trees", "grass", "flooded_veg", "crops",
                  "shrub_scrub", "built", "bare", "snow_ice")


def sample_along(geoms: Iterable, owners: Iterable[int], raster_path: str | Path):
    """Pipeline-identical samples of `geoms` against one raster.

    Returns (xy, seg_len, owner, vals): midpoint coordinates, per-sample
    segment length (the length weight), owning feature id, raster value.
    """
    xy, seg_len, owner = build_sample_arrays(geoms, owners)
    vals = sample_raster(raster_path, xy)
    return xy, seg_len, owner, vals


def per_feature_nodata(owner: np.ndarray, seg_len: np.ndarray, vals: np.ndarray,
                       n_features: int, nodata: float):
    """Length-weighted (mean value, NoData fraction) per feature — exactly the
    statistics workflow 03 writes to edge_month_weights."""
    marked = np.where(vals == nodata, nodata, vals)
    return edge_weighted_stats(owner, seg_len, marked, n_features)


def classify_nodata_cause(xy: np.ndarray) -> list[str]:
    """Why is each sample point NoData on the barge surface?

    The barge surface is valid on (LULC water | waterway corridor) & ~ice, so
    a NoData sample is explained by, in order: off the grid; a land-cover
    class with no corridor burn ("land_cover:<class>"); sea ice over
    threshold; inside the river-ice domain ("river_ice_domain"); else
    "unexplained" (should not happen — investigate).

    Reads the inputs named in friction_paths; callers pass ONLY the points
    they need explained (this opens full rasters).
    """
    from friction_surface.friction_config import SEA_ICE_THRESHOLD
    from friction_surface.friction_paths import (
        RASTER_FILES, WATERWAY_MASK_TIF, WATERWAY_RIVER_MASK_TIF, sea_ice_relpath, get_raster_dir)
    import os

    def _sample(path):
        with rasterio.open(path) as src:
            rows, cols = rasterio.transform.rowcol(src.transform, xy[:, 0], xy[:, 1])
            rows = np.asarray(rows); cols = np.asarray(cols)
            inside = (rows >= 0) & (rows < src.height) & (cols >= 0) & (cols < src.width)
            out = np.full(len(xy), np.nan)
            if inside.any():
                arr = src.read(1)
                out[inside] = arr[rows[inside], cols[inside]]
        return out, inside

    lulc, inside = _sample(RASTER_FILES["lulc"])
    wwm, _ = _sample(WATERWAY_MASK_TIF)
    sea, _ = _sample(os.path.join(get_raster_dir(), sea_ice_relpath(7)))
    rvm, _ = _sample(WATERWAY_RIVER_MASK_TIF)

    causes = []
    for i in range(len(xy)):
        if not inside[i]:
            causes.append("off_grid")
        elif lulc[i] != 0 and wwm[i] != 1:
            name = DW_CLASS_NAMES[int(lulc[i])] if 0 <= lulc[i] < len(DW_CLASS_NAMES) else str(lulc[i])
            causes.append(f"land_cover:{name}")
        elif not np.isnan(sea[i]) and sea[i] > SEA_ICE_THRESHOLD:
            causes.append("sea_ice")
        elif rvm[i] == 1:
            causes.append("river_ice_domain")
        else:
            causes.append("unexplained")
    return causes


def nearest_class_distance(raster_path: str | Path, x: float, y: float,
                           value: int, max_km: float = 300.0):
    """Distance (km) from (x, y) to the nearest pixel equal to `value`,
    by expanding windowed search. Returns (km, (px_x, px_y)) or (nan, None)."""
    with rasterio.open(raster_path) as src:
        px = abs(src.transform.a)
        r, c = rasterio.transform.rowcol(src.transform, x, y)
        halves = [67, 134, 334, 667, 2000]
        halves = [h for h in halves if h * px / 1000 <= max_km * 2] or [int(max_km * 1000 / px)]
        for half in halves:
            r0, c0 = max(0, r - half), max(0, c - half)
            win = rasterio.windows.Window(c0, r0,
                                          min(src.width, c + half + 1) - c0,
                                          min(src.height, r + half + 1) - r0)
            blk = src.read(1, window=win)
            mr, mc = np.nonzero(blk == value)
            if len(mr):
                d = np.hypot(mr + r0 - r, mc + c0 - c) * px
                k = d.argmin()
                if d[k] <= half * px:
                    gx, gy = src.transform * (c0 + mc[k] + 0.5, r0 + mr[k] + 0.5)
                    return float(d[k]) / 1000, (float(gx), float(gy))
    return float("nan"), None


def grid_matches(raster_path: str | Path, anchor_path: str | Path):
    """(True, "") when raster and anchor share CRS, transform and shape;
    else (False, a one-line description of the first difference)."""
    with rasterio.open(raster_path) as a, rasterio.open(anchor_path) as b:
        if a.crs != b.crs:
            return False, f"CRS {a.crs} != {b.crs}"
        if a.transform != b.transform:
            return False, f"transform {tuple(a.transform)[:6]} != {tuple(b.transform)[:6]}"
        if (a.height, a.width) != (b.height, b.width):
            return False, f"shape {(a.height, a.width)} != {(b.height, b.width)}"
    return True, ""


def endpoint_distances(points_xy: Sequence[tuple[float, float]],
                       targets_xy: np.ndarray) -> list[float]:
    """Distance from each point to the nearest target coordinate (meters) —
    the weld / snap check (assembler welds endpoints within its tolerance)."""
    from scipy.spatial import cKDTree
    tree = cKDTree(np.asarray(targets_xy))
    return [float(tree.query(p)[0]) for p in points_xy]
