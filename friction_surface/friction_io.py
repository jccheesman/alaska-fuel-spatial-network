# -*- coding: utf-8 -*-
"""friction_io.py

Shared raster and vector I/O helpers for the friction-layer pipeline.
Eliminates copy-paste CRS-coercion and profile-extraction boilerplate
across the friction-surface builders and corridor/mask scripts.
"""

from __future__ import annotations
import os
from pathlib import Path
import geopandas as gpd
import rasterio


def load_and_ensure_crs(path: str | Path, target_crs: str) -> gpd.GeoDataFrame:
    """Read a vector file and guarantee it's in target_crs.

    If the source CRS is missing, it's assumed to already be in target_crs
    (a deliberate, narrow assumption: project network shapefiles are known
    to be in EPSG:3338 even when the .prj is absent). If the source CRS
    differs, the GeoDataFrame is reprojected.
    """
    path = str(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Vector layer not found at {path}")
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(target_crs)
    elif str(gdf.crs).upper() != target_crs.upper():
        gdf = gdf.to_crs(target_crs)
    return gdf


def load_raster_profile(path: str | Path) -> dict:
    """Return the rasterio profile of a raster without reading its data.

    Used as the reference grid (CRS, transform, height, width, dtype)
    when rasterizing vector inputs onto an aligned target grid.
    """
    path = str(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raster not found at {path}")
    with rasterio.open(path) as src:
        return src.profile.copy()
