"""repo_paths.py — every repository location in one place.

Scripts used to compute the repo root themselves
(``Path(__file__).resolve().parents[N]``) and then spell out their own
``ROOT / "outputs" / ...`` paths, so moving any folder meant editing dozens
of files. They now import from here:

    import repo_paths as rp
    DB_PATH = rp.DUCKDB

Moving a folder is then a one-line change in this module.

Anchored to files, never the working directory. A script operates on the
checkout it lives in: when the running script (``__main__``) sits inside a
checkout of this repo, that checkout is ROOT — so a virtualenv shared by
several clones (CI's driver-parity step) never points one clone's scripts at
another clone's data. Imported from anywhere else (pytest, a notebook), ROOT
is the checkout holding this file. No environment overrides here — the
friction pipeline keeps its own (``RASTER_DIR``, ``FRICTION_DIR``, ...) in
``friction_surface.friction_paths``, which takes its defaults from this module.

Two scripts deliberately do NOT import this: ``run_all.py`` (it picks the
interpreter, so it may run outside the project environment) and
``tools/extract_inputs.py`` (stdlib-only, runs straight after cloning). The
``mmnet`` engine doesn't either: it is region-agnostic and takes every path
from ``profile.yaml``.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _find_root() -> Path:
    main = getattr(sys.modules.get("__main__"), "__file__", None)
    if main:
        for d in Path(main).resolve().parents:
            if (d / "source_scripts" / "repo_paths.py").is_file():
                return d
    return Path(__file__).resolve().parents[1]


ROOT = _find_root()

# --- top-level trees ---------------------------------------------------------
INPUTS = ROOT / "inputs"
DATA = ROOT / "data"                 # workflow 02 working tree (gitignored)
OUTPUTS = ROOT / "outputs"
WORKFLOWS = ROOT / "workflows"
FINAL_NETWORK = ROOT / "final_network"

# --- inputs/ -------------------------------------------------------------------
FACILITY_RELEASES = INPUTS / "raw_facility_data"      # one folder per AEA release
INVENTORY_QC = INPUTS / "inventory_qc"                # QC config: schema, corrections, ...
BULK_FUEL_DATA = INPUTS / "bulk_fuel_data"            # extracted 2022 bundle
NETWORK_DATA = INPUTS / "data_for_network_build"      # extracted curated shapefiles
FRICTION_RASTERS = INPUTS / "friction_rasters"        # canonical-grid rasters (not committed)
AIR_INPUTS = INPUTS / "air"
MANUAL_CONNECTIONS = INPUTS / "mannual_connections" / "mannual_connections.shp"
TIGER_STATES = INPUTS / "region_and_census_data" / "tiger" / "cb_2023_us_state_500k.shp"

# --- data/ (workflow 02 working tree) ------------------------------------------
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
BASEMAP = DATA / "basemap"
BOUNDARY = DATA / "boundary.geojson"

# --- outputs/ ------------------------------------------------------------------
INVENTORY_QC_OUT = OUTPUTS / "00_inventory_qc"        # <release>/facilities_clean.csv
FRICTION_BUILD = OUTPUTS / "01_friction_build"
FRICTION_STACK = FRICTION_BUILD / "friction_stack"
NETWORK_PROJECT = OUTPUTS / "02_network_build"        # mmnet project dir: output/ + reports/
DUCKDB = OUTPUTS / "fuel_network.duckdb"
FIGURES = OUTPUTS / "figures"
TABLES = OUTPUTS / "tables"
NETWORK_PLOTS = OUTPUTS / "final_network_plots"
DIAGNOSTICS_OUT = OUTPUTS / "diagnostics"         # diagnostics/<stage>/ scripts write here

# --- workflows/ ----------------------------------------------------------------
INVENTORY_QC_WORKFLOW = WORKFLOWS / "00_inventory_qc"
NETWORK_PROFILE = WORKFLOWS / "02_network_build" / "profile.yaml"

# --- final_network/ (the network-of-record; edge_id = edges row order) ---------
FINAL_NODES_SHP = FINAL_NETWORK / "network_joined_nodes" / "network_joined_nodes.shp"
FINAL_EDGES_SHP = FINAL_NETWORK / "network_joined_edges" / "network_joined_edges.shp"
HUB_MEMBERS_CSV = FINAL_NETWORK / "hub_members.csv"
HUB_SNAPS_CSV = FINAL_NETWORK / "hub_snaps.csv"
