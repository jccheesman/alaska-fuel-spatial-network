# Workflow 00 reassessment — coordinate universality and raw-data lineage

Written 2026-11-14 for the owner to read and decide on. Two concerns raised after
the Astra audit: (1) coordinates are not handled in one universal way — some were
changed manually, some flagged by code; (2) the raw data must be preserved and
copied with incremented changes until a finalized clean dataset. Section A lays
out what the workflow does today, stage by stage; B and C assess each concern
against it; D is the decision list. Nothing in this document changes anything.

---

## A. The current workflow, stage by stage

Every stage reads its predecessor's file and writes a NEW file — no stage edits
its input, and nothing ever writes the raw CSV. "Tracked" = committed to git.

| # | Stage | What it can change | What it preserves / records | Output tracked? |
|---|---|---|---|---|
| 0 | Raw publisher CSV | — (immutable; no code writes it) | SHA-256 in `SOURCE.md` + `inputs/MANIFEST.md`; local copy kept beside the manifest (never committed — contact fields) | no (checksummed) |
| 1 | `01_ingest` → `aea_inventory_<rel>.csv` | **Nothing.** Selects the 28 safe schema columns, types them, keeps raw row order (`source_row`) | The snapshot IS the raw values for every kept column; manifest records every column kept/dropped/never-read; diff vs previous release | **yes** |
| 2 | `02_apply_corrections` → `facilities_corrected.csv` | **The only stage that changes field values** — and only via owner-approved, `old_value`-guarded rows of `corrections.csv` (today: 9 latitude + 9 longitude + 38 community_name + 28 exclusions) | `corrections_log.csv` (old → new, reviewer, date, outcome, per row — tracked); `excluded.csv` (nothing is deleted; every excluded row kept whole with its reason — tracked) | corrected: no (regenerable) · log + excluded: **yes** |
| 3 | `03_normalise` → `facilities_normalised.csv` | **Nothing in source fields.** Adds derived columns only (`community_key` from aliases, `delivery_barge/plane/road`) | `name_report.csv` records every alias fold | no (regenerable) |
| 3b | `03b_assign_facility_ids` | Adds `facility_id` from the append-only ledger | the ledger (`facility_ids.csv`) never rewrites a number | — |
| 4 | `04_detect` | **Nothing** — flags only (shared farms/points, typos, map-vs-attribute, capacity mismatch, placeholder dates, envelope) | `flags_structural.csv`, `detectors_run.csv` | **yes** |
| 5 | `05_boundary_check`, `05b_assign_region` | **Nothing** — verifies labels, describes regions; never relabels or moves | `flags_boundary.csv`, distances, region tables | **yes** |
| 6 | `06_review_queue` | Nothing — collects undecided non-info flags into the owner's sheet | decisions return as new `corrections.csv` rows (the loop closes through stage 2, never by editing a table) | **yes** |
| 7 | `07_publish` → `facilities_clean.csv` | Two rule-based publications (owner-decided 2026-11-14): pre-1900 placeholder dates → blank; adds `capacity_status` + the other declared derived columns | contract checks (row reconciliation, schema-only columns, determinism, fixtures); `qc_report.md` enumerates everything | **yes** |

So the lineage chain is:

```
raw CSV (immutable, checksummed)
  → snapshot            (tracked; raw values, safe columns)      [stage 1]
  → corrected           (+ corrections_log, excluded — tracked)  [stage 2]
  → normalised          (+ derived columns only)                 [stage 3]
  → clean / published   (tracked; contract-checked)              [stage 7]
```

Any published value traces back to raw: the snapshot holds the original, the
log holds every change with reviewer/date/evidence, and the 2026-11 republication
was verified field-by-field to change in exactly the enumerated ways.

---

## B. Concern 1 — "coordinates are not handled in a universal way"

### What Astra actually observed

The dataset has **two coordinate representations** with different histories:

1. `ASTFacilityLatitude/Longitude` (→ our `latitude/longitude`) — the attribute pair.
2. `X/Y` (→ our `map_x/map_y`) — the publisher's EPSG:3338 map point.

The publisher fixed three records (Hooper Bay, Noorvik, Point Lay) by moving the
**map point only**; our eight approved coordinate corrections fix **lat/lon
only**. So across records, "which representation is right" differs — that is the
non-universality.

### What is already universal here (and worth keeping)

- **One consumed position.** Workflow 02's facilities entry reads ONLY
  `latitude/longitude`. `map_x/map_y` routes nothing, snaps nothing, builds
  nothing — it rides along as publisher evidence.
- **One change mechanism.** "Manual" and "code-identified" coordinate fixes do
  not exist as separate paths: a detector only *suggests* (review queue); every
  actual change is an owner-approved `corrections.csv` row applied by stage 2
  with an old-value guard and a logged reviewer/evidence/date. The difference is
  the *evidence source*, and that is recorded per row.

### The real gaps

1. **Stale map points on corrected records.** After a lat/lon correction, the
   published `map_x/map_y` still holds the publisher's wrong point. Anyone
   comparing the two columns re-derives the original error. (The
   `map_point_disagrees` detector knowingly skips corrected records, so it
   doesn't resurface them — but the stale values are still published.)
2. **No per-record position provenance.** `corrections_applied` lists corrected
   fields, but there is no plain column saying "this position is the publisher's"
   vs "this position is an owner correction".

### Options

- **Option 1 — declare + label (smallest).** Keep values as they are. Publish a
  derived `coordinate_source` column (`publisher` | `owner_correction`) and state
  the universal rule in the schema/README: *`latitude/longitude` is the canonical
  position consumed downstream; `map_x/map_y` is publisher evidence, never
  consumed.* Gap 2 closed; gap 1 documented but not fixed.
- **Option 2 — synchronize on correction (recommended).** Everything in Option 1,
  plus: when stage 2 applies a lat/lon correction it also recomputes
  `map_x/map_y` from the corrected position (EPSG:3338) and logs both changes.
  Published representations then always agree; the raw map point stays in the
  snapshot and the log. This is exactly Astra's "set one canonical position,
  recalculate both representations, preserve the rejected one". ~15 lines in
  `apply_corrections.py`, 16 new log rows, 8 records change in the published
  table.
- **Option 3 — publish one representation only.** Drop `map_x/map_y` from the
  published table (keep them in the snapshot for evidence and for the
  `map_point_disagrees` detector, which runs pre-publish). Maximally universal —
  the clean table has exactly one position — but the publish step would need an
  explicit "snapshot-only column" mechanism (today schema columns flow through),
  and readers lose the publisher's point without going back a stage.

### On "manual vs code-identified" more broadly

The same universality question applies to *evidence classes* inside
`corrections.csv`: 53 corrections were approved one-by-one, 27 exclusions follow
an owner-stated rule, and evidence strings range from "address verified on raw
CSV" to "confirmed via satellite imagery". These all share one mechanism and one
audit trail already; if more uniformity is wanted, the cheap step is a controlled
`evidence_kind` vocabulary (address / imagery / publisher-fix / rule / register)
added as a column — a classification exercise over 90 rows, no behavior change.

---

## C. Concern 2 — raw preserved, incremented copies, one finalized clean dataset

### Already carried through

The chain in §A is precisely the "immutable raw → incremented copies → finalized
clean" design: four successive full tables, each stage writing a new file, every
value change logged, exclusions kept whole, publish contract-checked and
byte-deterministic (a second run reproduces the identical file; CI re-derives
the snapshots from raw whenever the raw is present).

### Gaps against the strictest reading ("preserve every original column")

1. **16 non-contact raw columns are not in any tracked copy** (they exist only in
   the checksummed, uncommitted raw). Most are empty/constant (`EntityId`,
   `AV_Gas_Capacity`, `ASTFacilityState`, `Last_Visited_Surveyed`,
   `Data_Source_Link`, `FacilityLocated`) or redundant (`Date_Last_Modified`,
   `created_date`); four are free text the column map flags as possibly carrying
   personal names (`Comments`, `Description_of_Tank`, `Location_of_Tanks`,
   `Recommendations_by_AEA`) — deliberately excluded. The genuinely recoverable
   candidates, if wanted, are **`Tank_Category`, `Distance_to_Barge_Mooring`,
   `Fuel_Supplier`, `CommunityLocated`** — one `column_map.csv` edit + snapshot
   regeneration each (the raws are on this machine; done safely this week for
   the `uscg_id` drop in the other direction).
2. **The two intermediate tables are gitignored.** The increments exist on every
   machine that runs the workflow but not in git history. They are
   deterministically regenerable from tracked inputs (that is what CI proves),
   so tracking them adds no information — but if you want the increments
   *visible* in the repository, tracking `facilities_corrected.csv` and
   `facilities_normalised.csv` costs two ~1,800-row files per release that churn
   with every corrections edit.
3. **Lineage is spread across files** (corrections_log, name_report, flags,
   qc_report, ledger). A single per-record view ("what happened to this record
   at every stage") could be one more sheet in `inventory_ledger.xlsx`,
   assembled from the existing CSVs — presentation only, no new truth.

---

## D. Decisions for the owner

1. **Coordinate universality:** Option 1 (label only), **Option 2 (label +
   synchronize map point on corrected records — recommended)**, or Option 3
   (publish one representation)?
   → **DECIDED 2026-11-14: Option 2, implemented.** Stage 02 recomputes
   `map_x/map_y` from a corrected lat/lon (16 `applied-sync` log rows on 8
   records; publisher originals in the snapshot), `coordinate_source`
   (`publisher` | `owner_correction`, blank when unlocated) is published, and
   `map_point_disagrees` now runs on corrected records too as the sync's
   tripwire. Grounding evidence: of the 8 corrected records, the map point was
   right only for Kodiak and Coldfoot — the other six were wrong in BOTH
   representations, agreeing to the meter, so neither raw column can be
   universally authoritative; the reviewed correction is the only universal rule.
2. **Evidence vocabulary:** add a controlled `evidence_kind` column to
   `corrections.csv` (classify the existing 90 rows), or leave free-text
   evidence as is?
3. **Intermediates:** keep `facilities_corrected/normalised` regenerable-and-
   ignored (status quo, recommended), or track them so every increment is in
   git history?
4. **Dropped raw columns:** recover any of `Tank_Category`,
   `Distance_to_Barge_Mooring`, `Fuel_Supplier`, `CommunityLocated` into the
   tracked snapshot? (The free-text/contact columns stay out under the privacy
   rule either way.)
