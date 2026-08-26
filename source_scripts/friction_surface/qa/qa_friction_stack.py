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
  2. Year-round ports: every ICE_FREE_PORTS location is navigable on the
     barge surface in ALL 12 months, and every SEASONAL_PORTS location is
     navigable in summer but NOT in February. The first half catches river
     ice leaking onto salt water (which closed the whole marine network
     Nov-Apr before the river/marine split); the second half stops anyone
     "fixing" that by disabling ice gating altogether.
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
    WATERWAY_MASK_TIF,
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
# Seasonality tripwires
# ---------------------------------------------------------------------------
# Ports on the Gulf of Alaska / Inside Passage that carry year-round
# commercial barge service. Alaska Marine Lines sails Southeast twice weekly,
# every week of the year (Juneau, Ketchikan, Petersburg, Sitka, Haines,
# Skagway, Wrangell); Southcentral (Seward, Kodiak, Valdez, Whittier, Homer,
# Cordova) is ice-free year-round. If the barge surface closes any of these
# in any month, the model is wrong, and the historical way it goes wrong is
# river ice reaching salt water through the unbounded nearest-fill in
# friction_surface.extend_ice_nearest — which in Feb 2026 blocked 501,684 of
# 501,684 waterway cells statewide.
#
# (lon, lat) WGS84. Each must sit within PORT_PROBE_HALF_M of a rasterized
# waterway cell — the check counts network cells, not any water pixel, since
# the network is what routing traverses. Homer is deliberately absent: the
# NWN has no segment within 3 km of it.
ICE_FREE_PORTS = {
    "Ketchikan":   (-131.65, 55.34),
    "Sitka":       (-135.36, 57.05),
    "Juneau":      (-134.40, 58.30),
    "Petersburg":  (-132.96, 56.81),
    "Kodiak":      (-152.40, 57.79),
    "Seward":      (-149.42, 60.05),
    "Valdez":      (-146.35, 61.10),
    "Whittier":    (-148.68, 60.77),
}

# The converse tripwire: western/northern ports whose barge season really is
# seasonal. These MUST be open in August and closed in February. Without
# them, "make the Gulf open year-round" could be satisfied by switching ice
# gating off entirely.
SEASONAL_PORTS = {
    "Nome":       (-165.42, 64.50),
    "Utqiagvik":  (-156.79, 71.30),
}

# Interior river points that MUST freeze. Same open-in-August /
# closed-in-February rule as SEASONAL_PORTS, but chosen to exercise each tier
# of the river-ice gate, so a regression in any one of them is caught:
#
#   Yukon @ Galena      59/59 cells IDW-covered   -> tier 1, the raw product
#   Kuskokwim @ Aniak   64/64 covered             -> tier 1
#   Yukon @ Holy Cross  78 river cells, 0 covered -> tier 2, nearest-fill
#   Egegik River        10 river cells, 0 covered -> tier 3, latitude band
#
# Egegik is the important one. It has no IDW coverage and no covered cell
# within RIVER_ICE_FILL_MAX_KM, so it reaches the band fallback. If that
# fallback ever returns 0 — an empty band, a broken CRS, a silent refactor
# back to "no fill" — Egegik opens in February and this is what says so.
FREEZING_RIVERS = {
    "Yukon @ Galena":     (-156.93, 64.73),
    "Kuskokwim @ Aniak":  (-159.53, 61.58),
    "Yukon @ Holy Cross": (-159.77, 62.20),
    "Egegik River":       (-157.40, 58.20),
}

# Half-width of the window sampled around each port, in metres. 2 km is the
# smallest radius at which every port above has waterway cells in frame, so
# the check does not hinge on 150 m harbour geometry.
PORT_PROBE_HALF_M = 2_000.0


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


def _port_window(transform, lon: float, lat: float):
    """Square window of PORT_PROBE_HALF_M around a lon/lat, on `transform`."""
    x, y = pyproj.Transformer.from_crs(
        "EPSG:4326", "EPSG:3338", always_xy=True
    ).transform(lon, lat)
    return rasterio.windows.from_bounds(
        x - PORT_PROBE_HALF_M, y - PORT_PROBE_HALF_M,
        x + PORT_PROBE_HALF_M, y + PORT_PROBE_HALF_M,
        transform=transform,
    )


def _port_network_cells(lon: float, lat: float) -> np.ndarray:
    """Boolean window of rasterized waterway cells around a port."""
    with rasterio.open(WATERWAY_MASK_TIF) as mw:
        win = _port_window(mw.transform, lon, lat)
        return mw.read(1, window=win, boundless=True, fill_value=0) == 1


def _port_navigable(src, lon: float, lat: float, network: np.ndarray) -> bool:
    """True if any WATERWAY cell near the port is navigable on this surface.

    Counts network cells rather than any water pixel: off-network water can
    be open while the routed network beside it is severed, and the network is
    what the graph actually traverses. Reads a small window rather than the
    full 28,001 x 16,567 band, so the 12-month sweep costs kilobytes.
    """
    win = _port_window(src.transform, lon, lat)
    arr = src.read(1, window=win, boundless=True, fill_value=FRICTION_NODATA)
    return bool(np.any(network & (arr != FRICTION_NODATA)))


def check_year_round_ports(friction_dir: Path) -> list[str]:
    """Check 2: ice-free ports open all 12 months; seasonal ports closed in Feb.

    This is the regression gate for the river-ice-on-salt-water bug. It is
    deliberately expressed in terms of real operating facts (twice-weekly
    year-round service to Southeast Alaska) rather than pixel counts, so it
    stays meaningful if the rasters are rebuilt from different inputs.
    """
    errors: list[str] = []
    if not Path(WATERWAY_MASK_TIF).exists():
        return [f"waterway mask not found at {WATERWAY_MASK_TIF}; "
                "run 01_build_corridor_masks.py before QA"]

    all_ports = {**ICE_FREE_PORTS, **SEASONAL_PORTS, **FREEZING_RIVERS}
    network = {p: _port_network_cells(*ll) for p, ll in all_ports.items()}
    for port, cells in network.items():
        if not cells.any():
            errors.append(
                f"{port} has no waterway cell within "
                f"{PORT_PROBE_HALF_M:.0f} m — the port coordinate or the "
                "network changed; this check cannot see it"
            )
    if errors:
        return errors

    closures: dict[str, list[int]] = {}
    summer_open: dict[str, bool] = {}
    feb_open: dict[str, bool] = {}
    for month in range(1, 13):
        with rasterio.open(friction_dir / f"barge_{month:02d}.tif") as src:
            for port, (lon, lat) in ICE_FREE_PORTS.items():
                if not _port_navigable(src, lon, lat, network[port]):
                    closures.setdefault(port, []).append(month)
            if month in (2, 8):
                target = feb_open if month == 2 else summer_open
                seasonal = {**SEASONAL_PORTS, **FREEZING_RIVERS}
                for port, (lon, lat) in seasonal.items():
                    target[port] = _port_navigable(src, lon, lat, network[port])

    if closures:
        for port, months in sorted(closures.items()):
            errors.append(
                f"{port} has no navigable waterway cell in month(s) {months} — "
                "this port carries year-round commercial barge service. Check "
                "that river ice is clipped to waterway_river_mask_150m.tif in "
                "both extend_ice_nearest and build_mode_friction."
            )
    else:
        logger.info(
            "year-round ports OK: all %d Gulf/SE ports navigable in 12/12 months",
            len(ICE_FREE_PORTS),
        )

    still_open = sorted(p for p, o in feb_open.items() if o)
    never_open = sorted(p for p, o in summer_open.items() if not o)
    if still_open:
        rivers = [p for p in still_open if p in FREEZING_RIVERS]
        ports = [p for p in still_open if p not in FREEZING_RIVERS]
        if ports:
            errors.append(
                f"seasonal port(s) {ports} navigable in February — sea-ice "
                "gating looks disabled, not merely re-scoped"
            )
        if rivers:
            errors.append(
                f"river site(s) {rivers} navigable in February — these are "
                "frozen interior rivers. Check the river-ice tiers in "
                "write_friction_stack: an empty latitude band, a missing "
                "river mask, or a fill cap that rejected everything all "
                "leave p_ice=0 here."
            )
    if never_open:
        errors.append(
            f"seasonal site(s) {never_open} not navigable in August — the "
            "gate is closing water that should be open"
        )
    if not still_open and not never_open:
        logger.info(
            "seasonal sites OK: %s open in August, closed in February",
            ", ".join(sorted({**SEASONAL_PORTS, **FREEZING_RIVERS})),
        )
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
        ("year-round ports",         lambda: check_year_round_ports(friction_dir)),
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
