## Addendum 2026-11-17: Ice road and winter trail fuel haul (proposal; nothing applied)

Segment: fuel hauled overland in winter on the model's `IceRoad` and `IceRoadConnector` edges (3,541.2 and
46.8 statute miles in the network), priced per gallon per statute mile. Nothing in this addendum has been
applied to `friction_costs.py`, and for this segment nothing should change on the present evidence. All 2026
figures are in 2026 dollars at CPI-U 332.243 (`index_basis_2026-11-17.md`). The working files used 330.0;
every inflated figure below was recomputed from its source-year value, and the text says where the rounded
value differs from the working files. The verdict summarised here comes from one adversarial verifier and has
not had a second independent review. It does not overturn the applied IceRoad rate.

Two kinds of winter haul sit behind this one rate, and the record calls them the two regimes throughout:

- **Truck regime.** A fuel tank truck driving on an engineered ice road or a frozen-river ice road. The
  earlier chapter names the Deadhorse to Nuiqsut oilfield ice road and the Kuskokwim River ice road out of
  Bethel as examples.
- **Sled regime.** A tracked snow tractor, or a rolligon (a vehicle on very large soft tyres), towing a
  sled-mounted fuel tank over a packed-snow tundra trail. The examples are the Utqiagvik (Barrow) to Atqasuk
  winter trail and the proposed Noatak haul.

Short names used below. **ATRI** is the American Transportation Research Institute, whose 2025 survey of
trucking costs is the source of the truck figures. **DEC 2007** is the December 2007 cost assessment by the
Alaska Department of Environmental Conservation and Northern Economics. **ISER 2010** is the February 2010
report "Components of Alaska Fuel Costs" by the Institute of Social and Economic Research, University of Alaska
Anchorage. **PCE report** is the Alaska Energy Authority's Power Cost Equalization statistical report for
fiscal year 2025 (July 2024 to June 2025), which gives each utility's fuel price. **CPI-U** is the consumer
price index for all urban consumers. "mph" is statute miles per hour. In the passages quoted from the Noatak proposal,
"DMTS" is the Delong Mountain Transportation System (the road and port of the Red Dog mine) and "NWFHLS" is the
proposal's own name for the Noatak winter fuel haul and logistics system. A bare number such as 0.0068 in a
table is a rate in dollars per gallon per statute mile unless the cell gives another unit.

### Status

**Assumed.** No tariff, contract or invoice for any Alaska winter fuel haul exists in the supplied documents,
so the skill's standard (three independent methods within about 3x) is not met. The statewide rate is a
carried-over value that blends two regimes which differ by about 3.8 times, and the blend weights are not in
any source. The model should keep the applied $0.010 per gallon per statute mile, labelled assumed, and report
any result that depends on an ice-road leg with a range and not the point alone.

Status part by part:

| Part | Status | Why |
|---|---|---|
| Statewide single rate (what the model uses) | **Assumed** | Carried value. As one quantity the three checked points spread 3.81 times, which fails the 3x standard. |
| Sled regime level, about $0.026 per gallon per statute mile | Would be **Provisional** if the model carried it separately; it does not | Two method families (a cost build-up and one price difference) agree, but there are only two, the price case is a single community, and its delivery mode is not documented in the supplied files. |
| Truck regime level, about $0.007 per gallon per statute mile | **Assumed** | One cost build-up whose Alaska adjustments are all unsourced. No Alaskan price evidence supports it. |
| Fixed part per delivery (the vehicle's own loading and unloading time) | **Assumed**, and not billed | No observed price identifies it. It stays inside the per-mile rate. |
| Road-to-ice-road fee ($0.022 per gallon) and barge-to-ice-road fee ($0.011 per gallon) | **Assumed**, unchanged | Covered in the transfer-fee addendum; noted here only for the double-count check. |

### Result

Rates are in United States dollars per gallon of fuel per statute mile of model ice-road route, for a loaded
one-way mile with the empty return inside the figure.

| Item | Value |
|---|---|
| Form | Pure per-mile rate, all-in. No separately billed fixed part. |
| Point the model carries | $0.010 per gallon per statute mile (the applied value, unchanged, status Assumed) |
| Range coded today | $0.004 to $0.025 per gallon per statute mile (the applied band) |
| Verifier's best single reading, if one statewide figure must be used | $0.013 per gallon per statute mile. Not ready to apply. |
| Verifier's range | $0.006 to $0.030 per gallon per statute mile |
| Truck regime, line-haul | $0.0068 per gallon per statute mile ($0.0067 at the 330.0 basis); about $0.007 to $0.009 all-in |
| Sled regime, line-haul | $0.0255 (build-up) and $0.0257 (price difference) per gallon per statute mile; about $0.026 all-in |
| Fixed part | $0 billed separately. Indicative size if it were split out: truck $0.10 to $0.15 per gallon per delivery; sled $0.10 per gallon on crew time only, up to $0.42 per gallon at the full hourly cost. |
| Dollar basis | 2026 dollars, CPI-U 332.243 |
| Source-year figures | The carried $0.010 does not come from one dated source. The pieces under the regime values do: truck hourly costs are 2024 dollars (ATRI); the snow tractor and sled are $350,000 in 2012 dollars (dollar year assumed); the Atqasuk price difference is $1.705 per gallon in fiscal-year 2025 dollars, which is $0.0249 per gallon per statute mile over 68.46 miles. |

Restatement note. Moving from 330.0 to 332.243 does not change the carried point ($0.010), the verifier's
blended reading ($0.013; the restatement script gives 0.0131 at both bases) or the rounded range ends ($0.006 and $0.030).
It moves the last digit of several working figures. The main ones: the truck build-up goes from 0.0067 to
0.0068, the corrected sled build-up from 0.0254 to 0.0255, the Atqasuk price difference from $1.748 to $1.760
per gallon and from 0.0255 to 0.0257 per gallon per statute mile. Others are noted where they appear.

Index sensitivity. No marine freight index applies, because no input is a marine freight figure. The verdict
gave a CPI sensitivity in the working files (332.8 against 330.0, plus 0.85%); the new basis sits inside it.

A result that depends on an ice-road leg should carry both ranges until the owner edits the point: the applied
upper end is $0.025, and the verdict says the upper end should be about $0.030 whenever the point is next
edited, because the straight-line Atqasuk reading (0.0308) and the slow-speed sled variant (0.0351) both sit
above $0.025.

### Methods and convergence

Values are in dollars per gallon per statute mile, 2026 dollars at CPI-U 332.243, unless a per-gallon figure is
stated. "PDF p." is the page of the PDF file; "printed p." is the number printed on the page. Only two method
families exist for this segment: a cost build-up and a revealed price difference. There is no published tariff
or contract.

| Method | Counted as independent? | Value (2026 dollars) | Source documents with page | How it was checked | Kept or rejected and why |
|---|---|---|---|---|---|
| Truck regime build-up: ATRI highway truck cost per hour, rescaled for ice-road speed, a short season and Alaska costs, doubled for the empty return, divided by the load | Yes, as the only truck-regime point checked locally | 0.0068 line-haul (0.0067 at 330.0). Variants: 0.0047 at 5,000 gallons; 0.0055 with a 25 mph empty return; 0.0039 with both. Stacked envelope 0.0015 to 0.033. | `ATRI-Operational-Costs-of-Trucking-07-2025.pdf`, Table 9, printed p. 16 (PDF p. 19); PDF pp. 11, 15, 17, 48. `cost-assessment-fordiesel-fuel-transition-in-western-and-northern-alaska-communities.pdf`, printed p. 22 (PDF p. 38). | Verifier redid the arithmetic. For this record the Table 9 cells and the quotes were found on the stated pages and the script was rerun at both index values. | Kept as a point, low confidence. It is carrier cost with no margin, so it is a floor on price. Every Alaska adjustment is assumed. |
| Sled regime build-up, corrected: snow tractor and sled capital from the Noatak request, annualised, plus crew, repairs and fuel, divided by speed and load | Yes (sled family 1) | 0.0255 at 11 mph (0.0254 at 330.0). Variants: 0.0351 at 8 mph; 0.0225 at 12.5 mph. System check on the source's own volumes: 0.0215 to 0.0286; 0.0337 with season-salaried crew. Plausible band 0.019 to 0.035. | `Northwest_Arctic_Borough_Noatak_Winter_Fuel_Haul_System.pdf`, PDF pp. 1 to 3 (text) and PDF pp. 5 and 10 (image pages) | Verifier rendered the image pages. For this record PDF pp. 5 and 10 were viewed again, the text quotes were found on PDF pp. 1 to 3, and the script was rerun. | Kept, corrected. It is a 2012 proposal, not an outturn cost. |
| Sled regime build-up as submitted by the second-round analyst | No | 0.046 (0.0464 recomputed) | Same document, PDF pp. 1 to 3 only | Verifier traced the capital figure to PDF p. 5. | Rejected. Capital was overstated by 51%: the $425,000 request was read as the tractor alone and a $150,000 sled was added, but the source gives $350,000 for tractor, sled and shipment together. |
| Revealed price, corrected: Atqasuk utility fuel price less the mean of four marine-served North Slope villages, over the Barrow to Atqasuk ice path | Yes (sled family 2) | 0.0257 gross, all-in (0.0255 at 330.0). 0.0308 on the 57.1-mile straight line. Net of an assumed fixed part of $0.10 to $0.42 per gallon: 0.020 to 0.024 (0.019 to 0.024 at 330.0). | `2026.03.01 FY2025 PCE Statistical Report by Community (Final).pdf`, report pp. 27, 81, 135, 136, 179. Network tables. DEC 2007, printed p. 22 (PDF p. 38). | The five rows were matched on the decoded report pages and in the price table. The ice path was rerun: 68.46 statute miles. | Kept as a point. It is one case, the delivery mode in fiscal year 2025 is not documented, and the figure is gross. |
| Revealed price as submitted (statewide rate from price differences; Kasigluk and Atmautluak) | No (ceiling only) | Atmautluak: 0.0135 on the 44.4-mile ice path, 0.0356 on the 16.8-mile straight line. Kasigluk is negative (minus 0.0057 and minus 0.0111). | PCE report pp. 26, 28, 84. Network tables. | Rows matched; ice paths rerun (44.4 and 49.2 miles). | Ceiling only. No source says how these two villages receive fuel. The analyst's list of ice-road hubs missed hubs joined through a transfer edge. |
| Revealed price: Nuiqsut against the same four villages | No | Minus $0.455 per gallon in fiscal-year 2025 dollars (minus $0.470 in 2026 dollars); no rate | PCE report p. 124 | Row matched. | Not usable. Nuiqsut is the cheapest village in the borough on this series, and its supply comes by a different route, so the ice-road leg cannot be isolated. |
| Alatna and Allakaket frozen-river truck leg | No (ceiling only) | No price step at $0.50 resolution in 2010 dollars, which is under $0.76 per gallon | `components of alaska fuel costs.pdf`, PDF p. 65 | Quotes found on PDF p. 65. | Weak ceiling on a fixed part for a short truck crossing. No distance is given, so there is no per-mile figure. |
| Earlier chapter, methods A2 and D: snow-trail convoy at about $900 per hour, calibrated on the 2026 Anaktuvuk Pass haul | No. Same family as the sled build-up. | 0.021 routine (0.017 to 0.036; 0.036 is the emergency bound). Carried as the chapter states it; not restated. | Operator write-up and trade-magazine feature cited in `04_ice_road.md`. None is among the supplied files. | Not re-verified. | Carried only as a cross-check. It rests on an unverified $900 per hour and a 60% routine discount. |
| Earlier chapter, method A1: ATRI cost rescaled | No. Same method as the truck build-up. | 0.0041 (0.0034 before the chapter's 20% loading adder) | ATRI, as above | Verifier reproduced the chapter's arithmetic. | Counted once with the truck build-up. |
| Earlier chapter, Canadian methods B2, B3 and C | No (corroboration and floor only) | Ontario 0.0065; Northwest Territories 0.0033; Tibbitt to Contwoyto industrial floor 0.0016. Carried as the chapter states them; not restated. | Web sources cited in `04_ice_road.md`. None is among the supplied files. | Not re-verified. | The only support for the truck regime outside the build-up, and none of it is Alaskan or checkable here. |
| Bounds from other evidence | No (bounds only) | Competitive long-haul air 0.0190. Short-hop air 0.132 (Noatak against Kotzebue). Emergency ice-road truck delivery about 0.12 to 0.155. | ISER 2010, PDF p. 13. PCE report pp. 94 and 120. The emergency figure is from web search snippets only. | ISER quote found; PCE rows matched. The emergency figure was not re-confirmed. | No bound is broken by the regime values. |

Convergence, from the project toolkit's test on same-form figures:

| Test | Points | Spread | Reading |
|---|---|---|---|
| Sled regime | build-up 0.0255; price difference 0.0257 | 1.01 | Two families agree, but there are only two |
| Sled regime with the chapter's convoy method | adds 0.021 | 1.22 | The convoy method is not a third family |
| Truck regime | build-up 0.0068; chapter Ontario 0.0065; chapter Northwest Territories 0.0033 | 2.05 | Only the build-up could be checked locally |
| Statewide, the three points checked here | 0.0068; 0.0255; 0.0257 | 3.81 | Fails about 3x |
| Statewide with the chapter's web methods | six points | 7.79 (7.74 at 330.0) | Fails |
| Second round as submitted | 0.0068; 0.0464 | 6.88 (6.87 in the verdict) | Fails |

Spread. Taken as one statewide quantity, the three points checked in this round spread 3.81 times (the verdict
states the same figure at the 330.0 basis), which fails the standard of about 3x. Within each regime the figures agree
(1.01 for the sled regime, 2.05 for the truck regime), but neither regime has three independent methods: the
sled regime has two families, and the truck regime has one method that could be checked in the supplied
documents. The disagreement is therefore between the regimes and not between the methods. A single statewide
rate cannot meet the standard; a rate per regime could, if a third kind of evidence were found.

Bounds. None is broken: the industrial floor (0.0016), the Atmautluak ceiling (0.0135 to 0.0356) and the
emergency ceilings (0.036, and about 0.12 to 0.155 from search snippets) all bracket the regime values. The
sled regime is above competitive long-haul air per mile (0.0190) and far below short-hop air (0.132), which
fits air being the usual mode for long hauls.

Form. A fixed part per delivery is physically real, because the vehicle and crew wait while loading and
unloading. No observed price identifies it: each regime has one usable distance, and the Alatna crossing shows
no step at $0.50 resolution. The community ice legs in the network cluster at 44 to 69 miles (Atmautluak 44.4,
Kasigluk 49.2, Atqasuk 68.5), so folding the waiting time into the per-mile rate distorts little between them.

### Derived versus assumed

Rows 1 to 4 are what the carried figure rests on. Rows 5 to 43 are what the verifier's regime values, blended
reading and range rest on. Long quotes are in the list under the table (Q1 to Q14).

| # | Input | Value | Type | Reference | What changes if it is wrong |
|---|---|---|---|---|---|
| 1 | One statewide ice-road rate, no regime split | One rate for both regimes | Owner decision | `friction_costs.py`, rate comment: "single rate spanning two verified regimes per user decision (no regime split)". The date is not recorded in the file; the chapter's rounds are dated 2026-07-15 and 2026-07-17. The owner restated the choice on 2026-11-17 (statewide segments only, no village-specific rates). | With a split, the truck and sled regimes would each carry their own rate and most of the known error would go. |
| 2 | Carried point | $0.010 per gallon per statute mile | Assumed (earlier chapter's judgement, carried over) | `04_ice_road.md`, sections 7 and 8: a lean toward the geometric mean of 0.0045 and 0.021 | The verifier's reading is 0.013; the difference is smaller than the uncertainty. |
| 3 | Carried range | $0.004 to $0.025 | Assumed (carried over) | `friction_costs.py`, `BASELINE_RATE_RANGES` | The verdict puts the upper end at about 0.030. |
| 4 | All-in form: the rate carries the ice-road vehicle's own loading and unloading | No separate ice-side fee | Assumed (project convention; skill rule 5) | `friction_costs.py`, fee comment block (re-derivation dated 2026-07-28); skill invariant 5 | If changed to line-haul only (about 0.011), the waiting time must be billed once per delivery on the transfer edges. |
| 5 | ATRI truck cost per hour, 2024 | Wages $32.10; benefits $7.93; repair $7.96; insurance $4.11; permits $0.36; tires $1.90; lease or purchase $15.70; total $90.89 | Quoted | ATRI, Table 9, 2024 column, printed p. 16 (PDF p. 19); Q1 | The truck build-up moves in proportion. |
| 6 | ATRI average speed | 40.20 mph | Quoted | ATRI, PDF p. 11; Q2 | Sets annual hours in input 7. |
| 7 | ATRI annual truck mileage | 82,677 miles in 2024 | Quoted | ATRI, PDF p. 15; Q3 | With input 6 gives 2,057 hours a year, the base for the ownership cost. |
| 8 | ATRI waiting time per stop | 1 hour 38 minutes | Quoted | ATRI, PDF p. 48; Q4 | Sizes the indicative truck fixed part only. It is general-freight detention, not tank loading. |
| 9 | Only tank truck size in the supplied documents | Three 2,500-gallon and one 2,600-gallon tankers (Nome town delivery) | Quoted | DEC 2007, printed p. 22 (PDF p. 38); Q5 | Shows that input 11 has no local source for ice-road rigs. |
| 10 | Ice-road truck speed | 15 mph loaded and empty (variant: 25 mph empty) | Assumed (second-round analyst; the variant is the earlier chapter's) | None | 0.0068 falls to 0.0055 with the faster return. |
| 11 | Truck load | 3,500 gallons (earlier chapter: 5,000) | Assumed (second-round analyst) | None | The rate is inversely proportional: 0.0047 at 5,000 gallons. This is the largest single lever in the truck regime. |
| 12 | Truck season use | 600 hours a year | Assumed (second-round analyst) | None | Ownership is half of the hourly cost; fewer hours raise it in proportion. |
| 13 | Alaska adjustments to ATRI | Wages times 1.3; repair times 2; ownership times 1.4 | Assumed (second-round analyst) | None | With no adjustments and 1,000 hours a year the hourly cost is $91.8, against $158.5 in the central case. |
| 14 | Truck fuel use and price | 4 miles per gallon; $5.00 per gallon, taken as 2026 dollars | Assumed (second-round analyst) | None | Fuel is $2.50 of the $23.64 per loaded mile. |
| 15 | Empty return | The full round trip is charged to the loaded mile | Assumed (analyst and verifier) | None; winter hauls are out and back | A backhaul would lower every build-up figure. |
| 16 | CPI-U factors to 2026 | 2010: 1.5237; 2012: 1.4471; 2022: 1.1353; 2024: 1.0591; 2025: 1.0320 | Computed | 332.243 divided by the annual averages in `index_basis_2026-11-17.md` | See the restatement note. |
| 17 | Truck build-up result | $158.5 per hour; $23.64 per loaded mile; 0.0068 | Computed | Inputs 5 to 7 and 10 to 16; `restate_ice_road_332243.py` | Follows its inputs. |
| 18 | Noatak equipment cost | $350,000 for "an Arctic Tractor & sled and shipment to the DMTS port" | Quoted (image page) | Noatak proposal, PDF p. 5, Table 1; Q6 | The sled build-up moves with it: capital and repairs are 63% of the hourly cost. |
| 19 | Noatak total request and permitting | $425,000 in total; $75,000 for permitting and planning | Quoted | Noatak proposal, PDF p. 1 and PDF p. 5; Q6, Q7 | Reading the $425,000 as equipment gives the rejected 0.046. |
| 20 | Dollar year of the Noatak request | 2012 | Assumed (analyst and verifier) | The document is a 2012 Legislature report printed 5/2/2012; it states no dollar year | Taking 2013 as the dollar year (the request is for fiscal year 2013) lowers the capital by about 1.4%. |
| 21 | Snow tractor speed and trip time | 10 to 12 mph; about 2 hours one way | Quoted | Noatak proposal, PDF p. 3; Q8 | See input 22. |
| 22 | Speed used | 11 mph | Assumed (verifier: the midpoint of the quoted range; the analyst used 8 mph) | Input 21 | 0.0351 at 8 mph; 0.0225 at 12.5 mph. |
| 23 | Sled load per trip | "up to 3-5000 gallons"; 3,500 used | Quoted range; the 3,500 is Assumed (second-round analyst) | Noatak proposal, PDF p. 3 and PDF p. 10; Q8, Q9 | Inversely proportional. The source also implies 1,750 to 2,000 gallons per trip (input 24). |
| 24 | Noatak annual demand and trips | 350,000 to 400,000 gallons a year; up to 200 round trips with one tractor | Quoted (image page) | Noatak proposal, PDF p. 10; Q9 | Used for the system-level check (0.0215 to 0.0286). The two figures do not agree with input 23. |
| 25 | Sled season use | 400 hours a year | Assumed (second-round analyst) | Consistent with input 24 at 3,500 gallons a trip (107 trips of 4 hours) | Fewer hours raise the rate; capital and repairs are spread over the hours. |
| 26 | Sled crew and wage | Two people at $60 per hour, taken as 2026 dollars | Assumed (second-round analyst) | The source gives only "3-5 local jobs" for the whole system | Crew is $120 of the $491 per hour. |
| 27 | Snow tractor fuel burn and price | 12 gallons per hour at $5.00 per gallon | Assumed (second-round analyst) | None | Fuel is $60 of the $491 per hour. |
| 28 | Repairs | 12% of capital a year | Assumed (second-round analyst) | None | About $152 of the $491 per hour. |
| 29 | Equipment life and discount rate | 12 years; 7% | Assumed (second-round analyst) | None | About $159 of the $491 per hour. |
| 30 | Sled build-up result | Capital $506,481; $491 per hour; 0.0255 | Computed | Inputs 16 and 18 to 29 | Follows its inputs. |
| 31 | Atqasuk utility fuel price and gallons, fiscal year 2025 | $7.41 per gallon; 274,877 gallons | Measured | `shared/pce_prices_with_distances.csv`; PCE report p. 27 | The price difference moves one for one. |
| 32 | Prices in four marine-served North Slope villages | Kaktovik $5.73; Point Hope $5.68; Point Lay $5.74; Wainwright $5.67 per gallon | Measured | Same table; PCE report pp. 81, 135, 136, 179 | Their spread is only $0.07 per gallon. |
| 33 | Those four villages stand in for the supply price at Utqiagvik (Barrow) | Mean $5.705 per gallon | Assumed (verifier) | Barrow has no PCE row | If Barrow's laid-in price is lower, the true premium is larger, and the reverse. |
| 34 | Atqasuk's fiscal-year 2025 utility fuel moved overland by trail | Yes | Assumed (verifier) | Rests on the applied file's note that Atqasuk is listed as ice road from 2024-02-15 (Q13) and on the premium being far below Noatak's all-air premium. DEC 2007 says "Typically, air transport is used" (Q10). | If part of it flew, the figure is not a trail cost and the sled regime loses its second family. |
| 35 | The whole premium is haul cost | $1.705 per gallon | Assumed (verifier) | None | The figure is gross: it holds any extra tank handling at Utqiagvik and the waiting time at both ends. |
| 36 | Dollar year of fiscal-year 2025 prices | Treated as 2025 annual average | Assumed (analyst and verifier) | The reporting period is 07/01/24 to 06/30/25 | At most 2.6%, the gap between the 2024 and 2025 annual averages. |
| 37 | Barrow to Atqasuk ice path | 68.46 statute miles (57.1 in a straight line) | Measured | Harness `fuel_network.duckdb`, tables `network_nodes` and `network_edges`; shortest path on IceRoad and IceRoadConnector edges between the ice ends of transfer edges 92909 and 93034; `verify2/iceroad/net2.py` | 0.0308 on the straight line. Distances change if the network is re-exported. |
| 38 | Atqasuk price-difference result | $1.760 per gallon in 2026 dollars; 0.0257 | Computed | Inputs 16 and 31 to 37 | Follows its inputs. |
| 39 | Blend of the two regimes into one reading | Geometric mean of about 0.007 and 0.026, giving 0.013 | Assumed (verifier's judgement) | Verdict, recommended point | A cost-preserving arithmetic blend is 0.014 to 0.016. |
| 40 | Gallons behind the regime split | Nuiqsut 279,232; Atqasuk 274,877 | Measured | Same table; PCE report pp. 124 and 27 | These are utility generation gallons only, not total fuel. |
| 41 | Those two villages represent the truck and sled traffic, about half each | About 50/50 | Assumed (earlier chapter) | `04_ice_road.md`, section 7 | The blend moves toward whichever regime carries more gallons. |
| 42 | Which network ice edges belong to which regime | Unknown | Assumed (no flag exists) | `network_edges` has no regime field | Without it a regime rate cannot be applied or tested. |
| 43 | Range ends | 0.006 and 0.030 | Assumed (verifier's judgement) | Verdict: the truck regime's all-in centre to the upper sled reading | The stacked envelope is 0.0015 to 0.23 and is not a usable range. |

Quoted passages:

- Q1. ATRI, PDF p. 17: "Per-hour operational costs in 2024 totaled $90.89 with fuel and $71.57 without fuel." The line items are the 2024 column of Table 9 on PDF p. 19 (printed p. 16).
- Q2. ATRI, PDF p. 11: "converted to costs per hour (CPH) using the average speed of 40.20 miles per hour (MPH)".
- Q3. ATRI, PDF p. 15: "Average annual truck mileage increased for a second year in a row, from 80,159 in 2023 to 82,677 in 2024".
- Q4. ATRI, PDF p. 48: "Overall average dwell time decreased slightly in 2024, by 2 minutes, to 1 hour and 38 minutes per stop".
- Q5. DEC 2007, PDF p. 38: "The company has a fuel tank farm and a fuel tanker truck fleet with three 2,500 gallon and one 2,600 gallon fuel tankers."
- Q6. Noatak proposal, PDF p. 5 (image), Table 1 "Funding/Project Plan": "Equipment Procurement | Procurement of an Arctic Tractor & sled and shipment to the DMTS port. | July- December 2012 | Requesting $350,000" and "Permitting-Environmental-Logistics planning | Plan development and submittal of permits. | 2012 | $75,000".
- Q7. Noatak proposal, PDF p. 1: "The capital request for the NWFHLS Project is $425,000 to cover the procurement of an Arctic Snow Track Tractor capable of hauling fuel off road for up to 30 miles in winter conditions. The NWFHLS Project will be a self-sustaining business, operational costs will be paid for by the end-user".
- Q8. Noatak proposal, PDF p. 3: "Most Arctic Snow Tractors travel from 10-12 mph- approximately a 2 hour trip one way from the three proposed transportation corridors. We are currently estimating up to 3-5000 gallons of fuel transported with each trip."
- Q9. Noatak proposal, PDF p. 10 (image): "The annual fuel demand in Noatak is estimated to be 350-400,000 gallons annually for both heating, power generation, and vehicular travel purposes. The proposed fuel haul system could transport up to 3-5000 gallons of fuel with each trip. With one tractor, it would require up to 200 round trips to meet annual fuel demand".
- Q10. DEC 2007, PDF p. 38: "Typically, air transport is used to supply Atqasuk but fuel deliveries from Barrow to Atqasuk have occasionally been made in winter using rolligons or similar equipment for tundra travel, often towing sled-mounted fuel tanks."
- Q11. DEC 2007, PDF p. 38: "After freeze-up, fuel deliveries from Bethel are made to villages up and down the Kuskokwim River." PDF p. 23 (printed p. 7): "almost all fuel is delivered by barge, except for some small amounts that are delivered by air or moved overland on ice roads."
- Q12. ISER 2010, PDF p. 65: "Fuel is trucked from Allakaket to Alatna when the river is frozen." and "In January 2010, the price of gasoline and diesel for heating remained at the same price of $7.00 and $6.50 per gallon, respectively in both communities." PDF p. 13: "the most competitive air deliveries have a transportation component of ~$1.25 per gallon per hundred air miles."
- Q13. `friction_costs.py`, comment above the ice-road community loader: "Atqasuk is "Plane" as of 2023-08-15 and "Ice Road" as of 2024-02-15 onward." This is a comment in the applied file; the delivery-method layer it describes was not opened.
- Q14. North Slope winter trails sheet, PDF p. 1: "FY2020 Request: $1,672,077"; "This project was awarded at a total of $4,000,000"; "This project focuses on maintaining preexisting trails and managing public safety."

Which assumptions carry the most weight. Three carry most of it. First, the regime mix (inputs 39, 41 and 42):
the two regimes differ by about 3.8 times, no source says how many gallons or miles move under each, and the
network cannot tell an engineered ice road from a snow trail, so any single figure between 0.007 and 0.026 is
a judgement. Second, the reading that Atqasuk's fuel went overland in fiscal year 2025 (input 34): the sled
regime's second method family rests on it, and the only supplied document on the point is an 18-year-old
sentence that says air is typical. Third, the truck load (input 11): the truck regime moves from 0.0068 to
0.0047 between 3,500 and 5,000 gallons, and the only local figure is for 2,500-gallon town delivery trucks.
After those, the season hours (inputs 12 and 25) matter most, because equipment cost is spread over them.

### What the figure includes and excludes

Inside the all-in per-mile rate:

- Ownership of the vehicle and of its tank or sled, crew, repairs, tires, insurance and permits, and fuel burned.
- The empty return trip.
- The ice-road vehicle's own waiting time while loading and unloading, at both ends.
- In the Atqasuk price reading only, whatever intermediate tank handling the borough incurs at Utqiagvik. It
  cannot be separated.

Not inside, and not to be added to the rate:

- Building and maintaining the ice road or trail. This is public money. The North Slope winter trails sheet
  gives $1,672,077 for fiscal year 2020 and $4,000,000 in total, with no mileage, so it cannot be turned into
  a rate from the supplied documents.
- Tolls (none found) and carrier margin (the ATRI figures are cost, and the borough price is at cost).
- Storage of the winter fuel inventory at the origin, which is outside the model.
- The upstream road or barge line-haul to the start of the ice leg, and the fuel itself.

Fees that touch ice legs, so that no handling is billed twice:

| Event | Applied fee | Reading |
|---|---|---|
| Road to ice road (`IceRoadRoadTransfer`, 12 edges) | $0.022 per gallon, range $0.014 to $0.032 | Keep. It bills only the road side of the pumped changeover, so it does not overlap the ice-side waiting time in the rate. |
| Barge to ice road (`BargeIceRoadTransfer`, 21 edges) | $0.011 per gallon, range $0.00 to $0.02 | No double count, but a possible under-count at terminal hubs (below). |
| A separate ice-road loading fee | None | Do not add one while the rate is all-in. It would bill $0.10 to $0.42 per gallon twice. |

- A Barrow to Atqasuk delivery crosses two road-to-ice edges (92909 and 93034), which is $0.044 per gallon in
  fees. That is consistent with the fee's definition.
- The barge-to-ice fee skips the terminal's truck-rack charge, which is in neither all-in rate. The Bethel
  terminal sheet lists the truck rack at $0.25 per gallon (effective 10 August 2022), which is $0.284 in 2026
  dollars ($0.282 at the 330.0 basis). Where the ice leg starts from a road node (Barrow, Atqasuk, Nuiqsut)
  the path already pays the barge-to-road fee of $0.24 per gallon, so the rack is billed once. The ten
  barge-to-ice edges on the Bethel-area ice component bypass it, an under-count of about $0.24 to $0.28 per
  gallon on those paths. (The verdict says "six"; that is the number of ice-road nodes the ten edges meet,
  recounted for this record from `network_edges`.) That question belongs to the transfer-fee addendum.

### Compared with the applied value and the earlier chapter

Applied today: `IceRoad` $0.010 per gallon per statute mile, range $0.004 to $0.025. The comment describes one
rate spanning a tanker regime of about 0.004 and a cat-train regime of about 0.02, split about half and half
on PCE gallons, with a known bias of about two times high on Nuiqsut-type edges and two times low on
Atqasuk-type edges.

Earlier chapter (`04_ice_road.md`): $0.010, range $0.004 to $0.027, reached by leaning toward the geometric
mean of 0.0045 and 0.021. It described three independent families and moderate confidence in the point.

This round neither overturns nor tightens the applied value. It confirms that $0.010 is inside the supported
range, and it lowers the label the figure can carry.

Confirmed:

- The two-regime structure and the order of magnitude of each regime.
- The gallons used for the split (Nuiqsut 279,232 and Atqasuk 274,877).
- The chapter's reading of the Noatak document ($350,000 of equipment plus $75,000 of permitting, 350,000 to
  400,000 gallons a year, about 200 round trips). The second-round fact sheet and build-up had the capital
  wrong because the text extraction lacks the image pages.

Moved, modestly:

- The sled regime firms at about 0.025 to 0.026 and not 0.021. Two readings that are not emergency hauls agree
  (0.0255 and 0.0257). The chapter's reason for leaning to the geometric mean, emergency contamination of the
  sled figure, no longer holds.
- The truck regime at village-sized loads is about 0.0068 and not 0.0041 to 0.0045.
- The blend therefore rises from 0.010 to about 0.013 (geometric), or 0.014 to 0.016 if cost is preserved.
- The stated bias changes. At $0.010 the truck regime is about 1.4 times high (against an all-in truck figure of
  about 0.007), not 2 times, and the sled regime is about 2.6 times low. The model prices Barrow to Atqasuk at 68.46 miles times $0.010 plus two fees
  of $0.022, which is $0.73 per gallon, against a revealed $1.76 per gallon.

Weakened:

- The Alaskan support for the truck regime. Nuiqsut is $0.455 per gallon below the marine-served villages on
  PCE prices, so the chapter's Nuiqsut check does not survive a change of price series.
- The Kuskokwim as a tanker regime at about 0.004 has no price evidence in any supplied source. The one price
  found, from search snippets only, is an emergency quote that implies about 0.12 to 0.155.
- The chapter's count of three independent families. On this round's reading there are two families (build-up
  and price difference), and the Canadian figures could not be checked.

Not overturned. $0.010 is inside the verifier's range of 0.006 to 0.030, and the shift of about 30% to 0.013
is smaller than the uncertainty. The verifier would not edit the point on this evidence, and this record
agrees. A regime split would remove most of the error; that is the owner's decision, and it would have to be
taken together with the plane segment, because at the sled-regime rate the trail to Atqasuk costs $1.76 per
gallon (0.0257 times 68.46 miles) while the applied plane rate gives $1.43 per gallon (0.025 times 57.1 air
miles), so the plane rate would undercut the trail.

Two inconsistencies in the applied file's comments were noticed and are not resolved here. The rate comment
says ice roads run January to April; the fee comment says January to March. The fee comment places the 21
barge-to-ice edges "at North Slope hubs", while the network has 16 of them on the Kuskokwim, Yukon and Tanana
(ten of those on the Bethel-area ice component) and 5 on the North Slope, the same counts as in the
transfer-fee addendum.

### Open evidence gaps

A change to the point, or a status above Assumed, needs a third kind of evidence. In order of value:

1. A haul invoice, contract rate or purchase order for one Alaska winter fuel haul. Examples: the North Slope
   Borough Public Works contract or expenditure record for the Atqasuk fuel haul; an operator's hourly rate
   sheet for a snow tractor or rolligon; the executed operating budget of the Noatak haul, if it ever ran.
2. A carrier's published or quoted per-gallon surcharge for ice-road delivery from Bethel on the Kuskokwim,
   with the supply-point price for the same month.
3. A record of how Atqasuk's fuel was delivered in fiscal year 2025 (borough fuel division delivery logs or
   the delivery-method layer's source), and a laid-in fuel price at Utqiagvik.
4. A laid-in fuel price at Deadhorse (a wholesaler's rack price), so that the Nuiqsut ice-road leg can be
   separated from its different supply route.
5. A regime flag on the network's ice edges (engineered or river ice road against tundra trail), and total
   gallons hauled by regime, not only utility generation gallons.
6. The full public-radio article on the March 2026 Tuntutuliak ice-road delivery ($13.60 per gallon quoted)
   and a March 2026 Bethel bulk price. Together they would give the first real Alaska ice-road delivered
   price, though an emergency one.
7. A payload figure for the tank trucks that actually run on Alaska ice roads (a carrier equipment list or a
   weight-limit notice for an ice road).

Corrections owed to the working files: fact-sheet rows 6.1 and 6.5 in `extracts/local_air_road_winter.md`
should say that $350,000 is the tractor, sled and shipment, that $75,000 is permitting, that demand is
350,000 to 400,000 gallons a year, and that one tractor needs up to 200 round trips. The Noatak source is
itself inconsistent: 350,000 to 400,000 gallons over up to 200 trips is 1,750 to 2,000 gallons a trip, against
"up to 3-5000 gallons" a trip.

### Working files

All paths are under `harness: blind_derivations/working_2026-11-17/`.

| Path | What it holds |
|---|---|
| `derive2_results.json` | Key `verdicts.iceroad` (the verifier's verdict); keys `derivations.iceroad-operations-buildup` and `derivations.iceroad-revealed-prices` (the second-round blind derivations) |
| `derive2/iceroad_buildup/build.py` | Second-round build-up script, as run (330.0 basis; holds the capital error) |
| `derive2/iceroad_revealed/calc.py` and `calc_out.txt` | Second-round price-difference script and output |
| `verify2/iceroad/verify.py` | Verifier's recomputation, convergence tests and blends (330.0 basis) |
| `verify2/iceroad/net.py`, `net2.py`, `net3.py`, `net4.py` | Verifier's network checks: ice components, transfer edges, ice paths |
| `verify2/iceroad/noatak_img/p-05.png` to `p-10.png` | The image pages of the Noatak proposal, rendered |
| `extracts/local_air_road_winter.md` | Fact sheet, Topic 6 (winter haul); rows 6.1 and 6.5 need the correction above |
| `shared/pce_prices_with_distances.csv`, `work/pce/pce_decoded.txt` | The fiscal-year 2025 price table and the decoded report pages |
| `shared/index_basis_2026-11-17.md` | The index basis |
| `record/ice_road_checks/restate_ice_road_332243.py` and `restate_ice_road_332243_output.txt` | Written for this record: repeats the verifier's arithmetic at 330.0 and at 332.243 and prints the change |
| `record/ice_road_checks/verify_py_output_330basis.txt` | Output of the verifier's script, rerun for this record (identical on a second rerun) |
| `record/ice_road_checks/net_rerun_output.txt`, `net2_rerun_output.txt`, `net3_rerun_output.txt`, `net4_rerun_output.txt` | Outputs of the network checks, rerun for this record (identical on a second rerun) |
| `record/ice_road_checks/find_quote_page.py` and `quote_confirmation_output.txt` | Written for this record: finds each quoted passage and its PDF page in the text files |
| `record/ice_road_checks/pce_rows_check.py` and `pce_rows_check_output.txt` | Written for this record: matches the 14 PCE rows on the decoded report pages against the price table |
| `record/ice_road_checks/keyword_search_all_texts_output.txt` | Written for this record: winter-haul keyword counts in every source text |
| `record/ice_road_checks/barge_ice_edges_by_component.py` and `barge_ice_edges_by_component_output.txt` | Written for the consistency check of this record: barge-to-ice edges and the ice-road nodes they meet, per ice-road component (ten edges at six nodes on the 326.0-mile Bethel-area component) |

Source documents and links. Local copies are in the harness under `cost_derivation_resources/`. The links are
as given in the earlier chapters or in `DOWNLOAD_LIST.md`; none was opened in this session.

- `ATRI-Operational-Costs-of-Trucking-07-2025.pdf`: truckingresearch.org (the chapter's link is truncated).
- `Northwest_Arctic_Borough_Noatak_Winter_Fuel_Haul_System.pdf`: no link recorded.
- `NorthSlope_CommunityWinterTrails_2020.pdf`: omb.alaska.gov/ombfiles/20_budget/DCCED/Enacted/2020proj62733.pdf
- `2026.03.01 FY2025 PCE Statistical Report by Community (Final).pdf`: akenergyauthority.org/pce
- `components of alaska fuel costs.pdf` (ISER, February 2010): https://iseralaska.org/static/legacy_publication_links/componentsoffuel3.pdf
- `cost-assessment-fordiesel-fuel-transition-in-western-and-northern-alaska-communities.pdf` (DEC and Northern
  Economics, December 2007; branch `cost-sources`): `DOWNLOAD_LIST.md` item 1 says it is likely under
  https://dec.alaska.gov/air/anpms/ultra-low-sulfur-diesel/rural-economic-summary/
- `Bethel-Terminal-Storage-Rate-Sheet.pdf` (branch `cost-sources`): no link recorded.
- `NorthSlopeBorough-Budget-Book-FY26-27-FINAL-1.pdf`: no link recorded.

Not re-confirmed for this record:

- The earlier chapter's web-sourced methods and facts: the $900 per hour convoy rate, the 2026 Anaktuvuk Pass
  haul, the Ontario, Northwest Territories and Tibbitt to Contwoyto figures, the January 2026 commercial
  heating-oil prices, the 68-mile trail length and the 62-mile Deadhorse to Nuiqsut road. None is in the
  supplied documents. Their values are carried as the chapter states them and were not restated to 332.243.
- The March 2026 Tuntutuliak quote ($13.60 per gallon, about $114,000). It comes from web search snippets
  only.
- The 2016 news snippet that suggests the Noatak system was not operating at scale.
- The verifier's statement that five web searches found no winter-haul invoice. The searches were not rerun.
- The delivery-method layer behind the note that Atqasuk is ice-road served from 2024-02-15. Only the comment
  in `friction_costs.py` was read.
- The North Slope Borough budget book as a whole. For this record it was searched by keyword only (no hit for
  ten winter-haul terms); the fact-sheet reader's statement that it holds no fuel haul line or gallons is
  carried on that basis.
- The verdict's all-in regime centres (truck about 0.007 to 0.009, sled about 0.026) and its line-haul blend
  of about 0.011. The saved script does not print them as such; they are carried as stated, and the
  restatement of 0.68% does not change them at this rounding.
- The second-round analyst's component sizes (2,536 and 305 miles). The rerun network check gives 2,692.1
  miles for the main North Slope ice component and 326.0 miles for the Bethel-area one, and this record uses
  the rerun values.
