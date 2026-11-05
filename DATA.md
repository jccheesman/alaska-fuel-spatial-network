# DATA.md — from the original datasets to the deliverable

This is the one place that says where every dataset comes from, where it lives in
this repository, and which script turns it into the next thing. Other files
(README, the stage READMEs, the run scripts, the gate messages) point here
instead of repeating it. Checksums of the committed files are in
`inputs/MANIFEST.md`; the per-release and per-folder `SOURCE.md` files hold
retrieval dates and citation text for the datasets that have them. Alaska
place names, agency acronyms and the pipeline's own words are explained in
[`docs/GLOSSARY.md`](docs/GLOSSARY.md).

Every file mentioned below is one of three kinds. The **Kind** column in each
table tells you what, if anything, you have to do to get it.

| Kind | What it means for you | Examples |
|---|---|---|
| **In the repository** | It arrives with the clone. There is nothing to download. Some of these are zip files that a one-line command unpacks (`python tools/extract_inputs.py`). | `inputs/*.zip`, `inputs/air/*.csv`, `final_network/*.zip`, `outputs/00_inventory_qc/<release>/facilities_clean.csv` |
| **In the Zenodo deposit** | Too large for GitHub: the rasters (~7 GB of friction inputs, ~300 MB of finished friction stack) and the river-ice working directory. The deposit that complements this repository holds them as one zip per group; `python tools/fetch_archive.py --group <name>` downloads a group, verifies it against the deposit's checksum and unpacks it where the pipeline reads it. The DOI is recorded in that script once the deposit is published; until then the tool stops with exit code 3. | `inputs/friction_rasters/`, `outputs/01_friction_build/friction_stack/`, `inputs/river_ice_work/` |
| **Download and regenerate** | The original dataset is downloaded from the source link in section 1 and, where needed, converted by the script named in the walk-through. Public datasets that a publisher serves directly are never re-hosted here: you download them. This is also the way to reproduce what is in the deposit. | the six public transport and boundary layers of workflow 02 (§4.1), the Earth Engine exports (§3.1 Step A), the river-ice interpolation (§3.1 Step B) |
| **Built by the pipeline** | You never download or edit these. They are the intermediate and final products that the scripts in this repository write when you run them, starting from the kinds above. They are excluded from git on purpose. If one is missing or looks wrong, delete it and rerun the stage that produces it (section 6 names the command). | `data/interim/`, `outputs/02_network_build/`, `outputs/fuel_network.duckdb` |

Each run script checks for what it needs before starting; if something is
missing it stops with exit code 3 and prints the fetch command or the section
of this file that explains how to get it. That is a documented gap, not an
error.

## Three ways to use this repository

Pick the one that matches what you want to do. Each later path contains the
earlier ones.

### Path 1 — Use the finished network and costs (nothing to download)

Everything on this path is in the repository. The products are the ones the
paper reports.

```bash
uv venv && uv sync && uv pip install -e .
python tools/extract_inputs.py                            # unzip the committed input bundles
python workflows/00_inventory_qc/validate_inventory.py    # the facility-inventory QC, read-only
bash workflows/03_multimodal_join/run_all.sh              # loads the network-of-record into DuckDB; stops before weighting
```

You get the clean facility table (§2), the network-of-record extracted and
loaded (`final_network/`, §4.3), and the `network_nodes` / `network_edges`
tables (§5). The costed tables need the friction stack: add
`python tools/fetch_archive.py --group friction_stack` and rerun workflow 03,
then `bash workflows/04_duckdb_export/run_all.sh`, which is Path 2's last step.

### Path 2 — Rebuild from the archived intermediates (the deposit, no ArcGIS, no Earth Engine)

The deposit holds every intermediate that is slow or awkward to make. Fetch
what you want to start from, then run the workflows downstream of it:

| You want to rebuild | Fetch | Then run |
|---|---|---|
| the costed graph only | `python tools/fetch_archive.py --group friction_stack` | workflows 03 and 04 |
| the friction stack (§3.2), then the costed graph | `--group friction_inputs` | workflows 01, 03, 04 |
| the network (§4), then the costed graph | `--group friction_stack`, plus the six public downloads of §4.1 (the hand-edited layers are in the repository) | workflows 02 (export opt-in, see §4.3), 03, 04 |
| everything downstream of the raw rasters | `--group friction_inputs`, plus the six public downloads of §4.1 | `bash run_all.sh` |
| the river-ice interpolation itself (ArcGIS Pro) | `--group river_ice_work` | §3.1 Step B |

`run_all.sh` (or `python run_all.py` on Windows) runs workflows 01–04 in order
and skips, with a message, any stage whose inputs are absent.

### Path 3 — Rebuild from the raw sources (Earth Engine + ArcGIS Pro + the downloads)

Sections 2–5 below are this path: every original dataset in §1, downloaded
from its source link, and every script that turns it into the next product.
It needs an Earth Engine account (§3.1 Step A), ArcGIS Pro with Spatial
Analyst for the river ice (§3.1 Step B), R for the network noding (§4.3), and
roughly 12 GB of downloads. It is the path that reproduces the deposit. The
two layers that were drawn or merged by hand (the ice roads, the manual
connections) are in the repository on every path; they have no publisher.

## 1. Original datasets

Every input derives from an open or public dataset. The table says what each one
is used for and where it lands in the repository; the sections that follow walk
through the conversion.

### 1.1 Facilities, delivery methods and regions

| Dataset | Used for | Lands in | Kind | Source |
|---|---|---|---|---|
| AEA / DCRA Utilities Bulk Fuel Inventory (CSV export, one download per release) | The fuel facilities that become network hubs | `inputs/raw_facility_data/<release>/` — the safe-column snapshot, manifest and diff are committed; the raw CSV (contact fields) is never committed after 2022. The 2022 raw CSV is inside `inputs/raw_facility_data/2022/bulk_fuel_data.zip` | In the repository (the snapshot; the raw CSV is not) | [Utility Bulk Fuel Facility](https://akgeoportal.alaska.gov/datasets/8afa0d0dd8834256a2fa12e6003fede1_48/explore) · [REST service](https://maps.commerce.alaska.gov/server/rest/services/Services/Utilities_Bulk_Fuel_Inventory_with_Attachments/MapServer) · retrieval dates and citation in each release's `SOURCE.md` |
| AEA / DCRA Fuel Delivery Method | Per-community delivery mode: the ice-road community list for the transfer fees, and the delivery-method fallback in the network build | Shapefile inside `bulk_fuel_data.zip` (`bulk_fuel_data/raw/Fuel_Delivery_Method.zip`); a GeoJSON copy in `data/raw/boundaries/` | In the repository (shapefile) · Download and regenerate (GeoJSON copy in `data/raw/`) | [Fuel Delivery Method](https://akgeoportal.alaska.gov/datasets/e1971a57fdad4bb8ac29e8742afa9691_12/explore) |
| Alaska Energy Authority regions (the AEA library) | The energy region published per facility | `inputs/region_and_census_data.zip` → `region_and_census_data/Alaska_Energy_Authority_Library.zip` | In the repository | [AEA Regions](https://hub.arcgis.com/datasets/DCCED::alaska-energy-authority-regions/explore) |
| DCRA incorporated-city boundaries · Census Designated Place boundaries | The label-versus-location check in the inventory QC | `inputs/inventory_qc/boundaries/{City_Boundaries,Census_Designated_Place_Boundaries}.zip` | In the repository | Owner-supplied 2026-10-06; provenance and checksums in `inputs/inventory_qc/boundaries/SOURCE.md` |

### 1.2 Transport lines and points

| Dataset | Used for | Lands in | Kind | Source |
|---|---|---|---|---|
| AKDOT&PF Roads (2026-09 download) | The road network — the sole road source since 2026-09-15 | `data/raw/connectivity/road/Roads_AKDOT/` | Download (§4.1) | [Roads AKDOT](https://data-soa-akdot.opendata.arcgis.com/datasets/6ef677dc522542d88fba1711a7e16400_0/explore) |
| USACE National Waterway Network lines | The barge network, and the waterway corridor mask for the friction surface | `data/raw/connectivity/barge/NWN_Waterway_Network_Lines/` (network build); `inputs/data_for_network_build.zip` → `water_networks/waterways_network_ak_albers.shp` (corridor mask) | Download (the `data/raw/` copy, §4.1) · In the repository (the zip copy) | [USACE GeoSpatial](https://geospatial-usace.opendata.arcgis.com/maps/ace7645d305647448a84492a3b909d48) · [BTS/NTAD](https://geodata.bts.gov/datasets/national-waterway-network-lines) |
| North Slope ice roads, merged from three sources (UAA ACCS, AKDOT, SIRA) and edited by hand in ArcGIS Pro | The seasonal ice-road network | `inputs/data_for_network_build.zip` → `ice_roads_150m_3338/Ice_Roads.shp`; `tools/extract_inputs.py` also copies it to `data/raw/connectivity/ice_roads/ice_roads_150m_3338/` where the build reads it | In the repository (an authored layer: it exists nowhere else) | [UAA ACCS](https://accscatalog.uaa.alaska.edu/dataset/anthropogenic-datasets-north-slope/resource/5d898316-507e-4535-8bf0-b0608d3ca83a) · [AKDOT](https://www.arcgis.com/home/item.html?id=820ebeed349b484eab23ffaa685b64ef) · [SIRA](https://www.arcgis.com/home/item.html?id=ef4056f5fb0545698b5c4318821c8237) |
| Ports and harbors (points) | Barge anchors: where the waterway meets land | `data/raw/anchor_points/Ports_and_Harbors.geojson`; a zipped copy in `data_for_network_build.zip` → `water_networks/AK_Ports_and_Harbors.zip` | Download (the `data/raw/` copy, §4.1) · In the repository (the zip copy) | [Harbors](https://akgeoportal.alaska.gov/datasets/113cb18269e24c3fbd031238712b2ff5_0/explore) |
| AK DOT&PF airport registry and the matched origin–destination flight legs | The air network: airports are geocoded, each OD leg becomes a straight line | `inputs/air/airports_ak_dotpf.csv`, `inputs/air/flight_paths_combined.csv` (+ `flight_paths.xlsx`, the hand-digitised source) | In the repository | AK DOT&PF airport registry; flight legs digitised from carrier schedules |
| User-authored manual connections | Hand-drawn lines that stitch hubs the public layers leave disconnected; tagged by mode | `inputs/mannual_connections/mannual_connections.shp` | In the repository | Authored in this project (QGIS/ArcGIS); not an external dataset |
| GRIP4 global roads (CC-BY) | **No longer used.** Removed 2026-09-15; survives only in the legacy `roads_networks/ak_albers_roads_merge.shp` inside `data_for_network_build.zip` | — | In the repository (legacy, no longer read) | [GLOBIO GRIP](https://www.globio.info/download-grip-dataset) |
| OurAirports | **No longer used.** Legacy `Flights/Airports.csv` inside `data_for_network_build.zip` | — | In the repository (legacy, no longer read) | [ourairports.com/data](https://ourairports.com/data/) |

### 1.3 Boundaries and basemaps

| Dataset | Used for | Lands in | Kind | Source |
|---|---|---|---|---|
| US Census TIGER/Line 2022: places, county subdivisions, boroughs / census areas | Tagging hubs with a place and a borough; the Alaska outline | `data/raw/boundaries/{tiger_places,tiger_county_subdivisions,borough_census_area}/` | Download (§4.1) | [TIGER/Line](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) |
| US Census cartographic state boundary 2023 (500k) | Figures only | `inputs/region_and_census_data.zip` → `region_and_census_data/tiger/cb_2023_us_state_500k.shp` | In the repository | [TIGER/Line](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) |
| Natural Earth 10 m land and country borders | The publication map's basemap only | `data/basemap/` | Built by the pipeline (the script downloads it) | Natural Earth, public domain |

### 1.4 Environmental rasters (the friction surface)

All of these end up on the canonical grid: EPSG:3338, 150 m, the shape and
transform of the land-cover raster (`docs/DATA_CONTRACTS.md` §1). Each file
keeps the name its producer gave it, all the way into the build (§3.1).

| Dataset | Used for | Lands in | Kind | Source |
|---|---|---|---|---|
| FABDEM V1 (DEM → slope) | Slope-class friction | `inputs/friction_rasters/FABDEM_slope_150m_EPSG3338.tif` | Download and regenerate | [GEE community catalog](https://gee-community-catalog.org/projects/fabdem/) (read directly in GEE) |
| Dynamic World V1 (summer-mode land cover) | Land-cover friction; water class for barge | `inputs/friction_rasters/dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif` — the grid anchor | Download and regenerate | [GEE catalog](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1) (read directly in GEE) |
| Pastick et al. 2015 near-surface permafrost probability | Permafrost friction | `inputs/friction_rasters/permafrost_probability_150m_EPSG3338.tif` | Download and regenerate | [USGS](https://www.usgs.gov/publications/distribution-near-surface-permafrost-alaska-estimates-present-and-future-conditions) · [paper](https://www.sciencedirect.com/science/article/pii/S0034425715300778) (download, upload as a GEE asset) |
| Historical Sea Ice Atlas (UAF SNAP / AOOS), monthly medians 1990–2022 | Barge ice gating, 12 months | `inputs/friction_rasters/sea_ice/sea_ice_median_{01..12}_{Jan..Dec}_150m_EPSG3338.tif` | Download and regenerate | [SNAP catalog](https://catalog.snap.uaf.edu/geonetwork/srv/eng/catalog.search#/metadata/047e91c7-35c6-410a-a1ef-95539c1ee328) (download, upload as a GEE asset) |
| Brown et al. 2026 river-ice phenology (reach points) + USGS National Hydrography Dataset for Alaska | River ice gating, 12 months | The working directory `inputs/river_ice_work/` (reach points + the two NHD-derived river masks, described in `source_scripts/friction_surface/friction_preprocessing/README.md`); the twelve monthly rasters `inputs/friction_rasters/river_ice/river_ice_probability_{01..12}_150m_EPSG3338.tif` | In the Zenodo deposit (both: `--group river_ice_work`, `--group friction_inputs`) · Download and regenerate (the reach points from the DOI, the masks from the NHD download, the rasters in ArcGIS Pro; §3.1 Step B) | [Arctic Data Center 10.18739/A2SB3X15X](https://arcticdata.io/catalog/view/doi:10.18739/A2SB3X15X) · USGS National Map (NHD, Alaska state shapefile) |

The finished friction stack (the product of section 3) is in the Zenodo deposit
(`python tools/fetch_archive.py --group friction_stack`, Path 2) and is also
mirrored as GEE assets for users who work in Earth Engine. All three live under
`projects/gee-friction-layer-processing/assets/friction_stack_final/`:

| Asset | What it is | Link |
|---|---|---|
| `barge_monthly` (image collection) | The twelve monthly barge surfaces, `barge_01..12` | https://code.earthengine.google.com/?asset=projects/gee-friction-layer-processing/assets/friction_stack_final/barge_monthly |
| `overland_base` | The static overland (terrain) surface, `overland.tif` | https://code.earthengine.google.com/?asset=projects/gee-friction-layer-processing/assets/friction_stack_final/overland_base |
| `road_base` | The static NoData-free road surface, `road_base.tif` | https://code.earthengine.google.com/?asset=projects/gee-friction-layer-processing/assets/friction_stack_final/road_base |

## 2. The facility inventory → the clean facility table (workflow 00)

**Starts from:** one AEA/DCRA inventory download. **Ends with:**
`outputs/00_inventory_qc/<release>/facilities_clean.csv` (committed), the table
the network build and the downstream harness read.

1. **Ingest.** `workflows/00_inventory_qc/01_ingest.py RAW.csv --release <label>`
   reads the raw CSV through the column map in `inputs/inventory_qc/sources/aea/`,
   keeps only the clean-schema columns (no contact fields), and writes
   `inputs/raw_facility_data/<label>/`: the snapshot CSV, `snapshot_manifest.json`
   (checksums, columns kept and dropped) and a diff against the previous
   release. The raw CSV is not added to git; its sha256 goes in the release's
   `SOURCE.md` and in `inputs/MANIFEST.md`. On every later run, `01_ingest.py
   --check` re-derives the committed snapshots to prove nothing drifted.
2. **Correct, normalise, identify.** `02_apply_corrections.py` applies only the
   owner-approved rows of `inputs/inventory_qc/corrections.csv`;
   `03_normalise.py` builds the community key (with `aliases.csv`) and the
   delivery flags; `03b_assign_facility_ids.py` assigns the stable
   `facility_id` from the append-only ledger `facility_ids.csv`.
3. **Check.** `04_detect.py` runs the structural detectors (`thresholds.csv`);
   `05_boundary_check.py` compares each label with the DCRA city and CDP
   boundaries (`inputs/inventory_qc/boundaries/`) and only describes the
   difference; `05b_assign_region.py` assigns the AEA energy region, reading the
   AEA library straight out of `inputs/region_and_census_data.zip`.
4. **Review and publish.** `06_review_queue.py` turns open flags into the owner's
   review sheet (decisions come back as rows of `corrections.csv`, see the
   `record-facility-corrections` skill); `07_publish.py` writes
   `facilities_clean.csv` + `qc_report.md` after the output-contract checks;
   `08_ledger.py` writes the per-release workbook.

Run it all with `bash workflows/00_inventory_qc/run_all.sh [RELEASE]` or
`python workflows/00_inventory_qc/validate_inventory.py [--publish]`
(what CI runs). Everything under `outputs/00_inventory_qc/<release>/` except
the published table and reports is generated.

## 3. The environmental rasters → the friction stack (workflow 01)

**Starts from:** the five raster sources in §1.4. **Ends with:**
`outputs/01_friction_build/friction_stack/` — 14 GeoTIFFs (`overland.tif`,
`road_base.tif`, `barge_01..12.tif`) on the canonical grid, consumed by the
weighting stage of workflow 03. Path 2 shortcut: the inputs this section
produces are in the deposit (`--group friction_inputs`), and so is its result
(`--group friction_stack`).

### 3.1 Produce the input rasters (outside this repository's Python)

**One name per file, from the producer to the build.** Every raster keeps the
name its producer wrote; nothing is ever renamed on disk, so a file can be
traced from the download to the build by its name alone. Padding and
alignment happen *in place*, and the untouched export is kept beside the
live file in a `gee_export/` sub-folder. The names are defined once, in
`source_scripts/friction_surface/friction_paths.py` (`RASTER_NAMES`,
`sea_ice_name`, `river_ice_name`); the loaders, the preflight, the grid
checker, the pad/align scripts, the run drivers' gate and the tests all read
them from there, and a test checks that the two producers that cannot import
the module (the Earth Engine script and the ArcGIS script) spell them the same.

When everything below is done, `inputs/friction_rasters/` looks like this:

```
inputs/friction_rasters/
  FABDEM_slope_150m_EPSG3338.tif
  dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif     <- the grid anchor
  permafrost_probability_150m_EPSG3338.tif
  sea_ice/sea_ice_median_{01..12}_{Jan..Dec}_150m_EPSG3338.tif   (12 files)
  sea_ice/gee_export/…                                           the cropped originals, kept
  river_ice/river_ice_probability_{01..12}_150m_EPSG3338.tif     (12 files)
  river_ice/provenance/…                                         ArcGIS QA rasters; the build ignores them
```

The whole folder is about 7 GB and is never committed (`.gitignore`). If you
only need the *finished stack*, skip this section: download the three GEE
mirror assets in §1.4 into `outputs/01_friction_build/friction_stack/` and run
`python workflows/01_friction_build/03_qa_friction_stack.py` to confirm the
14-file contract.

#### Step A — Earth Engine: slope, land cover, permafrost, sea ice

1. **Upload two datasets as assets** in your own Earth Engine project:
   the Pastick et al. 2015 permafrost-probability GeoTIFF (USGS link in §1.4),
   and the Historical Sea Ice Atlas monthly rasters (SNAP link in §1.4) as an
   image collection whose band 1 is the concentration and band 2 the source
   flag (128 = land). FABDEM and Dynamic World are public catalog datasets;
   nothing to upload.
2. **Run the export script.** Open
   `source_scripts/friction_surface/friction_preprocessing/gee_friction_layer_multi_data_processing.js`
   in the Code Editor, set the `CONFIG` block at the top (your project's
   asset root, the two asset ids, the Drive folder), click Run, then start
   every `Export_*` task in the Tasks tab, plus `Bake_DW_summer_mode_10m`
   (the robust two-stage land-cover path; the script explains it). The
   script derives slope from FABDEM, takes the June–September mode of
   Dynamic World 2022–2024, and computes the 1990–2022 monthly sea-ice
   medians, all at 150 m in EPSG:3338 on the full-Alaska grid.
3. **Download without renaming.** Three files go to `inputs/friction_rasters/`,
   the twelve sea-ice files to `inputs/friction_rasters/sea_ice/`. If Drive
   delivered a raster as several tiles (`…-0000000000-0000000000.tif`), merge
   them into one file under the plain name (`rio merge`); the tile suffix is
   the only thing that may be removed from a name.
4. **Pad the sea ice.** The atlas is land-masked, so GEE crops each monthly
   export to the atlas footprint and the file is short on the east.
   ```bash
   python -m friction_surface.friction_preprocessing.pad_sea_ice_to_grid
   ```
   inserts each month into the full grid with no resampling (the pad is 0,
   "no ice"), writes it in place and keeps the original in `sea_ice/gee_export/`.
   Safe to re-run: a file already on the full grid is skipped.
5. **Align the permafrost.** The Pastick raster covers a smaller area than
   the land-cover grid.
   ```bash
   python -m friction_surface.friction_preprocessing.align_permafrost
   ```
   reprojects it (bilinear) onto the land-cover raster's transform and shape,
   in place.
6. **Check the grid.** `python -m friction_surface.check_grid_exports` must
   report every raster on the land-cover grid.

#### Step B — River ice: local Python, then ArcGIS Pro

River ice is not an Earth Engine product. It is interpolated in ArcGIS Pro
from two things: the Brown et al. **reach points** (raw data, one small public
download; they say *how much* ice per reach and month) and the two **river
masks** (the NHD polygons and centre lines of the thirty Brown rivers; derived
data, they say *where* a river cell exists and which cells share a polygon
median). `source_scripts/friction_surface/friction_preprocessing/README.md`
describes both masks field by field and how they were cut. Everything lives in
one working directory, `inputs/river_ice_work/` (gitignored):

```
inputs/river_ice_work/
  waterFilledMedians2000_2023.geojson   Brown et al. 2026 reach points (§1.4; 9.6 MB, CC0)
  brown_river_polygons/                 NHD wide channels of the 30 rivers (~160 MB; too big for git)
  brown_river_flowlines/                NHD centre lines of the 30 rivers (~15 MB)
  NHD_extracted/Shape/                  USGS National Hydrography Dataset for Alaska, unzipped
                                        (NHDArea.shp, NHDFlowline_0..6.shp; the zip is ~5 GB) —
                                        download it only to rebuild the masks
```

Set `FRICTION_LAYER_ROOT` to use a folder elsewhere instead.

1. **Get the working directory.** Either fetch it from the deposit,
   `python tools/fetch_archive.py --group river_ice_work` (reach points and
   masks together), and skip to step 3; or download the reach points from the
   Arctic Data Center (§1.4) into
   `inputs/river_ice_work/waterFilledMedians2000_2023.geojson` and build the
   masks in step 2.
2. **Build the river masks** (also the way to rebuild them if NHD or the Brown
   reach set changes). Download the NHD shapefile bundle (USGS National Map,
   "NHD Alaska, state, shapefile") into
   `inputs/river_ice_work/NHD_extracted/Shape/`, run
   `python tools/extract_inputs.py` if you have not (the mask builder needs the
   waterway shapefile to keep salt water out of the river mask), then
   ```bash
   python -m friction_surface.friction_preprocessing.build_brown_polygon_mask
   ```
   filters the statewide NHD to the thirty rivers Brown et al. observed and
   writes `brown_river_polygons/` (wide channels) and `brown_river_flowlines/`
   (centre lines).
3. **Interpolate the monthly ice probability** (ArcGIS Pro with Spatial
   Analyst, Windows). The land-cover raster from Step A must already be in
   `inputs/friction_rasters/`: it is the grid the output is aligned to.
   ```
   set RASTER_DIR=C:\path\to\repo\inputs\friction_rasters
   "C:\Program Files\ArcGIS\Pro\bin\Python\scripts\propy.bat" ^
       source_scripts\friction_surface\friction_preprocessing\river_ice_full_pipeline.py
   ```
   For each month it takes the median of Brown's three observation periods
   per reach, fills wide rivers with the per-polygon median and narrow rivers
   by inverse-distance weighting (12 neighbours, 50 km cap), clamps to 0–1,
   leaves cells with no source as NoData for the friction build's own capped
   fill, snaps the result onto the land-cover grid, and writes the twelve
   `river_ice_probability_MM_150m_EPSG3338.tif` straight into
   `inputs/friction_rasters/river_ice/`. July and August are ice-free by
   construction. QA rasters (`provenance_MM.tif`) and a browse mosaic land in
   `river_ice/provenance/`, which the build ignores.
4. Optional: `plot_river_ice_provenance.py` (same variable, same Python)
   draws which fill stage produced each cell.

`pad_river_ice_to_grid.py` is not part of a fresh regeneration: it lifts the
archived 2026-06 narrow-grid run (`inputs/friction_rasters/small_grid/river_ice/`)
onto the full grid for machines that still carry it.

#### Step C — Gate

```bash
python workflows/01_friction_build/00_preflight_inputs.py
```

must print every layer `OK`. A `FATAL` names the file and the reason (missing,
wrong grid, values out of range); fix it at its source in Step A or B. Then §3.2.

A new raster of any other kind is snapped onto the grid with the
`align-to-ak-stack` skill.

### 3.2 Build the stack (this repository)

Run `bash workflows/01_friction_build/run_all.sh`. It gates on the
land-cover raster (`inputs/friction_rasters/dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif`) and on the extracted
`inputs/data_for_network_build/` (from `python tools/extract_inputs.py`), then:

1. `00_preflight_inputs.py` checks every raster against the grid and its value
   range; a mismatch stops the build.
2. `01_build_corridor_masks.py` rasterises the USACE waterway lines
   (`inputs/data_for_network_build/water_networks/waterways_network_ak_albers.shp`,
   75 m buffer) into `outputs/01_friction_build/waterway_mask_150m.tif`. The mask
   is required: without it the barge surfaces sever about 18 % of waterway edges.
3. `02_build_friction_stack.py` combines slope, land cover and permafrost into
   `overland.tif` and the NoData-free `road_base.tif`, and gates the water
   mask by sea and river ice into `barge_01..12.tif`. Every constant comes from
   `source_scripts/friction_surface/friction_config.py`.
4. `03_qa_friction_stack.py` checks the 14-file contract, the ice-gating
   direction and the value floor.

## 4. The transport data → the network-of-record (workflow 02)

**Starts from:** the lines, points and boundaries in §1.2–1.3, the clean
facility table from §2, and the manual connections. **Ends with:**
`final_network/` — the committed, checksummed network-of-record.

### 4.1 Stage the raw sources

`data/raw/` is a working folder, never in the repository, laid out as the
`SPEC` table in `workflows/02_network_build/00_normalize_raw.py` names it file
by file. Its contents come from two places:

**From the repository** (the layers that were made by hand and have no
publisher): `python tools/extract_inputs.py` copies the ice-road layer out of
`inputs/data_for_network_build.zip` into the layout below, and the
manual-connections shapefile is read straight from `inputs/mannual_connections/`
(§4.2). The air tables are committed at `inputs/air/` and the facility table
comes from workflow 00, so neither is in `data/raw/`.

**Downloaded by you** (public datasets their publishers serve directly, so
this repository does not re-host them): the six layers marked *download*
below, from the links in §1.1–1.3. Unzip each into its folder; the file names
are the publishers' own.

```
data/raw/connectivity/road/Roads_AKDOT/Roads_AKDOT.shp                                  download: AKDOT&PF roads (§1.2)
data/raw/connectivity/barge/NWN_Waterway_Network_Lines/Waterway_Network.shp             download: USACE waterway lines (§1.2)
data/raw/connectivity/ice_roads/ice_roads_150m_3338/Ice_Roads.shp                       from the repository (extract_inputs.py)
data/raw/anchor_points/Ports_and_Harbors.geojson                                        download: ports and harbors (§1.2)
data/raw/boundaries/tiger_places/tl_2022_02_place.shp                                   download: TIGER 2022 places (§1.3)
data/raw/boundaries/borough_census_area/Alaska_Borough_and_Census_Area_Boundaries.shp   download: boroughs and census areas (§1.3)
data/raw/boundaries/tiger_county_subdivisions/tl_2022_02_cousub.shp                     download: TIGER 2022 county subdivisions (normalised, not used)
data/raw/boundaries/Fuel_Delivery_Method.geojson                                        download: DCRA fuel delivery method (§1.1)
```

Versions matter for an exact rebuild: the network-of-record was built from
the 2026-09 AKDOT&PF roads and the 2022 TIGER files. A publisher's current
release may differ, which changes the rebuilt network; that is expected on
this path and is why the network-of-record is frozen (§4.3).

### 4.2 Normalise and prepare

Run `bash workflows/02_network_build/run_all.sh`. It gates on a non-empty
`data/raw/`, then (only when `data/interim/MANIFEST.md` is absent):

1. `00_normalize_raw.py` reprojects every `SPEC` entry to EPSG:3338 with
   canonical column names into `data/interim/*.gpkg`, copies the air CSVs under
   their interim names, writes `data/interim/facilities.csv` from the latest
   `facilities_clean.csv`, and records what it did in `data/interim/MANIFEST.md`.
2. `01_prep_waterway.py` extracts the Alaska marine network from the raw NWN
   into `data/interim/ak_waterway.gpkg`.
3. `02_prep_airways.py` geocodes each flight leg into
   `data/processed/airways.geojson` and dissolves the boroughs into
   `data/boundary.geojson`.

On every run, `03_prep_manual_connections.py` splits
`inputs/mannual_connections/mannual_connections.shp` by its `Mode` tag into
`data/interim/manual_<mode>.gpkg` (skipped cleanly when the file is absent).
`03_fetch_basemap.py` (figures only) downloads Natural Earth into `data/basemap/`.

### 4.3 Build, verify, export

4. `04_build_network.py` validates `profile.yaml` (the only place region-specific
   choices live) and runs the `mmnet` engine stages 01→04: node each mode's
   lines (road, ice and air through the R oracle, the waterway in Python),
   build hubs from the facility table, snap them to the network, add the
   intermodal transfers and join the remaining components to the giant. Output:
   `outputs/02_network_build/output/0{1..4}_*.gpkg` plus `reports/` and the
   hub trails (`01_site_members.csv`, `02_hub_members.csv`, `02_hub_snaps.csv`).
5. `05_verify_north_slope.py` is the connectivity proof. It reloads the built
   network, finds the largest connected piece (the "giant" component), and
   checks that the network is joined the way the study requires. The name
   comes from the hardest case: the North Slope communities are reachable
   only by sea or by winter ice road, so if the road and ice-road nodes
   nearest Utqiaġvik (Barrow) sit in the giant component, the barge landings,
   ice-road welds and shore connections all did their job. It prints a
   before-and-after summary of what the engine added (the full marine
   network, barge transfers at ports and hubs, welds and bridges, shore
   landings) and then five pass/fail checks: the Barrow road node is in the
   giant, the Barrow ice node is in the giant, at least 95 % of road nodes and
   95 % of ice-road nodes are in the giant, and the number of barge transfers
   at ports and barge hubs is in the expected range (about 292). Any failure
   stops the driver before the export step, so a broken build can never
   become the network-of-record.
6. `06_export_final_network.py` writes `final_network/`: the node and edge
   shapefiles zipped, `hub_members.csv` and `hub_snaps.csv`, and
   `MANIFEST.sha256`. **This step is opt-in** (`EXPORT_FINAL_NETWORK=1`): the
   edge shapefile's row order defines `edge_id` for every downstream table, so a
   re-export is a new network-of-record and must be committed together with
   the new checksums and the regenerated DuckDB tables. Read
   `final_network/README.md` first.

## 5. Network + friction + rates → the costed graph (workflows 03 and 04)

**Starts from:** `final_network/` (committed), the friction stack from §3
(built, or fetched with `python tools/fetch_archive.py --group friction_stack`),
and the dollar rates in `source_scripts/friction_surface/friction_costs.py`.
**Ends with:** `outputs/fuel_network.duckdb`.

Run `bash workflows/03_multimodal_join/run_all.sh`:

1. `01_extract_network_handoff.py` unzips `final_network/*.zip` into the
   gitignored `final_network/network_joined_{nodes,edges}/`.
2. `02_load_final_network.py` loads them as `network_nodes` and
   `network_edges` (plus `hub_members` and `hub_snaps`), derives `edge_id` from
   shapefile row order, and fails if the inventory differs from the `EXPECTED`
   dict. This runs from committed data; it is CI's smoke test.
3. `03_weight_network_edges.py` samples the friction stack every 75 m along
   every edge for every month into `edge_month_weights`. The driver stops here
   (exit 3) when the stack is absent.
4. `04_assemble_weighted_graph.py` multiplies friction by the per-mode rates and
   adds the intermodal transfer fees into `edge_costs`. The ice-road community
   list for the fees is read from `Fuel_Delivery_Method.shp`, which
   `tools/extract_inputs.py` unpacks from `bulk_fuel_data.zip` into
   `inputs/bulk_fuel_data/raw/`.

`bash workflows/04_duckdb_export/run_all.sh` then runs the validation queries
and dumps the schema. Publication figures and tables are generated from the
database and the committed inputs by the scripts under `figure_scripts/`
(committed figures and tables) and `diagnostics/` (build checks).

## 6. Products: what is where, and how to get it back

| Product | Kind | Producer | To regenerate |
|---|---|---|---|
| `inputs/raw_facility_data/<release>/` snapshot, manifest, diff | In the repository | `00/01_ingest.py` | re-ingest the raw CSV (`SOURCE.md` has its sha256) |
| `outputs/00_inventory_qc/<release>/facilities_clean.csv`, `qc_report.md`, `inventory_ledger.xlsx` | In the repository | `00/07_publish.py`, `00/08_ledger.py` | `bash workflows/00_inventory_qc/run_all.sh` |
| other `outputs/00_inventory_qc/<release>/*` | Built by the pipeline | workflow 00 | same |
| `inputs/bulk_fuel_data/`, `inputs/data_for_network_build/`, `inputs/region_and_census_data/` | Built by the pipeline (unzipped from a repository file) | `tools/extract_inputs.py` | `python tools/extract_inputs.py` |
| `inputs/river_ice_work/` | In the Zenodo deposit | §3.1 Step B | `python tools/fetch_archive.py --group river_ice_work`, or download the reach points and build the masks |
| `inputs/friction_rasters/` | In the Zenodo deposit | §3.1 | `python tools/fetch_archive.py --group friction_inputs`, or Step A (GEE export + pad + align) and Step B (the ArcGIS river-ice pipeline); every file under its producer's name |
| `outputs/01_friction_build/friction_stack/` (14 TIFs) | Built by the pipeline · In the Zenodo deposit | workflow 01 | `bash workflows/01_friction_build/run_all.sh`, or `python tools/fetch_archive.py --group friction_stack` (also mirrored on GEE, §1.4) |
| `outputs/01_friction_build/waterway_mask_150m.tif` | Built by the pipeline | `01/01_build_corridor_masks.py` | `bash workflows/01_friction_build/run_all.sh` (from the committed waterway shapefile) |
| `data/raw/` | From the repository (the ice-road layer, via `tools/extract_inputs.py`) + Download (the six public layers) | §4.1 | `python tools/extract_inputs.py`, then the downloads listed in §4.1 |
| `data/interim/`, `data/processed/`, `data/boundary.geojson`, `data/basemap/` | Built by the pipeline | `02/00–03` | `bash workflows/02_network_build/run_all.sh` |
| `outputs/02_network_build/{output,reports}` | Built by the pipeline | `02/04_build_network.py` | same |
| `final_network/*.zip`, `hub_members.csv`, `hub_snaps.csv`, `MANIFEST.sha256` | In the repository | `02/06_export_final_network.py` | `EXPORT_FINAL_NETWORK=1 …` — deliberate, see §4.3 |
| `final_network/network_joined_{nodes,edges}/` | Built by the pipeline (unzipped from a repository file) | `03/01_extract_network_handoff.py` | `bash workflows/03_multimodal_join/run_all.sh` |
| `outputs/fuel_network.duckdb` | Built by the pipeline | workflows 03–04 | same |

## 7. Integrity

- `inputs/MANIFEST.md` lists the sha256 of every committed data file and of the
  raw inventory CSVs that are not committed. Update it in the same change as
  any deliberate repack.
- CI re-hashes `final_network/*.zip` on every push and fails on any change,
  because those bytes define `edge_id` (`docs/DATA_CONTRACTS.md` §5).
- `01_ingest.py --check` re-derives every committed inventory snapshot; CI runs
  the whole workflow 00 chain read-only and fails if `facilities_clean.csv`
  would differ.
- Git LFS is deliberately not used (`.gitattributes`): every committed file is a
  plain blob under 50 MB, so a clone is complete as is. Everything larger is in
  the Zenodo deposit, and `tools/fetch_archive.py` verifies each download against
  the md5 the deposit publishes for it before unpacking.
