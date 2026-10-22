# Alaska bulk-fuel multimodal network

[![CI](https://github.com/jccheesman/alaska-fuel-spatial-network/actions/workflows/ci.yml/badge.svg)](https://github.com/jccheesman/alaska-fuel-spatial-network/actions/workflows/ci.yml)

Companion code and data for the Data-in-Brief spatial-network paper: how much it
costs, per gallon and per month, to move bulk fuel along every edge of Alaska's
multimodal transport network (road + barge + air + seasonal ice road).

The repository is one pipeline across four steps, which are found in the numbered
folders under `workflows/`, with a facility-inventory QC gate (`00_`) feeding the
network build. Each is described below:

| Step | Workflow | What it does | Key output |
|---|---|---|---|
| (0) | `workflows/00_inventory_qc/` | QC a raw AEA/DCRA bulk-fuel inventory release into the published clean facility table that act (b) reads — apply owner-approved corrections, normalise community keys, run detectors + boundary check, build the review queue, publish | `outputs/00_inventory_qc/<release>/facilities_clean.csv` |
| (a) | `workflows/01_friction_build/` | Build monthly environmental friction surfaces for Alaska (terrain, land cover, permafrost, sea/river ice) on the canonical 150 m EPSG:3338 grid | `outputs/01_friction_build/friction_stack/` (14 TIFs) |
| (b) | `workflows/02_network_build/` | Build the connected multimodal network from the facility inventory (act 0's published clean table) + connectivity layers with the region-agnostic `mmnet` engine (`profile.yaml` holds every region-specific choice) | `final_network/network_joined_{nodes,edges}.zip` |
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

python tools/extract_inputs.py    # unzip the committed inputs/*.zip bundles
bash run_all.sh                   # run as far as the data on disk allows
```
A fresh clone runs the ingest half of step **(c)** (extract the frozen
network, load its 84,094 nodes / 93,049 edges into DuckDB) and all of step
**(d)** from committed data alone. The weighting and costing stages of (c)
additionally need the friction stack from (a), and the costing stage reads
`inputs/bulk_fuel_data/raw/Fuel_Delivery_Method.shp` (shipped inside
`inputs/raw_facility_data/2022/bulk_fuel_data.zip`; `tools/extract_inputs.py`
unpacks it). Steps (a) and (b)
need regenerable-only inputs — each stage's `run_all.sh` gates on what is
missing and prints exactly how to regenerate it (`EXTERNAL_DATA.md` is the
honest inventory of what exists where).

To run the test suite and linter, install the dev extra
(`uv sync --extra dev`, then `uv run pytest tests/` and `uv run ruff check`),
which is what CI does.

**Final friction stack TIF files are hosted on Google Earth Engine at:**

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
bash workflows/02_network_build/run_all.sh     # needs data/raw (inputs/network_raw.zip — local-only, license-gated)
bash workflows/03_multimodal_join/run_all.sh   # stages 01-02 run from committed data; 03-04 need the friction stack
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

`final_network/` is the network-of-record: the joined multimodal
network (84,094 nodes / 93,049 edges / 329 fuel hubs / 4 components / 99.99%
giant) exported by act (b) and ingested by act (c). Its shapefile **row order
defines `edge_id`** for every DuckDB table, so the committed zips are
checksummed (`inputs/MANIFEST.md`) and preserved byte-identical.

**Provenance:** re-exported 2026-10-15 — the first export carrying the
phase-5 hub builder, the corrected 2025 facility inventory (workflow 00's
`facilities_clean.csv`), the 25 km connect-to-giant / barge-transfer reach and
the 2 km snap-to-edge hub fallback, plus the hub handoff
(`final_network/hub_members.csv`, `hub_snaps.csv`). The road source is still
the 2026-09 AK DOT&PF download alone, and the user-authored manual-connections
layer is still included. It supersedes the 2026-09-15 AK-DOT-only export and
every earlier one (all preserved in git history; the version list is in
[`docs/CHANGELOG.md`](docs/CHANGELOG.md)). A re-export is a *new*
network-of-record and invalidates every edge_id-keyed table, so the zips,
checksums, the `EXPECTED` tripwire and the downstream tables must be
regenerated together. Full provenance: `final_network/README.md`.

> **The costed tables lag the network.** `edge_month_weights` / `edge_costs`
> were not regenerated with the 2026-10-15 export (they need the friction
> stack). Rerun workflow 03 in full on a machine that has it before using the
> costed graph.

## Where things are

| Path | What |
|---|---|
| `source_scripts/mmnet/` | The region-agnostic network engine (R-noding oracle included) — the single canonical copy |
| `source_scripts/friction_surface/` | Friction builders + `friction_config.py` + `friction_costs.py` (all USD $) |
| `source_scripts/inventory_qc/` | Workflow 00's facility-inventory QC chain, one module per stage (the numbered scripts are thin wrappers) |
| `source_scripts/fuel_network/` | Workflow 03's load / friction-weighting / costing, and the weighted-graph API analysis code imports |
| `source_scripts/repo_paths.py` | Every repository location, defined once; scripts import it instead of computing paths |
| `workflows/00..04_*/` | The inventory-QC gate + the four steps: thin numbered drivers, per-stage READMEs, run orders |
| `inputs/` | Committed input bundles + the inventory-QC config; `inputs/README.md` opens with a "where is X?" index by theme |
| `final_network/` | The frozen act-(b)→(c) handoff (zips + hub handoff CSVs); regenerable with the source scripts, but a re-export is a new network-of-record |
| `outputs/` | Gitignored regenerables + committed figures, tables and the published clean facility table + the DuckDB deliverable (`outputs/README.md`) |
| `docs/` | `DATA_DICTIONARY.md` (what every field means, with units), `DATA_CONTRACTS.md` (every inter-stage contract), `ARCHITECTURE.md` (engine design), `CHANGELOG.md` (network-of-record versions), `INVENTORY_QC_PLAN.md` + `data_audit/` (the facility-inventory QC plan and its 2026-10 investigation) |
| `tests/` | pytest suite (run by CI) |
| `.claude/skills/` | Nine procedural playbooks (friction, costs, network profile/build; inventory ingest/record-corrections/validate) |

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
- `docs/INVENTORY_QC_PLAN.md` — the facility-inventory QC plan + numbered owner decisions; the
  `ingest-`/`record-`/`validate-facility-inventory` skills run the chain, and `docs/data_audit/`
  archives the 2026-10 investigation that produced the decisions
- `docs/TEST_LOG.md` — the verified end-to-end friction → weighting → costing run
- `EXTERNAL_DATA.md` — what exists where (committed / regenerable / absent)
- `CLAUDE.md` — the lab notebook: one row per numbered script, with findings
- `docs/DATA_DICTIONARY.md` — field meanings and units for the handoff, the DuckDB tables and
  the clean facility table
- `docs/CHANGELOG.md` — every network-of-record version, with counts and what changed
- Cost-rate derivations and verification: the `supplementary/` folder was removed on 2026-08-14
  and survives in git history at commit `b35b730`; the live rates and their source notes are in
  `source_scripts/friction_surface/friction_costs.py`, audited by the `derive-fuel-costs` skill
