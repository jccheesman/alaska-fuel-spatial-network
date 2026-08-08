#!/usr/bin/env bash
# One-command reproduction of the four-act pipeline:
#   (a) 01_friction_build   — friction stack        [needs the ~7 GB regenerable rasters]
#   (b) 02_network_build    — multimodal network    [needs inputs/network_raw.zip extracted]
#   (c) 03_multimodal_join  — weighted edges        [stages 01-02 run from committed data]
#   (d) 04_duckdb_export    — validate the deliverable
#
# Each stage gates on its inputs and states how to regenerate what's missing,
# so a fresh clone runs as far as the committed data allows (acts c-d ingest)
# and tells you exactly what the rest needs.
#
# A stage that exits GATE_EXIT (3) is SKIPPED — a documented missing input, not
# a bug. Any other non-zero exit is a real FAILURE and makes this script exit
# non-zero, so CI and humans can tell the two apart.
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
. "$ROOT/workflows/_lib.sh"

skipped=()
failed=()

for wf in 01_friction_build 02_network_build 03_multimodal_join 04_duckdb_export; do
  echo; echo "================ workflows/$wf ================"
  set +e
  bash "$ROOT/workflows/$wf/run_all.sh"
  rc=$?
  set -e
  if [ "$rc" -eq 0 ]; then
    :
  elif [ "$rc" -eq "$GATE_EXIT" ]; then
    echo "[run_all] $wf SKIPPED — missing input (gate above explains what)."
    skipped+=("$wf")
  else
    echo "[run_all] $wf FAILED (exit $rc)." >&2
    failed+=("$wf")
  fi
done

echo
echo "================ summary ================"
echo "skipped (missing inputs): ${skipped[*]:-none}"
echo "failed  (real errors)   : ${failed[*]:-none}"

if [ "${#failed[@]}" -gt 0 ]; then
  echo "run_all: FAILED — ${#failed[@]} stage(s) errored." >&2
  exit 1
fi
echo "run_all complete."
