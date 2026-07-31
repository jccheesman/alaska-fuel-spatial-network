# -*- coding: utf-8 -*-
"""friction_paths.py

Path construction for the friction-layer pipeline. Centralizes raster and
network file locations so build scripts don't bake in directory layout.

Defaults are environment-overridable via RASTER_DIR and NETWORK_DIR; the
re-export shim in friction_config keeps existing call sites working.

Path resolution does not depend on the process working directory: the
default paths below are anchored to PROJECT_ROOT (the directory containing
the friction_surface package) as absolute paths. Environment overrides are
used verbatim, so a relative override is still resolved against the CWD.

Importing this module additionally chdirs into PROJECT_ROOT for backward
compatibility with sibling scripts at the repo root that use bare relative
paths like ``./outputs``. Set FRICTION_NO_CHDIR=1 to opt out (e.g., when
embedding in another tool); the anchored defaults keep working either way.
"""

from __future__ import annotations
import os

# ---------------------------------------------------------------------------
# Project-root chdir
# ---------------------------------------------------------------------------
# friction_paths.py lives inside the friction_surface/ package; the project
# root is one level up.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if not os.environ.get("FRICTION_NO_CHDIR") and os.getcwd() != PROJECT_ROOT:
    os.chdir(PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Raster inputs
# ---------------------------------------------------------------------------
RASTER_DIR = os.getenv(
    "RASTER_DIR",
    os.path.join(PROJECT_ROOT, "friction_surface", "friction_inputs"),
)

RASTER_FILES = {
    "slope":      os.path.join(RASTER_DIR, "slope.tif"),
    "lulc":       os.path.join(RASTER_DIR, "lulc.tif"),
    "permafrost": os.path.join(RASTER_DIR, "permafrost.tif"),
    "sea_ice":    os.path.join(RASTER_DIR, "sea_ice"),    # directory of sea_ice_{01..12}.tif
    "river_ice":  os.path.join(RASTER_DIR, "river_ice"),  # directory of river_ice_{01..12}.tif
}

# Friction-stack output directory (the 24 monthly friction TIFs: 12 overland
# + 12 barge). Kept with the other friction outputs rather than under
# RASTER_DIR.
FRICTION_OUTPUT_DIR = os.getenv(
    "FRICTION_DIR",
    os.path.join(PROJECT_ROOT, "friction_surface", "friction_outputs",
                 "friction_stack"),
)


# ---------------------------------------------------------------------------
# Network vectors
# ---------------------------------------------------------------------------
NETWORK_DIR = os.getenv(
    "NETWORK_DIR", os.path.join(PROJECT_ROOT, "inputs", "data_for_network_build")
)

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
INPUTS_DIR = os.getenv("INPUTS_DIR", os.path.join(PROJECT_ROOT, "inputs"))
OUTPUTS_DIR = os.getenv("OUTPUTS_DIR", os.path.join(PROJECT_ROOT, "outputs"))

# The .shp form ships zipped at inputs/bulk_fuel_data/raw/Fuel_Delivery_Method.zip;
# only the .csv (below) is read by code (friction_costs.load_ice_road_communities).
FUEL_DELIVERY_METHOD_SHP = os.path.join(INPUTS_DIR, "bulk_fuel_data", "raw",
                                        "Fuel_Delivery_Method.shp")
FUEL_DELIVERY_METHOD_CSV = os.path.join(INPUTS_DIR, "literature_sources_for_agent_analysis",
                                        "market_data", "Fuel_Delivery_Method.csv")
ICE_ROADS_SHP = os.path.join(NETWORK_DIR, "ice_roads_150m_3338",
                             "Ice_Roads.shp")

# Rasterized corridor masks (built by build_corridor_masks.py). Each gates
# routing for its mode in friction_surface.build_mode_friction.
ICE_ROAD_MASK_TIF = os.path.join(OUTPUTS_DIR, "ice_road_mask_150m.tif")
ROAD_MASK_TIF     = os.path.join(OUTPUTS_DIR, "road_mask_150m.tif")
WATERWAY_MASK_TIF = os.path.join(OUTPUTS_DIR, "waterway_mask_150m.tif")


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------

def get_raster_dir() -> str:
    """Path to the GEE raster directory.

    Returns the import-time-captured RASTER_DIR (env var RASTER_DIR with
    default ./friction_surface/friction_inputs). Re-reading the env on
    every call would let this drift from RASTER_FILES, which is built
    from the import-time value.
    """
    return RASTER_DIR


def get_friction_output_dir() -> str:
    """Path to the friction-stack output directory.

    Returns the import-time-captured FRICTION_OUTPUT_DIR (env var
    FRICTION_DIR with default ./friction_surface/friction_outputs/friction_stack).
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
