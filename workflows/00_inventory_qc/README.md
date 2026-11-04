# Workflow 00 — facility-inventory QC (the gate before act b)

Turns a raw AEA/DCRA bulk-fuel inventory release into the published, clean
facility table that workflow 02 consumes. Everything owner-decidable is DATA in
`inputs/inventory_qc/` (corrections, aliases, remote sites, thresholds, declared
derived columns) — the stages apply approved decisions, they never invent them.
Contact columns are never read. The investigation that produced these decisions
is archived under `docs/data_audit/`; the plan and numbered owner decisions are
in `docs/INVENTORY_QC_PLAN.md`.

## Run order

```bash
python 01_ingest.py RAW.csv --release <label>   # raw release -> safe-column snapshot + diff vs previous
python 02_apply_corrections.py                  # owner-approved corrections.csv rows (old_value-guarded)
python 03_normalise.py                          # community_key (canonical + aliases.csv) + delivery flags
python 03b_assign_facility_ids.py [--mint]      # stable facility_id from the append-only ledger (--mint appends new records)
python 04_detect.py                             # detector registry -> structural flags
python 05_boundary_check.py                     # label vs DCRA city + CDP boundary (verify only)
python 05b_assign_region.py                     # AEA energy region per record (inside, else nearest within the cap)
python 06_review_queue.py                       # open flags -> owner review sheet
python 07_publish.py                            # clean table + QC report, after the output-contract checks
# or: bash run_all.sh [RELEASE]                 # chains all of it (default: latest release); 01 runs --check
```

`01_ingest.py --check` re-derives the committed snapshots instead of writing a
new release — that is what `run_all.sh` and CI run. Only `approved` rows of
`corrections.csv` apply, and a stale `old_value` guard fails the stage (retire
the row, never force it). Stage 05 never relabels — a site inside no boundary is
a remote site (info), not a review item; only a mismatch inside *another*
community past `boundary_review_km` is reviewable.

## Inputs

Dataset sources and status (the AEA inventory, the DCRA boundaries, the AEA
region library): `DATA.md` §1.1 and §2.

- `inputs/raw_facility_data/<release>/` — the tracked release snapshots (safe
  columns only; the raw CSV is checksummed, never committed from 2025 on).
- `inputs/inventory_qc/` — `facility_schema.csv`, `sources/<src>/column_map.csv`,
  `corrections.csv`, `aliases.csv`, `remote_sites.csv`, `thresholds.csv`,
  `derived_columns.csv`, `facility_ids.csv` (the append-only facility-id ledger, owner data:
  a record's number never changes once written) and the DCRA `boundaries/`.
- `inputs/region_and_census_data.zip` — carries the AEA energy-region shapefile stage 05b
  reads (extracted on demand).

## Outputs

`outputs/00_inventory_qc/<release>/`: the staged tables (`facilities_corrected`,
`excluded`, `corrections_log`, `facilities_normalised`, `name_report`,
`facility_ids_assigned`, `flags_structural`, `detectors_run`, `flags_boundary`, `boundary_distance`,
`region_assignment`, `aea_regions`, `aea_region_adjacency` (the harness's region tables),
`boundary_summary`, `review_queue` + `.xlsx`) and, from stage 07, the published
**`facilities_clean.csv`** (tracked, regenerated only here) + `qc_report.md`.
`facilities_clean.csv` is the facility inventory workflow 02 reads, and — with `aea_regions.csv`
and `aea_region_adjacency.csv` — the only thing the harness's `build_facility_tables.py` loads:
it carries the facility id, every delivery mode (`delivery_barge/plane/road`), the AEA region and
the QC status, so the harness derives nothing from raw data (plan decisions 15–16).

## Skills (the repeatable procedure)

- **`ingest-facility-inventory`** — bring a new release or a new source onto the
  clean schema as a tracked release and diff it against the previous one.
- **`record-facility-corrections`** — turn the owner's reviewed decisions (a
  returned review queue / workbook, or a one-off) into rows of `corrections.csv`,
  `aliases.csv` or `remote_sites.csv`, with evidence, reviewer and date.
- **`validate-facility-inventory`** — run the whole QC chain and publish; the
  single entry point is `validate_inventory.py [--publish]`.

## Related docs

`docs/INVENTORY_QC_PLAN.md` (plan + owner decisions 1–12) ·
`docs/inventory_notes/` (one note per error pattern) ·
`docs/data_audit/` (the 2026-10 investigation: `report/`, `workbooks/`, `maps/`).
