# Blind Cost Derivations: Alaska Bulk Fuel Delivery by Mode

**Prepared:** July 15, 2026 (derivations + primary-source verification round)
**Purpose:** Independent, open-web derivation of transport cost in **USD per gallon-mile (2026 dollars)** for each fuel-delivery mode in the DOE MAS fuel-logistics routing model: highway truck, marine barge, aircraft, and winter ice road / snow trail.

## Methodology

Each mode was assigned to a separate research agent operating **blind**: no access to the model's current cost values, to the project's prior derivations, or to each other's work — so no estimate could anchor on an existing number. Each agent was required to:

1. Use at least **three genuinely independent methods** (published tariffs/contracts, engineering cost build-up, and revealed delivered-price differentials from state fuel-price surveys and contracts);
2. Keep a **derivation log** recording every search, source acceptance/rejection, and assumption made at each decision point;
3. Show all arithmetic and state all inflation/currency conversions;
4. Report a point estimate, range, confidence, and an explicit statement of what the figure includes and excludes.

Convergence between independent methods — not any single source — is the evidence standard.

**Verification round (July 15, 2026).** The original derivations were built from search-result snippets because direct page fetching was permission-blocked. After unblocking, a second round of agents fetched every chapter's flagged primary documents — the DCRA Winter 2026 price report (plus the state's ArcGIS community-price service), the State of Alaska heating-oil contract, the DEC/Econ One transport-cost filing, NOAA *Distances Between United States Ports*, the ISER 2010 report, the DCCED 2005 and DEC 2007 studies, the Everts/Wright Air/NAC tariff pages, the USAspending charter award, the UIC haul account, and the 267-page ASTAR trail study — and verified or corrected every load-bearing number in place. Each chapter now carries a dated verification addendum; snippet-era errors (a wrong hub baseline, two misattributed figures, a short route reconstruction, wrong source vintages) are corrected and logged. **All four point estimates survived verification**; the barge per-mile figures shifted ~10% on the NOAA-verified route distance.

**Local-documents round (July 17, 2026).** A third pass read manually downloaded primary documents the web round could not reach: the ATRI 2025 *Operational Costs of Trucking* report, the Econ One refining-industry study, the AEA **PCE FY2025 Statistical Report** (margin-free utility fuel prices by community), the State marine-diesel contract, the NSB FY26–27 budget book, the OMB CWAT project sheet, and the Northwest Arctic Borough **Noatak Winter Fuel Haul System** proposal. **All four point estimates held again.** Highlights: the last snippet-sourced ATRI figures were confirmed against the report's own tables; the plane chapter's assumed Fairbanks wholesale anchor was replaced with an empirical one from road-served PCE communities ($3.60/gal); the ice-road traffic weighting is now data-backed (PCE gallons: Nuiqsut 279k vs. Atqasuk 275k — the assumed 50/50 regime split confirmed); the Noatak proposal confirmed Method A2's physics (3,000–5,000 gal/trip, 10–12 mph, $425K tracked tractor) though it publishes no operating rate; and the PCE data delivered the report's cleanest single fact — **Sleetmute's utility pays $4.49/gal vs. Bethel's $4.45**, meaning ~310 river miles adds essentially zero realized freight and the village's ~$5/gal retail premium is entirely storage/margin/working-capital.

## Results

| Mode | Point estimate ($/gal-mi, 2026$) | Range | Confidence | Basis of convergence |
|---|---|---|---|---|
| **Road** (highway tanker) | **0.0007** | 0.00045–0.0011 | Moderate | Econ One transport map (Valdez→Fairbanks $0.20/gal truck — read off the source deck); ATRI build-up (Tables 8/11 verified: $2.260 avg / $2.32 specialized per mile); 11-point within-vendor state-contract distance regression (slope 0.00067, R² ≈ 0.75); USDOT BCA cross-check |
| **Barge — ocean linehaul** | **0.00023** | 0.00017–0.00039 | Med-high | ISER 2010 build-up (market rate $0.19–0.22/gal verified p. 17); voyage-cycle build-up; NOAA-verified route (Anchorage→Bethel 1,109 nm = 1,276 sm); PCE FY2025 margin-free prices bound from above |
| **Barge — river distribution leg** | **0.011** | 0.006–0.018 | Med-high | DEC 2007 invoice-based rate ($0.007/gal per map mile, verified p. 21); ISER small-barge cost ($0.60/gal typical, verified p. 20); PCE Sleetmute≈Bethel result confirms realized utility gradient is procurement-pooled, not marginal freight |
| **Plane** (bulk fuel by air) | **0.025** | 0.015–0.042 | Med-high | DCRA Jan 2026 revealed premiums (verified vs. state ArcGIS data); DC-6 build-up; ISER benchmark (verified p. 13); exact federal charter award ($11,792.50 / 1,400 gal); PCE FY2025 two-part regression (fixed $1.31/gal + $0.0082/gal-mi at the efficient full-load end) with empirical hub anchor ($3.60, Circle/Central); Wright Air & NAC tariffs corroborate Everts within 0–6% |
| **Ice road / winter trail** (single rate) | **0.010** | 0.004–0.025 | Moderate | Build-up calibrated to the verified 2026 Anaktuvuk haul and corroborated by the Noatak haul-system proposal (loads, speeds, $425K tractor); within-borough DCRA differentials; regime traffic weights now data-backed (PCE gallons ≈ 50/50 Nuiqsut/Atqasuk); Ontario & NWT analogs; Tibbitt–Contwoyto economics |

## Cross-cutting findings

**1. Fixed per-delivery costs dominate short hauls in every mode.** Every derivation independently found a two-part cost structure — a true per-mile rate plus a fixed per-gallon cost per delivery event (truck: ~$0.20/gal distributor/drop fixed; barge: $0.15–0.30/gal hub transfer plus ~$1.50/gal village lightering; plane: ~$2.20/gal per air delivery; ice road: load/unload and mobilization). A flat $/gal-mi therefore systematically underprices short hops and overprices long hauls. Where the model keeps single per-mile rates, the point estimates above are calibrated to each mode's *typical* route length; the fixed components belong in intermodal transfer fees.

**2. Mode ordering is economically coherent.** Ocean barge (0.00026) < road (0.0007) < ice road (0.010) < air (0.025) — each step roughly 3–40× the previous — which reproduces observed behavior: communities barge everything they can, truck what the road system reaches, build winter roads to displace airlift, and fly only what they must.

**3. The mid-2026 fuel price shock is a commodity effect, not a freight effect.** The June 2026 (Iran/Hormuz) price spike moved delivered fuel prices by dollars per gallon, but the estimated freight pass-through is small (e.g., ≈ +$0.02/gal on a barge voyage). All rates here are calibrated to pre-shock (Jan–early-2026) price relationships and are stated in real 2026 dollars.

**4. Retail price differentials overstate freight.** In every revealed-price method, the majority of a remote community's price premium proved to be storage, working capital, and retail margin rather than transport (e.g., ~85–90% of Bethel's $2.78/gal net premium is non-freight). The derivations use differentials only where the non-freight components could be netted out or bounded.

**5. Ice road remains the widest-uncertainty mode.** No published Alaska tariff or operating rate exists for winter fuel hauling — three rounds of verification confirmed this by exhausting the candidate sources (the 267-page ASTAR study contains no fuel-haul dollars; the UIC haul account publishes operations but no cost; the Noatak haul-system proposal specifies the full operation — 20–30 mi route, 3,000–5,000 gal/trip, ~200 trips/season, $425K tracked tractor — but prices nothing, deferring operating cost to "end-user pays"). The mode spans two operationally different regimes — engineered ice roads driven by conventional tankers (~$0.004/gal-mi) and tundra snow trails worked by tracked cat-trains (~$0.02/gal-mi) — and the regime traffic split is now data-backed at ≈50/50 (PCE FY2025 gallons: Nuiqsut 279,232 vs. Atqasuk 274,877), so the single recommended rate ($0.010) is a confirmed midpoint rather than a coin-flip, though it still misprices each regime by ~2× in opposite directions. The one remaining load-bearing assumption is the ~$900/hr convoy rate; a real NSB/UIC contract figure (FOIA-able) would retire it.

## Comparison to current model values

| Mode | Model (`friction_costs.py`) | This derivation (verified) | Assessment |
|---|---|---|---|
| Road | 0.000528 | 0.0007 | Model is at the pure-carriage floor of the derived range; defensible, ~25% low vs. point |
| Barge | 0.000556 | 0.00023 linehaul / ~0.0010 all-in at Bethel distance | Model value sits between linehaul-only and all-in — consistent once lightering is accounted; NOAA-verified route is 1,276 statute mi, not 1,800 |
| Plane | 0.033 | 0.025 | Model ~30% above the verified point estimate; inside the range (upper half) |
| IceRoad | 0.00667 | 0.010 | Model ~35% below the verified point estimate; inside the range (lower half) |

## Report contents

Chapters 1–4 are the four agents' full reports: search strategy, derivation log (steps and decisions), methods with complete arithmetic, source tables with reliability grades, cross-method reconciliation, final estimates, and prioritized follow-ups. Each chapter closes with a **Verification addendum (2026-07-15)** logging exactly which primary documents were fetched, which numbers were confirmed (with page cites), and which were corrected.
