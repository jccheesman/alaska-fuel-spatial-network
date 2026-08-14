# Alaska bulk-fuel multimodal network

[![CI](https://github.com/jccheesman/alaska-fuel-spatial-network/actions/workflows/ci.yml/badge.svg)](https://github.com/jccheesman/alaska-fuel-spatial-network/actions/workflows/ci.yml)

Companion code and data for the Data-in-Brief spatial-network paper: how much it
costs, per gallon and per month, to move bulk fuel along every edge of Alaska's
multimodal transport network (road + barge + air + seasonal ice road).

The repository is one pipeline across four steps, which are found in the numbered
folder under `workflows/`. Each is described below:

| Step | Workflow | What it does | Key output |
|---|---|---|---|
| (a) | `workflows/01_friction_build/` | Build monthly environmental friction surfaces for Alaska (terrain, land cover, permafrost, sea/river ice) on the canonical 150 m EPSG:3338 grid | `outputs/01_friction_build/friction_stack/` (14 TIFs) |
| (b) | `workflows/02_network_build/` | Build the connected multimodal network from the facility inventory + connectivity layers with the region-agnostic `mmnet` engine (`profile.yaml` holds every region-specific choice) | `final_network/network_joined_{nodes,edges}.zip` |
| (c) | `workflows/03_multimodal_join/` | Sample friction along every edge, join $-rates, assemble the weighted graph | `edge_month_weights`, `edge_costs` in DuckDB |
| (d) | `workflows/04_duckdb_export/` | Validate and document the deliverable | `outputs/fuel_network.duckdb` (4 tables) |

Reusable library code lives in `source_scripts/` (installable: the `mmnet` network engine
and the `friction_surface` builders/config/costs). The friction surface encodes
*environmental* traversability only (baseline 1.0); every dollar lives in
`source_scripts/friction_surface/friction_costs.py` — that separation is enforced
throughout.

## Quickstart

```bash
git clone <this-repo> && cd <this-repo>
uv venv && uv sync && uv pip install -e .

python tools/extract_inputs.py    # unzip the committed inputs
bash run_all.sh                   # run as far as the data on disk allows
```
A fresh clone runs steps **(c)–(d)** end-to-end from committed data alone
(the frozen network + ingest with its 82,300-node / 90,921-edge). 
Steps (a) and (b) need regenerable-only inputs — each stage's
`run_all.sh` gates on what is missing and prints exactly how to regenerate it
(`EXTERNAL_DATA.md` is the honest inventory of what exists where).

Final friction stack TIF files are hosted on Google Earth Engine at:

Barge_monthly Image Collection: https://code.earthengine.google.com/?asset=projects/gee-friction-layer-processing/assets/friction_stack_final/barge_monthly 
Overland Friction: https://code.earthengine.google.com/?asset=projects/gee-friction-layer-processing/assets/friction_stack_final/overland_base
Road_base Friction: https://code.earthengine.google.com/?asset=projects/gee-friction-layer-processing/assets/friction_stack_final/road_base

The run scripts find the project interpreter themselves (active `$VIRTUAL_ENV`,
then `.venv/bin/python`, then `python3` with a warning), so no activation step
is needed. They also distinguish two kinds of non-zero exit: **3** means a
documented input is absent and the stage was *skipped*; anything else is a real
failure, and the top-level `run_all.sh` exits non-zero when one occurs. Shared
helpers live in `workflows/_lib.sh`.

Per-stage runs:

```bash
bash workflows/01_friction_build/run_all.sh    # needs inputs/friction_rasters (~7 GB, regenerable)
bash workflows/02_network_build/run_all.sh     # needs data/raw (inputs/network_raw.zip — pending)
bash workflows/03_multimodal_join/run_all.sh   # stages 01-02 run from committed data
bash workflows/04_duckdb_export/run_all.sh
```

Stage (b) does **not** re-export the frozen handoff by default — that would
replace the network-of-record and invalidate every `edge_id`-keyed table. Opt in
deliberately, after reading `final_network/README.md`:

```bash
EXPORT_FINAL_NETWORK=1 bash workflows/02_network_build/run_all.sh
```

The R noding oracle in act (b) additionally needs `Rscript` +
sf/sfnetworks/tidygraph/dplyr on PATH. Everything is CPU-only.

### Windows & macOS

The install is identical on every OS (`uv venv && uv sync && uv pip install
-e .` — all geospatial dependencies ship wheels). The bash drivers above are
the Linux/macOS path; on Windows run their cross-platform twin instead:

```bash
python run_all.py                 # same stages, gates, and exit codes as run_all.sh
python run_all.py --only 03       # one stage (name or numeric prefix)
```

(or use WSL/Git Bash and the bash drivers, if you prefer). CI asserts both
drivers report the same skipped/failed summary. The R oracle is required on
every OS for stage (b): install R, then
`install.packages(c("sf", "sfnetworks", "tidygraph", "dplyr"))`.

## The handoff that holds it together

`final_network/` is the frozen network-of-record: the joined multimodal
network (82,300 nodes / 90,921 edges / 384 fuel hubs / 21 components / 99.65%
giant) exported by act (b) and ingested by act (c). Its shapefile **row order
defines `edge_id`** for every DuckDB table, so the committed zips are
checksummed (`inputs/MANIFEST.md`) and preserved byte-identical.

**Caution:** the delivered network was built with the pre-bugfix mmnet engine;
`source_scripts/mmnet` carries four later fixes. Rebuilding act (b) therefore produces a
*different* network and invalidates every edge_id-keyed table — freeze vs
rebuild is an open owner decision. Full provenance: `final_network/README.md`.

## Where things are

| Path | What |
|---|---|
| `source_scripts/mmnet/` | The region-agnostic network engine (R-noding oracle included) — the single canonical copy |
| `source_scripts/friction_surface/` | Friction builders + `friction_config.py` + `friction_costs.py` (all USD $) |
| `workflows/01..04_*/` | The four steps: thin numbered drivers, per-stage READMEs, run orders |
| `inputs/` | Available input datasets located here, open-source dataset information provided |
| `final_network/` | The frozen act-(b)→(c) handoff; this step is regenrable with source scripts |
| `outputs/` | Gitignored regenerables + committed tables/analysis + the DuckDB deliverable |
| `docs/` | `ARCHITECTURE.md` (engine design), `DATA_CONTRACTS.md` (every inter-stage contract), `API.md` |
| `supplementary/` | Blind cost-rate derivations + verification backing every number in `friction_costs.py` |
| `tests/` | pytest suite (run by CI) |
| `.claude/skills/` | Six procedural playbooks (friction, costs, network profile/build) |

## Preprocessing the friction inputs

The friction stack expects grid-aligned rasters (land cover, slope, permafrost,
12× sea ice, 12× river ice) snapped to the canonical `lulc.tif` grid
(EPSG:3338, 150 m, 28,000 × 16,567). They are regenerable-only (~12 GB):

- **GEE** (terrain, land cover, sea ice): `source_scripts/friction_surface/friction_preprocessing/gee_friction_layer_multi_data_processing.js` in the Earth Engine Code Editor
- **ArcGIS Pro** (river ice): `river_ice_full_pipeline.py` (edit its Configuration block; arcpy, no CLI).
- **Alignment:** `python -m friction_surface.friction_preprocessing.align_permafrost`, then gate with `python workflows/01_friction_build/00_preflight_inputs.py`.

Source datasets and URLs: `inputs/README.md`. The `align-to-ak-stack` skill
snaps any new raster onto the reference grid.

## Related docs

- `docs/DATA_CONTRACTS.md` — the 150 m grid spec, the 14-file friction-stack
  contract, the R WORKDIR contract, the handoff schema, the edge_id rule, the
  DuckDB schema — every inter-stage contract on one page
- `docs/ARCHITECTURE.md` — the mmnet engine: profile-as-data, stage chain, R↔Python seam
- `EXTERNAL_DATA.md` — what exists where (committed / regenerable / absent)
- `CLAUDE.md` — the lab notebook: one row per numbered script, with findings
- `supplementary/` — cost-rate derivations and verification
