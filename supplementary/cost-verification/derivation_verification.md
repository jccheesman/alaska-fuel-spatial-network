# Fuel Cost Derivation Verification

**Verifies:** `Fuel Cost Resources.pdf` (Gemini deep-research derivations) against primary sources, and against the values consumed by the model in `friction_surface/friction_costs.py` (`BASELINE_RATES_PER_GALLON_MILE`).
**Date:** 2026-07-14
**Method:** independent arithmetic recomputation of every formula in the PDF; page-by-page extraction of the ISER report (`components of alaska fuel costs.pdf`, 77 pp.); web verification of carrier tariffs, news coverage, and route distances.

---

## 1. Executive summary

| Mode | PDF / model value ($/gal-mi) | Arithmetic | Source support | Recommended value ($/gal-mi) |
|---|---|---|---|---|
| Road | 0.000528 | ✓ correct | **Strong** — all three inputs confirmed | **Keep 0.000528** (range 0.000389–0.000667) |
| Barge | 0.000556 | ✓ correct | **Weak as stated** — $1.00/gal is in **2010 dollars**; 1,800-mi distance is uncited | **Raise to ≈ 0.00087** (range 0.00081–0.00094) after inflation adjustment |
| Plane | 0.0248–0.0413; model uses midpoint 0.033 | ✓ correct | **Moderate** — surcharge and one distance are stale | **Lower slightly to ≈ 0.031** (range 0.023–0.038) |
| Ice road | 0.00667 (from $10–$30/veh-mi ÷ 3,000 gal) | ✓ correct | **Unsupported** — no published source exists for either input | **Keep 0.00667 as an engineering estimate**, flag provenance, add sensitivity bounds |

Every formula in the PDF computes correctly. The issues are all in the **inputs**: one dollar-year problem (barge), two stale/incorrect inputs (plane surcharge, one air distance), and one derivation that exists in the code but not in the PDF at all (ice road).

> **Part II (§9, added 2026-07-14) supersedes the recommendations above.** Four blind research agents independently re-derived each mode's rate from scratch (≥2 methods each, never shown the current values). The final recommended table is in §9.6.

---

## 2. Road — VERIFIED, strongest derivation

**Derivation:** $4.75 per vehicle-mile ÷ 9,000-gal tanker = **$0.000528/gal-mi**. Arithmetic: 4.75 / 9,000 = 0.0005278 ✓.

Every input checks out:

- **$3.50–$6.00/mi Alaska heavy-transport range** — confirmed verbatim at heavyequipmenttransport.com/trucking/alaska.php. Note that **$4.75 is exactly the midpoint** of this range, which makes the point estimate principled rather than arbitrary.
- **ATRI $2.260/mi national average ($1.779 non-fuel)** — confirmed; cite it precisely as ATRI, *An Analysis of the Operational Costs of Trucking*, **2025 edition (2024 data)**. This is a national floor, useful context only — Alaska rates sit well above it.
- **9,000-gal tanker capacity** — confirmed as typical for single-compartment petroleum trailers (industry range 9,000–9,800 gal; multi-compartment up to ~14,000 but never filled to max).

**Implied range:** $3.50/9,000 = $0.000389 to $6.00/9,000 = $0.000667 per gal-mi.

**Discrepancy with the code:** `VEHICLE_MILE_RATES_REFERENCE["Road"]["low"] = 2.37` (→ $0.000263/gal-mi in the comment) does not come from this PDF, which gives $3.50 as the low. $2.37 looks like a national ATRI-adjacent figure from the earlier dossier. Recommend updating the reference low to 3.50 (or documenting 2.37's actual source) so the range traces to a citable page.

**Caveats to record, not fix:**
- The $3.50–$6.00 range is for heavy/flatbed transport generally, not fuel tankers specifically; hazmat tanker rates may carry a premium.
- Carrier $/mile quotes are normally loaded-mile rates that already price in repositioning; if the routing model ever charges both directions of a round trip, this rate would double-count.

---

## 3. Barge — arithmetic correct, but the inputs need two fixes

**Derivation:** $1.00/gal Cook Inlet → Bethel ÷ 1,800 mi = **$0.000556/gal-mi**. Arithmetic: 1.00 / 1,800 = 0.000556 ✓.

### 3a. The $1.00/gal is real — but it is a 2010 number

The source is ISER, *Components of Alaska Fuel Costs* (Szymoniak, Fay, et al., prepared for the Alaska Senate Finance Committee, **February 17, 2010**) — the 77-page PDF in this folder. The figure is genuinely there (p. 7):

> "The estimated average cost of delivering fuel from Cook Inlet to Western Alaska communities is approximately $1.00 per gallon."

and it decomposes cleanly (Table 4, p. 22, totaling $0.98/gal):

| Component | $/gal (2010) |
|---|---|
| Purchase differential | 0.06 |
| **Linehaul (Cook Inlet → hub)** | **0.19** |
| Terminal use | 0.03 |
| **Small-barge (lightering/river) operations** | **0.60** |
| Working capital (distributor) | 0.03 |
| Administration | 0.07 |

All dollar figures in that report are nominal ~2009–2010 dollars. **CPI-adjusted to 2026 (×≈1.45–1.50), the $1.00 becomes ≈ $1.45–$1.50/gal**, and the gallon-mile rate becomes ≈ $0.00081–0.00083 at 1,800 mi.

### 3b. The 1,800-mile distance is not in the cited source

The ISER 2010 report contains **no Cook Inlet–Bethel transit distance anywhere** (the figure likely traces to ISER's 2008 companion, *Components of Delivered Fuel Prices in Alaska*). No published tug-barge mileage for the route was found; a leg-by-leg reconstruction (down Cook Inlet, along the Alaska Peninsula, through Unimak/False Pass, across Bristol Bay to Kuskokwim Bay, plus ~65 river miles to Bethel) gives roughly **1,500–1,700 statute miles**. 1,800 statute miles is the right order but probably ~10% long. NOAA's *Distances Between United States Ports* table would settle it (couldn't be fetched this session).

### 3c. Recommended value

Worked point estimate: **$1.48/gal (2026$) ÷ 1,700 mi ≈ $0.00087/gal-mi**, with a defensible range of $1.45/1,800 = **0.00081** to $1.50/1,600 = **0.00094**. This is a ~55% increase over the current 0.000556, driven almost entirely by the inflation adjustment.

### 3d. Structural note (future refinement, not a bug)

The $1.00 is an **all-in distribution cost**, but 60% of it is small-barge lightering — a per-transfer cost, not a per-mile one. Dividing the whole bundle by linehaul distance smears a fixed handoff cost across 1,800 miles, which overprices long linehauls and underprices short ones. Since `friction_costs.py` already has an `INTERMODAL_TRANSFER_FEES` mechanism, the cleaner long-term decomposition is:

- **Linehaul-only rate:** $0.19/gal (2010) ≈ $0.28/gal (2026) ÷ ~1,700 mi ≈ **$0.00017/gal-mi** for ocean linehaul edges;
- **Lightering as a transfer fee:** ISER's small-barge range $0.40–$0.80/gal (2010) ≈ **$0.60–$1.20/gal (2026)** charged at the linehaul→river-barge handoff — an entry the fee table currently lacks (`("barge_linehaul", "barge_river")` or similar).

Keep the blended rate for now (the network doesn't yet distinguish linehaul from river-barge legs); adopt the decomposition when/if it does.

### 3e. Two misattributions in the PDF worth correcting

- **"Working capital costs – $0.10 per gallon":** the $0.10 in ISER 2010 (p. 24) is the *community tank-farm owner's* (retail-side) working capital. The *delivery-side* working capital is $0.026–$0.03/gal (p. 21, Table 4). Attributing $0.10 to delivery double-counts.
- **"River barges draw no more than 3.5 feet":** not in the ISER 2010 report. What it actually says (pp. 17–18): Bethel's controlling depth is 12 ft, and loaded linehaul barges drawing 18–20 ft must lighter off one-third of cargo. The 3.5-ft claim needs re-sourcing if kept.
- Barge capacity 2.5–3.5M gal **is** confirmed (p. 15; "typical linehaul barge carries three million gallons," p. 17) — the code's 3,000,000 reference value is fine.

---

## 4. Plane — arithmetic correct; two inputs need updating

**Derivation:** C_gal = rate/lb × (1 + surcharge) × 7.1 lb/gal, then ÷ route miles. All three computations check:

| Route | PDF math | Check |
|---|---|---|
| ANC→Bethel | 1.01 × 1.38 × 7.1 = $9.90/gal ÷ 400 mi = 0.0248 | ✓ |
| FAI→Allakaket | 0.80 × 1.38 × 7.1 = $7.84/gal ÷ 190 mi = 0.0413 | ✓ |
| FAI→Arctic Village | 0.83 × 1.38 × 7.1 = $8.13/gal ÷ 290 mi = 0.0280 | ✓ |

### 4a. Corrections to inputs

- **Fuel surcharge is now 28% (Everts, effective June 25, 2026), not 38%.** The 38%/April 2026 figure is superseded (and couldn't be confirmed historically). The `friction_costs.py` comment "38% active Apr 2026" is stale.
- **FAI–Arctic Village is ≈ 237 statute miles, not 290.** The 290 figure circulates in community descriptions but is not the air distance (great-circle 237.1 mi). ANC–Bethel at 400 mi ✓ (398.8 GC); FAI–Allakaket at 190 mi ✓ (published figure; GC ≈ 181).
- The per-lb base rates ($1.01, $0.80, $0.83) could not be independently confirmed this session (the Everts rates page blocked automated fetching) but were not contradicted. **Spot-check them manually at evertsair.com/cargo/rates.**
- **Density:** 7.1 lb/gal is correct for #2 diesel/heating oil; **#1 is ≈ 6.8 lb/gal** (~4% lighter). Fine to keep 7.1 for a #2-dominated mix; note it slightly overstates #1 costs.

### 4b. Recomputed with corrections (28% surcharge, 237 mi)

| Route | $/gal | $/gal-mi |
|---|---|---|
| ANC→Bethel (399 mi) | 1.01 × 1.28 × 7.1 = 9.18 | **0.0230** |
| FAI→Allakaket (190 mi) | 0.80 × 1.28 × 7.1 = 7.27 | **0.0383** |
| FAI→Arctic Village (237 mi) | 0.83 × 1.28 × 7.1 = 7.54 | **0.0318** |

Corrected range **0.0230–0.0383**; midpoint **0.0306**; mean of the three routes **0.0310**. Recommended `Plane` rate: **0.031** (vs. current 0.033 — a 6% trim, same method).

### 4c. Independent cross-check and structural caveats

- ISER 2010 (p. 13): the most competitive bulk air deliveries ran "~$1.25 per gallon per hundred air miles" = $0.0125/gal-mi in 2010$ ≈ **$0.018/gal-mi in 2026$**. This anchors the *bulk-tanker charter* cost below the per-lb cargo-tariff proxy — so 0.031 is a **conservative (high-side) estimate**, appropriate if you'd rather overstate than understate air costs. A defensible full range is 0.018–0.038.
- **Bulk fuel doesn't actually fly on the cargo tariff.** Everts Air Fuel (a separate certificate from Everts Air Cargo) hauls village fuel in C-46/DC-6 tankers (~2,000–6,000 gal depending on distance) priced by **charter quote only** — no public per-gallon rate exists. The per-lb derivation is a reasonable proxy, but the code comment's "3,500-gal DC-6" capacity is inside the published envelope rather than a cited figure.
- **A flat $/gal-mi is a simplification of a distance-nonlinear tariff.** The three data points show the rate falling with distance (0.038 at 190 mi → 0.023 at 400 mi) because O-D tariffs embed fixed takeoff/landing/handling costs. The flat 0.031 rate therefore underprices short hops and overprices long hauls. If plane edges in the network span a wide distance range, a two-parameter form (fixed $/gal + $/gal-mi) would fit the tariff structure better; with the current single-rate design this is a documented limitation, and `PLANE_HANDLING_COST_PER_GALLON_USD` already absorbs part of the fixed component.

---

## 5. Ice road — arithmetic correct, but the derivation is not in the PDF and its inputs are unsourced

**What the code uses:** midpoint of $10–$30/vehicle-mile ÷ 3,000-gal truck = 20/3,000 = **$0.00667/gal-mi** ✓ (arithmetic fine).

**What the verification found:**

- **No published source exists for either input.** The $10–$30/veh-mi range and the 3,000-gal ice-road truck capacity could not be located in any carrier tariff, agency document, or news source. The ISER 2010 report contains *no ice-road cost content at all*. The `Fuel Cost Resources.pdf` ice-road section offers only anecdotes (Tuntutuliak; Noatak's $425K snow-track tractor) and never derives a gallon-mile rate. This is the model's weakest number.
- **The Tuntutuliak anecdote is confirmed and is richer than the PDF states** (KYUK, March 2 &amp; 24, 2026): Typhoon Halong disaster-relief context; the Kuskokwim Ice Road was plowed ~40 mi beyond its normal endpoint to reach the village for the first time since 2020; sole supplier Top Fuel quoted **$13.60/gal delivered**; ~8,380 gal (≈$114,000, internally consistent); delivered March 11, 2026; financed by an emergency bulk fuel loan.
- **What Tuntutuliak implies:** $13.60 is an all-in delivered price (commodity + haul + emergency/monopoly premium), not a transport rate. Netting out a plausible ~$7/gal Bethel commodity+margin leaves ~$6.6/gal of transport premium over a ~50-mi haul ≈ **$0.13/gal-mi — roughly 20× the model's baseline**. Treat this as a *distressed-conditions upper bound* (small lot, sole supplier, one-off road extension), not a baseline.
- **Plausibility of the baseline anyway (cost build-up):** ice-road hauling at ~10–15 mph with premium drivers, escort/support, and specialized equipment at an effective $200–$400/hr works out to $15–$40/veh-mi — so the unsourced $10–$30 range is *credible as an engineering estimate*, just not citable. Smaller-than-highway fuel trucks on the Kuskokwim ice road are confirmed practice (full tankers need 30" of ice; thin-ice years force "a fleet of smaller fuel trucks" — KYUK), but no gallonage is published.
- **Sanity check against alternatives:** at 0.00667 the ice road is ~13× road cost and ~4–5× cheaper than plane (0.031) — directionally consistent with why communities extend ice roads instead of flying fuel. A rate much above ~0.03 would make ice roads pointless vs. air, which argues the true steady-state rate is well below the Tuntutuliak figure.

**Recommendation:** keep **0.00667** as the baseline but (a) re-label its provenance in `friction_costs.py` as an *engineering estimate* (cost build-up + plausibility bounds), not a dossier citation; (b) record bounds — plausible steady-state 0.003–0.013, confirmed emergency upper ~0.13; (c) run any ice-road-sensitive results (Atqasuk, Nuiqsut routing) with a ±2× sensitivity band; (d) pursue a real quote (Top Fuel in Bethel, North Slope Borough fuel division, or Crowley) to retire the estimate.

**Noatak $425K snow-track tractor:** the OMB capital-project PDF couldn't be fetched (the cited `13_budget` URL is probably wrong — sibling projects in that number range live under `https://omb.alaska.gov/ombfiles/14_budget/CapBackup/`, so try `.../14_budget/CapBackup/proj58673.pdf` manually). The surrounding fact pattern is corroborated (ADN, May 2022: Noatak fuel at $16/gal, supplied entirely by air, with the overland-to-Kotzebue winter route as the discussed alternative).

---

## 6. Transfers

The PDF only sketches transfer *types* (barge→hub, linehaul→small barge, plane→tanks/trucks) with no numbers, so the code's `INTERMODAL_TRANSFER_FEES` (Crowley Bethel tariff, Bristol Bay tarmac fees) stands on its own sources — nothing here contradicts it. One addition surfaced by this verification:

- **Linehaul→river-barge lightering** is the single largest cost in the ISER decomposition ($0.60/gal of the $1.00 in 2010; range $0.40–$0.80) and has no entry in the fee table. It's currently implicit in the blended barge rate (§3d) — fine for now, but if the network ever splits ocean and river barge legs, this becomes a required fee entry of roughly **$0.60–$1.20/gal (2026$)**.

---

## 7. Proposed changes to `friction_costs.py` (not applied)

```python
BASELINE_RATES_PER_GALLON_MILE = {
    "Road":     0.000528,   # unchanged — fully verified
    "Barge":    0.00087,    # was 0.000556: ISER $1.00/gal is 2010$; ×1.48 CPI, ÷1,700 mi
    "Plane":    0.031,      # was 0.033: 28% surcharge (Jun 2026) + FAI–Arctic Village 237 mi (not 290)
    "IceRoad":  0.00667,    # unchanged, but provenance is an engineering estimate (see doc §5)
}
```

Comment/reference fixes regardless of whether the rates change:
- Road reference low: `2.37` → `3.50` (or cite where 2.37 came from); comment range becomes 0.000389–0.000667.
- Plane comment: "38% active Apr 2026" → "28% effective Jun 2026"; recompute noted endpoints.
- Barge comment: note $1.00/gal is nominal 2010$ (ISER Feb 2010, p. 7 / Table 4 p. 22) and that 1,800 mi is uncited (reconstruction: ~1,500–1,700 statute mi).
- IceRoad comment: mark $10–$30/veh-mi and 3,000 gal as unsourced engineering estimates; add Tuntutuliak 2026 ($0.13/gal-mi emergency, all-in) as the confirmed upper bound.

## 8. Open items

1. Manually confirm the three Everts per-lb base rates at evertsair.com/cargo/rates (automated fetch was blocked).
2. Try `https://omb.alaska.gov/ombfiles/14_budget/CapBackup/proj58673.pdf` for the Noatak tractor snapshot.
3. Pull NOAA *Distances Between United States Ports* for an authoritative Cook Inlet→Kuskokwim Bay mileage.
4. Locate ISER 2008, *Components of Delivered Fuel Prices in Alaska* (Wilson et al.) — the probable true source for the 1,800-mile figure and possibly the 3.5-ft draft claim.
5. Get a real ice-road haul quote (Top Fuel, NSB, or Crowley) to replace the $10–$30/veh-mi estimate.

---

# Part II — Independent blind re-derivation (2026-07-14)

To test the PDF-derived rates rather than just audit them, four research agents each re-derived one mode's $/gal-mi from scratch. Each agent was **blind to the current model values and to the PDF's derivations** (so results can't anchor), and was required to use at least two independent methods — typically a tariff/cost build-up plus revealed prices (delivered-fuel price differentials from the DCRA Alaska Fuel Price Survey and State of Alaska contract adders). Convergence between independent methods is the evidence standard here.

## 9.1 Convergence summary

| Mode | Part I value (PDF-derived) | Independent derivation (2026$) | Verdict |
|---|---|---|---|
| Road | 0.000528 | carriage **0.0006** (0.00045–0.0008); delivered 0.00105 | Converges — current value at low end |
| Barge | 0.000556 (→0.00087 inflation-adj.) | all-in **0.0010** (0.0006–0.0014); linehaul-only 0.00025 | Converges with the inflation-adjusted value; distance basis revised |
| Plane | 0.033 (→0.031 corrected) | **0.030** (0.015–0.055 at 130–350 mi) | Near-exact convergence |
| Ice road | 0.00667 (unsourced) | **0.012** single-rate (0.004–0.030) | Current value ~2× low; two cost regimes found |

## 9.2 Road — two methods converge at ~$0.0006 carriage

- **Build-up:** Alaska fuel-tanker linehaul runs $4.50–6.50/loaded-vehicle-mile (Alaska premium ~1.7–1.8× national spot; tanker/hazmat premium ~1.25–1.45× over flatbed; empty backhaul priced in). ÷ 8,000–10,000 gal → **$0.00045–0.00081/gal-mi**, central ≈ $0.0006. ATRI 2024 national floor: $2.26/mi ÷ 9,500 gal = $0.00024 — Alaska runs ~2.5–3.5× the national cost floor.
- **Revealed (State of Alaska heating-oil contract, OPPM, eff. 7/2025):** Fairbanks→Deadhorse adder differential $0.518/gal ÷ 495 road mi = **$0.00105/gal-mi delivered**; netting ~$0.15–0.25/gal of distributor margin/terminal handling gives ≈ **$0.0006/gal-mi pure carriage — independently matching the build-up**.
- **Remote low-volume premium:** Fairbanks→Eagle differential $1.066/gal ÷ 380 mi = **$0.0028/gal-mi** — small-volume gravel-road endpoints run **2.5–3× baseline**. Worth remembering if road edges ever serve Eagle-type endpoints.
- The Anchorage–Fairbanks pair is unusable (both are rack cities; the spread reveals refinery economics, not trucking).

**Recommended: 0.0006** (range 0.00045–0.0011). The current 0.000528 is inside the range but at the pure-carriage floor with full 10K-gal loads.

## 9.3 Barge — all-in ≈ $0.0010; route distance revised down to ~1,320 mi

- **Route distance (leg reconstruction, anchored on Anchorage–Dutch Harbor ≈ 825 nm and Port of Bethel ~80 nm above the river mouth):** Nikiski→Bethel ≈ **1,150 nm ≈ 1,320 statute miles** (range 1,210–1,440). The PDF's 1,800 mi is ~35% long. (NOAA *Distances Between US Ports* still worth a manual pull for the authoritative figure.)
- **Revealed, current:** Bethel — Vitus heating-oil contract (Dec 2025 award) nets to $3.50/gal ex-Bethel terminal ≈ **$1.30/gal premium** over the Cook Inlet lift price → **≈0.0010/gal-mi all-in**; transport-only (net of tank-farm/retail margin) ≈ 0.00064–0.00076. Kotzebue — utility diesel delivered at $3.10/gal (summer 2025 barge) → premium ≈ $0.90/gal ÷ ~1,750 mi = **0.00051/gal-mi** (bulk, no retail margin).
- **Build-up:** 3M-gal barge, ~16-day round trip at ~$44K/day ≈ $0.235/gal → **0.00018/gal-mi linehaul-only** (sensitivity 0.00014–0.00028). Consistent with ISER 2010 linehaul ($0.19–0.22 → $0.28–0.37 in 2026$ → 0.00023–0.00030).
- **Structure (Bethel vs. Kotzebue comparison):** the premium decomposes as a **fixed transfer/lightering component ≈ $0.55–0.90/gal plus ~0.00015–0.00025/gal-mi of distance**. A flat all-in $/gal-mi therefore falls with route length — 0.0010 is calibrated at Bethel-type distance and will overstate longer routes (Kotzebue reveals 0.0005).
- **Fee-table implication:** revealed lightering + terminal ≈ $0.8–1.2/gal dwarfs the current `("barge","storage")` fee of $0.15. With the current single-rate architecture that gap is absorbed by the blended 0.0010 rate; if the network ever splits linehaul from distribution, use linehaul 0.00025 + a $0.7–0.9/gal transfer fee instead.
- **Volatility flag:** all figures are pre-June-2026 steady state. The Iran-war shock is already moving 2026 contracts (Kotzebue expects >$6/gal delivered vs. $3.10) — that's commodity/risk, not freight, and should stay out of the baseline rate.

**Recommended: 0.0010 all-in** (range 0.0006–0.0014) for the current one-rate-per-mode design, calibrated to Bethel-type routes.

## 9.4 Plane — independent convergence at $0.030

- **Revealed (5 air-only communities, DCRA Winter 2026 + news):** village-minus-hub premiums are roughly flat at **$7–12/gal regardless of distance** (48–322 air mi). Net of ~$2/gal village storage/retail margin: Anaktuvuk Pass 0.019, Hughes 0.038, Arctic Village 0.041, Ambler 0.038–0.074 (hub ambiguous), Noatak (48-mi shuttle) 0.18 $/gal-mi.
- **Build-up (DC-6/C-46 tanker economics, $5,000–8,000/hr effective, 2,000–5,000 gal loads):** **0.012–0.027/gal-mi** at 130–350 mi; the mid case at 250 mi ($4.15/gal) sits just under the Anaktuvuk revealed premium — coherent, since revealed adds margin and storage.
- **Tariff proxy (Part I method, corrected inputs):** 0.023–0.038, midpoint 0.031 — brackets the above from the high side, as expected for an upper-bound proxy.
- **Distance dependence is strong and now quantified:** because the per-delivery fixed component is large (~$0.60–1.50/gal transport-only), a flat rate underprices <75-mi shuttles (real cost 0.10–0.22) and overprices long hauls. With the single-rate design, 0.030 is the defensible center; `PLANE_HANDLING_COST_PER_GALLON_USD` already captures part of the fixed term.

**Recommended: 0.030** (range 0.015–0.055 at typical 130–350 mi distances).

## 9.5 Ice road — two regimes; kept as ONE rate by decision

Three methods (cost build-up, Canadian winter-road analogs, DCRA revealed prices) all reproduce the same two-regime structure:

| Regime | Example | $/gal-mi |
|---|---|---|
| Engineered ice road, conventional tankers | Nuiqsut (60-mi Deadhorse road), Kuskokwim main stem, Tibbitt–Contwoyto (industrial analog: 0.0025) | **0.002–0.006** |
| Tundra snow trail, tracked/Rolligon convoys, 2,000–4,200-gal loads | Atqasuk (~90-mi trail from Utqiagvik), Anaktuvuk Pass CWAT | **0.012–0.030** |

Cleanest evidence (DCRA Winter 2026, same buyer — NSB Fuel Division — across communities): Nuiqsut pays only ~$0.15/gal over the marine-served baseline (Point Hope/Kaktovik $7.50–7.60) despite having no barge, while Atqasuk pays **+$1.25/gal over ~90 trail miles = 0.014/gal-mi**. A real 2026 anchor corroborates the trail regime: UIC's emergency Anaktuvuk convoy haul (100,000 gal, 12 runs, 109 mi) back-computes to ≈0.026/gal-mi. Trail *construction* cost is excluded (it's a fixed seasonal cost, potentially +$0.05–0.09/gal-mi at community volumes if amortized — don't fold it into the marginal rate).

**Decision (user, 2026-07-14): do not split the regimes — keep a single `IceRoad` rate.** Since the model's two ice-road-served communities (Nuiqsut, Atqasuk) sit one in each regime, any single rate misprices one of them; the least-bad single value is the agents' recommendation:

**Recommended: 0.012** (range 0.004–0.030) — vs. current 0.00667, which is calibrated to the engineered-road regime only and underprices Atqasuk-style trail haulage ~2×. The Tuntutuliak figure (~0.13, Part I §5) remains a distressed/emergency upper bound, not a baseline.

## 9.6 Final recommended rates (supersedes §7)

```python
BASELINE_RATES_PER_GALLON_MILE = {
    "Road":     0.0006,    # was 0.000528 — build-up + Dalton revealed converge at carriage ~0.0006
    "Barge":    0.0010,    # was 0.000556 — all-in revealed at Bethel; route is ~1,320 mi, not 1,800
    "Plane":    0.030,     # was 0.033   — revealed premiums + DC-6 economics + corrected tariff converge
    "IceRoad":  0.012,     # was 0.00667 — single rate spanning engineered-road and tundra-trail regimes
}
```

Ratio sanity check (new values): ice road ≈ 20× road, plane ≈ 2.5× ice road, barge ≈ 1.7× road per mile but barge routes carry 1000× the volume with the lowest linehaul-only rate (0.00025) — the ordering that makes communities extend ice roads rather than fly, and barge rather than truck, matches observed behavior.

Known limitation to carry forward: the four rates are not on an identical "includes" basis — Road 0.0006 is carriage-only (terminal handling lives in transfer fees), while Barge 0.0010 and Plane 0.030 are effectively all-in because their large lightering/handling components aren't in the fee table yet. Consistent decomposition (transport-only rates + realistic transfer fees) is the right long-term structure; §9.3/§9.4 give the split-out numbers when that day comes.

## 9.7 Highest-value manual fetches (blocked for agents this session)

1. **DCRA Alaska Fuel Price Report, Winter 2026** — commerce.alaska.gov (exact community price table underpinning §9.4/§9.5 revealed math)
2. **OPPM heating-oil contract sheet** — oppm.doa.alaska.gov/media/1337/08-heating-oil.pdf (full adder table: Anchorage, Glennallen, Tok rows would sharpen §9.2/§9.3)
3. **PCE FY2024 statistical report** (AEA) — utility delivered-fuel $/gal for every PCE community; the single best future refinement for plane/barge revealed rates
4. **NOAA Distances Between US Ports** — authoritative Nikiski→Bethel mileage
5. **ASTAR Atqasuk–Utqiaġvik road study** (north-slope.org) — has Rolligon fuel-haul cost detail for the trail regime

## Key sources

- ISER, *Components of Alaska Fuel Costs* (Feb 17, 2010) — local copy `components of alaska fuel costs.pdf`; pp. 7, 13, 15, 17–25 cited above.
- KYUK: [ice road reaches Tuntutuliak (Mar 2, 2026)](https://www.kyuk.org/public-safety/2026-03-02/kuskokwim-ice-road-reaches-tuntutuliak-as-part-of-halong-relief-efforts); [fuel delivered (Mar 24, 2026)](https://www.kyuk.org/public-safety/2026-03-24/tuntutuliak-receives-critically-needed-fuel-with-help-of-ice-road-extension)
- ATRI, *An Analysis of the Operational Costs of Trucking* (2025 ed., 2024 data): [press release](https://truckingresearch.org/2025/07/new-atri-report-shows-trucking-profitability-severly-squeezed-by-high-costs-low-rates/)
- [heavyequipmenttransport.com/trucking/alaska.php](https://www.heavyequipmenttransport.com/trucking/alaska.php) ($3.50–$6.00/mi)
- [Everts Air Cargo rates](https://evertsair.com/cargo/rates) (28% surcharge, eff. Jun 25, 2026); [Everts Air Fuel](https://evertsairfuel.com/) (charter bulk-fuel tankers)
- Distances: [airmilescalculator ANC–BET (398.8 mi)](https://www.airmilescalculator.com/distance/anc-to-bet/), [FAI–ARC (237.1 mi)](https://www.airmilescalculator.com/distance/fai-to-arc/); Tanana Chiefs Conference (Allakaket, 190 air mi)
- [ADN, rural fuel price spike (Apr 19, 2026)](https://www.adn.com/alaska-news/rural-alaska/2026/04/19/alaska-villages-can-already-pay-10-or-more-for-a-gallon-of-fuel-a-war-driven-spike-could-produce-a-survival-scenario/); [ADN, Noatak $16/gal (May 2022)](https://www.adn.com/alaska-news/rural-alaska/2022/05/18/fuel-in-the-alaska-village-of-noatak-was-16-a-gallon-the-costs-are-more-than-just-money/)
