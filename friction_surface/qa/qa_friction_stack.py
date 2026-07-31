#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qa_friction_stack.py

Post-build QA for the friction stack produced by write_friction_stack.
No CLI args — reads from friction_paths defaults. The output_dir is
./friction_surface/friction_outputs/friction_stack by default; override
via FRICTION_DIR env var.

Checks (1-3 are hard failures; 5 is a report line):
  1. The deduped stack is complete: 14 files — overland.tif (one static
     surface sampled for all 12 months), barge_{MM}.tif (MM 01..12), and
     the static road_base.tif — backing 24 logical (mode, month) entries.
     Every raster matches the reference profile (CRS, transform, shape,
     dtype, nodata).
  3. Monthly barge valid-pixel counts: July > January (sanity on the
     ice gating direction).
  4. Overland: no negative friction values other than nodata; min valid
     value >= min(SLOPE_FRICTION). Overland is a pure terrain surface
     (slope x LULC x permafrost) with no road / ice-road burn-in, written
     once as overland.tif.
  5. Ice-road geometry coverage: load ICE_ROADS_SHP, report whether any
     feature intersects a ~50 km box around Bethel (Kuskokwim ice road).
     Report line only — the model intentionally scopes ice roads to the
     supplied network; the gap is informational.

Exit 0 on all-pass; nonzero on any 1-4 failure.

Usage:
    python -m friction_surface.qa.qa_friction_stack
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pyproj
import rasterio
from shapely.geometry import box

from ..friction_config import (
    FRICTION_NODATA,
    SLOPE_FRICTION,
)
from ..friction_paths import (
    ICE_ROADS_SHP,
    get_friction_output_dir,
    get_raster_path,
)


logger = logging.getLogger(__name__)


# Bethel lon/lat (WGS84). Reprojected in-script to EPSG:3338 for the
# Kuskokwim-area ice-road intersection check.
BETHEL_LON = -161.76
BETHEL_LAT = 60.79
BETHEL_BOX_HALF_M = 25_000.0  # ~50 km square


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _friction_dir() -> Path:
    """Resolve the friction output dir from FRICTION_DIR or the package default."""
    return Path(get_friction_output_dir())


def _open_band(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as src:
        return src.read(1), src.profile.copy()


def _valid_count(arr: np.ndarray, nodata: float) -> int:
    return int(np.sum(arr != nodata))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_file_set_and_profile(friction_dir: Path) -> list[str]:
    """Check 1: the deduped stack is complete and matches the reference profile.

    Contract: overland is written once as overland.tif (no seasonal signal),
    barge is per-month (barge_MM.tif), plus the static road_base.tif — 14
    files backing the 24 logical (mode, month) entries.
    """
    errors: list[str] = []
    expected_paths = {friction_dir / f"barge_{mm:02d}.tif" for mm in range(1, 13)}
    expected_paths |= {friction_dir / "overland.tif", friction_dir / "road_base.tif"}
    expected_count = len(expected_paths)  # 14

    missing = sorted(p.name for p in expected_paths if not p.exists())
    if missing:
        errors.append(f"missing {len(missing)} expected files: {missing[:5]}...")
        return errors  # Don't try profile checks if files are missing.

    found = sorted(friction_dir.glob("*.tif"))
    if len(found) != expected_count:
        errors.append(
            f"expected exactly {expected_count} files (overland.tif, road_base.tif, "
            f"barge_01..12.tif); found {len(found)} in {friction_dir} "
            f"(stray files: {sorted(p.name for p in found if p not in expected_paths)})"
        )

    # Reference profile from lulc.tif (canonical grid).
    with rasterio.open(get_raster_path("lulc")) as ref:
        ref_crs = ref.crs
        ref_transform = ref.transform
        ref_shape = (ref.height, ref.width)

    for p in sorted(expected_paths):
        with rasterio.open(p) as src:
            if src.crs != ref_crs:
                errors.append(f"{p.name}: CRS {src.crs} != reference {ref_crs}")
            if src.transform != ref_transform:
                errors.append(f"{p.name}: transform != reference")
            if (src.height, src.width) != ref_shape:
                errors.append(
                    f"{p.name}: shape {(src.height, src.width)} != reference {ref_shape}"
                )
            if src.dtypes[0] != "float32":
                errors.append(f"{p.name}: dtype {src.dtypes[0]} != float32")
            if src.nodata != FRICTION_NODATA:
                errors.append(f"{p.name}: nodata {src.nodata} != {FRICTION_NODATA}")
    return errors


def check_barge_ice_gating(friction_dir: Path) -> list[str]:
    """Check 3: barge July valid-pixel count > January."""
    errors: list[str] = []
    jan, _ = _open_band(friction_dir / "barge_01.tif")
    jul, _ = _open_band(friction_dir / "barge_07.tif")
    jan_valid = _valid_count(jan, FRICTION_NODATA)
    jul_valid = _valid_count(jul, FRICTION_NODATA)
    if not jul_valid > jan_valid:
        errors.append(
            f"barge July valid pixels ({jul_valid:,}) not > January ({jan_valid:,}); "
            "ice gating direction looks inverted"
        )
    else:
        logger.info(
            "barge ice gating OK: Jan valid=%d, Jul valid=%d (Jul - Jan = %d)",
            jan_valid, jul_valid, jul_valid - jan_valid,
        )
    return errors


def check_overland_value_range(friction_dir: Path) -> list[str]:
    """Check 4: overland values are sane; min valid >= floor.

    Overland is now a pure terrain surface (slope x LULC x permafrost) with
    no road / ice-road burn-in, so the floor is simply min(SLOPE_FRICTION):
    permafrost multipliers are >= 1.0 and LULC classes are >= 1.0, so the
    product can't dip below the flat-slope value.
    """
    errors: list[str] = []
    floor = min(SLOPE_FRICTION)

    # One static overland.tif, sampled for all 12 months.
    arr, _ = _open_band(friction_dir / "overland.tif")
    valid = arr[arr != FRICTION_NODATA]
    if valid.size == 0:
        return ["overland: all NoData"]
    # No negatives other than nodata.
    neg = valid[valid < 0]
    if neg.size:
        errors.append(
            f"overland: {neg.size:,} negative friction values (not nodata)"
        )
    # Min valid >= floor (with tiny float slack).
    vmin = float(valid.min())
    if vmin < floor - 1e-6:
        errors.append(f"overland: min valid {vmin:.4f} < floor {floor:.4f}")
    return errors


def report_bethel_ice_road_coverage() -> str:
    """Check 5: report-only. Does the ice-road network reach Bethel?"""
    if not Path(ICE_ROADS_SHP).exists():
        return f"Bethel coverage: ICE_ROADS_SHP not found at {ICE_ROADS_SHP}"

    transformer = pyproj.Transformer.from_crs(
        "EPSG:4326", "EPSG:3338", always_xy=True
    )
    bx, by = transformer.transform(BETHEL_LON, BETHEL_LAT)

    bethel_box = box(
        bx - BETHEL_BOX_HALF_M, by - BETHEL_BOX_HALF_M,
        bx + BETHEL_BOX_HALF_M, by + BETHEL_BOX_HALF_M,
    )
    gdf = gpd.read_file(ICE_ROADS_SHP)
    if gdf.crs is None or str(gdf.crs) != "EPSG:3338":
        gdf = gdf.to_crs("EPSG:3338")
    hits = gdf[gdf.intersects(bethel_box)]
    return (
        f"Bethel coverage: {len(hits)} ice-road feature(s) intersect a "
        f"{int(2*BETHEL_BOX_HALF_M/1000)} km box around Bethel "
        f"(EPSG:3338 center: {bx:.0f}, {by:.0f}). "
        f"{'Network reaches Bethel.' if len(hits) else 'No coverage — Kuskokwim ice road not represented in the network.'}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    friction_dir = _friction_dir()
    logger.info("QA target: %s", friction_dir)

    if not friction_dir.is_dir():
        logger.error("friction directory does not exist: %s", friction_dir)
        return 2

    all_errors: list[str] = []
    for name, fn in [
        ("file-set / profile",       lambda: check_file_set_and_profile(friction_dir)),
        ("barge ice gating",         lambda: check_barge_ice_gating(friction_dir)),
        ("overland values",          lambda: check_overland_value_range(friction_dir)),
    ]:
        errors = fn()
        if errors:
            logger.error("[FAIL] %s — %d issue(s)", name, len(errors))
            for e in errors:
                logger.error("       %s", e)
            all_errors.extend(errors)
        else:
            logger.info("[OK]   %s", name)

    # Check 5 is informational, not a failure.
    logger.info("[INFO] %s", report_bethel_ice_road_coverage())

    if all_errors:
        logger.error("QA FAILED: %d issue(s) total", len(all_errors))
        return 1
    logger.info("QA PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
