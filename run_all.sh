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
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

for wf in 01_friction_build 02_network_build 03_multimodal_join 04_duckdb_export; do
  echo; echo "================ workflows/$wf ================"
  bash "$ROOT/workflows/$wf/run_all.sh" || {
    echo "[run_all] workflows/$wf stopped (gate above explains the missing input); continuing."
  }
done
echo; echo "run_all complete — see each stage's gate messages above for anything skipped."
