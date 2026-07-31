#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_corridor_masks.py

Rasterize a transport-corridor vector network into a 150 m binary mask
aligned with the friction-pipeline grid (rasters/lulc.tif).

Output (uint8, 1 = corridor, 0 = elsewhere):
    outputs/waterway_mask_150m.tif

friction_surface.build_mode_friction reads waterway_mask to widen barge
navigability to rivers narrower than a 150 m LULC pixel.

The road / ice-road corridor masks are no longer produced: overland is a
pure terrain surface, and roads / ice roads are priced by the network layer
(road_base.tif sampling), not burned into the raster. The generic
build_corridor_mask() below can still rasterize either network on demand if
a mask is ever needed again.

Each input shapefile is assumed pre-filtered upstream; this script does
no feature filtering, only rasterization onto the friction grid.

Usage:
    python build_corridor_masks.py            # build the waterway mask
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize

from friction_surface.friction_config import CORRIDOR_BUFFER_M, NETWORK_CRS
from friction_surface.friction_io import load_and_ensure_crs, load_raster_profile
from friction_surface.friction_paths import (
    NETWORK_FILES,
    WATERWAY_MASK_TIF,
    get_raster_path,
)

logger = logging.getLogger(__name__)


CORRIDOR_SPECS: list[tuple[str, str, str]] = [
    ("waterway", NETWORK_FILES["waterways"], WATERWAY_MASK_TIF),
]


def build_corridor_mask(
    shp_path: str | Path,
    output_path: str | Path,
    reference_raster: str | Path | None = None,
    buffer_m: float = CORRIDOR_BUFFER_M,
    name: str = "corridor",
) -> Path:
    """Rasterize a vector corridor network onto the friction grid.

    Args:
        shp_path: Path to the corridor shapefile (LineString / MultiLineString).
        output_path: Output GeoTIFF path.
        reference_raster: Raster whose grid (CRS, transform, height, width)
            defines the output. Defaults to RASTER_FILES["lulc"].
        buffer_m: Buffer applied to LineStrings before rasterization to
            ensure connectivity at the friction grid resolution.
        name: Display name used in log messages.

    Returns:
        Path to the written raster.
    """
    if reference_raster is None:
        reference_raster = get_raster_path("lulc")

    profile = load_raster_profile(reference_raster)
    gdf = load_and_ensure_crs(shp_path, NETWORK_CRS)
    logger.info("[%s] loaded %d features from %s", name, len(gdf), shp_path)

    if gdf.empty:
        raise RuntimeError(f"[{name}] shapefile is empty: {shp_path}")

    if buffer_m > 0:
        gdf["geometry"] = gdf.geometry.buffer(buffer_m)
        logger.info("[%s] buffered LineStrings by %.1f m", name, buffer_m)

    height = profile["height"]
    width = profile["width"]
    transform = profile["transform"]
    target_crs = profile["crs"]

    shapes = [
        (geom, 1) for geom in gdf.geometry
        if geom is not None and not geom.is_empty
    ]
    mask = rasterize(
        shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype=np.uint8,
        all_touched=True,
    )

    coverage = int((mask > 0).sum())
    pct = 100.0 * coverage / mask.size
    logger.info(
        "[%s] rasterized %d feature(s) into %dx%d grid: %d pixels (%.4f%%)",
        name, len(shapes), height, width, coverage, pct,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "uint8",
        "crs": target_crs,
        "transform": transform,
        "nodata": 0,
        "compress": "lzw",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
    }
    with rasterio.open(output_path, "w", **out_profile) as dst:
        dst.write(mask, 1)
    logger.info("[%s] wrote %s", name, output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--only",
        choices=[s[0] for s in CORRIDOR_SPECS],
        default=None,
        help="Build only one corridor mask (default: all three).",
    )
    parser.add_argument(
        "--reference",
        default=None,
        help="Reference raster for grid alignment (default: RASTER_FILES['lulc']).",
    )
    parser.add_argument(
        "--buffer",
        type=float,
        default=CORRIDOR_BUFFER_M,
        help=f"Buffer applied to LineStrings (default {CORRIDOR_BUFFER_M} m, "
             "half a 150 m pixel for grid connectivity).",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    specs = [s for s in CORRIDOR_SPECS if args.only is None or s[0] == args.only]
    for name, shp_path, out_path in specs:
        build_corridor_mask(
            shp_path=shp_path,
            output_path=out_path,
            reference_raster=args.reference,
            buffer_m=args.buffer,
            name=name,
        )


if __name__ == "__main__":
    main()
