# CLAUDE.md — lab notebook

House rules for working in this repo: never commit or push without the owner
asking; move-only commits separate from edit commits; every dollar lives in
`friction_costs.py` and every friction constant in `friction_config.py`;
`final_network` zip members stay byte-identical (edge_id contract);
`data/`, `outputs/01_*`, `outputs/02_*`, extracted `final_network/*/` are
regenerable working trees — never hand-edit them.

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
| `tools/extract_inputs.py` | Unzips committed inputs into gitignored working dirs | `inputs/{bulk_fuel_data,data_for_network_build,region_and_census_data}/`, `data/raw/` | — | One gate for workflows 01–02; fixes the fresh-clone story both old repos lacked |
| **01_friction_build** | | | | |
| `00_preflight_inputs.py` | Grid + range gates on the friction rasters | pass/fail report | RASTER_DIR env | Every input must match `lulc.tif`'s 28,000×16,567 grid exactly |
| `01_build_corridor_masks.py` | Rasterizes the waterway network (75 m buffer, all_touched) | `outputs/01_friction_build/waterway_mask_150m.tif` | `CORRIDOR_BUFFER_M` | **REQUIRED before stage 02** — a missing mask is a hard error in the stack build (maskless = ~18% of waterway edges severed; explicit opt-out for synthetic runs only) |
| `02_build_friction_stack.py` | overland + road_base + barge_01..12 | `outputs/01_friction_build/friction_stack/` (14 TIFs / 24 logical surfaces) | `friction_config.py` | road_base is NoData-free by construction so land edges can't be accidentally severed |
| `03_qa_friction_stack.py` | Hard post-build gates | exit code | — | Checks the 14-file contract, Jul>Jan barge pixels (ice gating direction), value floor |
| **02_network_build** | | | | |
| `00_normalize_raw.py` | data/raw → uniform EPSG:3338 interim layer + MANIFEST | `data/interim/` | its SPEC table | The SPEC table is de-facto config: one entry per raw file, incl. the official air-data swap |
| `01_prep_waterway.py` | Full-Alaska NWN extraction | `data/interim/ak_waterway.gpkg` | `NODE_TOL=50` (matches assembler rounding) | Replaced the old facility-bbox clip — ~316 lines / ~31,903 km marine network |
| `02_prep_airways.py` | Geocode OD legs | `data/processed/{airways,air_nodes}.geojson`, `data/boundary.geojson` | — | Interim files keep legacy names (`air_flight_paths_od.csv`) though sources are the official AK DOT&PF data — don't "fix" one without the other |
| `03_fetch_basemap.py` | Natural Earth downloads | `data/basemap/` | — | Figures only |
| `04_build_network.py` | validate_profile + mmnet stages 01→04 | `outputs/02_network_build/{output,reports}` | `profile.yaml` (THE config surface) | Region-as-data: improve the model by editing the profile, not the engine |
| `05_verify_north_slope.py` | Connectivity assertion gate | exit code | — | Rescued from the old repo's "disposable" explain/ folder that run_all depended on |
| `06_export_final_network.py` | Stage-04 gpkg → final_network/ + zips + sha256 manifest | `final_network/` | NODE_RENAME | **CAUTION**: a re-export is a NEW network-of-record — see final_network/README.md before committing one |
| **03_multimodal_join** | | | | |
| `01_extract_network_handoff.py` | Unzips the frozen handoff | `final_network/*/` dirs | — | Fixes the fresh-clone FileNotFoundError; the old README claimed the loader extracted zips (it never did) |
| `02_load_final_network.py` | Ingest + hard integrity tripwire + edge_class | `network_nodes`, `network_edges` | `EXPECTED` dict | edge_id = shapefile row order, derived here and ONLY here; legacy Bridge = weld, not a water crossing (ice-involved ones become IceRoadConnector) |
| `03_weight_network_edges.py` | 75 m friction sampling per edge-month | `edge_month_weights` (1,091,052 rows) | `SAMPLE_SPACING_M`, `EDGE_TYPE_MAP` | Strict any-NoData ⇒ impassable; consumes `edge_class` from the DB (run stage 02 first) |
| `04_assemble_weighted_graph.py` | $-rates × friction → costs + nx.MultiGraph | `edge_costs` (1,091,052 rows) | `friction_costs.py` | MultiGraph, not Graph — 648 parallel node-pairs would silently collapse; fee inference hard-errors on ambiguity |
| **04_duckdb_export** | | | | |
| `01_run_validation_queries.py` | Monthly passability by mode | stdout | — | Barge passability should peak Jun–Oct; IceRoad rows exist only Jan–Mar |
| `02_inspect_schema.py` | Schema/count dump | stdout | — | Also probes `hub_facility_map` — expected ABSENT (documented future work) |

## Caution rows

- **The network-of-record is PRE-FIX.** `final_network/*.zip` was built by the
  old engine before `src/mmnet`'s four bugfixes (notably the reset_index
  mis-snap fix). The engine and the deliverable deliberately disagree until
  the owners decide freeze-vs-rebuild. Do not "helpfully"
  rebuild and commit.
- **Strict NoData rule.** One NoData sample makes an edge impassable for the
  month. This is a design decision (auditable via nodata_frac), not a bug.
- **The friction half WAS verified end-to-end on 2026-08-06** on Julia's
  machine (canonical wide-grid rasters + padded river ice located there):
  preflight all-green, mask -> stack -> QA passed, full weighting + costing
  reproduced the documented QA envelope (Road friction within [1.0, 2.625],
  IceRoad Jan-Mar only, transfer fees 205x0.24 + 8x0.011, zero cost-free
  passable edge-months). See docs/TEST_LOG.md. Fresh clones still need the
  rasters copied/regenerated (EXTERNAL_DATA.md).
- **`tools/build_notebooks.py`** regenerates the per-stage walkthrough
  notebooks; its cell text still narrates the OLD flat-repo layout in places
  — regenerate + review before committing any notebooks.
- **`research/` and `diagnostics/` were removed on 2026-08-07** (build-only
  scope). They survive in git history at commit `3aa5eab`; docstrings in
  `src/mmnet/connect_extras.py`, `src/mmnet/inspect.py` and
  `workflows/02_network_build/01_prep_waterway.py` now name the prototypes
  without pointing at paths.
