# diagnostics/

Checks, audits and investigation plots from building the data. None of these runs
in a stage driver or CI (those checks live in their workflow). Each script here
answered a question at some point in the build; the table records which one and
where the answer went, so a finding never depends on rerunning the plot.

Rules (enforced in part by `tests/test_standalone_scripts.py`):

- **Runnable or retired.** A script here runs from a clone with the documented inputs,
  locates files through `repo_paths` / `friction_paths`, and imports absolutely. One that
  can't be made to run is deleted, with a pointer to the commit that still has it.
- **Output goes to `outputs/diagnostics/<stage>/`** (gitignored) unless the script
  documents another place. Nothing here writes into `inputs/` or a tracked output.
- **One row per script below.** Add the row when you add the script.

Not to be confused with `analysis/` (questions asked *of* the finished network) or
`figure_scripts/` (generators of the committed figures and tables).

## 00_inventory_qc

| Script | Question it answered | Where the answer lives | Runs? |
|---|---|---|---|
| `community_label_review.py` | Which inventory community labels are not DCRA community names, and what is each one? | `docs/inventory_notes/community_label_review_2026-11-16.md` + its sheet (written there with `--out`; open for the owner) | yes (needs the published table and `inputs/community_reference/`) |

## 01_friction_build

| Script | Question it answered | Where the answer lives | Runs? |
|---|---|---|---|
| `check_route_against_surface.py` | Does a line layer sit on valid pixels of a friction surface — and if not, WHY (land-cover class / sea ice / river-ice domain / off-grid; min-over-months separates land from ice)? The general form of workflow 02's `qa/00_check_manual_barge.py`, for drafts, audits and any mode; `--require-class marine` adds the nearshore water-label rule | the per-run table + failure points under `outputs/diagnostics/01_friction_build/`; primitives in `fuel_network.geo_checks` | yes (needs the friction stack; `--causes` needs `inputs/friction_rasters/`) |
| `qa_river_ice_thresholds.py` | Which `RIVER_ICE_THRESHOLD`? Pixel histograms of the 12 monthly river-ice rasters at candidate cut-offs | `friction_config.py`, the `RIVER_ICE_THRESHOLD = 0.15` rationale | yes (needs `inputs/friction_rasters/river_ice/`) |
| `plot_river_ice_marine_leak.py` | Is a blocked barge cell real ice, or river ice leaking onto salt water through the nearest-neighbour fill? | The river-subset waterway mask (`WATERWAY_RIVER_MASK_TIF`, `friction_paths.py`): river ice may gate only river cells | yes (needs the friction stack + masks) |
| `plot_marine_clip.py` | What the marine clip removes from the river-ice polygon mask, and why only four polygons | `drop_marine_polygons()` in `friction_preprocessing/build_brown_polygon_mask.py` | **no** — reads `/tmp` intermediates of that investigation that were never committed; kept as the record of the figure |
| `plot_mask_construction.py` | How the river-ice interpolation mask is built, panel by panel, and whether the arcpy rasters agree with it | `friction_preprocessing/README.md` | yes (needs `friction_preprocessing/data/` + river-ice rasters) |
| `plot_sea_ice_padding.py` | Does padding the GEE sea-ice export to the full grid put zeros only where there is no data? | `friction_preprocessing/pad_sea_ice_to_grid.py` | yes (needs the raw + padded sea-ice rasters) |
| `compare_lulc_grids.py` | How much did the fast LULC export (nearest sample) change classes vs the exact majority reference? | Its own report (overall + per-class agreement) | yes, given the two LULC rasters (`--new` / `--old`) |
| `compare_river_ice_stacks.py` | Did the river-ice rebuild change exactly what the plan predicted — truncation gone, coverage delta = old NN footprint + the 4 clipped polygons, corridor flips frozen-ward only? | `outputs/analysis/FRICTION_STACK_COMPARISON.md`, `river_ice_new_vs_old.csv` | yes, given the pre-rebuild backup (`--old-dir`, default `river_ice.bak_pre_rebuild`) |
| `nhd_river_marine_check.py` | Which NWN waterway segments are rivers according to NHD (and which FTypes can be trusted to say so)? | The `RIVER_SEGMENT_KEY_IDS` allowlist in `friction_config.py`; `docs/TEST_LOG.md` (2026-08-20) | yes (needs the ~5 GB NHD download under `inputs/river_ice_work/NHD_extracted/`) |
| `extract_barge_waterway.py` | Compact helper: per-month barge navigability over the 501,684 waterway cells, so stack comparisons don't re-read 464M-cell rasters | `outputs/analysis/barge_waterway_new.npz`, consumed by the stack comparison | yes (needs the friction stack) |
| `river_ice_interp.py` | Can the arcpy interpolation stages (polygon median → IDW → NN fallback) be reproduced in pure Python for parity checks? | `docs/TEST_LOG.md` (2026-08-21): a parity diagnostic, deliberately NOT wired into the pipeline | import-only module (no CLI) |

## 02_network_build

| Script | Question it answered | Where the answer lives | Runs? |
|---|---|---|---|
| `plot_network.py` | A static look at the stage-03 network without QGIS | — (a view, not a finding) | yes (needs `outputs/02_network_build/`) |

## 03_multimodal_join

| Script | Question it answered | Where the answer lives | Runs? |
|---|---|---|---|
| `audit_connector_modes.py` | Does every synthetic connector's type match the modes it joins, and does every cross-mode pair have a fee? | Exit code (gate it on a rebuild); `pipeline.classify_connectors` | yes (needs `outputs/fuel_network.duckdb`) |
| `make_network_plots.py` | Statewide / connector / hub views of the network-of-record | — (views); writes `outputs/final_network_plots/` | yes (needs the extracted `final_network/`) |
| `plot_edge_types.py` | Edges by type, statewide + small multiples | — (views); `outputs/final_network_plots/` | yes |
| `plot_connector_insets.py`, `plot_connector_callout.py` | One zoomed example per connector type, with a locator map | — (views); `outputs/final_network_plots/` | yes (needs `data/boundary.geojson`) |
