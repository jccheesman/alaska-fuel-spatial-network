"""Pad the old-grid river-ice rasters onto the full-Alaska friction grid.

Brown et al. river-ice p_ice covers only the interior (non-zero values span roughly
X[-622,500 -> 1,368,300]); the grid extension (western Aleutians/Bering, SE panhandle)
has no rivers that freeze and no Brown et al. data. The existing small_grid/river_ice
rasters are already on the exact new-grid 150 m lattice (integer column offset, same Y
origin), just narrower — the old grid is an interior sub-window of the new one. So this
is a lossless window insert, NOT an ArcGIS re-run: drop each month into its place on the
full grid and fill the surrounding extension with NoData.

Fill = the source NoData sentinel (-9999), matching the existing off-river convention:
`_load_ice` in friction_surface.py maps NoData -> 0.0 ("no ice") at load time. Do NOT fill
with literal 0 — 0 means "river present, ice-free this month", a different thing.

Reference grid is taken from lulc.tif (the canonical reference). Writes
inputs/friction_rasters/river_ice/river_ice_{01..12}.tif. The old rasters stay in small_grid/
as the archive (nothing is moved or deleted).
"""
from __future__ import annotations
import glob
import os
import re
from pathlib import Path

import numpy as np
import rasterio

from ..friction_paths import RASTER_DIR

INPUTS = Path(RASTER_DIR)                       # inputs/friction_rasters (env-overridable)
SRC_DIR = INPUTS / "small_grid" / "river_ice"   # interior-grid archive
OUT_DIR = INPUTS / "river_ice"
REF = INPUTS / "lulc.tif"

MONTH_RE = re.compile(r"river_ice_(\d{2})\.tif$")
DEFAULT_NODATA = -9999.0


def main() -> int:
    with rasterio.open(REF) as ref:
        ref_w, ref_h = ref.width, ref.height
        ref_transform = ref.transform
        ref_crs = ref.crs

    srcs = sorted(glob.glob(str(SRC_DIR / "river_ice_*.tif")))
    srcs = [s for s in srcs if MONTH_RE.search(os.path.basename(s))]
    if not srcs:
        print(f"No river_ice_MM.tif found in {SRC_DIR} — nothing to do.")
        return 1
    OUT_DIR.mkdir(exist_ok=True)

    print(f"Reference grid: {ref_w}x{ref_h}  origin=({ref_transform.c:.0f},{ref_transform.f:.0f})\n")

    for src_path in srcs:
        mm = MONTH_RE.search(os.path.basename(src_path)).group(1)
        out_path = OUT_DIR / f"river_ice_{mm}.tif"

        with rasterio.open(src_path) as src:
            off_col = round((src.transform.c - ref_transform.c) / ref_transform.a)
            off_row = round((src.transform.f - ref_transform.f) / ref_transform.e)
            assert off_col >= 0 and off_row >= 0, f"{mm}: source starts outside grid"
            assert off_col + src.width <= ref_w and off_row + src.height <= ref_h, \
                f"{mm}: source exceeds grid"
            nodata = src.nodata if src.nodata is not None else DEFAULT_NODATA
            data = src.read(1).astype("float32")

        data = np.where(np.isnan(data), np.float32(nodata), data)   # NaN -> NoData
        full = np.full((ref_h, ref_w), np.float32(nodata), dtype="float32")  # extension = NoData
        full[off_row:off_row + data.shape[0], off_col:off_col + data.shape[1]] = data

        profile = {
            "driver": "GTiff", "dtype": "float32", "count": 1,
            "width": ref_w, "height": ref_h,
            "crs": ref_crs, "transform": ref_transform,
            "nodata": nodata, "compress": "deflate", "predictor": 2,
            "tiled": True, "blockxsize": 256, "blockysize": 256,
        }
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(full, 1)

        ice = full[(full != nodata) & (full > 0)]
        rng = f"p_ice[{ice.min():.3f},{ice.max():.3f}] n={ice.size:,}" if ice.size else "no ice>0"
        print(f"[ok] month {mm}: offset(col={off_col},row={off_row}) "
              f"{data.shape[1]}x{data.shape[0]} -> {ref_w}x{ref_h}  {rng}  -> {out_path.name}")

    print(f"\nDone. Padded river-ice written to {OUT_DIR.relative_to(INPUTS)}/ "
          f"(originals kept in {SRC_DIR.relative_to(INPUTS)}/).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
