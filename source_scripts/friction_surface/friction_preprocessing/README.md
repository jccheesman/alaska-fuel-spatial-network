# friction_preprocessing/

Everything that produces the five friction inputs in `inputs/friction_rasters/`:
the Earth Engine export script, the two in-place pad/align fixes, and the
river-ice chain (local Python, then ArcGIS Pro). The step-by-step procedure, with
the download links, is `DATA.md` §3.1; this file says what each script is.

**One name per file.** Every raster keeps the name its producer wrote, from the
download to the build; nothing is renamed on disk. The names are defined once in
`../friction_paths.py` (`RASTER_NAMES`, `sea_ice_name`, `river_ice_name`), and
`tests/test_friction_paths.py` checks that the two scripts here that cannot import
it (the GEE script and the arcpy script) spell them the same.

## Scripts

| File | Runs in | Produces |
|---|---|---|
| `gee_friction_layer_multi_data_processing.js` | GEE Code Editor | The four Earth Engine inputs, on the full-Alaska 150 m grid: `FABDEM_slope_150m_EPSG3338.tif`, `dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif` (the grid anchor), `permafrost_probability_150m_EPSG3338.tif`, `sea_ice_median_{MM}_{Mon}_150m_EPSG3338.tif` ×12. Edit only its `CONFIG` block (your project's asset ids). |
| `pad_sea_ice_to_grid.py` | local Python | Inserts the land-masked (east-cropped) sea-ice exports into the full grid, in place, keeping the originals in `sea_ice/gee_export/`. Idempotent. |
| `align_permafrost.py` | local Python | Reprojects the permafrost export (smaller area) onto the land-cover grid, in place. |
| `build_brown_polygon_mask.py` | local Python | Filters the statewide NHD to the thirty Brown et al. rivers: `brown_river_polygons/` (wide channels, with the salt-water polygons removed) and `brown_river_flowlines/` (centre lines). Re-run only if NHD or the Brown reach set changes. |
| `river_ice_full_pipeline.py` | ArcGIS Pro (`arcpy`, Windows) | The twelve `river_ice_probability_{MM}_150m_EPSG3338.tif`, interpolated from the Brown reach points inside the masks, aligned to the land-cover grid, written straight into `inputs/friction_rasters/river_ice/`. QA rasters and a browse mosaic go to `river_ice/provenance/`. |
| `plot_river_ice_provenance.py` | ArcGIS Pro | Figure of which fill stage produced each river cell (Jan / Apr / Oct). |
| `pad_river_ice_to_grid.py` | local Python | Not part of a fresh run: lifts the archived 2026-06 narrow-grid river-ice run (`inputs/friction_rasters/small_grid/river_ice/`) onto the full grid. |
| `gee_network_layers_preview.js` | GEE Code Editor | Not a friction input. Overlays the network's transport layers (roads, waterways, ports, ice roads) for a visual check; nothing downstream reads its output. |

## The river-ice working directory

River ice is interpolated in ArcGIS Pro from two things: the Brown et al. **reach
points** (raw data; one small public download, they say *how much* ice per reach
and month) and the two **river masks** (derived from the 5 GB USGS NHD; they say
*where* a river cell exists and which cells share a polygon median). The masks are
slow to rebuild, so they are committed as `inputs/river_ice/river_ice_sources.zip`;
`inputs/river_ice/SOURCE.md` describes each one field by field. Everything lives in
one folder, `inputs/river_ice_work/` (gitignored), which `python tools/extract_inputs.py`
fills from the zip:

```
inputs/river_ice_work/
  waterFilledMedians2000_2023.geojson   Brown et al. 2026 reach points — DOWNLOAD (doi:10.18739/A2SB3X15X)
  brown_river_polygons/brown_river_polygons.shp     from the zip; rebuilt by build_brown_polygon_mask.py only if NHD changes
  brown_river_flowlines/brown_river_flowlines.shp   from the zip; same
  NHD_extracted/Shape/                  USGS NHD Alaska (download, ~5 GB) — only to rebuild the masks
  tiger/cb_2023_us_state_500k.shp       optional, the Alaska outline for the provenance figure
```

Set `FRICTION_LAYER_ROOT` (or pass `--work-dir`) to use a folder elsewhere. The
arcpy scripts also need `RASTER_DIR` = the repository's `inputs/friction_rasters`
folder (the same variable `friction_paths.py` honours), because that is where
they read the grid anchor and write the output; it has no default.

## How to run

```bash
# A. Earth Engine: run the .js in the Code Editor, start the tasks, download the
#    files into inputs/friction_rasters/ (sea ice into sea_ice/) WITHOUT renaming.
#    Then, from the repo root with the project environment active:
python -m friction_surface.friction_preprocessing.pad_sea_ice_to_grid
python -m friction_surface.friction_preprocessing.align_permafrost
python -m friction_surface.check_grid_exports

# B. River ice, step 1: unpack the committed masks, then download the reach points into
#    inputs/river_ice_work/waterFilledMedians2000_2023.geojson (skip step 2 unless NHD changed)
python tools/extract_inputs.py
# B. River ice, step 2 (local Python; only to REBUILD the masks from a fresh NHD download):
python -m friction_surface.friction_preprocessing.build_brown_polygon_mask

# B. River ice, step 3 (ArcGIS Pro's Python, Windows):
#   set RASTER_DIR=C:\path\to\repo\inputs\friction_rasters
#   "C:\Program Files\ArcGIS\Pro\bin\Python\scripts\propy.bat" river_ice_full_pipeline.py

# C. Gate, then build (workflow 01):
python workflows/01_friction_build/00_preflight_inputs.py
```

## Related docs

- `../../../DATA.md` §1.4 (the five source datasets, with links) and §3.1 (the procedure)
- `../README.md` — the friction surface itself: what consumes these rasters and how
- `../../../docs/DATA_CONTRACTS.md` §1 — the canonical grid
- `../../../.claude/skills/align-to-ak-stack/` — snapping any other raster onto the grid
