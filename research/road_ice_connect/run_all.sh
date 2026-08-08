#!/usr/bin/env bash
# Run the road↔ice-road gap study end to end. Requires output/03_network__*.gpkg (build first).
set -euo pipefail
cd "$(dirname "$0")"
python3 01_gaps.py
python3 02_candidates_map.py
python3 03_sensitivity.py
echo "done — see out/01_gaps.md, out/02_candidates.md, out/03_sensitivity.md and METHOD.md"
