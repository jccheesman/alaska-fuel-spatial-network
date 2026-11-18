## Addendum 2026-11-17: River barge (shallow-draft tug and fuel barge from a river hub to a river village) (proposal; nothing applied)

Segment: fuel carried by a shallow-draft tug and barge from a river hub to a village on the same river system. The
three cases are the Tanana and Yukon from Nenana, the Kuskokwim from Bethel and the Kobuk from Kotzebue. Nothing in
this addendum has been applied to `friction_costs.py`. All 2026 figures are in 2026 dollars at CPI-U 332.243 (the
owner's index decision of 2026-11-17, `shared/index_basis_2026-11-17.md`). The working files used 330.0; every
inflated figure below was recomputed from its source-year value, and the text says where a rounded figure moved. The
verdict summarised here comes from ONE adversarial verifier (`derive2_results.json`, key `verdicts.river`) and has
not had a second independent review.

Terms used below. A **channel mile** is a statute mile measured along the river in the project network (waterway
edges only). A **map mile** is the unit of the DEC report; it is read here as a straight-line statute mile. **DEC**
is the Alaska Department of Environmental Conservation, **ISER** the Institute of Social and Economic Research at
the University of Alaska Anchorage, **AEA** the Alaska Energy Authority, **PCE** the Power Cost Equalization
program, **AVEC** the Alaska Village Electric Cooperative (one buyer for many villages) and **MAFA** Mark A. Foster
and Associates (the consultant behind the DEC figure). **BLS** is the US Bureau of Labor Statistics and **CPI-U**
its consumer price index for all urban consumers. In passage Q2, "ULSD" is ultra-low-sulfur diesel and "cwt" is a
hundredweight (100 pounds). Page numbers are PDF pages of the local file, with the printed
page in brackets where it differs.

### Status

**Provisional (every part).** The evidence is real but the methods agree on a total at one short distance and not
on the form of the cost, which is the second case of "Provisional" in `CONVENTIONS.md`.

- **Total for a short haul: Provisional, and the strongest part.** Three independent methods put one delivery to
  Tanana (164 channel miles from Nenana) at 0.61, 1.10 and 0.63 dollars per gallon, a spread ratio of 1.8 against
  the 3x standard. This does not make the figure Derived, for three reasons: the agreement holds at one distance
  only (the same comparison per channel mile is 2.7 at 280 miles and 3.1 at 364 miles); it widens to 3.2 to 3.5
  when the fourth independent method is added; and the model needs a rate, not a total at one place.
- **Per-mile part: Provisional.** Three independent methods give 0.0044, 0.0011 and 0.0014 dollars per gallon per
  channel mile, a spread ratio of 3.9. This fails the 3x standard.
- **Fixed part per delivery: Provisional.** It is not identified. The readings run from zero (contracts) to 0.82
  dollars per gallon (one reading of the ISER tables).
- **What the model should carry meanwhile.** Nothing is applied. The code keeps its single Barge rate of 0.0010
  dollars per gallon-mile on every waterway edge, which lies within 10% of one per-mile method and about 26% below
  another. A result that depends on a river leg should be reported with the provisional two-part form and its
  ranges (table below), labelled provisional, and not with a point alone. On routes that start at Nenana the model
  already bills two barge-to-road fees of 0.24 dollars per gallon, which together are close to the provisional
  fixed part; on routes that enter a river from salt water it bills one, so those legs carry about 0.26 dollars per
  gallon less fixed cost than this evidence suggests.

### Result

| Item | Value |
|---|---|
| Form | Cost per gallon for one river delivery = fixed part + per-mile part x one-way channel miles. A pure per-mile rate is rejected. |
| Point, fixed part | 0.50 dollars per gallon, once per river delivery (provisional) |
| Point, per-mile part | 0.0013 dollars per gallon per channel mile (provisional; the empty return is inside the rate) |
| Range, fixed part | 0.20 to 0.80 dollars per gallon per river delivery |
| Range, per-mile part | 0.0009 to 0.0044 dollars per gallon per channel mile. The top end is the contract slope; it holds only for hauls up to about 360 channel miles and only with no fixed part added. For hauls over 300 miles the upper limit from delivered prices is 0.0026. |
| Implied total at four distances | 0.71 dollars per gallon at 164 channel miles; 0.86 at 280; 0.97 at 364; 1.53 at 794 |
| Implied total, low and high cases | Low 0.35 to 0.91 dollars per gallon; high 1.13 to 2.39 dollars per gallon, over the same four distances |
| Unit | Dollars per gallon delivered (fixed part); dollars per gallon per statute channel mile of the project network (per-mile part) |
| Dollar basis | 2026 dollars, CPI-U 332.243 (January to September 2026 average) |
| Effect of the restatement | The verdict gives both points at CPI-U 330.0. Multiplying by 1.0068 gives 0.503 and 0.00131, which round to the same 0.50 and 0.0013, so the implied totals do not change. One rounded figure moves: the top of the per-mile range, the contract slope, is 0.00435 at 332.243 and rounds to 0.0044 (the working files give 0.0043). |
| Source-year dollars | The two points are the verifier's judgement across sources of four different years, so they have no single source year. The anchors in their own dollars are: contract slope 0.00256 dollars per gallon per channel mile (2003 and 2006 contracts averaged, treated as 2005 dollars); DEC invoice rate 0.007 dollars per gallon per map mile (2007 dollars); ISER build 0.13 dollars per gallon per voyage plus 0.00084 dollars per gallon per channel mile, and ISER's flat 0.77 dollars per gallon for a 15-day trip (2010 dollars); delivered-price slope 0.0013 dollars per gallon per channel mile (fiscal year 2025 dollars). |

**Marine-freight-index sensitivity.** If the BLS inland water freight index replaced CPI-U, the 2010-dollar sources
would fall by about 7% and the 2005-dollar source would rise by about 20% (the 2007-dollar source by about 3.5%).
The per-mile point would then lie between about 0.0012 and 0.0016 dollars per gallon per channel mile. The working
file states the same result as minus 7% to plus 19.5%, measured against a 332.8 basis; against 332.243 it is minus
6.9% to plus 19.7%. The verdict gives no index sensitivity for the fixed part. This is a sensitivity and never the
base case.

### Methods and convergence

All values are in 2026 dollars at CPI-U 332.243. "Per gallon" means dollars per gallon for one delivery. Passages
marked Q are quoted in full under "Quoted passages".

| Method | Counted as independent? | Value (2026 dollars) | Source documents with page | How it was checked | Kept or rejected and why |
|---|---|---|---|---|---|
| State contract delivery charges for Tanana, Ruby and Koyukuk, fitted against channel miles from Nenana (second round) | Yes. Independent method 1. | Slope 0.0044 per gallon per channel mile (0.00435; 0.0042 if the charges are 2006 dollars). Totals net of the truck leg to Nenana: 0.61, 1.12 and 1.48 per gallon at 164, 280 and 364 channel miles. | `Components of Delivered Fuel Prices in Alaska.pdf`, page 33 (printed 27), Table 10 (Q3); page 34 (printed 28) (Q4) | Table re-read in the text file. The verifier measured its own distances (163.8, 279.8, 363.4 miles) and re-fitted; its script was re-run for this record and reproduces. | Kept as a point estimate, valid only between 164 and 364 channel miles. Three points, so the intercept is not distinguishable from zero. |
| DEC 2007 invoice rate per map mile, with its hundredweight cross-check (second round) | Yes. Independent method 2, but usable only as a total near 100 map miles. | 0.0112 per gallon per map mile as published. Per channel mile on a main-stem river: 0.0075 (0.0067 to 0.0080). Total 1.12 per gallon at DEC's own example of 100 map miles; 1.10 at Tanana (98.1 map miles). | `cost-assessment-fordiesel-fuel-transition-in-western-and-northern-alaska-communities.pdf`, page 37 (printed 21) (Q1); page 105 (printed 89) (Q2); page 19 (printed 3) (Q5) | Sentence, footnotes and the cross-check inputs confirmed in the text file; arithmetic reproduced. | Kept as a bound, and as a point only for the total near 100 map miles. Rejected as a per-mile rate: it is an all-in charge divided by distance, its workings are in an appendix that is not in the PDF, and extended to long hauls it breaks every ceiling. |
| ISER 2010 day cost times an assumed voyage time (first round, "Nenana operations build-up") | Yes. Independent method 3, together with the next row. | 0.20 per gallon per voyage plus 0.0013 per gallon per channel mile (0.196 and 0.00128). Totals 0.41, 0.56, 0.66 and 1.21 per gallon at 164, 280, 364 and 794 miles. | `components of alaska fuel costs.pdf`, pages 19 and 20, Tables 1 to 3 (Q6, Q7); page 17 (Q9); caveat page 12 (Q8) | Tables re-read in the text file; arithmetic reproduced by the verifier's script, re-run for this record. | Kept, best read as a cost floor. Speeds, loading time and stop times are the analyst's assumptions; ISER gives none. |
| ISER 2010 barge-days, river case (first round) | No. It uses the same day cost, so it counts inside method 3. | ISER's published flat figure: 1.18 per gallon for a 15-day round trip of 250,000 gallons (ISER's range for most locations 0.61 to 1.22). Inferred split: 0.82 per gallon fixed plus 0.0009 per gallon per mile (0.00095). | Same file, page 20, Table 3 (Q7); page 19, footnote 18 | Tables reproduce exactly. The split is an inference from season throughput, not a source value. | Kept only inside the ISER family, which enters the tests at the geometric mean of the two variants (slope 0.0011; total 0.63 per gallon at 164 miles). |
| Fiscal year 2025 delivered utility prices against river miles from Nenana (first round, "Nenana revealed prices") | Yes. Independent method 4. | Per-mile part 0.0014 per gallon per channel mile (0.00136; interval 0.0003 to 0.0026). Fixed part not identified: 0.08 per gallon above the road-system price for AVEC villages, 1.03 for single-village utilities. | `2026.03.01 FY2025 PCE Statistical Report by Community (Final).pdf`, as decoded in `shared/pce_prices_with_distances.csv`; supply point: `12 2015_06_01 Rural Fuel Model Report.pdf`, page 8 (Q11) | The verifier's fit script was re-run for this record and reproduces all five fits. Seven prices were spot-checked against the decoded report text. | Kept as a point estimate for the slope, with low weight: it rests on one zero-mile anchor (Minto), and inside 164 to 414 miles the slope is negative and not different from zero. |
| Village revealed prices, river results for the Kuskokwim and the Kobuk (first round) | No. Same price report as method 4. | Kuskokwim slope about 0.0012 per gallon per river mile. Kobuk: Noorvik 1.67 per gallon over Kotzebue at 56 river miles, Kiana 1.39 at 84 river miles. | Same price table; ISER 2008, page 31 (printed 25) (Q14) | Fits re-run by the verifier's script for this record. | Kept as bounds and context only. It shows that village premiums are mostly fixed; it does not measure freight. |
| Long-haul ceilings from 2007 retail and utility prices at Fort Yukon and Mountain Village (second round) | Not counted. Bounds only. | Mountain Village: at most 1.45 to 2.36 per gallon for all transport, storage and distributor margin over 793 channel miles (0.0018 to 0.0030 per channel mile). Fort Yukon: at most 2.15 per gallon over 462 channel miles (0.0046 per channel mile). | `Components of Delivered Fuel Prices in Alaska.pdf`, pages 55, 57, 60, 69, 71 (printed 49, 51, 54, 63, 65) (Q12, Q13) | Quotes and Table 15 cells confirmed in the text file. The verifier corrected the second-round ceiling, which had subtracted a gasoline mark-up from a fuel-oil figure. | Kept as ceilings. They include storage, the Nenana terminal, the truck leg and margin. |
| Second-round recommended rate: geometric mean of the DEC figure per channel mile and the contract slope, with no fixed part | Not a method. It combines methods 1 and 2. | 0.0055 per gallon per channel mile. | `derive2_results.json`, `derivations["river-dec-and-contract"]` | Arithmetic reproduced. | Rejected as a statewide rate. It gives 4.36 per gallon at Mountain Village against a ceiling of 1.45 to 2.36, and exceeds the whole fiscal year 2025 price premium at 15 of 16 Yukon villages. It is a fair all-in average for hauls of 100 to 360 channel miles only. |

**Spread ratios against the 3x standard.**

- **Total per gallon at Tanana (164 channel miles).** Contracts 0.61, DEC 1.10 and ISER 0.63 dollars per gallon
  give a spread ratio of 1.8 and a geometric mean of 0.75 dollars per gallon. This meets the standard. The verdict
  computes the DEC value on Tanana's own 98.1 straight-line miles; the verifier's script computes it on channel
  miles divided by 1.5 and gets 1.23 dollars per gallon, a spread ratio of 2.0 and a geometric mean of 0.78. Both
  pass. Adding the fourth method (the AVEC price line, 0.35 dollars per gallon at 164 miles) widens the spread to
  3.2 on the first reading and 3.5 on the second.
- **All-in average per channel mile.** Contracts 0.00375, DEC 0.00748 and ISER 0.00384 dollars per gallon per
  channel mile give 2.0 at 164 miles (the working files give 0.0037, 0.0074 and 0.0038 at the 330.0 basis). The
  same comparison gives 2.7 at 280 miles and 3.1 at 364 miles, so the agreement weakens as the haul lengthens.
- **Per-mile part.** Contracts 0.0044, ISER 0.0011 and delivered prices 0.0014 dollars per gallon per channel mile
  give a spread ratio of 3.9 and a geometric mean of 0.0019. This fails the standard. DEC cannot supply a slope;
  if its all-in average were counted as one anyway the spread would be 6.8.
- **Fixed part.** Contracts zero (interval up to about 0.10 dollars per gallon), ISER 0.20 or 0.82, delivered
  prices 0.08 to 1.03 (the working file prints 0.99 for the last figure, which is in fiscal year 2025 dollars). A
  spread ratio is not defined when one reading is zero. This fails.

In plain terms: the sources agree on what a short river delivery costs in total, and they do not agree on how that
cost grows with distance. A rate fitted to short hauls (0.0044 to 0.0075 dollars per gallon per channel mile)
overshoots the long-haul ceilings by 1.5 to 4 times. A rate fitted to long hauls (about 0.0013) prices a 164-mile
haul at 0.21 dollars per gallon against evidence of 0.61 to 1.10. Only a fixed part plus a per-mile part fits both
ends, and the split between the two is the unsettled piece.

**Quoted passages** (confirmed in `pdf_text/` on 2026-11-17).

- Q1. DEC 2007, page 37 (printed 21): "In 2007, the cost for delivery via river fuel barge is about $0.007 per
  gallon per map mile of transport from the fuel hub. Thus, for a village that is 100 map miles upriver from a
  regional fuel hub, the cost to deliver fuel is around 70¢ per gallon." Footnote 6: "MAFA Analysis of Crowley Marine
  Services invoices. To simplify the analysis, a map-mile is adopted rather than a river-mile."
- Q2. DEC 2007, page 105 (printed 89): "ULSD No. 1 Density = 6.76 lb/gallon" and "River fuel barge freight cost
  component = $0.112 per cwt per one-way map-mile". Footnote 10: "MAFA developed assumptions from review of Crowley
  Maritime Invoices and Alaska Fuel Supplier price quotes for ULSD in 55-gallon drums delivered to a shipping wharf."
- Q3. ISER 2008, page 33 (printed 27), Table 10: "Nenana $ 0.04 Truck"; "Tanana $ 0.40 Seasonal Barge"; "Ruby $ 0.70
  Seasonal Barge"; "Koyukuk $ 0.91 Seasonal Barge". Text above the table: "We combined the two fuel contract years
  and averaged costs for communities that received contracts in both years." and "these contracts should provide a
  reasonable proxy for the costs of delivering fuel to specific ports with a reasonable return on investment and
  profits."
- Q4. ISER 2008, page 34 (printed 28): "Prices are determined for each community based on the time and risks
  Crowley faces when delivering fuel. Fixed costs are estimated on a per gallon basis and require an estimate of
  how much fuel will be delivered to a particular community."
- Q5. DEC 2007, page 19 (printed 3): "There are five communities considered as regional hubs." and "All of these
  hubs have tidewater access and are supplied by ocean-going fuel barges."
- Q6. ISER 2010, page 19, Table 1: "Capital Costs $ 600,000; Operating Costs $ 750,000", with "It assumes a 10%
  return on capital investment."
- Q7. ISER 2010, page 20: "Areas such as the Yukon and Upper Kuskokwim rivers have operating seasons that are about
  30 days shorter due to a longer ice season, and barges often deliver less than two million gallons per year".
  Table 3: "Annual Barge Cost $ 1,350,000; Operating Days 105; Daily Cost $ 12,857; Trip Length (days) 15; Cost per
  Trip $ 192,857; Gallons per Trip 250,000; Cost per Gallon $ 0.77". Same page: "the estimated range of costs for
  Western Alaska small barge deliveries is $0.40-$0.80 per gallon for most locations."
- Q8. ISER 2010, page 12: "The numbers used in this report reflect the best estimates and memories of historical
  costs but should not be considered exact without confirming data with current fuel distribution companies."
- Q9. ISER 2010, page 17: "In the case of the Yukon River, fuel is trucked to the Nenana terminal from a North Pole
  refinery. This is a straightforward process with costs of less than $0.05 per gallon." and "From the Tanana River
  at Nenana, fuel is shipped to the Yukon River, supplying fuel to communities as far downstream as Mountain Village
  and as far upstream as Fort Yukon."
- Q10. ISER 2008, pages 30 and 31 (printed 24 and 25): "Nenana serves as the fuel hub for the Yukon River." and
  "Occasionally fuel is shipped from the mouth of the Yukon from the Bethel or Nome fuel hubs. Generally the more
  direct route from the Nenana fuel terminal is less costly, even for communities near the mouth of the Yukon."
- Q11. AEA 2015 model report, page 8: "Communities along the Yukon River receive fuel shipments from barges that
  depart from Nenana". Footnote 4: "Communities at the mouth of the Yukon River receive fuel shipments via
  ocean-going barge. These communities were grouped with the coastal communities instead of the Yukon River
  communities."
- Q12. ISER 2008, page 57 (printed 51): "The “other” costs of fuel in Mountain Village in late 2007 were roughly
  $1.83 for gasoline and $2.22 for fuel oil." Page 71 (printed 65): "In November 2007 Mountain Village reported a #1
  heating fuel price of $4.92 and a gasoline price of $4.60. This includes a 30% mark-up on the delivered price."
- Q13. ISER 2008, page 69 (printed 63): "Diesel #2 sold to the Gwitchyaa Zhee Utility for $3.65 per gallon." Page 55
  (printed 49): "Fuel barged 400 river miles upriver from Nenana." Page 60 (printed 54), Table 15: crude price
  1.78, refinery 0.59 (gasoline) and 0.53 (#2 diesel), barge distance 440 (Fort Yukon) and 750 (Mountain Village).
- Q14. ISER 2008, page 31 (printed 25): "Kotzebue is the fuel hub for communities on the Kobuk River. The cost of
  barging fuel on the Kobuk is high because of difficult navigation and hazards."
- Q15. ISER 2010, pages 22 and 23: "Missing header or pipelines and docking issues are not uncommon. This could
  represent a $0.10-0.15 per gallon difference in the price the fuel distribution company charges a community."
  Page 7: "These costs can easily increase by $0.20 per gallon for docking and fuel off-loading deficiencies".
- Q16. ISER 2010, page 18: "All risk of a fuel spill is borne by the fuel distribution company until the fuel passes
  through the customer’s header pipe upon delivery."

### Derived versus assumed

One row per input that the provisional figure rests on. Dollar values are dollars per gallon unless the row gives
another unit. "Analyst 2" is the second-round analyst, "analyst 1a" the first-round delivered-price analyst,
"analyst 1b" the first-round operations build-up analyst, "analyst 1c" the first-round barge-days analyst and
"verifier" the author of `verdicts.river`.

| Input | Value | Type | Reference | What changes if it is wrong |
|---|---|---|---|---|
| Contract delivery charges, three river villages | Tanana 0.40, Ruby 0.70, Koyukuk 0.91 | Quoted | ISER 2008, page 33 (printed 27), Table 10 (Q3) | Method 1 rests on these three cells alone. |
| Contract delivery charge, Nenana by truck | 0.04 | Quoted | Same table (Q3) | It is subtracted to get the river part; without it the river totals are 0.07 higher in 2026 dollars. |
| Subtracting the Nenana truck row from the three charges | 0.36, 0.66, 0.87 | Assumed (verifier) | `verify2/river/verify.py`; the table does not say the river bids contain that row | The fixed part implied by contracts moves by 0.07 either way. |
| Dollar year of the contract charges | 2005, as the mid-point of 2003 and 2006 contracts | Assumed (analyst 2 and verifier); the source states no dollar year | Q3 ("combined the two fuel contract years") | On a 2006 basis the slope is 0.0042. On a 2003 basis it would be 0.0046 (computed for this record from the index table; the working files could not bracket it). |
| Supply point for Tanana, Ruby and Koyukuk | Nenana | Assumed (analyst 2); Table 10 does not state it | General support: Q10. Against it: DEC 2007, page 36 (printed 20) lists a Crowley terminal at Galena, between Ruby and Koyukuk | The distances behind the slope would be wrong for Koyukuk, and the slope with them. |
| Channel miles from Nenana | Tanana 163.8, Ruby 279.8, Koyukuk 363.4, Fort Yukon 461.9, Mountain Village 793.4 | Measured | `verify2/river/dist_check.json` (shortest path over waterway edges of `network_nodes` and `network_edges`) | Every per-mile figure scales with these. ISER prints 440 and 750 miles for the last two (Q13), about 5% lower. |
| Straight-line miles from Nenana, and the ratio of channel to straight-line miles | Tanana 98.1, Ruby 190.3, Koyukuk 256.3; ratio 1.41 to 1.67 on main-stem rivers, 2.6 to 3.2 on the Yukon Flats | Measured | Same file | Sets how the DEC map-mile rate converts to channel miles. |
| Contract slope | 0.00256 per channel mile in contract dollars; 0.00435 in 2026 dollars | Computed | Least-squares fit of the three charges on channel miles; times 1.7013 | Top of the per-mile range. With one spare data point the 95% interval on the intercept is minus 0.09 to plus 0.06 (2005 dollars). |
| Contract totals net of the truck leg | 0.61, 1.12, 1.48 | Computed | 0.36, 0.66, 0.87 times 1.7013 | Feed the short-haul convergence test. |
| What a contract charge contains | A bid per community, with fixed costs spread over the expected gallons | Quoted | ISER 2008, page 34 (printed 28) (Q4) | The slope may partly reflect volume: Tanana buys about twice what Ruby or Koyukuk do (96,654 against 49,854 and 49,609 gallons in fiscal year 2025, Measured). |
| DEC river invoice rate | 0.007 per gallon per map mile, 2007; 100 map miles is about 0.70 | Quoted | DEC 2007, page 37 (printed 21) (Q1) | It is the middle value in the short-haul test and the old source of 0.011. |
| Meaning of "map mile" | A straight-line statute mile | Assumed (analyst 2 and verifier, a judgement between two readings) | Q1 footnote; the same report uses "map mile of air transport" on page 89 (printed 73) | If a map mile were a channel mile, DEC would be 0.0112 per channel mile, 1.5 times higher. |
| Ratio used to turn DEC's rate into channel miles | 1.5 (range 1.41 to 1.67) | Assumed central value (verifier) inside a Measured range | `verify2/river/dist_check.json` | DEC per channel mile is 0.0067 to 0.0080 across the range. |
| Hub and villages behind the DEC rate | Not known; used with Nenana distances | Assumed (analyst 2) | DEC's "regional hubs" are five tidewater hubs (Q5), so Nenana is not one; the workings are in Appendix C, which is not in the PDF | The DEC total at Tanana (1.10) may describe a different river. |
| DEC rate in 2026 dollars | 0.0112 per map mile; 0.0075 per channel mile; 1.10 at Tanana | Computed | 0.007 times 1.6024; divided by 1.5; times 98.1 map miles | Follows the rows above. |
| DEC hundredweight cross-check | 0.112 per hundredweight per map mile at 6.76 pounds per gallon is 0.0076 per gallon per map mile, 1.08 times the invoice rate | Quoted inputs, Computed result | DEC 2007, page 105 (printed 89) (Q2) | None: it is the same MAFA review of Crowley invoices, so it is a consistency check and not a second source. |
| Annual cost of a tug-and-barge set | 1,350,000 dollars (600,000 capital at a 10% return plus 750,000 operating) | Quoted | ISER 2010, page 19, Table 1 (Q6) | The whole ISER family scales with it. The set described is a coastal one; ISER gives no river-set cost. |
| Short-season day cost, trip length and load | 105 days; 12,857 dollars per day; 15-day trip; 250,000 gallons; 0.77 per gallon | Quoted | ISER 2010, page 20, Table 3 (Q7) | The only published river figure; it carries no distance. |
| Reliability of the ISER numbers | "best estimates and memories of historical costs" | Quoted | ISER 2010, page 12 (Q8) | The inputs are recollections of former carrier executives, not records. |
| Dollar year of the ISER 2010 figures | 2010 | Assumed (project convention; the report is dated February 2010) | Earlier chapter, verification addendum of 2026-07-15 | If they are 2009 dollars, every ISER-based value rises 1.6%. |
| Tug speed and running hours | 7 miles per hour downstream, 4 upstream, 24 hours a day | Assumed (analyst 1b); ISER gives none | `derive/nenana_buildup/model.py` | The per-mile part of the build-up is inversely proportional to speed; 6 and 3.5 miles per hour raise it about 30%. |
| Loading time and village stops | 1 day loading; 3 stops of half a day | Assumed (analyst 1b) | Same script | They set the build-up's fixed part (0.20; its own range 0.08 to 0.41). |
| Whole load carried to the farthest point | 250,000 gallons delivered at the end of the haul | Assumed (analyst 1b) | Same script | A load split among several villages costs more per gallon-mile. |
| Days per load that do not depend on distance | 10.5 days | Assumed (analyst 1c, inferred from ISER's season throughput) | `derive/village_iser/calc.py` | This reading puts the fixed part at 0.82. The verifier's view is that it measures yearly idle time, not time per delivery. |
| River speed in the barge-days reading | 8 miles per hour through the water, 3 miles per hour current (82.5 one-way miles per sailing day) | Assumed (analyst 1c) | Same script | Sets the 0.00095 per-mile figure and puts ISER's 15-day trip at 371 one-way miles; the build-up puts it at 764. |
| Combining the two ISER readings | Geometric mean (slope 0.0011; total 0.63 at 164 miles) | Assumed (verifier) | `verify2/river/synth.py` | The two readings alone give 0.41 and 0.98 at 164 miles, so the ISER entry in the short-haul test could sit anywhere between them. |
| Fiscal year 2025 utility prices and gallons | For example Minto 2.78, Tanana 4.16, Nulato 3.13, Koyukuk 4.08 dollars per gallon | Measured | `shared/pce_prices_with_distances.csv` (decoded from the PCE report) | A decoding error would move the fit; seven rows were spot-checked. |
| River miles from Nenana used in the price fit | For example Tanana 162.9, Nulato 377.9, Pilot Station 757.0 | Measured | Same table, column `river_mi_from_Nenana` | The slope is per network mile, which is the unit the model uses. |
| All sixteen villages supplied from Nenana | Yes | Assumed (analyst 1a) | For: Q9, Q10. Against, for the lowest villages: Q11 footnote | Measured from the river mouth the gradient is negative. |
| Zero-mile anchor for the price fit | Minto, a road-served AVEC village, at 2.78 dollars per gallon | Assumed (analyst 1a) | Same table | Without it the slope is 0.0015 with an interval that includes zero. |
| Villages left out of the price fit | Ruby (7.02 dollars per gallon), Hughes, Rampart and Fort Yukon | Assumed (analyst 1a; partly after seeing the data) | `blind_results.json`, `nenana-revealed-prices` | Including Ruby turns the pooled slope negative. |
| Dollar year of the fiscal year 2025 prices | Mid-point of 2024 and 2025 (factor 1.0454) | Assumed (analyst 1a and verifier) | Fiscal year 2025 runs July 2024 to June 2025 | A calendar-2025 basis (factor 1.0320) lowers the slope by 1.3%. |
| Delivered-price slope | 0.0013 per river mile in fiscal year 2025 dollars; 0.00136 in 2026 dollars; interval 0.0003 to 0.0026 | Computed | Fits in `verify2/river/pce_fit.py`; times 1.0454 | One of the three slopes; the upper limit for long hauls. |
| 2007 prices used for the ceilings | Fort Yukon utility diesel 3.65; Mountain Village heating fuel 4.92 and gasoline 4.60, with a 30% mark-up; crude 1.78; refining 0.53 and 0.59 | Quoted | ISER 2008, pages 69, 71 and 60 (printed 63, 65, 54) (Q12, Q13) | The ceilings move with them. |
| Using crude plus refining (2.31) as the price before transport | 2.31 | Assumed (ISER's own method, adopted by the verifier) | ISER 2008, Table 15 | It compares a September 2007 refinery price with November 2007 retail prices. |
| Federal diesel tax taken off the Mountain Village fuel-oil figure | 0.244 | Assumed (the verifier's reconstruction; the table cell is blank) | `verify2/river/verify.py` | Without it the fuel-oil residual is 2.47, not ISER's 2.22. |
| Long-haul ceilings | Mountain Village 1.45 to 2.36; Fort Yukon 2.15 | Computed | 0.90 to 1.47 and 1.34 in 2007 dollars, times 1.6024 | They bound any form at 462 and 793 channel miles. |
| Per-mile point | 0.0013 per channel mile | Assumed (verifier's choice of the median of the three slopes) | `verdicts.river`; a least-squares fit to all method totals gives 0.0012 (`verify2/river/synth.py`) | Long-haul totals move with it; at 794 miles each 0.0001 is 0.08. |
| Fixed-part point | 0.50 per river delivery | Assumed (verifier's judgement between readings of zero, 0.20 and 0.82) | `verdicts.river`; the least-squares value is 0.53 | Short-haul totals move one for one. The verifier judges it more likely high than low for AVEC villages and too low for the Kobuk. |
| Ranges | Fixed 0.20 to 0.80; per-mile 0.0009 to 0.0044 | Assumed (verifier) | `verdicts.river` | These are judgement ranges, not confidence intervals. |
| Which methods count as independent | Four, after merging those that share a source | Assumed (verifier) | `verdicts.river`, convergence | DEC and the contracts come from the same carrier era (Crowley), so they may be less independent than counted. |
| One statewide river figure | No separate figure for the Yukon, the Kuskokwim or the Kobuk | Owner decision, 2026-11-17 | Decision 6 in the re-derivation log | All direct evidence is from the Yukon below Nenana; the Kobuk is under-priced and the Kuskokwim untested. |
| Index used to bring dollars to 2026 | CPI-U, 2026 value 332.243 | Owner decision, 2026-11-17 | `shared/index_basis_2026-11-17.md` | By the inland freight index, minus 7% to plus 20% depending on the source year. |

**Which assumptions carry the most weight.** The two points themselves are the largest: 0.50 dollars per gallon and
0.0013 dollars per gallon per channel mile are the verifier's judgement between readings that span zero to 0.82 and
0.0011 to 0.0044, and no document states either. Next are the voyage assumptions behind the ISER split (speeds,
stop times and the 10.5 fixed days), which decide whether the ISER family says the cost is mostly fixed or mostly
mileage, and the supply assumptions behind the price slope (every village supplied from Nenana, Minto as the
zero-mile anchor). The reading of "map mile" as a straight-line mile changes the DEC figure by 1.5 times. The
dollar year of the contracts and the choice of index move the result by a few percent to 20%, which is small
against the ranges.

### What the figure includes and excludes

**Inside the per-mile part (0.0013 dollars per gallon per channel mile):**

- The tug and barge set while under way, on the loaded leg and the empty return: crew, tug fuel, insurance and the
  10% return on capital in ISER's set cost.
- A small allowance above bare cost (the point sits about 20% above the ISER build).

**Inside the fixed part (0.50 dollars per gallon per river delivery):**

- The barge set's time loading at the river hub and discharging through the village header (Q16), and its waits.
- The idle overhead of a short season.
- The carrier's administration and margin, as embedded in contract charges.
- The river hub's barge-loading throughput (the contract charges net of the Nenana truck row include it).

**Consequences for fees, so that no handling is billed twice:**

- No separate fee for loading a river barge, and none for barge-side discharge at a village with a working header.
  Both are in the fixed part.
- The fixed part must be billed exactly once per river haul. On routes from Nenana the two existing barge-to-road
  fees of 0.24 dollars per gallon already total 0.48, so a river fixed fee added on top would bill it twice. The
  amount fits; the label does not, because the 0.24 is documented as truck-rack loading on the road side and
  villages have no truck rack.
- On routes that enter a river from salt water (Kuskokwim, Kobuk, Yukon mouth) only one 0.24 is billed. The missing
  0.26 dollars per gallon or so belongs on the transfer from the line-haul vessel to the shallow-draft barge, and
  that fee must then not also contain the river set's loading time.
- The two points above describe the fee table as applied today. The transfer-fee addendum proposes replacing each
  0.24 with 0.01 dollars per gallon at an origin port and 0.046 at a village landing. If that is adopted, the two
  fees no longer stand in for the fixed part, and the 0.50 must then be billed explicitly, once per river haul.
  Under the first overlap rule of that addendum the village-landing fee is zero wherever this fixed part is applied,
  because discharge at the village is already inside it; the 0.046 and the 0.50 must not be added together without
  saying so. Whether that addendum's origin-port charge (0.01) may be billed at a river hub, when the hub's
  barge-loading throughput is inside this fixed part, is not settled either.
- Under this form the river per-mile rate is carriage only. That differs from the skill's rule 5, which treats the
  barge rate as all-in. If the project keeps one all-in barge rate with no fixed part, the evidence supports it
  only as an average at one distance: about 0.0048 dollars per gallon per channel mile at 164 miles, falling to
  about 0.0019 at 794 miles (the working file gives 0.0047 and 0.0019 at the 330.0 basis).

**Not inside either part; bill elsewhere or not at all:**

- Truck from North Pole to Nenana: under 0.05 dollars per gallon in 2010, which is 0.076 in 2026 dollars (Q9). The
  Road rate over the model's 68.7 road miles (0.048 dollars per gallon; the verdict writes "about 65 miles" and
  0.045) covers it; no extra fee.
- Ocean line-haul to the river hub or the river mouth: the ocean segment.
- Coastal hub discharge and terminal fees (ISER 2010, page 18: shore labour 0.06 to 0.09, dock fee 0.03 to 0.06,
  third-party terminal 0.11 to 0.23 dollars per gallon in 2026 dollars): the fees segment.
- Lightering from an ocean vessel: the fees segment.
- A surcharge for a village with no header or a bad landing: 0.15 to 0.23 dollars per gallon, up to 0.30 (Q15).
  Additive, and only at landings known to be deficient.
- Village storage, working capital (0.03 dollars per gallon in 2010 dollars), retail mark-up and taxes: outside
  the transport model.

### Compared with the applied value and the earlier chapter

**Applied today** (`source_scripts/friction_surface/friction_costs.py`). One Barge rate of 0.0010 dollars per
gallon-mile on every waterway edge, river or ocean, with a documented range of 0.00023 to 0.011. The code comment
names 0.011 as the "river distribution" end of that range (the DEC rate of 0.007 dollars per gallon per map mile,
inflated) and calls the barge rate all-in. The value 0.011 is not charged on any edge; it is the top of the range
and part of the comment's decomposition. A barge-to-road transfer costs 0.24 dollars per gallon.

**Earlier chapter** (`blind_derivations/02_barge.md`, sections 4, 6 and 7). It recommended 0.011 dollars per
gallon-mile on river distribution edges (range 0.006 to 0.018) at medium-high confidence, because ISER's 0.91
dollars per gallon and the DEC rate "agree within 10%" at 82 map miles. It read the much flatter gradient in
fiscal year 2025 utility prices (about 0.0010 to 0.0015 dollars per gallon per mile) as an effect of AVEC's pooled
buying, and kept the DEC rate as "the true marginal transport cost".

**Effect of the new evidence.**

- **Overturns 0.011 as a river rate per network mile.** The reasons are these.
  - It is a figure per map mile. Per channel mile on a main-stem river it is 0.0075.
  - It is an all-in average at about 100 map miles, not a marginal rate. The agreement with ISER holds only at
    one chosen distance, because ISER's figure carries no distance.
  - State contract charges on the Yukon below Nenana are 1.6 to 2.0 times lower (0.0044 per channel mile).
  - At 0.011 the charge to Mountain Village is about 8.9 dollars per gallon against a ceiling of 1.45 to 2.36, and
    it exceeds the whole fiscal year 2025 price premium at 16 of 16 Yukon villages.
  - The earlier chapter set the flat price gradient aside as an effect of pooled buying. The verdict counts it as
    one of three per-mile methods, and the ISER day-cost build, which uses no prices, gives a figure close to it
    (0.0011 against 0.0014 dollars per gallon per channel mile).
- **Lowers the top of the Barge range.** The verdict's view is that the top should come down from 0.011 to about
  0.0044 (the contract slope), or to 0.0075 if the DEC figure per channel mile is kept as the outer bound.
- **Does not move the applied per-mile point.** The applied 0.0010 is within 10% of the ISER cost build (0.0011)
  and about 26% below the delivered-price slope (0.0014; the verdict rounds this gap to 30%). Only the contract slope argues for more, and only for
  hauls under 360 miles.
- **Shows where today's totals are right and wrong.** A route from Nenana crosses a barge-to-road transfer near
  Nenana and another at the village, so it carries 0.48 dollars per gallon of fees. Before friction multipliers the
  applied total is then 0.64 dollars per gallon at 164 channel miles, 0.76 at 280, 0.84 at 364 and 1.27 at 794.
  That is inside the evidence at short and long distance and 30% to 45% below the contract charges at Ruby and
  Koyukuk. A route that enters a river from salt water carries one fee (0.24), not about 0.50.
- **Rejects the second-round figure as a statewide rate.** As a pure rate with no fixed part, 0.0055 dollars per
  gallon per channel mile is 5.5 times the applied rate. It describes the all-in average on hauls of 100 to 360
  channel miles (the three-method geometric mean there is 0.0042 to 0.0048; the working file gives 0.0042 to
  0.0047 at the 330.0 basis) and nothing longer.
- **Remaining misfit of the provisional form.** It exceeds the whole fiscal year 2025 premium over the Interior
  road-system price at 8 of 16 Yukon villages, all AVEC, so the fixed part is more likely high than low. At
  Mountain Village it gives 1.53 dollars per gallon, which is below the upper reading of the 2007 ceiling (2.36)
  and above the lower one (1.45). At Fort Yukon it gives 1.10 against a ceiling of 2.15.

**Review status.** The overturning of 0.011 dollars per gallon-mile as a river rate, and the lowering of the top of
the Barge range that follows from it, come from ONE verifier and have not had a second independent review. The
flat river landing charge of 0.50 dollars per gallon used in the what-if assembly is an assembly choice labelled
Assumed in the re-derivation log; it is this provisional fixed part reused, not separate evidence.

### Open evidence gaps

Each item names the document type that would raise the status.

- **A same-year charge schedule from one river hub covering short and long hauls.** A carrier rate table or a bid
  tabulation with six or more villages from about 50 to 800 channel miles. This alone would separate the fixed
  part from the per-mile part and could make the figure Derived.
- **Appendix C of the DEC 2007 report** (the MAFA invoice workbook): which hub and villages, how map miles were
  measured, and whether 0.007 is a ratio at one distance or a fitted slope.
- **Voyage records for a river tug and barge set**: days per round trip and gallons delivered by destination, from
  carrier logs or vessel-tracking data. The two ISER-based readings put the published 15-day, 0.77-dollar trip at
  371 or 764 one-way miles, and their fixed parts differ fourfold (0.20 against 0.82 dollars per gallon).
- **The fiscal year 2025 supply point of each lower-Yukon utility** (Nenana or the coast), from utility fuel
  purchase records or bid awards, and a Nenana or Fairbanks rack price for the same year. Without them the price
  slope rests on the single Minto anchor.
- **The 2003 and 2006 State fuel contracts separately**, with parcel sizes and delivery points for Tanana, Ruby and
  Koyukuk, to test whether the slope reflects distance or volume and to fix the dollar year.
- **Evidence for upstream hauls.** Fort Yukon and Rampart paid 6.88 and 6.04 dollars per gallon in fiscal year
  2025, about 2.3 dollars per gallon (2026 dollars) above the downstream line, and channel distance on the Yukon
  Flats is 2.6 to 3.2 times straight-line. A delivery charge or invoice for either village would show whether
  upstream needs its own treatment.
- **Evidence for the Kobuk and the Kuskokwim.** Kiana and Noorvik pay 1.39 to 1.67 dollars per gallon over Kotzebue
  at 56 to 84 river miles, well above the provisional form. Table 10 has no Kuskokwim or Kobuk row. A contract,
  bid or invoice for a Kobuk or upper Kuskokwim village is needed before one statewide figure can be trusted there.
- **Dollar years and the index.** The ISER 2010 dollar year (2009 or 2010), and whether the BLS inland water
  freight index represents Alaska river trade. The CPI-U series is a mirror; the BLS download (series CUUR0000SA0)
  should replace it.

**Not re-confirmed for this record.**

- Not re-confirmed: that Ruby Marine runs three trips a season from Nenana to Emmonak. It comes from a web search
  snippet and is in no supplied document. The same holds for the historical river transit times and the tug speeds
  cited in the first-round derivations.
- Not re-confirmed: the first-round regressions as the first-round analysts ran them (`derive/nenana_revealed/`,
  `derive/village_revealed/`) and the first-round operations model (`derive/nenana_buildup/model.py`). They were
  read from the working files. The verifier's own scripts, which redo the main fits and the ISER arithmetic, were
  re-run and reproduce.
- Not re-confirmed: the channel and straight-line distances. `dist_check.py` was not re-run because it rewrites its
  output file; the distances are taken from `dist_check.json` as the verifier left it.
- Not re-confirmed: that a routed path from Nenana actually crosses two barge-to-road transfers. Only the edge
  classes were read. For this record the transfer edges were confirmed to exist in the harness network: one of 225
  metres about 1.1 kilometres from the Nenana hub, and one at each of the Tanana, Koyukuk and Aniak hubs. Friction
  multipliers on river edges were not read, so the applied totals quoted are before any multiplier.
- Not re-confirmed: the federal diesel tax of 0.244 dollars per gallon that the verifier used to reproduce ISER's
  2.22-dollar Mountain Village residual. The tax cell for diesel is blank in Table 15 of the text layer.
- Not re-confirmed: how the verdict built its high-case totals (1.13 to 2.39 dollars per gallon). They reproduce
  with a fixed part of 0.80 and a per-mile part of 0.0020 dollars per gallon per channel mile. That pairing is a
  reconstruction made for this record; the verdict does not state it.
- The fiscal year 2025 prices were confirmed against the project's decoded table, and seven of them (Minto, Tanana,
  Nulato, Koyukuk, Ruby, McGrath, Noorvik) against the decoded report text, not against the pages of the PDF.
- The count "8 of 16 villages, all AVEC" is not in the verifier's scripts, which test an earlier draft form (0.45
  plus 0.0015). It was recomputed for this record for the verdict's form and reproduces at both index bases.

### Working files

All under `harness: blind_derivations/working_2026-11-17/`.

- `derive2_results.json`: `verdicts.river` (the verdict) and `derivations["river-dec-and-contract"]` (the
  second-round blind derivation).
- `blind_results.json`: first-round derivations `nenana-revealed-prices`, `nenana-operations-buildup`,
  `village-iser-bargedays` (river case) and `village-revealed-prices` (river results).
- `derive2/river_published/`: `dist.py`, `calc.py`, `calc_out.txt` (second-round distances and arithmetic).
- `verify2/river/`: `dist_check.py`, `dist_check.json`, `verify.py`, `pce_check.py`, `pce_fit.py`, `synth.py` (the
  verifier's distance check, recomputation, price fits and synthesis). `verify.py`, `pce_fit.py` and `synth.py`
  were re-run read-only for this record and reproduce the working figures at the 330.0 basis.
- `derive/nenana_revealed/` (`geom.py`, `geom.json`, `fit.py`, `fit2.py`, `fit3.py`); `derive/nenana_buildup/model.py`;
  `derive/village_iser/calc.py`; `derive/village_revealed/` (`build.py`, `fit.py`, `extra.py`, `bands.py`,
  `village_deltas.csv`, `fits_by_region.csv`, `results.txt`).
- `record/river_barge_checks/`: `restate_river_332243.py` and `restate_river_332243_output.txt` (the restatement
  to CPI-U 332.243 and the re-checks made for this record); `find_quote_page.py` (the helper used to confirm quotes
  and pages in `pdf_text/`).
- `shared/pce_prices_with_distances.csv`, `shared/build_distances.py`, `shared/inflation_factors.md`,
  `shared/index_basis_2026-11-17.md`, `shared/cpi/cpiai_datahub_mirror.csv`; `work/pce/` (the decoded PCE report).
- `extracts/dec_2007.md`, `extracts/iser_2008.md`, `extracts/aea_2015_2009.md`, `extracts/local_air_road_winter.md`;
  `work/iser/iser_extracts.md`.
- `pdf_text/` (full text used to confirm every quote above).

**Local documents and public links.** Local files are in the harness under `cost_derivation_resources/`. The links
are those in `DOWNLOAD_LIST.md` or the earlier chapter; they were not opened from this session.

| Document | Local file | Branch | Link |
|---|---|---|---|
| ISER, Components of Delivered Fuel Prices in Alaska (June 2008) | `Components of Delivered Fuel Prices in Alaska.pdf` | cost-sources | https://scholarworks.alaska.edu/cgi/viewcontent.cgi?article=1348&context=uaa_iser_reports |
| DEC and Northern Economics, Cost Assessment for Diesel Fuel Transition in Western and Northern Alaska Communities (December 2007) | `cost-assessment-fordiesel-fuel-transition-in-western-and-northern-alaska-communities.pdf` | cost-sources | https://dec.alaska.gov/air/anpms/ultra-low-sulfur-diesel/rural-economic-summary/ (the earlier chapter gives dec.alaska.gov/media/8915/ulsd-cost-rpt-1207.pdf) |
| ISER, Components of Alaska Fuel Costs (February 2010) | `components of alaska fuel costs.pdf` | main | None recorded |
| AEA, PCE Statistical Report by Community, fiscal year 2025 | `2026.03.01 FY2025 PCE Statistical Report by Community (Final).pdf` | main | None recorded |
| AEA, Rural Fuel Model Report (June 2015) | `12 2015_06_01 Rural Fuel Model Report.pdf` | cost-sources | https://www.akenergyauthority.org/Portals/0/What%20We%20Do/Grants%20%26%20Loans/Renewable%20Energy%20Fund/12%202015_06_01%20Rural%20Fuel%20Model%20Report.pdf |
| BLS inland water freight index (series PCU483211483211) | `PCU483211483211.csv` | cost-sources | FRED series page for that series ID; `DOWNLOAD_LIST.md` records the address for series PCU483113483113 (https://fred.stlouisfed.org/series/PCU483113483113) and says the other two series are found the same way |
| CPI-U series (mirror) | `shared/cpi/cpiai_datahub_mirror.csv` (scratch folder) | not in the harness | https://github.com/datasets/cpi-us |
