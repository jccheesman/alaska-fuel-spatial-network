# CLAUDE.md — lab notebook

House rules for working in this repo: never commit or push without the owner
asking; move-only commits separate from edit commits; every dollar lives in
`friction_costs.py` and every friction constant in `friction_config.py`;
`final_network` zip members stay byte-identical (edge_id contract);
`data/`, `outputs/01_*`, `outputs/02_*`, extracted `final_network/*/` are
regenerable working trees — never hand-edit them; `outputs/00_inventory_qc/*/facilities_clean.csv`
is tracked but regenerated only by workflow 00 (edit `inputs/inventory_qc/corrections.csv`, never
the table); the raw AEA inventory CSV (contact fields) is never committed.

## Run-script conventions

All five drivers (`run_all.sh` + the four stage ones) source
`workflows/_lib.sh`. Three rules, and they are contracts CI checks:

- **`resolve_python`** picks the interpreter — active `$VIRTUAL_ENV`, then
  `.venv/bin/python`, then `python3` with a warning. Never call bare `python3`
  in a driver again.
- **`run_step LABEL CMD…`** filters known-noisy output but preserves the exit
  status and aborts the stage on failure. Never `cmd | grep … || true`; that is
  the bug this replaced.
- **`gate MSG…`** exits `GATE_EXIT` (3) = "documented input absent, skip".
  Any other non-zero exit means a real failure. The top-level `run_all.sh`
  reports the two separately and exits non-zero only for the second.

Stage 02's export step is opt-in (`EXPORT_FINAL_NETWORK=1`) because it
replaces the network-of-record.

## Pipeline table

| Script | Does | Outputs | Knobs | Finding |
|---|---|---|---|---|
| `tools/extract_inputs.py` | Unzips committed inputs (incl. `inputs/raw_facility_data/2022/bulk_fuel_data.zip`) into gitignored working dirs | `inputs/{bulk_fuel_data,data_for_network_build,region_and_census_data}/`, `data/raw/` | — | One gate for workflows 01–02; fixes the fresh-clone story both old repos lacked |
| **00_inventory_qc** | | | | |
| `01_ingest.py` | Raw AEA release → clean-schema snapshot under `inputs/raw_facility_data/<release>/` + diff vs previous release | release folder (tracked; raw CSV never) | `inputs/inventory_qc/facility_schema.csv`, `sources/<src>/column_map.csv` | Contact columns are never read; `--check` re-derives committed snapshots. 2025 release = base |
| `02_apply_corrections.py` | Owner-approved rows of `corrections.csv`, `old_value`-guarded | `outputs/00_inventory_qc/<rel>/facilities_corrected.csv`, `excluded.csv`, `corrections_log.csv` | `inputs/inventory_qc/corrections.csv` | Only `approved` rows apply; an exclusion carries a reason; a stale row fails the stage (retire it, don't force it) |
| `03_normalise.py` | community_key (canonical + `aliases.csv`), delivery flags | `facilities_normalised.csv`, `name_report.csv` | `inputs/inventory_qc/aliases.csv` | Runs AFTER corrections so an alias can never move a correction's target |
| `04_detect.py` | Detector registry (shared farm ids, copies, shared points, typos, map point vs lat/lon, …) | `flags_structural.csv`, `detectors_run.csv` | `inputs/inventory_qc/thresholds.csv` | Each detector declares its needed columns and skips itself otherwise; see `docs/inventory_notes/` |
| `05_boundary_check.py` | Label vs DCRA city + CDP boundary — verify only | `flags_boundary.csv`, `boundary_distance.csv`, `boundary_summary.csv` | `thresholds.csv`, `remote_sites.csv`, `inputs/inventory_qc/boundaries/` | Never relabels; communities without a boundary are untested and kept (no borough layer, owner 2026-10-06). **`outside` (inside no boundary at all) is info, never reviewed** (owner 2026-10-08: that is what a remote Alaskan site looks like); only `mismatch` (inside ANOTHER community) is reviewable. The km to the own boundary is published as `community_distance_km` for the hub builder's `remote_site_km` rule |
| `06_review_queue.py` | Open flags → owner review sheet | `review_queue.csv` (+`.xlsx`) | — | Decisions come back through `record-facility-corrections` |
| `07_publish.py` | The clean facility table + QC report, after the output-contract checks | `facilities_clean.csv` (tracked), `qc_report.md` | — | Row reconciliation, reviewer+date, schema-only columns, regression fixtures, determinism — never loosen one |
| **01_friction_build** | | | | |
| `00_preflight_inputs.py` | Grid + range gates on the friction rasters | pass/fail report | RASTER_DIR env | Every input must match `lulc.tif`'s 28,000×16,567 grid exactly |
| `01_build_corridor_masks.py` | Rasterizes the waterway network (75 m buffer, all_touched) | `outputs/01_friction_build/waterway_mask_150m.tif` | `CORRIDOR_BUFFER_M` | **REQUIRED before stage 02** — a missing mask is a hard error in the stack build (maskless = ~18% of waterway edges severed; explicit opt-out for synthetic runs only) |
| `02_build_friction_stack.py` | overland + road_base + barge_01..12 | `outputs/01_friction_build/friction_stack/` (14 TIFs / 24 logical surfaces) | `friction_config.py` | road_base is NoData-free by construction so land edges can't be accidentally severed |
| `03_qa_friction_stack.py` | Hard post-build gates | exit code | — | Checks the 14-file contract, Jul>Jan barge pixels (ice gating direction), value floor |
| **02_network_build** | | | | |
| `00_normalize_raw.py` | data/raw → uniform EPSG:3338 interim layer + MANIFEST; the **facilities** entry reads workflow 00's published `facilities_clean.csv` (latest release), never the raw AEA CSV | `data/interim/` | its SPEC table | The SPEC table is de-facto config: one entry per raw file, incl. the official air-data swap. `inventory.record_id` in the profile makes consolidation write `output/01_site_members.csv` (site ↔ raw record) |
| `01_prep_waterway.py` | Full-Alaska NWN extraction | `data/interim/ak_waterway.gpkg` | `NODE_TOL=50` (matches assembler rounding) | Replaced the old facility-bbox clip — ~316 lines / ~31,903 km marine network |
| `02_prep_airways.py` | Geocode OD legs | `data/processed/{airways,air_nodes}.geojson`, `data/boundary.geojson` | — | Interim files keep legacy names (`air_flight_paths_od.csv`) though sources are the official AK DOT&PF data — don't "fix" one without the other |
| `03_fetch_basemap.py` | Natural Earth downloads | `data/basemap/` | — | Figures only |
| `03_prep_manual_connections.py` | Split the user-authored `mannual_connections.shp` by its `Mode` tag | `data/interim/manual_<mode>.gpkg` | source shp under `inputs/mannual_connections/` (opted-in like `inputs/air/`) | User-extensible layer: hand-draw a line, tag its Mode, rebuild. One mode per layer (engine drops per-feature attrs), so a mixed-mode file must be split; each split reuses the mode's existing edge_label so costing is unchanged. Endpoints snapped to existing nodes weld automatically (1 m) — no connection rule needed |
| `04_build_network.py` | validate_profile + mmnet stages 01→04 | `outputs/02_network_build/{output,reports}` (+ trails `01_site_members`, `01b_conflicts`, `02_hub_members`, `02_hub_snaps` .csv) | `profile.yaml` (THE config surface) | Region-as-data: improve the model by editing the profile, not the engine. **Hub builder, phase 5 (2026-10-07):** hubs group by the canonical corrected label (`group_by: [community]`, not city/borough); `cannot_link_across_community` keeps a 50 m stack of several villages apart; a label-vs-borough conflict is kept + reported, never dropped; unlabelled sites outside places group by `buffer_dist` blob; `max_snap_dist_m` leaves far hubs unplaced and a snap collision merges instead of overwriting; `remote_site_km` makes a site > N km from its labelled community its own hub (`hub_kind=remote_site`, label kept) so a repeater or mine never drags the town's centroid. **Same-mode line layers are R-noded TOGETHER** (one `st_node` per mode, keyed by the base layer) so manual flight paths share airport nodes with `airways` — noded in isolation, two manual legs meeting at a shared off-network endpoint linemerge and detach. **All Barge-mode layers are concatenated** into the waterway (was single-layer), so `manual_barge` isn't dropped; a manual-barge endpoint that lands mid-edge on the marine spine is welded in (`_weld_barge_landings` inserts a shared vertex), since waterway noding is vertex-rounding not planar |
| `05_verify_north_slope.py` | Connectivity assertion gate | exit code | — | Rescued from the old repo's "disposable" explain/ folder that run_all depended on |
| `06_export_final_network.py` | Stage-04 gpkg → final_network/ + zips + sha256 manifest | `final_network/` | NODE_RENAME | **CAUTION**: a re-export is a NEW network-of-record — see final_network/README.md before committing one |
| **03_multimodal_join** | | | | |
| `01_extract_network_handoff.py` | Unzips the frozen handoff | `final_network/*/` dirs | — | Fixes the fresh-clone FileNotFoundError; the old README claimed the loader extracted zips (it never did) |
| `02_load_final_network.py` | Ingest + hard integrity tripwire + edge_class | `network_nodes`, `network_edges` | `EXPECTED` dict | edge_id = shapefile row order, derived here and ONLY here; `edge_class` mirrors the mode-based `type` (pass-through), only mapping a LEGACY frozen network's generic `Bridge` into the new vocabulary |
| `03_weight_network_edges.py` | 75 m friction sampling per edge-month | `edge_month_weights` (1,115,736 rows) | `SAMPLE_SPACING_M`, `EDGE_TYPE_MAP` | Strict any-NoData ⇒ impassable; consumes `edge_class` from the DB (run stage 02 first) |
| `04_assemble_weighted_graph.py` | $-rates × friction → costs + nx.MultiGraph | `edge_costs` (1,115,736 rows) | `friction_costs.py` | MultiGraph, not Graph — parallel node-pairs would silently collapse; each per-pair `*Transfer` type maps straight to its fee via `TRANSFER_TYPE_TO_MODES` |
| **04_duckdb_export** | | | | |
| `01_run_validation_queries.py` | Monthly passability by mode | stdout | — | Barge passability should peak Jun–Oct; IceRoad rows exist only Jan–Mar |
| `02_inspect_schema.py` | Schema/count dump | stdout | — | Also probes `hub_facility_map` — expected ABSENT (documented future work) |

## Caution rows

- **Synthetic connectors use a mode-based vocabulary (refine-synthetic-connectors,
  2026-09).** `pipeline.classify_connectors` names every synthetic connector by the
  modes at its endpoints: within-mode welds → `{Mode}Connector` (RoadConnector,
  IceRoadConnector), cross-mode handoffs → per-pair `{A}{B}Transfer`
  (BargeRoadTransfer, BargeIceRoadTransfer, IceRoadRoadTransfer, AirRoadTransfer).
  The old flat `Bridge`/`Weld`/`Join`/generic-`Transfer` type labels are retired
  (provenance stays in `source`). Ice↔road connections are now a **priced Transfer**
  (`("overland","ice_road")` = $0.022/gal), not an ice-road line-haul. `EXPECTED`
  counts: RoadConnector 1,498 · IceRoadConnector 35 · BargeRoadTransfer 234 ·
  BargeIceRoadTransfer 11 · IceRoadRoadTransfer 12 · AirRoadTransfer 2. The mode is
  spelled `IceRoad` (no space) everywhere in the profile.
- **The network-of-record was rebuilt 2026-09-15 with AK-DOT-only roads**
  (84,089 nodes / 92,978 edges / 385 hubs / 5 components): the GRIP4 Canada
  border-stitch `extra_source` was removed (transnational roads are not
  fuel-delivery routes) and the road source updated to the 2026-09 AK DOT&PF
  download. It supersedes the 2026-09-12 manual-connections export and the
  2026-07-20 pre-fix freeze (both preserved in git history); the
  manual-connections layer is still included. **The phase-5 hub-builder fixes
  (2026-10-07) are in the code and profile but NOT yet in the network-of-record:
  the next rebuild on the owner's machine is the one rebuild the plan allows.**
  A re-export is a NEW network-of-record: regenerate the zips, the checksums
  (`inputs/MANIFEST.md`, `final_network/README.md`, `.github/workflows/ci.yml`),
  the `EXPECTED` tripwire, and the edge_id-keyed tables together. Do not
  re-export and commit without the owner asking.
- **Strict NoData rule.** One NoData sample makes an edge impassable for the
  month. This is a design decision (auditable via nodata_frac), not a bug.
- **The friction half WAS verified end-to-end on 2026-08-06** on the owner's
  machine (canonical wide-grid rasters + padded river ice located there):
  preflight all-green, mask -> stack -> QA passed, full weighting + costing
  reproduced the documented QA envelope (Road friction within [1.0, 2.625],
  IceRoad Jan-Mar only, transfer fees 205x0.24 + 8x0.011, zero cost-free
  passable edge-months). See docs/TEST_LOG.md. Fresh clones still need the
  rasters copied/regenerated (EXTERNAL_DATA.md).
- **`tools/build_notebooks.py` and `tools/gen_api_docs.py` (+ `docs/API.md`) were removed on 2026-08-17** (minimalism pass: off the build path; notebooks were never committed and the API reference was auto-generated). They survive in git history at commit `53569d0`.
- **`research/` and `diagnostics/` were removed on 2026-08-07** (build-only
  scope). They survive in git history at commit `3aa5eab`; docstrings in
  `source_scripts/mmnet/connect_extras.py`, `source_scripts/mmnet/inspect.py` and
  `workflows/02_network_build/01_prep_waterway.py` now name the prototypes
  without pointing at paths.
