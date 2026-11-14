# The 2026-11 Astra data audit: reconciliation and disposition

In November 2026 the owner ran two external audit sessions (ChatGPT's Astra
model, 2026-11-12/13) over the bulk-fuel facility inventory, working against a
separate clone with the pre-workflow-00 layout. The sessions produced a
cross-version comparison (2022 vs 2025 vs a fresh "2026" download), an issue
census, a proposed deterministic cleaning workflow (`00_inventory_qc_astra`),
and two handoff documents. The raw output lives on the owner's machine
(`~/Desktop/DataAuditAstra_2026.11.12/`); this document records what this
repository did with each recommendation, so the audit is closed out rather than
re-litigated. Adopted changes landed on branch `astra-audit-qc-improvements`
(2026-11-14, owner decisions recorded per item).

## 1. Findings already handled before the audit

The audit could not see `workflows/00_inventory_qc/` (its clone predated it), so
its priority list largely re-derived decisions already in `inputs/inventory_qc/`:

| Astra finding | Disposition here |
|---|---|
| 8 map/attribute coordinate conflicts > 100 m (its "priority review" table) | All resolved. Kodiak + Coldfoot: approved lat/lon corrections in `corrections.csv`. Hooper Bay, Noorvik, Point Lay and the three Kuspuk School District rows (Lower/Upper Kalskag, Red Devil): owner-approved exclusions 2026-10-08 — tank-farm copies, not mislocated facilities. |
| 8 locally reviewed coordinate candidates (its Appendix C) | They ARE this repo's correction register: the audit read a staged copy of `corrections.csv` (90 entries, 80 approved) and reflected it back. |
| 5 physical-community reassignments (Appendix D) | Already approved `community_name` corrections, applied by stage 02. |
| 71 removed records = duplicate cleanup; 66 match survivors | Matches `diff_2022_to_2025.csv` and the release README. |
| Publisher map moves changed X/Y but not lat/lon — "a pipeline reading only attributes misses them" | Known: `map_point_disagrees` (stage 04) flags exactly this, and the three records are excluded anyway. |
| Shared points, shared farm ids, copied farm rows, name variants, missing fields | Covered by the existing stage-04 detectors (`shared_point_labels`, `shared_farm_id`, `within_farm_copies`, `spelling_variants`, `missing_fields`) and the stage-05 boundary check. |
| "Create a review queue; apply only guarded, approved corrections; never auto-merge" | That is workflow 00's architecture (old_value-guarded `corrections.csv`, review queue, exclusions with reasons, output-contract checks). |

## 2. Findings adopted (branch `astra-audit-qc-improvements`, 2026-11-14)

| Astra finding | What landed |
|---|---|
| The "2026" download is byte-identical to the 2025 release (SHA `3fbee569c63d…`) | Recorded in `inputs/raw_facility_data/README.md`: no new release exists; verify the SHA before re-ingesting. |
| 12 capacity discrepancies (total vs populated per-fuel sum; its Appendix E) | New stage-04 detector `capacity_mismatch` (threshold `capacity_mismatch_gal`): components above the total = high (6, a physical contradiction), below = medium (6, possibly an incomplete breakdown). Owner 2026-11-14: **all 12 are review items** — they sit in `review_queue.csv` as `pending_review` until decided, and are never repaired by arithmetic. |
| 10 placeholder inspection dates (1899-12-30/31, the Esri epoch) | New info detector `placeholder_inspection_date` (9 survive exclusion); stage 07 publishes them **blank** (owner 2026-11-14) — the raw values stay in the release snapshot. |
| Capacity eligibility as an explicit dimension | One declared derived column `capacity_status` (`ok | missing | mismatch`) in `facilities_clean.csv`, so capacity figures can filter or footnote unreliable totals. Unknown stays unknown — never zero. |
| Broad Alaska plausibility envelope | New detector `alaska_envelope` (lat 50–72, lon ≤ −129 or ≥ 170): flags nothing on the corrected release; exists so a future release's gross coordinate error cannot arrive silently. |
| `<Null>` artifacts in `USCG_ID` | Owner 2026-11-14: the field is unused downstream — dropped from the clean schema entirely (`column_map.csv` keep=no); both release snapshots regenerated from raw and re-verified byte-identical under `--check`. |
| "Synchronize coordinate representations; set one canonical position; record provenance" | Adopted as Option 2 of `docs/WORKFLOW_REASSESSMENT_2026-11.md` (owner 2026-11-14): stage 02 recomputes the publisher map point from a corrected lat/lon (logged `applied-sync`; originals in the snapshot), `coordinate_source` is published per record, and `map_point_disagrees` verifies agreement on every located record. |

## 3. Proposals NOT adopted, and why

| Astra proposal | Why not |
|---|---|
| The parallel `00_inventory_qc_astra` workflow (run.py + patches.json + baseline_records.csv + review_cases.csv) | It duplicates machinery this repo already has (guarded corrections = `corrections.csv`; review cases = `review_queue.csv`; baseline = tracked snapshots + release diffs + determinism checks), has no facility-id ledger or region handoff (both load-bearing for the harness), and its own README says not to point the network at its output. Its good ideas were ported as the items in §2 instead. |
| All-61-column "enriched" outputs (every raw column preserved, contacts included) | House rule: contact columns are never read, never committed (`column_map.csv` marks them `never`; the publish contract fails on any contact column). Lossless-ness is provided differently — the raw file is checksummed and the safe-column snapshot is tracked. |
| Per-record raw fingerprint baseline (`baseline_records.csv`) | Release-level diffing (`diff_2022_to_2025.csv`, `release_diff` detector) already surfaces upstream edits with less machinery; the snapshots are byte-checksummed. |
| Deriving lat/lon from X/Y for the 63 records missing attributes | Those records are unlocated by design; locating them is an owner evidence decision, not a transformation. The build withholds nothing silently — `missing_fields` flags them. |

## 4. Not independently re-verified

The audit itself notes its historical imagery/address checks were NOT repeated
in 2026; the corrections carrying them keep their original evidence strings and
reviewer (JC). The audit's external-data leads (DCRA community layers, Fuel
Delivery Method service, AEDG gateway) remain unconsumed — each would need
schema/lineage verification before production ingestion (its §9 caveats stand).

## 5. Outcome on the published table (release 2025)

`uscg_id` dropped; `capacity_status` added (1,716 ok · 75 missing · 12
mismatch); 9 placeholder dates published blank; the 12 capacity records moved
`clean → pending_review` (73 open queue rows on 47 records). Row count,
exclusions, facility ids, regions and every other field are byte-unchanged.
Owner decisions on the 12 queue items return through
`record-facility-corrections` as usual.
