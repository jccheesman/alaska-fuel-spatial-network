## Supplement 2026-11-18: Coastal small barge (lightering from a hub or a line-haul vessel to a village on salt water) (second batch of sources; proposal, nothing applied)

This supplement belongs to `addendum_coastal_small_barge.md` (2026-11-17). It reports an adversarial check of one
new blind derivation, made from the second batch of documents, for the hub-to-village small-barge leg. Nothing here
has been applied to `friction_costs.py`, and nothing in it calls for a change to the applied value or to the
addendum's point or range. All 2026 figures are in 2026 dollars at CPI-U 332.243
(`shared/index_basis_2026-11-17.md`); every source-year value is shown next to its restated value. The check was
made by one verifier and has not had a second review.

Short names. **Barge Landing report** is "Alaska Barge Landing System Design, Statewide, Phase 1, Final Report",
January 2009, prepared by URS Corporation for the U.S. Army Engineer District, Alaska (file
`alaskabargelandingsystemdesignstatewidephase1.pdf`). **Marine memo** is the draft "Marine and Riverine
Transportation: Conditions, Issues, and Trends" of the Northwest Alaska Transportation Plan (file
`nwatpMarineRiverineConditions.pdf`). **NSEDC newsletter** is "NSEDC News, Fall 2006" of the Norton Sound
Economic Development Corporation (file `2006-fall2006newsletter.pdf`). **DEC 2007**, **ISER 2010**, **PCE** and
**AVEC** are as in the addendum. **OPIS** is the Oil Price Information Service, whose wholesale ("rack") prices
DEC 2007 tabulates. The three new files are in `batch2/src/` of the working folder and on the `cost-sources`
branch of the harness under `cost_derivation_resources/`. "PDF p." is the page of the PDF file; a number in
square brackets is the printed page.

### What the new documents add

The second batch holds no tariff, contract, invoice or quoted charge for lightering fuel from a hub or a
line-haul vessel to a coastal village. It holds no fuel-barge day rate, no tug speed, no days per trip and no
gallons per trip. What it adds is this.

1. **One day rate for barging, given for construction work.** The Barge Landing report says, in its chapter
   "10.0 Construction Costs": "Recently, barging costs in this region have run $12,000 to $15,000 per day"
   (PDF p. 166 [148]). The sentence sits between construction labour rates and construction unit prices. The
   report does not say what vessels, crew or fuel the rate covers, and it does not say the year. It is a price
   paid to hire barging for construction mobilisation in western Alaska, not a fuel-lighter rate. At an assumed
   2008 dollar year it is $18,518 to $23,147 per day in 2026 dollars (factor 1.5431).
2. **A second price observation for Norton Sound villages.** The NSEDC newsletter says that NSEDC "was able to
   negotiate with Delta Western, Inc. for an average price of $3.07 per gallon for 230,000 gallons of heating
   fuel and $3.15 per gallon for 76,000 gallons of unleaded gasoline" for nine organisations in seven communities
   (Elim, Gambell, Koyuk, Savoonga, Shaktoolik, Stebbins and Unalakleet) in its 2006 Consolidated Bulk Fuel
   Program (PDF p. 5). The article does not say whether the price is delivered to the village tank, where the
   fuel was loaded, or when it was priced or delivered. The buyers are city governments and two Native
   corporations, not the electric utilities.
3. **Physical confirmation that stop time, not distance, drives this leg.** The Barge Landing report says "some
   communities have multiple marine headers, each requiring a separate barge landing within the same community.
   This extends delivery times, and at some tidally-influenced sites can halt operations for up to 24 hours"
   (PDF p. 27 [9]). For Norton Sound it records "three fuel offloading points" at Stebbins (PDF p. 33 [15]),
   "Multiple stops" at Saint Michael (PDF p. 34 [16]), "At least two fuel stops" at Shaktoolik, where "Landings
   are dependent on favorable weather and tide conditions" (PDF p. 36 [18]), and "several stops" at Teller
   (PDF p. 41 [23]). It also records one fuel header at Unalakleet, reachable only at high tide (PDF p. 35
   [17]), and a satisfactory single fuel landing at Koyuk, reached across tidal flats at high tide (PDF p. 37
   [19]). The two places where it reports a 24-hour fuel stop are Kongiganak (PDF p. 79 [61]) and Chefornak
   (PDF p. 83 [65]), which are on the Kuskokwim delta, not on Norton Sound. This supports the addendum's form
   (a fixed part per delivery plus a small per-mile part). It gives no number of days for a Norton Sound stop.
4. **Vessel classes.** The Barge Landing report says "mainline barges anchor offshore and lightering barges
   deliver products to the coastal communities" and that operators "use 80-ft by 24-ft lighter vessels with
   shallow drafts (3-ft)"; barges in rural operations "range in size from 120 to 200 feet" (PDF p. 26 [8]).
   This agrees with the lighter classes already in the record (DEC 2007, Table 7, PDF p. 37 [21]: 63,000 to
   285,000 gallons for barges of 80 to 175 feet) and with the 275,000-gallon barge of ISER 2010.
5. **More evidence that Nome is not the loading point for much village fuel.** The Barge Landing report records
   a bulk fuel tank farm at Saint Michael with an adjacent dock owned by Crowley Marine Services (PDF p. 34
   [16]); Saint
   Michael is 8.2 straight-line statute miles from Stebbins and 47.3 from Unalakleet (project hub table),
   against 116.6 and 145.4 from Nome. The marine memo says tankers "anchor offshore to transfer fuel to barges
   that then lighter fuel to smaller communities" and that "fuel delivery to smaller communities is beginning
   to bypass these hubs" (PDF p. 20 [14]). This strengthens the addendum's caveat that miles from Nome are not
   the sailing miles (its rows on Nome as the supply point, and passages Q15 and Q16).
6. **How often fuel carriers call.** The marine memo's Table 2 (PDF p. 19 [13]) gives, for "Nome Area
   Villages", "2 Sailings: June or July and September" for Crowley Marine Services and "As Needed" for Vitus
   Marine. Those two are the fuel carriers (PDF p. 21 [15]). The "4 Sailings: June–September" in the same row
   is Alaska Logistics and the "2 Sailings May, August or September" is Alaska Marine Lines; both are cargo
   carriers (PDF p. 19 [13], "AML and Alaska Logistics provide the primary cargo services"). The table is
   dated 2019.

### The new method, checked

The blind derivation offered two methods and kept them apart. Method A is a build-up: a day rate times days per
trip, divided by gallons per trip. Method B compares the NSEDC 2006 price with an Anchorage wholesale price.
Both were re-run from the quoted inputs (`batch2/verify/coastal/verify_coastal.py`); every figure the blind
derivation reported reproduces to the last digit shown. There is no arithmetic, unit or inflation-factor
error. The faults are in what the inputs are, not in the sums.

| Step | Value | Type | Reference (document and page) |
|---|---|---|---|
| A1. Barging day rate | $12,000 to $15,000 per day; midpoint $13,500 per day (source dollars) | Quoted (range); Computed (midpoint) | Barge Landing report, PDF p. 166 [148], chapter "10.0 Construction Costs". Confirmed in the text file and on the page image. |
| A2. What the day rate covers | Treated as the whole daily cost of a tug and fuel lighter | Assumed (blind analyst) | Not in the source. The sentence is about construction projects and names no vessel, crew or fuel. |
| A3. Dollar year of the day rate | 2008 | Assumed (blind analyst) | The report is dated January 2009 and says "Recently"; its text refers to "the summer of 2008" (PDF p. 79 [61]). 2007 would raise the result 3.8%; 2009 would raise it 0.4%. |
| A4. Day rate in 2026 dollars | $18,518, $20,832 and $23,147 per day | Computed | $12,000, $13,500 and $15,000 times 1.5431 (332.243 / 215.303). |
| A5. Gallons per trip | 120,000 gallons (low-cost case 180,000; high-cost case 60,000) | Assumed (blind analyst) | Anchored on DEC 2007, Table 7, PDF p. 37 [21] (a 100-foot barge holds 120,000 gallons, Quoted) and on 3 villages at about 40,000 gallons each. No document gives gallons per lightering trip for this region. |
| A6. Gallons per village call | About 40,000 gallons | Assumed, from a Computed 43,714 gallons (306,000 gallons / 7 communities) | NSEDC newsletter, PDF p. 5. This is one group of buyers, not the whole call. See check C3 below. |
| A7. Villages per trip | 3 (range 2 to 4) | Assumed | Not in any document. |
| A8. Days loading at the hub | 1.0 day (0.5 to 1.5) | Assumed | Not in any document. |
| A9. Days per village stop | 1.0 day (0.75 to 1.5) | Assumed | The only support is "up to 24 hours" for tide-bound sites with several headers (Barge Landing report, PDF p. 27 [9]) and the 24-hour stops at Kongiganak and Chefornak (PDF pp. 79 and 83), which are outside Norton Sound. An upper case was used as the central value. |
| A10. Tide and weather standby per trip | 1.5 days (0.5 to 3) | Assumed | Not in any document. |
| A11. Non-sailing days per trip | 5.5 days (4.0 to 7.5) | Computed from A7 to A10 | 1.0 + 3 x 1.0 + 1.5. |
| A12. Sailing speed | 6.9 statute miles per hour, which is 6 knots (8 and 5 in the other cases) | Assumed | Not in any document. 6 knots x 1.15078 = 6.905 miles per hour, so the unit conversion is right. |
| A13. Route length | 1.25 x the straight-line miles from Nome, out and back, return empty (1.15 and 1.35) | Assumed | Not in any document. |
| A14. Loading point | Nome tank farm | Assumed | Against it: item 5 above and the addendum's passages Q15 and Q16. |
| A15. Straight-line miles from Nome | Elim 93.5; Stebbins 116.6; Shaktoolik 125.8; Koyuk 128.7; Unalakleet 145.4; Savoonga 163.9; Gambell 198.0; mean 138.8 statute miles | Measured | `hub_community` table of `fuel_network.duckdb`, x and y in EPSG:3338 metres divided by 1,609.344. Recomputed for this check (`dist_check.py`); all seven match within 0.05 mile, and great-circle distances from the table's longitude and latitude are within 0.7 mile. |
| A16. Share of the farthest distance borne by the average gallon | 0.75 | Assumed | Not in any document. It raises the per-mile part by one third. |
| A17. Idle-season charge | None in the point case; x1.5 in the high case | Assumed | Not in any document. |
| A18. Fixed part, point case | $0.619 per gallon in 2008 dollars; **$0.955 per gallon in 2026 dollars** | Computed from A1 to A11 | $13,500 x 5.5 / 120,000, times 1.5431. |
| A19. Per-mile part, point case | $0.00226 per gallon per straight-line statute mile in 2008 dollars; **$0.00349 in 2026 dollars** | Computed from A1 to A16 | $13,500 x 2 x 1.25 / (24 x 6.9) / (120,000 x 0.75), times 1.5431. |
| A20. All-in, point case | $0.83 to $1.07 per gallon in 2008 dollars; **$1.28 (Elim) to $1.65 (Gambell) per gallon in 2026 dollars; $1.44 at the 138.8-mile mean** | Computed | A18 + A19 x miles. |
| A21. All-in, low and high cases | Low $0.57 to $0.74 per gallon; high $5.96 to $7.78 per gallon (2026 dollars) | Computed from Assumed inputs | Low: $12,000, 4.0 days, 180,000 gallons. High: $15,000 x 1.5, 7.5 days, 60,000 gallons. The high case is 10.6 times the low case at the mean distance. |
| B1. NSEDC price, heating fuel | $3.07 per gallon for 230,000 gallons, 2006 | Quoted | NSEDC newsletter, PDF p. 5. Confirmed word for word on the page image. |
| B2. NSEDC price, gasoline | $3.15 per gallon for 76,000 gallons, 2006 | Quoted | Same. Not used: the record has no 2006 gasoline wholesale price in a table. |
| B3. Whether $3.07 is a delivered price | Treated as delivered to the village tank | Assumed (blind analyst) | The article says only "the best price possible on fuel deliveries". |
| B4. Anchorage wholesale price, ULS No. 1 | June 2006 $2.5588; July $2.5189; August $2.5754; September $2.4704; October $2.1763 per gallon | Quoted | DEC 2007, Table 20, PDF p. 65 [49], "Source: Northern Economics, OPIS". Confirmed in the text file. |
| B5. Month of the purchase | August or September 2006 | Assumed (blind analyst) | The board directed the programme in July 2006 (newsletter, PDF p. 5); no date of pricing or delivery is given. |
| B6. Supplier's cost base | Anchorage ULS No. 1 | Assumed (blind analyst) | Not in any document. See check C4 below. |
| B7. Gap, heating fuel over Anchorage ULS No. 1 | August $0.495; September $0.600; October $0.894 per gallon (2006 dollars) | Computed | $3.07 less B4. |
| B8. Same gap in 2026 dollars | **August $0.82; September $0.99; October $1.47 per gallon** | Computed | B7 times 1.6481 (332.243 / 201.592). |
| B9. Gap divided by 138.8 miles | $0.0059 to $0.0071 per gallon per mile (2026 dollars) | Computed | B8 / A15 mean. Rejected: see check C6. |

**Checks made against the blind derivation, and what each found.**

- **C1. The day rate is real, but it is not a fuel-lighter cost.** The quote is on the page given. It is a hire
  price for construction barging. ISER 2010's daily cost for a coastal fuel set is $10,000 per day in 2010
  dollars (Table 2, addendum passage Q6), which is $15,237 per day in 2026 dollars. The construction day rate
  is 1.22 to 1.52 times that (1.37 at the midpoint). A hire price would be expected to sit above a cost at a
  10% return, so the two are consistent in order of magnitude. That is all the quote establishes.
- **C2. Method A has one Quoted cost input and eight Assumed inputs, and the Assumed inputs decide the answer.**
  Moved one at a time across reasonable values, with the others held at the point case, the all-in cost at the
  138.8-mile mean ($1.44 per gallon) moves as follows.

  | Assumed input | Values tried | All-in cost, 2026 dollars per gallon | Multiple of the point case |
  |---|---|---|---|
  | Gallons per trip | 60,000; 180,000; 250,000 (ISER 2010's load); 285,000 | 2.88; 0.96; 0.69; 0.61 | 2.00; 0.67; 0.48; 0.42 |
  | Day rate | $12,000; $15,000; ISER's $10,000 in 2010 dollars | 1.28; 1.60; 1.05 | 0.89; 1.11; 0.73 |
  | Idle-season charge | x1.5 | 2.16 | 1.50 |
  | Days per village stop | 0.5; 1.5 | 1.18; 1.70 | 0.82; 1.18 |
  | Standby per trip | 0.5 day; 3 days | 1.27; 1.70 | 0.88; 1.18 |
  | Villages per trip, same 120,000 gallons | 2; 4 | 1.27; 1.61 | 0.88; 1.12 |
  | Speed | 5; 8; 11.5 statute miles per hour | 1.62; 1.37; 1.25 | 1.13; 0.95; 0.87 |
  | Share of farthest distance | 1.0; 0.5 | 1.32; 1.68 | 0.92; 1.17 |
  | Route length factor | 1.0; 1.5 | 1.34; 1.54 | 0.93; 1.07 |
  | Days loading | 0.5; 1.5 | 1.35; 1.53 | 0.94; 1.06 |
  | Dollar year | 2007; 2009 | 1.50; 1.45 | 1.04; 1.00 |

  Gallons per trip alone moves the result by a factor of 4.75, and no document gives it.
- **C3. The parcel assumption is biased low.** The 40,000 gallons per village call is the NSEDC order divided
  by seven communities. That order was for city governments and two Native corporations only. The electric
  utilities of the same seven villages bought 66,926 to 200,152 gallons each in fiscal year 2025, a mean of
  133,650 gallons per village (Measured, `shared/pce_prices_with_distances.csv`; `parcel_check.py`). The NSEDC
  order is 33% of that utility volume alone. A lighter calling at a village delivers to every tank owner there,
  which is why the Barge Landing report counts several fuel stops per village. With ISER 2010's 250,000 gallons
  per trip and every other point-case input unchanged, Method A gives $0.69 per gallon at the mean distance,
  not $1.44. This is shown as a sensitivity, not as a corrected estimate: the parcel is still Assumed.
- **C4. Method B is not a firm upper bound.** The blind derivation called the gap a ceiling on everything
  between the Anchorage rack and the village tank. Three things prevent that reading.
  - ULS No. 1 is the dearest distillate in Table 20, so it gives the smallest gap. The same table gives Jet A
    at $2.3744 per gallon in August 2006 and $2.2877 in September, and DEC 2007 says Jet A "can also be used
    for home heating fuel oil" (PDF p. 64 [48]). On Jet A the gap is $0.696 and $0.782 per gallon in 2006
    dollars, which is $1.15 and $1.29 per gallon in 2026 dollars; in October it is $1.67.
  - A supplier that buys cargoes may pay less than the Anchorage rack. On the Anacortes high-sulphur No. 2
    price (DEC 2007, Table 22, PDF p. 69 [53]: August 2006 $2.5292, September $1.9127) the gap is $0.89 per
    gallon in August and $1.91 in September, in 2026 dollars.
  - The month is unknown, and the Anchorage prices fell 13% to 16% between August and October 2006.
  Across these readings the gap runs from $0.82 to about $1.9 per gallon in 2026 dollars. It is a soft,
  conditional bound on the whole supply chain, not a cap of $0.82 to $0.99.
- **C5. What Method B leaves for the lighter leg.** The chain between a rack and a village tank includes the
  ocean line-haul. ISER 2010 gives $0.19 to $0.22 per gallon for line-haul to a Western Alaska hub in 2010
  dollars (ocean line-haul addendum, input 1), which is $0.29 to $0.34 per gallon in 2026 dollars. Taking
  that off the August and September gaps leaves $0.48 to $0.70 per gallon on the ULS No. 1 basis and $0.81
  to $1.00 on the Jet A basis, for the lighter leg together with hub handling, supplier margin and any
  product difference. The addendum's figure for these villages ($0.45 + $0.0010 x 93.5 to 198.0 miles =
  $0.54 to $0.65 per gallon) is inside the first band and under the second. ISER's own point ($0.91 per
  gallon) is above the first band and inside the second. Method A's point case ($1.28 to $1.65) is above
  both. The subtraction uses an Assumed supply route, so this is a consistency check and nothing more.
- **C6. The per-mile figure from Method B is rejected.** Dividing a chain total that starts at a refinery
  rack by the miles from Nome to the village mixes two different distances. The blind derivation said so
  itself. It is not carried forward.
- **C7. One unsupported sentence.** The blind derivation said a fuel lighter "would have to be well under a
  third of the quoted rate" for Method A to meet Method B. At the mean distance the day rate would have to be
  0.57 to 0.69 of the quoted rate to bring Method A down to the $0.82 to $0.99 gap, and 0.33 to 0.49 of it
  once the line-haul is taken off. "Between a third and two thirds" is what the arithmetic supports.
- **C8. Two citation faults, neither load-bearing.** The Deering tide sentence is on PDF p. 37 [31] of the
  marine memo, in a table, not on PDF p. 11 [5] as the blind derivation gave it. It reads in full "Barge
  landings occur on high tide and sometimes must wait until the next high tide to depart, depending on the
  amount of cargo", and Deering is on Kotzebue Sound. The "4 sailings" the blind derivation cited for idle
  time are a cargo carrier's (item 6 above); the fuel carrier's figure is 2 sailings.

**Quotes and numbers that could not be confirmed.** None of the load-bearing ones. The day rate, the multi-header
passage, the two 24-hour stops, the vessel sizes, the Norton Sound village passages, Table 2 of the marine memo,
the NSEDC price paragraph, DEC 2007 Table 7 and Table 20, and the seven distances were all found where stated,
apart from the Deering page number in C8. The blind derivation's wording "three offloading points" is "three
fuel offloading points" in the source.

### Derived versus assumed (new inputs only)

| Input | Value | Type | Reference | What changes if it is wrong |
|---|---|---|---|---|
| Barging day rate, construction work, western Alaska | $12,000 to $15,000 per day | Quoted | Barge Landing report, PDF p. 166 [148] | Method A scales in proportion. |
| Dollar year of the day rate | 2008 | Assumed (blind analyst; kept by the verifier) | Report dated January 2009; "Recently" | 2007 raises every Method A figure 3.8%; 2009 raises it 0.4%. |
| Day rate in 2026 dollars | $18,518 to $23,147 per day | Computed | Times 1.5431 | Follows the two rows above. |
| Reading the day rate as a fuel lighter's daily cost | Same figure | Assumed (blind analyst). The verifier does not accept it as more than an order-of-magnitude check. | The source is about construction mobilisation and names no vessel set | If a fuel lighter costs ISER's $15,237 per day, Method A's point falls 27%. |
| Ratio of the day rate to ISER 2010's daily cost | 1.22 to 1.52 | Computed | $18,518 to $23,147 over $15,237 ($10,000 x 1.5237) | This is the one new number the verifier carries forward. |
| Gallons per trip, villages per trip, days loading, days per stop, standby, speed, route factor, distance share, idle charge | 120,000 gallons; 3; 1.0 day; 1.0 day; 1.5 days; 6.9 miles per hour; 1.25; 0.75; none | Assumed (blind analyst), all nine | No document | Table under C2. Together they span a factor of 10.6. |
| Straight-line miles, Nome to seven villages | 93.5 to 198.0 statute miles; mean 138.8 | Measured | `hub_community` table; `dist_check.py` | Sets the per-mile share only; the loading point is itself Assumed. |
| Utility fuel bought in the seven villages, fiscal year 2025 | 66,926 to 200,152 gallons; mean 133,650 gallons per village | Measured | `shared/pce_prices_with_distances.csv` | Shows the 40,000-gallon call understates the parcel; it does not fix the parcel. |
| NSEDC 2006 consolidated price | $3.07 per gallon, 230,000 gallons of heating fuel; $3.15 per gallon, 76,000 gallons of gasoline | Quoted | NSEDC newsletter, PDF p. 5 | The whole of Method B rests on it. |
| The price is delivered to the village tank | Yes | Assumed (blind analyst) | The article does not say | If it is a price at a terminal, Method B says nothing about the lighter leg. |
| Month the price was set | August or September 2006 | Assumed (blind analyst) | Board direction in July 2006 | October widens the gap by $0.29 to $0.40 per gallon in 2006 dollars. |
| Anchorage wholesale ULS No. 1 and Jet A, June to October 2006 | $2.1763 to $2.5754 and $2.0561 to $2.3744 per gallon | Quoted | DEC 2007, Table 20, PDF p. 65 [49] | The choice between the two columns moves the gap by $0.18 to $0.20 per gallon in 2006 dollars. |
| Supplier's cost base is the Anchorage rack for ULS No. 1 | As stated | Assumed (blind analyst). The verifier treats the product and the origin as open. | No document names the origin or the product specification | Gap in 2026 dollars: $0.82 to $0.99 on ULS No. 1, $1.15 to $1.29 on Jet A, $0.89 to $1.91 on Anacortes No. 2 (August to September). |
| Gap in 2026 dollars | $0.82 to $1.67 per gallon across ULS No. 1 and Jet A, August to October | Computed | Gap in 2006 dollars times 1.6481 | Follows the rows above. |
| Line-haul taken off the gap | $0.19 to $0.22 per gallon in 2010 dollars ($0.29 to $0.34 in 2026 dollars) | Quoted (ISER 2010, p. 17), Computed (times 1.5237); Assumed that it applies to this 2006 supply (verifier) | Ocean line-haul addendum, input 1 | If the fuel came from a tanker offshore the line-haul share differs and the residual moves with it. |

### Convergence after the new evidence

**What the new evidence is.**

- **Method A is not an independent point estimate.** It has the same form as the ISER 2010 build-up and the
  first-round operations build-up already in the addendum (a vessel-day cost times days, divided by gallons).
  Its one sourced input comes from a different document and different informants, so that input is
  independent of ISER 2010. Everything else is Assumed. It is usable as a **consistency check on one input of
  the ISER family, the vessel-day cost**: a construction hire rate of $18,518 to $23,147 per day against
  ISER's cost of $15,237 per day (2026 dollars). It does not count as a method.
- **Method B is a soft upper bound on a different quantity.** It is independent of the three sources in the
  addendum's level test: a different document, year (2006) and set of buyers from the fiscal year 2025 utility
  prices, and a different region from Angoon. It uses DEC 2007, which is already in the record, but a table
  (OPIS wholesale prices) that no existing method uses. It bounds the whole chain from a wholesale rack to a
  village tank, and only if the supplier paid at least the rack price and the $3.07 is a delivered price. It
  is usable as a **consistency check on the level**, not as a bound on the lighter leg and not as a point.

**The test again.** The methods that count as independent sources for the all-in level are unchanged.

| Source | Kind | Value, 2026 dollars per gallon per delivery | Counted? |
|---|---|---|---|
| ISER 2010 build-up (with the first-round operations build-up inside it) | Point | 0.91 ($0.60 in 2010 dollars) | Yes |
| Fiscal year 2025 utility price premium, 14 Norton Sound villages over Nome | Upper bound | 0.67 ($0.645 nominal) | Yes |
| Angoon over Ketchikan retail difference, November 2007 | Upper bound | 0.62 ($0.39 in 2007 dollars) | Yes |
| New: Method A, point case at the 138.8-mile mean | Build-up on Assumed inputs | 1.44 ($0.93 in 2008 dollars); low case 0.64; high case 6.75 | No |
| New: construction day rate inside ISER's own trip (15 days, 250,000 gallons) | Inside the ISER family | 1.11 to 1.39 ($0.72 to $0.90 in 2008 dollars) | No |
| New: Method B gap, whole chain | Soft upper bound on a larger quantity | 0.82 to 0.99 (ULS No. 1, August to September 2006); 1.15 to 1.29 (Jet A) | No |
| New: Method B gap less line-haul | Consistency check | 0.48 to 1.00 | No |

- **All-in level.** Three counted sources, 0.62 to 0.91 dollars per gallon: spread ratio 1.46, geometric mean
  0.72 dollars per gallon. This is the addendum's result and it is unchanged. It still meets the standard of
  three independent sources within about 3x, with the same two qualifications (two of the three are bounds,
  and there is no tariff, contract or invoice).
- **If the new figures were counted anyway.** Adding Method A's point case gives a spread ratio of 2.30;
  adding the construction day rate in ISER's trip gives 2.00; adding the Method B gap gives 1.46 to 1.58 on
  ULS No. 1 and 2.06 on Jet A in September; adding the gap less line-haul gives 1.46 to 1.90. None reaches
  3x. So the new evidence does not break the level, and it does not tighten it.
- **Fixed part.** No new number. The stop-time passages support the form. The fixed-part test (spread ratio
  1.51 on three values, two of which depend on an assumed per-mile part) is unchanged.
- **Per-mile part.** No new valid method. Method A's per-mile part ($0.00349 per gallon per straight-line
  statute mile) is 5.5 times the day-rate arithmetic already in the addendum ($0.00063). The whole difference
  is Assumed factors: the smaller load (x2.08), the higher day rate (x1.37), the distance share (x1.33), the
  route factor (x1.25) and the slower speed (x1.17). Counting it would widen the per-mile spread from 3.19 to
  5.5. The per-mile part still fails the standard.

**The two new checks pull in opposite directions.** The construction day rate suggests that a vessel day may
cost more than ISER 2010 recalled, which would put the ISER-family level at $1.11 to $1.39 per gallon, at or
above the top of the addendum's all-in range ($1.21). The 2006 price gap suggests the opposite: once line-haul
is taken off, the lower half of the range fits better than ISER's $0.91. Neither is firm enough to move a
number. The day rate is for a different service, and the gap depends on an unknown product, origin and month.

### Status before and after

| Item | Before (addendum, 2026-11-17) | After this supplement |
|---|---|---|
| Headline status for the rate as it would be applied | Provisional | Provisional (no change) |
| All-in level per village delivery | Derived (three sources within 1.46x; two are bounds; no tariff, contract or invoice) | Derived, with the same qualifications (no change) |
| Split into a fixed part and a per-mile part | Provisional | Provisional (no change) |
| Point, fixed part | 0.45 dollars per gallon per village delivery | No change |
| Point, per-mile part | 0.0010 dollars per gallon per one-way statute sailing mile | No change |
| Range, fixed part | 0.15 to 0.70 dollars per gallon | No change |
| Range, per-mile part | 0.0005 to 0.0020 dollars per gallon per mile | No change |
| Range, all-in per delivery | 0.40 to 1.21 dollars per gallon | No change |

**Why nothing changes.** The second batch contains no tariff, contract, invoice or carrier rate for this leg,
no per-mile rate, no tug speed and no measured days per stop. Its one cost figure is a hire rate for
construction barging with no stated vessel set. Its one price is a consolidated purchase with no stated
delivery terms, origin or date. A build-up that rests on eight Assumed inputs and spans a factor of 10.6 is
not a new independent method, and a chain-level gap that moves from $0.82 to about $1.9 per gallon with the
choice of base price is not a bound on this leg. The evidence does not require a change to the point or the
range, and none is proposed.

**Proposed additions to the addendum (text only; no number changes).**

1. In "Methods and convergence", add two rows marked "not counted": the Barge Landing construction day rate
   as a consistency check on ISER's vessel-day cost (1.22 to 1.52 times), and the NSEDC 2006 price gap as a
   soft chain-level bound ($0.82 to $1.29 per gallon in 2026 dollars for August to September 2006, depending
   on the base product).
2. In "Derived versus assumed", note against the row on Nome as the supply point that Saint Michael has a
   bulk fuel tank farm beside a Crowley-owned dock (Barge Landing report, PDF p. 34 [16]) and that the marine memo describes
   deliveries bypassing the hubs (PDF p. 20 [14]).
3. In "What the figure includes and excludes", cite the multi-header and tide passages (Barge Landing report,
   PDF pp. 27, 33, 34, 36) as support for the fixed-part form.
4. In "Open evidence gaps", change the vessel-day item to say that a construction hire rate has been found
   and that a fuel-lighter day rate or charter rate is still missing.
5. In the same list, record the tension stated above: if a fuel lighter's day cost matched the construction
   hire rate, the ISER-family level would be $1.11 to $1.39 per gallon and the top of the all-in range would
   need to rise. This is a reason to find the fuel-lighter rate, not a reason to move the range now.

### Still missing

- **A tariff, contract, bid tabulation or invoice for the leg itself.** This is the same first gap as in the
  addendum, and the second batch does not close it. The NSEDC programme is a lead: the newsletter says
  suppliers gave "bid prices" and that the programme ran again in 2007. The bid documents or the supplier's
  invoice to NSEDC would show whether the price was delivered, from where, on what date, and possibly a
  freight line per village.
- **A day rate, charter rate or cost statement for a fuel lighter and its tug**, with the vessel set, crew
  and fuel stated. The construction day rate cannot stand in for it.
- **Gallons per lightering trip and per village call.** No document in either batch gives them. They move the
  build-up by a factor of nearly five.
- **Days per village stop and standby days in Norton Sound**, from vessel logs, voyage records or vessel
  tracking. The 24-hour figure is a stated maximum for tide-bound sites and is documented for two Kuskokwim
  delta villages only.
- **Tug speed and sailed distances.** Still in no supplied document. The loading points (tankers at
  lightering areas, the Saint Michael tank farm, Nome) are needed before any per-mile part can be tested.
- **The product, origin and pricing date of the 2006 NSEDC purchase**, and a 2006 wholesale price for
  high-sulphur No. 1 heating fuel and for gasoline. Without them Method B cannot be made a bound on anything
  narrower than the whole chain.
- **A second review.** This check, like the addendum's verdict, was made by one verifier.

**Working files** (all under
`harness: blind_derivations/working_2026-11-17/batch2_2026-11-18/`).

- `derive/coastal/coastal_calc.py` and `coastal_calc_output.txt`: the blind derivation's arithmetic.
- `verify/coastal/verify_coastal.py` and `verify_coastal_out.txt`: the re-run, the sensitivities, Method B on
  other bases and the convergence figures.
- `verify/coastal/find_quotes.py` and `find_quotes_out.txt`: the quote search by page.
- `verify/coastal/dist_check.py` and `dist_check_out.txt`: the distances from the project hub table.
- `verify/coastal/parcel_check.py` and `parcel_check_out.txt`: the utility volumes for the seven villages.
- `verify/coastal/img/bl_p166-166.png`: the page image of the day-rate passage.
- `extracts/barge_landing_system_design_phase1.md`, `extracts/nwatp_marine_riverine_conditions.md`,
  `extracts/newsletter_fall_2006.md`: the fact sheets. `text/`: the page-split text used to confirm quotes.
