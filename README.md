# DOE_MAS — Alaska fuel-delivery friction surface & weighted network

Companion code and data for the Data-in-Brief spatial-network paper. It covers three
things, in order:

1. **Friction stack** — an environmental traversability surface for Alaska (road / barge /
   ice-road, by month) built from land cover, terrain, permafrost, sea ice, and river ice.
2. **Network ingest** — reading the delivered multi-modal fuel network (nodes + edges,
   supplied as shapefiles in `final_network/`) into a DuckDB database.
3. **Edge weighting** — sampling the friction stack along every network edge and assembling
   per-month, per-mode edge costs into a weighted graph.

Friction encodes *environmental* traversability only (baseline 1.0); per-mode operational
cost rates live separately in `friction_surface/friction_costs.py`. The two are never mixed
(see `friction_surface/README_friction.md`).

> The multi-agent routing / TSP-optimization layer is **not** part of this release; it is
> the subject of separate work.

## Repository layout

**Friction stack** (`friction_surface/` — see `friction_surface/README_friction.md`)
- `run_friction_pipeline.py` — entry point: validate inputs, build surfaces, compute edge costs
- `friction_config.py` — single source of truth (CRS, thresholds, seasons, LULC multipliers)
- `friction_costs.py` — per-mode operational cost rates (kept separate from friction)
- `friction_surface.py`, `friction_io.py`, `friction_preflight.py`, `friction_paths.py`
- `friction_preprocessing/` — GEE Code Editor + ArcGIS Pro input-generation scripts
- `tests/`, `qa/`, `viz_scripts/`

**Network ingest + edge weighting** (repo root)
- `load_final_network.py` — ingest `final_network/*` shapefiles → `network_nodes` / `network_edges`
- `weight_network_edges.py` — sample friction rasters along each edge → `edge_month_weights`
- `assemble_weighted_graph.py` — per-month, per-mode edge costs → `edge_costs` + weighted graph
- `build_corridor_masks.py` — rasterize transport corridors onto the friction grid
- `pipeline.py` — shared infra helpers (logging + input-raster path resolution)

**Inspection / viz**
- `make_network_plots.py` — plot the network and weighted edges
- `run_validation_query.py` — passability summaries from `edge_month_weights`
- `query_duckdb.py` — ad-hoc DuckDB queries

**Reusable tooling & supplementary**
- `mmnet-toolkit/` — installable multimodal-network builder (provenance for the delivered network)
- `supplementary/` — cost-rate blind derivations & verification (provenance for `friction_costs.py`)
- `.claude/skills/` — the friction & cost-model playbooks (align / assign / derive / run pipeline)

**Data & setup**
- `inputs/` — all input datasets (large; see `EXTERNAL_DATA.md` — not committed to git)
- `final_network/` — delivered network shapefiles (`network_joined_nodes.zip`, `network_joined_edges.zip`)
- `outputs/` — publication figures, tables, light analysis artifacts
- `requirements.txt`, `setup/` — Python dependencies and environment provisioning

---

## Running the pipeline

Run everything from the repository root (scripts import each other by module name).

### 1. Build the friction stack

```bash
python -m friction_surface.run_friction_pipeline
```

Reads the aligned input rasters (see [Preprocessing](#preprocessing-friction-inputs) and
`EXTERNAL_DATA.md`) and writes the friction TIFs to
`friction_surface/friction_outputs/friction_stack/`. Use `--skip-surfaces` to reuse existing
TIFs and only recompute edges. Rebuild-and-QA guidance lives in the `run-friction-pipeline`
skill and `friction_surface/README_friction.md`.

### 2. Ingest the final network

```bash
python load_final_network.py            # add --dry-run to preview without writing
```

Extracts `final_network/network_joined_{nodes,edges}` and writes the `network_nodes` and
`network_edges` tables into `fuel_network.duckdb`.

### 3. Weight each edge

```bash
python weight_network_edges.py          # samples friction along edges -> edge_month_weights
python assemble_weighted_graph.py       # per-month/mode costs -> edge_costs + weighted graph
```

`weight_network_edges.py` samples each month's friction raster along every edge geometry;
`assemble_weighted_graph.py` combines those weights with the `friction_costs.py` rates into
per-(mode, month) edge costs and assembles the weighted multigraph. Inspect the result with:

```bash
python run_validation_query.py          # monthly passability by mode
python make_network_plots.py            # network / weighted-edge figures
```

---

## Preprocessing friction inputs

The friction stack expects a set of grid-aligned rasters (land cover, slope/DEM, permafrost,
12 monthly sea-ice, 12 monthly river-ice) all snapped to the canonical `lulc.tif` grid
(EPSG:3338, 150 m). Most are bundled in `inputs/AK_Stack_150m.zip`; `EXTERNAL_DATA.md`
documents sizes and regeneration. The `align-to-ak-stack` skill snaps any new raster onto
the reference grid.

### GEE Code Editor — terrain, land cover, sea ice

The canonical export script is
`friction_surface/friction_preprocessing/gee_friction_layer_mutli_data_processing.js`
(run in the Google Earth Engine Code Editor). It produces:

| Input | Source dataset |
|---|---|
| `lulc.tif` | Dynamic World v1 modal |
| `slope.tif`, `dem.tif` | FABDEM |
| `permafrost.tif` | Pastick et al. 2015 (uploaded user asset) |
| `sea_ice/*.tif` | NSIDC sea-ice concentration (CDR), 12 monthly medians |

Exports land in Google Drive at 150 m EPSG:3338, aligned to the LULC reference grid.

### ArcGIS Pro — river ice

`river_ice/*.tif` is **not** produced in GEE. It is generated in ArcGIS Pro from Brown et al.
2026 river-ice phenology by
`friction_surface/friction_preprocessing/river_ice_full_pipeline.py` (edit the
`Configuration` block at the top for your local paths; it takes no CLI args). It computes
`p_ice = clamp(1 - areaPropMedWater, 0, 1)` per reach, medians per (ReachID, month), then
fills the river network via per-polygon zonal median + IDW. p_ice is near 1.0 Nov–Apr
(frozen) and near 0.0 in the open/transition months.

### Permafrost alignment

The GEE Pastick export covers only continental Alaska, so it reports a smaller bounding box
than statewide `lulc.tif`. Snap it onto the canonical grid:

```bash
python -m friction_surface.friction_preprocessing.align_permafrost
```

Out-of-footprint pixels become NoData (read as "no permafrost penalty").

### Verify alignment

Every friction-input raster must share identical shape, CRS, transform, and pixel alignment
with `lulc.tif`. `friction_surface/friction_preflight.py` runs this check as part of the
pipeline; `friction_surface/check_grid_exports.py` verifies the GEE exports.

---

## Setup

- Python 3.10+ with the geospatial stack (`geopandas`, `rasterio`, `shapely`, `pyproj`,
  `duckdb`, `networkx`, `numpy`, `pandas`). See `requirements.txt` and
  `friction_surface/requirements-friction.txt`.
- `setup/installations.txt` — supplementary install notes.
- `setup/JETSTREAM_SETUP_GUIDE.md` — optional Jetstream2 VM provisioning for large runs.
- The pipeline is CPU-only; no GPU or LLM backend is required.

## Related docs

- `EXTERNAL_DATA.md` — large/external datasets and how to regenerate them
- `STRUCTURE.md` — repository structure and layout notes
- `friction_surface/README_friction.md` — friction-surface design notes and the friction-vs-cost rule
- `supplementary/` — cost-rate derivations and verification
- `final_network/README.md` — delivered network schema
