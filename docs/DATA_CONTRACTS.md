# DATA CONTRACTS — every inter-stage agreement on one page

The pipeline is four workflows connected by intermediate data artifacts. Each contract
below names its producer, its consumer(s), and what breaks if it drifts.

## 1. The canonical 150 m grid (all rasters)

| Property | Value |
|---|---|
| CRS | EPSG:3338 (NAD83 / Alaska Albers, meters) |
| Resolution | 150 m |
| Dimensions | 28,000 × 16,567 |
| Anchor | `inputs/friction_rasters/lulc.tif` — every other raster must match its CRS, transform, and shape exactly |

Producer: the GEE export + arcpy preprocessing. Consumers: everything in
workflow 01. Enforced by `friction_preflight` (auto-run inside
`write_friction_stack`) and `check_grid_exports.py`; the `align-to-ak-stack`
skill snaps new rasters onto it. Drift ⇒ preflight FATAL, no build.

## 2. The friction stack (workflow 01 → workflow 03)

`outputs/01_friction_build/friction_stack/` — **14 physical files backing 24
logical (mode, month) surfaces**:

| File(s) | Semantics |
|---|---|
| `overland.tif` | Static terrain surface: slope-class × LULC × permafrost; water = NoData |
| `road_base.tif` | Static, **NoData-free** land-edge surface: max(1.0, slope friction) × permafrost |
| `barge_01..12.tif` | Monthly barge navigability: `(lulc_water ∨ waterway_mask) ∧ ¬(sea_ice>0.15 ∨ river_ice>0.15)`; friction 1.0, blocked = NoData |

Precondition: the waterway corridor mask
(`outputs/01_friction_build/waterway_mask_150m.tif`, built by
`01_build_corridor_masks.py`) must exist before the stack build — a
missing mask is a HARD ERROR (a maskless build severs ~18% of waterway
edges; the explicit synthetic-run opt-out is `require_waterway_mask=False`
/ `FRICTION_ALLOW_MISSING_WATERWAY_MASK=1`).
Consumer: `03_weight_network_edges.py`. QA gate: `03_qa_friction_stack.py`
(14-file contract, ice-gating direction, value floor).

## 3. The R WORKDIR contract (inside workflow 02)

`mmnet.build.node_layers_via_r` writes a temp WORKDIR — `layers/*.gpkg` +
`params.json` + `registry.json` — and runs `r_oracle/build_network.R
--node-only` (st_union → st_node → subdivision → smooth, per mode: road /
ice / air only; the waterway is noded in Python at 50 m rounding).
`CONTRACT_VERSION` in `source_scripts/mmnet/build.py` must equal the version in
`source_scripts/mmnet/r_oracle/build_network.R`; full spec in
`source_scripts/mmnet/r_oracle/CONTRACT.md`. Drift ⇒ hard error at build.

## 4. The final_network handoff (workflow 02 → workflow 03)

Producer: `06_export_final_network.py` (zips + sha256 manifest + the hub handoff
`hub_members.csv` / `hub_snaps.csv` via `mmnet.handoff`). Consumers:
`01_extract_network_handoff.py` → `02_load_final_network.py`.

The hub handoff (2026-10): `hub_members.csv` has one row per (hub, raw inventory
record) — `hub_id`, `hub_key`, `hub_community`, `hub_kind`, `delivery_method`,
`hub_type`, `ast_facility_id`, `record_id`, `node_id`, `snap_status`; `hub_snaps.csv`
is stage 03's placement trail (`hub_id`, `node_id`, `snap_dist_m`, `snap_surface`,
`status`). Both are listed in `final_network/MANIFEST.sha256`. A consumer takes hub
membership and a hub's community from these files, never by re-inference.

Schema (DBF-safe field names; meanings + units in `docs/DATA_DICTIONARY.md`):
see `final_network/README.md` — nodes
(node_id, is_hub, hub_id, deliv_meth, hub_type, hub_cap, snap_surf,
component, is_giant; Point, EPSG:3338), edges (from, to, type ∈ {Road,
Waterway, Air, IceRoad, RoadConnector, IceRoadConnector, BargeRoadTransfer,
BargeIceRoadTransfer, IceRoadRoadTransfer, AirRoadTransfer, BargeAirTransfer},
source, join_gap_m;
LineString, EPSG:3338). `length_m` is DERIVED by the consumer
(geometry.length — EPSG:3338 is meters).

Inventory (the ingest's hard tripwire, `EXPECTED` in
`02_load_final_network.py`): 84,094 nodes / 93,049 edges / 329 hubs / 4
components / giant 0.9999 / Road 55,539 · Waterway 34,178 · Air 226 ·
IceRoad 1,248 · RoadConnector 1,498 · IceRoadConnector 34 ·
BargeRoadTransfer 289 · BargeIceRoadTransfer 21 · IceRoadRoadTransfer 12 ·
AirRoadTransfer 2 · BargeAirTransfer 2.

## 5. THE edge_id RULE (the contract everything hangs on)

**`edge_id` = 0-based row order of
`final_network/network_joined_edges/network_joined_edges.shp`.**

Created at ingest (`02_load_final_network.py`) and consumed by
`03_weight_network_edges.py` (which reads `edge_class` back from the DB, so
the rule lives in exactly one place). Every DuckDB table joins on it. The
shapefile bytes are therefore checksummed (`inputs/MANIFEST.md`,
`final_network/README.md`) and preserved byte-identical; the cross-check at
ingest verifies the id *range* of any pre-existing `edge_month_weights`, not
content — so never mix tables from different exports.

## 6. Connector vocabulary + edge_class (stage 02 of workflow 03)

Synthetic connectors are named by the modes they join
(`pipeline.classify_connectors`): within-mode welds → `{Mode}Connector`
(RoadConnector, IceRoadConnector); cross-mode handoffs → per-pair
`{A}{B}Transfer` (BargeRoadTransfer, BargeIceRoadTransfer, IceRoadRoadTransfer,
AirRoadTransfer, BargeAirTransfer). `edge_class` is a pass-through of this `type`; it only diverges
for a LEGACY frozen network, mapping generic `Bridge` welds into the vocabulary
(ice-road provenance → IceRoadConnector, else → RoadConnector). Persisted on
`network_edges`; **no other code may re-derive this rule.**

## 7. Weighting semantics (workflow 03, stage 03)

75 m densification; length-weighted mean friction over valid samples;
**strict rule: ANY NoData sample ⇒ impassable that month** (nodata_frac
logged); IceRoad (and IceRoadConnector) hard-gated to months {1,2,3} with the
×2.0 time penalty; RoadConnector / *Transfer / Air unsampled at flat 1.0.
Friction-vs-cost separation: this stage writes environmental multipliers
only — dollars enter exclusively in stage 04 via
`friction_surface.friction_costs` (BASELINE_RATES_PER_GALLON_MILE,
INTERMODAL_TRANSFER_FEES; each per-pair `*Transfer` maps straight to its fee
via `TRANSFER_TYPE_TO_MODES`).

## 8. The DuckDB deliverable (`outputs/fuel_network.duckdb`)

| Table | Rows | Columns | Writer |
|---|---|---|---|
| `network_nodes` | 84,094 | node_id PK, is_hub, hub_id, deliv_meth, hub_type, hub_cap, snap_surf, component, is_giant, x, y | 03/02_load |
| `network_edges` | 93,049 | edge_id PK, from_node, to_node, type, edge_class, source, join_gap_m, length_m | 03/02_load |
| `edge_month_weights` | 1,116,588 | edge_id, month, mode, avg_friction, nodata_frac, passable | 03/03_weight |
| `edge_costs` | 1,116,588 | edge_id, month, cost_per_gallon, passable | 03/04_assemble |
| `hub_members` | one per (hub, raw record) | hub_id, hub_key, hub_community, hub_kind, delivery_method, hub_type, ast_facility_id, record_id, node_id, snap_status | 03/02_load from `final_network/hub_members.csv` (when present) |
| `hub_snaps` | one per hub | hub_id, node_id, snap_dist_m, snap_surface, status | 03/02_load from `final_network/hub_snaps.csv` (when present) |

Row counts are those for the 2026-10-15 network-of-record (93,049 edges × 12
months). The weighted tables were not regenerated with that export: any
`edge_month_weights` / `edge_costs` still on disk from before it hold the
2026-09 network's 1,115,736 rows (92,978 × 12). Rerun workflow 03 in full, and
never join tables from different exports.

`hub_members` is the writer the old "`hub_facility_map` — documented future
work" note waited for: hub ↔ inventory record membership comes from stage 02's
build itself (`mmnet.handoff`), keyed by workflow 00's `record_id`, so a
downstream facility table joins on `record_id`. The routing layer's
`backfill_facility_edges` stub can now be built on it. Exports before 2026-10
carry neither table.

## 9. Config surfaces (one per concern)

| Surface | Owns |
|---|---|
| `workflows/02_network_build/profile.yaml` | Every region-specific network choice (modes, layers, anchors, transfer/snap/bridge tolerances, hub rules, join cap, seed) — THE single copy |
| `source_scripts/friction_surface/friction_config.py` | Every friction constant (grid, thresholds, seasons, multipliers) |
| `source_scripts/friction_surface/friction_costs.py` | Every dollar (rates, fees, fee inference) — audited by the `derive-fuel-costs` skill |

They are deliberately not merged: network topology knobs and friction
constants serve different stages.
