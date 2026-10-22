# DATA DICTIONARY — what every field means

Field meanings and units for the products a downstream user reads. Producers and
consumers are covered in `DATA_CONTRACTS.md`; this page covers what the values mean.
Counts and value lists describe the current network-of-record (2026-10-15; see
`CHANGELOG.md`).

**Conventions.** Every coordinate is in EPSG:3338 (NAD83 / Alaska Albers), in
meters, unless a column says degrees. Money is in USD (2026 dollars), always
**per gallon of fuel moved**. Friction is a dimensionless multiplier with a
baseline of 1.0. Months are 1–12 (January = 1).

## 1. Network nodes

`final_network/network_joined_nodes.zip` (shapefile) and the DuckDB table
`network_nodes`. There is one row per graph node (84,094).

| Field | Type | Unit / values | Meaning |
|---|---|---|---|
| `node_id` | integer | 0-based | Node id; edges reference it in `from` / `to` (`from_node` / `to_node` in DuckDB) |
| `is_hub` | boolean | 0/1 | A fuel hub is placed on this node |
| `hub_id` | text | `Hub_<n>`; `Hub_a+Hub_b` when two hubs share a node | Hub identifier; join key to `hub_members` / `hub_snaps`. Empty when not a hub |
| `deliv_meth` | text | Road · Barge · Plane, or combinations like `Barge or Road` | The hub's delivery mode(s): the union over its member facilities (shapefile name for `delivery_method`) |
| `hub_type` | text | Supplier · Receiver | Supplier if the hub's capacity is at or above the 90th percentile among hubs with the same delivery method (profile `hubs.percentile`), else Receiver |
| `hub_cap` | number | gallons | Total fuel storage capacity at the hub: the sum over member sites of the inventory `total_capacity` (text in the DBF, numeric in DuckDB) |
| `snap_surf` | text | Road · IceRoad · Waterway · Air+Road | The network surface the hub was snapped to (shapefile name for `snap_surface`) |
| `component` | integer | 1 = the giant | Connected-component id |
| `is_giant` | boolean | 0/1 | The node is in the giant component (99.99% of nodes) |
| `x`, `y` | number | m (EPSG:3338) | Node position (DuckDB only; the shapefile carries it as geometry) |

## 2. Network edges

`final_network/network_joined_edges.zip` (shapefile) and the DuckDB table
`network_edges`. There is one row per graph edge (93,049).

| Field | Type | Unit / values | Meaning |
|---|---|---|---|
| `edge_id` | integer | 0-based | **The shapefile's row order** (DuckDB only; derived at ingest and nowhere else). Every edge-keyed table joins on it. See `DATA_CONTRACTS.md` §5 |
| `from` / `from_node`, `to` / `to_node` | integer | `node_id` | Edge endpoints. The graph is undirected and may have parallel edges, so load it as a `MultiGraph` |
| `type` | text | see the vocabulary below | What the edge is |
| `edge_class` | text | same vocabulary | Costing class (DuckDB only). Mirrors `type`; it differs only for a legacy export's generic `Bridge` |
| `source` | text | e.g. `Road`, `ports`, `barge_hubs`, `weld:*`, `bridge:*`, `shore:*`, `join:to-giant` | Provenance: which layer or connection rule created the edge |
| `join_gap_m` | number | m | For stage-04 join connectors, the straight-line gap that was closed; NULL or 0 otherwise |
| `length_m` | number | m | Geometric length (DuckDB only; derived from the EPSG:3338 geometry) |

**Edge-type vocabulary.** Line-haul edges: `Road`, `Waterway` (barge), `Air`,
`IceRoad` (seasonal, January–March only). Synthetic connectors are named by the
modes they join. Same-mode connectors are `{Mode}Connector` (`RoadConnector`,
`IceRoadConnector`); mode-to-mode handoffs are per-pair `{A}{B}Transfer`
(`BargeRoadTransfer`, `BargeIceRoadTransfer`, `IceRoadRoadTransfer`,
`AirRoadTransfer`, `BargeAirTransfer`). Current counts are in `final_network/README.md`.

## 3. Hub handoff

`final_network/hub_members.csv` and `hub_snaps.csv`, loaded into DuckDB as
`hub_members` and `hub_snaps`.

**`hub_members`** has one row per (hub, raw inventory record).

| Field | Unit / values | Meaning |
|---|---|---|
| `hub_id` | as in `network_nodes.hub_id` | The hub |
| `hub_key` | upper-case key | Workflow 00's `community_key`, the canonical community the hub was built for |
| `hub_community` | text | Display label of that community |
| `hub_kind` | community · remote_site · blob | `community`: grouped by label. `remote_site`: a site farther than `remote_site_km` from its labelled community, kept as its own hub. `blob`: unlabelled sites grouped by distance |
| `delivery_method`, `hub_type` | as on the node | Copied from the hub |
| `ast_facility_id` | AEA id, or `SYN-<cluster>` | The member site |
| `record_id` | AEA GlobalID | The raw inventory record. Join key to the clean facility table (§6) |
| `node_id` | `node_id`; empty if unplaced | Where the hub landed |
| `snap_status` | placed · merged:`<hub>` · unplaced:beyond_cap | Placement outcome |

**`hub_snaps`** has one row per hub (placed, merged or unplaced).

| Field | Unit / values | Meaning |
|---|---|---|
| `hub_id` | | The hub |
| `node_id` | `node_id`; empty if unplaced | The node it was snapped to |
| `snap_dist_m` | m | Distance from the hub centroid to that node |
| `snap_surface` | Road · IceRoad · Waterway · Air+Road | Surface snapped to |
| `status` | placed · merged:`<hub>` · unplaced:`<reason>` | Placement outcome |

## 4. Monthly friction weights — `edge_month_weights`

One row per (edge, month): 93,049 × 12.

| Field | Type | Unit / values | Meaning |
|---|---|---|---|
| `edge_id` | integer | | The edge |
| `month` | integer | 1–12 | Calendar month |
| `mode` | text | Road · Barge · Plane · IceRoad · Transfer | The rate mode the edge is costed at |
| `avg_friction` | number | dimensionless, ≥ 1.0 | Length-weighted mean environmental friction along the edge, sampled every 75 m. Road and IceRoad edges sample `road_base.tif` (IceRoad multiplied by 2.0 as a seasonal time penalty); Waterway edges sample that month's `barge_MM.tif`; connectors, transfers and Air are a flat 1.0 |
| `nodata_frac` | number | 0–1 (fraction of length) | Share of the edge's length whose samples hit NoData (blocked) |
| `passable` | boolean | | Usable this month: `nodata_frac` = 0 **and**, for IceRoad and IceRoadConnector, the month is January–March. One NoData sample makes an edge impassable (a deliberate rule) |

## 5. Monthly costs — `edge_costs`

One row per (edge, month): 93,049 × 12.

| Field | Type | Unit | Meaning |
|---|---|---|---|
| `edge_id`, `month` | integer | | As above |
| `cost_per_gallon` | number | USD per gallon (2026$) | Cost to move one gallon across this edge in this month. **Line-haul:** `(length_m / 1609.344) × avg_friction × rate[mode]`, where `rate` is in USD per gallon-mile. **Transfer:** the flat per-gallon fee for the mode pair, regardless of distance. May be NULL only when `passable` is false |
| `passable` | boolean | | Copied from `edge_month_weights` (transfers are always passable) |

Rates and fees live only in `source_scripts/friction_surface/friction_costs.py`
(`BASELINE_RATES_PER_GALLON_MILE`, `INTERMODAL_TRANSFER_FEES`). The cost of a route
is the sum of `cost_per_gallon` over its passable edges for that month.

## 6. Clean facility table — `facilities_clean.csv`

`outputs/00_inventory_qc/<release>/facilities_clean.csv` has one row per kept
inventory record. The authoritative definitions are machine-checked config, so
they are not repeated here:

- `inputs/inventory_qc/facility_schema.csv` — every schema column, with its type,
  unit (degrees, m, gallons) and description;
- `inputs/inventory_qc/derived_columns.csv` — every column workflow 00 adds
  (`community_key`, `delivery_*`, `community_distance_km`, `located_in_place`,
  `community_relation`, `corrections_applied`, `qc_release`, `qc_status`).
  Workflow 00's publish step fails on any column that isn't declared there.

Key reading rules: `community_name` is the **service** community and is never
relabelled; `located_in_place` is where the point physically sits; and
`community_relation` summarises the two. `latitude` / `longitude` are EPSG:4326
degrees; capacities are gallons. Records with `qc_status = pending_review` can be
withheld from hubs by the network build.

## 7. Friction rasters

`outputs/01_friction_build/friction_stack/` holds 14 files on the canonical 150 m
grid (`DATA_CONTRACTS.md` §1–2).

| File | Value | Meaning |
|---|---|---|
| `overland.tif` | dimensionless, ≥ 1.0; NoData on water | Off-road terrain friction: slope class × land cover × permafrost |
| `road_base.tif` | dimensionless, ≥ 1.0; no NoData | Friction for land edges: max(1.0, slope friction) × permafrost |
| `barge_01..12.tif` | 1.0 where navigable; NoData where blocked | Monthly navigability: water (or the waterway corridor) and not ice-covered (sea or river ice > 15%) |

Friction is environmental only; dollars enter in `edge_costs` and nowhere else.
Every friction constant lives in `source_scripts/friction_surface/friction_config.py`.
