# Architecture proposal C — library + workflows (src-layout) — ADOPTED BASIS

**Status: ADOPTED** as the basis of `../MIGRATION_SPEC.md`. Its file mapping and migration steps below are the most detailed operational reference for the merge.

_Auto-generated from the 2026-08-05 diagnostic workflow. Raw JSON in `raw/`._

## Proposal name

alaska-fuel-multimodal-network (src-layout LIBRARY+WORKFLOWS merge)

## Rationale

The design puts the two things worth reusing — the region-agnostic mmnet engine and the friction_surface library (config, costs, builders, QA) — under src/ as one installable distribution, and moves every run-this-then-that concern into four numbered workflows/ stages that literally spell out the user's required narrative: 01 friction build, 02 network build, 03 multimodal join with weighted edges, 04 the DuckDB deliverable. This is the LIBRARY+WORKFLOWS angle taken seriously: the follow-on paper analyses (routing/TSP, the blocked hub_facility_map work) can `pip install` the repo and import friction_costs rates, the mmnet engine, and the DuckDB schema without touching workflow scripts, while CI tests the library (pytest + profile validation) plus the one data-backed smoke that committed zips permit (extract + dry-run ingest validating the full 82,300/90,921 inventory). Canonical-copy choices are forced by the evidence: A's mmnet-toolkit/mmnet is the newest of three copies and carries four strict bugfixes, so it becomes src/mmnet and the other two copies die — while the delivered network stays frozen in final_network/ with checksums and an explicit built-pre-fix provenance note, because rebuilding with the fixed engine would change hub snapping and invalidate the edge_id=row-order contract behind edge_month_weights and edge_costs. Constraint 3 (mostly as-is) is honored: scripts move and get renamed, but the only code edits are path constants, one import-deduplication (the verbatim fee-inference copy in assemble_weighted_graph), and ~5 new thin files (extract helper, build driver, three friction drivers) — each fixing a documented fresh-clone failure rather than rewriting logic. Constraint 2 lands everything ingestible under inputs/, including the single biggest gap the audits found: repo B's 200MB of raw network data existed only on one disk with no remote; inputs/network_raw.zip (LFS) gives it a committed home and makes workflow 02 runnable from a clone. House style is applied throughout: NN_verb_noun scripts, profile.yaml/friction_config as the two per-stage config surfaces (documented in DATA_CONTRACTS.md rather than force-merged, since friction constants and network topology knobs serve different stages), outputs carrying their producing stage (outputs/01_friction_build/, outputs/fuel_network.duckdb), reason-commented gitignore, a CLAUDE.md lab notebook with a Finding column, and one top-level run_all.sh whose gates state honestly which stages need the 4.7GB regenerable GEE stack.

## Proposed tree

```
alaska-fuel-multimodal-network/
├── README.md                          # NEW narrative: the 4-stage story (friction -> network -> join -> DuckDB), badges, quickstart; merges both old READMEs; fixes --skip-surfaces / "extracts the zips" / missing-mask-step doc inaccuracies
├── LICENSE                            # NEW — code license (owner decision; MIT suggested) + pointer to data-terms note in inputs/README.md
├── CITATION.cff                       # NEW — Data-in-Brief paper metadata (Cheesman + Arias; DOI pending)
├── CLAUDE.md                          # NEW lab notebook: pipeline table (Script | Does | Outputs | Knobs | Finding) with one row per numbered workflow script, incl. Caution rows (pre-fix network-of-record, strict NoData rule)
├── EXTERNAL_DATA.md                   # rewritten from A/EXTERNAL_DATA.md — drops the stale "present on disk" claims; documents the 4.7GB GEE stack + ~7GB friction rasters as regenerable-only, with entry points
├── pyproject.toml                     # ONE distribution, src-layout, packages = [mmnet, friction_surface], r_oracle as package data; replaces A/requirements.txt, A/friction_surface/requirements-friction.txt, both mmnet-toolkit pyprojects, B/pyproject.toml
├── uv.lock                            # NEW — single pinned lockfile (house style: uv)
├── run_all.sh                         # NEW one-command reproduction: chains workflows 01->04, each stage gated on its inputs existing with a clear "regenerate via X" message when absent
├── .gitignore                         # merged, every line with a reason comment; reconciles A's blanket-geodata+negations regime with B's data/** regime; adds __MACOSX/, example_skills/, *.egg-info, .venv
├── .gitattributes                     # NEW — git-lfs tracking: inputs/*.zip, final_network/*.zip
├── .github/
│   └── workflows/ci.yml               # NEW — uv sync; ruff; pytest tests/; mmnet validate_profile on workflows/02_network_build/profile.yaml; workflow-03 dry-run ingest (extract zips + load_final_network --dry-run validates the 82,300/90,921 inventory from committed data)
├── .claude/
│   └── skills/                        # all 6 playbooks, internal paths updated to src/ + workflows/
│       ├── align-to-ak-stack/         # from A (SKILL.md + scripts/align_raster.py)
│       ├── assign-friction-values/    # from A
│       ├── derive-fuel-costs/         # from A (check_cost_invariants.py, cost_derivation_tools.py)
│       ├── run-friction-pipeline/     # from A (validate_friction_stack.py — stale "writes DuckDB" docstring fixed)
│       ├── define-network-profile/    # from mmnet-toolkit/skills
│       └── build-and-verify-network/  # from mmnet-toolkit/skills
├── inputs/                            # HARD CONSTRAINT: every input dataset in one top-level folder (A's pattern extended to cover B)
│   ├── README.md                      # merged provenance: A/inputs/README.md + NEW section covering network_raw.zip (URLs: AEA, AKDOT, GRIP4, USACE NWN, TIGER) + data-redistribution terms
│   ├── bulk_fuel_data.zip             # LFS; repacked clean (strip __MACOSX/.DS_Store; Utilities_Bulk_Fuel_Inventory.csv normalized to LF — resolves the false "divergence")
│   ├── data_for_network_build.zip     # LFS; repacked clean (strip .DS_Store, __pycache__/build_map.cpython-39.pyc, Flights/.claude/settings.local.json); still feeds BOTH the corridor mask (workflow 01) and provenance
│   ├── region_and_census_data.zip     # LFS; as-is
│   ├── network_raw.zip                # NEW, LFS — B's until-now-uncommitted data/raw/**: Roads_AKDOT + GRIP4_canada, NWN Waterway_Network, Ice_Roads, TIGER places/cousub/boroughs, Ports_and_Harbors.geojson, facilities CSV, Fuel_Delivery_Method; 'Flight Paths.xlsx' -> flight_paths.xlsx
│   ├── air/                           # small tracked plain files (diffable): airports_ak_dotpf.csv, flight_paths_combined.csv
│   ├── gee_exports/                   # GITIGNORED (# 4.7GB AK_Stack_150m.zip — exceeds GitHub limit; regenerate via src/friction_surface/friction_preprocessing GEE script)
│   └── friction_rasters/              # GITIGNORED (# ~7GB slope/lulc/permafrost + sea_ice/ + river_ice/ — regenerable from gee_exports + arcpy river-ice pipeline); was friction_surface/friction_inputs/
├── src/                               # installable library code — `uv pip install -e .`
│   ├── mmnet/                         # THE single canonical engine — promoted from A/mmnet-toolkit/mmnet (newest copy: reset_index mis-snap fix, scoped warnings, py<3.10 typing, nullable-string fix); B's two copies DROPPED
│   │   ├── README.md                  # from mmnet-toolkit/README.md, reframed as package doc
│   │   ├── __init__.py  config.py  pipeline.py  build.py  assemble.py  connect_extras.py  network.py  inspect.py  io_readers.py  io_writers.py  viz.py
│   │   ├── steps/                     # consolidate.py  tag.py  hubs.py  __init__.py
│   │   └── r_oracle/                  # build_network.R  lib.R  CONTRACT.md (contract_version '2') — shipped as package data
│   └── friction_surface/              # A's package, moved under src/ mostly as-is
│       ├── README.md                  # was README_friction.md — stale burn-in / viz-dir / env-default sections fixed
│       ├── __init__.py  friction_config.py  friction_costs.py  friction_paths.py  friction_io.py  friction_preflight.py  friction_surface.py  run_friction_pipeline.py  check_grid_exports.py
│       │                              # friction_paths.py edits: PROJECT_ROOT for src-layout; defaults RASTER_DIR=inputs/friction_rasters, mask/output paths under outputs/; dead ROAD_MASK/ICE_ROAD_MASK + broken FUEL_DELIVERY_METHOD_CSV constants removed
│       ├── pipeline_utils.py          # was root pipeline.py (setup_logging)
│       ├── friction_preprocessing/    # align_permafrost.py, river_ice_full_pipeline.py (arcpy), build_brown_polygon_mask.py, pad_sea_ice_to_grid.py, pad_river_ice_to_grid.py, plot_river_ice_provenance.py, gee_friction_layer_multi_data_processing.js (typo fixed), README.md (drift fixed)
│       └── qa/                        # qa_friction_stack.py, qa_river_ice_thresholds.py, compare_lulc_grids.py, __init__.py (committed PNG relocated to outputs/analysis/)
├── workflows/                         # thin numbered drivers — the repo's narrative spine
│   ├── 01_friction_build/             # (a) friction-layer build
│   │   ├── README.md                  # run order INCLUDING the corridor-mask step (fixes the severed-barge-edges doc bug) + pointers to external GEE/ArcGIS preprocessing
│   │   ├── 00_preflight_inputs.py     # thin driver -> friction_surface.check_grid_exports + friction_preflight
│   │   ├── 01_build_corridor_masks.py # was A/build_corridor_masks.py — writes outputs/01_friction_build/waterway_mask_150m.tif
│   │   ├── 02_build_friction_stack.py # thin driver -> friction_surface.run_friction_pipeline (overland, road_base, barge_01..12 -> outputs/01_friction_build/friction_stack/)
│   │   ├── 03_qa_friction_stack.py    # thin driver -> friction_surface.qa.qa_friction_stack (14-file contract, ice gating, value floor)
│   │   ├── viz/                       # was friction_surface/viz_scripts/*.py: plot_friction_stack, plot_combined_friction, generate_grid_schema(_public), generate_pipeline_diagram, plot_sea_ice_padding
│   │   └── run_all.sh
│   ├── 02_network_build/              # (b) spatial-network build (mmnet engine + profile)
│   │   ├── README.md                  # correct run order incl. prep_waterway + fetch_basemap (fixes B's README gaps); names the downstream consumer
│   │   ├── profile.yaml               # THE single config surface for this stage (was B root copy; the 2 example duplicates DROPPED)
│   │   ├── 00_normalize_raw.py        # was B/scripts/normalize_raw.py (SPEC table; reads inputs/network_raw.zip extraction)
│   │   ├── 01_prep_waterway.py        # was B/scripts/prep_waterway.py
│   │   ├── 02_prep_airways.py         # was B/scripts/prep_airways.py (stale raw-path docstring fixed)
│   │   ├── 03_fetch_basemap.py        # was B/scripts/fetch_basemap.py (Natural Earth, figures only)
│   │   ├── 04_build_network.py        # NEW ~15-line driver: validate_profile + mmnet.run_pipeline('profile.yaml') (stages 01->04 + reports)
│   │   ├── 05_verify_north_slope.py   # was B/explain/verify_north_slope.py — the assertion gate, rescued from the "disposable" folder
│   │   ├── 06_export_final_network.py # was B/scripts/export_final_shapefile.py — sys.path hack dropped; now ALSO zips into final_network/*.zip + writes sha256 manifest (closes the undocumented manual handoff)
│   │   ├── preprocessing/build_flight_map.py  # was B data/raw/connectivity/air/build_map.py (code out of the data tree)
│   │   ├── viz/                       # export_qgis.py, export_qgis_components.py, plot_network.py, plot_components.py, plot_join.py, plot_paper_network.py
│   │   └── run_all.sh                 # was B/scripts/run_all.sh — updated paths; export step added; no longer depends on explain/
│   ├── 03_multimodal_join/            # (c) join network + friction -> weighted multimodal edges (writes fuel_network.duckdb incrementally, as the code already does)
│   │   ├── README.md                  # stage contract: edge_id = shapefile row order; EXPECTED inventory; strict any-NoData-impassable rule
│   │   ├── 01_extract_network_handoff.py  # NEW ~20 lines: unzips final_network/*.zip into gitignored subdirs (fixes the fresh-clone FileNotFoundError)
│   │   ├── 02_load_final_network.py   # was A/load_final_network.py — network_nodes/network_edges + inventory validation + edge_class derivation
│   │   ├── 03_weight_network_edges.py # was A/weight_network_edges.py — 75 m sampling of road_base/barge rasters -> edge_month_weights
│   │   ├── 04_assemble_weighted_graph.py  # was A/assemble_weighted_graph.py — EDIT: duplicated FEE_MODE/_lookup_fee/infer_transfer_fees deleted, imported from friction_surface.friction_costs; -> edge_costs + nx.MultiGraph
│   │   └── viz/make_network_plots.py  # was A/make_network_plots.py (3 PNGs from the shapefiles)
│   └── 04_duckdb_export/              # (d) the DuckDB deliverable: certify + document outputs/fuel_network.duckdb
│       ├── README.md                  # full schema contract: network_nodes, network_edges, edge_month_weights (1,091,052), edge_costs; hub_facility_map documented as future work (no writer exists)
│       ├── 01_run_validation_queries.py   # was A/run_validation_query.py (monthly passability by mode)
│       └── 02_inspect_schema.py       # was A/query_duckdb.py
├── final_network/                     # the frozen network-of-record handoff between workflows 02 and 03
│   ├── README.md                      # MERGE of both repos' versions: field dictionary + inventory + sha256 checksums + explicit note it was built with the PRE-reset_index-fix engine; regenerate section now points at workflows/02_network_build
│   ├── network_joined_edges.zip       # LFS; from A (byte-identical member shapefiles preserved — edge_id contract depends on it; only __MACOSX junk stripped, member md5s verified)
│   └── network_joined_nodes.zip       # LFS; ditto  (extracted network_joined_{nodes,edges}/ dirs gitignored — # regenerated by 03/01_extract)
├── outputs/                           # gitignored by default; committed deliverables opted in per outputs/README.md contract
│   ├── README.md                      # rewritten deliverable table (File | Producer stage | Content); stale road/ice-road-mask section deleted
│   ├── 01_friction_build/             # GITIGNORED (# ~288MB friction stack + waterway mask, regenerated by workflow 01)
│   ├── 02_network_build/              # GITIGNORED (# 01..04 gpkg stages + reports + qgz, regenerated by workflow 02)
│   ├── fuel_network.duckdb            # GITIGNORED (# ~30MB, regenerated by workflows 03-04)  [DB_PATH edit in 4 scripts]
│   ├── analysis/                      # committed QA/sensitivity deliverables from A (+ relocated lulc_fast_vs_exact_disagreement.png)
│   ├── figures/                       # committed publication figures from A + relocated friction_pipeline_diagram.pdf, sea_ice_padding png
│   │   └── scripts/                   # plot_weighted_network.py, plot_hub_network.py, plot_reference_grid.py (A's deliberate generator-beside-output pairing kept)
│   ├── final_network_plots/           # committed: 01_statewide_overview.png, 02_connectors_detail.png, 03_hubs.png
│   └── tables/                        # committed xlsx + their generators (build_combined_friction_tables.py, build_input_datasets_xlsx.py)
├── tests/
│   └── test_friction_surface.py       # was friction_surface/tests/ — run by CI; room for mmnet smoke tests later
├── docs/
│   ├── ARCHITECTURE.md                # from B — air-data section corrected; paths updated to merged layout
│   ├── API.md                         # regenerated by tools/gen_api_docs.py against src/mmnet
│   ├── DATA_CONTRACTS.md              # NEW — every inter-stage contract in one page: 150m grid spec, 14-file friction-stack contract, R WORKDIR contract v2, shapefile handoff schema, edge_id=row-order rule, DuckDB schema
│   ├── JETSTREAM_SETUP.md             # from A/setup/ (stale drag-and-drop section pruned)
│   └── provenance/Alaska_Fuel_Hubs_Transport_Network.md  # was B/data/_archive/ (source report)
├── research/                          # B's tracked decision-record sandboxes, as-is (already house-style NN_+FINDINGS.md): airport_connection/ flights_network/ ice_ice_connect/ multimodal_network/ param_check/ road_ice_connect/ road_road_connect/ waterway_network/ (out/ dirs gitignored)
├── supplementary/                     # from A, as-is
│   ├── cost-derivations/              # 00..06 md + build_pdf.py + build_transfer_pdf.py + transfer_fees.pdf (regenerable combined.html/transfer_fees.html DROPPED)
│   └── cost-verification/             # fuel_cost_blind_derivations.pdf (renamed, no spaces) + Fuel Cost Derivation Verification.md -> derivation_verification.md
└── tools/
    ├── extract_inputs.py              # NEW — unzips inputs/*.zip into gitignored working dirs (one gate for workflows 01 and 02)
    ├── build_notebooks.py             # was B/scripts/build_notebooks.py — EDIT: relative project root (committed .ipynb DROPPED; regenerable)
    └── gen_api_docs.py                # was B/scripts/gen_api_docs.py
```

## File mapping (old -> new)

- === REPO A = alaska-fuel-spatial-network, REPO B = alaska_network_mmnet ===
- A/README.md -> MERGE into README.md (new 4-stage narrative; stale --skip-surfaces / 'extracts the zips' / AK_Stack path claims dropped)
- A/STRUCTURE.md -> DROP (superseded by README + annotated tree)
- A/EXTERNAL_DATA.md -> EXTERNAL_DATA.md (rewritten; stale on-disk claims removed)
- A/.gitignore -> MERGE into .gitignore (reason comments per line)
- A/requirements.txt -> DROP (MERGE into pyproject.toml + uv.lock)
- A/pipeline.py -> src/friction_surface/pipeline_utils.py (setup_logging; importers updated)
- A/build_corridor_masks.py -> workflows/01_friction_build/01_build_corridor_masks.py
- A/load_final_network.py -> workflows/03_multimodal_join/02_load_final_network.py
- A/weight_network_edges.py -> workflows/03_multimodal_join/03_weight_network_edges.py
- A/assemble_weighted_graph.py -> workflows/03_multimodal_join/04_assemble_weighted_graph.py (MERGE: duplicated fee block deleted, imports friction_surface.friction_costs)
- A/make_network_plots.py -> workflows/03_multimodal_join/viz/make_network_plots.py
- A/run_validation_query.py -> workflows/04_duckdb_export/01_run_validation_queries.py
- A/query_duckdb.py -> workflows/04_duckdb_export/02_inspect_schema.py
- A/friction_surface/{__init__,friction_config,friction_costs,friction_paths,friction_io,friction_preflight,friction_surface,run_friction_pipeline,check_grid_exports}.py -> src/friction_surface/<same> (friction_paths: src-layout root + new default dirs; dead ROAD_MASK/ICE_ROAD_MASK + broken FUEL_DELIVERY_METHOD_CSV constants removed)
- A/friction_surface/README_friction.md -> src/friction_surface/README.md (stale burn-in/viz-dir/env-default sections fixed)
- A/friction_surface/requirements-friction.txt -> DROP (unified pyproject)
- A/friction_surface/friction_preprocessing/{__init__.py,README.md,align_permafrost.py,build_brown_polygon_mask.py,pad_river_ice_to_grid.py,pad_sea_ice_to_grid.py,plot_river_ice_provenance.py,river_ice_full_pipeline.py} -> src/friction_surface/friction_preprocessing/<same> (README drift fixed)
- A/friction_surface/friction_preprocessing/gee_friction_layer_mutli_data_processing.js -> src/friction_surface/friction_preprocessing/gee_friction_layer_multi_data_processing.js (typo fixed)
- A/friction_surface/qa/{__init__.py,qa_friction_stack.py,qa_river_ice_thresholds.py,compare_lulc_grids.py} -> src/friction_surface/qa/<same>
- A/friction_surface/qa/lulc_fast_vs_exact_disagreement.png -> outputs/analysis/lulc_fast_vs_exact_disagreement.png (artifact out of source dir)
- A/friction_surface/tests/{__init__.py,test_friction_surface.py} -> tests/test_friction_surface.py (__init__ DROP)
- A/friction_surface/viz_scripts/{plot_friction_stack,plot_combined_friction,generate_grid_schema,generate_grid_schema_public,generate_pipeline_diagram,plot_sea_ice_padding}.py -> workflows/01_friction_build/viz/<same> (module docstring paths fixed); viz_scripts/__init__.py DROP
- A/friction_surface/viz_scripts/friction_pipeline_diagram.pdf -> outputs/figures/friction_pipeline_diagram.pdf
- A/friction_surface/viz_scripts/sea_ice_padding_vs_data_03_Mar.png -> outputs/figures/sea_ice_padding_vs_data_03_Mar.png
- A/inputs/README.md -> inputs/README.md (MERGE with new network_raw provenance + data-terms section)
- A/inputs/bulk_fuel_data.zip -> inputs/bulk_fuel_data.zip (LFS; repacked: junk stripped, facilities CSV LF-normalized)
- A/inputs/data_for_network_build.zip -> inputs/data_for_network_build.zip (LFS; repacked: .DS_Store, __pycache__ .pyc, Flights/.claude/settings.local.json stripped)
- A/inputs/region_and_census_data.zip -> inputs/region_and_census_data.zip (LFS)
- A/final_network/README.md -> final_network/README.md (MERGE with B/final_network/README.md; + sha256 manifest + pre-fix-engine provenance note)
- A/final_network/network_joined_edges.zip -> final_network/network_joined_edges.zip (LFS; member shapefiles byte-identical — edge_id contract)
- A/final_network/network_joined_nodes.zip -> final_network/network_joined_nodes.zip (LFS; ditto)
- A/mmnet-toolkit/mmnet/** (18 files: __init__.py, assemble.py, build.py, config.py, connect_extras.py, inspect.py, io_readers.py, io_writers.py, network.py, pipeline.py, viz.py, steps/{__init__,consolidate,hubs,tag}.py, r_oracle/{build_network.R,lib.R,CONTRACT.md}) -> src/mmnet/** (CANONICAL copy — carries all 4 bugfixes)
- A/mmnet-toolkit/README.md -> src/mmnet/README.md (reframed as package doc)
- A/mmnet-toolkit/pyproject.toml -> MERGE into pyproject.toml
- A/mmnet-toolkit/.gitignore -> DROP
- A/mmnet-toolkit/examples/alaska/{README.md,profile.yaml,verify_north_slope.py} -> DROP (duplicates of workflows/02_network_build/{profile.yaml,05_verify_north_slope.py})
- A/mmnet-toolkit/skills/define-network-profile/SKILL.md -> .claude/skills/define-network-profile/SKILL.md
- A/mmnet-toolkit/skills/build-and-verify-network/SKILL.md -> .claude/skills/build-and-verify-network/SKILL.md
- A/.claude/skills/align-to-ak-stack/{SKILL.md,scripts/align_raster.py} -> .claude/skills/align-to-ak-stack/<same> (paths updated to src/)
- A/.claude/skills/assign-friction-values/SKILL.md -> .claude/skills/assign-friction-values/SKILL.md (paths updated)
- A/.claude/skills/derive-fuel-costs/{SKILL.md,scripts/check_cost_invariants.py,scripts/cost_derivation_tools.py} -> .claude/skills/derive-fuel-costs/<same> (paths updated)
- A/.claude/skills/run-friction-pipeline/{SKILL.md,scripts/validate_friction_stack.py} -> .claude/skills/run-friction-pipeline/<same> (stale 'writes DuckDB' docstring fixed)
- A/outputs/README.md -> outputs/README.md (rewritten deliverable table; stale mask-TIF section deleted)
- A/outputs/analysis/{_lulc_edge_sensitivity.json,_lulc_sensitivity_buffer.json,_lulc_sensitivity_results.json,_road_grade_distribution.json,lulc_sensitivity_test.md,road_grade_distribution.md} -> outputs/analysis/<same>
- A/outputs/figures/*.{png,pdf} (14 committed figures incl. weighted_network_monthly* variants, ak_stack_150m_reference_grid, idw_*, regions.png) -> outputs/figures/<same>
- A/outputs/figures/scripts/{plot_weighted_network.py,plot_hub_network.py,plot_reference_grid.py} -> outputs/figures/scripts/<same> (DB path updated to outputs/fuel_network.duckdb)
- A/outputs/final_network_plots/{01_statewide_overview,02_connectors_detail,03_hubs}.png -> outputs/final_network_plots/<same>
- A/outputs/tables/{build_combined_friction_tables.py,build_input_datasets_xlsx.py,combined_friction_tables.xlsx,friction_config.xlsx,input_datasets.xlsx} -> outputs/tables/<same>
- A/setup/installations.txt -> DROP (superseded by pyproject/uv.lock)
- A/setup/JETSTREAM_SETUP_GUIDE.md -> docs/JETSTREAM_SETUP.md (stale transfer section pruned)
- A/supplementary/cost-derivations/{00_executive_summary..06_connection_costs}.md + build_pdf.py + build_transfer_pdf.py + transfer_fees.pdf -> supplementary/cost-derivations/<same>
- A/supplementary/cost-derivations/{combined.html,transfer_fees.html} -> DROP (regenerable build products)
- A/supplementary/cost-verification/'Fuel Cost Blind Derivations.pdf' -> supplementary/cost-verification/fuel_cost_blind_derivations.pdf (space-free rename)
- A/supplementary/cost-verification/'Fuel Cost Derivation Verification.md' -> supplementary/cost-verification/derivation_verification.md
- B/README.md -> MERGE into README.md + docs/ARCHITECTURE.md (stale air-data story corrected)
- B/.gitignore -> MERGE into .gitignore
- B/pyproject.toml -> MERGE into pyproject.toml
- B/profile.yaml -> workflows/02_network_build/profile.yaml (THE canonical copy)
- B/mmnet/** (18 files) -> DROP (oldest copy, NETWEAVE_*-only, lacks bugfixes; superseded by src/mmnet; history preserved via merge — this is the copy that built the frozen network-of-record, documented in final_network/README.md)
- B/mmnet-toolkit/** (26 files) -> DROP (middle copy; skills + example already mapped from A's toolkit)
- B/scripts/normalize_raw.py -> workflows/02_network_build/00_normalize_raw.py
- B/scripts/prep_waterway.py -> workflows/02_network_build/01_prep_waterway.py
- B/scripts/prep_airways.py -> workflows/02_network_build/02_prep_airways.py (stale docstring paths fixed)
- B/scripts/fetch_basemap.py -> workflows/02_network_build/03_fetch_basemap.py
- B/scripts/export_final_shapefile.py -> workflows/02_network_build/06_export_final_network.py (sys.path hack dropped; + zip + sha256 manifest step added)
- B/scripts/run_all.sh -> workflows/02_network_build/run_all.sh (paths updated; export step added; explain/ dependency removed)
- B/scripts/export_qgis.py -> workflows/02_network_build/viz/export_qgis.py
- B/scripts/export_qgis_components.py -> workflows/02_network_build/viz/export_qgis_components.py
- B/scripts/plot_network.py -> workflows/02_network_build/viz/plot_network.py
- B/scripts/plot_components.py -> workflows/02_network_build/viz/plot_components.py
- B/scripts/plot_join.py -> workflows/02_network_build/viz/plot_join.py
- B/scripts/plot_paper_network.py -> workflows/02_network_build/viz/plot_paper_network.py
- B/scripts/build_notebooks.py -> tools/build_notebooks.py (baked absolute ROOT replaced with relative resolution)
- B/scripts/gen_api_docs.py -> tools/gen_api_docs.py
- B/scripts/extract_od_table.py -> DROP (dead: broken output path, superseded by flight_paths_combined.csv)
- B/explain/verify_north_slope.py -> workflows/02_network_build/05_verify_north_slope.py
- B/explain/{README.md,_trace.py,explain00_normalize.py,explain01_consolidate.py,explain01b_tag.py,explain02_hubs.py,explain03_build.py,explain04_multimodal.py,explain05_join.py,run_all.sh} -> DROP (self-declared disposable walkthroughs; narration survives in docs/ARCHITECTURE.md + research/)
- B/notebooks/{01_consolidate,01b_tag,02_hubs,03_build,04_join,05_run_pipeline}.ipynb -> DROP (generated artifacts with baked /home/diegoarias paths; regenerable via tools/build_notebooks.py)
- B/docs/ARCHITECTURE.md -> docs/ARCHITECTURE.md (air section + paths updated)
- B/docs/API.md -> docs/API.md (regenerated against src/mmnet)
- B/final_network/README.md -> MERGE into final_network/README.md
- B/data/_archive/Alaska_Fuel_Hubs_Transport_Network.md -> docs/provenance/Alaska_Fuel_Hubs_Transport_Network.md
- B/data/raw/connectivity/air/airports_ak_dotpf.csv -> inputs/air/airports_ak_dotpf.csv
- B/data/raw/connectivity/air/flight_paths_combined.csv -> inputs/air/flight_paths_combined.csv
- B/data/raw/connectivity/air/'Flight Paths.xlsx' -> inside inputs/network_raw.zip as air/flight_paths.xlsx (space-free)
- B/data/raw/connectivity/air/build_map.py -> workflows/02_network_build/preprocessing/build_flight_map.py (code out of the data tree)
- B/research/** (all 8 sandboxes, ~60 tracked files: airport_connection, flights_network, ice_ice_connect, multimodal_network, param_check, road_ice_connect, road_road_connect, waterway_network — scripts, cores, _trace.py, FINDINGS/README md) -> research/<same, unchanged> (out/ dirs stay gitignored; waterway_network/README 'bbox clip' staleness noted in CLAUDE.md)
- B/data/raw/** UNTRACKED on-disk source data (Roads_AKDOT shp+dbf, GRIP4_canada, NWN Waterway_Network, Ice_Roads, Ports_and_Harbors.geojson + ports gpkg, TIGER places/county-subdivisions/borough_census_area, Utilities_Bulk_Fuel_Inventory.csv, Fuel_Delivery_Method.geojson) -> packed into NEW inputs/network_raw.zip (LFS) — first committed copy anywhere; junk (zips-in-zip, .DS_Store) excluded
- B/data/{interim,processed,basemap,boundary.geojson}, B/output/**, B/reports/**, B/research/**/out/, B/.venv, B/*egg-info, B/example_skills/, B/output/coach/ -> DROP (derived/junk; regenerated by workflows 02 scripts 00-06)
- A untracked/absent friction rasters (friction_inputs, gee_exports, friction_outputs, fuel_network.duckdb) -> not assets to migrate: gitignored target paths inputs/friction_rasters/, inputs/gee_exports/, outputs/01_friction_build/, outputs/fuel_network.duckdb
- NEW files: LICENSE, CITATION.cff, CLAUDE.md, uv.lock, run_all.sh, .gitattributes, .github/workflows/ci.yml, docs/DATA_CONTRACTS.md, tools/extract_inputs.py, workflows/01_friction_build/{README.md,00_preflight_inputs.py,02_build_friction_stack.py,03_qa_friction_stack.py,run_all.sh}, workflows/02_network_build/{README.md,04_build_network.py}, workflows/03_multimodal_join/{README.md,01_extract_network_handoff.py}, workflows/04_duckdb_export/README.md, inputs/network_raw.zip

## Migration steps (ordered)

- SAFETY NET FIRST: alaska_network_mmnet has NO remote — create a private backup remote and push master (plus `git tag pre-merge-2026-08`); tag alaska-fuel-spatial-network main the same way. Delete the fully-merged feat/param-eval branch in B (verified: zero unmerged commits).
- Decide the publishing home (open question 1). Steps below assume a NEW GitHub repo `alaska-fuel-multimodal-network` so LFS history-rewrite is free; the old jccheesman repo gets archived with a pointer README.
- Prepare repo B for import: clone a throwaway copy; `git filter-repo` to drop mmnet-toolkit/, notebooks/*.ipynb, explain/ (except verify_north_slope.py), scripts/extract_od_table.py. Do NOT path-rename in filter-repo — do renames as ordinary `git mv` commits later so history stays legible.
- In a clone of repo A (branch `merge-restructure`): `git remote add mmnet <path-to-filtered-B>` ; `git fetch mmnet` ; `git merge mmnet/master --allow-unrelated-histories` (only collisions: README.md, .gitignore, final_network/README.md, pyproject-adjacent files — resolve per mapping). Both authors' histories survive.
- Apply the A-side moves with `git mv` per the file_mapping: friction_surface -> src/friction_surface (+ pipeline.py -> pipeline_utils.py, tests -> tests/, viz_scripts -> workflows/01_friction_build/viz/), root stage scripts -> workflows/03,04, mmnet-toolkit/mmnet -> src/mmnet, toolkit skills -> .claude/skills/. Delete B's mmnet/ and mmnet-toolkit/ trees and the two duplicate profile.yaml/verify_north_slope copies in the same commit, with a commit message naming src/mmnet as canonical and listing the 4 bugfixes it carries.
- Apply the B-side moves: scripts/* -> workflows/02_network_build/{00..06,viz/}, profile.yaml -> workflows/02_network_build/, explain/verify_north_slope.py -> 05_verify_north_slope.py, docs + provenance moves, build_map.py out of data/raw.
- Build the data layer: (a) repack A's three inputs zips stripping __MACOSX/.DS_Store/.pyc/.claude junk and LF-normalizing Utilities_Bulk_Fuel_Inventory.csv (verify row/column identity before and after — the 'divergence' is line-endings only); (b) create inputs/network_raw.zip from B's on-disk data/raw/** (rename 'Flight Paths.xlsx' -> flight_paths.xlsx; keep it under 100MB — expect ~60MB given the AKDOT source zip was 32MB); (c) move the two tracked air CSVs to inputs/air/; (d) repack final_network zips ONLY to strip __MACOSX, verifying member md5s unchanged (edge_id = row order depends on byte-identical shapefiles); (e) write the sha256 manifest into final_network/README.md.
- Set up LFS BEFORE the first push: `.gitattributes` tracking inputs/*.zip and final_network/*.zip; `git lfs migrate import --include='inputs/*.zip,final_network/*.zip' --everything` (safe here because the target is a new repo; skip migrate and use plain tracking if the owner insists on keeping the existing remote un-rewritten).
- Unify the environment: write root pyproject.toml (single distribution, src-layout, packages mmnet + friction_surface, r_oracle/*.{R,md} as package data, deps = union of A/requirements.txt + toolkit pyproject + nbformat/pyogrio); `uv venv && uv sync && uv pip install -e .`; delete requirements.txt, requirements-friction.txt, both toolkit pyprojects, B/pyproject.toml.
- Make the enumerated small code edits (keep-as-is everywhere else): (1) friction_paths.py — src-layout PROJECT_ROOT, defaults RASTER_DIR=inputs/friction_rasters, FRICTION_DIR=outputs/01_friction_build/friction_stack, WATERWAY_MASK_TIF=outputs/01_friction_build/waterway_mask_150m.tif; delete dead ROAD_MASK/ICE_ROAD_MASK and broken FUEL_DELIVERY_METHOD_CSV constants; (2) DB_PATH -> outputs/fuel_network.duckdb in 02_load/03_weight/04_assemble + plot_weighted_network.py; (3) 04_assemble_weighted_graph.py imports FEE_MODE/_lookup_fee/infer_transfer_fees from friction_surface.friction_costs, duplicated block deleted; (4) `from pipeline import setup_logging` -> `from friction_surface.pipeline_utils import setup_logging` in the movers; (5) 06_export_final_network.py drops the sys.path hack, adds zip+sha256; (6) tools/build_notebooks.py relative root; (7) fix stale docstrings (prep_airways, validate_friction_stack, generate_pipeline_diagram, build_corridor_masks --only help).
- Write the NEW thin drivers and helpers: workflows/01_friction_build/{00_preflight_inputs.py,02_build_friction_stack.py,03_qa_friction_stack.py} (each ~10 lines calling the package mains), workflows/02_network_build/04_build_network.py, workflows/03_multimodal_join/01_extract_network_handoff.py, tools/extract_inputs.py, per-workflow run_all.sh, top-level run_all.sh with data-presence gates.
- Write the governing docs: README.md (4-stage narrative + quickstart + badges), docs/DATA_CONTRACTS.md (grid spec, 14-file friction contract, R WORKDIR contract v2, handoff schema, edge_id rule, DuckDB schema), CLAUDE.md lab notebook seeded with one pipeline-table row per numbered script incl. Finding column (Caution row: network-of-record built pre-reset_index-fix), stage READMEs, rewritten outputs/README.md and EXTERNAL_DATA.md, merged inputs/README.md with source URLs and data-terms.
- Write the merged .gitignore with a reason comment on every line (inputs/gee_exports '# 4.7GB, exceeds GitHub limit, regenerable in GEE'; inputs/friction_rasters '# ~7GB regenerable'; outputs/01_*,02_* '# derived, regenerated by workflow NN'; final_network/*/ '# regenerated by 03/01_extract'; *.duckdb, .venv, *.egg-info, __pycache__, __MACOSX, .DS_Store, example_skills/).
- Add governance files: LICENSE (owner picks), CITATION.cff (owner supplies paper metadata), .github/workflows/ci.yml running: uv sync; ruff check; pytest tests/; python -c mmnet validate_profile(workflows/02_network_build/profile.yaml); and the fresh-clone smoke = tools/extract_inputs is NOT needed for it: 03/01_extract_network_handoff.py + 03/02_load_final_network.py --dry-run (validates the 82,300/90,921 inventory purely from committed zips — the one end-to-end check that runs with no external data).
- Update .claude/skills paths (align-to-ak-stack reference layer -> inputs/friction_rasters/lulc.tif; run-friction-pipeline commands -> workflows/01_friction_build/*; derive-fuel-costs module paths -> src/friction_surface/friction_costs.py) and verify check_cost_invariants.py still passes against the moved module.
- Verify what is verifiable on this machine: pytest; validate_profile; workflow 03 steps 01-02 against the committed zips (counts must equal EXPECTED); ruff; `git ls-files` audit for junk (no __MACOSX, no .ipynb, no egg-info); `git gc`.
- Handle the external consumer: alaska_network_pipeline_mmnet's venv editable-installs the absolute path .../alaska_network_mmnet/mmnet-toolkit/mmnet and its run_arm.sh diffs ../alaska_network_mmnet/profile.yaml — do NOT delete the old B working directory; leave it frozen as a local archive, and (separately, later) re-point that project to `pip install -e <new-repo>` per open question 5.
- Publish: create the new GitHub repo, push merge-restructure as main, enable LFS, add repo description/topics, archive jccheesman/alaska-fuel-spatial-network with a forwarding note (or repurpose it — owner decision). Do all pushes only after the owner signs off (house rule: never push unasked).

## Risks

- Frozen-vs-rebuilt network: src/mmnet (with the reset_index mis-snap fix) can no longer reproduce final_network/*.zip bit-for-bit; anyone who reruns workflow 02 gets a (slightly) different network whose counts break 03's EXPECTED inventory and whose row order breaks every edge_id-keyed table. Mitigated by the provenance note + checksums, but it is a standing trap until a deliberate rebuild-and-requantify happens.
- The friction half cannot be smoke-tested on this machine (no copy of AK_Stack_150m.zip or friction_inputs exists anywhere here), so the friction_paths.py edits (src-layout root, new default dirs, chdir behavior) ship unverified end-to-end; a path mistake would only surface on Julia's machine or after a full GEE regeneration.
- friction_paths' import-time os.chdir side effect interacts with scripts now living two directories deep in workflows/; if kept, all relative writes still pin to repo root (intended), but any script that avoids importing friction_surface (as load_final_network did) can write the DuckDB elsewhere — the DB_PATH edits must be absolute-anchored, not relative.
- Repacking zips risks breaking the edge_id contract: final_network zip members must remain byte-identical (verify md5s), and the LF-normalization of the facilities CSV must be proven content-neutral (it is line-endings-only per the audit, but the check belongs in the migration).
- inputs/network_raw.zip may not be publicly redistributable (AKDOT roads terms, USACE NWN, AEA inventory); if any source forbids redistribution the zip must become a fetch script + MANIFEST of sha256s, which weakens the runnable-from-clone story.
- LFS history rewrite (or a fresh repo) invalidates existing clones/links to jccheesman/alaska-fuel-spatial-network; if the Data-in-Brief manuscript already cites that URL, archiving-with-pointer is mandatory and the paper link may need updating.
- The sibling TAPS project (alaska_network_pipeline_mmnet) editable-installs B's mmnet-toolkit by absolute path and diffs B's profile.yaml; deleting or moving the old working trees breaks it. The plan freezes the old dirs on disk, but that leaves three mmnet copies alive on the machine until TAPS is re-pointed.
- Two-author merge: repo A history is Julia's ([email redacted]), repo B is Diego's; merging unrelated histories into one public repo needs her sign-off on attribution, the publishing account, and archiving her repo.
- Path-reference sprawl: six .claude skills, four stage READMEs, docs/ARCHITECTURE.md, and the notebooks generator all hard-reference old paths; any missed reference leaves a stale doc of exactly the kind both audits flagged. A post-move `grep -r 'friction_surface/friction_inputs\|mmnet-toolkit\|scripts/run_all'` sweep is part of step 16 but remains the likeliest source of residual drift.
- Renaming pipeline scripts (load_final_network.py -> 02_load_final_network.py etc.) breaks muscle memory and any external notes/paper text that cite the old commands; the README must carry an old->new command table for one release cycle.

## Open questions for the owners

- Publishing home and continuity: new repo under which account/org (jccheesman, Diego, or a lab org)? Archive jccheesman/alaska-fuel-spatial-network with a pointer, or force-push the merged history into it? Julia's sign-off is required either way.
- License: which code license (MIT/BSD/Apache), and are the committed AEA/AKDOT/USACE/TIGER-derived zips — especially the new network_raw.zip — cleared for public redistribution, or must they become fetch-scripts?
- CITATION.cff needs the paper's identity (title, author order, journal, DOI/preprint) — nothing in either repo states it.
- Freeze or rebuild: keep the pre-fix network-of-record as canonical for the paper (proposed), or rebuild with the fixed src/mmnet and re-derive EXPECTED counts, edge_month_weights, and edge_costs? A rebuild quantifies the mis-snap fix's actual impact but invalidates the shipped DuckDB lineage.
- mmnet's long-term home: fold into this repo permanently (proposed), or keep mmnet-toolkit as a separate installable repo that this repo and the TAPS comparison project both depend on? If the latter, src/mmnet becomes a pinned dependency instead. Also: when do you want alaska_network_pipeline_mmnet re-pointed?
- hub_facility_map / backfill_facility_edges stub: delete from the public release, or keep as documented future work for the routing paper? (No writer or mapping data exists anywhere on this machine.)
- research/ sandboxes (8 dirs, ~60 files): include in the public repo as decision records (proposed) or move to a private archive? Some READMEs describe superseded states.
- Notebooks: is dropping the six committed .ipynb (regenerable via tools/build_notebooks.py) acceptable, or do you want portable regenerated copies committed with .executed.ipynb alongside per house convention?
- The old repo-B working directory: after merge, keep it frozen on disk indefinitely for TAPS, or migrate TAPS promptly and delete? (Its backup remote from step 1 stays either way.)
- Jetstream guide and setup/ material: keep docs/JETSTREAM_SETUP.md in the public repo or drop as internal ops?
- Do you want the DuckDB stage split exactly as proposed (03 writes the DB as the code already does; 04 certifies/documents it), or should 04_assemble_weighted_graph move into workflows/04_duckdb_export so stage (d) is the writer of the final edge_costs table? Both are as-is-preserving; it's a narration choice.
