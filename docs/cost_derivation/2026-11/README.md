# Cost re-derivation, November 2026

This folder is the record behind the rates and fees in
`source_scripts/friction_surface/friction_costs.py` as of 2026-11-18.

**Read this first.** The addenda, supplements, summary and decision log were written on 2026-11-17 and
2026-11-18, *before* the figures were applied, so they say "proposal; nothing applied". On 2026-11-18 the owner
decided to apply them, and this branch does. The documents are kept as written; this page says what was applied
and how.

## What is applied

All figures are 2026 dollars at CPI-U 332.243 (`index_basis_2026-11-17.md`), per gallon, and per statute mile
for rates. Status words are defined in `CONVENTIONS.md`.

| In `friction_costs.py` | Value | Range | Status | Was | Record |
|---|---|---|---|---|---|
| `BASELINE_RATES_PER_GALLON_MILE["Road"]` | 0.0007 | 0.00045 to 0.0011 | Derived | 0.0007 | `addendum_road.md` |
| `["Barge"]` (now ocean line-haul only) | 0.00021 | 0.00013 to 0.00028 | Derived | 0.0010 blended | `addendum_ocean_linehaul.md` |
| `["BargeRiver"]` (new; per channel mile) | 0.0013 | 0.0009 to 0.0044 | Provisional | 0.0010 blended | `addendum_river_barge.md` |
| `["Plane"]` | 0.016 | 0.013 to 0.024 | Provisional | 0.025 | `addendum_plane.md` |
| `["IceRoad"]` | 0.010 | 0.004 to 0.030 | Assumed | 0.010 (range to 0.025) | `addendum_ice_road.md` |
| `LANDING_CLASS_FEES["road_port"]` | 0.01 | 0.00 to 0.03 | Provisional | 0.24 | `addendum_transfer_fees.md` |
| `LANDING_CLASS_FEES["hub"]` | 0.12 | 0.05 to 0.20 | Provisional | 0.24 | `addendum_transfer_fees.md` |
| `LANDING_CLASS_FEES["coastal_village"]` | 0.65 | 0.40 to 1.15 | Provisional, **assembled** | 0.24 | `addendum_coastal_small_barge.md` |
| `LANDING_CLASS_FEES["river_village"]` | 0.50 | 0.20 to 0.80 | Provisional | 0.24 | `addendum_river_barge.md` |
| `INTERMODAL_TRANSFER_FEES[("barge","overland")]` (fallback only) | 0.04 | 0.01 to 0.10 | Provisional | 0.24 | `addendum_transfer_fees.md` |
| `[("barge","ice_road")]`, `[("overland","ice_road")]`, `[("plane","overland")]` | 0.011, 0.022, 0.025 | unchanged | Assumed | same | `addendum_transfer_fees.md` |

## How the split works in the model

- **Ocean or river.** Each Waterway edge is priced by its marine / river share from the `edge_water_class` table
  (workflow 03 stage 05, sampled from workflow 01's water-class label): marine at the ocean rate, river at the
  river rate, a mixed edge at the length-weighted blend. Workflow 03 now runs stage 05 before stage 04.
- **Landing fees by place.** Each barge landing edge (BargeRoadTransfer, BargeAirTransfer) is given a class by
  `source_scripts/fuel_network/landings.py`: the reviewed table `inputs/network_qc/landing_classes.csv` first, then
  "on the Anchorage road system" (road port), then the river share at its water node (river or coastal village).
  The class that priced each landing is written to the `edge_landing_class` table.
- **Coastal village delivery has no edges of its own.** The derived form is $0.45 per delivery plus 0.0010 per
  sailing mile from the hub or the vessel at anchor. The network has no edge for that sailing leg, so the charge is
  carried flat on the landing: $0.45 + 0.0010 x about 250 miles, less the ocean line-haul the route already pays
  over those miles, which is about $0.65. That flat figure is **assembled, not derived** (decision log, section 5).

## What is not settled

1. **The landing table is proposed, not approved.** `inputs/network_qc/landing_classes.csv` lists ten places as
   hubs (rows marked `proposed`; proposed rows are applied). The owner reviews it: set `status` to `approved` or
   `rejected` and fill `reviewer`. Naknek has no document behind it.
2. **Three verdicts overturn earlier values on one verifier's reading** (plane, the 0.24 fee, the 0.011 river
   rate) and have not had a second independent review.
3. **Two rates are Provisional and one is Assumed.** Report results that depend on them with the range.
4. **The network of record has not been re-costed.** Until workflow 03 is rerun on the owner's machine,
   `outputs/fuel_network.duckdb`, the published tables and figures, and the harness still carry the old costs.
5. Evidence gaps are listed at the end of each addendum.

## Files

| File | What it is |
|---|---|
| `SUMMARY.md` | The result in one page, with the assembly rules and what applying depends on |
| `addendum_*.md` | One per segment: status, result, methods, a derived-versus-assumed table for every input, scope, gaps |
| `supplement_*_2026-11-18.md` | What the second batch of documents added (no status changed) |
| `SOURCES.md` | Register of every source: file, title, publisher, date, link and its basis, where cited |
| `errata.md` | Defects found in the earlier chapters and code comments (seven reported, fifteen more found) |
| `DECISION_LOG.md` | Why the costs were reopened, each decision with date and reason, how the work was run, limits |
| `CONVENTIONS.md`, `index_basis_2026-11-17.md` | Status tiers and input types; the inflation basis |

The source documents themselves are third-party files and are not in this public repository. They are in the
private harness repository (`cost_derivation_resources/`, branch `cost-sources`), with the working files of the
derivation (`blind_derivations/working_2026-11-17/`). References in these documents that begin `harness:` point
there. The earlier chapters that `errata.md` corrects (`blind_derivations/00` to `06`) are also in the harness.
