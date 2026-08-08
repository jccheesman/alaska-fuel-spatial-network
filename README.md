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

Reusable library code lives in `src/` (installable: the `mmnet` network engine
and the `friction_surface` builders/config/costs). The friction surface encodes
*environmental* traversability only (baseline 1.0); every dollar lives in
`src/friction_surface/friction_costs.py` — that separation is enforced
throughout.

> The multi-agent routing / TSP-optimization layer is **not** part of this
> release; it is the subject of separate work. (Its extension point, the
> `hub_facility_map` table, is documented in `workflows/04_duckdb_export/README.md`.)

## Quickstart

```bash
git clone <this-repo> && cd <this-repo>
git lfs pull                      # committed data zips are LFS objects
uv venv && uv sync && uv pip install -e .

python tools/extract_inputs.py    # unzip the committed inputs
bash run_all.sh                   # run as far as the data on disk allows
```

A fresh clone runs steps **(c)–(d)** end-to-end from committed data alone
(the frozen network + ingest with its 82,300-node / 90,921-edge integrity
tripwire). Steps (a) and (b) need regenerable-only inputs — each stage's
`run_all.sh` gates on what is missing and prints exactly how to regenerate it
(`EXTERNAL_DATA.md` is the honest inventory of what exists where).

Per-stage runs:

```bash
bash workflows/01_friction_build/run_all.sh    # needs inputs/friction_rasters (~7 GB, regenerable)
bash workflows/02_network_build/run_all.sh     # needs data/raw (inputs/network_raw.zip — pending)
bash workflows/03_multimodal_join/run_all.sh   # stages 01-02 run from committed data
bash workflows/04_duckdb_export/run_all.sh
```

The R noding oracle in act (b) additionally needs `Rscript` +
sf/sfnetworks/tidygraph/dplyr on PATH. Everything is CPU-only.

## The handoff that holds it together

`final_network/` is the frozen network-of-record: the joined multimodal
network (82,300 nodes / 90,921 edges / 384 fuel hubs / 21 components / 99.65%
giant) exported by act (b) and ingested by act (c). Its shapefile **row order
defines `edge_id`** for every DuckDB table, so the committed zips are
checksummed (`inputs/MANIFEST.md`) and preserved byte-identical.

**Caution:** the delivered network was built with the pre-bugfix mmnet engine;
`src/mmnet` carries four later fixes. Rebuilding act (b) therefore produces a
*different* network and invalidates every edge_id-keyed table — freeze vs
rebuild is an open owner decision. Full provenance: `final_network/README.md`.

## Where things are

| Path | What |
|---|---|
| `src/mmnet/` | The region-agnostic network engine (R noding oracle included) — the single canonical copy |
| `src/friction_surface/` | Friction builders + `friction_config.py` (all knobs) + `friction_costs.py` (all dollars) |
| `workflows/01..04_*/` | The four steps: thin numbered drivers, per-stage READMEs, run orders |
| `inputs/` | Every input dataset, one home (`inputs/README.md` = provenance + URLs; `MANIFEST.md` = sha256s) |
| `final_network/` | The frozen act-(b)→(c) handoff (zips + field dictionary + checksums) |
| `outputs/` | Gitignored regenerables + committed publication figures/tables/analysis |
| `docs/` | `ARCHITECTURE.md` (engine design), `DATA_CONTRACTS.md` (every inter-stage contract), `API.md` |
| `research/` | Eight tracked decision-record sandboxes behind the engine's rules (see `research/README.md`) |
| `supplementary/` | Blind cost-rate derivations + verification backing every number in `friction_costs.py` |
| `tests/` | pytest suite (run by CI) |
| `.claude/skills/` | Six procedural playbooks (friction, costs, network profile/build) |
| `diagnostics/` | The 2026-08 two-repo merge evidence base (audits + adopted proposal) |

## Old → new commands

The merge renamed the stage scripts (they were flat files in two repos); one
release cycle of translation:

| You used to run | Now run |
|---|---|
| `python -m friction_surface.run_friction_pipeline` | `python workflows/01_friction_build/02_build_friction_stack.py` |
| `python build_corridor_masks.py` | `python workflows/01_friction_build/01_build_corridor_masks.py` |
| `python scripts/normalize_raw.py` (mmnet repo) | `python workflows/02_network_build/00_normalize_raw.py` |
| `bash scripts/run_all.sh` (mmnet repo) | `bash workflows/02_network_build/run_all.sh` |
| `python scripts/export_final_shapefile.py` | `python workflows/02_network_build/06_export_final_network.py` |
| `python load_final_network.py` | `python workflows/03_multimodal_join/02_load_final_network.py` |
| `python weight_network_edges.py` | `python workflows/03_multimodal_join/03_weight_network_edges.py` |
| `python assemble_weighted_graph.py` | `python workflows/03_multimodal_join/04_assemble_weighted_graph.py` |
| `python run_validation_query.py` | `python workflows/04_duckdb_export/01_run_validation_queries.py` |
| `python query_duckdb.py` | `python workflows/04_duckdb_export/02_inspect_schema.py` |

(There is no `--skip-surfaces` flag and the ingest step does **not** unzip the
handoff itself — `01_extract_network_handoff.py` does; both old claims were
documentation bugs, now fixed.)

## Preprocessing the friction inputs

The friction stack expects grid-aligned rasters (land cover, slope, permafrost,
12× sea ice, 12× river ice) snapped to the canonical `lulc.tif` grid
(EPSG:3338, 150 m, 28,000 × 16,567). They are regenerable-only (~12 GB):

- **GEE** (terrain, land cover, sea ice): `src/friction_surface/friction_preprocessing/gee_friction_layer_multi_data_processing.js` in the Earth Engine Code Editor → `inputs/gee_exports/AK_Stack_150m.zip` → unzip into `inputs/friction_rasters/`.
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
- `CITATION.cff` — how to cite (paper metadata pending — see MIGRATION_SPEC §6)
