# -*- coding: utf-8 -*-
"""friction_paths.py

Path construction for the friction-layer pipeline. Centralizes raster and
network file locations so build scripts don't bake in directory layout.

Defaults are environment-overridable via RASTER_DIR and NETWORK_DIR; the
re-export shim in friction_config keeps existing call sites working.

Path resolution does not depend on the process working directory: the
default paths below come from ``repo_paths`` (the one place every repository
location is defined) as absolute paths. Environment overrides are used
verbatim, so a relative override is still resolved against the CWD.

This module has no import-time side effects. (The old import-time
``os.chdir(PROJECT_ROOT)`` is gone: every consumer now anchors its paths
absolutely, so scripts can run from any working directory.)
"""

from __future__ import annotations
import os
import sys
import logging
from datetime import datetime

import repo_paths as rp

# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = str(rp.ROOT)


# ---------------------------------------------------------------------------
# Raster inputs
# ---------------------------------------------------------------------------
RASTER_DIR = os.getenv("RASTER_DIR", str(rp.FRICTION_RASTERS))

# ---------------------------------------------------------------------------
# THE ONE NAME RULE (owner, 2026-11-04): every input raster keeps the name its
# producer wrote, all the way through the pipeline. The Earth Engine script
# (friction_preprocessing/gee_friction_layer_multi_data_processing.js) exports
# slope, land cover, permafrost and the sea-ice medians under exactly these
# names; the ArcGIS river-ice pipeline (river_ice_full_pipeline.py) writes
# the river-ice names below. Padding and alignment happen IN PLACE under the
# same name (the raw export is kept beside it in gee_export/). Nothing is
# ever renamed on disk, so a reader can trace a file from the download to
# the build by its name alone.
#
# This dict and the two month helpers are the only place the names live.
# Everything else (the loaders, preflight, the grid checker, the pad/align
# scripts, the tests, the run drivers' gate) reads them from here. The
# arcpy script cannot import this module (it runs in ArcGIS Pro's Python),
# so it repeats RIVER_ICE_NAME_FMT verbatim; tests/test_friction_paths.py
# checks that the two copies agree.
# ---------------------------------------------------------------------------
RASTER_NAMES = {
    "slope":      "FABDEM_slope_150m_EPSG3338.tif",
    "lulc":       "dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif",
    "permafrost": "permafrost_probability_150m_EPSG3338.tif",
}
# Monthly stacks live in a sub-folder each; {mm} is the zero-padded month,
# {mon} the three-letter English abbreviation GEE put in the sea-ice names.
SEA_ICE_SUBDIR = "sea_ice"
RIVER_ICE_SUBDIR = "river_ice"
SEA_ICE_NAME_FMT = "sea_ice_median_{mm}_{mon}_150m_EPSG3338.tif"
RIVER_ICE_NAME_FMT = "river_ice_probability_{mm}_150m_EPSG3338.tif"
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def sea_ice_name(month: int) -> str:
    """File name of the sea-ice median for `month` (1..12), e.g.
    sea_ice_median_03_Mar_150m_EPSG3338.tif."""
    return SEA_ICE_NAME_FMT.format(mm=f"{month:02d}", mon=MONTH_ABBR[month - 1])


def river_ice_name(month: int) -> str:
    """File name of the river-ice probability for `month` (1..12), e.g.
    river_ice_probability_03_150m_EPSG3338.tif."""
    return RIVER_ICE_NAME_FMT.format(mm=f"{month:02d}")


def sea_ice_relpath(month: int) -> str:
    """Path of the month's sea-ice raster relative to the raster directory."""
    return os.path.join(SEA_ICE_SUBDIR, sea_ice_name(month))


def river_ice_relpath(month: int) -> str:
    """Path of the month's river-ice raster relative to the raster directory."""
    return os.path.join(RIVER_ICE_SUBDIR, river_ice_name(month))


RASTER_FILES = {
    "slope":      os.path.join(RASTER_DIR, RASTER_NAMES["slope"]),
    "lulc":       os.path.join(RASTER_DIR, RASTER_NAMES["lulc"]),   # the grid anchor
    "permafrost": os.path.join(RASTER_DIR, RASTER_NAMES["permafrost"]),
    "sea_ice":    os.path.join(RASTER_DIR, SEA_ICE_SUBDIR),    # directory, see sea_ice_name
    "river_ice":  os.path.join(RASTER_DIR, RIVER_ICE_SUBDIR),  # directory, see river_ice_name
}

# Friction-stack output directory (the 24 monthly friction TIFs: 12 overland
# + 12 barge, backed by 14 physical files). Produced by workflow 01.
FRICTION_OUTPUT_DIR = os.getenv("FRICTION_DIR", str(rp.FRICTION_STACK))


# ---------------------------------------------------------------------------
# Network vectors
# ---------------------------------------------------------------------------
NETWORK_DIR = os.getenv("NETWORK_DIR", str(rp.NETWORK_DATA))

NETWORK_FILES = {
    "roads":     os.path.join(NETWORK_DIR, "roads_networks",
                              "ak_albers_roads_merge.shp"),
    "waterways": os.path.join(NETWORK_DIR, "water_networks",
                              "waterways_network_ak_albers.shp"),
    # NOTE: the public data bundle ships airports/flights as CSVs
    # (data_for_network_build/Airports.csv, Flights/flight_paths_combined.csv);
    # the *_ak_albers.shp vector forms are not included — regenerate from the
    # CSVs or supply your own before using these two entries.
    "airports":  os.path.join(NETWORK_DIR, "airports",
                              "airports_ak_albers.shp"),
    "flight_paths": os.path.join(NETWORK_DIR, "flight_paths_ak_albers",
                                 "flight_paths_ak_albers.shp"),
    "ports":     os.path.join(NETWORK_DIR, "AK_Ports_and_Harbors.zip"),
}

NETWORK_CRS = "EPSG:3338"


# ---------------------------------------------------------------------------
# Ice-road datasets
# ---------------------------------------------------------------------------
INPUTS_DIR = os.getenv("INPUTS_DIR", str(rp.INPUTS))
OUTPUTS_DIR = os.getenv("OUTPUTS_DIR", str(rp.OUTPUTS))

# Ships zipped in inputs/raw_facility_data/2022/bulk_fuel_data.zip; extract with tools/extract_inputs.py.
# Read by friction_costs.load_ice_road_communities.
FUEL_DELIVERY_METHOD_SHP = os.path.join(INPUTS_DIR, "bulk_fuel_data", "raw",
                                        "Fuel_Delivery_Method.shp")
ICE_ROADS_SHP = os.path.join(NETWORK_DIR, "ice_roads_150m_3338",
                             "Ice_Roads.shp")

# Rasterized corridor mask (built by workflows/01_friction_build/
# 01_build_corridor_masks.py; consumed by the barge surfaces in
# friction_surface.build_mode_friction).
WATERWAY_MASK_TIF = os.path.join(OUTPUTS_DIR, "01_friction_build",
                                 "waterway_mask_150m.tif")

# Freshwater-river SUBSET of the waterway corridor mask, built by the same
# script from the NWN attribute classification in friction_config
# (RIVER_SEGMENT_*). This is the ONLY domain in which river ice is allowed to
# gate a barge pixel; everything else on the waterway network is salt water
# and is gated by the sea-ice climatology alone.
#
# Without it, the nearest-covered-cell fill in
# friction_surface.extend_ice_nearest smears interior river ice onto the
# marine network and closes the Gulf of Alaska, SE Alaska and Kodiak in
# winter — 414,895 of the 501,684 waterway cells (82.7%) are salt water. See
# the QA gate qa_friction_stack.check_year_round_ports.
WATERWAY_RIVER_MASK_TIF = os.path.join(OUTPUTS_DIR, "01_friction_build",
                                       "waterway_river_mask_150m.tif")


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------

def get_raster_dir() -> str:
    """Path to the input-raster directory.

    Returns the import-time-captured RASTER_DIR (env var RASTER_DIR with
    default <PROJECT_ROOT>/inputs/friction_rasters). Re-reading the env on
    every call would let this drift from RASTER_FILES, which is built
    from the import-time value.
    """
    return RASTER_DIR


def get_friction_output_dir() -> str:
    """Path to the friction-stack output directory.

    Returns the import-time-captured FRICTION_OUTPUT_DIR (env var
    FRICTION_DIR with default <PROJECT_ROOT>/outputs/01_friction_build/friction_stack).
    """
    return FRICTION_OUTPUT_DIR


def get_vector_dir() -> str:
    """Path to the vector data directory (VECTOR_DIR env var, default
    <PROJECT_ROOT>/vectors)."""
    return os.getenv("VECTOR_DIR", os.path.join(PROJECT_ROOT, "vectors"))


def get_raster_path(key: str) -> str:
    """Resolve a raster key (slope, lulc, permafrost, sea_ice, river_ice) to its path."""
    if key not in RASTER_FILES:
        raise KeyError(
            f"Unknown raster key {key!r}; expected one of {sorted(RASTER_FILES)}"
        )
    return RASTER_FILES[key]


def get_network_path(key: str) -> str:
    """Resolve a network key (roads, waterways, airports, flight_paths, ports) to its path."""
    if key not in NETWORK_FILES:
        raise KeyError(
            f"Unknown network key {key!r}; expected one of {sorted(NETWORK_FILES)}"
        )
    return NETWORK_FILES[key]


def setup_logging(log_dir=None):
    """Configure logging to both console and a timestamped log file.

    Args:
        log_dir: Directory for the log file. Defaults to <repo root>/outputs,
            anchored absolutely so callers work from any CWD.
    """
    if log_dir is None:
        log_dir = str(rp.OUTPUTS)
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"pipeline_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    print(f"Logging to: {log_file}")
    return log_file
