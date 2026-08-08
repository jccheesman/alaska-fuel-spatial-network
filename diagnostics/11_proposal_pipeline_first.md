# Architecture proposal B — pipeline-first (flat numbered scripts)

**Status: not adopted** (most restructuring). Kept for its producer-numbered outputs idea and its exhaustive code-edit enumeration, both folded into the adopted design.

_Auto-generated from the 2026-08-05 diagnostic workflow. Raw JSON in `raw/`._

## Proposal name

alaska-fuel-multimodal-network

## Rationale

The pipeline-first layout makes the repo read exactly like the paper's methods section: block A (01–05) builds the multimodal network from public GIS sources, block B (10–13) builds the 150 m friction stack, block C (20–22) joins them — network into DuckDB, friction sampled onto every edge per month, dollars attached — and block D (30+) validates and draws the deliverables. The decade-gapped numbering encodes the DAG (A and B are independent; C needs both) while keeping the house NN_verb_noun convention, and every artifact carries its producer's number (outputs/12_friction_stack, outputs/20_duckdb, figs/32_*), so an outside reader can trace any file back to one script. Constraint 3 is honored by making the stages thin wrappers: mmnet and friction_surface move under src/ with module names unchanged, and the eight code edits are enumerated exhaustively in the migration steps — everything else is a git mv. The design also resolves the four structural pathologies the audit surfaced: the triplicated mmnet package collapses to one canonical src/mmnet (the copy carrying the bugfixes); the two opposite-role final_network/ dirs become one producer-numbered outputs/05_network_shapefiles/ that stage 05 writes and stage 20 reads, turning the undocumented cross-repo manual handoff into an ordinary pipeline edge with committed, sha256-pinned zips; the two conflicting .gitignore regimes are replaced by one reasoned file; and the single top-level inputs/ (constraint 2) absorbs both repos' data with per-dataset provenance URLs, fixing repo B's fresh-clone-unrunnable problem. GitHub best practice arrives as LICENSE, CITATION.cff, CI with a data-free stage-20 reproducibility smoke, LFS for the ~55 MB of committed zips, uv-locked single environment, and a CLAUDE.md lab notebook per house style. The committed network zips are deliberately kept as the frozen v1 deliverable so the fragile edge_id=row-order and EXPECTED-inventory contracts stay valid even though the shipped network predates the engine bugfixes.

## Proposed tree

```
alaska-fuel-multimodal-network/
├── README.md                          # THE narrative: 4 numbered blocks (01–05 network, 10–13 friction, 20–22 join+weight→DuckDB, 30+ validate/figures); quickstart = clone → uv sync → ./run_all.sh
├── LICENSE                            # code license (owner choice, MIT suggested); data terms live in inputs/README.md
├── CITATION.cff                       # Data-in-Brief paper + software citation (authors: Cheesman + Arias; needs DOI/title from owners)
├── CLAUDE.md                          # NEW lab notebook: pipeline table | Script | What | Outputs | Knobs | Finding | (house-mandatory)
├── pyproject.toml                     # ONE env spec: packages mmnet + friction_surface (src-layout), pinned deps, r_oracle package-data
├── uv.lock                            # locked env (replaces requirements.txt, requirements-friction.txt, 2× toolkit pyprojects)
├── run_all.sh                         # one-command reproduction; gates: skips 01–05 if inputs/network/raw absent (falls back to committed zips), skips 10–13 if inputs/friction absent
├── profile.yaml                       # network-build config surface — the single canonical copy (was 3×)
├── .gitignore                         # rewritten, every block carries a reason comment; merges the two conflicting regimes
├── .github/
│   └── workflows/ci.yml               # NEW: uv sync + ruff + pytest + mmnet validate_profile + stage-20 DuckDB smoke from the committed network zips
│
├── inputs/                            # CONSTRAINT 2: single top-level inputs/ for ALL input datasets
│   ├── README.md                      # provenance + download URL per dataset (merge of A/inputs/README.md + A/EXTERNAL_DATA.md + the URLs repo B never wrote down)
│   ├── MANIFEST.md                    # NEW: sha256 of every committed zip/CSV + expected hashes for fetched (gitignored) data
│   ├── network/                       # sources for stages 01–05
│   │   ├── data_for_network_build.zip # committed via LFS (34M): AKDOT+GRIP4 roads merge, NWN waterways, ice roads, flights (repacked: __MACOSX/.DS_Store/.pyc/.claude stripped)
│   │   ├── bulk_fuel_data.zip         # committed via LFS: AEA facilities inventory — ONE LF-normalized copy (the two repo copies were the same snapshot with different line endings)
│   │   ├── region_and_census_data.zip # committed via LFS: TIGER states/places + AEA library
│   │   ├── air/                       # tracked small official air inputs (the files the stale docs never mention)
│   │   │   ├── flight_paths_combined.csv
│   │   │   ├── airports_ak_dotpf.csv
│   │   │   └── flight_paths.xlsx      # renamed from "Flight Paths.xlsx" (no spaces)
│   │   ├── _archive/
│   │   │   └── Alaska_Fuel_Hubs_Transport_Network.md   # archived source report (provenance)
│   │   └── raw/                       # GITIGNORED (154M+ shapefiles; re-fetch per inputs/README.md URLs) — Roads_AKDOT/, GRIP4_canada/, NWN_Waterway_Network_Lines/, boundaries/, ice_roads/, facilities/, anchor_points/
│   └── friction/                      # sources for stages 10–13 — GITIGNORED (multi-GB), regeneration documented
│       ├── gee_exports/               # AK_Stack_150m.zip (4.7GB) from the stage-00 GEE script — NOT committed, NOT currently on this machine
│       └── rasters/                   # slope.tif, lulc.tif, permafrost.tif, sea_ice/, river_ice/ (~7GB; was friction_surface/friction_inputs/)
│
├── scripts/                           # thin numbered NN_verb_noun entry points; logic stays in src/
│   ├── 00_external_preprocess/        # stage 00: runs in GEE / ArcGIS Pro, not the venv (README says so)
│   │   ├── README.md                  # rewritten (old one listed phantom files, omitted the pad scripts)
│   │   ├── gee_friction_layer_multi_data_processing.js   # typo "mutli" fixed
│   │   ├── river_ice_full_pipeline.py                    # arcpy; PROJECT_ROOT default de-Windowsed
│   │   ├── build_brown_polygon_mask.py
│   │   ├── pad_sea_ice_to_grid.py
│   │   ├── pad_river_ice_to_grid.py
│   │   ├── align_permafrost.py
│   │   ├── plot_river_ice_provenance.py
│   │   └── check_grid_exports.py                         # cheap metadata gate on GEE re-exports
│   │                                  # ---- block A: spatial-network build (constraint 1b) ----
│   ├── 01_normalize_network_inputs.py # was B/scripts/normalize_raw.py; SPEC table now points at inputs/network/raw/
│   ├── 02_extract_waterway_network.py # was B/scripts/prep_waterway.py (finally in the documented run order)
│   ├── 03_geocode_airways.py          # was B/scripts/prep_airways.py; stale docstring paths fixed
│   ├── 04_build_multimodal_network.py # NEW thin wrapper: mmnet.run_pipeline('profile.yaml') → outputs/04_network/ (internal mmnet stages 01→04 + reports)
│   ├── 05_export_network_shapefiles.py# was B/scripts/export_final_shapefile.py; now ALSO zips + writes sha256 into outputs/05_network_shapefiles/README.md (closes the manual handoff)
│   │                                  # ---- block B: friction-layer build (constraint 1a) ----
│   ├── 10_preflight_friction_inputs.py# thin wrapper → friction_surface.friction_preflight
│   ├── 11_build_corridor_masks.py     # was A/build_corridor_masks.py → outputs/11_masks/waterway_mask_150m.tif (now IN the run order — was the silent-degrade trap)
│   ├── 12_build_friction_stack.py     # thin wrapper → friction_surface.run_friction_pipeline → outputs/12_friction_stack/ (14 tifs)
│   ├── 13_qa_friction_stack.py        # thin wrapper → friction_surface.qa.qa_friction_stack
│   │                                  # ---- block C: join + weight → DuckDB (constraints 1c+1d) ----
│   ├── 20_load_network_duckdb.py      # was A/load_final_network.py; auto-extracts the zips (fixes fresh-clone FileNotFoundError); EXPECTED inventory read from outputs/05_.../README.md-adjacent JSON
│   ├── 21_weight_network_edges.py     # was A/weight_network_edges.py; consumes edge_class from stage 20 instead of re-deriving
│   ├── 22_assemble_weighted_graph.py  # was A/assemble_weighted_graph.py; imports fee helpers from friction_costs (66-line duplicate deleted)
│   │                                  # ---- block D: validate + deliverable figures/tables ----
│   ├── 30_validate_fuel_network_db.py # was A/run_validation_query.py (monthly passability by mode)
│   ├── 31_plot_final_network.py       # was A/make_network_plots.py → figs/31_*
│   ├── 32_plot_weighted_network.py    # was A/outputs/figures/scripts/plot_weighted_network.py → figs/32_*
│   ├── 33_plot_hub_network.py         # was A/outputs/figures/scripts/plot_hub_network.py → figs/33_*
│   ├── 34_plot_reference_grid.py      # was A/outputs/figures/scripts/plot_reference_grid.py → figs/34_*
│   ├── 35_build_friction_tables.py    # was A/outputs/tables/build_combined_friction_tables.py → tables/35_*
│   ├── 36_build_input_datasets_xlsx.py# was A/outputs/tables/build_input_datasets_xlsx.py → tables/36_*
│   └── 37_plot_paper_network.py       # was B/scripts/plot_paper_network.py (publication faceted map) → figs/37_*
│
├── src/                               # house src-layout; installed editable via uv
│   ├── mmnet/                         # THE one canonical engine (from A/mmnet-toolkit/mmnet — newest copy, carries the 4 bugfixes incl. assemble.py reset_index)
│   │   ├── __init__.py  pipeline.py  config.py  build.py  assemble.py  network.py
│   │   ├── connect_extras.py  inspect.py  io_readers.py  io_writers.py  viz.py
│   │   ├── steps/{__init__,consolidate,tag,hubs}.py
│   │   └── r_oracle/{build_network.R, lib.R, CONTRACT.md}   # hybrid R-oracle pattern, shipped as package data
│   └── friction_surface/              # friction package, module names unchanged (imports survive)
│       ├── __init__.py                # dead routing-era re-exports trimmed
│       ├── friction_config.py         # friction knobs — single source of truth (unchanged)
│       ├── friction_costs.py          # every dollar; now the ONLY copy of FEE_MODE/_lookup_fee/infer_transfer_fees
│       ├── friction_paths.py          # repointed: inputs/friction, outputs/12_friction_stack, outputs/20_duckdb; import-time os.chdir REMOVED
│       ├── friction_surface.py  friction_io.py  friction_preflight.py  run_friction_pipeline.py
│       ├── pipeline_logging.py        # was A/pipeline.py (setup_logging only; compat re-exports dropped)
│       └── qa/{__init__,qa_friction_stack,qa_river_ice_thresholds,compare_lulc_grids}.py
│
├── data/                              # GITIGNORED intermediates of stages 01–03 (derived, regenerable)
│   ├── interim/                       # normalize_raw outputs + MANIFEST.md (regenerated)
│   ├── processed/                     # airways.geojson, air_nodes.geojson, boundary.geojson
│   └── basemap/                       # Natural Earth downloads (tools/fetch_basemap.py)
│
├── outputs/                           # GITIGNORED regenerables, producer-numbered; README.md is the tracked deliverable contract
│   ├── README.md                      # tracked: File | Producer script | Content table, ends with "cite fuel_network.duckdb"
│   ├── 04_network/                    # mmnet gpkg chain 01_facilities…04_network_joined__* + reports/*.md
│   ├── 05_network_shapefiles/         # THE handoff, now internal: network_joined_{nodes,edges}.zip (COMMITTED via LFS — the frozen v1 deliverable) + README.md (field dictionary, inventory, sha256) + expected_inventory.json
│   ├── 11_masks/                      # waterway_mask_150m.tif
│   ├── 12_friction_stack/             # overland.tif, road_base.tif, barge_01..12.tif (~288MB)
│   ├── 20_duckdb/
│   │   └── fuel_network.duckdb        # network_nodes, network_edges, edge_month_weights, edge_costs (written by 20→22)
│   └── logs/                          # timestamped pipeline logs
│
├── figs/                              # COMMITTED publication figures, producer-numbered (31_…, 32_…, 37_…); regenerated by scripts 31–34, 37
├── tables/                            # COMMITTED publication tables (35_*.xlsx, 36_*.xlsx)
│
├── tools/                             # non-pipeline utilities (run ad hoc, unnumbered on purpose)
│   ├── query_duckdb.py                # ad-hoc DB inspector (hub_facility_map probe removed or flagged future-work)
│   ├── fetch_basemap.py  build_notebooks.py  export_qgis.py  export_qgis_components.py  gen_api_docs.py
│   ├── viz_network/{plot_network,plot_components,plot_join}.py
│   └── viz_friction/{plot_friction_stack,plot_combined_friction,generate_grid_schema,generate_grid_schema_public,generate_pipeline_diagram,plot_sea_ice_padding}.py
│
├── tests/
│   ├── test_friction_surface.py       # was A/friction_surface/tests/…
│   └── verify_north_slope.py          # was B/explain/verify_north_slope.py — the connectivity gate run_all.sh calls after stage 04 (explain/ itself dropped)
│
├── docs/
│   ├── architecture.md                # merged + corrected B/docs/ARCHITECTURE.md (air-data section rewritten for flight_paths_combined.csv)
│   ├── network_build.md               # deep network-workflow notes from B/README.md
│   ├── friction.md                    # corrected A/friction_surface/README_friction.md (burn-in prose deleted, env-var table fixed)
│   ├── duckdb_schema.md               # the 4-table schema + edge_id=row-order contract, stated once
│   ├── API.md                         # regenerated by tools/gen_api_docs.py
│   ├── mmnet.md                       # from mmnet-toolkit/README.md: the region-agnostic engine story
│   └── setup_jetstream.md             # optional VM guide (updated for git clone, not drag-and-drop)
│
├── supplementary/                     # committed evidence backing the numbers
│   ├── cost-derivations/              # 00..06 blind-derivation mds + build_pdf.py + build_transfer_pdf.py (committed html DROPPED, regenerable)
│   ├── cost-verification/             # audit md + fuel_cost_blind_derivations.pdf (renamed, no spaces)
│   └── sensitivity/                   # was A/outputs/analysis/: LULC sensitivity + road-grade JSON/md studies
│
├── research/                          # tracked archival sandboxes from B (scripts + FINDINGS.md; out/ gitignored)
│   ├── README.md                      # NEW index: each sandbox, its finding, and where it was ported into the engine
│   └── road_road/ ice_ice/ road_ice/ waterway_network/ flights_network/ multimodal_network/ airport_connection/ param_check/
│
└── .claude/
    └── skills/                        # 6 committed playbooks: align-to-ak-stack, assign-friction-values, derive-fuel-costs, run-friction-pipeline (paths repointed), define-network-profile, build-and-verify-network (from mmnet-toolkit)
```

## File mapping (old -> new)

- LEGEND: A = alaska-fuel-spatial-network, B = alaska_network_mmnet
- A/load_final_network.py -> scripts/20_load_network_duckdb.py (add zip auto-extract; EXPECTED dict externalized to outputs/05_network_shapefiles/expected_inventory.json)
- A/weight_network_edges.py -> scripts/21_weight_network_edges.py (read edge_class from DuckDB instead of re-deriving)
- A/assemble_weighted_graph.py -> scripts/22_assemble_weighted_graph.py (MERGE: delete duplicated FEE_MODE/_lookup_fee/infer_transfer_fees, import from friction_surface.friction_costs)
- A/build_corridor_masks.py -> scripts/11_build_corridor_masks.py (fix --only help text: one spec, not three)
- A/run_validation_query.py -> scripts/30_validate_fuel_network_db.py
- A/make_network_plots.py -> scripts/31_plot_final_network.py
- A/query_duckdb.py -> tools/query_duckdb.py (drop hub_facility_map probe or mark future-work)
- A/pipeline.py -> src/friction_surface/pipeline_logging.py (MERGE: keep setup_logging; drop get_raster_dir/get_vector_dir compat re-exports)
- A/friction_surface/__init__.py -> src/friction_surface/__init__.py (trim dead re-exports)
- A/friction_surface/friction_config.py -> src/friction_surface/friction_config.py
- A/friction_surface/friction_costs.py -> src/friction_surface/friction_costs.py (fix broken FUEL_DELIVERY_METHOD_CSV path or drop load_ice_road_communities + get_hub_facilities)
- A/friction_surface/friction_paths.py -> src/friction_surface/friction_paths.py (repoint dirs; remove import-time os.chdir; drop dead ROAD_MASK_TIF/ICE_ROAD_MASK_TIF)
- A/friction_surface/friction_surface.py -> src/friction_surface/friction_surface.py
- A/friction_surface/friction_io.py -> src/friction_surface/friction_io.py
- A/friction_surface/friction_preflight.py -> src/friction_surface/friction_preflight.py (+ NEW thin scripts/10_preflight_friction_inputs.py)
- A/friction_surface/run_friction_pipeline.py -> src/friction_surface/run_friction_pipeline.py (+ NEW thin scripts/12_build_friction_stack.py)
- A/friction_surface/check_grid_exports.py -> scripts/00_external_preprocess/check_grid_exports.py
- A/friction_surface/qa/qa_friction_stack.py -> src/friction_surface/qa/qa_friction_stack.py (+ NEW thin scripts/13_qa_friction_stack.py)
- A/friction_surface/qa/qa_river_ice_thresholds.py -> src/friction_surface/qa/qa_river_ice_thresholds.py
- A/friction_surface/qa/compare_lulc_grids.py -> src/friction_surface/qa/compare_lulc_grids.py (document unshipped default inputs)
- A/friction_surface/qa/lulc_fast_vs_exact_disagreement.png -> DROP (regenerable artifact in source dir)
- A/friction_surface/tests/test_friction_surface.py -> tests/test_friction_surface.py
- A/friction_surface/friction_preprocessing/gee_friction_layer_mutli_data_processing.js -> scripts/00_external_preprocess/gee_friction_layer_multi_data_processing.js (typo fixed)
- A/friction_surface/friction_preprocessing/river_ice_full_pipeline.py -> scripts/00_external_preprocess/river_ice_full_pipeline.py (de-Windows PROJECT_ROOT default)
- A/friction_surface/friction_preprocessing/{pad_sea_ice_to_grid,pad_river_ice_to_grid,build_brown_polygon_mask,align_permafrost,plot_river_ice_provenance}.py -> scripts/00_external_preprocess/ (same names)
- A/friction_surface/friction_preprocessing/README.md -> scripts/00_external_preprocess/README.md (rewritten: real file list)
- A/friction_surface/viz_scripts/*.py -> tools/viz_friction/ (same names; generate_pipeline_diagram docstring path fixed)
- A/friction_surface/viz_scripts/{sea_ice_padding_vs_data_03_Mar.png, friction_pipeline_diagram.pdf} -> DROP (regenerable)
- A/friction_surface/README_friction.md -> docs/friction.md (burn-in prose + env-var defaults corrected)
- A/friction_surface/requirements-friction.txt -> DROP (MERGE into pyproject.toml)
- A/requirements.txt -> DROP (MERGE into pyproject.toml + uv.lock)
- A/README.md -> MERGE into README.md (phantom --skip-surfaces, false 'extracts', missing mask step all fixed)
- A/STRUCTURE.md -> DROP (superseded by README tree)
- A/EXTERNAL_DATA.md -> MERGE into inputs/README.md (corrected: rasters are NOT on disk in this copy)
- A/setup/installations.txt -> DROP (superseded by pyproject)
- A/setup/JETSTREAM_SETUP_GUIDE.md -> docs/setup_jetstream.md (updated)
- A/inputs/data_for_network_build.zip -> inputs/network/data_for_network_build.zip (repacked clean; LFS)
- A/inputs/bulk_fuel_data.zip -> inputs/network/bulk_fuel_data.zip (MERGE with B/data/raw/facilities/Utilities_Bulk_Fuel_Inventory.csv — same AEA snapshot, keep one LF-normalized CSV; LFS)
- A/inputs/region_and_census_data.zip -> inputs/network/region_and_census_data.zip (LFS)
- A/inputs/README.md -> MERGE into inputs/README.md
- A/final_network/network_joined_edges.zip -> outputs/05_network_shapefiles/network_joined_edges.zip (LFS; frozen v1 deliverable)
- A/final_network/network_joined_nodes.zip -> outputs/05_network_shapefiles/network_joined_nodes.zip (LFS; MERGE — byte-identical to B/final_network/*.shp, zips are the canonical committed form)
- A/final_network/README.md -> outputs/05_network_shapefiles/README.md (MERGE with B/final_network/README.md — identical; regenerate section rewritten to scripts 01–05, + sha256 + built-with-engine note)
- A/outputs/figures/scripts/plot_weighted_network.py -> scripts/32_plot_weighted_network.py
- A/outputs/figures/scripts/plot_hub_network.py -> scripts/33_plot_hub_network.py
- A/outputs/figures/scripts/plot_reference_grid.py -> scripts/34_plot_reference_grid.py
- A/outputs/figures/*.{png,pdf} -> figs/32_*|33_*|34_* (renamed to producer numbers)
- A/outputs/final_network_plots/* -> figs/31_* (renamed)
- A/outputs/tables/build_combined_friction_tables.py -> scripts/35_build_friction_tables.py
- A/outputs/tables/build_input_datasets_xlsx.py -> scripts/36_build_input_datasets_xlsx.py
- A/outputs/tables/*.xlsx -> tables/35_*|36_* (renamed)
- A/outputs/analysis/{_lulc_edge_sensitivity.json,_lulc_sensitivity_buffer.json,_lulc_sensitivity_results.json,_road_grade_distribution.json,lulc_sensitivity_test.md,road_grade_distribution.md} -> supplementary/sensitivity/
- A/outputs/README.md -> outputs/README.md (rewritten: drop phantom road/ice-road mask docs; deliverable-contract table)
- A/supplementary/cost-derivations/{00..06}*.md + build_pdf.py + build_transfer_pdf.py -> supplementary/cost-derivations/ (as-is)
- A/supplementary/cost-derivations/{combined.html,transfer_fees.html} -> DROP (regenerable)
- A/supplementary/cost-verification/* -> supplementary/cost-verification/ ('Fuel Cost Blind Derivations.pdf' renamed fuel_cost_blind_derivations.pdf)
- A/mmnet-toolkit/mmnet/** -> src/mmnet/** (CANONICAL — newest copy with the 4 bugfixes; MERGE point for all three copies)
- A/mmnet-toolkit/pyproject.toml -> DROP (MERGE into root pyproject.toml)
- A/mmnet-toolkit/skills/{define-network-profile,build-and-verify-network}/** -> .claude/skills/
- A/mmnet-toolkit/examples/alaska/{profile.yaml,verify_north_slope.py} -> DROP (root profile.yaml and tests/verify_north_slope.py are canonical)
- A/mmnet-toolkit/README.md -> docs/mmnet.md
- A/.claude/skills/{align-to-ak-stack,assign-friction-values,derive-fuel-costs,run-friction-pipeline}/** -> .claude/skills/ (paths repointed; validate_friction_stack.py stale 'writes DuckDB' docstring fixed)
- A/.gitignore + B/.gitignore -> MERGE into new .gitignore (rewritten from scratch with reason comments)
- B/profile.yaml -> profile.yaml (canonical single copy)
- B/mmnet/** -> MERGE into src/mmnet (superseded by A's toolkit copy; diff-verify only env-var naming + the 4 fixes differ before deleting)
- B/mmnet-toolkit/** -> DROP (middle-aged duplicate)
- B/pyproject.toml -> MERGE into root pyproject.toml
- B/scripts/normalize_raw.py -> scripts/01_normalize_network_inputs.py (SPEC raw dir -> inputs/network/raw/)
- B/scripts/prep_waterway.py -> scripts/02_extract_waterway_network.py
- B/scripts/prep_airways.py -> scripts/03_geocode_airways.py (stale docstring paths fixed)
- B/scripts/export_final_shapefile.py -> scripts/05_export_network_shapefiles.py (writes outputs/05_network_shapefiles/ + zip + sha256)
- B/scripts/run_all.sh -> MERGE into run_all.sh (extended to the full 01→31 chain)
- B/scripts/fetch_basemap.py -> tools/fetch_basemap.py
- B/scripts/build_notebooks.py -> tools/build_notebooks.py (emit dynamic project root, not /home/diegoarias)
- B/scripts/export_qgis.py -> tools/export_qgis.py
- B/scripts/export_qgis_components.py -> tools/export_qgis_components.py
- B/scripts/plot_network.py -> tools/viz_network/plot_network.py
- B/scripts/plot_components.py -> tools/viz_network/plot_components.py
- B/scripts/plot_join.py -> tools/viz_network/plot_join.py
- B/scripts/plot_paper_network.py -> scripts/37_plot_paper_network.py
- B/scripts/gen_api_docs.py -> tools/gen_api_docs.py
- B/scripts/extract_od_table.py -> DROP (dead: broken output path, superseded by flight_paths_combined.csv)
- B/docs/ARCHITECTURE.md -> docs/architecture.md (air-data section rewritten)
- B/docs/API.md -> docs/API.md (regenerated)
- B/README.md -> MERGE into README.md + docs/network_build.md
- B/explain/verify_north_slope.py -> tests/verify_north_slope.py
- B/explain/** (rest) -> DROP (self-declared disposable walkthroughs)
- B/notebooks/*.ipynb -> DROP (generated artifacts; regenerable via tools/build_notebooks.py)
- B/research/{road_road,ice_ice,road_ice,waterway_network,flights_network,multimodal_network,airport_connection,param_check}/** -> research/ (tracked scripts+FINDINGS.md as-is; out/ stays gitignored; + NEW research/README.md status index)
- B/research/sfnetwork_check/ -> DROP (orphan out/-only dir, nothing tracked)
- B/data/raw/connectivity/air/{flight_paths_combined.csv,airports_ak_dotpf.csv} -> inputs/network/air/ (tracked)
- B/data/raw/connectivity/air/'Flight Paths.xlsx' -> inputs/network/air/flight_paths.xlsx
- B/data/raw/connectivity/air/build_map.py -> DROP (loose code in data tree, referenced nowhere)
- B/data/_archive/Alaska_Fuel_Hubs_Transport_Network.md -> inputs/network/_archive/Alaska_Fuel_Hubs_Transport_Network.md
- B/data/raw/** (gitignored bulk: Roads_AKDOT, GRIP4_canada, NWN waterways, ice_roads, boundaries, facilities, ports) -> inputs/network/raw/** (still gitignored; URLs + hashes documented in inputs/README.md + MANIFEST.md)
- B/data/{interim,processed,basemap}/**, B/output/**, B/reports/** -> NOT MIGRATED (derived, regenerated into data/ and outputs/04_network/ by stages 01–04)
- B/final_network/*.{shp,shx,dbf,prj,cpg} -> MERGE (byte-identical content already committed as the zips in outputs/05_network_shapefiles/)
- B/example_skills/** -> DROP (stray copies of A's skills + __MACOSX junk)
- B/{.venv,mmnet.egg-info,__pycache__,data/interim/MANIFEST.html+MANIFEST_files,output/coach/COACH_LEDGER.json} -> DROP (never tracked; junk)
- NEW files: LICENSE, CITATION.cff, CLAUDE.md, run_all.sh, pyproject.toml, uv.lock, .github/workflows/ci.yml, inputs/MANIFEST.md, outputs/05_network_shapefiles/expected_inventory.json, research/README.md, scripts/{04,10,12,13}_*.py thin wrappers

## Migration steps (ordered)

- SAFETY NET: push alaska_network_mmnet to a private GitHub remote as-is (it has NO remote — 1.3GB incl. the only copy of hand-curated data exists on one machine); run `git gc` first (44M loose objects). Tag both repos (pre-merge-A, pre-merge-B).
- OWNER DECISIONS (blocking): pick hosting account (jccheesman vs Diego), license, and freeze-vs-rebuild for the delivered network (see open questions). The steps below assume FREEZE (v1 network built with the pre-fix engine, documented as such).
- Create the new repo locally. Import both histories with git-filter-repo: clone A, `git filter-repo --to-subdirectory-filter _incoming_A --strip-blobs-bigger-than 5M` (drops superseded figure/zip revisions from history; current large files re-enter via LFS); clone B, same with _incoming_B; then in the new repo `git merge --allow-unrelated-histories` both. This preserves Julia's and Diego's authorship. (Alternative: fresh orphan 'Initial public release' commit — repo A already squashed once; owner call.)
- Install git-lfs; `git lfs track 'inputs/network/*.zip' 'outputs/05_network_shapefiles/*.zip'` before any data lands.
- Write the new .gitignore FIRST (reason comments per block): inputs/network/raw/ (too large, re-fetchable), inputs/friction/ (multi-GB rasters, regenerable via stage 00), data/ (derived), outputs/** except README.md, 05_network_shapefiles/{*.zip,README.md,expected_inventory.json} (regenerable; DuckDB rebuilt by 20–22), research/**/out/, .venv/, __pycache__/, *.egg-info/, __MACOSX/, .DS_Store.
- Consolidate mmnet: `diff -r` A/mmnet-toolkit/mmnet against B/mmnet and B/mmnet-toolkit/mmnet to confirm the only deltas are the MMNET_*/NETWEAVE_* env rename + the 4 documented fixes (assemble.py reset_index, build.py scoped warnings, config.py Optional, io_readers.py nullable string); copy A's toolkit copy to src/mmnet/; delete the other two copies and both toolkit pyprojects.
- Move friction_surface to src/friction_surface (git mv, module names unchanged); move A/pipeline.py into it as pipeline_logging.py; move tests/ out to top-level tests/.
- Apply the full file mapping with git mv in one 'restructure: pipeline-first layout' commit: numbered scripts/, tools/, docs/, supplementary/, research/, inputs/ trees as designed.
- Write root pyproject.toml (packages: mmnet, mmnet.steps, friction_surface, friction_surface.qa; package-data r_oracle/*; deps = union of A/requirements.txt pins + B pyproject + missing nbformat/pyogrio/duckdb/rasterio); `uv venv && uv lock && uv sync`; delete requirements*.txt.
- ENUMERATED CODE EDITS (the only ones; everything else moves as-is): (1) friction_paths.py — new dirs (inputs/friction, outputs/11_masks, outputs/12_friction_stack, outputs/05_network_shapefiles, outputs/20_duckdb/fuel_network.duckdb), delete import-time os.chdir and dead mask constants; (2) 01_normalize_network_inputs.py SPEC raw-dir -> inputs/network/raw/; (3) 05_export_network_shapefiles.py out-dir -> outputs/05_network_shapefiles/ + zip + sha256 emission; (4) 20_load_network_duckdb.py — auto-extract zips, read expected_inventory.json, DB path from friction_paths; (5) 21/22 — DB path constant, and 22 imports fee helpers from friction_costs (delete duplicate block); (6) mmnet output dir -> outputs/04_network (env/one constant in io_writers); (7) tools/build_notebooks.py dynamic root; (8) new thin wrappers 04/10/12/13 calling package mains.
- Data normalization: repack the three inputs/network zips stripping __MACOSX/.DS_Store/*.pyc/.claude; pick the LF-normalized Utilities_Bulk_Fuel_Inventory.csv (verified same AEA snapshot as A's CRLF copy) and note it in inputs/README.md; copy the two final_network zips to outputs/05_network_shapefiles/; write inputs/MANIFEST.md + expected_inventory.json with sha256 of everything committed.
- Write run_all.sh: stage chain 01→05 (gated on inputs/network/raw presence) → tests/verify_north_slope.py → 10→13 (gated on inputs/friction presence) → 20→22 (from committed zips if 05 not rebuilt) → 30→31. Fresh-clone default path = stages 20–31 only, fully reproducible from committed data.
- Docs pass: root README (four-block narrative, quickstart, badges, explicit 'what runs from a fresh clone vs what needs the 4.7GB GEE stack'); fix every stale-doc item flagged by the audit (README_friction burn-in prose, outputs/README phantom masks, preprocessing README file list, final_network regenerate section, validate_friction_stack docstring, IceRoad Jan-Apr vs Jan-Mar comment); write CLAUDE.md lab-notebook pipeline table (one row per numbered script incl. Finding); LICENSE; CITATION.cff; docs/duckdb_schema.md stating the edge_id=row-order contract once.
- Add .github/workflows/ci.yml: uv sync, ruff, pytest tests/, `python -c 'import mmnet; mmnet.validate_profile("profile.yaml")'`, and a stage-20 smoke (unzip committed network zips -> load -> assert expected_inventory.json counts) — a real reproducibility check needing no external data.
- Verify end-to-end on this machine: fresh clone -> uv sync -> ./run_all.sh reproduces fuel_network.duckdb (4 tables, 1,091,052-row weights/costs absent without rasters — the run degrades loudly and stops after stage 20 validation + plots; document this). Full verification of stages 10–22 waits until the GEE stack is re-exported (it is on NO machine right now).
- Decommission gently: leave alaska_network_mmnet on disk untouched (the TAPS study alaska_network_pipeline_mmnet resolves mmnet via an absolute editable path into it and diffs ../alaska_network_mmnet/profile.yaml — deleting it breaks that venv); add MOVED.md pointers in both old repos; archive the old GitHub repo jccheesman/alaska-fuel-spatial-network with a pointer README once the new repo is live.
- Release: tag v1.0.0, enable Zenodo integration for a DOI, put the DOI in CITATION.cff and a badge row (CI, license, DOI) in README.

## Risks

- Frozen-network tension: src/mmnet ships the bugfixed engine, but the committed outputs/05 zips were built pre-fix. Anyone re-running stages 01–05 may get different node/edge counts, tripping expected_inventory.json and orphaning edge_month_weights/edge_costs keyed on edge_id=row-order. Must be documented loudly; a rebuild decision belongs to the owners.
- The friction half (stages 10–13) cannot be end-to-end tested during migration: the 4.7GB GEE stack and ~7GB friction_inputs exist on NO machine right now (EXTERNAL_DATA.md is stale). The friction_paths repointing therefore ships verified only by unit tests and preflight dry runs until someone re-exports from GEE.
- Removing friction_paths' import-time os.chdir changes CWD-dependent behavior for every consumer (skills' checker scripts, QA modules, ad-hoc runs from subdirs); each entry point must resolve paths from PROJECT_ROOT explicitly, and a missed one fails silently by writing elsewhere.
- The TAPS sibling study (alaska_network_pipeline_mmnet) hard-codes an absolute editable install into alaska_network_mmnet/mmnet-toolkit and asserts 'mmnet-toolkit' in mmnet.__file__; the old repo must stay on disk or that project's venv and run_arm.sh break.
- History merge via filter-repo rewrites SHAs; if the owners instead keep the existing public jccheesman repo and restructure in place, force-pushing rewritten history breaks any existing forks/clones of the published companion repo.
- Data redistribution: the committed zips embed AEA, AKDOT, USACE, GRIP4 and Census-derived layers; publishing them under a code license without checking source terms is a legal exposure (GRIP4 in particular has attribution requirements).
- LFS quotas: ~55MB of tracked zips is fine for storage, but GitHub LFS bandwidth caps (1GB/mo free) could throttle cloners of a popular public repo; fallback is plain git blobs under the 100MB limit (current state) at the cost of history bloat on re-curation.
- Renaming committed publication figures/tables to producer-numbered filenames breaks any external references (the in-prep paper, the README schema image currently hosted on github user-attachments) — the paper's figure sources must be re-pointed once.
- Mass git mv plus edits in the same window risks losing rename detection if edits are large; keep the restructure commit move-only and the eight code edits in separate commits so blame/history stay legible.
- The hand-digitized layers (Ice_Roads, flight paths) have no regeneration path; their only durable home becomes the committed data_for_network_build.zip — corrupting or carelessly re-curating that zip loses source data permanently. The private backup of repo B (step 1) is the real safety net.

## Open questions for the owners

- Hosting and identity: which account/org publishes the merged repo (jccheesman, who owns the current public repo, or Diego)? Is the existing jccheesman/alaska-fuel-spatial-network archived with a pointer, or restructured in place (force-push implications)? Author order and roles for CITATION.cff?
- Freeze or rebuild: keep the delivered 82,300/90,921 network as the frozen v1 (built with the pre-reset_index engine) or rebuild with the fixed src/mmnet — accepting new counts, a new expected_inventory.json, and recomputing edge_month_weights/edge_costs? Only the owners can judge whether the mis-snap fix materially changes the published network.
- What are the Data-in-Brief paper's title/authors/DOI (or preprint link)? Required for CITATION.cff, the README, and Zenodo metadata; it appears nowhere in either repo.
- Code license choice (MIT/BSD-3/Apache-2), and have the redistribution terms of the committed AEA/AKDOT/USACE/GRIP4/TIGER-derived zips been checked?
- History: preserve both merged histories with attribution (recommended above) or start a clean squashed 'Initial public release' as repo A did before?
- Commit the ~30MB fuel_network.duckdb via LFS as a convenience deliverable for non-Python readers, or keep it regenerable-only (current design)?
- hub_facility_map / backfill_facility_edges: the 384-hub-to-1,838-facility mapping exists nowhere on this machine — drop the stub and probe entirely, or keep them documented as future work (does the routing/TSP layer have a planned home)?
- Scope of the public repo: do the eight research/ sandboxes, docs/setup_jetstream.md, and the .claude/skills playbooks belong in the public release, or in a private companion archive?
- Should src/mmnet eventually leave for its own repo/PyPI as the region-agnostic toolkit (its stated ambition), with this repo pinning a version — and if so, does the merged repo vendor it until that split?
- Utilities_Bulk_Fuel_Inventory.csv: confirm the LF-normalized single copy is acceptable as the canonical AEA snapshot for both workflows (audit verified the two repo copies differ only in line endings, but the owners should bless the snapshot date).
