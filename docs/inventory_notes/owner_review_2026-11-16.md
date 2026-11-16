# Owner review 2026-11-16 — manual approvals

**Every change below is a manual decision by the owner (JC), stated in chat on
2026-11-16 and entered by hand as rows of `inputs/inventory_qc/corrections.csv`.
None was produced by a detector, a rule or a script.** The inventory-QC chain
(workflow 00) only applied them: stage 02 checks each row's `old_value` guard
against the 2025 base release and writes the new value; stages 03 to 07 then
re-derive the dependent columns and republish `facilities_clean.csv`.

How the inventory process works, for context: the raw AEA/DCRA bulk-fuel
inventory is ingested as a tracked release; detectors (stage 04) and the
boundary check (stage 05) FLAG suspected errors; a human reviews each flag; the
owner's decision becomes a row of `corrections.csv` with evidence, reviewer and
date; only `approved` rows are applied. Nothing is relabelled, moved or dropped
by rule unless the owner stated the rule, and such rows say so in `decided_in`
(the ledger, `outputs/00_inventory_qc/2025/inventory_ledger.xlsx`, lists them
apart as "Applied by rule"). Every row of this review is in the ledger's
**"Approved by owner"** tab: their `decided_in` names this review, not a rule.

How to find the rows: `reviewed_on = 2026-11-16`, `reviewer = JC`, `decided_in`
one of `chat 2026-11-16 (FAA Nome station)`, `owner review 2026-11-16 (chat):
community codes for earlier relabels`, `owner review 2026-11-16 (chat): pending
decisions approved`. Each approved row's `evidence` begins `MANUAL OWNER
APPROVAL 2026-11-16` (the two FAA relabel rows quote the owner's evidence
directly). History is append-only: a row that was pending is set to `retired`
with a note, and the approval is a new row, so the 2026-10-05 state stays
readable.

## 1. FAA Nome station: Fairbanks → Nome (decided_in `chat 2026-11-16 (FAA Nome station)`)

| Facility | Record | Field | Old | New |
|---|---|---|---|---|
| 1058 FAA – Fairbanks – FAI Shop | `{2B48564F-DF5A-4814-B2B3-21E3157048CA}` | community_name | Fairbanks | Nome |
| 1058 | same | community_id | Fairbanks `{7102AFBB-…}` | Nome `{72E9842F-ABE0-4390-9A93-917EDB1CF17B}` |
| 1060 FAA – Fairbanks – FAI Butler Building | `{9D56DBE7-1A09-4398-8622-73AF3113418C}` | community_name | Fairbanks | Nome |
| 1060 | same | community_id | Fairbanks `{7102AFBB-…}` | Nome `{72E9842F-…}` |

Owner's evidence: both sit at 64.51252, -165.4303, the FAA Nome Station complex
at Nome airport; the FAA Butler Building in Nome is a prefabricated metal
utility/shop structure there (web search). The coordinates are right and the
label was wrong. The two "(undecided)" rows of 2026-10-05 (open questions) are
retired. Before this, the pair formed a separate road-only hub labelled
Fairbanks inside the Bering Straits region (`hub:h000707` in the harness).

## 2. Community codes for seven earlier relabels (decided_in `owner review 2026-11-16 (chat): community codes for earlier relabels`)

The owner relabelled these records earlier; the relabel changed `community_name`
but the record kept the old community's `community_id` (the DCRA community
GUID). See [relabel_keeps_community_id](relabel_keeps_community_id.md). The
owner approved correcting the code to match the label. Each new code is the
community's `CommunityID` in the State of Alaska DCRA Community Overview, and
matches the code every other record of that community already carries (Point
MacKenzie had no other record).

| Facility | Relabel (original decision) | Old code (old community) | New code | Effect |
|---|---|---|---|---|
| 754 University of Alaska Fairbanks – Fort Yukon | Fairbanks → Fort Yukon (2026-10-05) | Fairbanks | Fort Yukon `{641D75DC-…}` | elsewhere 214.64 km → inside |
| 898 Alaska Commercial Company – King Salmon | King Cove → King Salmon (2026-10-05) | King Cove | King Salmon `{DEFFD70D-…}` | elsewhere 520.88 km → inside |
| 1680 (entity "Unknown") | Nightmute → Iliamna (2026-10-06) | Nightmute | Iliamna `{5ADEA6FC-…}` | elsewhere 543.34 km → inside |
| 1654 Lower Kuskokwim Schools | Napakiak → Kwethluk (2026-10-06) | Napakiak | Kwethluk `{FF083E35-…}` | elsewhere 30.63 km → inside |
| 322 DOT&PF APT / MS | Valdez → Cordova (2026-11-14) | Valdez | Cordova `{3921BE55-…}` | elsewhere 61.81 km → inside |
| 592 Dept. of Corrections – Point MacKenzie Correctional Farm | Wasilla → Point MacKenzie (2026-11-14) | Wasilla | Point MacKenzie `{5736B8FC-BE6B-44A6-8A67-0A66F497EDC5}` | elsewhere 31.89 km → inside |
| 595 Dept. of Corrections – Goose Creek Correctional Center | Wasilla → Point MacKenzie (2026-11-14) | Wasilla | Point MacKenzie `{5736B8FC-…}` | elsewhere 32.93 km → inside |

Why it matters: with the old code, the boundary check measured each site
against its old community, and the network build's `remote_site_km` rule (20 km)
made any site farther than that its own hub. With the code corrected each site
is "inside" its community and joins that community's hub at the next build.

## 3. Pending decisions approved (decided_in `owner review 2026-11-16 (chat): pending decisions approved`)

These were decided by the owner on 2026-10-05 (`corrections_decisions.xlsx/Decisions`)
but stayed `pending`: the entries read "reject" with a value given, which the
correction skill treats as ambiguous rather than guessing. On 2026-11-16 the
owner approved them as recorded. The original evidence is kept in each row.

| Facility | Field | Old | New | Owner's evidence (2026-10-05) |
|---|---|---|---|---|
| 1197 Healy Lake Tribal Transportation | community_name | Delta Junction | Healy Lake | "This tank belongs to Healy Lake, not Delta Junction. Confirmed with satellite imagery" |
| 1197 | community_id | Delta Junction `{763EEB4F-…}` | Healy Lake `{093A0B52-9C15-4F33-8872-681E456A939D}` | the code that goes with the relabel (DCRA CommunityID), same decision |
| 797 AT&T – Ketchikan | latitude | 58.37542 | 55.353511 | "located in Ketchikan and has the incorrect coordinates. Confirmed via raw CSV file" |
| 797 | longitude | -134.574986 | -131.684099 | same |
| National Guard Armory, Newtok | exclude | — | true | "Newtok was relocated and Kipnuk was evacuated due to Typhoon Halong. This facility can be dropped" (Newtok's residents moved to Mertarvik) |

One step here is mechanical, not a decision: after the Ketchikan latitude and
longitude were applied, stage 02 recomputed the record's AEA map point
(`map_x`/`map_y`) from the corrected position, because the published map point
still sat on the refuted one. That is the pipeline's standing sync rule (owner
2026-11-14, "Option 2 + map-first"), logged in `corrections_log.csv` as
`applied-sync` with status `derived`.

## Code changed in this review (reporting only; not a decision)

`source_scripts/inventory_qc/ledger.py`, which writes `inventory_ledger.xlsx`,
attached each row's last-run outcome by record, field and old value only. With
this review's append-only history (a retired pending row beside its new
approved row) each such row appeared twice in its tab, once marked "retired",
and the unguarded Newtok exclusion showed no outcome (a blank old value read as
"" on one side and missing on the other). It now also matches on status and
normalises blanks. No correction, published value or gate changed; the ledger
now lists exactly one line per row: 103 approved by owner (all applied), 33
applied by rule, 3 pending, 19 rejected or retired.

## Result (workflow 00 republished; every gate passes)

| | Before | After |
|---|---|---|
| Records kept / excluded | 1,797 / 33 | 1,796 / 34 |
| Corrections approved / pending / retired | 120 / 9 / 2 | 136 / 3 / 8 |
| Records changed by these decisions | — | 11 kept records (1058, 1060, 754, 898, 1680, 1654, 322, 592, 595, 1197, 797) and the Newtok exclusion |
| Side effect (not a decision) | — | record 384 now `pending_review` (see the Point MacKenzie spelling question below) |

## Not decided here (questions for the owner)

- **Spelling of Point MacKenzie.** Correcting the two prisons' code gave
  `{5736B8FC-…}` two spellings: "Point MacKenzie" (the owner's relabel, and
  DCRA's official name) and "Point Mackenzie" on record 384 (Goose Bay Airport
  Maintenance Station). The `spelling_variants` detector now flags 384, which
  is `pending_review` and would be withheld from hubs at the next build. The
  usual fix is an `aliases.csv` row, `Point Mackenzie → Point MacKenzie`.
- **Four more relabels with the old community's code**, found in the same
  check. Today they do no harm (the old community is a census place with no city
  boundary, so the check falls back to the label and reports them correctly),
  but the stored code is still wrong: 51 Anchorage (carries Eielson AFB), 104
  Seward (Fort Wainwright), 632 Healy Lake power plant (Healy), 1858 Arctic
  Village (Stevens Village).
- **Haines.** Nine records labelled Haines carry the Haines Borough code: a
  publisher convention, no correction involved; noted only.
- **Still pending:** Craig (a record placed in Coffman Cove; no value decided),
  Noorvik (an AVEC record with an Anchorage address; "need to confirm"),
  Koliganek (capacity contradiction, asked of the publisher 2026-11-14).

## Next

These reach the network the agents use only through a new network-of-record:
workflow 02 (re-export), workflow 03 on the owner's machine (needs the friction
stack), then the harness adoption (`docs/DATA_PROVENANCE.md` in the harness).
