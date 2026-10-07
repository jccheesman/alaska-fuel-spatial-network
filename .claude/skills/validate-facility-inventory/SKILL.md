---
name: validate-facility-inventory
description: Run the facility-inventory QC chain (workflow 00: ingest check -> corrections ->
  normalise -> detectors -> boundary check -> review queue -> publish) and interpret each
  failure into a cause and a fix. Use after ingesting a new inventory release
  (ingest-facility-inventory), after recording corrections (record-facility-corrections),
  before any hub/network build, or when the owner asks to validate, refresh or debug the
  clean facility table. Do NOT use to ingest a release, to decide or record a correction,
  or to change a threshold — route to the owning skill.
---

# Validate the facility inventory

The build-and-validate phase of the inventory-QC skill set. The two sibling skills each
*change* one thing (a release comes in; a decision is recorded) and then say "now validate"
— this skill owns that step and says what a failure means and where to fix it.

## The inventory-QC skill set

| Phase | Skill | Changes |
|---|---|---|
| Intake | `ingest-facility-inventory` | a new release or source onto the clean schema |
| Change config | `record-facility-corrections` | `corrections.csv`, `aliases.csv`, `remote_sites.csv` |
| **Build + validate** | **`validate-facility-inventory`** (this) | re-run the chain, publish, interpret failures |

Downstream: `build-and-verify-network` requires this chain to exit 0 before a hub build.

## Core invariants (always true)

1. **Validate before trusting the table.** `outputs/00_inventory_qc/<release>/facilities_clean.csv`
   is consistent only if the whole chain passes, read-only and byte-identical to the committed copy.
2. **Inputs gate outputs.** Fix the earliest failing step first; a publish failure usually has its
   real cause upstream (a stale correction, a changed column map).
3. **Fix at the source, not the symptom.** Every failure traces to a config file
   (`inputs/inventory_qc/*.csv`, a source adapter) or a pinned input. Never edit a snapshot,
   a published table, or a flag file by hand.
4. **Don't loosen a check to make it pass.** Thresholds (`thresholds.csv`), regression fixtures in
   `07_publish.py`, and the row-reconciliation rule encode the output contract. A red check is a defect.
5. **Nothing disappears silently; nothing is relabelled by code.** Detectors and the boundary check only
   report. Only an approved correction changes data, and an exclusion always carries a reason.
6. **Never commit the raw inventory CSV** (contact fields). `.gitignore` blocks it; do not negate that.

## The orchestrator

`scripts/validate_inventory.py` runs the chain and prints, under any failing step, the probable
cause and the file or skill that owns the fix.

```
# read-only (default): chain into a temp dir, then compare with the committed published table
python .claude/skills/validate-facility-inventory/scripts/validate_inventory.py

# refresh outputs/00_inventory_qc/<release>/ (same as workflows/00_inventory_qc/run_all.sh)
python .claude/skills/validate-facility-inventory/scripts/validate_inventory.py --publish

python .claude/skills/validate-facility-inventory/scripts/validate_inventory.py --keep-going --release 2025
```

Exit 0 = every gating step passed. CI runs the read-only form.

## The chain (what each step gates)

1. **`01_ingest.py --check`** — every committed release snapshot matches its manifest and (when the
   raw file is reachable) re-derives byte-identically. Fail → a snapshot was hand-edited or the
   column map changed under it: re-ingest from the pinned raw file.
2. **`02_apply_corrections.py`** — every `approved` row applies; its `old_value` still matches.
   Fail → the publisher changed that record: mark the row `retired` (fixed upstream) or update it,
   via `record-facility-corrections`.
3. **`03_normalise.py`** — community keys + delivery flags; reports new spellings in `name_report.csv`.
4. **`04_detect.py`** — the detector registry (`detectors_run.csv` says which ran / were skipped).
5. **`05_boundary_check.py`** — labels vs city/CDP boundaries; `boundary_summary.csv`.
6. **`06_review_queue.py`** — open flags only, for the owner.
7. **`07_publish.py`** — row reconciliation, reviewer+date on every applied correction, schema-only
   columns, regression fixtures, determinism. Fail → see the orchestrator's message; the fix is in
   `corrections.csv`, never in the output.

## Interpreting results that are NOT failures

- `detectors_run.csv` shows `skipped … release lacks [...]` — the source has no such column (e.g. no
  tank-farm ids). Expected for a non-AEA source; not a defect.
- `boundary_summary.csv` "untested: no boundary for this community" — Anchorage, Juneau, Sitka,
  Wrangell, military bases, unincorporated places without a CDP. Kept as labelled by owner decision
  (2026-10-06); not a defect.
- `review_queue.csv` has open items — that is the owner's work, not a failure. Hand the file over.

## Procedure

1. **Identify what changed** (a release, a decision, a threshold, a boundary file) and confirm it
   landed in its single source of truth, not in a script.
2. **Run read-only first.** If the committed table differs from a fresh run, the published outputs
   are stale: run `--publish` and commit the refreshed `outputs/00_inventory_qc/<release>/` together
   with the config change.
3. **Fix the earliest failure first**, in the owning file or skill; re-run until exit 0.
4. **Report**: steps passed, counts from `qc_report.md`, open review-queue items, anything skipped.
   Never report "done" on a non-zero exit.

## What NOT to do

- Do NOT edit `facilities_clean.csv`, a release snapshot, or a flags file to make a check pass.
- Do NOT relax a threshold, a fixture, or the row-reconciliation rule.
- Do NOT apply or decide a correction here — route to `record-facility-corrections`.
- Do NOT commit or push; the owner approves each commit.

## Related

- `ingest-facility-inventory`, `record-facility-corrections` — the change-phase siblings.
- `build-and-verify-network` — requires this chain green.
- `docs/INVENTORY_QC_PLAN.md` — design; `docs/inventory_notes/` — known upstream data bugs.
