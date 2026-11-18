#!/usr/bin/env bash
# Workflow 03 — join network + friction into weighted multimodal edges.
# Stages 01-02 run from COMMITTED data alone (the frozen final_network zips);
# stages 03-04 additionally need the friction stack from workflow 01.
# Usage:  bash workflows/03_multimodal_join/run_all.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"
. "$HERE/../_lib.sh"
resolve_python

run_step "01_extract_network_handoff" "$PY" "$HERE/01_extract_network_handoff.py"
run_step "02_load_final_network"      "$PY" "$HERE/02_load_final_network.py"

if [ ! -f outputs/01_friction_build/friction_stack/road_base.tif ]; then
  echo "GATE: friction stack missing (outputs/01_friction_build/friction_stack/)."
  echo "  Stages 03-04 need workflow 01's rasters. Fetch the finished stack from the Zenodo"
  echo "  deposit:  $PY tools/fetch_archive.py --group friction_stack   (DATA.md, path 2)"
  echo "  or build it: bash workflows/01_friction_build/run_all.sh (DATA.md section 3)."
  echo "  Stopping after the ingest stage (network_nodes + network_edges written)."
  exit "$GATE_EXIT"
fi

run_step "03_weight_network_edges"    "$PY" "$HERE/03_weight_network_edges.py"
run_step "04_assemble_weighted_graph" "$PY" "$HERE/04_assemble_weighted_graph.py"

# Marine/river class per Waterway edge (needs workflow 01's water-class label;
# guarded here so a stack-only machine still completes the weighting above).
if [ -f outputs/01_friction_build/water_class_150m.tif ]; then
  run_step "05_edge_water_class" "$PY" "$HERE/05_edge_water_class.py"
else
  echo "SKIP 05_edge_water_class: water_class_150m.tif absent (run workflow 01's 04_build_water_class.py)."
fi
# Barge passability by hub — the check that would have caught Kodiak/Unalaska.
# A NEW no-summer-path barge hub fails; known ones live in
# inputs/network_qc/accepted_barge_exceptions.csv.
run_step "06_qa_barge_passability" "$PY" "$HERE/06_qa_barge_passability.py"
echo "Done. Tables in outputs/fuel_network.duckdb."
