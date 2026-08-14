# DATA CONTRACTS — every inter-stage agreement on one page

The pipeline is four workflows connected by data artifacts. Each contract
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
| `road_base.tif` | Static, **NoData-free** land-edge surface: max(1.0, slope friction) × permafrost — a land edge can never be accidentally severed |
| `barge_01..12.tif` | Monthly barge navigability: `(lulc_water ∨ waterway_mask) ∧ ¬(sea_ice>0.15 ∨ river_ice>0.15)`; friction 1.0, blocked = NoData |

Precondition: the waterway corridor mask
(`outputs/01_friction_build/waterway_mask_150m.tif`, built by
`01_build_corridor_masks.py`) must exist before the stack build — a
missing mask is a HARD ERROR (a maskless build severs ~18% of waterway
edges; the explicit synthetic-run opt-out is `require_waterway_mask=False`
/ `FRICTION_ALLOW_MISSING_WATERWAY_MASK=1`).
Consumer: `03_weight_network_edges.py`. QA gate: `03_qa_friction_stack.py`
(14-file contract, ice-gating direction, value floor).

## 3. The R WORKDIR contract (inside workflow 02, contract_version "2")

`mmnet.build.node_layers_via_r` writes a temp WORKDIR — `layers/*.gpkg` +
`params.json` + `registry.json` — and runs `r_oracle/build_network.R
--node-only` (st_union → st_node → subdivision → smooth, per mode: road /
ice / air only; the waterway is noded in Python at 50 m rounding).
`CONTRACT_VERSION` in `source_scripts/mmnet/build.py` must equal the version in
`source_scripts/mmnet/r_oracle/build_network.R`; full spec in
`source_scripts/mmnet/r_oracle/CONTRACT.md`. Drift ⇒ hard error at build.

## 4. The final_network handoff (workflow 02 → workflow 03)

Producer: `06_export_final_network.py` (zips + sha256 manifest). Consumers:
`01_extract_network_handoff.py` → `02_load_final_network.py`.

Schema (DBF-safe field names): see `final_network/README.md` — nodes
(node_id, is_hub, hub_id, deliv_meth, hub_type, hub_cap, snap_surf,
component, is_giant; Point, EPSG:3338), edges (from, to, type ∈ {Road,
Waterway, Air, IceRoad, Transfer, Bridge, Join}, source, join_gap_m;
LineString, EPSG:3338). `length_m` is DERIVED by the consumer
(geometry.length — EPSG:3338 is meters).

Frozen inventory (the ingest's hard tripwire, `EXPECTED` in
`02_load_final_network.py`): 82,300 nodes / 90,921 edges / 384 hubs / 21
components / giant 0.9965 / Road 53,795 · Waterway 34,099 · Bridge 1,367 ·
IceRoad 1,248 · Transfer 213 · Air 154 · Join 45.

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

## 6. edge_class (derived once, stage 02 of workflow 03)

The exporter's `Bridge` type means an mmnet topology **weld**, not a
road-over-water bridge. `derive_edge_class` splits it by provenance:
`weld:IceRoad` / `bridge:IceRoad->Road` → `IceRoadConnector` (seasonal,
IceRoad treatment: road_base sampling × 2.0 penalty, Jan–Mar gate); other
`Bridge` → `Weld` (flat 1.0, Road rate); all other types pass through.
Persisted on `network_edges`; **no other code may re-derive this rule.**
Rebuilds emit `IceRoadConnector` as the `type` itself (the profile's
ice-road bridge rules carry `edge_type: IceRoadConnector`), so the frozen
and rebuilt vocabularies are identical.

## 7. Weighting semantics (workflow 03, stage 03)

75 m densification; length-weighted mean friction over valid samples;
**strict rule: ANY NoData sample ⇒ impassable that month** (nodata_frac
logged); IceRoad (and IceRoadConnector) hard-gated to months {1,2,3} with the
×2.0 time penalty; Bridge/Air/Transfer unsampled at flat 1.0.
Friction-vs-cost separation: this stage writes environmental multipliers
only — dollars enter exclusively in stage 04 via
`friction_surface.friction_costs` (BASELINE_RATES_PER_GALLON_MILE,
INTERMODAL_TRANSFER_FEES; Transfer edges priced by incident-mode inference,
ambiguity = hard error).

## 8. The DuckDB deliverable (`outputs/fuel_network.duckdb`)

| Table | Rows | Columns | Writer |
|---|---|---|---|
| `network_nodes` | 82,300 | node_id PK, is_hub, hub_id, deliv_meth, hub_type, hub_cap, snap_surf, component, is_giant, x, y | 03/02_load |
| `network_edges` | 90,921 | edge_id PK, from_node, to_node, type, edge_class, source, join_gap_m, length_m | 03/02_load |
| `edge_month_weights` | 1,091,052 | edge_id, month, mode, avg_friction, nodata_frac, passable | 03/03_weight |
| `edge_costs` | 1,091,052 | edge_id, month, cost_per_gallon, passable | 03/04_assemble |

`hub_facility_map` (hub_id ↔ facility_id) is **documented future work**: the
routing layer's `backfill_facility_edges` stub depends on it, and no writer
or source data exists in this repository (see
`workflows/04_duckdb_export/README.md`).

## 9. Config surfaces (one per concern)

| Surface | Owns |
|---|---|
| `workflows/02_network_build/profile.yaml` | Every region-specific network choice (modes, layers, anchors, transfer/snap/bridge tolerances, hub rules, join cap, seed) — THE single copy |
| `source_scripts/friction_surface/friction_config.py` | Every friction constant (grid, thresholds, seasons, multipliers) |
| `source_scripts/friction_surface/friction_costs.py` | Every dollar (rates, fees, fee inference) — audited by the `derive-fuel-costs` skill |

They are deliberately not merged: network topology knobs and friction
constants serve different stages.
