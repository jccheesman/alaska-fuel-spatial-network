"""Pad the cropped GEE sea-ice medians onto the full-Alaska friction grid.

The SNAP sea-ice medians come off GEE land-masked, so GEE crops each month to the
atlas footprint (~23,296 x 16,567) instead of the full 28,001 x 16,567 grid. They
already share the target grid's exact origin and 150 m lattice — they're only short
on the EAST — so bringing them to full extent is a lossless window insert (no
resampling): NaN/masked -> 0 inside the existing window, then append zero-columns
east to reach the reference width.

Reference grid is taken from FABDEM_slope_150m_EPSG3338.tif (already the confirmed
full grid), so this does NOT wait on lulc.tif.

Writes the padded, full-grid friction_inputs/sea_ice/sea_ice_{01..12}.tif (the files
the pipeline consumes) and moves the raw GEE-named sources into
friction_inputs/sea_ice/gee_export/ (ignored by check_grid_exports.py).
"""
from __future__ import annotations
import glob
import os
import re
import shutil
from pathlib import Path

import numpy as np
import rasterio

HERE = Path(__file__).resolve().parent
INPUTS = HERE.parent / "friction_inputs"
SEA_ICE = INPUTS / "sea_ice"
GEE_EXPORT = SEA_ICE / "gee_export"
REF = INPUTS / "FABDEM_slope_150m_EPSG3338.tif"

MONTH_RE = re.compile(r"sea_ice_median_(\d{2})_")


def main() -> int:
    with rasterio.open(REF) as ref:
        ref_w, ref_h = ref.width, ref.height
        ref_transform = ref.transform
        ref_crs = ref.crs

    raws = sorted(glob.glob(str(SEA_ICE / "sea_ice_median_*.tif")))
    if not raws:
        print("No raw sea_ice_median_*.tif found — nothing to do.")
        return 1
    GEE_EXPORT.mkdir(exist_ok=True)

    print(f"Reference grid: {ref_w}x{ref_h}  origin=({ref_transform.c:.0f},{ref_transform.f:.0f})\n")

    for src_path in raws:
        m = MONTH_RE.search(os.path.basename(src_path))
        if not m:
            print(f"[skip] cannot parse month from {src_path}")
            continue
        mm = m.group(1)
        out_path = SEA_ICE / f"sea_ice_{mm}.tif"

        with rasterio.open(src_path) as src:
            # integer pixel offset of the source within the reference grid
            off_col = round((src.transform.c - ref_transform.c) / ref_transform.a)
            off_row = round((src.transform.f - ref_transform.f) / ref_transform.e)
            assert off_col >= 0 and off_row >= 0, f"{mm}: source starts outside grid"
            assert off_col + src.width <= ref_w and off_row + src.height <= ref_h, \
                f"{mm}: source exceeds grid"

            data = src.read(1).astype("float32")
            data = np.nan_to_num(data, nan=0.0)          # masked/NaN -> "no ice"
            if src.nodata is not None:
                data[data == np.float32(src.nodata)] = 0.0

        full = np.zeros((ref_h, ref_w), dtype="float32")  # east pad = 0 = no ice
        full[off_row:off_row + data.shape[0], off_col:off_col + data.shape[1]] = data

        profile = {
            "driver": "GTiff", "dtype": "float32", "count": 1,
            "width": ref_w, "height": ref_h,
            "crs": ref_crs, "transform": ref_transform,
            "nodata": None, "compress": "deflate", "predictor": 2,
            "tiled": True, "blockxsize": 256, "blockysize": 256,
        }
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(full, 1)

        vmin, vmax = float(full.min()), float(full.max())
        print(f"[ok] month {mm}: offset(col={off_col},row={off_row}) "
              f"{data.shape[1]}x{data.shape[0]} -> {ref_w}x{ref_h}  "
              f"range[{vmin:.0f},{vmax:.0f}]  -> {out_path.name}")

        shutil.move(src_path, GEE_EXPORT / os.path.basename(src_path))

    print(f"\nDone. Raw GEE exports moved to {GEE_EXPORT.relative_to(INPUTS)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
