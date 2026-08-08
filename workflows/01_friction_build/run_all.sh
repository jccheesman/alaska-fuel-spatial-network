#!/usr/bin/env bash
# Workflow 01 — friction-layer build: preflight -> corridor mask -> stack -> QA.
# Requires inputs/friction_rasters/ (~7 GB, NOT committed — regenerate from the
# GEE export + arcpy river-ice pipeline; see EXTERNAL_DATA.md) and the waterways
# shapefile from inputs/data_for_network_build.zip (python tools/extract_inputs.py).
# Usage:  bash workflows/01_friction_build/run_all.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"
. "$HERE/../_lib.sh"
resolve_python

if [ ! -f inputs/friction_rasters/lulc.tif ]; then
  gate "inputs/friction_rasters/lulc.tif missing." \
       "The ~7 GB friction rasters are not committed (regenerable only)." \
       "Regenerate via src/friction_surface/friction_preprocessing/ (GEE + arcpy)," \
       "then re-run. See EXTERNAL_DATA.md."
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
