# Data audit — the facility-inventory and hub investigation (2026-10-05 → 2026-10-09)

The record of how the hub errors were found, what was decided, and how the fixes were
proven. The **live** artefacts (corrections, aliases, thresholds, the published clean table,
the skills) live elsewhere in the repo; this folder keeps the investigation that led to them,
in the order it happened, so a reader can retrace every decision.

Privacy: no file here carries a contact column (names, phones, emails were never read).
Every table is keyed by the AEA `record_id` (GlobalID) or the 2022 harness facility id.

| folder | what is in it |
|---|---|
| `report/` | `REPORT.md` — the root-cause report (R1–R8: source errors, tag check, grouping key, snapping, 50 m merge, borough fallback, nearest-hub map, harness relabel) and its tables: proposed corrections per facility, recovered hub membership (382/385 exact), hub causes, the 121 assignment mismatches, the boundary check, the stacked-farm review |
| `workbooks/` | the review workbooks in the order they were exchanged: `01` sent to the owner · `02` returned with the owner's notes · `03` the owner's decision log (seeded `corrections.csv`) · `04` boundary check · `05` the current review queue (61 rows) + `05b` the 13 far-mismatch singles with a reading of each |
| `maps/` | `map1` coordinate errors · `map2` copied coordinates · `map3` the Fairbanks split (all EPSG:3338) · `map4` the snap experiment, current vs road-first + fallback, with `snap_experiment.py` to rerun it against `final_network/` |
| `diagrams/` | `inventory_flow` (skills, scripts and data; Mermaid source + PNG) · `inventory_errors_explainer` (the six error kinds, before/after) · `skills_explainer` (the five skills) · the drawing scripts |
| `evidence/` | the ACEP public bulk-fuel file (evidence only, never merged — owner 2026-10-06) with its source note · the owner's 2026-10-08 rebuild trails (`02_hub_snaps`, `03_network.md`) that showed 60 unplaced hubs and led to the snap fallback |

## Where the decisions live now

- `docs/INVENTORY_QC_PLAN.md` — the plan and the numbered owner decisions (1–12).
- `inputs/inventory_qc/` — corrections, aliases, remote sites, thresholds, derived columns, boundaries.
- `outputs/00_inventory_qc/<release>/` — the published clean table and the QC report.
- `docs/inventory_notes/` — one note per error pattern (what it looks like, why, how it is handled).
- `.claude/skills/{ingest,validate,record}-facility-*` — the repeatable procedure.

## Not in this folder

The raw AEA download (contact fields) and the extracted intermediates. The raw files are
pinned by sha256 in `inputs/raw_facility_data/<release>/SOURCE.md`.
