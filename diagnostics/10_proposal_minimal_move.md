# Architecture proposal A — minimal-move merge

**Status: not adopted** (lowest migration risk, but keeps the two codebases as separate islands). Kept for its subtree-merge git mechanics and its cautious path-edit analysis.

_Auto-generated from the 2026-08-05 diagnostic workflow. Raw JSON in `raw/`._

## Proposal name

alaska-fuel-spatial-network (minimal-move merge — existing public repo retained as the base; two preserved workflow subtrees + shared inputs/ + thin join/export stages)

## Rationale

This is the lowest-risk merge that still satisfies every hard constraint. The repo keeps its existing GitHub identity (alaska-fuel-spatial-network already hosts the public release, its committed data zips, and the paper-facing history), so the URL in the Data-in-Brief manuscript never changes. Each codebase survives nearly untouched inside one numbered workflow directory — 10_build_friction/ is repo A's friction half with a single 3-line path edit, 20_build_network/ is repo B subtree-merged with full history and one 1-line output-path edit — so every import, relative path, config surface (friction_config.py / friction_costs.py / profile.yaml), and QA gate keeps working exactly as audited, and git blame/log stay familiar to both authors. The numbered top-level dirs (10 friction, 20 network, 30 join, 40 DuckDB export) make the directory listing itself narrate constraint 1's four-act process, while house-style NN_verb_noun numbering is applied only where files move anyway (the six repo-A root stage scripts), never inside the preserved packages. The single top-level inputs/ is repo A's existing pattern extended: repo B's never-committed 200 MB of raw GIS finally gets a committed, provenance-documented home as themed zips, and a 20-line 00_stage_inputs.py glue script reproduces repo B's expected data/raw layout without touching profile.yaml or normalize_raw.py — the same zip-then-extract idiom repo A already uses. The three genuinely new pieces are all thin: an orchestrator run_all.sh giving the one-command reproduction the house style demands, 00_extract_final_network.py closing the documented fresh-clone FileNotFoundError, and 01_finalize_duckdb.py making 'export to DuckDB' an explicit, verifiable stage (d) with a sha256 manifest. Contract-critical logic — edge_id = shapefile row order, the EXPECTED inventory tripwire, the frozen mmnet engine that actually built the delivered network — is deliberately left byte-identical, because the audits showed a rebuild with the fixed toolkit would cascade into invalidating every edge_id-keyed table; that decision is surfaced to the owner instead of being made silently by a file move. Deduplication is limited to cases the evidence proved safe: the byte-identical final_network READMEs, the verbatim fee-inference block (replaced by an import from its audited canonical home), the superseded middle copy of mmnet-toolkit, and two dead scripts.

## Proposed tree

```
alaska-fuel-spatial-network/                     # ONE public repo; numbered dirs narrate (a)->(b)->(c)->(d)
├── README.md                                    # NEW root narrative: pipeline map 10->20->30->40, quickstart, badges, paper link
├── CLAUDE.md                                    # NEW lab notebook: pipeline table (Script|Does|Outputs|Knobs|Finding), QA glossary, roadmap
├── LICENSE                                      # NEW (code license; data terms live in inputs/README.md)
├── CITATION.cff                                 # NEW (Data-in-Brief metadata — owner supplies title/DOI/author order)
├── EXTERNAL_DATA.md                             # REWRITTEN: committed vs regenerable vs archive-only (fixes stale "present on disk" claims)
├── requirements.txt                             # UNIFIED env spec: repo A pins + mmnet deps + nbformat/pyogrio; "+ pip install -e 20_build_network"
├── run_all.sh                                   # NEW thin orchestrator: sets PYTHONPATH/env, phases: network|friction|join|export|all
├── pipeline.py                                  # shared setup_logging helper (repo A root, unchanged)
├── .gitignore                                   # NEW merged file; reason comment per block; A's blanket-geodata+negations at root, B's data/** rules scoped under 20_build_network/
├── .gitattributes                               # NEW: LFS patterns (inputs/**/*.zip, final_network/*.zip) for FUTURE revisions — no history rewrite
├── .github/
│   └── workflows/ci.yml                         # NEW: pip install + editable mmnet install + pytest friction tests + validate_profile smoke + py_compile of stage scripts
├── .claude/
│   └── skills/                                  # repo A's 4 playbooks kept; internal paths updated to 10_build_friction/
├── inputs/                                      # SHARED single inputs home (constraint 2; friction repo's pattern extended)
│   ├── README.md                                # provenance table for EVERY dataset — now also covers the network-build raw data
│   ├── bulk_fuel_data.zip                       # repacked: __MACOSX/.DS_Store/.pyc/.claude junk stripped; facilities CSV LF-normalized
│   ├── data_for_network_build.zip               # unchanged (merged roads, waterways, ice roads, flights — friction/mask inputs)
│   ├── region_and_census_data.zip               # unchanged
│   ├── network_build_raw/                       # NEW: repo B's gitignored data/raw finally committed, as themed zips (LFS)
│   │   ├── roads_akdot.zip                      # reuse original source zip (~32 MB)
│   │   ├── grip4_canada.zip                     # ~4 MB
│   │   ├── nwn_waterway_network.zip             # USACE NWN lines (~10-15 MB zipped)
│   │   ├── boundaries_tiger.zip                 # TIGER places + boroughs
│   │   ├── facilities_inventory.zip             # Utilities_Bulk_Fuel_Inventory.csv, LF-normalized (single authoritative snapshot)
│   │   ├── ports_and_harbors.zip  ice_roads.zip  fuel_delivery_method.zip   # small
│   │   ├── air/                                 # tracked flat: flight_paths_combined.csv, airports_ak_dotpf.csv, flight_paths.xlsx (renamed, space removed)
│   │   └── Alaska_Fuel_Hubs_Transport_Network.md  # archived source report (was B: data/_archive/)
│   └── gee_exports/                             # GITIGNORED (reason: 4.7 GB AK_Stack_150m.zip exceeds GitHub; regenerate via GEE script)
├── 10_build_friction/                           # WORKFLOW (a): friction-layer build — repo A's friction half, nearly untouched
│   ├── README.md                                # was friction_surface/README_friction.md + stale-fix pass (burn-in text, viz/ name, --skip-surfaces)
│   ├── 01_build_corridor_masks.py               # was root build_corridor_masks.py — NOW in the canonical run order (fixes silent barge degradation)
│   ├── 02_build_friction_stack.py               # NEW 5-line wrapper -> friction_surface.run_friction_pipeline.main (gives the stage its NN script)
│   └── friction_surface/                        # package moved INTACT (importable via PYTHONPATH set by run_all.sh)
│       ├── friction_config.py                   # single friction-knob surface (unchanged)
│       ├── friction_costs.py                    # single $ surface (unchanged; 30_/03 re-pointed to import from here)
│       ├── friction_paths.py                    # 3-line edit: PROJECT_ROOT one dirname deeper; RASTER_DIR/FRICTION_DIR strings prefixed 10_build_friction/
│       ├── friction_surface.py  run_friction_pipeline.py  friction_preflight.py  friction_io.py  check_grid_exports.py  __init__.py
│       ├── friction_inputs/                     # GITIGNORED (~7 GB rasters; regenerate from inputs/gee_exports + arcpy pipeline)
│       ├── friction_outputs/                    # GITIGNORED (~288 MB friction stack)
│       ├── friction_preprocessing/              # GEE js, river-ice arcpy pipeline, align_permafrost, pad_*, build_brown_polygon_mask (unchanged)
│       └── qa/  tests/  viz_scripts/            # unchanged (qa_friction_stack, pytest unit tests, figure generators)
├── 20_build_network/                            # WORKFLOW (b): spatial-network build — alaska_network_mmnet subtree, nearly untouched
│   ├── README.md                                # stale-fix pass: real air inputs, prep_waterway in run order, handoff documented
│   ├── profile.yaml                             # THE network config surface (unchanged)
│   ├── pyproject.toml                           # mmnet editable install (unchanged)
│   ├── mmnet/                                   # FROZEN engine-of-record that built the delivered network (17 files, unchanged; frozen status noted)
│   │   ├── pipeline.py  config.py  build.py  assemble.py  connect_extras.py  network.py  inspect.py  io_readers.py  io_writers.py  viz.py
│   │   ├── steps/{consolidate,tag,hubs}.py
│   │   └── r_oracle/{build_network.R, lib.R, CONTRACT.md}
│   ├── scripts/
│   │   ├── 00_stage_inputs.py                   # NEW glue: extracts ../inputs/network_build_raw/*.zip + copies air/ -> data/raw/ (exact layout profile.yaml expects)
│   │   ├── normalize_raw.py  prep_waterway.py  prep_airways.py  fetch_basemap.py   # unchanged (README now lists ALL four in order)
│   │   ├── run_all.sh                           # workflow-local driver (unchanged; called by root run_all.sh)
│   │   ├── export_final_shapefile.py            # 1-line edit: OUT = ROOT.parent/"final_network"; + zips the exports (closes the manual handoff gap)
│   │   └── export_qgis.py  export_qgis_components.py  plot_network.py  plot_components.py  plot_join.py  plot_paper_network.py  build_notebooks.py  gen_api_docs.py
│   ├── data/                                    # GITIGNORED runtime tree (raw/ staged by 00_stage_inputs; interim/processed/basemap derived)
│   ├── output/                                  # GITIGNORED per-stage gpkg + QGIS artifacts
│   ├── notebooks/                               # regenerated by build_notebooks.py with RELATIVE root (kills baked /home/diegoarias paths)
│   ├── explain/                                 # narrated walkthroughs + verify_north_slope.py gate (kept; "disposable" claim removed)
│   ├── research/                                # 8 archival sandboxes with FINDINGS.md (kept as documented provenance)
│   └── docs/{ARCHITECTURE.md, API.md}           # ARCHITECTURE air-data section fixed
├── 30_join_multimodal/                          # WORKFLOW (c): thin join stage — repo A's root scripts, numbered
│   ├── 00_extract_final_network.py              # NEW ~20-line script: unzips final_network/*.zip into expected subdirs (fixes fresh-clone FileNotFoundError)
│   ├── 01_load_final_network.py                 # was load_final_network.py (ingest + EXPECTED tripwire + edge_class; DB path -> outputs/fuel_network.duckdb)
│   ├── 02_weight_network_edges.py               # was weight_network_edges.py (75 m sampling, NoData-strict, IceRoad gate)
│   ├── 03_assemble_weighted_graph.py            # was assemble_weighted_graph.py (edge_costs + MultiGraph; duplicated fee code replaced by import from friction_costs)
│   └── 04_plot_final_network.py                 # was make_network_plots.py
├── 40_export_duckdb/                            # WORKFLOW (d): the DuckDB deliverable
│   ├── 01_finalize_duckdb.py                    # NEW thin: assert 4-table contract + row counts, write outputs/40_duckdb_manifest.md (schema + sha256)
│   ├── 02_run_validation_query.py               # was run_validation_query.py (monthly passability by mode)
│   └── query_duckdb.py                          # ad-hoc inspector utility (hub_facility_map probe removed or marked future-work)
├── final_network/                               # THE 20->30 handoff artifact — single home for both roles
│   ├── README.md                                # merged (the two copies were byte-identical) + producer/consumer stages, export date + sha256 pinned
│   ├── network_joined_nodes.zip                 # committed (1.2 MB) — lets users skip workflow 20 entirely
│   ├── network_joined_edges.zip                 # committed (9.5 MB)
│   └── network_joined_{nodes,edges}/            # GITIGNORED extracted dirs (created by 00_extract_final_network.py)
├── mmnet-toolkit/                               # ONE canonical toolkit = repo A's copy (newest, 4 bugfixes); README declares canonical + divergence from frozen engine
│   ├── mmnet/  skills/  examples/alaska/{profile.yaml, verify_north_slope.py}  pyproject.toml  README.md
├── outputs/                                     # committed deliverables + gitignored regenerables
│   ├── README.md                                # updated: File | Producer(stage number) | Content; stale road/ice-road mask text removed
│   ├── fuel_network.duckdb                      # GITIGNORED (reason: 30 MB, regenerable by stages 30-40) — the (d) product
│   ├── waterway_mask_150m.tif                   # GITIGNORED (produced by 10_build_friction/01_)
│   ├── figures/  final_network_plots/  tables/  analysis/   # committed publication artifacts + their generator scripts (unchanged)
├── supplementary/                               # cost-derivations (00-06 + build_pdf) + cost-verification (unchanged)
└── docs/
    └── JETSTREAM_SETUP_GUIDE.md                 # was setup/ (drag-and-drop file-transfer section replaced by git clone)
```

## File mapping (old -> new)

- === REPO A = alaska-fuel-spatial-network (base repo; paths relative to its root) ===
- A: README.md -> MERGE into new root README.md (friction-specific run instructions move to 10_build_friction/README.md)
- A: STRUCTURE.md -> DROP (superseded by the annotated tree in the new root README.md)
- A: EXTERNAL_DATA.md -> EXTERNAL_DATA.md (rewritten: fixes false 'present on disk' claims; adds network raw data section)
- A: .gitignore -> MERGE into new root .gitignore (blanket-geodata + zip negations kept at root, reason comments added per house style)
- A: requirements.txt -> requirements.txt (unified: adds mmnet-side deps nbformat, pyogrio; trailing newline fixed)
- A: pipeline.py -> pipeline.py (unchanged)
- A: build_corridor_masks.py -> 10_build_friction/01_build_corridor_masks.py (rename only; stale --only help text fixed)
- A: friction_surface/** (38 tracked files: __init__.py, friction_config.py, friction_costs.py, friction_paths.py, friction_surface.py, run_friction_pipeline.py, friction_preflight.py, friction_io.py, check_grid_exports.py, README_friction.md, qa/{__init__,compare_lulc_grids,qa_friction_stack,qa_river_ice_thresholds}.py + lulc_fast_vs_exact_disagreement.png, tests/{__init__,test_friction_surface}.py, viz_scripts/{__init__,generate_grid_schema,generate_grid_schema_public,generate_pipeline_diagram,plot_combined_friction,plot_friction_stack,plot_sea_ice_padding}.py + friction_pipeline_diagram.pdf + sea_ice_padding_vs_data_03_Mar.png, friction_preprocessing/{README.md,__init__,align_permafrost,build_brown_polygon_mask,pad_river_ice_to_grid,pad_sea_ice_to_grid,plot_river_ice_provenance,river_ice_full_pipeline}.py + gee_friction_layer_mutli_data_processing.js) -> 10_build_friction/friction_surface/** (dir move intact; ONLY friction_paths.py edited: PROJECT_ROOT one dirname deeper + RASTER_DIR/FRICTION_DIR default strings prefixed '10_build_friction/'; README_friction.md becomes 10_build_friction/README.md with stale-fix pass)
- A: friction_surface/requirements-friction.txt -> DROP (single env surface at root; its rationale comments folded into requirements.txt)
- A: load_final_network.py -> 30_join_multimodal/01_load_final_network.py (edits: DB_PATH -> ROOT/outputs/fuel_network.duckdb; false 'extracts' docstring removed)
- A: weight_network_edges.py -> 30_join_multimodal/02_weight_network_edges.py (edits: DB_PATH/EDGES_SHP anchored to repo root; sys.path shim for friction_surface import)
- A: assemble_weighted_graph.py -> 30_join_multimodal/03_assemble_weighted_graph.py (edit: delete duplicated FEE_MODE/_lookup_fee/infer_transfer_fees at lines 66-131, import from friction_surface.friction_costs)
- A: make_network_plots.py -> 30_join_multimodal/04_plot_final_network.py (rename)
- A: run_validation_query.py -> 40_export_duckdb/02_run_validation_query.py (rename; DB path -> outputs/)
- A: query_duckdb.py -> 40_export_duckdb/query_duckdb.py (hub_facility_map probe marked future-work)
- A: final_network/{README.md, network_joined_edges.zip, network_joined_nodes.zip} -> final_network/<same> (README MERGE with B's byte-identical copy; stale 'Regenerate' section rewritten to point at 20_build_network; export sha256 + date added)
- A: inputs/README.md -> inputs/README.md (extended with network_build_raw provenance)
- A: inputs/data_for_network_build.zip -> inputs/data_for_network_build.zip (unchanged)
- A: inputs/region_and_census_data.zip -> inputs/region_and_census_data.zip (unchanged)
- A: inputs/bulk_fuel_data.zip -> inputs/bulk_fuel_data.zip (REPACKED: strip __MACOSX/.DS_Store/build_map.cpython-39.pyc/Flights/.claude/settings.local.json; facilities CSV LF-normalized)
- A: mmnet-toolkit/** (25 files) -> mmnet-toolkit/** (unchanged; README gains 'canonical copy' declaration + bugfix changelog vs the frozen 20_build_network/mmnet engine)
- A: outputs/README.md -> outputs/README.md (rewritten: File | Producer(stage) | Content; stale road/ice-road mask text removed)
- A: outputs/analysis/{_lulc_edge_sensitivity,_lulc_sensitivity_buffer,_lulc_sensitivity_results,_road_grade_distribution}.json + {lulc_sensitivity_test,road_grade_distribution}.md -> outputs/analysis/<same> (unchanged)
- A: outputs/figures/* (13 committed PNG/PDF artifacts) + outputs/figures/scripts/{plot_hub_network,plot_reference_grid,plot_weighted_network}.py -> outputs/figures/<same> (unchanged; plot_weighted_network.py DB anchor -> outputs/fuel_network.duckdb)
- A: outputs/final_network_plots/{01_statewide_overview,02_connectors_detail,03_hubs}.png -> outputs/final_network_plots/<same> (unchanged)
- A: outputs/tables/{build_combined_friction_tables,build_input_datasets_xlsx}.py + 3 xlsx -> outputs/tables/<same> (unchanged)
- A: supplementary/cost-derivations/* (13 files) + supplementary/cost-verification/* (2 files) -> supplementary/<same> (unchanged)
- A: .claude/skills/** (8 files, 4 skills) -> .claude/skills/** (kept; hard-coded friction_surface/ paths in validate_friction_stack.py, check_cost_invariants.py, align_raster.py updated to 10_build_friction/; stale 'writes DuckDB' docstring fixed)
- A: setup/JETSTREAM_SETUP_GUIDE.md -> docs/JETSTREAM_SETUP_GUIDE.md (drag-and-drop transfer section replaced by git clone)
- A: setup/installations.txt -> DROP (comment-only; folded into README quickstart)
- === REPO B = alaska_network_mmnet (subtree-merged under 20_build_network/; paths relative to its root) ===
- B: README.md -> 20_build_network/README.md (stale-fix pass: real air inputs named, prep_waterway + fetch_basemap in run order, handoff to 30_join documented, giant-component metric drift reconciled)
- B: .gitignore -> MERGE into root .gitignore as a scoped 20_build_network/data/** section (plus new __MACOSX, .venv, *.egg-info, __pycache__ blocks, all with reason comments)
- B: profile.yaml -> 20_build_network/profile.yaml (unchanged — THE network config surface)
- B: pyproject.toml -> 20_build_network/pyproject.toml (unchanged; the editable-install target)
- B: mmnet/** (17 files: __init__,pipeline,config,build,assemble,connect_extras,network,inspect,io_readers,io_writers,viz + steps/{__init__,consolidate,tag,hubs} + r_oracle/{build_network.R,lib.R,CONTRACT.md}) -> 20_build_network/mmnet/** (unchanged — FROZEN engine-of-record that built the delivered shapefiles; no fix backports without a rebuild decision)
- B: scripts/{normalize_raw,prep_waterway,prep_airways,fetch_basemap,export_qgis,export_qgis_components,plot_network,plot_components,plot_join,plot_paper_network,build_notebooks,gen_api_docs}.py + scripts/run_all.sh -> 20_build_network/scripts/<same> (unchanged except prep_airways.py stale docstring paths)
- B: scripts/export_final_shapefile.py -> 20_build_network/scripts/export_final_shapefile.py (edit: OUT = ROOT.parent/'final_network'; zip step appended so the handoff artifact is regenerated in place)
- B: scripts/extract_od_table.py -> DROP (dead: broken output path, superseded by flight_paths_combined.csv)
- B: notebooks/{01_consolidate,01b_tag,02_hubs,03_build,04_join,05_run_pipeline}.ipynb -> 20_build_network/notebooks/<same> (REGENERATED by build_notebooks.py with a relative project root — the /home/diegoarias-baked versions do not survive verbatim)
- B: explain/** (10 files: README,_trace,explain00..05,run_all.sh,verify_north_slope.py) -> 20_build_network/explain/** (unchanged; README's 'rm -rf explain/' advice removed — run_all.sh depends on verify_north_slope.py)
- B: research/** (45 files across airport_connection, flights_network, ice_ice_connect, multimodal_network, param_check, road_ice_connect, road_road_connect, waterway_network) -> 20_build_network/research/** (unchanged, archival provenance)
- B: docs/ARCHITECTURE.md -> 20_build_network/docs/ARCHITECTURE.md (air-data section fixed); B: docs/API.md -> 20_build_network/docs/API.md (regenerated by gen_api_docs.py)
- B: final_network/README.md -> MERGE into root final_network/README.md (byte-identical with A's copy)
- B: mmnet-toolkit/** (25 files) -> DROP (superseded by root mmnet-toolkit/, which carries the reset_index mis-snap fix, scoped warnings, Optional typing, nullable-string fixes)
- B: data/raw/connectivity/air/flight_paths_combined.csv -> inputs/network_build_raw/air/flight_paths_combined.csv
- B: data/raw/connectivity/air/airports_ak_dotpf.csv -> inputs/network_build_raw/air/airports_ak_dotpf.csv
- B: 'data/raw/connectivity/air/Flight Paths.xlsx' -> inputs/network_build_raw/air/flight_paths.xlsx (space removed)
- B: data/raw/connectivity/air/build_map.py -> DROP (loose script committed inside the data tree, referenced nowhere)
- B: data/_archive/Alaska_Fuel_Hubs_Transport_Network.md -> inputs/network_build_raw/Alaska_Fuel_Hubs_Transport_Network.md
- === REPO B UNTRACKED DATA ASSETS (on disk only today — packaged into committed zips, not git-moved) ===
- B(disk): data/raw/connectivity/road/Roads_AKDOT_8888552456722853580.zip -> inputs/network_build_raw/roads_akdot.zip (reused as-is, ~32 MB, LFS)
- B(disk): data/raw/connectivity/road/GRIP4_canada/* -> inputs/network_build_raw/grip4_canada.zip (NEW zip)
- B(disk): data/raw/connectivity/barge/NWN_Waterway_Network_Lines/* -> inputs/network_build_raw/nwn_waterway_network.zip (NEW zip)
- B(disk): data/raw/boundaries/* (TIGER places, county subdivisions, borough_census_area) -> inputs/network_build_raw/boundaries_tiger.zip (NEW zip)
- B(disk): data/raw/facilities/Utilities_Bulk_Fuel_Inventory.csv -> inputs/network_build_raw/facilities_inventory.zip (LF-normalized single authoritative snapshot — the A-vs-B md5 'divergence' is line endings only, verified)
- B(disk): data/raw/anchor_points/Ports_and_Harbors.geojson + data/raw/connectivity/barge/AK_Ports_and_Harbors -> inputs/network_build_raw/ports_and_harbors.zip (NEW zip)
- B(disk): data/raw/connectivity/ice_roads/* -> inputs/network_build_raw/ice_roads.zip (NEW zip; byte-identical to the copy inside data_for_network_build.zip — duplication documented)
- B(disk): data/raw fuel-delivery-method geojson -> inputs/network_build_raw/fuel_delivery_method.zip (NEW zip)
- B(disk): data/interim/**, data/processed/**, data/basemap/**, data/boundary.geojson, output/**, reports/**, explain/out/**, research/**/out/**, final_network/*.shp+sidecars -> NOT MIGRATED (derived/regenerable; the final_network .shp are already byte-identical inside the committed zips)
- B(disk): .venv/, mmnet.egg-info/ (x2), __pycache__/**, example_skills/ (incl. __MACOSX), data/interim/MANIFEST.html + MANIFEST_files/, output/coach/COACH_LEDGER.json, data/raw/**/tl_2022_02_place.zip -> DROP (never enters the merged repo; blocked by the merged .gitignore)
- === NEW FILES (no old path) ===
- NEW -> README.md, CLAUDE.md, LICENSE, CITATION.cff, .gitattributes, .github/workflows/ci.yml, run_all.sh, docs/ (dir), 10_build_friction/02_build_friction_stack.py (5-line wrapper), 20_build_network/scripts/00_stage_inputs.py (inputs -> data/raw glue), 30_join_multimodal/00_extract_final_network.py (unzip glue), 40_export_duckdb/01_finalize_duckdb.py (table contract + sha256 manifest)

## Migration steps (ordered)

- 0. SAFETY NET: create a bare backup of alaska_network_mmnet (it has NO remote — this is the only copy of its history): `git clone --bare alaska_network_mmnet /backup/alaska_network_mmnet.git`; tag both repos (`pre-merge-2026-08`); work in a fresh clone of alaska-fuel-spatial-network on branch `merge/mmnet` — never on main directly.
- 1. IMPORT REPO B WITH HISTORY: in a temp clone of alaska_network_mmnet, run `git filter-repo --to-subdirectory-filter 20_build_network` (its history is tiny — largest blob 0.05 MB — so this is cheap and keeps Diego's 66-commit log + attribution). Rename its branch master -> main. In the merge clone: `git remote add mmnet <temp>; git fetch mmnet; git merge --allow-unrelated-histories mmnet/main`.
- 2. GIT MV — repo A side (pure renames, one commit): friction_surface/ -> 10_build_friction/friction_surface/; README_friction.md -> 10_build_friction/README.md; build_corridor_masks.py -> 10_build_friction/01_build_corridor_masks.py; load_final_network.py -> 30_join_multimodal/01_load_final_network.py; weight_network_edges.py -> 30_join_multimodal/02_weight_network_edges.py; assemble_weighted_graph.py -> 30_join_multimodal/03_assemble_weighted_graph.py; make_network_plots.py -> 30_join_multimodal/04_plot_final_network.py; run_validation_query.py -> 40_export_duckdb/02_run_validation_query.py; query_duckdb.py -> 40_export_duckdb/query_duckdb.py; setup/JETSTREAM_SETUP_GUIDE.md -> docs/; delete STRUCTURE.md, setup/installations.txt, friction_surface/requirements-friction.txt.
- 3. GIT MV/RM — repo B subtree (one commit): git rm -r 20_build_network/mmnet-toolkit (superseded by root copy) and 20_build_network/scripts/extract_od_table.py and 20_build_network/data/raw/connectivity/air/build_map.py; git mv the three tracked air files + data/_archive report to inputs/network_build_raw/ (rename 'Flight Paths.xlsx' -> flight_paths.xlsx); git mv 20_build_network/final_network/README.md away (root copy is byte-identical — keep one).
- 4. PATH EDITS (small, enumerated, one commit): (a) 10_build_friction/friction_surface/friction_paths.py — PROJECT_ROOT gains one more os.path.dirname (now 3 levels up from the file), and the RASTER_DIR/FRICTION_DIR defaults gain the '10_build_friction/' prefix; INPUTS_DIR/OUTPUTS_DIR/NETWORK_DIR then resolve to top-level inputs/ and outputs/ automatically. (b) The three 30_join scripts + 40_export scripts: DB_PATH -> ROOT/'outputs'/'fuel_network.duckdb' and a 2-line sys.path.insert for 10_build_friction (or rely on run_all.sh PYTHONPATH — pick one and do both defensively). (c) outputs/figures/scripts/plot_weighted_network.py DB anchor. (d) 20_build_network/scripts/export_final_shapefile.py: OUT = ROOT.parent/'final_network' + zip step. (e) .claude/skills scripts: friction paths -> 10_build_friction/. (f) 03_assemble_weighted_graph.py: replace the duplicated fee-inference block (old lines 66-131) with `from friction_surface.friction_costs import FEE_MODE, infer_transfer_fees`.
- 5. NEW GLUE + ORCHESTRATOR (one commit): write run_all.sh (phases: stage-inputs -> network [scripts/run_all.sh + export_final_shapefile] -> friction [01_ + 02_, guarded: skips with a clear message if friction_inputs/ rasters absent] -> join [00_..04_] -> export [01_finalize + 02_validate]; exports PYTHONPATH=$ROOT/10_build_friction and NETWEAVE_PROJECT=$ROOT/20_build_network); write 20_build_network/scripts/00_stage_inputs.py, 30_join_multimodal/00_extract_final_network.py, 10_build_friction/02_build_friction_stack.py, 40_export_duckdb/01_finalize_duckdb.py.
- 6. PACKAGE THE NETWORK RAW DATA (one commit): build inputs/network_build_raw/*.zip from alaska_network_mmnet's on-disk data/raw (roads_akdot reusing the original source zip; LF-normalize Utilities_Bulk_Fuel_Inventory.csv and record in inputs/README.md that the two prior copies differed only in line endings); repack inputs/bulk_fuel_data.zip stripping __MACOSX/.DS_Store/.pyc/settings.local.json; add .gitattributes with `inputs/**/*.zip filter=lfs` and `final_network/*.zip filter=lfs` BEFORE adding the new zips so new blobs land in LFS (do NOT rewrite existing history — the published repo A blobs stay as-is).
- 7. MERGED .gitignore (one commit): single root file, house-style reason comment per block — repo A's blanket geodata excludes + explicit zip negations (now including inputs/network_build_raw/*.zip and the air CSVs/xlsx); repo B's rules rescoped to 20_build_network/data/**, 20_build_network/output/, 20_build_network/reports/, explain/out, research/**/out; final_network/*/ extracted dirs; outputs/fuel_network.duckdb + waterway_mask_150m.tif; plus .venv/, *.egg-info/, __pycache__/, __MACOSX/, .DS_Store.
- 8. GITHUB BEST-PRACTICE FILES (one commit): LICENSE (owner decision), CITATION.cff (owner supplies paper metadata), root README.md with the four-stage narrative + badges, CLAUDE.md lab notebook seeded with one pipeline-table row per numbered script (Findings imported from the audit evidence: e.g. '01_build_corridor_masks required or barge surfaces sever ~18% of waterway edges — Caution'), .github/workflows/ci.yml (ubuntu: pip install -r requirements.txt; pip install -e 20_build_network; pytest 10_build_friction/friction_surface/tests; python -c mmnet validate_profile('20_build_network/profile.yaml'); python -m py_compile over all NN_ scripts).
- 9. DOCS PASS (one commit): fix the enumerated stale claims — root/10 README: remove --skip-surfaces, add corridor-mask step, state that 00_extract does the unzipping; 20 README: real air inputs, full prep order incl. prep_waterway + fetch_basemap; final_network/README.md: producer/consumer stages, sha256 + export date of the current zips; EXTERNAL_DATA.md: honest per-machine availability (the 4.7 GB GEE stack and ~7 GB friction_inputs exist on Julia's machine only); outputs/README.md producer table; regenerate notebooks + docs/API.md.
- 10. VERIFY BEFORE PUSH: fresh clone to /tmp; `pip install -r requirements.txt && pip install -e 20_build_network`; run `./run_all.sh join export` (the only fully runnable path on this machine — friction rasters are absent) and confirm 01_load passes the EXPECTED tripwire, edge_month_weights/edge_costs land in outputs/fuel_network.duckdb only if rasters exist (otherwise confirm the guard message), pytest green, CI green on the branch. Diff the frozen 20_build_network/mmnet against the pre-merge repo B copy (must be byte-identical).
- 11. PUBLISH: merge to main, push to the chosen account/org (open question), enable LFS on the remote, `git gc` locally. Leave the old alaska_network_mmnet directory ON DISK untouched with a MOVED.md pointer — alaska_network_pipeline_mmnet's venv editable-installs mmnet from an absolute path inside it and its run_arm.sh diffs against ../alaska_network_mmnet/profile.yaml; deleting it breaks the TAPS study.
- 12. FOLLOW-UP (separate PRs, not in the merge): decide freeze-vs-rebuild for the network given the toolkit's mis-snap fix (a rebuild changes edge counts -> invalidates EXPECTED + every edge_id-keyed table); archive the 4.7 GB GEE stack + 7 GB rasters to Zenodo/UA repository and link from EXTERNAL_DATA.md; optionally adopt uv + pyproject + uv.lock as the single env spec.

## Risks

- Frozen-vs-fixed engine tension: 20_build_network/mmnet (which built the deliverable) lacks the mis-snap fix that root mmnet-toolkit carries. The merge documents but does not resolve this; any future rebuild with either engine can change node/edge counts, breaking 01_load_final_network's EXPECTED tripwire and invalidating edge_month_weights/edge_costs keyed by edge_id = row order.
- friction_paths.py edits are subtle: it performs an import-time chdir and anchors RASTER_DIR/FRICTION_DIR/INPUTS_DIR/NETWORK_DIR off PROJECT_ROOT. Getting the new dirname depth or prefix strings wrong silently relocates fuel_network.duckdb or makes preflight look in the wrong place. Mitigate with a unit test asserting the resolved paths from a fake CWD.
- The friction workflow cannot be end-to-end verified on this machine (the 4.7 GB GEE stack and ~7 GB friction_inputs exist only on Julia's machine), so stage-10 breakage from the move could ship unnoticed. The CI can only import-check and unit-test it; a full rebuild on the machine that has the rasters must happen before tagging a release.
- External coupling: alaska_network_pipeline_mmnet (TAPS study) editable-installs mmnet from an absolute path inside alaska_network_mmnet and diffs ../alaska_network_mmnet/profile.yaml. The migration leaves that directory on disk, but any later cleanup that deletes it breaks the TAPS venv and run_arm.sh assertions.
- Repo size and LFS half-measure: existing history already carries ~50 MB of zip blobs; new network_build_raw zips add ~60-90 MB more. Putting only NEW blobs in LFS avoids rewriting published history but leaves a mixed storage model; forgetting .gitattributes before step 6 bakes the new zips into plain history permanently.
- Subtree merge with --allow-unrelated-histories produces a two-root history; tools that assume a single root (some release/changelog generators, shallow clones with --since) can behave oddly, and contributors doing `git log -- 20_build_network/mmnet/pipeline.py` must know renames cross the graft point (use --follow).
- Data redistribution: committing repo B's raw AKDOT/GRIP4/USACE/TIGER/AEA extracts to a public repo assumes their licenses permit redistribution; TIGER and USACE are public domain, but GRIP4 (CC-BY) and AEA inventory terms need explicit confirmation before push.
- The 30_join scripts' dual path strategy (PYTHONPATH from run_all.sh AND an in-file sys.path shim) can mask misconfiguration; users invoking scripts directly from odd CWDs may still write the DuckDB to an unexpected place if the friction_paths chdir edit and the DB_PATH edits disagree.
- Notebook regeneration replaces committed .ipynb content wholesale; if build_notebooks.py's relative-root change is buggy, the committed notebooks are broken for cloners while looking 'regenerated'. CI should execute at least the 01_consolidate notebook headlessly or drop notebooks from the public repo.
- Duplicated data across zips remains (Ice_Roads, flight paths exist in both data_for_network_build.zip and network_build_raw/): a future re-curation of one copy silently diverges the other; the inputs/README.md duplication note is the only guard.

## Open questions for the owners

- License: which code license (MIT/Apache-2.0/BSD-3) — and do the AEA facilities inventory, GRIP4 (CC-BY), and hand-digitized flight paths permit public redistribution inside inputs/? If not, network_build_raw zips must move to a data repository (Zenodo/UA ScholarWorks) with a fetch script instead.
- Publishing identity: keep the repo under github.com/jccheesman (Julia's account, where the public release lives) or transfer to an org/Diego's account? Repo A is authored by Julia, repo B by Diego — CITATION.cff author order and the commit-attribution story need an explicit decision.
- Rename the repo? 'alaska-fuel-spatial-network' undersells the merged scope; 'alaska-fuel-multimodal-network' is truer, and GitHub redirects old URLs — but is the current name already cited in the submitted manuscript?
- Freeze or rebuild: keep the delivered network as-is (built with the pre-fix engine; EXPECTED tripwire and all edge_id-keyed tables stay valid) or rebuild Stage 03/04 with the fixed mmnet-toolkit engine and re-derive EXPECTED, the zips, and the DuckDB? Only the owners can weigh scientific correctness against re-validating 1.09 M-row tables mid-review.
- CITATION.cff metadata: title, author list/order, DOI or preprint link for the Data-in-Brief paper — none of this exists in either repo.
- Public-repo scope of repo B's process history: keep research/ (45 files), explain/, and notebooks/ in the public tree (they narrate method provenance) or move them to a private archive branch to slim the public face?
- Where do the big rasters live long-term? The 4.7 GB GEE stack and ~7 GB friction_inputs exist only on Julia's machine; should they be deposited (Zenodo has a 50 GB limit) so EXTERNAL_DATA.md can point at a DOI instead of 'regenerate in GEE'?
- hub_facility_map / backfill_facility_edges stub: drop the dead probe + NotImplementedError from the public release, or keep them documented as the routing-layer extension point (the 384-hub-to-1,838-facility mapping exists nowhere on this machine)?
- Environment modernization: stay with the unified requirements.txt (lowest risk, matches current repos) or move now to the house-preferred uv + pyproject + uv.lock in the same release?
- Old alaska_network_mmnet directory: after the merge, keep it on disk indefinitely for the TAPS study's absolute-path venv, or update alaska_network_pipeline_mmnet to install from the merged repo and then archive the old directory?
