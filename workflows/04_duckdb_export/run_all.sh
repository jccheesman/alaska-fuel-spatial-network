#!/usr/bin/env bash
# Workflow 04 — certify + document the DuckDB deliverable.
# Usage:  bash workflows/04_duckdb_export/run_all.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"

if [ ! -f outputs/fuel_network.duckdb ]; then
  echo "GATE: outputs/fuel_network.duckdb missing — run workflow 03 first."
  exit 1
fi
python3 "$HERE/01_run_validation_queries.py"
python3 "$HERE/02_inspect_schema.py"
echo "Done."
