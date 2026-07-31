# Plane (air fuel delivery) — $/gallon-mile derivation

## 1. Search strategy

**Tooling constraint (disclosure):** `WebFetch` and `Bash` (curl) were both permission-blocked in the original session. The derivation below was originally built from WebSearch result snippets. **Update 2026-07-15: the primary sources have now been fetched and verified; corrections are propagated throughout and summarized in the Verification addendum at the end.** The one material error found: the Fairbanks *heating fuel* baseline was $4.05, not $3.34 ($3.34 is gasoline only). **Update 2026-07-17 (second pass, local documents): the AEA FY2025 PCE Statistical Report by Community was read page-by-page; Method A″ was upgraded from a four-community sketch to a mode-screened distance regression, and the Fairbanks hub anchor is now empirical (see the dated second-pass note in the Verification addendum). Point estimate held at $0.025.**

Search sequence (all July 2026):
1. Carrier/aircraft identification: "Everts Air Fuel DC-6 bulk fuel delivery rural Alaska", C-46 tanker, "Alaska Air Fuel Wasilla DC-4".
2. Revealed prices: Alaska DCRA Fuel Price Report (Winter 2026 PDF, January 2026 survey), community-specific queries (Anaktuvuk Pass, Arctic Village, Alatna, Hughes, Lime Village, McGrath/Nikolai), AHFC fuel survey, PCE statistical reports (AEA), KYUK/ADN/Alaska Beacon/KNBA 2026 fuel-crisis coverage.
3. Operating economics: DC-6 fuel burn (PMDG/prop-liners technical data), avgas prices (AirNav July 2026), airtanker contract rates.
4. Bounding tariffs: Everts Air Cargo rates, Wright Air Service freight prices, Northern Air Cargo (NAC) rates, Alaska Air Cargo.
5. Revealed federal procurement: USAspending.gov contracts to Everts Air Fuel, Inc.
6. Distances: airmilescalculator.com (FAI–AKP, FAI–ARC), NPS/pilot sources for Coal Creek airstrip; remaining distances computed by spherical approximation from community coordinates (stated where used).
7. Benchmark study: ISER (UAA) *Components of Alaska Fuel Costs* (2010) — found the key published $/gallon/100-air-miles figure.

## 2. How bulk fuel moves by air in Alaska (carriers, aircraft, pricing structure)

- **Everts Air Fuel** (Fairbanks International west ramp, plus Kenai) is the dominant carrier — "the primary source of fuel for most rural villages in the state" ([alaska.org, "Pipeline in the Sky"](https://www.alaska.org/detail/pipeline-in-the-sky)). Aircraft: **Douglas DC-6A/B** tankers (FAA-certified internal aluminum tanks, split-load capable, 2,000–5,000 gal per Everts; 5,000–6,000 gal cited for short hauls; ISER cites "4,900-gallon DC-6") and **Curtiss C-46** tankers (roughly half a DC-6 load) for shorter/rougher strips ([evertsair.com/fuel](https://evertsair.com/fuel), [AOPA 2005](https://www.aopa.org/news-and-media/all-news/2005/november/pilot/legendary-aircraft-extraordinary-service)). Weight, not tank volume, binds for diesel: Everts' stated average DC-6 payload is 28,000 lb ≈ **~4,000 gal of diesel** (7.05 lb/gal) or ~4,700 gal of gasoline (6.1 lb/gal).
- **Alaska Air Fuel, Inc.** (Wasilla) flies **Douglas DC-4/C-54** tankers, delivering Jet A, 100LL, mogas and heating oil statewide since 2012, often hauling Crowley-supplied product (e.g., the 2024 fatal C-54 accident was a fuel run Fairbanks→Kobuk) ([Wikipedia](https://en.wikipedia.org/wiki/2024_Alaska_Air_Fuel_Douglas_C-54_crash), [alaskaairfuel.com](https://www.alaskaairfuel.com/)).
- Very small communities/lodges get drummed or small-tank fuel in Caravan/CASA-class aircraft (e.g., Glenn Air) at much higher unit cost.
- **Pricing structure:** bulk fuel air service is sold **on a charter basis only** (Everts states this explicitly) — the customer (village corporation, city, utility, North Slope Borough, federal agency) pays for the round trip; the aircraft returns empty. Villages then retail the fuel with local tank-farm and margin costs on top. So there are two distinct "costs per gallon-mile": (a) the **charter transport component** and (b) the **delivered retail premium** (charter + local storage/handling/margin). Both are derived and kept separate.
- The DC-6/C-46/DC-4 fleet burns **100LL avgas**, a major and volatile cost input (national average $7.44/gal, Alaska region FBO average $10.97, July 2026, [AirNav](https://www.airnav.com/fuel/report.html)).
- Air delivery is the year-round backstop: barge-served villages that miss the barge window also fly fuel in "at even higher prices" ([KYUK, Apr 2026](https://www.kyuk.org/economy/2026-04-20/alaska-villages-can-already-pay-10-or-more-for-a-gallon-of-fuel-a-war-driven-spike-could-produce-a-survival-scenario)).

## 3. Derivation log (steps and decisions)

1. **Identified carriers/aircraft** (Everts DC-6/C-46; Alaska Air Fuel DC-4; charter-only pricing). Decision: model the DC-6 as the reference vehicle; treat C-46/DC-4 (smaller strips) as a cost-up variant.
2. **Chose the January 2026 DCRA survey as the price baseline** (calls placed Jan 6–28, 2026) because it *predates* the June 2026 Iran/Hormuz price shock — premiums computed within one survey date net out the commodity price level entirely. Rejected June–July 2026 news prices (Hooper Bay $8.44 gas, etc.) for the premium method because the shock was propagating unevenly through communities (and Hooper Bay is barge-served anyway).
3. **Collected air-only community prices (Jan 2026; verified 2026-07-15 against the DCRA Winter 2026 PDF and the DCRA CDO ArcGIS layers, survey calls Jan 6–28, 2026):** Anaktuvuk Pass commercial heating fuel **$9.97** and gasoline **$9.97** (residential HF $1.50 is NSB-subsidized — rejected as non-market; DCRA: the subsidy "is not extended to commercial businesses"); Arctic Village heating fuel **$15.00**, gasoline **$10.00**; Hughes heating fuel **$13.00**, gasoline **$11.50**; Alatna heating fuel **$8.50**, gasoline **$11.50** (vendor: City of Allakaket). Hub baseline **corrected**: Fairbanks gasoline **$3.34** (University Chevron) but heating fuel **$4.05** (Alaska Petroleum) — the snippet-era assumption that both were $3.34 was wrong; all HF premiums now use $4.05. Checked and absent from the Winter 2026 survey layers: Lime Village, Takotna, Stony River, Chalkyitsik, Venetie, Birch Creek, Allakaket, Fort Yukon, Beaver, Rampart, Koyukuk, Nikolai, Bettles (no records — not surveyed or no reporting vendor). Hughes/Alatna mixed-mode ambiguity noted (occasionally reached by small Koyukuk barges in high water, but predominantly flown; retained with caveat — Alatna's HF at $8.50 vs gasoline $11.50, and Hughes's FY2025 PCE fuel at $4.94, both hint at some barged product). Rejected McGrath as "air-only" — Crowley still barges 250–300k gal/yr upriver ([akbizmag](https://www.akbizmag.com/industry/transportation/no-port-no-problem/)).
4. **Established distances:** FAI–Anaktuvuk Pass **252 mi**, FAI–Arctic Village **237 mi** ([airmilescalculator.com](https://www.airmilescalculator.com/distance/fai-to-akp/)); Coal Creek strip **124 NM = 143 statute mi** east of FAI (pilot guide). Computed FAI–Allakaket/Alatna ≈ **180 mi** and FAI–Hughes ≈ **205 mi** by spherical approximation from coordinates (assumption, ±5%).
5. **Found the ISER published benchmark (verified 2026-07-15 against the local PDF, p. 13):** "With current aviation fuel prices, the most competitive air deliveries have a transportation component of **~$1.25 per gallon per hundred air miles**. The price is even higher for the many villages with airports unable to accommodate the 4,900 gallon DC-6 transport planes operated by Everts Air Cargo." Same page: flying fuel is only cost-effective "to communities within a few hundred miles of Kenai or Fairbanks and then only in quantities of less than five thousand gallons." (ISER/UAA, *Analysis of Rural Alaska Fuel Markets*, Feb 17, 2010 — the document served at the componentsoffuel3.pdf URL; note it attributes the DC-6s to "Everts Air Cargo".) This is the only directly published $/gal-mile figure found; adopted as an independent anchor (Method C-ii).
6. **Found a revealed federal charter transaction (verified 2026-07-15 via the USAspending API):** contract 140P9725F0047 — **$11,792.50 obligated** to Everts Air Fuel, Inc. (DOI/NPS), description "FUEL AMOUNT AND TYPE - 1400 GALLONS OF UNLEADED FUEL DELIVERY LOCATION - COAL CREEK CAMP AIRSTRIP", period of performance starting Sept 18, 2025 (recorded PoP end June 30, 2030; place of performance listed as Fairbanks, AK). Adopted as Method A′ (small-lot revealed price). The earlier "~$12K rounded" band is retired — the amount is exact.
7. **Built the DC-6 cost model (Method B):** fuel burn from type data (2,000 lb/hr at long-range cruise ⇒ ~333 gal/hr; block average assumption 400 gal/hr), avgas $7/gal bulk (below the $10.97 Alaska FBO retail average — Everts self-fuels in Fairbanks at volume; assumption), crew/maintenance/insurance build-up (assumptions stated in §4), 25–30% overhead+margin to convert cost to charter-equivalent. Rejected using DC-10 airtanker rates ($26,500/hr) as irrelevant scale; no published DC-6 charter rate found.
8. **Tariff bounding (Method C-i, upgraded 2026-07-15):** NAC's published backhaul formula (**$0.35/lb** base) gives a general-cargo floor; Everts Air Cargo's per-pound village rate table was fetched directly (evertsair.com/cargo/rates: FAI–Allakaket $0.80/lb, FAI–Arctic Village $0.83/lb, FAI–Anaktuvuk Pass $0.92/lb, ANC–Bethel $1.01–1.07/lb by weight break; fuel surcharge **26%** effective July 15, 2026) and now provides a real packaged-freight upper bracket. Later the same day, Wright Air Service's full Fairbanks-hub table and NAC's rate page were also fetched (see step 9).
9. **Second-carrier tariff cross-check (fetched 2026-07-15):** Wright Air Service (wrightairservice.com/freight-prices/, 11+ lb tier): FAI–Allakaket **$0.84/lb**, FAI–Anaktuvuk Pass **$0.92/lb**, FAI–Arctic Village **$0.85/lb**, FAI–Hughes **$0.85/lb**, FAI–Fort Yukon $0.65/lb — an independent carrier pricing the same lanes within 0–6% of Everts, which is strong evidence the per-lb tariff level is a competitive market price, not one carrier's quirk. NAC (nac.aero/rates, effective 2026-01-02): backhaul formula **$0.35/lb × fuel surcharge × 6.25% federal tax** confirmed verbatim ($30 min); headhaul ANC–Bethel $1.25 (1 lb) → **$1.19/lb (5,000 lb)**, bracketing Everts' $1.01–1.07. Alaska Air Cargo was considered and dropped — it does not carry bulk fuel (hazmat), so its tariff is not a meaningful bound.
9. **Inflation factors** (BLS CPI-U annual averages; 2025–26 assumed +2.5%/yr): 2010→2026 ×**1.51** (218.1→~330); 2025→2026 ×**1.02**. Fuel-specific escalation handled separately inside Method B via the avgas price input.
10. **Distance dependence:** derived structurally from the Method B two-part model (fixed ground/turn time vs. airborne time) and checked against the empirical spread (143-mi Coal Creek vs 252-mi AKP).
11. **Reconciled** (§7) and issued a two-part recommended edge cost plus a single-constant fallback (§8).

## 4. Method A / B / C — full derivations with arithmetic

### Method A — Revealed delivered-price premiums (DCRA, Jan 2026; commodity-neutral; verified 2026-07-15)

Premium = village price − Fairbanks same-product price (**HF baseline $4.05, gasoline baseline $3.34** — verified from the DCRA CDO ArcGIS survey layers), same survey window, then ÷ air miles:

| Community | Product | Price | Premium | Miles (FAI) | $/gal-mi (retail-inclusive) |
|---|---|---|---|---|---|
| Anaktuvuk Pass | HF (commercial) | $9.97 | $5.92 | 252 | **$0.0235** |
| Anaktuvuk Pass | Gasoline | $9.97 | $6.63 | 252 | **$0.0263** |
| Arctic Village | HF | $15.00 | $10.95 | 237 | **$0.0462** |
| Arctic Village | Gasoline | $10.00 | $6.66 | 237 | **$0.0281** |
| Hughes | HF | $13.00 | $8.95 | 205 | **$0.0437** |
| Hughes | Gasoline | $11.50 | $8.16 | 205 | **$0.0398** |
| Alatna | Gasoline | $11.50 | $8.16 | 180 | **$0.0453** |
| Alatna | HF | $8.50 | $4.45 | 180 | **$0.0247** |

(New rows added 2026-07-15: AKP gasoline, Arctic Village gasoline, Alatna HF — all from the CDO "Gas Prices, All Years" / "Heating Fuel Price, All Years" layers, Winter 2026 records. Distances as in §3: AKP 252 mi and Arctic Village 237 mi per airmilescalculator; Hughes ≈205 mi and Alatna ≈180 mi by spherical approximation, ±5%. Note the within-community spreads — Arctic Village HF $15.00 vs gasoline $10.00, Alatna HF $8.50 vs gasoline $11.50 — retail idiosyncrasy and possible mixed delivery mode/stock vintage; treat single-village points as noisy.)

These include village tank-farm and retail margin. Correcting to a transport-only figure by subtracting an assumed **$1.50/gal** local storage+distribution+margin component (ISER puts storage/distribution near $1.00/gal typical, higher in micro-markets; assumption):

- AKP: HF (5.92−1.50)/252 = **$0.0175**; gasoline (6.63−1.50)/252 = **$0.0204** — the efficient case (NSB-organized full DC-6 loads)
- Arctic Village: HF 9.45/237 = **$0.0399**; gasoline 5.16/237 = **$0.0218**
- Hughes: HF 7.45/205 = **$0.0363**; gasoline 6.66/205 = **$0.0325**
- Alatna: gasoline 6.66/180 = **$0.0370**; HF 2.95/180 = **$0.0164** (suspect barged product — treat as low outlier)

**Method A result (corrected): transport component ≈ $0.016–0.040/gal-mi (2026$), efficient full-load (AKP) ≈ $0.018–0.020, small-village ≈ $0.032–0.040.**

**Method A″ — PCE utility delivered-fuel regression (upgraded 2026-07-17; supersedes the four-community sketch).** The AEA *FY2025 PCE Statistical Report by Community* (published 2026-03-01; reporting period 07/01/24–06/30/25) prints, for every participating utility, an **"Average Price of Fuel"** ($/gal) computed as annual Fuel Cost ÷ Fuel Used (Gallons). This is the utility's *delivered purchase price*, margin-free at the retail level and inclusive of transport — exactly the quantity §9 item 4 called for. The 2026-07-15 pass pulled only four communities from the CDO layer; here the primary PDF was read page-by-page for **every plausibly air-only community** and each was mode-screened.

*Hub wholesale anchor (FY2025, empirically grounded — replaces the old $3.2–3.6 assumption).* Two **road-connected** PCE communities appear in the same report and receive trucked diesel from the Fairbanks rack over ~130–160 road miles: **Circle $3.58** (32,675 gal) and **Central $3.66** (36,391 gal). Their mean **$3.62/gal** is the closest in-dataset proxy for FY2025 Fairbanks-rack-plus-short-road diesel. Adopt **$3.60/gal** as the Interior (Fairbanks-hub) anchor, uncertainty ±$0.30; it carries a small road-haul component, so it biases the fixed intercept *slightly low* (conservative). No comparable road anchor exists for the Kotzebue hub (Kotzebue is itself a high-cost coastal barge point), so NW-Arctic points are treated as a **qualitative** cross-check only, not entered into the regression.

*Air-only community table (FY2025 PCE "Average Price of Fuel"; premium = price − hub anchor; distances great-circle from community/airport coordinates, spherical approximation ±5%, except AKP/Arctic Village which use airmilescalculator):*

| Community | Utility | FY25 $/gal | Gallons | Hub | Air mi | Premium $/gal | $/gal-mi |
|---|---|---|---|---|---|---|---|
| Anaktuvuk Pass | North Slope Borough | **$6.38** | 320,380 | FAI ($3.60) | 252 | 2.78 | **$0.0110** |
| Allakaket; Alatna | Alaska Power & Telephone | **$6.19** | 56,927 | FAI | 185 | 2.59 | **$0.0140** |
| Nikolai | City of Nikolai | **$7.65** | 37,854 | FAI | 233 | 4.05 | **$0.0174** |
| Takotna | Takotna Comm. Assoc. | $5.63 | 34,801 | FAI | 285 | 2.03 | $0.0071 ⚠ |
| Hughes | Hughes Power & Light | $4.94 | 53,418 | FAI | 202 | 1.34 | $0.0066 ⚠ |
| Ambler | AVEC | $6.17 | 88,715 | OTZ | 126 | — | — ◊ |
| Shungnak (+Kobuk intertie) | AVEC | $7.77 | 106,514 | OTZ | 138 | — | — ◊ |
| Noatak | AVEC | $9.41 | 134,327 | OTZ | 55 | — | — ◊ |

⚠ **Excluded from regression — mode-contaminated.** Takotna sits ~18 mi from barge-served McGrath and its $5.63/285 mi *falls* below shorter-haul villages (breaks the distance monotonicity) → almost certainly receives McGrath-staged barged product. Hughes ($4.94, down from FY2024 $6.41) is on the Koyukuk and its price collapsed to barge-level → partial barge in FY2025 (chapter already flagged this). ◊ **NW-Arctic (Kotzebue hub) — flagged ambiguous, cross-check only:** Ambler and Shungnak are upper-Kobuk river-barge villages from Kotzebue in normal water, flown only in low-water years; the FY2025 average blends whatever mode ran. Noatak ($9.41, 55 air mi from OTZ) is the striking datum — an *extreme* $/gal-mi at short haul, exactly the fixed-cost-dominated short-haul behavior Method B predicts, but the missing Kotzebue anchor bars a clean number.

**Excluded outright (no usable FY2025 fuel datum):** Arctic Village (Avg Price of Fuel $0.00 — "11 rpts filed, no powerhouse/usage rpts," staffing), Lime Village ($0.00, no powerhouse reports), Venetie ($0.00, "no diesel gen/usage reprt"), Kobuk ($0.00 — "Receives power from Shungnak via intertie"). **Confirmed barge/mixed and excluded:** Stony River ($4.49, Middle Kuskokwim — barge), Bettles/Evansville ($4.61, Koyukuk — barge-level price), Rampart ($6.04, Yukon River — barge), Fort Yukon ($6.88, Yukon barge hub). These barge/road points ($3.58–$4.61 for road/river vs $6.19–$7.65 for the clean air villages) sharply validate the mode screen: **flown fuel carries a $2–4/gal premium over river/road fuel at comparable Interior latitudes.**

*Two-part regression (§9 item 4), clean Interior air-only set (n=3: AKP, Allakaket, Nikolai):* OLS of premium (y, $/gal) on air-miles (x): x̄=223.3, ȳ=$3.14; Σ(dx·dy)=19.56, Σdx²=2384.7 ⇒ **slope = $0.0082/gal-mi (variable), intercept = $1.31/gal (fixed)**. Fit is weak (**R²≈0.12**, 3 noisy single-village points, Nikolai high-leverage) — the regression is *illustrative, not decisive*; the identified structure remains Method B's. Interpretation: this set is dominated by **organized utility full-load buys** (AKP alone is 320k gal/yr), so both terms land *below* Method B's small-lot-inclusive $0.0126 variable / $2.18 fixed — precisely the "utility-scale airlift is cheaper than the marginal small-lot rate" result. The per-point $/gal-mi (0.011–0.017) clusters at the **low end** of the chapter's range. Anchor sensitivity: a $3.30 (vs $3.90) hub anchor shifts every premium by +$0.30 (−$0.30), moving the intercept by ±$0.30 and the mean $/gal-mi by roughly ±$0.0014 — the ±$0.30 anchor uncertainty is the dominant error, not the fit.

**Method A″ result: FY2025 utility-scale full-load air transport ≈ $0.011–0.017/gal-mi (2026$), fixed ≈ $1.3/gal + variable ≈ $0.008/gal-mi from the (noisy) regression — confirming organized bulk airlift sits at or below the Method B full-load curve, and empirically anchoring the Fairbanks hub at $3.6/gal from the report's own road-served communities.**

### Method A′ — Revealed federal charter transaction (NPS Coal Creek, Sept 2025; verified 2026-07-15)

**$11,792.50** ÷ 1,400 gal = **$8.42/gal delivered** unleaded (exact obligated amount from USAspending; supersedes the "~$12K → $8.57" estimate). Fairbanks retail unleaded ≈ $3.45 (late 2025 assumption; Jan 2026 survey $3.34). Transport+service premium = 8.42 − 3.45 = **$4.97/gal** over 143 mi = **$0.0348/gal-mi** (×1.02 to 2026$ → **$0.0355**; band $0.034–0.037 now driven only by the Fairbanks price assumption, the award amount being exact). This is a genuine arms-length price for a **small-lot (1,400 gal) short-haul** delivery including carrier margin — it directly evidences the fixed-cost inflation at short distance/small load.

### Method B — DC-6 operating-economics build-up (2026$)

Inputs (assumptions flagged):
- Payload: 28,000 lb ⇒ **4,000 gal diesel** (7.05 lb/gal) [Everts spec; ISER's 4,900 gal applies to gasoline/short-haul]
- Block speed **230 mph** (cruise ~280, minus climb/descent/pattern) [assumption]
- Fuel burn **400 gal/hr** block avg (type data: 333 gal/hr LRC to ~450 normal cruise) × avgas **$7.00/gal** bulk = **$2,800/hr**
- Oil (R-2800s): ~$150/hr; crew (2–3): ~$450/hr; maintenance (4 geriatric radials, overhauls ~$60–80K/engine/~1,200 hr + airframe): ~$1,000–1,300/hr; insurance/ownership: ~$250/hr [assumptions]
- **Direct operating cost ≈ $4,650/hr**; +25% overhead & margin ⇒ **charter-equivalent ≈ $5,800/hr**
- Fixed per-round-trip ground/turn time (load, pump-off at ~150–200 gpm, taxi): **1.5 hr** [assumption]

Trip cost to distance D: $5,800 × (2D/230 + 1.5). Per gallon-mile = that ÷ (4,000 × D):

- Variable term: 2×5,800/(230×4,000) = **$0.0126/gal-mi**
- Fixed term: 5,800×1.5/4,000 = **$2.18/gal per delivery**, ÷ D

| D (mi) | $/gal | $/gal-mi |
|---|---|---|
| 100 | $3.44 | $0.0344 |
| 143 (Coal Creek) | $3.98 | $0.0278 |
| 200 | $4.70 | $0.0235 |
| 252 (AKP) | $5.36 | **$0.0213** |
| 400 | $7.22 | $0.0180 |

Sensitivity: avgas $6→$8/gal moves the hourly cost ∓/± ~9% (≈ ±$0.002/gal-mi at 250 mi). C-46/DC-4 variant (payload ~2,200 gal, $3,500/hr, 180 mph): variable $0.0177 + $1.91/D fixed ⇒ **$0.027/gal-mi at 200 mi** — matching the small-village Method A band.

**Method B result: $0.018–0.028/gal-mi full DC-6 loads over 150–400 mi; ~$0.027–0.035 for C-46/DC-4-class or <150-mi hauls.**

### Method C — Published tariff/benchmark bounds

**(i) General air-cargo bounds (NAC floor + Everts actuals, fetched 2026-07-15):** NAC's documented backhaul base rate **$0.35/lb**; ANC–Bethel = 399 mi. 0.35 × 7.05 lb/gal = $2.47/gal ÷ 399 = **$0.0062/gal-mi** — a floor *not achievable* for bulk fuel (specialized tanker, guaranteed empty return, hazmat); it explains why fuel-by-air must exceed ~$0.01. Everts Air Cargo's actual published general-freight rates (evertsair.com/cargo/rates, fetched 2026-07-15; **fuel surcharge 26%** effective 2026-07-15, post-Hormuz-shock; minimum charge $40): FAI–Allakaket $0.80/lb, FAI–Arctic Village $0.83/lb, FAI–Anaktuvuk Pass $0.92/lb, FAI–Fort Yukon $0.60/lb, FAI–Kaktovik $2.12/lb; ANC–Bethel $1.07 (500 lb) → $1.01/lb (>5,000 lb). Diesel-equivalents incl. surcharge (×1.26 ×7.05 lb/gal ÷ miles): FAI–ARC **$0.0311**, FAI–AKP **$0.0324**, FAI–Allakaket **$0.0395**, ANC–Bethel bulk **$0.0225/gal-mi**. Packaged general freight thus brackets **$0.022–0.040/gal-mi** — an upper-bound proxy for fuel (palletized freight carries handling costs a tanker avoids, but no empty-return guarantee), and it lands exactly on the small-lot cluster from Methods A/A′. Still labeled a **bounding proxy**, not a fuel rate.

**(ii) ISER 2010 published benchmark (quote verified 2026-07-15 against the PDF, p. 13):** "With current aviation fuel prices, the most competitive air deliveries have a transportation component of ~$1.25 per gallon per hundred air miles. The price is even higher for the many villages with airports unable to accommodate the 4,900 gallon DC-6 transport planes operated by Everts Air Cargo." (ISER/UAA, *Analysis of Rural Alaska Fuel Markets*, Feb 17, 2010.) $0.0125/gal-mi in 2009–10$; CPI-U 2010→2026: 330/218.1 = 1.51 ⇒ **$0.0189/gal-mi (2026$)**. Sits within ~10% of Method B's full-load figure — strong independent convergence.

## 5. Source table

| Source | URL | Year | Provided | Reliability |
|---|---|---|---|---|
| Alaska DCRA Fuel Price Report, Winter 2026 | https://www.commerce.alaska.gov/web/Portals/4/pub/RA/Fuel_price_report/Alaska%20Fuel%20Price%20Report%20-%20January%202026.pdf ; https://storymaps.arcgis.com/stories/64310ec78e234eb3bc8f50ed16a0f37d | Jan 2026 | AKP commercial HF $9.97 / residential $1.50 (NSB table); Arctic Village $15.00 & Hughes $13.00 (highest-HF list); Fairbanks gasoline $3.34; survey dates Jan 6–28; NSB subsidy note | **Verified 2026-07-15** (PDF fetched & read; no full community table in PDF) |
| DCRA CDO ArcGIS survey layers (Heating Fuel Price / Gas Prices / PCE, All Years) | https://maps.commerce.alaska.gov/server/rest/services/Services/CDO_Utilities/MapServer (layers 6, 7, 4) | Jan 2026 | Fairbanks HF **$4.05**; Alatna HF $8.50; Arctic Village gas $10.00; AKP gas $9.97; Hughes $13.00/$11.50; PCE utility fuel prices FY2023–25 | **Verified 2026-07-15** (queried REST API directly) |
| AEA, *FY2025 PCE Statistical Report by Community* (Final) | local: `cost_derivation_resources/2026.03.01 FY2025 PCE Statistical Report by Community (Final).pdf` (183 pp); akenergyauthority.org/pce | Mar 2026 (FY2025) | Per-utility "Average Price of Fuel" $/gal + gallons: AKP $6.38/320,380; Allakaket/Alatna $6.19; Nikolai $7.65; Takotna $5.63⚠; Hughes $4.94⚠; Ambler $6.17; Shungnak $7.77; Noatak $9.41; road anchors Circle $3.58, Central $3.66; barge Stony River $4.49, Bettles $4.61, Rampart $6.04, Fort Yukon $6.88 | **Verified 2026-07-17** (primary PDF read page-by-page) |
| ISER/UAA, *Analysis of Rural Alaska Fuel Markets* (Components of Fuel Costs series) | https://iseralaska.org/static/legacy_publication_links/componentsoffuel3.pdf ; local copy `components of alaska fuel costs.pdf` | Feb 17, 2010 | "~$1.25 per gallon per hundred air miles"; 4,900-gal DC-6 (Everts Air Cargo); <5,000-gal lots, few hundred mi of Kenai/Fairbanks; storage/distribution components | **Verified 2026-07-15** (p. 13, exact quote) |
| USAspending, Everts Air Fuel NPS contract | https://www.usaspending.gov/award/CONT_AWD_140P9725F0047_1443_140P9725A0010_1443 (data via api.usaspending.gov) | Sept 2025 | **$11,792.50** / 1,400 gal unleaded to Coal Creek Camp airstrip; DOI/NPS; PoP start 2025-09-18 | **Verified 2026-07-15** (exact amount) |
| Everts Air — bulk fuel page & fleet | https://evertsair.com/fuel | 2026 | Charter-only pricing; 2,000–5,000 gal tanks; DC-6 payload 28,000 lb | High |
| AOPA "Legendary Aircraft" | https://www.aopa.org/news-and-media/all-news/2005/november/pilot/legendary-aircraft-extraordinary-service | 2005 | DC-6 5,000–6,000 gal (distance-dependent); North Slope ops | Med |
| alaska.org "Pipeline in the Sky" | https://www.alaska.org/detail/pipeline-in-the-sky | n.d. | Everts primacy, hubs (FAI/Kenai), FAA-certified tanks | Med |
| Alaska Air Fuel / C-54 crash article | https://en.wikipedia.org/wiki/2024_Alaska_Air_Fuel_Douglas_C-54_crash ; https://www.alaskaairfuel.com/ | 2024–26 | Second carrier, DC-4s, FAI→Kobuk run | High |
| AirNav fuel price report | https://www.airnav.com/fuel/report.html | Jul 2026 | 100LL national $7.44, Alaska region $10.97 | High (retail FBO, not bulk) |
| DC-6 type/fuel-burn data | http://www.prop-liners.com/dc6btech.htm ; PMDG forum | — | 2,000 lb/hr LRC burn | Med |
| Air Miles Calculator | https://www.airmilescalculator.com/distance/fai-to-akp/ ; /fai-to-arc/ | 2026 | 252 mi, 237 mi | High |
| Coal Creek strip location | https://sites.google.com/site/bushplaneparksalaska/home/alaska-fly-in-parks/yukon---charley-rivers | — | 124 NM (143 mi) E of FAI | Med |
| NAC rates | https://www.nac.aero/rates/ | eff. 2026-01-02 | $0.35/lb backhaul formula (verified verbatim); headhaul ANC–Bethel $1.19–1.25/lb | High (fetched 2026-07-15) |
| Wright Air Service freight prices | https://wrightairservice.com/freight-prices/ | 2026 | FAI-hub per-lb table: Allakaket $0.84, AKP $0.92, Arctic Village $0.85, Hughes $0.85 — matches Everts within 0–6% | High (fetched 2026-07-15) |
| Everts Air Cargo rates | https://evertsair.com/cargo/rates | Jul 2026 | FAI–village per-lb rates (Allakaket $0.80, Arctic Village $0.83, AKP $0.92, Fort Yukon $0.60, Kaktovik $2.12); ANC–Bethel $1.01–1.07; fuel surcharge 26% (eff. 2026-07-15); $40 minimum | **Verified 2026-07-15** |
| KYUK/ADN/Beacon 2026 fuel-crisis series | https://www.kyuk.org/economy/2026-04-20/... ; https://alaskabeacon.com/2026/06/03/... | 2026 | Shock context; air = backstop at higher price; 1,200 gal/person/yr | High (context) |
| KNBA — AKP fuel shortage | https://www.knba.org/news/2026-01-15/a-weeklong-fuel-shortage-in-anaktuvuk-pass-caused-school-closures-and-left-homes-without-heat | Jan 2026 | 18,500 gal diesel flown in a week; Everts diesel-capable fleet expansion | High |
| akbizmag "No Port No Problem" | https://www.akbizmag.com/industry/transportation/no-port-no-problem/ | 2021 | McGrath still barge-served (excluded from air-only set) | Med |

## 6. Distance-dependence analysis

**Cost per gallon-mile is NOT constant — it falls hyperbolically with distance.** Structurally (Method B): per-gal-mi = **$0.0126 + ($2.18/D)** for DC-6 loads. The fixed component (loading, pump-off, taxi, dispatch — ~1.5 hr of a ~$5,800/hr asset spread over 4,000 gal) contributes $2.18/gal *per delivery* regardless of distance. Consequences: per-gal-mi at 100 mi ($0.034) is ~1.9× the 400-mi value ($0.018); halving load size (C-46) raises the whole curve ~35–50%. The empirical points agree: Coal Creek (143 mi, 1,400-gal lot) ≈ $0.035 vs AKP (252 mi, full loads) ≈ $0.018–0.026 (verified values). **For the routing model, a two-part edge cost (fixed per-delivery $ + true per-mile $) is strictly better than any single $/gal-mi constant.** Beyond ~400–500 mi, aircraft fuel uplift begins to displace payload, so the curve flattens then rises slightly; irrelevant at typical hub–village stage lengths (100–300 mi).

## 7. Cross-method comparison and reconciliation

| Method | Basis | $/gal-mi (2026$) | Includes |
|---|---|---|---|
| A (DCRA premiums, corrected −$1.50/gal local) | market prices (verified) | 0.016–0.040 (AKP 0.018–0.020) | charter + residual local costs |
| A″ (PCE utility fuel, FY2025 report) | utility purchase prices, mode-screened; hub anchored to road-served PCE communities ($3.60) | ≈0.011–0.017 (clean full-load buys); regression $1.31 fixed + $0.0082/gal-mi (R²≈0.12) | charter, utility-scale |
| A′ (NPS Coal Creek, $11,792.50) | actual contract (verified) | 0.034–0.037 @143 mi, 1,400 gal | charter + margin, small lot |
| B (DC-6 build-up) | engineering | 0.018–0.028 (full loads, 150–400 mi) | charter-equivalent |
| C-i (NAC floor; Everts general-freight actuals) | tariffs (Everts verified) | floor 0.006–0.012; packaged-freight bracket 0.022–0.040 | general cargo bounds (not fuel rates) |
| C-ii (ISER ×1.51) | published study (verified) | 0.019 ("most competitive") | charter, full DC-6 |

Convergence is good once load size and distance are controlled: **full-tanker-load charter cost clusters at $0.018–0.022/gal-mi** (B, C-ii, A-efficient AKP; the FY2025 PCE regression puts organized bulk buys slightly *below* this, ~$0.011–0.017, with the road-served-community hub anchor now empirical rather than assumed); **small-lot/small-aircraft reality clusters at $0.031–0.040** (A′, A small villages, Everts packaged-freight equivalents); the general-cargo floor confirms air fuel can't go below ~$0.012. Retail-inclusive delivered premiums run $0.024–0.046. No method is contaminated by the June 2026 commodity shock (Jan 2026 premiums are same-date differentials; Method B's avgas input is a stated sensitivity; the one post-shock input, Everts' 26% fuel surcharge, is flagged and only affects the bounding proxy).

## 8. Final estimate: point, range, confidence, includes/excludes

- **Point estimate: $0.025 per gallon-mile (2026$)** — carrier charter transport cost of bulk fuel by air, hub→village, averaged over the realistic mix of DC-6 full loads and C-46/DC-4 partial loads at typical 150–300 mi stage lengths.
- **Preferred model form:** edge cost = **$0.0126/gal-mi + $2.20/gal fixed per air delivery** (DC-6 class); multiply both terms by ~1.4 for communities whose strips only take C-46/DC-4-class aircraft.
- **Range: $0.015–0.042/gal-mi** ($0.015–0.022 efficient full-load long-haul, with PCE utility data supporting the low end; $0.031–0.040 small-lot/short-haul/small-aircraft). **Delivered-price premium including village storage, handling and margins: $0.024–0.046/gal-mi.**
- **The point estimate did not move** ($0.025 before and after both passes). The 2026-07-15 verification adjustments were symmetric; the 2026-07-17 PCE regression added information at the **low end only** (utility full-load buys at $0.011–0.017), which the blended point estimate already reflected by averaging efficient full loads against small-lot/small-aircraft realities ($0.031–0.040). No basis to move $0.025; if anything the new data *firm up* the full-load floor. The one substantive upgrade is qualitative: the Fairbanks hub anchor is now empirical ($3.60 from road-served PCE communities), not assumed.
- **Confidence: medium-high** (held; the FY2025 PCE regression corroborates rather than overturns). The formerly snippet-only load-bearing values are now verified: Fairbanks baselines ($3.34 gas / $4.05 HF), all village prices, the NPS award ($11,792.50 exact), the ISER quote, and Everts' rate table. Remaining softness: Method B's hourly cost is a build-up, not a quoted rate; Hughes/Alatna mode ambiguity; ±5% spherical distances for Hughes/Alatna.
- **Includes:** round-trip aircraft operation (empty return), crew, loading/pump-off, carrier overhead and margin. **Excludes:** fuel commodity price, hub terminal storage, village tank-farm and retail margin (except in the "delivered premium" variant above), weather-delay/emergency surcharges.
- Air is roughly **10–20× barge linehaul** on a per-gallon-mile basis (ISER barge ≈ $0.19/gal over long linehauls).

## 9. What would most improve this estimate

*(Updated 2026-07-15 — the original item 1 fetch list is done except where noted; see Verification addendum.)*

1. ~~Remaining unfetched tariffs~~ **Done (2026-07-15 second pass):** Wright Air and NAC rate pages fetched; both corroborate the Everts-based bracket (see log steps 8–9). Alaska Air Cargo dropped — it does not carry bulk fuel (hazmat), so its tariff is not a meaningful bound. Still open: the Everts recipient profile on USAspending (all awards) could yield more $/gal/distance points beyond Coal Creek.
2. A direct **charter quote from Everts Air Fuel / Alaska Air Fuel** (e.g., FAI→AKP, 4,000 gal diesel) would replace Method B's hourly build-up with a market rate.
3. North Slope Borough budget documents for the AKP annual airlift (gallons and contract $) would give the single best full-load revealed rate (PCE shows NSB's AKP utility fuel at $6.33–6.38/gal FY2024–25 on ~320k gal/yr — a contract figure would decompose this).
4. ~~Regressing PCE delivered fuel cost on air distance across all flown-fuel communities... A contemporaneous Fairbanks rack/wholesale diesel series is needed to anchor the premiums.~~ **Done (2026-07-17 second pass, local documents):** the *FY2025 PCE Statistical Report by Community* (AEA, 2026-03-01) was read community-by-community; every plausibly air-only village was extracted and mode-screened; the hub anchor is now **empirical** ($3.60/gal, from road-served PCE communities Circle $3.58 / Central $3.66 in the same report — the old $3.2–3.6 assumption is retired). The two-part regression ran (n=3 clean Interior air-only: fixed $1.31/gal + variable $0.0082/gal-mi, R²≈0.12 — noisy but confirming utility-scale full loads sit *below* the Method B curve). **Still open:** the clean set is small because most small air-only villages either don't report fuel (Arctic Village, Lime, Venetie — $0.00) or show barge contamination (Takotna, Hughes); a Kotzebue-hub diesel anchor would unlock the NW-Arctic points (Ambler/Shungnak/Noatak); and verified great-circle distances (vs the ±5% spherical ones used here) would tighten the slope.
5. Verified great-circle distances for Hughes and Alatna (currently spherical approximations, ±5%).

## Verification addendum (2026-07-15)

WebFetch became available; all §9-item-1 primary sources except Wright Air/NAC/Alaska Air Cargo were fetched and the numbers propagated.

**Fetched:** (1) DCRA Winter 2026 PDF (18 pp — narrative + NSB table only; no full community price table); (2) the DCRA Community Database Online ArcGIS REST layers behind the report (CDO_Utilities MapServer layers 6 "Gas Prices, All Years", 7 "Heating Fuel Price, All Years", 4 "PCE Program"), queried directly for Winter 2026 / FY2023–25; (3) USAspending API for award CONT_AWD_140P9725F0047_1443_140P9725A0010_1443; (4) evertsair.com/cargo/rates; (5) local ISER PDF p. 13 (*Analysis of Rural Alaska Fuel Markets*, Feb 17, 2010).

**Confirmed:** AKP commercial HF $9.97 / residential $1.50 (NSB-subsidized; subsidy "not extended to commercial businesses"); Arctic Village HF $15.00; Hughes HF $13.00 / gas $11.50; Alatna gas $11.50; Fairbanks gasoline $3.34; survey window Jan 6–28, 2026; NPS award = Everts Air Fuel, 1,400 gal unleaded, Coal Creek Camp airstrip, PoP start 2025-09-18; ISER "~$1.25 per gallon per hundred air miles" and 4,900-gal DC-6 (attributed to Everts Air Cargo), quoted exactly.

**Corrected:** Fairbanks *heating fuel* baseline $3.34 → **$4.05** (the $3.34-for-both assumption was wrong, as suspected) — all HF premiums re-derived (AKP 0.0263→0.0235, Arctic Village 0.0492→0.0462, Hughes 0.0471→0.0437 retail-inclusive); NPS award $12,000 → **$11,792.50** ($8.57→$8.42/gal; A′ 0.0366→0.0355); ISER source title corrected.

**Added:** three Method A rows (AKP gasoline $9.97 → 0.0263; Arctic Village gasoline $10.00 → 0.0281; Alatna HF $8.50 → 0.0247 retail-inclusive); Method A″ PCE utility fuel prices (AKP $6.33–6.38, Alatna/Allakaket $6.19–7.38, Hughes $4.94–6.41, FY2024–25); real Everts general-freight bracket for Method C-i (FAI–ARC/AKP/Allakaket $0.80–0.92/lb + 26% surcharge ⇒ $0.031–0.040/gal-mi packaged-freight equivalents; ANC–Bethel bulk $0.0225). Communities checked and absent from the Winter 2026 survey: Lime Village, Takotna, Stony River, Chalkyitsik, Venetie, Birch Creek, Allakaket, Fort Yukon, Beaver, Rampart, Koyukuk, Nikolai, Bettles.

**Net effect:** final point estimate **unchanged at $0.025/gal-mi (2026$)**; range tightened to $0.015–0.042; confidence raised medium → medium-high. One fetch failure: maps.commerce.alaska.gov rejects the `/arcgis/rest/` path (WAF) — the `/server/rest/` path works.

### Second pass — local documents (2026-07-17)

Read the primary source **`cost_derivation_resources/2026.03.01 FY2025 PCE Statistical Report by Community (Final).pdf`** (AEA, 183 pp) page-by-page to execute §9 item 4 (Method A″ upgraded from a four-community sketch to a mode-screened regression).

**Fetched/read:** per-community pages for every plausibly air-only village plus road/river/barge controls — Anaktuvuk Pass (p.21), Allakaket;Alatna (19), Arctic Village (25), Ambler (20), Kobuk (89), Shungnak (151), Noatak (120), Lime Village (100), Nikolai (118), Takotna (161), Venetie (178), Stony River (160), Bettles;Evansville (29), Rampart (140), Hughes (75), plus road/hub controls Central (32), Circle (43), Fort Yukon (62). Field used: **"Average Price of Fuel" = Fuel Cost ÷ Fuel Used (Gallons)** — the utility's delivered, margin-free purchase price.

**Confirmed / new data:** FY2025 utility fuel $/gal — AKP **$6.38** (320,380 gal, NSB), Allakaket/Alatna **$6.19** (56,927), Nikolai **$7.65** (37,854), Ambler $6.17 (88,715), Shungnak $7.77 (106,514, feeds Kobuk via intertie), Noatak $9.41 (134,327); road-served controls Circle $3.58, Central $3.66; barge/river controls Stony River $4.49, Bettles/Evansville $4.61, Rampart $6.04, Fort Yukon $6.88.

**Corrected / retired:** the Method A″ Fairbanks-wholesale anchor **$3.2–3.6 (assumed) → $3.60 (empirical)**, taken from the report's own road-served PCE communities (Circle/Central mean $3.62). The FY2024/FY2025 CDO figures from the 2026-07-15 pass are consistent with the FY2025 report values.

**Mode-screen results (new):** *air-only, clean* = AKP, Allakaket/Alatna, Nikolai. *Excluded — no fuel datum* = Arctic Village, Lime Village, Venetie, Kobuk (all $0.00 / intertie / non-reporting). *Excluded — barge/mixed contamination* = Takotna ($5.63, McGrath-adjacent, breaks distance monotonicity), Hughes ($4.94, down from $6.41 → partial barge on the Koyukuk), Stony River/Bettles/Rampart/Fort Yukon (river/barge). *Flagged ambiguous, cross-check only* = Ambler/Shungnak/Noatak (Kotzebue hub, no clean diesel anchor; Noatak's $9.41 at 55 air-mi is a textbook short-haul fixed-cost spike).

**Regression (§9 item 4):** premium = price − $3.60, on great-circle air-miles (spherical approximation ±5%; AKP 252 & Arctic Village 237 from airmilescalculator). n=3 clean Interior air-only ⇒ **fixed $1.31/gal + variable $0.0082/gal-mi, R²≈0.12** — noisy (3 single-village points) but directionally clear: utility-scale full loads sit *below* Method B's $2.18 fixed + $0.0126 variable, consistent with organized bulk airlift being the efficient end of the range. Per-point $/gal-mi 0.011–0.017. Dominant uncertainty is the ±$0.30 hub anchor, not the fit.

**Net effect (second pass):** final point estimate **unchanged at $0.025/gal-mi (2026$)**; the new evidence lands entirely in the already-modeled full-load low end ($0.011–0.017) and does not shift the blended point. Substantive gains are (a) an *empirical* Fairbanks hub anchor replacing an assumption, and (b) a mode-screened, distance-resolved confirmation that flown fuel carries a $2–4/gal premium over river/road fuel at comparable Interior latitudes. Confidence held at medium-high. Limitation: clean air-only sample is small (n=3) because most tiny air villages don't report fuel or are barge-contaminated; a Kotzebue-hub anchor and verified distances remain the highest-value next steps.
