#!/usr/bin/env bash
# Workflow 02 — spatial-network build. Re-run the WHOLE stage from profile.yaml:
# after any profile edit this refreshes every downstream artifact.
#
#   0-2. prep (only if data/interim is missing): normalize_raw -> prep_waterway -> prep_airways
#   3. validate the profile
#   4. build the network (mmnet stages 01->04 + reports)
#   5. verify the expected connected network (North Slope gate)
#   6. QGIS projects + component distances + figures
#   7. export the final_network/ handoff — OPT-IN ONLY, see below
#
# Artifacts: outputs/02_network_build/{output,reports}; handoff: final_network/.
# Usage:  bash workflows/02_network_build/run_all.sh [profile.yaml]
#
# Step 7 is NOT run by default. A re-export replaces the frozen
# network-of-record, and because edge_id is shapefile row order, that
# invalidates every edge_id-keyed DuckDB table. To run it deliberately:
#     EXPORT_FINAL_NETWORK=1 bash workflows/02_network_build/run_all.sh
# Read final_network/README.md first.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"
. "$HERE/../_lib.sh"
resolve_python

PROFILE="${1:-$HERE/profile.yaml}"
FILT='Axes3D|warnings.warn|user_version|QStandardPaths|Application path'

# The six public layers of data/raw are downloads (DATA.md section 4.1); the ice-road
# layer is placed by tools/extract_inputs.py. Gate on the downloads by name so a
# partially staged folder is a clean skip, not a crash inside the build.
RAW_DOWNLOADS=(
  data/raw/connectivity/road/Roads_AKDOT/Roads_AKDOT.shp
  data/raw/connectivity/barge/NWN_Waterway_Network_Lines/Waterway_Network.shp
  data/raw/anchor_points/Ports_and_Harbors.geojson
  data/raw/boundaries/tiger_places/tl_2022_02_place.shp
  data/raw/boundaries/borough_census_area/Alaska_Borough_and_Census_Area_Boundaries.shp
  data/raw/boundaries/Fuel_Delivery_Method.geojson
)
missing=()
for f in "${RAW_DOWNLOADS[@]}"; do [ -f "$f" ] || missing+=("$f"); done
if [ "${#missing[@]}" -gt 0 ]; then
  gate "data/raw is missing ${#missing[@]} of the 6 public downloads:" \
       "${missing[@]}" \
       "Download each from its source (DATA.md section 4.1 lists the file and the link), and run" \
       "$PY tools/extract_inputs.py once for the ice-road layer."
fi

# Gate on the MANIFEST 00_normalize_raw writes LAST, not on mere non-emptiness:
# a crashed prep leaves a partial data/interim that would otherwise skip prep.
if [ ! -f data/interim/MANIFEST.md ]; then
  echo "######## 0-2. prep: normalize_raw -> prep_waterway -> prep_airways ########"
  run_step "00_normalize_raw" "$PY" "$HERE/00_normalize_raw.py"
  run_step "01_prep_waterway" "$PY" "$HERE/01_prep_waterway.py"
  run_step "02_prep_airways"  "$PY" "$HERE/02_prep_airways.py"
fi

# Manual connections: user-authored line layer(s) that stitch disconnected hubs into the
# network. Re-split EVERY build (outside the prep gate above) so edits to the shapefile take
# effect. Optional — skipped cleanly when the authored shapefile is absent.
MANUAL_SHP="inputs/mannual_connections/mannual_connections.shp"
if [ -f "$MANUAL_SHP" ]; then
  echo; echo "######## 3. prep manual connections (split by mode) ########"
  run_step "03_prep_manual_connections" "$PY" "$HERE/03_prep_manual_connections.py"
else
  echo "SKIP 03_prep_manual_connections: no $MANUAL_SHP (optional user layer)."
fi

echo; echo "######## 3-4. validate + build (mmnet 01->04 + reports) ########"
run_step "04_build_network" "$PY" "$HERE/04_build_network.py" "$PROFILE"

echo; echo "######## 5. verify the expected connected network ########"
run_step "05_verify_north_slope" "$PY" "$HERE/05_verify_north_slope.py"

echo; echo "######## 6. QGIS projects + components + figures ########"
run_step "viz/export_qgis" "$PY" "$HERE/viz/export_qgis.py"
if [ -f outputs/02_network_build/output/04_network_joined__nodes.gpkg ]; then
  run_step "viz/export_qgis (joined)" "$PY" "$HERE/viz/export_qgis.py" --stem 04_network_joined
fi
run_step "viz/export_qgis_components" "$PY" "$HERE/viz/export_qgis_components.py"
run_step "viz/plot_components" "$PY" "$HERE/viz/plot_components.py"
if [ -f outputs/02_network_build/output/04_network_joined__nodes.gpkg ]; then
  run_step "viz/plot_join" "$PY" "$HERE/viz/plot_join.py"
fi

echo; echo "######## 7. export the final_network/ handoff ########"
if [ "${EXPORT_FINAL_NETWORK:-0}" = "1" ]; then
  echo "EXPORT_FINAL_NETWORK=1 — regenerating the network-of-record."
  echo "  Together with these zips you MUST regenerate: the EXPECTED inventory in"
  echo "  source_scripts/fuel_network/load.py, edge_month_weights,"
  echo "  and edge_costs. See final_network/README.md."
  run_step "06_export_final_network" "$PY" "$HERE/06_export_final_network.py"
else
  echo "SKIPPED (default). Step 7 replaces the frozen network-of-record and"
  echo "  invalidates every edge_id-keyed table. To run it deliberately:"
  echo "    EXPORT_FINAL_NETWORK=1 bash workflows/02_network_build/run_all.sh"
fi

echo; echo "Done. Artifacts in outputs/02_network_build/{output,reports}."
