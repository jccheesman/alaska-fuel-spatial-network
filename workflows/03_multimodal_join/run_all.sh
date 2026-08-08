#!/usr/bin/env bash
# Workflow 03 — join network + friction into weighted multimodal edges.
# Stages 01-02 run from COMMITTED data alone (the frozen final_network zips);
# stages 03-04 additionally need the friction stack from workflow 01.
# Usage:  bash workflows/03_multimodal_join/run_all.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"

python3 "$HERE/01_extract_network_handoff.py"
python3 "$HERE/02_load_final_network.py"

if [ ! -f outputs/01_friction_build/friction_stack/road_base.tif ]; then
  echo "GATE: friction stack missing (outputs/01_friction_build/friction_stack/)."
  echo "  Stages 03-04 need workflow 01's rasters — regenerate via"
  echo "  bash workflows/01_friction_build/run_all.sh (see EXTERNAL_DATA.md)."
  echo "  Stopping after the ingest stage (network_nodes + network_edges written)."
  exit 0
fi

python3 "$HERE/03_weight_network_edges.py"
python3 "$HERE/04_assemble_weighted_graph.py"
echo "Done. Tables in outputs/fuel_network.duckdb."
