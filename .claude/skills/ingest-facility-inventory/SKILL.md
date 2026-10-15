---
name: ingest-facility-inventory
description: Bring a new bulk-fuel facility-inventory release (a fresh AEA/DCRA download) or a
  new source (e.g. the ACEP gateway file) onto the canonical clean schema as a tracked release
  under inputs/raw_facility_data/<release>/, and diff it against the previous release. Use when
  the owner has a new inventory download, when a source's columns changed, or when adding a
  source adapter. Do NOT use to decide or record corrections (record-facility-corrections) or to
  validate/publish the clean table (validate-facility-inventory).
---

# Ingest a facility-inventory release

The intake phase of the inventory-QC skill set: the analogue of `align-to-ak-stack`. Every
source must land on one canonical schema (`inputs/inventory_qc/facility_schema.csv`) the way every
raster must sit on the AK_Stack grid. Differences between releases are evidence — the 2025
release confirmed three proposed corrections and removed 71 duplicate rows — so each release is
tracked.

## Core invariants (always true)

1. **The raw file is never committed and never edited.** It carries personal contact fields.
   Only the safe-column snapshot, manifest, `SOURCE.md` (with the raw sha256) and the diff are
   tracked. `.gitignore` blocks `Utilities_Bulk_Fuel_Inventory*.csv` under `raw_facility_data/`.
2. **Contact columns are never read.** The source adapter (`inputs/inventory_qc/sources/<source>/
   column_map.csv`) marks them `never`; the loader parses only `keep`/`fold` columns.
3. **`record_id` is the key.** It must be present and unique on every row (AEA `GlobalID`).
   Corrections and release diffs are keyed on it; a source without a stable id needs an adapter
   decision before ingest, not a made-up id.
4. **Fail loudly on schema drift.** A kept column missing from the raw file stops the ingest;
   unknown new columns are reported, not kept, until added to the column map.
5. **Snapshots are regenerable from the pinned raw file** — `01_ingest.py --check` re-derives
   them; never hand-edit one.

## Where the canonical values live

- `inputs/inventory_qc/facility_schema.csv` — the clean schema (name, type, unit, required).
- `inputs/inventory_qc/sources/<source>/column_map.csv` — one adapter per source:
  `source_column, schema_column, type, keep (yes|fold|no|never), fold_into, reason`.
- `inputs/raw_facility_data/<release>/` — `SOURCE.md`, `<source>_inventory_<release>.csv`,
  `snapshot_manifest.json`, `diff_<prev>_to_<release>.csv`; `README.md` explains the layout.
- `inputs/MANIFEST.md` — sha256 of every tracked release file and every raw file.
- `workflows/00_inventory_qc/01_ingest.py` — the loader (`--release`, `--source`, `--check`).

## Procedure: a new release of an existing source

1. **Checksum the download** (`shasum -a 256`) and compare with the latest `SOURCE.md`. Identical
   → nothing to ingest; say so.
2. **Pick the label**: the release year (`2026`); a second release in a year gets a suffix (`2026-06`).
3. **Ingest**: `python workflows/00_inventory_qc/01_ingest.py RAW.csv --release <label>`.
   It writes the release folder and the diff. If it fails on a missing column, the source schema
   changed → step 6.
4. **Fill in `SOURCE.md`** (download date, by whom, publisher note) and add the raw sha256 and the
   snapshot sha256 to `inputs/MANIFEST.md`. Never list the raw file as tracked.
5. **Read the diff** (`diff_<prev>_to_<label>.csv`, summary in `snapshot_manifest.json`) and report
   in plain language: records removed / added; records edited beyond the ~1 m map-point jitter and
   which fields. Then check `corrections.csv`: a correction whose target the publisher fixed will
   fail the `old_value` guard in stage 02 — list those as "candidates to retire" for
   `record-facility-corrections`; do not retire them yourself.
6. **Hand off** to `validate-facility-inventory`.

## Procedure: a new source (or a changed schema)

1. Create `inputs/inventory_qc/sources/<source>/column_map.csv`: every raw column gets a row;
   contact/person columns are `never`; map what fits the schema; `fold_into` for a secondary
   column that fills a schema column when blank.
2. If the source has no stable per-record id, STOP and surface it to the owner: a `record_id`
   must come from the data, not be invented.
3. Ingest with `--source <source>`; detectors that need columns the source lacks will skip
   themselves (`detectors_run.csv` says so) — that is expected.
4. Decide with the owner whether the source is **authoritative** (feeds the clean table) or
   **evidence only** (e.g. the ACEP gateway file, owner decision 2026-10-06); record it in
   `docs/INVENTORY_QC_PLAN.md`.

## What NOT to do

- Do NOT commit the raw CSV, open it in a tool that re-saves it, or copy contact columns anywhere.
- Do NOT overwrite a release folder for a different download — new download, new label.
- Do NOT edit a snapshot CSV, manifest or diff by hand.
- Do NOT retire or edit corrections here — report candidates to `record-facility-corrections`.

## Related

- `record-facility-corrections`, `validate-facility-inventory` — the other two phases.
- `docs/inventory_notes/aea_map_point_vs_latlon.md` — why a publisher "fix" may not show in lat/lon.
- `inputs/raw_facility_data/README.md` — the release-folder contract.
