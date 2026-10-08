# Plan: facility-inventory cleaning workflow (v2)

Revised 2026-10-06 after review against the friction-layer skill set. Nothing here has been committed or applied. Every phase ends at an owner-approval gate.

## Goal

Turn any bulk-fuel facility source (today: the AEA/DCRA inventory; later: a new AEA release, the ACEP gateway file, or something else) into one clean, documented facility table that both repositories read. Code does the deterministic checks, agent skills do the judgement and paperwork, and the owner approves every data change. A new download should take about an hour of review.

## Design principles (borrowed from the friction-layer skills)

| Friction layer | This workflow |
|---|---|
| One canonical grid (`AK_Stack_150m`) every raster must sit on | One canonical **clean schema** (`facility_schema.csv`) every source must map onto |
| `align-to-ak-stack` brings a new raster onto the grid | `ingest-facility-inventory` brings a new source onto the schema |
| `friction_config.py` is the single source of truth for values | `inputs/inventory_qc/*.csv` is the single source of truth for corrections, aliases and exceptions |
| `run-friction-pipeline` runs a chain and interprets each failure | `validate-facility-inventory` runs the inventory chain and interprets each failure |
| Known upstream bugs recorded as notes (`[[river_ice_winter_zero_pockets]]`) | Known inventory bugs recorded as notes (`[[aea_shared_tank_farm_ids]]`, …) |
| "Fix at the source, not the symptom"; "don't loosen a check to pass" | Same, verbatim |

## Core invariants (non-negotiable)

1. **The raw file is never edited.** Every change lives in `corrections.csv` with evidence, reviewer and date.
2. **Contact fields are never read.** The source adapter reads only columns its column map marks as kept. Publish asserts that only schema columns reach any output.
3. **No record disappears silently.** Every exclusion carries a logged reason; the hub build's 50 m merge must write a `site_members` table so the trail continues past the inventory.
4. **The boundary check verifies; it never relabels.** Communities without a boundary, or missing from a reference list, are kept as labelled.
5. **Fix at the source, not the symptom.** A bad label is corrected in `corrections.csv`, never by special-casing a script. A detector threshold is never loosened to make a run pass.
6. **Nothing is committed, and the network of record is never re-exported, without owner approval.**
7. **One clean table feeds both repos.** The harness never re-derives a facility from raw data.

## The canonical clean schema

`inputs/inventory_qc/facility_schema.csv` — columns `name, type, unit, required, description`. Fixed across sources; changing it is a schema version bump with a note.

| Group | Columns |
|---|---|
| Keys | `record_id` (stable per-source id; required), `source_row`, `ast_facility_id`, `aea_id`, `uscg_id`, `tank_farm_id`, `tank_farm_evaluation_id` |
| Place | `community_id`, `community_name`, `street_address`, `postal_code` |
| Position | `latitude`, `longitude` (required), `map_x`, `map_y` |
| Facility | `entity_name`, `delivery_method`, `total_capacity`, `gasoline_capacity`, `diesel_capacity`, `jet_fuel_capacity`, `other_fuel_capacity`, `number_of_tanks` |
| Provenance | `source_dataset` (e.g. `aea_2025`), `source` (AEA / DEC / USCG), `report`, `inspected_by_uscg`, `last_inspected`, `last_edited` |

Each source gets an **adapter**: a column map `inputs/inventory_qc/sources/<dataset>/column_map.csv` with columns `source_column, schema_column, type, keep, fold_into, reason`. `keep` ∈ {yes, fold, no, never}; `fold_into` names the schema column a secondary field fills when blank (replaces the hardcoded `Delivery_Methods` fold). A source that lacks a schema column leaves it empty; the detectors that need it skip themselves (below).

## Where things live

Data repo `alaska-fuel-spatial-network` (the hubs are built there; the harness vendors a snapshot and reads the published table):

```
workflows/00_inventory_qc/
  01_ingest.py            adapter: raw → schema (snapshot + manifest + diff vs pinned release)
  02_apply_corrections.py approved corrections.csv rows, keyed by record_id, old_value-guarded
  03_normalise.py         aliases → community_key; delivery flags
  04_detect.py            detector registry (see below)
  05_boundary_check.py    label vs boundary, mismatches only
  06_review_queue.py      review.xlsx for the owner
  07_publish.py           facilities_clean.csv + qc_report.md + publish checks
inputs/inventory_qc/
  facility_schema.csv     the canonical schema
  sources/<dataset>/column_map.csv   one adapter per source
  corrections.csv         approved decisions (record_id, field, old_value, new_value, evidence, reviewer, date, status)
  aliases.csv             community-name normalisation (variant → canonical, community_id)
  remote_sites.csv        accepted boundary exceptions (record_id, reason, reviewer, date)
  boundaries/             DCRA City_Boundaries + Census_Designated_Place_Boundaries (public; checksummed)
  MANIFEST.md             checksums + dates of every pinned input (raw releases, boundaries, gateway file)
tests/inventory_qc/       one test per detector and per publish check; today's known cases as fixtures
docs/inventory_notes/     known upstream bugs, one note each
.claude/skills/
  ingest-facility-inventory/   validate-facility-inventory/ (with scripts/validate_inventory.py)
  record-facility-corrections/
```

### Tracked releases: `inputs/raw_facility_data/<release>/`

Each inventory release is committed as a **safe-column snapshot**, labelled by release year (`2022/`, `2025/`; a second release in a year gets a suffix such as `2025-12/`):

```
inputs/raw_facility_data/
  README.md                      what a release folder holds; how to add one
  2022/
    bulk_fuel_data.zip           the existing committed bundle (full 2022 CSV + processed files + Fuel_Delivery_Method.zip), MOVED here unchanged; still extracted by tools/extract_inputs.py
    SOURCE.md                    download date, AEA service, full raw file SHA-256, row counts, notes
    aea_inventory_2022.csv       clean-schema columns only, raw row order kept (source_row); CSV so GitHub diffs line by line
    snapshot_manifest.json       checksums; columns kept / dropped / never read; folded fills; unknown columns
  2025/
    SOURCE.md · aea_inventory_2025.csv · snapshot_manifest.json
    diff_2022_to_2025.csv        per-record added / removed / edited, generated by 01_ingest.py, never hand-edited
  <next release>/                same layout; a second release in a year gets a suffix (2025-12/)
  gateway_2026/                  ACEP public_bulk_fuel (CC-BY-4.0) may be committed in full, with its own SOURCE.md
```

From the 2025 release on, the **full raw CSV is not committed** (personal contact fields); its SHA-256 in `SOURCE.md` lets anyone verify a local copy. The 2022 bundle `bulk_fuel_data.zip` stays tracked for now (owner decision 2026-10-06: leave the full zip, move it into `2022/`); whether to replace it with the safe snapshot is decision 1b below. Release-to-release diffs are evidence: the 2025 release removed 71 duplicate rows and moved Hooper Bay, Noorvik and Point Lay into their labelled communities, confirming three proposed corrections. Text fields have internal line breaks normalised to ` | ` at ingest so a line-ending change between releases is not reported as an edit. 

## The chain (what each step gates)

Order matters: corrections are keyed by `record_id` and must be applied **before** normalisation, so an alias change can never move a correction's target.

| # | Step | Gates | Fails when |
|---|---|---|---|
| 1 | **Ingest** | schema conformance; release tracking | a kept column is missing from the raw file; `record_id` missing or duplicated; an unknown column appears (reported, not kept); the release folder's manifest checksum does not match `SOURCE.md` / `inputs/MANIFEST.md`. Writes `raw_facility_data/<release>/` and the diff against the previous release |
| 2 | **Apply corrections** | correction integrity | an `approved` row's `old_value` no longer matches (AEA fixed it, or the key moved) → reported, not applied; a `pending`/`rejected` row is never applied |
| 3 | **Normalise** | label coverage | a label maps to nothing in `aliases.csv` or the boundary names → reported as "new community name" |
| 4 | **Detect** | structural checks | any detector finds a record not already covered by an approved correction or exception |
| 5 | **Boundary check** | label/position agreement | a labelled record sits inside another community's boundary (`mismatch`, reviewable); one inside no boundary at all (`outside`) is info only — a remote site with its home-town label (owner 2026-10-08) — and its km is published as `community_distance_km`; communities without a boundary produce no rows |
| 6 | **Review queue** | — | writes `review.xlsx`; never fails |
| 7 | **Publish** | output contract | any publish check below fails. Output: `outputs/00_inventory_qc/<release>/` — `facilities_clean.csv` (tracked; CSV so it diffs), `qc_report.md`, `corrections_log.csv`, `excluded.csv`, `name_report.csv` |

**Publish checks** (also run by CI in `--check` mode):
- row reconciliation: raw rows = published rows + excluded rows, every exclusion with a reason;
- every applied correction has reviewer and date;
- only schema columns in the output; no contact column name anywhere;
- regression fixtures stay fixed (Bethel < 66°N; nothing labelled Unalaska on Norton Sound; Kodiak on land; the six "relabel to keep farm" rows still carry a farm);
- rerun on identical inputs → byte-identical outputs;
- every pinned input's checksum matches `MANIFEST.md`; a drifted boundary file or gateway file is reported as "reference layer changed";
- every committed release snapshot re-derives byte-identically from its manifest (CI recomputes `snapshot_csv_sha256`).

## Detector registry (stage 4)

Each detector declares the schema columns it needs and is **skipped with a note** when a source lacks them, so a new source runs the subset it can support.

| Detector | Needs | Finds |
|---|---|---|
| `shared_farm_id` | `tank_farm_id`, `community_name` | one farm id on several communities; names the farm's own record (label matches where the point sits) or `NONE` |
| `within_farm_copies` | `tank_farm_id`, `total_capacity` | rows repeating a farm's total (capacity must be counted once) |
| `shared_point_labels` | `latitude`, `longitude`, `community_name` | one coordinate under several labels |
| `one_digit_typo` | `latitude`, `longitude`, `community_name` | a single-digit edit lands in the labelled community |
| `map_point_disagrees` | `map_x`, `map_y`, `latitude`, `longitude` | AEA's map point ≠ lat/lon (how the Kodiak/Coldfoot fixes were found) |
| `missing_fields` | — | no coordinates / label / delivery / capacity |
| `spelling_variants` | `community_id`, `community_name` | one id, several spellings |
| `release_diff` | pinned previous release | added / removed / moved / relabelled since last release |
| `external_disagrees` | optional gateway file | position or label differs from the ACEP file (evidence only) |

Thresholds (20 km boundary, 50 m duplicate, 10 km typo match) live in `inputs/inventory_qc/thresholds.csv`, not in code.

## Agent skills (phase-based, matching the friction set)

| Skill | Phase | Use when | Procedure (summary) | Never |
|---|---|---|---|---|
| `ingest-facility-inventory` | intake | a new AEA release, or a new source such as the gateway file | checksum it; write or extend the source adapter; run stage 1; diff against the pinned release; summarise added/removed/moved/relabelled in plain language; propose which corrections AEA has resolved | overwrite the pinned release; read contact columns; invent a `record_id` |
| `record-facility-corrections` | change config | the owner returns a review workbook, or asks for a one-off fix | validate entries (coordinate sign, decimal degrees, contradictions, missing evidence/reviewer/date); write approved rows to `corrections.csv` / `aliases.csv` / `remote_sites.csv`; list questions for the owner | apply pending/rejected rows; guess an ambiguous entry; edit the raw file |
| `validate-facility-inventory` | build and validate | after either skill above, or before any network build | run `scripts/validate_inventory.py` (read-only by default, `--publish` to write); fix the earliest failure first; interpret each failure into cause + owning config file or skill; never report done on a non-zero exit | loosen a threshold; edit a published table in place; skip a failing step |
| `build-and-verify-network` (existing) | network | hub/network build | new prerequisite: `validate_inventory.py` exits 0 on the inventory the profile points at | — |

Each `SKILL.md` follows the house sections: core invariants · when to use / do not trigger · where the canonical values live · procedure · what NOT to do · related.

## Known upstream bugs (notes to write)

- `[[aea_shared_tank_farm_ids]]` — 21 farm ids carry records from 2–6 communities; the label is the record's own data, position and capacity are the farm's. 6 farms have no correctly-labelled row.
- `[[aea_unalaska_unalakleet_swap]]` — f001606/f000147 coordinates swapped; CommunityID matches the label on both.
- `[[aea_map_point_vs_latlon]]` — AEA's Dec-2025 fixes moved the map geometry only; the lat/lon columns both pipelines read were not updated.
- `[[aea_within_farm_copies]]` — a farm's rows all repeat the farm total; AEA deleted 66 such copies in 2025.
- `[[gateway_drops_unlisted_communities]]` — the ACEP file omits ~130 records whose community is not on its master list (Haines, Eagle River, Fort Wainwright, …).

## Phases and approval gates

| Phase | Work | Owner approves |
|---|---|---|
| **0 (done)** | investigation, decision log, boundary prototype, draft column map, stage-1 prototype (scratch) | this plan |
| **1a (done 2026-10-06)** | schema + AEA adapter(s) + stage 1; `raw_facility_data/2022/` and `2025/` committed; `corrections.csv` seeded from the ready decisions; `MANIFEST.md`; tests | the seeded `corrections.csv` |
| **1b** | stages 2, 3, 7 + `aliases.csv` + `run_all.sh` driver + tests; first published `facilities_clean.csv` for release 2025 | the published table and its QC report |
| **2 (built 2026-10-06)** | stages 4–6: detector registry, boundary check (city + CDP boundaries tracked under `inputs/inventory_qc/boundaries/`), review queue; `remote_sites.csv` (empty until the owner reviews the queue); tests with the audit's cases as fixtures | the first review queue (`outputs/00_inventory_qc/2025/review_queue.csv`) |
| **3** | the three skills + orchestrator script; `build-and-verify-network` prerequisite; the five bug notes; CI `--check` job | skill text |
| **4 (built 2026-10-07)** | data repo: `00_normalize_raw.py` reads the latest published `outputs/00_inventory_qc/<release>/facilities_clean.csv`; `inventory.record_id` in the profile carries each record through consolidation; `consolidate` emits `member_record_ids`/`n_members` and the pipeline writes `output/01_site_members.csv`. Harness `build_facility_tables.py` wiring and the `mmnet-toolkit` re-snapshot are deferred (owner 2026-10-06: data repo only; final network extracted manually) | before/after comparison of sites; no network rebuild until phase 5 |
| **5 (code built 2026-10-07; rebuild pending)** | hub-builder fixes, all profile-driven: `tag` tests every labelled facility and keeps + reports conflicts (`01b_conflicts.csv`); hubs group by the canonical corrected label (`group_by: [community]`, `inventory.community_key`), unlabelled sites outside places by `buffer_dist` blob; `cannot_link_across_community` in the 50 m merge; `max_snap_dist_m: 25000` + snap-collision merge (`02_hub_snaps.csv`); `02_hub_members.csv`. Tests: `tests/test_hub_builder.py`. **Still to do: one rebuild of the network of record on the owner's machine** (needs `data/raw`, R + the friction rasters) and its re-export | the rebuild and re-export (zips, checksums, `EXPECTED`, edge-keyed tables) |

Phases 1–4 change no network output. The network of record changes only in phase 5, once — that
rebuild has not happened yet (the container has no `data/raw`, R or rasters); until it does, the
committed `final_network/` and the stage-03 `EXPECTED` tripwire describe the 2026-09-15 build.

## Phase-1a commit plan (approved 2026-10-06; executed on `claude/hub-audit-investigation-dukz8z`)

Branch `claude/hub-audit-investigation-dukz8z` in the data repo. House rule: move-only commits are separate from edit commits.

**Commit 1 — move only.** `git mv inputs/bulk_fuel_data.zip inputs/raw_facility_data/2022/bulk_fuel_data.zip`. Bytes unchanged (sha256 `184181c0…`), so `inputs/MANIFEST.md`'s checksum stays valid; only its path column changes in commit 2.

**Commit 2 — edits + new files.**

| File | Change |
|---|---|
| `.gitignore` | replace `!inputs/bulk_fuel_data.zip` with `!inputs/raw_facility_data/` + `inputs/raw_facility_data/**/Utilities_Bulk_Fuel_Inventory*.csv` (the full raw CSV can never be added by accident); negate the release-folder files |
| `tools/extract_inputs.py` | `TARGETS` key → `inputs/raw_facility_data/2022/bulk_fuel_data.zip`; docstring line 4 and the `fdm_zip` comment; extraction destination unchanged (`inputs/bulk_fuel_data/`) so every downstream path still works |
| `inputs/MANIFEST.md` | path of the zip row; add rows for `2022/aea_inventory_2022.csv`, `2025/aea_inventory_2025.csv`, `2025/diff_2022_to_2025.csv` and the two raw SHA-256s (recorded, file not tracked) |
| `source_scripts/friction_surface/friction_costs.py` (3 mentions), `friction_paths.py` (1), `CLAUDE.md` pipeline table | update the zip path in comments / error text / table |
| `inputs/raw_facility_data/README.md`, `2022/{SOURCE.md, aea_inventory_2022.csv, snapshot_manifest.json}`, `2025/{SOURCE.md, aea_inventory_2025.csv, snapshot_manifest.json, diff_2022_to_2025.csv}` | new (built and reviewed in scratch) |
| `inputs/inventory_qc/facility_schema.csv`, `inputs/inventory_qc/sources/aea/column_map.csv` | new: the canonical schema and the AEA adapter |
| `workflows/00_inventory_qc/01_ingest.py` | new: today's `snapshot.py` + the release-folder/diff writer, `--release <label>` CLI |
| `tests/inventory_qc/test_ingest.py` | new: ingest reproduces both committed snapshots byte-for-byte from their raw files (skipped when the raw file is absent, checksum-asserted when present); contact columns never appear |
| `inputs/README.md` | one paragraph pointing at `raw_facility_data/` |

Not touched: `inputs/bulk_fuel_data/` extraction target, `data/`, the network of record, the harness.

**After commit 2:** `python tools/extract_inputs.py` and the stage-01/02 workflows run exactly as before; `python workflows/00_inventory_qc/01_ingest.py --check` re-derives both snapshots.

## Decisions (owner, 2026-10-06)

1. **Base release: AEA 2025**, keyed on `record_id`. The 2022 bundle `bulk_fuel_data.zip` stays tracked in `inputs/raw_facility_data/2022/`. Corrections keyed on 2022 `record_id`s carry over unchanged (every 2025 record exists in 2022); the 9 corrections that targeted records AEA deleted are retired automatically by the `old_value` guard.
2. **Gateway file (ACEP `public_bulk_fuel`): evidence only** for now. Its rows are used by the `external_disagrees` detector and the `public_says` column, never merged into the facility table. Whether to adopt its 295 AEA-2024 assessment rows is a later, separate decision (they lack ids and may duplicate older farm rows).
3. **Review decisions:** the owner's `corrections_decisions.xlsx` (2026-10-06) seeded `inputs/inventory_qc/corrections.csv`: 53 approved rows (37 labels, 8 coordinate pairs), 2 rejected, 8 pending (7 open questions + the Delta Junction→Healy Lake confirm).
4. **Borough boundaries: not used.** Communities without a city or CDP boundary are skipped by the check and kept as labelled.
6. **Outside every boundary is not a review item (2026-10-08).** Of 76 `outside` rows only one was a copied coordinate (caught anyway by `shared_point_labels`); the rest are repeaters, radar sites, mines, camps and hatcheries correctly labelled with the nearest town. They leave the queue (268 → 195 rows). What matters for them is hub membership, not the label, so the hub builder's `remote_site_km` (20 km, profile) gives a far site its own hub instead of dragging the town's centroid; the 61 `mismatch` rows beyond 20 km stay in the queue and are isolated the same way until decided.
11. **Withhold, never fix (2026-10-08).** The owner has no authoritative source for the 35 records still under review (1.1 % of capacity, 29 communities, none left without a record). The clean table publishes `qc_status` (clean | pending_review = open review-queue item); the profile's `hubs.withhold_pending_review` ON/OFF flag keeps those records out of consolidation and hubs (`output/01_withheld.csv`). A decision or an upstream fix flips the status on the next run and the record enters the next rebuild with no code change. The owner's hypothesis that some shared points are one hub serving several villages (schools, AVEC) is a review decision, not a build rule: if confirmed, the rows are relabelled or excluded through corrections.csv.
10. **Repeatable by script (2026-10-08).** The chain runs as one Python entry point (`validate_inventory.py`, `--publish` to refresh outputs); derived columns are declared in `inputs/inventory_qc/derived_columns.csv` and checked at publish (missing or undeclared fails), and `00_normalize_raw.py` reads that list so a new variable reaches the build with no code edit; a returned review queue is turned into correction rows by `record_corrections.py` (dry run, validation, questions instead of guesses, `--write`).
9. **Service community vs physical place are both kept (2026-10-08).** The clean table publishes `community_name` (the labelled = service community; what the hub builder groups on, never changed by rule) next to `located_in_place` (the city/CDP polygon the point physically sits in) and `community_relation` (inside / adjacent / remote / elsewhere / untested). Boundaries describe; they never decide. Only `elsewhere` rows (35) are review material, and the question for each is which of the two columns is wrong.
8. **Near mismatches are the same town (2026-10-08).** A labelled site inside a neighbouring Census place within `boundary_review_km` (Badger/North Pole, Kodiak Station/Kodiak, Nikiski/Kenai, Fritz Creek/Homer, Kalifornsky/Soldotna) has a correct label and correct coordinates; the hub builder groups by label, so nothing is wrong. Info, never reviewed: 40 rows leave the queue (101 → 61). The 25 far mismatches stay: 13 are copied coordinates (stack rule), 12 are singles for a map look.
7. **Stacked tank farms (2026-10-08).** Keep the row whose community matches the farm's coordinates; drop the same-capacity copies on that farm id (27 exclusions, guarded on `tank_farm_id`); a farm with no matching row has no clear winner and stays in the decision queue (4 orphan farms, 12 rows). Queue 195 → 101 rows. Two earlier "reject the move" rows (Perryville farm 621, Toksook Bay farm 830) are superseded and retired.
5. **Thresholds: approved** as in the table below (typo radius lowered to 3 km); each lives in `inputs/inventory_qc/thresholds.csv` with its reason, and changing one is a config change reviewed like a correction.

### Thresholds

| Name | Value | Used by | What it does | Evidence from this inventory |
|---|---|---|---|---|
| `boundary_buffer_m` | 2,000 | boundary check | a record this close outside its own boundary still counts as a match (tanks at airstrips / barge landings just outside the CDP) | 61 records match only via the buffer; none is a known error. 500 m → 43, 1 km → 54, 5 km → 96 |
| `boundary_review_km` | 20 | boundary check | a mismatch farther than this from its own boundary is "review"; nearer is "low" (neighbouring place) | review flags 140 / 121 / 114 / 96 at 10 / 20 / 30 / 50 km; known errors caught 72 / 72 / 69 / 62 of 74 |
| `typo_match_km` | 3 | `one_digit_typo` | a one-digit edit landing this close to the label's cluster is a typo candidate | all 3 confirmed typos land < 1 km; the 4 "possible" ones (all rejected by the owner) matched at 4–8 km, so 3 km excludes them |
| `shared_point_m` | 1 | `shared_point_labels` | coordinates equal within this are "the same point" | 51 stack records share points to the metre; 57 of 130 conflicts sit within 50 m of another community's site |
| `dedup_tol_m` | 50 | data-repo `consolidate` (existing) | rows closer than this merge into one site | 1,838 → 1,489 sites; 32 cross-community merges at 50 m vs 23 at 1 m → the cannot-link rule (phase 5) matters more than the number |
| `label_spread_km` | 30 | first-audit detector (retained as `far_from_label`) | a record this far from its label's main cluster is reported (info) | 57 records; mostly remote sites with a home-town label |
| `last_mile_m` | 25,000 | harness `build_hub_facility_map` (existing) | local vs remote facility→hub link | unchanged by this plan |

## Risks

- **Source schema changes** → stage 1 fails loudly; only the adapter's column map needs editing.
- **A correction made obsolete by an upstream fix** → the `old_value` guard reports it; `ingest` proposes retiring it.
- **Boundary or alias false positives for remote sites** → `remote_sites.csv`, approved once, checked by `record-facility-corrections`.
- **Repos diverging** → both read one published table; CI compares its checksum in both repos.
- **Threshold creep** → thresholds live in config with a reason column; invariant 5.
