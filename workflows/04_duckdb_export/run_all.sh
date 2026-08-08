#!/usr/bin/env bash
# Workflow 04 — certify + document the DuckDB deliverable.
# Usage:  bash workflows/04_duckdb_export/run_all.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"
. "$HERE/../_lib.sh"
resolve_python

if [ ! -f outputs/fuel_network.duckdb ]; then
  gate "outputs/fuel_network.duckdb missing." \
       "Run workflow 03 first: bash workflows/03_multimodal_join/run_all.sh"
fi
run_step "01_run_validation_queries" "$PY" "$HERE/01_run_validation_queries.py"
run_step "02_inspect_schema"         "$PY" "$HERE/02_inspect_schema.py"
echo "Done."
