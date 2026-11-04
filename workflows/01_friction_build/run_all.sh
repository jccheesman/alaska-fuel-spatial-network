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

if [ ! -f inputs/friction_rasters/lulc.tif ]; then
  gate "inputs/friction_rasters/lulc.tif missing." \
       "The friction rasters are not in the repository: download and regenerate them" \
       "(GEE export + pad/align + river-ice pipeline), then re-run. See DATA.md section 3.1."
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
