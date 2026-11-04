"""Pad the cropped GEE sea-ice medians onto the full-Alaska friction grid, in place.

The Historical Sea Ice Atlas medians come off GEE land-masked, so GEE crops each month
to the atlas footprint (~23,296 x 16,567) instead of the full 28,001 x 16,567 grid. They
already share the target grid's exact origin and 150 m lattice — they're only short
on the EAST — so bringing them to full extent is a lossless window insert (no
resampling): NaN/masked -> 0 inside the existing window, then append zero-columns
east to reach the reference width.

One-name rule (friction_paths): the padded file keeps the GEE name
(sea_ice/sea_ice_median_{MM}_{Mon}_150m_EPSG3338.tif) and the raw, cropped export is
kept beside it in sea_ice/gee_export/ under the same name. Nothing is renamed. A file
already on the reference grid is left alone, so the script is safe to re-run.

Reference grid: the land-cover raster (the canonical anchor) when present, else the
slope raster (both come off GEE on the full grid).

Run from the repo root (any CWD works; paths come from friction_paths):
    python -m friction_surface.friction_preprocessing.pad_sea_ice_to_grid
"""
from __future__ import annotations
import shutil
from pathlib import Path

import numpy as np
import rasterio

from ..friction_paths import (
    RASTER_DIR, RASTER_FILES, SEA_ICE_SUBDIR, sea_ice_name,
)

INPUTS = Path(RASTER_DIR)  # inputs/friction_rasters (env-overridable)
SEA_ICE = INPUTS / SEA_ICE_SUBDIR
GEE_EXPORT = SEA_ICE / "gee_export"


def _reference() -> Path:
    for key in ("lulc", "slope"):
        p = Path(RASTER_FILES[key])
        if p.exists():
            return p
    raise FileNotFoundError(
        f"neither the land-cover nor the slope raster is present in {INPUTS}; "
        "one of them is needed as the full-grid reference (DATA.md section 3.1)."
    )


def _on_grid(path: Path, ref_w: int, ref_h: int, ref_transform) -> bool:
    with rasterio.open(path) as src:
        return (src.width, src.height) == (ref_w, ref_h) and src.transform == ref_transform


def main() -> int:
    ref_path = _reference()
    with rasterio.open(ref_path) as ref:
        ref_w, ref_h = ref.width, ref.height
        ref_transform = ref.transform
        ref_crs = ref.crs
    print(f"Reference grid: {ref_path.name}  {ref_w}x{ref_h}  "
          f"origin=({ref_transform.c:.0f},{ref_transform.f:.0f})\n")

    todo: list[tuple[int, Path]] = []
    for month in range(1, 13):
        name = sea_ice_name(month)
        live = SEA_ICE / name
        raw = GEE_EXPORT / name
        if live.exists() and _on_grid(live, ref_w, ref_h, ref_transform):
            print(f"[ok]   month {month:02d}: already on the full grid — {name}")
            continue
        if live.exists():          # a cropped export sitting in the live spot
            GEE_EXPORT.mkdir(exist_ok=True)
            shutil.move(str(live), str(raw))
        if not raw.exists():
            print(f"[miss] month {month:02d}: no export found for {name}")
            continue
        todo.append((month, raw))

    if not todo:
        print("\nNothing to pad.")
        return 0

    for month, src_path in todo:
        out_path = SEA_ICE / src_path.name
        with rasterio.open(src_path) as src:
            # integer pixel offset of the source within the reference grid
            off_col = round((src.transform.c - ref_transform.c) / ref_transform.a)
            off_row = round((src.transform.f - ref_transform.f) / ref_transform.e)
            assert off_col >= 0 and off_row >= 0, f"{month:02d}: source starts outside grid"
            assert off_col + src.width <= ref_w and off_row + src.height <= ref_h, \
                f"{month:02d}: source exceeds grid"

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
        print(f"[pad]  month {month:02d}: offset(col={off_col},row={off_row}) "
              f"{data.shape[1]}x{data.shape[0]} -> {ref_w}x{ref_h}  "
              f"range[{vmin:.0f},{vmax:.0f}]  -> {out_path.relative_to(INPUTS)}")

    print(f"\nDone. Raw GEE exports kept in {GEE_EXPORT.relative_to(INPUTS)}/ "
          "under the same names.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
