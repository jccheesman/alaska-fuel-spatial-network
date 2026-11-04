"""Pad an ARCHIVED narrow-grid river-ice run onto the full-Alaska friction grid.

You normally do not need this. `river_ice_full_pipeline.py` (ArcGIS Pro) writes its
twelve rasters straight onto the canonical grid, under the pipeline's own names,
into inputs/friction_rasters/river_ice/. This script exists for the archived
2026-06 narrow-grid run kept in inputs/friction_rasters/small_grid/river_ice/
(the old names river_ice_{MM}.tif), so it can be lifted onto the full grid without
re-running ArcGIS.

Brown et al. river-ice p_ice covers only the interior (non-zero values span roughly
X[-622,500 -> 1,368,300]); the grid extension (western Aleutians/Bering, SE panhandle)
has no rivers that freeze and no Brown et al. data. The archived rasters are already
on the exact 150 m lattice (integer column offset, same Y origin), just narrower — the
old grid is an interior sub-window of the new one. So this is a lossless window insert:
drop each month into its place on the full grid and fill the surrounding extension
with NoData.

Fill = the source NoData sentinel (-9999), matching the existing off-river convention:
`_load_ice` in friction_surface.py maps NoData -> 0.0 ("no ice") at load time. Do NOT fill
with literal 0 — 0 means "river present, ice-free this month", a different thing.

Reads  <src-dir>/river_ice_{MM}.tif  or  <src-dir>/river_ice_probability_{MM}_150m_EPSG3338.tif
Writes inputs/friction_rasters/river_ice/river_ice_probability_{MM}_150m_EPSG3338.tif
(the name friction_paths.river_ice_name gives). The archive is never moved or deleted.

    python -m friction_surface.friction_preprocessing.pad_river_ice_to_grid [--src-dir DIR]
"""
from __future__ import annotations
import argparse
from pathlib import Path

import numpy as np
import rasterio

from ..friction_paths import RASTER_DIR, RASTER_FILES, RIVER_ICE_SUBDIR, river_ice_name

INPUTS = Path(RASTER_DIR)                       # inputs/friction_rasters (env-overridable)
SRC_DEFAULT = INPUTS / "small_grid" / "river_ice"   # the archived narrow-grid run
OUT_DIR = INPUTS / RIVER_ICE_SUBDIR
REF = Path(RASTER_FILES["lulc"])
DEFAULT_NODATA = -9999.0


def _find_source(src_dir: Path, month: int) -> Path | None:
    for name in (f"river_ice_{month:02d}.tif", river_ice_name(month)):
        if (src_dir / name).exists():
            return src_dir / name
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src-dir", type=Path, default=SRC_DEFAULT,
                    help=f"folder holding the archived narrow-grid run (default: {SRC_DEFAULT})")
    args = ap.parse_args(argv)

    if not REF.exists():
        raise FileNotFoundError(f"canonical grid raster missing: {REF} (DATA.md section 3.1)")
    with rasterio.open(REF) as ref:
        ref_w, ref_h = ref.width, ref.height
        ref_transform = ref.transform
        ref_crs = ref.crs

    srcs = [(m, _find_source(args.src_dir, m)) for m in range(1, 13)]
    srcs = [(m, p) for m, p in srcs if p is not None]
    if not srcs:
        print(f"No river-ice rasters found in {args.src_dir} — nothing to do.")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reference grid: {ref_w}x{ref_h}  origin=({ref_transform.c:.0f},{ref_transform.f:.0f})\n")

    for month, src_path in srcs:
        out_path = OUT_DIR / river_ice_name(month)
        with rasterio.open(src_path) as src:
            off_col = round((src.transform.c - ref_transform.c) / ref_transform.a)
            off_row = round((src.transform.f - ref_transform.f) / ref_transform.e)
            assert off_col >= 0 and off_row >= 0, f"{month:02d}: source starts outside grid"
            assert off_col + src.width <= ref_w and off_row + src.height <= ref_h, \
                f"{month:02d}: source exceeds grid"
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
        print(f"[ok] month {month:02d}: offset(col={off_col},row={off_row}) "
              f"{data.shape[1]}x{data.shape[0]} -> {ref_w}x{ref_h}  {rng}  -> {out_path.name}")

    print(f"\nDone. Padded river-ice written to {OUT_DIR.relative_to(INPUTS)}/ "
          f"(archive left untouched in {args.src_dir}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
