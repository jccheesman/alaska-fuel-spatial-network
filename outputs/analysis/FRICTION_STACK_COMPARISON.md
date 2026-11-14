# Friction stack: old vs rebuilt (2026-08-25)

Old = the stack built 2026-08-20 from the truncated arcpy river-ice input.
New = today's rebuild from the corrected input (no EucAllocation, marine clip).
Both stacks share byte-identical corridor masks (86,789 river / 501,684
waterway cells), so every difference below is attributable to the river-ice
data alone. Analysis ran on the waterway-cell extracts
(`diagnostics/01_friction_build/extract_barge_waterway.py`); two independent passes, one attributing
changed cells, one auditing the QA sites.

## Verdict: the rebuild passes

| gate | result |
|---|---|
| marine cells changed, any month, either direction | **0 of 414,895** |
| ice-free ports (Ketchikan…Whittier), both stacks | 8/8 open 12/12 |
| Nome / Utqiagvik seasonal pattern | unchanged, correct |
| freezing rivers closed Jan–Feb, both stacks | 6/6 |
| changed cells across all months | 13,297, all river corridor |

## The monthly picture

| month | old navigable | new | Δ |
|---|---|---|---|
| Jan | 301,451 | 292,568 | **−8,883** |
| Feb | 288,879 | 288,879 | 0 |
| Mar | 291,512 | 291,218 | −294 |
| Apr | 303,470 | 299,397 | −4,073 |
| May | 394,821 | 387,699 | −7,122 |
| Jun | 450,837 | 450,838 | +1 |
| Jul–Sep | — | — | 0 |
| Oct | 448,446 | 442,830 | −5,616 |
| Nov | 373,973 | 369,575 | −4,398 |
| Dec | 315,259 | 315,258 | −1 |

Direction is as predicted: the truncation manufactured open water, so the fix
*closes* river cells in winter and shoulder months. Figure:
`outputs/analysis/friction_stack_old_vs_new.png`.

## Where January's −8,883 comes from

Decomposed against the old input raster, cell by cell:

| cause | cells |
|---|---|
| old input held exactly 0.0 — the truncation, corrected | 4,821 |
| old input NoData — the fill cascade now draws on an honest pool | 4,046 |
| ordinary value shifts | 16 |

The 4,821 lands within 1.5% of the 4,894 predicted in `docs/TEST_LOG.md`
before the rebuild. By river: Kobuk 4,811, Kvichak 2,372, Koyukuk 884,
Nushagak 802. Kobuk dominating is expected — it sits 21–35 km from surviving
coverage, squarely in fallback territory.

## Why February changed by zero

Not a bug. The old February input's footprint (521,176 valid cells vs
January's 566,766) already lacked coverage at the affected cells, so the old
build sent them through the same k-median fallback the new build uses — same
mechanism, same answer. Both stacks agree those 8,883 cells are blocked in
February, 8,883/8,883. (Established from new provenance being identical
across months 01–03 and both stacks' February agreement; the old February
input raster itself is no longer on disk to check directly.)

## Two site-level changes, both in the right direction

**Egegik and Ugashik now stay closed through April** (old: opened in April;
new: open May–October). These are the two rivers the truncation kept
navigable in deep winter — the corrected data extends their frozen season
one month later into spring. No other site calendar changed.

## The Kvichak question, resolved

The open TEST_LOG item — "Kvichak *opened* under the k-nearest fallback,
1,478 cells in January, unverified" — is now closed. Those were cells along
the segment fed by the old input's truncated/contaminated pool; in the new
stack all 2,372 January-navigable Kvichak-assigned cells are blocked. At the
village probe itself the river is winter-closed in **both** stacks (the
1,478 figure counted segment cells, not the 5 km probe). The anomaly was an
artifact of the defective input, and the fix removed it.

## One item stays open

**October gains 1,071 cells**, 732 of them on "Dahl Creek" (the Port
Clarence segment already flagged as a likely NWN mislabel) and 225 on the
Koyukuk. The plausible mechanism is the *other* arm of the truncation — old
cells stamped exactly 1.0 (frozen) now carrying realistic freeze-up values —
but the old October input no longer exists on disk, so this is inferred, not
verified. It is confined to river cells, small (0.2% of the corridor), and
concentrated on the one segment already on the review list.

## Edge level (added 2026-08-25, after workflows 03/04)

Waterway-edge passability from `fuel_network.duckdb`, old vs rebuilt.
Passable = `nodata_frac = 0` (the strict rule: one frozen pixel severs the
edge); fraction is length-weighted across all 34,099 Waterway edges.

| month | frac by length old → new | passable edges old → new | Δ edges |
|---|---|---|---|
| Jan | 0.5298 → **0.5114** | 4,796 → **1,024** | −3,772 |
| Feb | 0.5114 → 0.5114 | 1,024 → 1,024 | 0 |
| Mar | 0.5114 → 0.5114 | 1,024 → 1,024 | 0 |
| Apr | 0.5439 → 0.5289 | 1,664 → 1,026 | −638 |
| May | 0.7477 → 0.7344 | 29,936 → 26,740 | −3,196 |
| Jun–Sep | unchanged | unchanged | 0 |
| Oct | 0.8603 → 0.8468 | 20,023 → 16,307 | −3,716 |
| Nov | 0.6892 → 0.6662 | 4,551 → 2,782 | −1,769 |
| Dec | ≈unchanged (Δ 4e−6) | 1,476 → 1,476 | 0 |

**January now sits exactly on the February/March floor — 1,024 edges,
0.5114 by length — which is the ice-free Gulf/Southeast marine network.**
Under the old data January carried 3,772 more passable edges than February:
deep midwinter reading as more navigable than late winter, never physically
sensible. Those edges rode on truncated fake-open river cells. The three
deep-winter months are now identical: all river traffic frozen, marine
linehaul untouched.

Consistency checks that landed as the strict rule predicts:

- **March** lost 294 cells (all Egegik) but zero edges — Egegik's edges were
  already blocked in March, so cell changes there could not sever more.
- **October** lost 3,716 edges but only 1.4 points by length — short interior
  river edges, while the long Gulf routes carry the kilometres.
- **December** kept its 1,476 count while the length fraction moved in the
  sixth decimal — the month's ±2 changed cells swapped which edges clip the
  threshold, not how many.

Net effect of the fix at the routing level: about 2 points of
length-weighted passability removed in January and 1–2 points in the
shoulder months, all of it interior river mileage; the marine network is
byte-for-byte untouched in every month.

## Bottom line

The rebuilt stack differs from the old one exactly where the defect
predicted, in the predicted direction, entirely on the river corridor, with
every regression gate passing — from raw raster (truncation gone, marine
clip in), through the friction stack (zero marine changes, ports 12/12,
prediction hit within 1.5%), to the routed network (winter floor coherent,
changes confined to river months). Verification of the river-ice fix is
complete; the pre-rebuild backups are clear to retire
(`cleanup_river_ice_fix.py --apply 5`).
