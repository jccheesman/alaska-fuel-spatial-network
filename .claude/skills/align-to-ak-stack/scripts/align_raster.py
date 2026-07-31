#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""align_raster.py

Reproject, resample, and snap a source raster onto the canonical
inputs/AK_Stack_150m/ grid as defined by the LULC reference layer.

Used by the `align-to-ak-stack` skill. Standalone — no project package imports.

Usage:
    python align_raster.py \
        --input <src.tif> \
        --reference inputs/AK_Stack_150m/dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif \
        --resampling {bilinear,nearest} \
        --output inputs/AK_Stack_150m/<layer_name>.tif

Behavior:
  - Reads source CRS, transform, dtype, nodata; reports them before transforming.
  - Reprojects + resamples onto reference grid (CRS, transform, width, height).
  - Source extent larger than reference: clipped (reference window only).
  - Source extent smaller than reference: padded with nodata; warns user.
  - Source missing CRS: aborts (does not assume).
  - NoData defaults: -9999 for float, 255 for uint8 (overridable via --nodata).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

logger = logging.getLogger(__name__)

RESAMPLING_MAP = {
    "nearest": Resampling.nearest,
    "bilinear": Resampling.bilinear,
    "cubic": Resampling.cubic,
    "average": Resampling.average,
    "mode": Resampling.mode,
}


def default_nodata(dtype: np.dtype) -> float | int:
    """Pick a sensible nodata value for the output dtype."""
    if np.issubdtype(dtype, np.floating):
        return -9999.0
    if dtype == np.uint8:
        return 255
    if np.issubdtype(dtype, np.integer):
        info = np.iinfo(dtype)
        return info.max
    raise ValueError(f"No default nodata for dtype {dtype}")


def inspect_source(src_path: Path) -> dict:
    """Read source metadata and return a summary dict. Aborts if no CRS."""
    with rasterio.open(src_path) as src:
        if src.crs is None:
            logger.error(
                "Source %s has no CRS metadata. Refusing to assume — aborting. "
                "Define the CRS explicitly (e.g. gdal_edit.py -a_srs EPSG:XXXX) "
                "and re-run.",
                src_path,
            )
            sys.exit(2)
        return {
            "crs": src.crs,
            "transform": src.transform,
            "width": src.width,
            "height": src.height,
            "bounds": src.bounds,
            "dtype": np.dtype(src.dtypes[0]),
            "nodata": src.nodata,
            "count": src.count,
        }


def check_extent(src_bounds, ref_bounds) -> None:
    """Warn if source extent does not cover reference extent."""
    src_covers = (
        src_bounds.left <= ref_bounds.left
        and src_bounds.bottom <= ref_bounds.bottom
        and src_bounds.right >= ref_bounds.right
        and src_bounds.top >= ref_bounds.top
    )
    if not src_covers:
        logger.warning(
            "Source extent does not fully cover reference extent — pixels "
            "outside source will be filled with nodata. "
            "Source bounds: %s; Reference bounds: %s",
            src_bounds,
            ref_bounds,
        )


def align(
    input_path: Path,
    reference_path: Path,
    output_path: Path,
    resampling: Resampling,
    nodata: float | int | None,
) -> None:
    """Reproject + resample input onto reference grid; write to output."""
    src_meta = inspect_source(input_path)
    logger.info(
        "Source: CRS=%s, shape=(%d, %d), dtype=%s, nodata=%s",
        src_meta["crs"],
        src_meta["height"],
        src_meta["width"],
        src_meta["dtype"],
        src_meta["nodata"],
    )

    with rasterio.open(reference_path) as ref:
        ref_crs = ref.crs
        ref_transform = ref.transform
        ref_width = ref.width
        ref_height = ref.height
        ref_bounds = ref.bounds

    if ref_crs.to_epsg() != 3338:
        logger.warning(
            "Reference CRS is %s, expected EPSG:3338 (Alaska Albers). "
            "Proceeding, but verify this is intentional.",
            ref_crs,
        )

    check_extent(src_meta["bounds"], ref_bounds)

    out_dtype = src_meta["dtype"]
    out_nodata = nodata if nodata is not None else default_nodata(out_dtype)

    with rasterio.open(input_path) as src:
        bands = src.count
        destination = np.full(
            (bands, ref_height, ref_width),
            out_nodata,
            dtype=out_dtype,
        )
        for b in range(1, bands + 1):
            reproject(
                source=rasterio.band(src, b),
                destination=destination[b - 1],
                src_transform=src.transform,
                src_crs=src.crs,
                src_nodata=src.nodata,
                dst_transform=ref_transform,
                dst_crs=ref_crs,
                dst_nodata=out_nodata,
                resampling=resampling,
            )

    profile = {
        "driver": "GTiff",
        "height": ref_height,
        "width": ref_width,
        "count": bands,
        "dtype": out_dtype,
        "crs": ref_crs,
        "transform": ref_transform,
        "nodata": out_nodata,
        "compress": "lzw",
        "tiled": True,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(destination)

    verify(output_path, ref_crs, ref_transform, ref_width, ref_height, out_nodata)
    logger.info("Wrote aligned raster to %s", output_path)


def verify(
    out_path: Path,
    expected_crs,
    expected_transform,
    expected_width: int,
    expected_height: int,
    expected_nodata: float | int,
) -> None:
    """Confirm output matches reference grid exactly. Raises on mismatch."""
    with rasterio.open(out_path) as out:
        if out.crs != expected_crs:
            raise RuntimeError(
                f"Output CRS {out.crs} != expected {expected_crs}"
            )
        if out.width != expected_width or out.height != expected_height:
            raise RuntimeError(
                f"Output shape ({out.height}, {out.width}) != expected "
                f"({expected_height}, {expected_width})"
            )
        if out.transform != expected_transform:
            raise RuntimeError(
                f"Output transform {out.transform} != expected "
                f"{expected_transform} (must match exactly, not approximately)"
            )
        if out.nodata != expected_nodata:
            raise RuntimeError(
                f"Output nodata {out.nodata} != expected {expected_nodata}"
            )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[2])
    p.add_argument("--input", required=True, type=Path, help="Source raster path")
    p.add_argument(
        "--reference",
        required=True,
        type=Path,
        help="Reference raster defining the canonical grid (CRS, transform, shape)",
    )
    p.add_argument("--output", required=True, type=Path, help="Output raster path")
    p.add_argument(
        "--resampling",
        required=True,
        choices=sorted(RESAMPLING_MAP),
        help="Resampling method: nearest for categorical, bilinear for continuous",
    )
    p.add_argument(
        "--nodata",
        type=float,
        default=None,
        help="Override nodata value (default: -9999 for float, 255 for uint8)",
    )
    return p.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    args = parse_args()
    align(
        input_path=args.input,
        reference_path=args.reference,
        output_path=args.output,
        resampling=RESAMPLING_MAP[args.resampling],
        nodata=args.nodata,
    )


if __name__ == "__main__":
    main()
