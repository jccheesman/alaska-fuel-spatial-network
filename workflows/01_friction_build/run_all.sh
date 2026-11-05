#!/usr/bin/env bash
# Workflow 01 — friction-layer build: preflight -> corridor mask -> stack -> QA.
# Requires inputs/friction_rasters/ (not in the repository — download and
# regenerate, DATA.md §3.1) and the waterways shapefile unzipped from
# inputs/data_for_network_build.zip (python tools/extract_inputs.py).
# Usage:  bash workflows/01_friction_build/run_all.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"
. "$HERE/../_lib.sh"
resolve_python

# The land-cover raster is the grid anchor; its name is the producer's (GEE) name,
# defined once in source_scripts/friction_surface/friction_paths.py (RASTER_NAMES).
LULC="inputs/friction_rasters/dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif"
if [ ! -f "$LULC" ]; then
  gate "$LULC missing." \
       "The friction rasters are not in the repository. Either fetch them from the Zenodo" \
       "deposit:  $PY tools/fetch_archive.py --group friction_inputs   (DATA.md, path 2)" \
       "or regenerate them (GEE export + pad/align + river-ice pipeline; DATA.md section 3.1)."
fi
if [ ! -d inputs/data_for_network_build ]; then
  gate "inputs/data_for_network_build/ not extracted." \
       "Run: $PY tools/extract_inputs.py"
fi

run_step "00_preflight_inputs"      "$PY" "$HERE/00_preflight_inputs.py"
run_step "01_build_corridor_masks"  "$PY" "$HERE/01_build_corridor_masks.py"
run_step "02_build_friction_stack"  "$PY" "$HERE/02_build_friction_stack.py"
run_step "03_qa_friction_stack"     "$PY" "$HERE/03_qa_friction_stack.py"
echo "Done. Friction stack in outputs/01_friction_build/friction_stack/."
