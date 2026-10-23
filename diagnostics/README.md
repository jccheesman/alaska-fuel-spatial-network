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
`paper/` (generators of the publication figures and tables).

## 01_friction_build

| Script | Question it answered | Where the answer lives | Runs? |
|---|---|---|---|
| `qa_river_ice_thresholds.py` | Which `RIVER_ICE_THRESHOLD`? Pixel histograms of the 12 monthly river-ice rasters at candidate cut-offs | `friction_config.py`, the `RIVER_ICE_THRESHOLD = 0.15` rationale | yes (needs `inputs/friction_rasters/river_ice/`) |
| `plot_river_ice_marine_leak.py` | Is a blocked barge cell real ice, or river ice leaking onto salt water through the nearest-neighbour fill? | The river-subset waterway mask (`WATERWAY_RIVER_MASK_TIF`, `friction_paths.py`): river ice may gate only river cells | yes (needs the friction stack + masks) |
| `plot_marine_clip.py` | What the marine clip removes from the river-ice polygon mask, and why only four polygons | `drop_marine_polygons()` in `friction_preprocessing/build_brown_polygon_mask.py` | **no** — reads `/tmp` intermediates of that investigation that were never committed; kept as the record of the figure |
| `plot_mask_construction.py` | How the river-ice interpolation mask is built, panel by panel, and whether the arcpy rasters agree with it | `friction_preprocessing/README.md` | yes (needs `friction_preprocessing/data/` + river-ice rasters) |
| `plot_sea_ice_padding.py` | Does padding the GEE sea-ice export to the full grid put zeros only where there is no data? | `friction_preprocessing/pad_sea_ice_to_grid.py` | yes (needs the raw + padded sea-ice rasters) |
| `compare_lulc_grids.py` | How much did the fast LULC export (nearest sample) change classes vs the exact majority reference? | Its own report (overall + per-class agreement) | yes, given the two LULC rasters (`--new` / `--old`) |

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
