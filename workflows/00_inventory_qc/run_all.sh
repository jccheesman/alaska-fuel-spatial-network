#!/usr/bin/env bash
# Workflow 00 — facility-inventory QC: verify releases, apply approved corrections,
# normalise, run detectors + boundary check, build the review queue, publish the clean table.
# Usage:  bash workflows/00_inventory_qc/run_all.sh [RELEASE]      (default: latest release folder)
#         RELEASE must be a folder under inputs/raw_facility_data/.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"
. "$HERE/../_lib.sh"
resolve_python

REL="${1:-}"
if [ -n "$REL" ] && [ ! -f "inputs/raw_facility_data/$REL/snapshot_manifest.json" ]; then
  gate "inputs/raw_facility_data/$REL/ has no snapshot_manifest.json." \
       "Ingest it first: $PY workflows/00_inventory_qc/01_ingest.py RAW.csv --release $REL"
fi
RELARG=(); [ -n "$REL" ] && RELARG=(--release "$REL")

run_step "01_ingest --check"     "$PY" "$HERE/01_ingest.py" --check
run_step "02_apply_corrections"  "$PY" "$HERE/02_apply_corrections.py" "${RELARG[@]}"
run_step "03_normalise"          "$PY" "$HERE/03_normalise.py" "${RELARG[@]}"
run_step "04_detect"            "$PY" "$HERE/04_detect.py" "${RELARG[@]}"
run_step "05_boundary_check"    "$PY" "$HERE/05_boundary_check.py" "${RELARG[@]}"
run_step "06_review_queue"      "$PY" "$HERE/06_review_queue.py" "${RELARG[@]}"
run_step "07_publish"            "$PY" "$HERE/07_publish.py" "${RELARG[@]}"
echo "Done."
