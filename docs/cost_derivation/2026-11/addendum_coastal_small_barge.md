## Addendum 2026-11-17: Coastal small barge (lightering from a hub or a line-haul vessel to a village on salt water) (proposal; nothing applied)

This addendum records the second-round derivation and its verification for one segment. It changes nothing in
`friction_costs.py`. All 2026 figures are restated to CPI-U 332.243 (the owner's index decision of 2026-11-17,
`shared/index_basis_2026-11-17.md`). The working files were computed at 330.0; where the restatement changes a
rounded figure, the text says so. The verdict summarised here comes from one adversarial verifier
(`derive2_results.json`, key `verdicts.coastal`).

Short names used below. **ISER** is the Institute of Social and Economic Research at the University of Alaska
Anchorage; "ISER 2010" is its report "Components of Alaska Fuel Costs" and "ISER 2008" its report "Components of
Delivered Fuel Prices in Alaska". **DEC** is the Alaska Department of Environmental Conservation; "DEC 2007" is its
December 2007 cost assessment with Northern Economics. **AEA** is the Alaska Energy Authority and **PCE** its Power
Cost Equalization program, whose fiscal year 2025 report (July 2024 to June 2025) gives each utility's fuel price.
**AVEC** is the Alaska Village Electric Cooperative, one buyer for many villages. **OSRO** stands for oil spill
response organization; the "lightering guide" is Alaska OSRO's 2026 guide to tanker lightering in Western Alaska.
**BLS** is the US Bureau of Labor Statistics and **CPI-U** its consumer price index for all urban consumers. "YFC"
in passage Q8 is read as Yukon Fuel Company, which the report names elsewhere, and "MAFA" in passage Q18 is Mark A. Foster and Associates, the consultant
behind the DEC figure. A "hub" is a regional port with a tank farm (Nome, Bethel, Kotzebue); a
"line-haul vessel" is the large ocean barge or tanker that brings fuel to the region.

### Status

**Headline status for the rate as it would be applied: Provisional.** The rate is a fixed part plus a per-mile part, and that split rests on one source. The all-in level is well supported (three sources within 1.46x, of which two are bounds). Detail follows.

**All-in level per village delivery: Derived. Split into a fixed part and a per-mile part: Provisional.**

- **Level (Derived).** Three independent sources put one small-barge village delivery at 0.62 to 0.91 dollars per
  gallon, a spread ratio of 1.46 against the 3x standard, and their inputs were re-read in the source documents.
  Two qualifications apply. The verifier classes two of the three sources as upper bounds, not point estimates,
  and no tariff, contract or invoice for this leg was found. The level describes seasonal lightering in Western and
  Northern Alaska; it overstates ice-free, dock-served legs in Southeast Alaska (see "Open evidence gaps").
- **Split (Provisional).** No source gives a per-mile rate for a coastal small barge. The fixed part and the
  per-mile part rest on one source's cost figures plus an assumed tug speed and assumed stop times. The per-mile
  test has a spread ratio of 3.19 and is not a valid three-method test.
- **What the model should carry meanwhile.** Nothing is applied. The model keeps its single Barge rate of 0.0010
  dollars per gallon-mile, which happens to equal the per-mile part proposed here. The model has no slot for a fixed
  part per delivery, so a result that depends on a hub-to-village coastal leg should be reported with the all-in
  range below (0.40 to 1.21 dollars per gallon per delivery), labelled provisional, and with the note that such a
  leg is under-priced today by roughly 0.35 to 0.5 dollars per gallon.

### Result

| Item | Value |
|---|---|
| Form | Cost per gallon for one delivery = fixed part + per-mile part x one-way statute sailing miles. A pure per-mile rate is rejected. |
| Point, fixed part | 0.45 dollars per gallon per village delivery |
| Point, per-mile part | 0.0010 dollars per gallon per one-way statute sailing mile (the empty return is inside the rate) |
| Range, fixed part | 0.15 to 0.70 dollars per gallon per village delivery |
| Range, per-mile part | 0.0005 to 0.0020 dollars per gallon per one-way statute sailing mile |
| All-in at three distances | 0.61 dollars per gallon at 160 miles; 0.70 at 250 miles; 0.89 at 435 miles |
| Range, all-in per delivery | 0.40 to 1.21 dollars per gallon |
| Unit | Dollars per gallon delivered (fixed part); dollars per gallon per statute mile (per-mile part) |
| Dollar basis | 2026 dollars, CPI-U 332.243 (January to September 2026 average) |
| Effect of the restatement | The working files give the same points at CPI-U 330.0. Multiplying by 1.0068 gives 0.453 and 0.00101, which round to the same 0.45 and 0.0010. The three all-in values round the same. Only the top of the all-in range moves, from 1.20 to 1.21. |
| Source-year dollars | The two points are the verifier's judgement across sources from three different years, so they have no single source year. The anchors in their own dollars are: 0.60 dollars per gallon (range 0.40 to 0.80), 2010 dollars (ISER 2010); 0.39 dollars per gallon, November 2007 (ISER 2008, Angoon); 0.645 dollars per gallon, fiscal year 2025 nominal (14 Norton Sound villages over Nome). |

**Marine-freight-index sensitivity.** If the figures anchored on ISER 2010 are inflated with the BLS coastal and
Great Lakes freight index (factor 1.749 from 2010) instead of CPI-U, the fixed part becomes about 0.52 dollars per
gallon, the per-mile part about 0.00116 dollars per gallon per mile, and the all-in cost about 0.81 dollars per
gallon at 250 miles. That is about 15% above the CPI-U 332.243 figures (the working file says 16%, measured against
the 330.0 basis; the index-based values themselves do not change). Whether Alaska tug-and-barge trade is inside that
national index is not established, so this is a sensitivity and never the base case.

### Methods and convergence

All values are in 2026 dollars at CPI-U 332.243. "Per gallon" means dollars per gallon for one delivery. Page
numbers are PDF pages of the local file, with the printed page in brackets where it differs. Passages marked Q are
quoted in full under "Quoted passages".

| Method | Counted as independent? | Value (2026 dollars) | Source documents with page | How it was checked | Kept or rejected and why |
|---|---|---|---|---|---|
| ISER 2010 small-barge cost build-up (first-round "barge-days" method; second-round cross-check) | Yes. Independent source 1, and the only point estimate. | 0.91 per gallon (stated range 0.61 to 1.22). Near a terminal: 0.59 to 0.69 per gallon. | `components of alaska fuel costs.pdf`, pages 18 to 20 (Q1 to Q7), caveat page 12 (Q9) | Tables 1 to 3 re-read in the text file; arithmetic reproduced (1,350,000 dollars over 135 days is 10,000 dollars per day; 15 days over 250,000 gallons is 0.60 dollars per gallon). | Kept. It is a cost at a 10% return, not a price, and the source calls its numbers recollections. |
| First-round operations build-up (tug and 275,000-gallon barge voyage model) | No. It uses the same ISER cost inputs, so it counts inside source 1. | Per-mile part 0.00101 per gallon per mile (0.00067 to 0.00165). Fixed part 0.27 per gallon for one full-load village, 0.47 for a three-call voyage. | `derive/village_buildup/buildup.py`; ISER 2010 pages 18 to 19 | The verifier recomputed the central case by hand. Speed, weather allowance and stop times have no source. | Kept only as part of the ISER family. It supplies the 0.0010 per-mile point. |
| Fiscal year 2025 utility price premium over the hub (first round, 29 villages; second round, 14 Norton Sound villages) | Yes. Independent source 2, as a bound only. Both rounds use the same report and count once. | Norton Sound over Nome: mean 0.67 per gallon. Ten AVEC villages: 0.91. Four other utilities: 0.04. First round, 29 villages around four hubs: 1.01 (0.78 to 1.24) on that round's mid-2024-to-2025 dollar basis. | `2026.03.01 FY2025 PCE Statistical Report by Community (Final).pdf`, as decoded in `shared/pce_prices_with_distances.csv`; `2009-Alaska Energy - A First Step Toward Energy Independence.pdf`, page 234 (Q14) | The verifier's fit script was re-run for this record and reproduces the working figures. Straight-line miles were recomputed from the network nodes. | Kept as a gross upper bound on the whole hub-to-village increment. The slope is rejected: buyer identity, not distance, explains the premium. |
| Angoon over Ketchikan retail difference, November 2007 | Yes. Independent source 3 (different survey, year and region), as a bound only. | 0.62 per gallon over 185 straight-line miles (235 to 266 network water miles). | `Components of Delivered Fuel Prices in Alaska.pdf`, page 66 (printed 60) (Q13) | Quote confirmed, including the following sentence that the analyst had cut. Distance recomputed (184.8 straight-line miles). | Kept as an upper bound on transport. It is a retail difference on an ice-free route with a larger class of barge. |
| State fuel contract delivery charges (ISER 2008 Tables 10 and 15) | No. | No small-barge value. Context only: Klawock minus Ketchikan 0.12 per gallon. | Same file, page 33 (printed 27) | Table confirmed; the fit was re-run by the verifier. | Rejected. These are bundled bids to a hub or port tank farm with no stated supply point. |
| Volume differentials for barge delivery (DEC 2007 Table 8) | No. | Structure only: plus 0.08, 0.16, 0.24 and 0.40 per gallon for the four smaller parcel classes. | `cost-assessment-fordiesel-fuel-transition-in-western-and-northern-alaska-communities.pdf`, page 39 (printed 23) | Table confirmed in the text file. | Rejected as a cost per delivery. It is a stepped price schedule. It shows the Angoon bound overstates large-parcel transport by about 0.24 per gallon. |
| River invoice rate (DEC 2007), the earlier chapter's second anchor | Independent, but it measures a different segment. Bound only. | 0.0112 per gallon per map mile; 1.35 per gallon at 120 map miles. By the coastal freight index: 0.0138 per gallon per map mile. | Same DEC file, page 37 (printed 21) (Q18) | Quote and footnote confirmed. | Kept as an upper bound only. Rejected as a coastal rate: it is a river figure with no fixed part. |
| Ice-free Southeast hub-to-town differences (found during verification) | Not counted. | Sitka over Ketchikan: at least 0.14 per gallon. Klawock over Ketchikan contract charge: 0.12 per gallon. | `components of alaska fuel costs.pdf`, pages 33 and 39 (Q19, Q20); ISER 2008 Table 10 | Quotes confirmed. | Kept as evidence of a second, cheaper regime. It shows the figure does not fit dock-served Southeast towns. |

**Spread ratios against the 3x standard.**

- **All-in level.** ISER 0.91, Norton Sound premium 0.67 and Angoon 0.62 dollars per gallon give a spread ratio of
  1.46 and a geometric mean of 0.72 dollars per gallon. This meets the standard. Using the 29-village premium (1.00
  dollars per gallon on the calendar-2025 basis the verifier used) in place of Norton Sound gives 1.60. Adding the
  river rate at 120 miles (1.35 dollars per gallon), which is not the same quantity, gives 2.15.
- **Fixed part.** ISER near-terminal cost 0.59, the second-round intercept 0.40 and Angoon less mileage 0.39 dollars
  per gallon give a spread ratio of 1.51 and a geometric mean of 0.45 dollars per gallon. The last two depend on an
  assumed per-mile part, so this test is weaker than it looks.
- **Per-mile part.** Day-rate arithmetic at 7 knots 0.00063, the operations build-up 0.00101 and the price slope
  0.0020 dollars per gallon per mile give a spread ratio of 3.19. The first two share one source and the third is
  statistically zero. This does not meet the standard.

In plain terms: the size of the bill for one delivery is established; how much of it depends on distance is not.

**Quoted passages** (confirmed in `pdf_text/` on 2026-11-17).

- Q1. ISER 2010, page 18: "A new set (tug and barge) for coastal operations costs about $6 million. That set could
  deliver between 2.5 million to 3.5 million gallons over 120 to 135 days, depending where it is put into service."
- Q2. ISER 2010, page 19: "A costal set of equipment would have direct operating costs of about $750,000 per year."
  and "fuel makes up $100,000 of annual operating costs (approximately 40,000 gallons of fuel at $2.50 per gallon)."
- Q3. ISER 2010, page 19, Table 1: "Capital Costs $600,000; Operating Costs $750,000; Total Costs $1,350,000; Gallons
  Delivered 3,000,000; Cost per Gallon $0.45", with "It assumes a 10% return on capital investment."
- Q4. ISER 2010, page 19: "Delivering three million gallons of fuel with one tug and barge set would be considered
  excellent utilization and can only be accomplished if the equipment is making shorter trips close to a terminal."
- Q5. ISER 2010, page 19: "The example given in Table 2 assumes the 275,000 gallon barge is delivering 250,000
  gallons to communities that require a 15-day round trip per delivery."
- Q6. ISER 2010, page 20, Table 2: "Annual Barge Cost $1,350,000; Operating Days 135; Daily Cost $10,000; Trip Length
  (days) 15; Cost per Trip $150,000; Gallons per Trip 250,000; Cost per Gallon $0.60".
- Q7. ISER 2010, page 20: "Based on the best information available, the estimated range of costs for Western Alaska
  small barge deliveries is $0.40-$0.80 per gallon for most locations."
- Q8. ISER 2010, page 19, footnote 18: "Analysis conducted at YFC showed small boat operations had a fixed costs of
  70% and variable cost of 30%," (the footnote runs off the page in the text file).
- Q9. ISER 2010, page 12: "The numbers used in this report reflect the best estimates and memories of historical
  costs but should not be considered exact without confirming data with current fuel distribution companies."
- Q10. ISER 2010, page 18: "All risk of a fuel spill is borne by the fuel distribution company until the fuel passes
  through the customer's header pipe upon delivery."
- Q11. ISER 2010, pages 22 to 23: "Missing header or pipelines and docking issues are not uncommon. This could
  represent a $0.10-0.15 per gallon difference in the price the fuel distribution company charges a community."
  Page 7: "These costs can easily increase by $0.20 per gallon for docking and fuel off-loading deficiencies".
- Q12. ISER 2010, page 22: "Communities that receive fuel even a few weeks apart could have a cost difference of
  $0.50/gallon."
- Q13. ISER 2008, page 66 (printed 60): "In November 2007, heating fuel retailed for $3.40 per gallon in Ketchikan
  and $3.79 per gallon in Angoon. The $0.39 difference in price consisted primarily of the cost of transporting fuel
  from the tank farms in Ketchikan in small barges to Angoon. Lesser but significant costs are attributable to an
  increased proportion of overhead costs associated with selling smaller amounts of fuel."
- Q14. 2009 Alaska Energy report, page 234 (left column): "The fuel cost reported to PCE seems to be the price paid
  per gallon for that entire drop of fuel, and so it averages the cost of transportation over all the villages
  served by that particular shipment, regardless of the actual transportation cost calculated by the shipper."
- Q15. Corps of Engineers Nome study, page 196 (printed 168): "If regional delivery barges had to pull into the Port
  of Nome for fuel shipments, instead of receiving it offshore, this could increase their travel time as well".
- Q16. Alaska OSRO lightering guide, page 22: "using 'temporary distribution hubs' (stationary tank vessels) and
  barges delivering the fuel from the 'temporary distribution hub' to the shoreside facility."
- Q17. ISER 2008, page 71 (printed 65): "Unalakleet's fuel is usually delivered from Nome." and "The fuel is pumped
  from Nome tank farms into lightering barges for delivery to Unalakleet."
- Q18. DEC 2007, page 37 (printed 21): "In 2007, the cost for delivery via river fuel barge is about $0.007 per
  gallon per map mile of transport from the fuel hub." Footnote 6: "MAFA Analysis of Crowley Marine Services
  invoices. To simplify the analysis, a map-mile is adopted rather than a river-mile."
- Q19. ISER 2010, page 39: "Before 2005, fuel prices were more stable and Sitka appeared to be paying an average of
  $0.08 more per gallon. This is the price difference that would reasonably be expected if prices were based
  primarily on the cost of distribution."
- Q20. ISER 2010, page 33: "Such smaller barges have a capacity of one million gallons of fuel."
- Q21. Port of Nome Tariff 16.6, page 25 (printed 22): "Inbound only ... $0.05 per gal; Outbound only ... $0.032 per
  gal; Over-side only ... $0.017 per gal".

### Derived versus assumed

One row per input that the recommended figure rests on. Dollar values are dollars per gallon unless the row gives
another unit. "Analyst 1a" is the first-round barge-days analyst, "analyst 1b" the first-round operations build-up
analyst, "analyst 2" the second-round analyst, and "verifier" the author of `verdicts.coastal`.

| Input | Value | Type | Reference | What changes if it is wrong |
|---|---|---|---|---|
| Capital cost of a coastal tug-and-barge set | 6 million dollars | Quoted | ISER 2010, page 18 (Q1) | The whole ISER level scales with it; the source says vessel prices have risen. |
| Return on capital in the capital charge | 10%, giving 600,000 dollars per year | Quoted (the source's own assumption) | ISER 2010, page 19 (Q3) | A different return changes the capital charge and the 0.60 with it. |
| Annual operating cost of the set | 750,000 dollars, of which tug fuel 100,000 dollars | Quoted | ISER 2010, page 19 (Q2) | The operating-cost part of the ISER level scales with it. |
| Operating season | 135 days (source range 120 to 135 days) | Quoted | ISER 2010, page 20, Table 2 (Q6); page 18 (Q1) | A 105-day season raises the 15-day trip to 0.77 (1.18 in 2026 dollars). |
| Trip length for a typical delivery | 15-day round trip | Quoted | ISER 2010, pages 19 to 20 (Q5, Q6) | Each day more or less is 0.04 in 2010 dollars. |
| Gallons delivered per trip | 250,000 gallons from a 275,000-gallon barge | Quoted | ISER 2010, page 19 (Q5) | Cost per gallon scales as one over the parcel for a dedicated trip. |
| Typical cost of one delivery, 2010 dollars | 0.60 (range 0.40 to 0.80) | Quoted | ISER 2010, page 20, Table 2 and text (Q6, Q7) | It is the only point estimate; the level moves with it. |
| Same in 2026 dollars | 0.91 (range 0.61 to 1.22) | Computed | 0.60, 0.40 and 0.80 times 1.5237 | Follows the two rows above and the dollar year. |
| Near-terminal cost at best utilisation | 0.45 at 3.0 million gallons (0.69 in 2026 dollars); 0.386 at 3.5 million gallons (0.59 in 2026 dollars) | Quoted (0.45) and Computed (1,350,000 dollars over 3,500,000 gallons) | ISER 2010, page 19, Table 1 and text (Q3, Q4); page 18 (Q1) | This is the anchor for the top of the fixed-part range. |
| Reliability of the ISER numbers | "best estimates and memories of historical costs" | Quoted | ISER 2010, page 12 (Q9) | The source's inputs are recollections of two former carrier executives, not records. |
| Dollar year of the ISER 2010 figures | 2010 | Assumed (project convention; the report is dated February 2010 and states no dollar year) | Earlier chapter, verification addendum of 2026-07-15 | If the figures are 2009 dollars, every ISER-based value rises 1.6%. |
| Index used to bring dollars to 2026 | CPI-U, 2026 value 332.243 | Owner decision, 2026-11-17 | `shared/index_basis_2026-11-17.md` | By the coastal freight index the ISER-based values are about 15% higher. |
| Fiscal year 2025 utility fuel prices, Nome and 14 villages | Nome 3.59; villages 3.08 to 5.04 | Measured | `shared/pce_prices_with_distances.csv` (the price table decoded from the PCE report) | All 15 rows were re-read for this record. A decoding error in a village price would move the premium. |
| Mean premium of the 14 villages over Nome | 0.645 nominal; 0.67 in 2026 dollars | Computed | Mean village price 4.235 less 3.59; times 1.0320 | Follows the row above. |
| Premium by buyer | Ten AVEC villages 0.886 nominal (0.91); four other utilities 0.043 nominal (0.04) | Computed | Same table, utility column; `verify2/coastal/refit.py` | This is the evidence that the premium is not a freight measure. |
| Dollar year of the fiscal year 2025 prices | Calendar 2025 (factor 1.0320) | Assumed (analyst 2 and verifier) | Fiscal year 2025 runs July 2024 to June 2025; the first round used the mid-point of 2024 and 2025 | The mid-point basis raises the premium by 1.3%. |
| Nome as the supply point for the 14 villages | Straight-line miles from Nome | Assumed (analyst 2) | Against it: Q15, Q16 (delivery barges load from tankers offshore). For it, for one village in 2007: Q17 | The distance variable is partly wrong, so the fitted slope and intercept carry little weight. |
| Reading the price premium as an upper bound, not a point | Bound only | Assumed (verifier's judgement between two readings) | Q12, Q14; two villages are below Nome | If it were a point estimate, the level would have two point estimates in place of one. |
| Using the Norton Sound premium (0.67) in the level test and not the 29-village premium (1.00) | 0.67 | Assumed (verifier) | `verdicts.coastal`, convergence | With 1.00 the spread ratio is 1.60; the test still passes. |
| Angoon over Ketchikan retail difference | 0.39, November 2007 | Quoted | ISER 2008, page 66 (printed 60) (Q13) | It bounds the fixed part from above for ice-free legs. |
| Same in 2026 dollars | 0.62 | Computed | 0.39 times 1.6024 (2007 annual average, used for a November price) | A November 2007 monthly index would differ slightly. |
| Reading the Angoon difference as an upper bound on transport | Bound only | Assumed (verifier), supported by the second sentence of Q13 | ISER 2008, page 66 (printed 60) | If it were all transport, 0.0034 per gallon per straight-line mile. |
| Ketchikan to Angoon distance | 184.8 straight-line miles; 235 to 266 network water miles | Measured | Network nodes and edges; `verify2/coastal/dist_check.json` | Sets how much of the 0.62 the per-mile part uses up, and so the fixed part that Angoon allows. |
| Angoon parcel size | 88,000 gallons per year in 8 deliveries | Quoted | ISER 2008, page 51 (printed 45): "typically there are eight deliveries per year"; Table 15, page 60 (printed 54) | Small parcels (about 11,000 gallons) make Angoon overstate large-parcel transport by about 0.24. |
| Tug speed | 7 knots (analyst 1a); 7.5 statute miles per hour (analyst 1b) | Assumed | No supplied document states a speed. One search snippet gives about 10 knots. | The per-mile part from day-rate arithmetic is 0.00063 at 7 knots, 0.00044 at 10 knots and 0.00074 at 6 knots. |
| Weather allowance, hub days, days per village call, pumping rate, tug fuel burn | 35%; 2.5 days; 1.75 days; 300 gallons per minute; 40 gallons per hour | Assumed (analyst 1b; set so that a season matches the ISER season throughput) | `derive/village_buildup/buildup.py` | These set the per-mile point of 0.0010; the build-up's own range is 0.00067 to 0.00165. |
| Days per load that do not depend on distance | 10.5 days (9.6 to 11.25) | Computed from Quoted throughput, plus an Assumed tug fuel burn of 45 gallons per hour | ISER 2010, pages 18 to 19 (Q1, Q3); `derive/village_iser/calc.py` | Fewer fixed days lower the fixed part and raise the per-mile part. |
| Per-mile point | 0.0010 dollars per gallon per one-way statute sailing mile | Assumed (verifier's choice of the operations build-up's central value) | `verdicts.coastal`; between 0.00063 (day rate at 7 knots) and 0.0020 (price slope) | The all-in cost at long distances moves with it; at short distances the fixed part dominates. |
| Second-round intercept used in the fixed-part test | 0.40, with a per-mile part of 0.0020 | Assumed (analyst 2 chose 0.0020 inside a fitted interval that includes zero) | `derive2/coastal_published/pool.py` | With a per-mile part of 0.0005 the intercept is 0.60; with 0.0050 it is 0.05. |
| Fixed-part point | 0.45 dollars per gallon per delivery | Assumed (verifier's judgement between two regimes) | Western and Northern lightering alone supports 0.50 to 0.55; ice-free Southeast supports at most 0.35 at Angoon and about 0.10 to 0.15 at dock-served towns | A regional figure would be higher in the west and north and much lower in Southeast. |
| Ranges | Fixed 0.15 to 0.70; per-mile 0.0005 to 0.0020; all-in 0.40 to 1.21 | Assumed (verifier), anchored on the ISER stated range and the Southeast evidence | `verdicts.coastal` | These are judgement ranges, not confidence intervals. |
| Sitka over Ketchikan difference, used for the low regime | 0.08, treated as 2005 dollars (at least 0.14 in 2026 dollars) | Quoted (value), Assumed (dollar year; the prices are before 2005) | ISER 2010, page 39 (Q19) | An earlier dollar year raises the 2026 value, so 0.14 is a floor. |
| Klawock minus Ketchikan contract charge, used for the low regime | 0.07, treated as 2005 dollars (0.12 in 2026 dollars) | Quoted (0.20 and 0.13), Assumed (dollar year; 2003 and 2006 contracts averaged) | ISER 2008, page 33 (printed 27), Table 10 | Small either way; it only supports the low end of the range. |
| River invoice rate, used as an upper bound | 0.007 dollars per gallon per map mile in 2007 (0.0112 in 2026 dollars) | Quoted, Computed (times 1.6024) | DEC 2007, page 37 (printed 21) (Q18) | It is a bound; the recommended values sit well below it. |
| Distance the per-mile part multiplies in the model | Network water miles stand in for sailing miles | Assumed (if the proposal is ever applied) | Measured against it: network miles from Nome are 1.0 to 4.6 times straight-line (median about 2.3); six of 14 villages have no water route (`verify2/coastal/dist_check.json`) | The per-mile part is overstated by roughly 1.5 times on the Seward Peninsula. |

**Which assumptions carry the most weight.** The level rests on one build-up from recollection (ISER 2010) and on
the verifier's reading of two price differences as upper bounds; if the ISER dollar year or the index is wrong the
level moves by 1.6% to about 15%, which is small against the range. The split is where assumptions dominate: the tug speed,
the stop times and the choice of 0.45 dollars per gallon between a Western regime (0.50 to 0.55) and a Southeast
regime (0.35 or less) are all judgement, and none comes from a document. The choice of a single statewide fixed part
is the largest of these, because it overcharges dock-served Southeast towns about fivefold.

### What the figure includes and excludes

**Inside the fixed part plus the per-mile part** (the scope of ISER 2010 pages 18 to 19):

- The tug-and-barge set: capital at a 10% return, crew, tug fuel, insurance and regulatory compliance.
- The small barge's time loading alongside the line-haul vessel or at a hub dock.
- Sailing out loaded and back empty, waits for tide and weather, idle days in the season, and the inefficiency of
  multi-stop voyages.
- Discharge through the vessel's hose up to the customer's marine header (Q10).

**Not inside:**

- Ocean line-haul, including the line-haul vessel's own time during the transfer.
- Port wharfage and hub tank-farm handling.
- Village storage and retail.
- Distributor administration (0.08 to 0.15 dollars per gallon) and working capital (0.04 dollars per gallon).

**Fees by event that touch this segment** (dollars per gallon; tariff figures are 2026 actuals and are not inflated):

| Event | Bill | Range | Who carries it today |
|---|---|---|---|
| Line-haul vessel to small barge at anchor | 0 | 0 to 0.02 | The small-barge side is in the fixed part; the line-haul side belongs to the line-haul rate. |
| Over-side transfer at the Nome dock | 0.017 | Tariff (Q21) | Nothing |
| Fuel through the Nome tank farm (wharfage in 0.05 plus out 0.032) | 0.082 | Tariff (Q21) | Nothing |
| Hub shore labour for a line-haul offload | 0.06 to 0.09 | ISER 2010, page 18 | Nothing |
| Third-party terminal fee, where it applies | 0.11 to 0.23 | ISER 2010, page 18 | Nothing |
| Small barge to village marine header | 0 | 0 | Vessel-side discharge is in the fixed part. |
| Village with no header, or a docking deficiency | 0.19 | 0.15 to 0.23, up to 0.30 (Q11) | Nothing. Bill it only where known; otherwise leave it in the range. |

The tank-farm rows apply only to gallons that actually pass through hub storage. Most village gallons are loaded
offshore and pay none of them (Q15, Q16), although ISER 2008 records Unalakleet as usually supplied through the Nome
tank farms in 2007 (Q17).

**Where these events are billed, so that none is billed twice.** The hub rows above are the same events that the
transfer-fee addendum prices: the inbound wharfage and the shore labour are its hub discharge fee (0.12 dollars per
gallon at a distributor's own terminal, range 0.05 to 0.20), the outbound and over-side charges are its hub reload
(0.045 dollars per gallon, range 0.017 to 0.12), and the third-party terminal fee is its third-party sensitivity.
They are billed there, once, and not again from this table. This table bills nothing at a village with a marine
header. The transfer-fee addendum proposes 0.046 dollars per gallon on the village crossing as a stand-in for
average hub terminal use, and its first overlap rule sets that fee to zero where a barge rate keeps a fixed part
fitted from delivered prices. Two of the three anchors of the 0.45 fixed part (the second-round price intercept and
the Angoon retail difference) come from delivered prices, so under that rule the village-landing fee is zero
wherever this fixed part is applied, and the 0.046 is for a barge rate with no fixed part. The verifiers did not
settle this between them: this segment's verdict describes the fixed part as vessel-side cost only, which would
leave room for the 0.046. It is therefore an open item. The difference is at most 0.046 dollars per gallon, and the
two must not be added together without saying so.

**The existing 0.24 dollars per gallon barge-to-road fee.** It bills truck-rack out-loading, which is not small-barge
handling, so it does not overlap the fixed part in content. But at a village where the barge pumps straight into the
tank farm there is no rack. The fixed part plus 0.24 plus mileage is about 0.94 dollars per gallon at 250 miles,
which exceeds the gross Norton Sound premium (0.67) and reaches the AVEC premium (0.91). The verifier's view is that
at such villages the fixed part should replace the 0.24 and not be added to it.

### Compared with the applied value and the earlier chapter

**Applied today** (`source_scripts/friction_surface/friction_costs.py`). One Barge rate of 0.0010 dollars per
gallon-mile on every waterway edge, with a documented range of 0.00023 to 0.011. There is no fixed small-barge
component. The code comment says lightering and terminal handling of about 0.8 to 1.2 dollars per gallon is
"currently smeared into this blended rate". The only fee at a village landing is 0.24 dollars per gallon for
truck-rack out-loading. The value 0.011 appears in the code only as the top of the Barge range and in the comment's
decomposition; it is not charged on any edge.

**Earlier chapter** (`blind_derivations/02_barge.md`, sections 4 and 7). It gave a village distribution leg of 0.91
dollars per gallon typical (0.60 to 1.21) from ISER 2010, and 0.011 dollars per gallon-mile on distribution edges
from the DEC river invoice rate, and said the two agree within 10%. It recommended not smearing.

**Effect of the new evidence.**

- **Confirms** the ISER level and the advice not to smear. The price cross-section and the Angoon difference land at
  0.62 to 0.67 dollars per gallon, inside the ISER range.
- **Confirms the per-mile number by coincidence.** The proposed per-mile part (0.0010) equals the applied blended
  rate, so the rate on these edges need not change. The applied rate was derived as a whole-path blend, not as a
  small-barge figure.
- **Tightens the fixed component downwards.** The comment's 0.8 to 1.2 dollars per gallon becomes about 0.45 dollars
  per gallon plus mileage, because 0.91 is the ISER total for a 15-day trip and not an amount free of distance.
- **Overturns 0.011 dollars per gallon-mile for coastal legs.** It is a river invoice figure with no fixed part. The
  10% agreement with ISER holds only at 82 map miles. Applied to Norton Sound distances it gives 0.67 to 2.2 dollars
  per gallon (0.66 at the 330.0 basis), above the ISER top for the longer legs.
- **Shows a gap in today's pricing.** A hub-to-village leg of 120 to 250 miles costs 0.12 to 0.25 dollars per gallon
  in the model today, or 0.36 to 0.49 with the 0.24 fee. The evidence is 0.6 to 0.9 dollars per gallon for the
  vessel alone, so the leg is under-priced by about 0.35 to 0.5 dollars per gallon. On a whole Anchorage-to-village
  path this is masked, because the line-haul is charged 0.0010 dollars per gallon-mile against about 0.00021 in
  the ocean line-haul addendum of this record (0.00023 in the earlier chapter).

**Review status.** The overturning of 0.011 dollars per gallon-mile for coastal legs, and the view that the fixed
part should replace the 0.24 fee at villages with a direct header, come from ONE verifier and have not had a second
independent review.

### Open evidence gaps

Each item names the document type that would raise the status.

- **A tariff, contract or invoice for the leg itself (would complete the level and could make the split Derived).**
  A fuel distributor contract or bid tabulation that shows the transportation charge per village: an Alaska Village
  Electric Cooperative annual fuel bid, a school district bulk fuel bid, or Alaska Energy Authority Bulk Fuel
  Revolving Loan purchase records. A carrier rate table by village or zone would serve the same purpose.
- **Per-delivery invoices by buyer.** The price premium is ten AVEC villages at 0.91 dollars per gallon over Nome
  and four other utilities at 0.04. It cannot serve as a point estimate until invoices separate freight from the
  buyer's pooled price.
- **Vessel logs, voyage records or vessel-tracking data** giving tug speed and days per stop. No supplied source
  states either. One search snippet gives about 10 knots against the 7 knots assumed.
- **The economics appendix of the Corps of Engineers Port of Nome study** (vessel operating costs). It is not in the
  supplied PDF and would give an independent vessel-day cost.
- **A Southeast delivered-price or freight schedule** (for example a distributor's schedule for Sitka, Klawock and
  Angoon). The figure exceeds the Angoon bound by 10% to 15% and exceeds dock-served towns about fivefold, so a
  regional switch or a lower fixed part for ice-free, dock-served legs needs its own evidence.
- **Sailing distances.** Delivery barges load at lightering areas, not at Nome. Network water miles from Nome are 1.0
  to 4.6 times straight-line, and six of the 14 Norton Sound villages have no water route in the network (White
  Mountain, Golovin, Stebbins, Shaktoolik, Unalakleet, Savoonga). A table of sea distances from lightering areas
  would fix the distance the per-mile part multiplies.
- **Dollar years and the index.** The ISER 2010 dollar year (2009 or 2010), the dollar year of the Sitka difference
  (before 2005), and whether Alaska tug-and-barge trade is inside the BLS coastal freight index. The CPI-U series is
  a mirror; the BLS download (series CUUR0000SA0) should replace it.

**Not re-confirmed for this record.**

- The tug speeds (7 knots assumed; about 10 knots from a search snippet) appear in no supplied document.
- The first-round regressions (29 villages, the regional fits) and the first-round operations build-up were read from
  the working files and not re-run. The verifier also read, and did not re-run, the first-round regressions.
- The fiscal year 2025 prices were confirmed against the project's decoded table, not against the pages of the PCE
  report itself.
- Angoon's 88,000 gallons per year: the verifier did not re-check it. For this record the eight deliveries were
  confirmed in the text (ISER 2008, page 51, printed 45), and "8" and "88,000" appear in the Angoon column position
  of Table 15 in the text layer (page 60, printed 54). Column alignment in that text layer is not exact.

### Working files

All under `harness: blind_derivations/working_2026-11-17/`.

- `derive2_results.json`: `verdicts.coastal` (the verdict) and `derivations["coastal-contract-and-dec"]` (the
  second-round blind derivation).
- `blind_results.json`: first-round derivations `village-iser-bargedays`, `village-revealed-prices` and
  `village-operations-buildup`.
- `derive2/coastal_published/`: `dist.py`, `dist2.py`, `dist_table.json`, `fit_t10.py`, `fit_pce.py`, `pool.py`
  (second-round distances and fits).
- `verify2/coastal/`: `dist_check.py`, `dist_check.json`, `refit.py` (the verifier's distance check and refit;
  `refit.py` was re-run read-only for this record and reproduces the working figures at the 330.0 basis).
- `derive/village_iser/calc.py`; `derive/village_buildup/` (`buildup.py`, `buildup_results.json`, `run_output.txt`);
  `derive/village_revealed/` (`build.py`, `fit.py`, `extra.py`, `bands.py`, `village_deltas.csv`,
  `fits_by_region.csv`, `results.txt`).
- `shared/pce_prices_with_distances.csv`, `shared/build_distances.py`, `shared/inflation_factors.md`,
  `shared/index_basis_2026-11-17.md`, `shared/cpi/cpiai_datahub_mirror.csv`.
- `extracts/iser_2008.md`, `extracts/dec_2007.md`, `extracts/bering_strait_lightering.md`, `extracts/tariffs.md`,
  `extracts/usace_nome_2019.md`, `extracts/aea_2015_2009.md`; `work/iser/iser_extracts.md`.
- `pdf_text/` (full text used to confirm every quote above).

**Local documents and public links.** Local files are in the harness under `cost_derivation_resources/`. The links
are those in `DOWNLOAD_LIST.md` or the earlier chapter; they were not opened from this session.

| Document | Local file | Branch | Link |
|---|---|---|---|
| ISER, Components of Alaska Fuel Costs (February 2010) | `components of alaska fuel costs.pdf` | main | None recorded |
| ISER, Components of Delivered Fuel Prices in Alaska (June 2008) | `Components of Delivered Fuel Prices in Alaska.pdf` | cost-sources | https://scholarworks.alaska.edu/cgi/viewcontent.cgi?article=1348&context=uaa_iser_reports |
| DEC and Northern Economics, Cost Assessment for Diesel Fuel Transition (December 2007) | `cost-assessment-fordiesel-fuel-transition-in-western-and-northern-alaska-communities.pdf` | cost-sources | https://dec.alaska.gov/air/anpms/ultra-low-sulfur-diesel/rural-economic-summary/ (the earlier chapter gives dec.alaska.gov/media/8915/ulsd-cost-rpt-1207.pdf) |
| AEA, PCE Statistical Report by Community, fiscal year 2025 | `2026.03.01 FY2025 PCE Statistical Report by Community (Final).pdf` | main | None recorded |
| Alaska Energy: A First Step Toward Energy Independence (2009) | `2009-Alaska Energy - A First Step Toward Energy Independence.pdf` | cost-sources | None recorded |
| Alaska OSRO, Western Alaska Tanker Lightering Best Practices Guide (2026) | `Alaska-OSRO-2026-Western-Alaska-Tanker-Lightering-Best-Practices-Guide-1.pdf` | cost-sources | https://alaskaosro.org/wp-content/uploads/2026-Western-Alaska-Tanker-Lightering-Best-Practices-Guide-1.pdf |
| Corps of Engineers, Port of Nome Modification draft report (December 2019) | `DraftPortofNomeModificationIFREA31Dec2019.pdf` | cost-sources | https://www.poa.usace.army.mil/Portals/34/docs/civilworks/publicreview/portofnome/DraftPortofNomeModificationIFREA31Dec2019.pdf |
| Port of Nome Tariff 16.6 (12 March 2026) | `PON Tariff No 16.6 - 03.12.26 Final.pdf` | cost-sources | None recorded (City of Nome, Port of Nome tariff page) |
| BLS coastal and Great Lakes freight index | `PCU483113483113.csv` | cost-sources | https://fred.stlouisfed.org/series/PCU483113483113 |
| CPI-U series (mirror) | `shared/cpi/cpiai_datahub_mirror.csv` (scratch folder) | not in the harness | https://github.com/datasets/cpi-us |
