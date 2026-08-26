#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_corridor_masks.py

Rasterize a transport-corridor vector network into a 150 m binary mask
aligned with the friction-pipeline grid (rasters/lulc.tif).

Outputs (uint8, 1 = corridor, 0 = elsewhere):
    outputs/waterway_mask_150m.tif          every waterway segment
    outputs/waterway_river_mask_150m.tif    freshwater-river segments only

friction_surface.build_mode_friction reads waterway_mask to widen barge
navigability to rivers narrower than a 150 m LULC pixel.

The river mask is the subset of the waterway mask on which river ice is
allowed to gate a barge pixel; everything else on the waterway network is
salt water and is gated by the sea-ice climatology alone. Both masks are
written from the same shapefile in one pass so they cannot drift apart, and
the classification predicates live in friction_config.RIVER_SEGMENT_* rather
than here.

The road / ice-road corridor masks are no longer produced: overland is a
pure terrain surface, and roads / ice roads are priced by the network layer
(road_base.tif sampling), not burned into the raster. The generic
build_corridor_mask() below can still rasterize either network on demand if
a mask is ever needed again.

Apart from the river/marine split, each input shapefile is assumed
pre-filtered upstream; this script does no other feature filtering, only
rasterization onto the friction grid.

Usage:
    python build_corridor_masks.py            # build both waterway masks
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize

from friction_surface.friction_config import (
    CORRIDOR_BUFFER_M,
    NETWORK_CRS,
    RIVER_SEGMENT_KEY_IDS,
    RIVER_SEGMENT_NAME_FIELDS,
    RIVER_SEGMENT_NAME_RE,
    RIVER_SEGMENT_REJECTED,
    RIVER_SEGMENT_STATE,
)
from friction_surface.friction_io import load_and_ensure_crs, load_raster_profile
from friction_surface.friction_paths import (
    NETWORK_FILES,
    WATERWAY_MASK_TIF,
    WATERWAY_RIVER_MASK_TIF,
    get_raster_path,
)

logger = logging.getLogger(__name__)


# NWN attribute columns the river/marine split reads. Named here so a schema
# change fails loudly in select_river_segments instead of silently selecting
# nothing (which would reinstate the marine freeze-out).
RIVER_SEGMENT_COLUMNS = ("KEY_ID", "STATE", "RIVERNAME", "LINKNAME")


def _clean(series):
    """Strip whitespace and the stray quotes some NWN redistributions carry."""
    return series.fillna("").astype(str).str.strip().str.strip("'").str.strip()


def select_river_segments(gdf: "gpd.GeoDataFrame") -> "gpd.GeoDataFrame":
    """Return the freshwater-river subset of an NWN waterway GeoDataFrame.

    Selection is by REVIEWED ALLOWLIST (friction_config.RIVER_SEGMENT_KEY_IDS),
    not by a live attribute predicate — no single NWN column survives contact
    with this table, and the consequences of getting it wrong run both ways
    (river ice on the Gulf; no river ice on the lower Yukon). See the
    RIVER_SEGMENT_* block in friction_config for the counterexamples.

    The name heuristic still runs, as a DRIFT DETECTOR: if the set of
    candidates it proposes stops matching allowlist | rejected, the NWN
    extract has changed and the review needs redoing, so this raises rather
    than guessing.

    Raises KeyError on a missing attribute column, and RuntimeError if the
    allowlist does not resolve or the candidate set has drifted.
    """
    missing = [c for c in RIVER_SEGMENT_COLUMNS if c not in gdf.columns]
    if missing:
        raise KeyError(
            f"waterway shapefile is missing NWN attribute column(s) {missing}; "
            f"the river/marine split needs {list(RIVER_SEGMENT_COLUMNS)}. "
            "Without it river ice would be smeared onto salt water."
        )

    key = _clean(gdf["KEY_ID"])
    is_river = key.isin(RIVER_SEGMENT_KEY_IDS)

    found = set(key[is_river])
    absent = set(RIVER_SEGMENT_KEY_IDS) - found
    if absent:
        raise RuntimeError(
            f"{len(absent)} allowlisted river KEY_ID(s) are not in "
            f"{len(gdf)} waterway features: {sorted(absent)[:5]}. The NWN "
            "extract has changed; re-review RIVER_SEGMENT_KEY_IDS before "
            "building — a shrunken river mask silently un-gates real rivers."
        )

    # Drift check. Nothing selects on this; it only has to agree.
    pattern = re.compile(RIVER_SEGMENT_NAME_RE)
    matches = None
    for field in RIVER_SEGMENT_NAME_FIELDS:
        hit = _clean(gdf[field]).str.upper().str.contains(pattern)
        matches = hit if matches is None else (matches | hit)
    candidates = set(key[(_clean(gdf["STATE"]) == RIVER_SEGMENT_STATE) & matches])
    expected = set(RIVER_SEGMENT_KEY_IDS) | set(RIVER_SEGMENT_REJECTED)
    if candidates != expected:
        raise RuntimeError(
            "river/marine candidate set has drifted from the reviewed one.\n"
            f"  new, unreviewed: {sorted(candidates - expected)}\n"
            f"  reviewed but now absent: {sorted(expected - candidates)}\n"
            "Re-audit RIVER_SEGMENT_KEY_IDS / RIVER_SEGMENT_REJECTED in "
            "friction_config against the new extract, then rebuild."
        )

    rivers = gdf[is_river]
    logger.info(
        "[waterway] river/marine split: %d of %d features are freshwater "
        "rivers (%s); %d candidate(s) rejected on review",
        len(rivers), len(gdf),
        ", ".join(sorted(set(_clean(gdf["LINKNAME"])[is_river].str.upper()))),
        len(RIVER_SEGMENT_REJECTED),
    )
    return rivers


# (name, shapefile, output raster, feature filter). The river mask is built
# from the same shapefile, buffer and reference grid as the full waterway
# mask, so `river_mask == 1` is always a strict subset of `waterway_mask == 1`
# — friction_surface relies on that.
CORRIDOR_SPECS: list[tuple[str, str, str, object]] = [
    ("waterway",       NETWORK_FILES["waterways"], WATERWAY_MASK_TIF,       None),
    ("waterway_river", NETWORK_FILES["waterways"], WATERWAY_RIVER_MASK_TIF,
     select_river_segments),
]


def build_corridor_mask(
    shp_path: str | Path,
    output_path: str | Path,
    reference_raster: str | Path | None = None,
    buffer_m: float = CORRIDOR_BUFFER_M,
    name: str = "corridor",
    feature_filter=None,
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
        feature_filter: Optional callable applied to the loaded GeoDataFrame
            before buffering, returning the subset to rasterize. Used to emit
            the freshwater-river mask from the same shapefile and buffer as
            the full waterway mask, so the two are guaranteed co-registered.

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

    if feature_filter is not None:
        gdf = feature_filter(gdf).copy()

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
        help="Build only one corridor mask (default: every entry in "
             "CORRIDOR_SPECS — the full waterway mask and its freshwater-river "
             "subset).",
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
    for name, shp_path, out_path, feature_filter in specs:
        build_corridor_mask(
            shp_path=shp_path,
            output_path=out_path,
            reference_raster=args.reference,
            buffer_m=args.buffer,
            name=name,
            feature_filter=feature_filter,
        )


if __name__ == "__main__":
    main()
