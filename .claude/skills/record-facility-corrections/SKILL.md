---
name: record-facility-corrections
description: Turn the owner's reviewed decisions (a returned review_queue / corrections workbook,
  or a one-off instruction) into rows of inputs/inventory_qc/corrections.csv, aliases.csv or
  remote_sites.csv, with evidence, reviewer and date. Use when the owner returns a review queue,
  approves/rejects a flagged record, accepts a remote site, or asks to retire a correction the
  publisher has fixed. Do NOT use to run the QC chain (validate-facility-inventory), to ingest a
  release (ingest-facility-inventory), or to decide a case the owner has not decided.
---

# Record facility corrections

The change-config phase of the inventory-QC skill set: the analogue of `assign-friction-values`.
`corrections.csv` is the single source of truth for every change to the inventory; nothing else
may alter a facility's label, position or inclusion.

## Core invariants (always true)

1. **Only the owner decides.** This skill records decisions; it never makes one. An ambiguous
   entry (a "reject" with a value given, a note that contradicts the decision, a coordinate with
   no hemisphere) becomes a question for the owner, not a guess.
2. **Every row carries evidence, reviewer and date.** A row without them is `pending`, never `approved`.
3. **Keyed by `record_id`, guarded by `old_value`.** `old_value` is the record's current value in the
   base release; if it later stops matching, stage 02 reports the row instead of applying it.
4. **Corrections fix the source, not the symptom.** A wrong label is corrected in `community_name`;
   a wrong position in `latitude`/`longitude`; a record that should not be in the network is
   `field=exclude` with a reason — never deleted from a snapshot.
5. **Nothing is relabelled or moved by rule.** A boundary mismatch or a shared farm id is a flag;
   the fix is a reviewed row here.
6. **Status vocabulary is closed:** `approved | pending | rejected | retired`.

## Where the canonical values live

- `inputs/inventory_qc/corrections.csv` — `record_id, facility_pid_2022, source_row_2022,
  community_name, field, old_value, new_value, reason, evidence, reviewer, reviewed_on, status,
  decided_in, present_in_2025`. `field` ∈ schema column | `exclude` | `(no change)` | `(undecided)`.
- `inputs/inventory_qc/aliases.csv` — `variant, canonical, basis, decided_on` (name normalisation
  for a community spelled several ways; applied AFTER corrections).
- `inputs/inventory_qc/remote_sites.csv` — `record_id, community_name, reason, reviewer,
  reviewed_on` (owner-accepted sites that sit inside ANOTHER community's boundary but are
  correctly labelled; suppresses the boundary flag only. Sites outside every boundary need no
  entry — they are never reviewed, owner 2026-10-08).
- The clean table's `located_in_place` / `community_relation` describe where a record physically
  sits versus its label; they are derived, never corrected. A correction changes `community_name`
  or the coordinates; the relation re-derives on the next run.
- `inputs/inventory_qc/thresholds.csv` — a threshold change is a config change with a reason row,
  approved by the owner like a correction.
- `outputs/00_inventory_qc/<release>/review_queue.csv|xlsx` — what the owner fills in.

## The script

`scripts/record_corrections.py REVIEW.xlsx` does the mechanical part of the procedure below and
nothing more: it maps each filled `decision` to a row, reads `old_value` from the base release,
validates values and dates, refuses to overwrite a (record_id, field) already decided, and prints
every ambiguity as a QUESTION for the owner instead of guessing. Dry run by default; `--write`
appends. Exit 2 = questions remain. Then run `validate-facility-inventory --publish`.

```
python .claude/skills/record-facility-corrections/scripts/record_corrections.py REVIEW.xlsx          # dry run
python .claude/skills/record-facility-corrections/scripts/record_corrections.py REVIEW.xlsx --write  # append
```

Rule-based decisions the owner states in chat (a stack rule, a class of remote sites) are written
by the agent as rows whose `evidence` names the rule and date, guarded where a guard exists
(`old_value=column=value` for an exclusion).

## Procedure: a returned review queue

1. **Read the decisions** (`decision`, `your_value`, `notes`, `reviewed_by`, `reviewed_on`).
   Map: `approve` → the flag's suggestion becomes the row; `approve with my value` → the owner's
   value; `reject` → `(no change)` row with status `rejected`; `remote site (keep as labelled)` →
   a `remote_sites.csv` row; `ask publisher` / `skip for now` → `pending`.
2. **Validate values**: coordinates as decimal degrees, latitude 51–72 N, longitude −180 to −129
   (west = negative; convert "151.38001° W"); a label must be a real community string; a
   `reviewed_on` date must not be in the future.
3. **Resolve old_value** from the base release snapshot for each `record_id`/`field`; if it
   differs from what the review showed, STOP and ask — the data moved under the review.
4. **Write rows**; keep `decided_in` pointing at the file the decision came from. Append, never
   rewrite history: a reversed decision is a new row with the earlier one set to `retired` and a
   reason.
5. **Hand off** to `validate-facility-inventory` and report counts: approved / pending / rejected,
   and the questions for the owner.

## Procedure: retire a correction the publisher fixed

1. Confirm from the release diff (`diff_<prev>_to_<label>.csv`) or stage 02's
   `skipped-old-value-mismatch` log that the current value already equals (or supersedes) `new_value`.
2. Set `status=retired`, add the release label and evidence to `reason`. Do not delete the row.

## What NOT to do

- Do NOT infer a decision from a note, a map, or your own judgement.
- Do NOT edit `facilities_clean.csv`, a snapshot, or a flags file.
- Do NOT drop a record: use `field=exclude` with a reason. Guard a rule-based exclusion with
  `old_value=column=value` (e.g. `tank_farm_id=377`) so an upstream fix retires it; an
  unguarded exclusion (owner's one-off) has an empty old_value.
- Do NOT relabel by rule, bulk-approve a detector's suggestions, or change a threshold without an
  owner-approved reason row.

## Related

- `validate-facility-inventory` — run after every change here.
- `ingest-facility-inventory` — reports retire candidates after a new release.
- `docs/inventory_notes/` — the known upstream bugs behind most flags (shared farm ids, the
  Unalaska/Unalakleet swap, map point vs lat/lon).
