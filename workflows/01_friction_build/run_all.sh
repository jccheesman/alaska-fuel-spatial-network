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

if [ ! -f inputs/friction_rasters/lulc.tif ]; then
  echo "GATE: inputs/friction_rasters/lulc.tif missing."
  echo "  The ~7 GB friction rasters are not committed (regenerable only)."
  echo "  Regenerate via src/friction_surface/friction_preprocessing/ (GEE + arcpy),"
  echo "  then re-run. See EXTERNAL_DATA.md."
  exit 1
fi
if [ ! -d inputs/data_for_network_build ]; then
  echo "GATE: inputs/data_for_network_build/ not extracted — run: python tools/extract_inputs.py"
  exit 1
fi

python3 "$HERE/00_preflight_inputs.py"
python3 "$HERE/01_build_corridor_masks.py"
python3 "$HERE/02_build_friction_stack.py"
python3 "$HERE/03_qa_friction_stack.py"
echo "Done. Friction stack in outputs/01_friction_build/friction_stack/."
