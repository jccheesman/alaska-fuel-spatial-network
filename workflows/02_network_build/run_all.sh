#!/usr/bin/env bash
# Workflow 02 — spatial-network build. Re-run the WHOLE stage from profile.yaml:
# after any profile edit this refreshes every downstream artifact.
#
#   0-2. prep (only if data/interim is missing): normalize_raw -> prep_waterway -> prep_airways
#   3. validate the profile
#   4. build the network (mmnet stages 01->04 + reports)
#   5. verify the expected connected network (North Slope gate)
#   6. QGIS projects + component distances + figures
#   7. export the final_network/ handoff (zips + sha256 manifest)
#
# Artifacts: outputs/02_network_build/{output,reports}; handoff: final_network/.
# Usage:  bash workflows/02_network_build/run_all.sh [profile.yaml]
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"
PROFILE="${1:-$HERE/profile.yaml}"
FILT='Axes3D|warnings.warn|user_version|QStandardPaths|Application path'

if [ ! -d data/raw ] || [ -z "$(ls -A data/raw 2>/dev/null)" ]; then
  echo "GATE: data/raw is empty. Populate it first:"
  echo "  python tools/extract_inputs.py   (needs inputs/network_raw.zip — see inputs/README.md)"
  exit 1
fi

if [ ! -d data/interim ] || [ -z "$(ls -A data/interim 2>/dev/null)" ]; then
  echo "######## 0-2. prep: normalize_raw -> prep_waterway -> prep_airways ########"
  python3 "$HERE/00_normalize_raw.py"  2>&1 | grep -vE "$FILT" || true
  python3 "$HERE/01_prep_waterway.py"  2>&1 | grep -vE "$FILT" || true
  python3 "$HERE/02_prep_airways.py"   2>&1 | grep -vE "$FILT" || true
fi

echo; echo "######## 3-4. validate + build (mmnet 01->04 + reports) ########"
python3 "$HERE/04_build_network.py" "$PROFILE" 2>&1 | grep -vE "$FILT" || true

echo; echo "######## 5. verify the expected connected network ########"
python3 "$HERE/05_verify_north_slope.py" 2>&1 | grep -vE "$FILT" || true

echo; echo "######## 6. QGIS projects + components + figures ########"
python3 "$HERE/viz/export_qgis.py" 2>&1 | grep -vE "$FILT" || true
if [ -f outputs/02_network_build/output/04_network_joined__nodes.gpkg ]; then
  python3 "$HERE/viz/export_qgis.py" --stem 04_network_joined 2>&1 | grep -vE "$FILT" || true
fi
python3 "$HERE/viz/export_qgis_components.py" 2>&1 | grep -vE "$FILT" || true
python3 "$HERE/viz/plot_components.py" 2>&1 | grep -vE "$FILT" || true
if [ -f outputs/02_network_build/output/04_network_joined__nodes.gpkg ]; then
  python3 "$HERE/viz/plot_join.py" 2>&1 | grep -vE "$FILT" || true
fi

echo; echo "######## 7. export the final_network/ handoff ########"
echo "NOTE: overwrites the frozen network-of-record extraction; only COMMIT the"
echo "      regenerated zips deliberately (edge_id contract — final_network/README.md)."
python3 "$HERE/06_export_final_network.py" 2>&1 | grep -vE "$FILT" || true

echo; echo "Done. Artifacts in outputs/02_network_build/{output,reports}; handoff in final_network/."
