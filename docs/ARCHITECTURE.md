# mmnet — Architecture

`mmnet` builds a connected **multimodal spatial network** from a facility inventory and a set of
transport layers. It is **region-agnostic**: every region-specific value is DATA in one
`profile.yaml`; the package code never hard-codes a region, mode, path, or tolerance.

For the Python↔R file
contract see [`../mmnet/r_oracle/CONTRACT.md`](../mmnet/r_oracle/CONTRACT.md).

## The three pieces

```
  profile.yaml              mmnet/  (Python)                 r_oracle/  (R)
  ────────────              ──────────────────               ──────────────
  region as DATA      →     region-agnostic engine    ⇄      sfnetworks noder
  (paths, modes,            (orchestration + the              (the planar noding
   tolerances, the          gold connection logic)            that is hard in Python)
   snap/anchor rules)
```

- **profile.yaml** — the single source of truth. Inventory column map, CRS, modes, transport
  layers (each declares its own `mode`/`edge_label`/`snap_target`), tagging polygons, anchors and
  transfer rules, hub + topology tolerances. Change the model by editing this file.
- **mmnet package** — reads the profile and runs the pipeline. Pure Python (geopandas / shapely /
  networkx / pandas) plus a subprocess call to R for noding.
- **R oracle** (`r_oracle/build_network.R` + `lib.R`) — used **only** to node each mode's lines
  into an `sfnetwork`. Invoked over a self-contained file contract; no R project, no cache.

## Data flow

```
  data/raw/* ──(00_normalize_raw.py)──▶ data/interim/*   [uniform: EPSG:3338, canonical cols]
                                                  │
              02_prep_airways.py ─────────────────┤  derives airways.geojson, air_nodes.geojson,
              (geocode OD, dissolve boroughs)      │           data/boundary.geojson
                                                   ▼
  profile.yaml ─▶ run_pipeline()
        │
        ├─ 01  consolidate  facilities CSV ─▶ output/01_facilities.gpkg     steps/consolidate.py
        ├─ 01b tag          + place/region  ─▶ output/01b_tagged.gpkg        steps/tag.py
        ├─ 02  hubs          ─▶ classified  ─▶ output/02_hubs.gpkg           steps/hubs.py
        ├─ 03  build         R nodes ─▶ Python connects ─▶ output/03_network__{nodes,edges}.gpkg
        │                    build.py (node_layers_via_r) + assemble.py (connect_multimodal)
        │                                          │
        │   viz/{plot_network,export_qgis}.py ─────┴─▶ reports/figs/*.png, output/alaska_network.qgz
        └─ 04  join          join components ≤ max_dist to the giant ─▶ output/04_network_joined__*.gpkg
                             assemble.py (join_components_to_giant) · profile join_components.max_dist · 0 = off
```

## The pipeline stages

| Stage | Entry point | In → Out | What it does |
| --- | --- | --- | --- |
| **01 consolidate** | `steps.consolidate.consolidate_facilities` | inventory CSV → `01_facilities.gpkg` | read inventory, **optionally fill blank `delivery_method` from a community→mode fallback layer** (`fill_delivery_method`), scope to routable modes, reproject, dedup co-located tanks (complete-linkage at `dedup_tol_m`), union modes + max() capacity. A facility needs a mode + a capacity to be kept; a **blank inventory ID is not a drop reason** — it gets a deterministic synthetic id (`SYN-<cluster_id>`). |
| **01b tag** | `steps.tag.assign_community_region` (or `passthrough_tag`) | facilities → `01b_tagged.gpkg` | two-tier spatial join: facility → TIGER place, else borough/census area; inventory community is authoritative, then reconciled against the polygon into **`name_match`** (`agree` after canonical spelling normalization · `neighbor` same-borough mismatch kept · `conflict` cross-borough → **dropped** as a data error) |
| **02 hubs** | `steps.hubs.aggregate_hubs` | tagged → `02_hubs.gpkg` | one hub per `(community, city, region)` at the member centroid — **delivery methods unioned**, capacity summed (set `group_by` to add `delivery_method` for per-mode hubs); coincident centroids still merged; classify Supplier/Receiver |
| **03 build** | `build.build_network` | hubs + layers → `03_network__{nodes,edges}.gpkg` | **R nodes** road/ice/air; **Python nodes the waterway** + **connects** (snap hubs, anchor transfers, proximity bridges, connect-to-giant) |
| **04 join** (optional) | `assemble.join_components_to_giant` | `03_network` → `04_network_joined__{nodes,edges}.gpkg` | join every still-disconnected component to the giant by a straight `Join` connector when its nearest node is within `join_components.max_dist` (m), iterated until stable. Runs only when `max_dist > 0`; **does not change 03** |

`pipeline.run_pipeline(profile)` runs stages 01–03 (and 04 when enabled), then emits a **connectivity
report** via `inspect.connectivity_report` (per-mode + fuel-hub reachability) +
`inspect.mode_contribution("Air")` (the official flight data's marginal contribution) → printed headline
+ `reports/03_network.md`. When Stage 04 runs it writes a second report `reports/04_network_joined.md`.
`run_pipeline` **returns the canonical 03 `NetworkTables`**; the joined network is the on-disk
`04_network_joined` deliverable.

## Stage 03 — the R↔Python seam (no redundancy)

R and Python each do their half once:

1. **`build.node_layers_via_r(layers)`** writes a *lean* contract (the line layers + a minimal
   registry/params) and runs `build_network.R --node-only`. R reuses `lib.R::clean_subnetwork`
   per mode (`st_union → st_node → to_spatial_subdivision → to_spatial_smooth`) and returns the
   noded edges (geometry + `type`). R does **not** aggregate hubs, blend, build transfers, or join.
2. **`assemble.connect_multimodal(...)`** takes those noded edges and connects them, fast and once:
   - derive the global node table from edge endpoints (no `unary_union` re-noding);
   - **node the full waterway in Python** — the marine network skips R (its spines are already a clean
     graph) and is noded by rounding vertices to 50 m, its node ids offset past the land nodes;
   - **snap each hub to the nearest ground node** — `snap_types` = the profile's `snap_target`
     layers (Road ∪ Ice Road); records a `snap_surface` per hub;
   - **anchor transfers** (`sjoin_nearest`): a `Transfer` edge where an anchor is within `max_dist` of
     both modes' nodes — barge↔road **and** barge↔ice at ports + barge hubs (airports instead **snap** onto
     the road — `build._snap_airways_to_road`, a shared node, not a transfer edge);
   - **proximity bridges** (`connect_extras`): the before-policies — road↔road / ice↔ice welds
     (within-mode) and the ice↔road bridge (cross-mode), each added when the gap ≤ the rule's `max_dist`;
   - **connect-to-giant** (`connect_extras.connect_to_giant`): a final shore-landing pass that joins
     every still-disconnected **surface** piece (road ∪ ice ∪ waterway — air excluded, bulk fuel moves
     over the surface) to the giant within `connect_to_giant.max_dist` — a coastal barge landing
     (`shore:Barge↔*`) where it meets the waterway, else a noding weld (`weld:to-giant`). This is what
     joins the North Slope at its ~210 m barge landing;
   - label connected components. A piece beyond every policy's reach stays isolated rather than joined
     by a fabricated long edge.

R's whole job is the node-only noder (`build_network.R --node-only` → `lib.R::clean_subnetwork`);
Python owns every connection. There is no other R path.

## Module responsibilities

| Module | Responsibility |
| --- | --- |
| `config.py` | Typed profile schema (`RegionProfile` → `PipelineConfig`/`Params`); load + validate |
| `io_readers.py` | Read + clean inputs (`read_facilities_raw`, `_read_lines`, `load_roads/waterways/airways/places/regions`) |
| `io_writers.py` | Write artifacts (`write_gdf`, `output_dir`, `out_path`) |
| `steps/consolidate.py` | Stage 01 — dedup the inventory |
| `steps/tag.py` | Stage 01b — community/region tagging |
| `steps/hubs.py` | Stage 02 — aggregate + classify hubs |
| `build.py` | Stage 03 driver — node-only R contract + connect; `_load_line_layer`, `_load_anchor`, `_resolve_anchor` (incl. the `barge_hubs` virtual anchor) |
| `assemble.py` | The Python connector (`connect_multimodal` — waterway noding, transfers, bridges, connect-to-giant); `join_components_to_giant` (Stage 04); `snap_to_roads` |
| `connect_extras.py` | Proximity policies + shore-landing pass: `within_mode_connectors`, `cross_mode_connectors`, `connect_to_giant` |
| `network.py` | `NetworkTables` (nodes+edges ⇄ networkx ⇄ GeoPackage) |
| `inspect.py` | Evaluation layer: `describe_output`, `diff_columns`, step reports; **`connectivity_report`** (components, giant, per-mode + fuel-hub reachability), **`mode_contribution`** (a mode's with/without marginal contribution), `write_network_report` |
| `viz.py` | `plot_before_after`, `plot_hubs`, `plot_network` (map layer) |
| `pipeline.py` | `run_pipeline` — wires the four stages |
| `r_oracle/` | The R noder + the file contract (see CONTRACT.md) |

## Extend by editing the profile (no engine change)

- **Add a transport mode** — add a `layers:` entry with its own `mode`/`edge_label`/`source`. The
  build derives modes from the layer registry (this is how *Ice Road* was added).
- **Let hubs sit on a surface** — set `snap_target: true` on a layer (Road and Ice Road use this).
- **Add an intermodal link** — add an `anchors:` point layer + a `transfers:` rule
  (`from_mode`/`to_mode`/`anchor`/`max_dist`). Use the `barge_hubs` virtual anchor to transfer at the
  barge-served Stage-02 hubs (no file needed).
- **Add a proximity policy** — add a `bridges:` rule (`from_mode`/`to_mode`/`max_dist`): same mode is a
  within-mode weld, distinct modes a cross-mode bridge.
- **Pull in coastal near-misses** — set `connect_to_giant.max_dist` (meters) to join every still-isolated
  surface piece to the giant where it is that close (a barge shore landing where road meets sea).
- **Join leftover components by distance (Stage 04)** — set `join_components.max_dist` (meters) to join
  every remaining non-giant component (any mode) to the giant when its nearest node is within reach. The
  join is iterated until stable and written to a separate `04_network_joined` (03 stays canonical); `0`
  disables it. A large cap collapses the network to a single component.
- **Recover blank delivery modes** — add `inventory.delivery_method_fallback` (a community→mode
  point layer + `community_col`/`method_col`/`max_dist_m`); Stage 01 then fills facilities whose
  inventory mode is blank by community name, else by the nearest marker within `max_dist_m`.
- **Tune the build** — edit `hubs:` / `topology:` tolerances.

## Reproducible scripts (`workflows/02_network_build/`)

`00_normalize_raw.py` (raw → `data/interim/`), `01_prep_waterway.py` (full-Alaska NWN extraction —
required before the build), `02_prep_airways.py` (geocode OD → airways/air_nodes + boundary),
`04_build_network.py` (validate + run_pipeline), `05_verify_north_slope.py` (assertion gate),
`06_export_final_network.py` (the frozen handoff), `viz/plot_network.py` (static PNG),
`viz/export_qgis.py` (styled `.qgz` + GeoPackage). Typical order:
`00 → 01 → 02 → 04 → 05 → 06`.

### Air data (the official sources)

The air mode's tracked inputs are `inputs/air/flight_paths_combined.csv` (OD flight legs) and
`inputs/air/airports_ak_dotpf.csv` (the AK DOT&PF registry). `00_normalize_raw.py` copies them
into the interim layer under their legacy names (`air_flight_paths_od.csv`, `airports.csv`),
which is what `02_prep_airways.py` reads — the old report-extracted OD table and the global
OurAirports dump are retired (`extract_od_table.py` was deleted in the merge). Engine artifacts
land under `outputs/02_network_build/` (the mmnet project dir), so `output/...` paths in the
diagram above are relative to it.
