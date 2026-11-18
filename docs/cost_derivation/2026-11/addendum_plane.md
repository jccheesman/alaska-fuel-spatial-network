## Addendum 2026-11-17: Plane (bulk fuel flown to a village in a tanker aircraft) (proposal; nothing applied)

Segment: bulk fuel carried in a tanker-class aircraft (about 3,000 to 5,000 gallons a load) from a road-system
or coastal supply point to a village airstrip, priced per gallon per one-way statute air mile of the model's
air route. Nothing in this addendum has been applied to `friction_costs.py`. All 2026 figures are in 2026
dollars at CPI-U 332.243 (`index_basis_2026-11-17.md`). The working files used 330.0; every inflated figure
below was recomputed from its source-year value, and the text says where a rounded value differs from the
working files. **The verdict summarised here overturns the applied Plane rate of 0.025. It comes from one
adversarial verifier and has not had a second independent review.**

In the tables, "PDF p." is the page of the PDF file and "printed p." is the number printed on the page.
"Q1" to "Q9" refer to the quoted passages listed under the tables. Unless a different unit is stated, rates
are in United States dollars per gallon of fuel per one-way statute air mile.

Short names used below. **ISER 2010** and **ISER 2008** are the reports "Components of Alaska Fuel Costs"
(February 2010) and "Components of Delivered Fuel Prices in Alaska" (June 2008) by the Institute of Social and
Economic Research, University of Alaska Anchorage. **DEC 2007** is the December 2007 cost assessment by the
Alaska Department of Environmental Conservation and Northern Economics; "MAFA" in its footnotes is its
consultant, Mark A. Foster and Associates. **PCE** is the Power Cost Equalization program; its report for fiscal
year 2025 (July 2024 to June 2025) gives each utility's fuel price. **CPI-U** is the consumer price index for
all urban consumers. DC-6, DC-4, C-54 and C-46 are types of piston-engine freight aircraft.

### Status

**Level and range: Provisional.** Two independent methods whose inputs were checked in the source documents
agree within a factor of 1.40: published per-mile statements (0.0190) and one real delivery in November 2007
(0.0136). The standard asks for three. The only candidate for a third point, the earlier chapter's engineering
build-up (0.0246 at 182 miles), rests entirely on assumed inputs that no supplied document states, and it
charges more than a ceiling set by fiscal-year 2025 prices. A fourth line of evidence, the fiscal-year 2025
utility fuel price at Allakaket, is independent but gives only a ceiling, not a point. The transaction and
the ceiling both sit on one route, Fairbanks to Allakaket.

**Form (a pure per-mile rate with no fixed part): Provisional.** The published statements are strictly
proportional to distance, and the one observed charter billed little or no ground time. No source measures a
fixed per-flight charge for tanker-class aircraft, so the evidence limits it to between $0 and about $0.5 per
gallon on one route; it does not show that it is zero.

**Small aircraft (150 to 200 gallons a load): not represented.** They cost 0.05 to 0.11 and are outside the
figure. Treating them as negligible by gallons is an assumption (row 26 below).

**What the model should carry meanwhile.** The code keeps the applied 0.025 (range 0.015 to 0.042) until the
owner decides; this record changes nothing. The best estimate on the evidence is 0.016 with the range 0.013 to
0.024, labelled provisional. Until a decision is made, a result that depends on an air leg should be reported
for that range, with a note of what the applied 0.025 gives, and not for a single point.

### Result

| Item | Value |
|---|---|
| Form | Pure per-mile rate: cost per gallon equals the rate times the one-way statute air miles. The round trip with an empty return is inside the rate. |
| Point | $0.016 per gallon per one-way statute air mile (1.6 cents; $1.60 per gallon per 100 air miles) |
| Range | $0.013 to $0.024. The low end is the November 2007 delivery; the high end is the DEC 2007 point statement. |
| Narrower range for full DC-6 or DC-4 loads over about 180 to 250 miles | $0.013 to $0.019 (the top is the Allakaket ceiling) |
| Fixed part | None ($0) proposed. The one observed charter limits it to between $0 and about $0.5 per gallon. |
| Unit | United States dollars per gallon of fuel per one-way statute air mile, airstrip to airstrip in a straight line |
| Dollar basis | 2026 dollars, CPI-U 332.243 |
| Same charge per gallon | $2.91 per gallon over the model's 181.7-mile Fairbanks to Allakaket route (the applied 0.025 gives $4.54) |
| Source-year figures | The point is midway between two sources of different years, so it has no single source year. Low end: $1.50 per gallon over 183.4 miles, which is 0.82 cents per gallon per mile (2007 dollars). High end: 1.5 cents (2007 dollars). Published point: 1.25 cents (2010 dollars). |
| Outside the figure | Small aircraft (150 to 200 gallons): $0.05 to $0.11 |

Restatement note. Moving from 330.0 to 332.243 does not change the rounded point (0.016; unrounded 0.0161)
or the rounded range ends (0.0131 rounds to 0.013; 0.0240 rounds to 0.024). It moves the last digit of the
working figures: the published point goes from 0.0189 to 0.0190, the transaction from 0.0135 to 0.0136 (range
0.0130 to 0.0140 becomes 0.0131 to 0.0141), the DEC 2007 point from 0.0239 to 0.0240, and the Allakaket ceiling
from $3.45 to $3.68 per gallon to $3.48 to $3.70 per gallon.

Index sensitivity. The marine freight indexes do not apply to air, and the shared files hold no aviation cost
index. The verdict notes that old piston freighters burn a great deal of aviation gasoline, so a 2026
aviation-fuel price well above the general price trend would push the true level toward the top of the range.

### Methods and convergence

| Method | Counted as independent? | Value (2026 dollars) | Source documents with page | How it was checked | Kept or rejected and why |
|---|---|---|---|---|---|
| Published per-mile statements (DEC 2007 and ISER 2010) | Yes (point 1); the two documents count as one method | 0.0190 (ISER 2010). DEC 2007 range 0.0160 to 0.0224, midpoint 0.0192; DEC 2007 point 0.0240 | `components of alaska fuel costs.pdf`, p. 13 (Q1). `cost-assessment-fordiesel-fuel-transition-in-western-and-northern-alaska-communities.pdf`, printed p. 73 (PDF p. 89) (Q2) and printed p. 93 (PDF p. 109) (Q3) | Verifier re-read each passage and redid the arithmetic. For this record every quote was found on the stated page and the figures were recomputed at 332.243. | Kept. These are estimates and authors' statements, not tariffs or invoices, and the two documents may share an industry source. |
| One real delivery: Brooks, Fairbanks to Allakaket, 13 November 2007 | Yes (point 2) | 0.0131 to 0.0141, carried as 0.0136 ($2.40 to $2.56 per gallon) | `Components of Delivered Fuel Prices in Alaska.pdf`, printed p. 60 (PDF p. 66) (Q4, Q5); Table 15, printed p. 54 (PDF p. 60) (Q6) | Verifier re-read the pages and recomputed the distance. For this record the quotes were found, the Table 15 page image was viewed, and the distance scripts were re-run with the same results. | Kept. It is one delivery on one route in one month. |
| Second-round charter build-up (hourly rate times round-trip and ground time, divided by the load) | No | As reported, restated: $0.96 per gallon fixed plus 0.0151 per mile, which is 0.0204 all-in at 181.7 miles (0.0150 and 0.0202 at the 330.0 basis). Calibrated to the hours actually billed it equals the transaction. | Same ISER 2008 pages; web snippets for speeds | Verifier reproduced the formulas and compared the result with the delivery it was built from. | Rejected as a separate method. Its only source input, $2,400 per hour, is from the same delivery. Its central case predicts 44% to 54% more than that delivery cost. It also used the wrong origin node (176.4 miles) and uplifts with no source. |
| Fiscal-year 2025 utility fuel price less a road-system purchase price (second-round revealed prices) | Independent, but a ceiling only | Allakaket: at most $3.48 to $3.70 per gallon, which is at most 0.019 to 0.020. With a $3.60 reference: 0.0147 to 0.0149 | `2026.03.01 FY2025 PCE Statistical Report by Community (Final).pdf`, printed p. 19 and the pages in row 31 below; ISER 2010 p. 65 (Q7) | Verifier checked the price rows and reran the fits. For this record the rows were read again from the decoded table. | Kept as a ceiling. The regression itself carries no information (three villages; the 95% interval on the slope runs from minus 26 to plus 27 cents). |
| Earlier chapter, Method B: DC-6 engineering build-up (0.0126 per mile plus $2.18 per gallon fixed) | Independent in its inputs, but none of them verified | 0.0246 at 182 miles ($4.47 per gallon); 0.0212 at 253 miles; 0.0308 at 120 miles. Stated by the chapter in 2026 dollars; not inflated. | `03_plane.md`, section 4. No supplied document gives its inputs. | Verifier searched the supplied documents for each input and found none; the air fact sheet records the same under "Topic 5, not found". | Not usable as a point. Shown in the spread only for openness. It charges 21% to 29% more than the Allakaket ceiling. |
| Earlier chapter, Methods A, A-prime and C-i: January 2026 retail premiums, a National Park Service charter award, per-pound freight tariffs | Ceilings only | 0.022 to 0.046 as the chapter states them. Re-read on a like-for-like basis: 0.014 to 0.020 and 0.0106 to 0.0167 | Sources are web pages cited in `03_plane.md`; none is among the supplied files | Not re-verified by the verifier or for this record. Only the retail markup used in the re-reading was checked (ISER 2008 printed p. 60). | Ceilings only. Retail premiums include the village retailer's markup; the award is a 1,400-gallon part load; the tariffs are for packaged freight. |
| Earlier chapter, Methods C-ii and A-double-prime: the ISER 2010 statement and the fiscal-year 2025 price regression | No | 0.0190; 0.011 to 0.017 per village with a $3.60 reference | Same sources as the first and fourth rows | Quote and price rows checked as above. | Add no independent evidence: they are the same sources as two rows above. |

Spread. Across the two verified independent points (0.0190 and 0.0136) the ratio of highest to lowest is
1.40, and their geometric mean is 0.0161. If the earlier chapter's assumption-based build-up is counted as a
third point, the ratio is 1.81 (1.82 at the 330.0 basis) and the geometric mean 0.0185. The three published
sub-statements alone (0.0160, 0.0240, 0.0190) span a ratio of 1.50. All are far inside the 3x standard. The
weakness is that the evidence is thin, not that it disagrees: there are two verified point methods where the
standard asks for three, and the transaction and the ceiling share one route.

Ceiling test. The Allakaket ceiling (at most 0.019 to 0.020) is respected by the transaction (0.0136), met
at the limit by ISER 2010 (0.0190), and exceeded by the DEC 2007 point (0.0240), by the earlier chapter's
build-up (0.0246) and by the applied 0.025.

### Derived versus assumed

| # | Input | Value | Type | Reference | What changes if it is wrong |
|---|---|---|---|---|---|
| 1 | ISER 2010 air rate | About $1.25 per gallon per 100 air miles | Quoted | `components of alaska fuel costs.pdf`, p. 13 (Q1) | The published point moves in proportion, and the proposed point by about half as much. |
| 2 | Dollar year of row 1 | 2010 | Assumed (blind analyst; kept by the verifier) | The source says only "current aviation fuel prices"; the report is dated 17 February 2010. | Read as 2009 dollars: 0.0194 in place of 0.0190. |
| 3 | "Air miles" in row 1 are one-way miles | One-way | Assumed (blind analyst, by analogy with the DEC example in Q3) | The source does not say. | Read as miles flown out and back, the one-way figure is 0.0381, which is 1.9 times the top of the Allakaket ceiling. The ceiling argues against that reading. |
| 4 | DEC 2007 range | 1.0 to 1.4 cents per gallon per map mile | Quoted | DEC 2007, printed p. 73 (PDF p. 89) (Q2) | It corroborates row 1 (midpoint 0.0192). Without it the published method rests on ISER 2010 alone. |
| 5 | DEC 2007 point | About 1.5 cents per one-way map mile; 200 miles one way costs about $3.00 per gallon | Quoted | DEC 2007, printed p. 93 (PDF p. 109) (Q3) | It sets the top of the range (0.0240). |
| 6 | Dollar year of rows 4 and 5 | 2007 | Quoted | "In 2007" (Q2); "cost estimates from 2007" (Q3) | Read as 2008: 3.7% lower. The blind analyst listed this year as assumed; the verifier corrected that, and the words were confirmed for this record. |
| 7 | A "map mile" is a straight-line statute mile | Statute mile | Assumed (blind analyst; kept by the verifier) | DEC 2007 does not define the term. | If nautical miles were meant, the rate per statute mile would be lower by the ratio of a nautical mile to a statute mile. |
| 8 | Factors to 2026 | 2007: 1.6024; 2010: 1.5237 | Computed | 332.243 divided by 207.342 and by 218.056 (`index_basis_2026-11-17.md`) | None beyond the index choice in row 9. |
| 9 | Carrying 2007 and 2010 aircraft charges to 2026 by general consumer prices | CPI-U, all items | Owner decision for the index (2026-11-17); that it fits aviation costs is Assumed | `index_basis_2026-11-17.md`; no aviation index is in the shared files | If aviation fuel and old-airframe upkeep have risen faster than consumer prices, the true level is nearer the top of the range. The ceiling checks the level only up to mid-2025. |
| 10 | Brooks landed price | $4.51 per gallon; 3,000 gallons of heating fuel; 13 November 2007 | Quoted | ISER 2008, printed p. 60 (PDF p. 66) (Q4) | The transaction moves cent for cent. |
| 11 | Brooks purchase price | $3.01 per gallon, #1 heating fuel, bought in Fairbanks, November 2007 | Quoted | Same page (Q4) | The transaction moves cent for cent. |
| 12 | Air freight equals landed price minus purchase price | $1.50 per gallon | Computed from rows 10 and 11. That the whole difference is air freight is Assumed (blind analyst; verifier). | Table 15 prints "Price/gal 1.5" in its Air block (Q6). | Any margin Brooks takes on the product is inside the $1.50, so the true freight could be lower. |
| 13 | The "$0.95 per gallon charge for fuel delivery" is not the air charge | Read as the retailer's markup | Assumed: a judgement between two readings (verifier, agreeing with the published-rates analyst) | Q5. Retail $5.50 less landed $4.51 is $0.99. The other reading would need a purchase price of $3.56 against the stated $3.01. | If $0.95 is the air charge, the transaction is 0.0083 and the low end of the range falls to it. |
| 14 | Brooks hourly rate and load | $2,400 per hour; 3,000 gallons | Quoted | ISER 2008, printed p. 60 (Q4) | With row 15 it gives the upper reading of the transaction ($1.60 per gallon). |
| 15 | Flight time to Allakaket | 2 hours | Quoted | ISER 2008, Table 15, printed p. 54 (PDF p. 60) (Q6) | See rows 16 and 17. |
| 16 | The 2 hours is the round trip | Round trip | Assumed (blind analyst; kept by the verifier) | The table does not say. Read as one way it implies about 92 miles per hour. | If it is one way, the hourly reading doubles and no longer agrees with row 12. Row 12 does not depend on it. |
| 17 | The Table 15 air figures are data, not ISER estimates | Printed in upright type | Quoted (the table's own note in Q6; the type style was read from the page image for this record) | `img_iser/p-60.png`. The table marks estimates in italic; the storage-cost rows are italic, the Air block is not, as far as the image resolution shows. | If they are estimates, the $1.60 reading is weaker. The $1.50 is confirmed separately by rows 10 and 11. |
| 18 | The flight starts at Fairbanks | Fairbanks | Quoted for where the fuel is bought (Q4) and for the supply route (Q7). That the aircraft departs from Fairbanks International is Assumed. | ISER 2008 printed p. 60; ISER 2010 p. 65 | A different departure point changes the miles. |
| 19 | One-way distance | 181.7 miles (the model's own air route) to 183.4 miles (straight line between the Fairbanks and Allakaket hub nodes) | Measured | `fuel_network.duckdb`, tables `network_edges` and `network_nodes`; `verify2/plane/airstage.py`, `dist2.py` | About 1% either way. The model's air edges are straight lines, so the source's mile and the model's mile are the same thing. |
| 20 | Transaction rate | 0.82 to 0.88 cents per gallon per mile (2007 dollars); 0.0131 to 0.0141; carried as 0.0136 | Computed | Rows 8 and 10 to 19 | It is the low anchor of the point and the low end of the range. |
| 21 | Everts delivery, 6 November 2007 | 4,462 gallons of gasoline landed at $4.52 per gallon | Quoted | ISER 2008, printed p. 60 (Q4) | Corroboration only. |
| 22 | Everts purchase price and origin | $2.99 per gallon (Brooks's gasoline price); Fairbanks | Assumed (blind analyst) | The source says the Everts price "is not known" (Q4). | It gives 0.0134 to 0.0135, which agrees with row 20 but is not counted as a separate observation. |
| 23 | The point sits midway between the two methods | 0.016 (arithmetic mean 0.0163; geometric mean 0.0161) | Assumed: equal weight (blind analyst; kept by the verifier) | Rows 1 and 20 | The transaction alone gives 0.0136; the published statements alone give 0.0190. |
| 24 | Range ends | Low: the lowest transaction reading. High: the DEC 2007 point. | Assumed: judgement (verifier) | Rows 5 and 20 | A narrower or wider band; the point does not move. |
| 25 | No fixed part | $0 | Assumed: judgement on the evidence (verifier) | Q1 to Q3 quote rates proportional to distance. Brooks billed 1.875 to 2.0 hours for a 363-mile round trip. | The one route allows up to about $0.5 per gallon. Any pure per-mile rate underprices short hops (see Open evidence gaps). |
| 26 | One rate stands for tanker-class aircraft only; small aircraft are left out as negligible by gallons | 3,000 to 5,000 gallons a load | Assumed (verifier) | No source gives the share of flown gallons by aircraft size. ISER 2010 says the price is "even higher for the many villages" that cannot take a DC-6 (Q1). | Villages served by small aircraft pay 0.05 to 0.11, three or more times the proposed rate. |
| 27 | Aircraft type and cruise speed used to bound the billed ground time | DC-4 or C-54; 190 to 227 miles per hour | Assumed: web search snippets, not re-confirmed | Links are in the verdict (`derive2_results.json`). | It affects only the limit on the fixed part ($0.11 to $0.51 per gallon at those speeds). |
| 28 | DC-6 payload | 4,750 gallons (printed pp. 73 and 93); 4,900 gallons in ISER 2010. DEC 2007 printed p. 22 says 2,000 gallons. | Quoted, all three. That p. 22 has the two aircraft the wrong way round is Assumed (verifier). | Q2, Q3, Q1, Q8 | The rates are already per gallon, so the point does not rest on it. If the DEC cost per trip applied to 2,000 gallons, its rate would be 5.71 cents, 2.4 times higher. |
| 29 | Fiscal-year 2025 delivered price, Allakaket and Alatna | $6.19 per gallon (56,927 gallons; $352,162) | Measured | `work/pce/pce_rows.json`, the project's decoded table of the PCE report, printed p. 19 | The ceiling moves cent for cent. |
| 30 | Allakaket was supplied wholly by air from Fairbanks in fiscal year 2025 | Yes | Quoted for 2007 and for 2009 to 2010 (Q4, Q7). For fiscal year 2025 it is Assumed, supported by the model's delivery flag "Plane" (Measured, `network_nodes`). | ISER 2008 printed p. 60; ISER 2010 p. 65 | If some fuel arrived another way, the price gap is not a ceiling on air freight. |
| 31 | Purchase price at the road-system origin | $2.82 per gallon down to $2.65 | $2.82 is Computed: the median of Tok $2.81, Northway $2.96, Minto $2.78 and Slana $2.83 (Measured; printed pp. 169, 123, 108, 153). Choosing those four is Assumed (blind analyst). $2.65 is Assumed (verifier's lower value; no source is named). | `work/pce/pce_rows.json` | With Circle and Central ($3.60) the ceiling is 0.0147 to 0.0149. The reference moves the ceiling between about 0.015 and 0.020. |
| 32 | Factor from fiscal year 2025 to 2026 | 1.0320 (calendar 2025, 11 months) to 1.0454 (mid-fiscal-year index 317.816) | Computed; which of the two applies is Assumed | `index_basis_2026-11-17.md` | 1.3%. |
| 33 | Allakaket ceiling | At most $3.48 to $3.70 per gallon; at most 0.019 to 0.020 | Computed | Rows 19 and 29 to 32 | It is not an input to the point. It narrows the range for full DC-6 loads and is the main test that the applied 0.025 fails. |

Quoted passages (exact words; each was found on the stated page for this record):

- **Q1.** ISER 2010, p. 13: "With current aviation fuel prices, the most competitive air deliveries have a
  transportation component of ~$1.25 per gallon per hundred air miles. The price is even higher for the many
  villages with airports unable to accommodate the 4,900 gallon DC-6 transport planes operated by Everts Air
  Cargo."
- **Q2.** DEC 2007, printed p. 73: "fuel deliveries may be made by air, typically via a DC-6 fuel tanker with
  a capacity of 4,750 gallons. In 2007, the cost for delivery via air is estimated to be 1.0-1.4 cents per
  gallon per map mile of air transport from the fuel hub or up to $1.40 per gallon air delivery of 100 miles."
  Footnote 8: "MAFA Analysis of Small Air Fuel Delivery Service Cost Estimates."
- **Q3.** DEC 2007, printed p. 93: "Based on project interviews and cost estimates from 2007, the estimated
  cost of fuel delivered by DC-6 is somewhere in the range of 1.5 cents per one-way map mile. A 200-mile
  one-way delivery (400-mile round trip) would cost about $3.00 per gallon for air delivery on top of the
  price of fuel delivered to the air tanker."
- **Q4.** ISER 2008, printed p. 60: "Fuel is pumped directly from the plane into the communities' fuel tanks.
  [...] Brooks Air is capable of flying 3,000 gallons of heating fuel, or 3,300 gallons of gasoline, at a rate
  of $2,400 per hour. [...] Brooks Fuel purchases its fuel from Alaska Aero Fuel in Fairbanks. As of November
  2007, the company paid $3.01 per gallon for #1 heating fuel. On November 13, 2007 Brooks Fuel delivered
  3,000 gallons of heating fuel at a landed price of $4.51 per gallon. [...] Everts Air delivered 4,462
  gallons of gasoline on November 6 at a landed price of $4.52 per gallon. This gasoline retailed at $6.00 per
  gallon. The price at which Everts Air purchased its gasoline is not known, but Brooks Fuel reports
  purchasing its gasoline from Alaska Aero fuel at $2.99 per gallon."
- **Q5.** ISER 2008, printed p. 60: "The retail price for this fuel was $5.50, with a reported $40 per barrel,
  or $0.95 per gallon, charge for fuel delivery."
- **Q6.** ISER 2008, Table 15, printed p. 54, column "Allakakat & Alatna", block "Air": Runway "Long";
  "Flight time (hours)" 2; "Price/gal" 1.5. Table note: "Italic = estimate".
- **Q7.** ISER 2010, p. 65: "Both communities receive their fuel by airplane (from Fairbanks), because fuel
  barges cannot navigate the upper Koyukuk River."
- **Q8.** DEC 2007, printed p. 22 (PDF p. 38): "The company operates DC-6 and C-46 aircrafts that can carry
  2,000 and 5,000 gallons of fuel, respectively."
- **Q9.** DEC 2007, printed p. 73: "Rather than incurring an upfront cost associated with tank cleaning, it is
  much more likely that air transport companies would clean tanks as a regular, recurring expense. These costs
  would be integrated into the rates charged to their customers."

Which assumptions carry the most weight. Four decide the level. First, reading ISER 2010's "air miles" as
one-way miles (row 3): the other reading would double the published point, although the ceiling argues
against it. Second, treating landed price minus purchase price as the air freight and setting aside the
"$0.95 per gallon" wording (rows 12 and 13): the other reading would put the only real transaction at about
half the published statements. Third, giving the published statements and the single transaction equal weight
(row 23): the point is a judgement between 0.0136 and 0.0190, not a measurement. Fourth, carrying 2007 and
2010 aircraft charges to 2026 by general consumer prices (row 9). Two more decide what the figure stands for
and not its level: that tanker-class aircraft carry nearly all flown gallons (row 26) and that there is no
fixed part (row 25). The case against the applied 0.025 leans on the reference price in row 31; with the
highest reference considered ($3.60) the ceiling is lower still, so that choice does not rescue 0.025.

### What the figure includes and excludes

Inside the rate (by the sources' own wording):

- Aircraft time both ways. The 2 flight hours cover the leg out and the empty return, and DEC 2007 prices 200
  miles one way as a 400-mile round trip (Q3).
- Loading at the origin and pumping off into the village tank. The Allakaket figure is a landed price, and
  "Fuel is pumped directly from the plane into the communities' fuel tanks" (Q4).
- The carrier's margin. These are prices charged, not costs.
- Tank cleaning between products, which DEC 2007 says is "integrated into the rates charged" (Q9).

Outside the rate:

- The fuel itself and getting it to the aircraft: "on top of the price of fuel delivered to the air tanker"
  (Q3).
- Storage at the origin terminal.
- The village tank farm ($0.55 per gallon of throughput at Allakaket, Table 15) and the village retailer's
  markup ($0.99 to $1.48 per gallon in 2007 dollars, which is $1.59 to $2.37 in 2026 dollars).
- Local truck delivery and taxes.

So that no handling is billed twice:

- The plane-to-overland transfer fee must not bill aircraft loading, pump-off, crew, standby or tank cleaning;
  all of these are inside the rate. The only handling without a home is the road side of a truck-to-aircraft
  handoff at the origin ramp. The applied fee of $0.025 per gallon (range $0.015 to $0.045) is described that
  way and can stay. The sources hold no figure for it, so its size is not verified; that fee is treated in the
  transfer-fee addendum. It is a per-gallon fee and only by coincidence has the same digits as the applied
  per-mile rate.
- At the village no second fee is due, because the sources show the plane pumping straight into the tank.
- The two barge-to-air transfer edges are priced as barge-to-overland and contain no aircraft handling.
- No fixed air fee is proposed. If a two-part form were adopted later, the per-mile rate would have to fall to
  its variable part and the fee be charged exactly once per air route. The network cannot do that today: of 83
  air terminals, 78 join the road at a shared node with no transfer edge, and only 2 air-to-road transfer
  edges exist (re-run for this record, same counts).
- Do not derive the Plane rate from utility or retail price premiums. They contain storage and markup, which
  is why they serve here only as ceilings.

### Compared with the applied value and the earlier chapter

Applied today: Plane 0.025, range 0.015 to 0.042 (`friction_costs.py`). The earlier chapter (`03_plane.md`)
concluded 0.025 at medium-high confidence and preferred a two-part form of 0.0126 per mile plus $2.20 per
gallon per delivery.

The verdict **overturns the applied point**, moving it down 36% to 0.016, and **rejects the two-part form**.
It keeps the order of magnitude and the ordering of modes: plane stays the dearest mode, at 1.6 times the
ice-road rate in place of 2.5 times. The proposed point lies inside the applied range, near its bottom; the
top of the proposed range (0.024) lies just below the applied point. This is the judgement of one verifier and
has not had a second independent review.

What is confirmed from the earlier chapter: the ISER 2010 statement, word for word (0.0190); the chapter's own
full-load figures of 0.011 to 0.022, which already sat below its 0.025 point; and plane as the dearest mode.

What is changed, and why:

- Two documents are new since the chapter: DEC 2007 and ISER 2008. Every statement in them, and the one real
  delivery, falls below 0.025 after inflation; the highest is 0.0240.
- The applied rate charges more than a ceiling from the same year's prices. It charges $4.54 per gallon to
  Allakaket against a ceiling of $3.48 to $3.70 (23% to 31% above). It charges $6.34 per gallon to Anaktuvuk
  Pass, where the whole delivered price, fuel included, was $6.38 in fiscal year 2025 ($6.58 to $6.67 in 2026
  dollars). It charges $5.14 per gallon to Hughes, where the whole delivered price was $4.94 ($5.10 to $5.16
  in 2026 dollars).
- The verdict traces 0.025 to an average of full-load figures with a 1,400-gallon part-load charter, retail
  premiums with too small a markup deduction, and packaged-freight tariffs. None of those measures bulk
  freight to a village.
- The $2.20 fixed part is not supported. The two-part form predicts $4.47 per gallon to Allakaket; the actual
  2007 delivery is $2.40 to $2.56 in 2026 dollars.
- Confidence should be medium, not medium-high.

If the owner decides to apply the proposal, these change together in one edit: the rate; the range in
`BASELINE_RATE_RANGES["Plane"]`; the provenance comment; the "(0.025)" reference in the plane-to-overland fee
comment; and the plane block of the toolkit self-test. That block's lower limit is 0.0229 (the charter award
divided by 1,400 gallons and by 350 miles, less 5%), which 0.016 would fail. It has to be re-documented from
the new derivation, not loosened. The verdict also notes that this block divides a full delivered price, fuel
included, by distance, so it would pass any rate from 0.023 to 0.065 and is not a test of the freight rate.

The proposal rests on the evidence about air freight alone. The audit of the outside report found two coastal
villages the model reaches only by air (Shaktoolik and Savoonga). That is a gap in the network's barge links
and is no reason to move the air rate in either direction.

### Open evidence gaps

Each item names the kind of document that would help.

- **A third independent point (would raise the level to Derived).** A current charter quotation, rate sheet
  or paid invoice from an air-fuel carrier for a named route and load, for example Fairbanks to Anaktuvuk
  Pass with 4,000 gallons. The owner has said they will look for current plane charter prices.
- **A second route.** A fuel purchase order or freight invoice from a village utility that is supplied by
  air, showing freight separately from product: Alaska Power and Telephone for Allakaket, the North Slope
  Borough for Anaktuvuk Pass, or Alaska Village Electric Cooperative for Noatak with the origin airport
  named. Noatak's origin (Anchorage or Kotzebue) decides whether its $9.41 per gallon implies about 1.0 to
  1.2 cents per mile or a large fixed part.
- **How Anaktuvuk Pass and Hughes were supplied in fiscal year 2025.** A borough fuel contract or utility
  record stating the mode. If Anaktuvuk Pass was all by air, its ceiling (0.0145 to 0.0154) would pull the
  top of the range down to about 0.015 to 0.019.
- **Short hops.** No source shows an air delivery below $1.00 per gallon in 2007 to 2008 dollars ($1.54 to
  $1.60 today), even at 15 miles. A third of the model's 76 air routes are under 75 miles; the shortest, Bethel
  to Napaskiak at 5.6 miles, costs $0.09 per gallon at 0.016. A carrier's minimum charge or per-flight fee
  schedule would size a floor. Billing one would also need a transfer edge at every air terminal.
- **An aviation cost series.** A price series for aviation gasoline or an air-freight cost index from 2007 to
  2026, to replace general consumer prices in row 9.
- **A Fairbanks wholesale price for fiscal year 2025.** A rack price series would fix the reference in row 31
  and so the ceiling.
- **Small aircraft.** More than one operator's hourly rate with route and load. Today there are two points
  from two operators: 5.5 cents per gallon per mile over 62 miles and 10.7 cents over 15 miles.
- **The earlier chapter's web sources as files.** The January 2026 fuel price survey, the federal charter
  award record and the carriers' tariff pages, saved as documents, so that those figures can be re-verified.

Not re-confirmed for this record (repeated from the working files, not checked against a document):

- The web search snippets on aircraft: tank capacities of the C-46 and DC-6, that Brooks Fuel flew DC-4 or
  C-54 aircraft, and DC-4 cruise speeds of 190 to 227 miles per hour.
- The earlier chapter's inputs: the January 2026 survey prices, the National Park Service award ($11,792.50
  for 1,400 gallons over 143 miles), the per-pound tariffs, every input of the DC-6 build-up, and the Hughes
  price of $6.41 for fiscal year 2024.
- The supply mode of Anaktuvuk Pass and Hughes in fiscal year 2025.
- The printed page number of the Noatak quotation (found on PDF p. 2; the text has no printed number).

Public links. ISER 2008: https://scholarworks.alaska.edu/cgi/viewcontent.cgi?article=1348&context=uaa_iser_reports
(`DOWNLOAD_LIST.md`, item 2; that list says its links were not opened). ISER 2010:
https://iseralaska.org/static/legacy_publication_links/componentsoffuel3.pdf (earlier chapter). DEC 2007:
`DOWNLOAD_LIST.md` has no direct link and suggests looking under
https://dec.alaska.gov/air/anpms/ultra-low-sulfur-diesel/rural-economic-summary/. Local copies: ISER 2010, the
PCE report and the Noatak document are in the harness under `cost_derivation_resources/` on main; DEC 2007 and
ISER 2008 are on branch `cost-sources`.

### Working files

All under `harness: blind_derivations/working_2026-11-17/`.

- `derive2_results.json`: the verdict (`verdicts.plane`) and the three second-round blind derivations
  (`derivations.plane-published-rates`, `plane-charter-buildup`, `plane-revealed-prices`).
- `derive2/plane_published/calc.py`, `derive2/plane_buildup/build.py`, `derive2/plane_revealed/air.py` and
  `out.txt`: the blind analysts' scripts and output.
- `verify2/plane/verify.py`, `dist.py`, `dist2.py`, `airtopo.py`, `airstage.py`: the verifier's scripts
  (figures at the 330.0 basis).
- `record/plane_checks/restate_plane_332243.py` and `restate_plane_332243_output.txt`: every inflated figure
  recomputed at 332.243 beside its 330.0 value. Re-run for this record with identical output.
- `record/plane_checks/second_pass_checks.py` and `second_pass_checks_output.txt`: each quoted passage found
  in the full text with its PDF page and printed page; the price rows used; the few restated figures the first
  script does not print.
- `record/plane_checks/verify_py_output_330basis.txt`, `airstage_rerun_output.txt`, `airtopo_rerun_output.txt`,
  `dist2_rerun_output.txt`, `network_facts_check.py` and its output: re-runs of the verifier's scripts and of
  the network counts. `quote_confirmation_output.txt` and `find_quote_page.py`: the first quote search.
- `img_iser/p-60.png`: page image of ISER 2008 Table 15.
- `work/pce/pce_rows.json`: the decoded fiscal-year 2025 price table.
- `extracts/local_air_road_winter.md` (Topic 5), `extracts/dec_2007.md`, `extracts/iser_2008.md`: fact sheets.
- `pdf_text/`: full text of DEC 2007, ISER 2008, ISER 2010, the PCE report and the Noatak document.
- `shared/index_basis_2026-11-17.md`: the index basis.
