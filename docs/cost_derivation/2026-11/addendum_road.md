## Addendum 2026-11-17: Road tanker trucking (proposal; nothing applied)

Segment: a highway tank truck carrying a full bulk load between a refinery or terminal and a road-system
community, priced per gallon per statute mile of the model's road route. Nothing in this addendum has been
applied to `friction_costs.py`, and for this segment nothing needs to change. All 2026 figures are in 2026
dollars at CPI-U 332.243 (`index_basis_2026-11-17.md`). The working files used 330.0; every inflated figure
below was recomputed from its source-year value, and the text says where the rounded value differs from the
working files. The verdict summarised here comes from one adversarial verifier and has not had a second
independent review. It confirms the applied Road rate; it does not overturn it.

Short names used below. **Econ One** is the December 2016 slide deck "The State of Alaska's Refining Industry"
by Barry Pulliam of Econ One; its labels are in "cpg", read as cents per gallon. **ATRI** is the American
Transportation Research Institute, whose 2025 survey of trucking costs covers the contiguous United States.
**ISER 2010** and **ISER 2008** are the reports "Components of Alaska Fuel Costs" (February 2010) and "Components
of Delivered Fuel Prices in Alaska" (June 2008) by the Institute of Social and Economic Research, University of
Alaska Anchorage. **DEC** is the Alaska Department of Environmental Conservation. **PCE** is the Power Cost
Equalization program; its report for fiscal year 2025 (FY2025, July 2024 to June 2025) gives each utility's fuel
price. FY27 is the State fiscal year from July 2026 to June 2027. **CPI-U** is the consumer price index for all
urban consumers. A bare number such as 0.00076 in a table is a rate in dollars per gallon per statute mile unless
the cell gives another unit.

### Status

**Headline status for the rate as it would be applied: Derived.** Detail follows.

**Level: Derived, with one of the three methods not re-opened in this round.** Three methods of different kinds
(a published charge for a bulk truck leg, an operating-cost build-up, and the price gradient in a State fuel
contract) give $0.00067 to $0.00085 per gallon per statute mile, a spread of about 1.3 against the 3x standard.
Two of the three were checked against the supplied documents in this round. The third, the State heating-oil
contract gradient, is carried on the earlier chapter's record of a page-by-page read on 2026-07-15, because
that contract is not among the supplied files. The build-up also rests on an assumed tank payload that no
supplied document states; across the whole payload range considered the spread stays under 1.8.

**Fixed truck-side part (the truck's own loading and unloading time): Provisional.** One published point and
one published ceiling together limit it to between $0 and about $0.03 per gallon. The central value of about
$0.02 per gallon is the verifier's judgement inside those limits, not a derived figure. It is not proposed as
a new charge.

**What the model should carry meanwhile.** Keep what is applied: $0.0007 per gallon per statute mile on road
edges and on the connector edges that take the Road rate, with the range $0.00045 to $0.0011. A result that turns on a road-only route can be
reported with the note that the route carries no truck-side handling, an under-count of at most $0.03 per
gallon.

### Result

| Item | Value |
|---|---|
| Form | Pure per-mile carriage rate, charged on the model's statute road miles. No fixed part inside the rate. |
| Point | $0.0007 per gallon per statute mile (unchanged from the applied value) |
| Range on the evidence checked in this round | $0.00055 to $0.0011 per gallon per statute mile |
| Range the verdict says can stay | $0.00045 to $0.0011 (the applied band; its low end rests on the contract gradient, which was not re-opened) |
| Fixed part | About $0.02 per gallon per truck haul (range $0 to $0.03), kept out of the rate and not added as a new charge. The existing road-incident transfer fees already bill it. |
| All-in equivalent, if no fixed part is billed anywhere | $0.00076 per gallon per statute mile at about 360 miles |
| Unit | United States dollars per gallon of fuel per statute mile of model road route |
| Dollar basis | 2026 dollars, CPI-U 332.243 |
| Same charge per gallon | $0.25 per gallon at 364 statute miles; with $0.02 of handling, $0.275 against $0.277 observed on the published leg |
| Source-year figures | The point does not come from one dated source. Published leg: $0.20 per gallon (2016 slide), which is $0.00055 per gallon per statute mile over 364 miles. Build-up: $4.001 of revenue per truck mile (2024). Contract gradient: $0.00067 per gallon per statute mile from fees effective 1 July 2026, which are 2026 actuals and are not inflated. |

Restatement note. Moving from 330.0 to 332.243 does not change the rounded point ($0.0007), the rounded range
ends ($0.00055 and $0.0011) or the published-leg figure ($0.00076). It does move the last digit of several
working figures. The main ones: the corrected build-up point goes from $0.00084 to $0.00085, the Nenana ceiling
as a per-mile rate from $0.00110 to $0.00111, the smallest slope a two-part form allows from $0.00067 to
$0.00068, and the geometric mean of the three points from $0.00075 to $0.00076. Others are noted where they
appear.

Index sensitivity. The marine freight indexes do not apply to road. The verdict gives a trucking-cost
sensitivity in their place: if the published leg is carried from 2016 to 2024 by the trucking survey's own
cost-per-mile series ($1.592 to $2.260 per mile, a factor of 1.420) and then to 2026 by CPI-U, it is $0.00083
per gallon per statute mile ($0.00082 at the 330.0 basis), 8% to 9% above the CPI-U figure.

### Methods and convergence

Values are in dollars per gallon per statute mile, 2026 dollars at CPI-U 332.243, unless a per-gallon figure is
stated. "PDF p." is the page of the PDF file; "printed p." is the number printed on the page.

| Method | Counted as independent? | Value (2026 dollars) | Source documents with page | How it was checked | Kept or rejected and why |
|---|---|---|---|---|---|
| Published bulk truck leg: Econ One, 20 cents per gallon over 364 miles | Yes (point 1) | 0.00076 (0.00074 to 0.00080 across endpoint and dollar-year readings) | `6_barry_pulliam-_econ_one_-_the_state_of_alaskas_refining_industry.pdf`, slide 15; date on slide 1 | Verifier rendered the slide and recomputed four network distances. For this record the image was viewed again, the labels were found in the text layer of slide 15, and the distance script was re-run with identical output. | Kept as a point estimate. Read from a map image; unit, dollar year, payload and endpoints are not stated. |
| Operating-cost build-up: ATRI tank-carrier revenue per mile, doubled for the empty return, divided by a 10,000-gallon load | Yes (point 2) | 0.00085 (0.00065 at 13,000 gallons to 0.00116 at 7,300 gallons); 0.00084 at the 330.0 basis | `ATRI-Operational-Costs-of-Trucking-07-2025.pdf`, Figure 27, printed p. 53 (PDF p. 56); printed p. 44 (PDF p. 47); Figure 22, printed p. 45 (PDF p. 48) | Verifier rendered both figures and read the tables. For this record both images were viewed again and the text quotes were found on the stated pages. | Kept as a corrected point, low confidence. The payload is assumed and the survey has no Alaska content. |
| State heating-oil contract, FY27 fees against distance, 11 locations (earlier chapter, Method C) | Yes (point 3), not re-opened | 0.00067 (specification band 0.00044 to 0.00083); intercept $0.267 per gallon; not inflated | `08-heating-oil.pdf`, Table A. Not among the supplied files. Link in the earlier chapter. | Not checked in this round by the verifier or for this record. Carried on the earlier chapter's record of a page-by-page read on 2026-07-15. | Kept. It is independent of the other two. It is a marginal slope, so it compares with the carriage-only rate. |
| Second-round blind "published legs" headline | No | 0.0011 as reported | Econ One slide 15; ISER 2010 PDF p. 17; ISER 2008 PDF p. 68 | Verifier reran the fit and re-read the three sources. | Rejected. It is a line through the origin over three unlike observations: it treats the Nenana "less than" as an equality and includes the Chitina home-delivery charge. |
| Second-round blind build-up as reported | No | 0.00128 per mile plus $0.053 per gallon fixed (0.00127 plus $0.053 at the 330.0 basis) | ATRI Tables 8 and 9, printed pp. 15-16 (PDF pp. 18-19), and the pages above | Verifier reproduced the arithmetic from the script; the three cases were rerun for this record. | Rejected on four counts: a 7,300-gallon payload from a lower-48 weight limit; it breaks both Alaska observations (see Bounds); unsourced Alaska uplifts and a $5.00 diesel price; it missed the tanker dwell figure in Figure 22. |
| ISER 2010, North Pole to Nenana, "less than $0.05 per gallon" | No (ceiling) | Total trucking cost below $0.076 per gallon over 68.7 miles; below 0.00111 if read as a pure per-mile rate | `components of alaska fuel costs.pdf`, PDF p. 17; route also PDF p. 15 | Quote found on PDF p. 17 for this record; distance re-run. | Ceiling only. It is an inequality and the authors' own estimate. |
| ISER 2008, Anchorage to Chitina delivery charge | No (ceiling for a different service) | $0.40 to $0.48 per gallon, which is 0.00165 to 0.00198 over 243.2 miles | `Components of Delivered Fuel Prices in Alaska.pdf`, printed p. 62 (PDF p. 68); Table 15, printed p. 54 (PDF p. 60) | Quotes found on PDF p. 68 for this record. | Ceiling only. It is small-lot heating fuel delivered to homes, not bulk line-haul. |
| ISER 2008 Table 10, State contract delivery charges | No | Per-leg 0.00020, 0.00099 and 0.00091; three-point slope 0.0011 with intercept minus $0.04 per gallon | Same document, printed p. 27 (PDF p. 33) | Table and the sentence on the negative Anchorage figure found on PDF p. 33. | Not usable. The figures are bid differences against an index price, not freight. |
| FY2025 utility fuel prices against road miles, ten communities (second-round blind) | No (ceiling) | No slope identified: plus 0.015 cents per gallon-mile, 95% interval minus 0.52 to plus 0.55. Ceiling about $0.008. | `2026.03.01 FY2025 PCE Statistical Report by Community (Final).pdf`, as decoded in `shared/pce_prices_with_distances.csv` | The ten rows were matched in the price table and the regression was rerun for this record on the verifier's distances. | Ceiling only, about ten times any cost-based figure. |
| Earlier chapter Method A (DEC report citing Econ One, Valdez to Fairbanks) | No. Same study as point 1. | 0.00077 on a 2015 dollar basis | DEC Fairbanks cost analysis, p. 15. Not among the supplied files. | Not re-opened. The slide behind it was checked as point 1. | Counted once with point 1. |
| Earlier chapter Method B ($3.00 per mile times 1.9, divided by 10,500 gallons) | No. Same survey as point 2. | 0.00054 as written; 0.00077 when the $3.00 is replaced by ATRI tank-carrier revenue (0.00076 at the 330.0 basis) | ATRI Figure 27 and Table 11, printed p. 17 (PDF p. 20) | Verifier's substitution, reproduced for this record. | Not usable as written; biased low. Corrected, it joins point 2. |
| Port of Alaska assessment, federal benefit-cost truck cost | No. Cross-check inside the build-up class. | $2.53 per truck mile against ATRI's all-sector $2.39. The $2.53 is $2.23 in 2022 dollars, computed from the assessment's $1.32 per mile of operating cost, $33.50 per driver hour at 45 mph and $0.1644 per mile of maintenance; the assessment does not print the sum, and its table on PDF p. 83 is headed "Costs (2022 US$)". | `POA Economic Assessment_202405013.pdf`, PDF pp. 83 and 85 | Quotes found on both pages for this record. | Cross-check only. Container trucks, not tankers. |

Spread. Across the three independent points (0.00067, 0.00076, 0.00085) the ratio of highest to lowest is 1.27
and the geometric mean is 0.00076. The verdict states 1.25 and 0.00075 at the 330.0 basis. Across the two
points checked in this round the ratio is 1.11. The standard is agreement within about 3x across three
independent methods of different kinds, and this segment meets it with room to spare. It still holds if the
build-up is taken at either end of its payload range (ratios 1.17 and 1.73) or is left uncorrected at the
second-round figure (1.90).

One difference between the verdict and its saved script is recorded here and not resolved. The verdict text
takes the build-up point at a 10,000-gallon load (0.00084 at the 330.0 basis). The saved script
`verify2/road/verify.py` computes its convergence sets at 9,500 gallons (0.00089), which gives a spread of 1.32
and a geometric mean of 0.00077 for three points, and 1.17 for two. Both readings are far inside 3x and neither
changes the conclusion.

Bounds. The Nenana ceiling ($0.076 per gallon over 68.7 miles) is respected by $0.0007 alone ($0.048), by
$0.0008 alone ($0.055) and by $0.0007 with $0.02 of handling ($0.068). The second-round build-up breaks it in
its central case ($0.141) and its high case ($0.213), and prices the Econ One leg at $0.52 against $0.277
observed; only its low case complies ($0.070 and $0.262). The price-regression ceiling and the Chitina
small-lot ceiling are respected by every estimate.

Form. The Econ One point and the Nenana ceiling together allow a slope of at least 0.00068 and a fixed part of
at most $0.03 per gallon ($0.0295 computed; $0.029 at the 330.0 basis). The contract gradient is a marginal
slope; the other two points are all-in averages at about 360 miles. The gap between the two forms is at most
$0.03 over 364 miles, which is $0.00008 per gallon per statute mile, so the three can be compared.

### Derived versus assumed

| # | Input | Value | Type | Reference | What changes if it is wrong |
|---|---|---|---|---|---|
| 1 | Econ One truck charge | 20 cpg, on the green "Via Truck" line | Quoted (read from a map image) | Econ One, slide 15; passage Q1 | Point 1 moves in proportion. |
| 2 | Econ One deck date | December 2016 | Quoted | Econ One, slide 1: "Anchorage, Alaska December 2016" | Sets the dollar year assumed in input 22. |
| 3 | ATRI tank-carrier revenue | $4.001 per truck mile, 2024 | Quoted (chart image) | ATRI, Figure 27, printed p. 53 (PDF p. 56); passage Q2 | Point 2 moves in proportion. |
| 4 | ATRI per-mile figures are per total mile, empty miles included | "total cost divided by total mileage" | Quoted | ATRI, printed p. 44 (PDF p. 47); passage Q3 | If revenue were per loaded mile, the doubling in input 25 would be wrong and point 2 would halve. |
| 5 | ATRI tank-carrier empty mileage | 43.8 percent | Quoted | Same page; passage Q3 | Used for the low end of the range and for input 25's alternative. |
| 6 | ATRI tanker dwell time | 1.52 hours per stop in 2024 | Quoted (chart image) | ATRI, Figure 22, printed p. 45 (PDF p. 48) | Supports reading revenue per mile as already covering loading and unloading time (input 26). |
| 7 | ISER 2010 trucking cost, North Pole to Nenana | "less than $0.05 per gallon" | Quoted | `components of alaska fuel costs.pdf`, PDF p. 17; passage Q4 | It sets the top of the range and the limit on the fixed part. |
| 8 | ISER 2008 on the structure of trucking cost | "most of the delivery costs are fixed" | Quoted | ISER 2008, printed p. 23 (PDF p. 29); passage Q5 | Form only. |
| 9 | ISER 2008 Chitina delivery charge | $0.25 to $0.30 per gallon, November 2007 | Quoted | ISER 2008, printed p. 62 (PDF p. 68); passage Q6 | Used only as a ceiling and to size the small-drop premium kept out of the rate. |
| 10 | State contract FY27 management fees, 11 locations | $0.2432 (Willow) to $0.4695 (Delta Junction) per gallon | Quoted in the earlier chapter; not re-confirmed | `08-heating-oil.pdf`, Table A, as transcribed in `01_road.md`, section 3, Method C | Point 3 rests on it. Without point 3 there are two independent points. |
| 11 | Network road miles | North Pole to Nenana 68.7; Fairbanks to Valdez 362.3; North Pole to Valdez 348.6; North Pole to Anchorage 375.6; Fairbanks to Anchorage 362.0; Anchorage to Chitina 243.2 | Measured | Harness `fuel_network.duckdb`, tables `network_nodes` and `network_edges` (Road and RoadConnector edges), shortest path; `verify2/road/dist.json` | The Nenana ceiling per mile changes inversely. Distances change if the network is re-exported. |
| 12 | FY2025 utility fuel prices and gallons, ten road communities | $2.78 to $4.05 per gallon | Measured | `shared/pce_prices_with_distances.csv` (decoded from the FY2025 PCE report) | Affects the price-regression ceiling only. |
| 13 | CPI-U factors to 2026 | 2016: 1.3843; 2015: 1.4018; 2010: 1.5237; 2007: 1.6024; 2024: 1.0591; 2025: 1.0320 | Computed | 332.243 divided by the annual averages in `index_basis_2026-11-17.md` | See inputs 38 and 39. |
| 14 | Point 1 per mile | 0.000761 | Computed | $0.20 times 1.3843 = $0.2769 per gallon, divided by 364 miles | Follows inputs 1 and 20 to 23. |
| 15 | Point 2 per mile | 0.000848 | Computed | $4.001 times 1.0591 = $4.238 per truck mile; times 2 = $8.475 per loaded mile; divided by 10,000 gallons | Follows inputs 3, 4 and 24 to 27. |
| 16 | Nenana ceiling | $0.0762 per gallon; 0.00111 as a pure per-mile rate | Computed | $0.05 times 1.5237; divided by 68.7 miles | Follows inputs 7, 11, 29 and 30. |
| 17 | Limits on a two-part form | Slope at least 0.00068; fixed part at most $0.0295 per gallon | Computed | ($0.2769 minus $0.0762) divided by (364 minus 68.7) miles; $0.2769 minus 364 times that slope | Follows inputs 14 and 16. |
| 18 | Point 3: contract gradient | Slope 0.000672; intercept $0.267 per gallon; fit quality (R squared) about 0.75 | Computed in the earlier chapter; not re-run | Least-squares line through input 10 on the distances of input 31 | Follows inputs 10, 31 and 32. |
| 19 | Small-drop premium at Chitina | About $0.27 per gallon | Computed | $0.275 times 1.6024 = $0.441, less $0.0007 times 243.2 miles | It is kept out of the rate. It matches the contract intercept of input 18. |
| 20 | Length of the Econ One truck leg | 364 statute miles | Assumed | Earlier chapter (Valdez to Fairbanks, from its reading of the DEC report, which is not among the supplied files); kept by the verifier. The slide draws the endpoints and does not name them. | Network readings of 348.6 to 375.6 miles give 0.00074 to 0.00080. |
| 21 | "cpg" means cents per gallon | Cents per gallon | Assumed | Both analysts and the verifier; the slide does not define it | If it is another unit, point 1 is void. |
| 22 | Econ One dollar year | 2016 | Assumed | Verifier (the earlier chapter used 2015, following the DEC citation) | A 2015 basis gives 0.00077 (1.3% higher). |
| 23 | The Econ One charge is all-in for a full bulk load | Carriage plus the truck's own loading and unloading time | Assumed | Verifier; the slide states no scope and no payload | If it is carriage only, the carriage-only rate is nearer 0.00076 than 0.0007. |
| 24 | Tank payload | 10,000 gallons | Assumed | Verifier, from web search snippets that were not opened and the trade article cited in the earlier chapter. No supplied document states a payload. | 7,300 gallons gives 0.00116; 13,000 gallons gives 0.00065. |
| 25 | The truck returns empty | Loaded miles are half of total miles | Assumed | Second-round analyst and verifier (the network prices each loaded mile one way) | At ATRI's average empty share (43.8 percent) the 10,000-gallon figure is 0.00075. |
| 26 | Revenue per mile, not marginal cost, is the basis for a charged rate, and it already covers dwell time | $4.001, not the 61.7 percent that is marginal cost | Assumed | Verifier | On marginal cost alone the build-up would be lower and would not be a charged rate. |
| 27 | No Alaska uplift on the contiguous-US survey | Factor 1.0 | Assumed | Verifier (the second round's uplifts of 1.10 to 1.5 were rejected as unsourced) | Any real Alaska premium raises point 2 in proportion. |
| 28 | The survey's "Tanker" sector stands for bulk fuel haulers | All tank carriers, whatever the cargo | Assumed | Implicit in the method; the survey does not split tank carriers by cargo, and the verdict does not discuss it | If fuel haulers earn more or less per mile than the tank average, point 2 moves in proportion. |
| 29 | ISER 2010 dollar year | 2010 | Assumed | Verifier; the report is dated February 17, 2010 and states no year | A 2009 basis gives $0.0774 per gallon. |
| 30 | The Nenana figure covers the whole trucking process | Loading, haul and unloading together | Assumed (reading) | Verifier, from "This is a straightforward process" | If it covers the haul only, it does not limit the fixed part. |
| 31 | Contract gradient distances and supply point | Highway mileposts, 70 to 338 miles from Anchorage; Delta Junction taken as supplied from Anchorage | Assumed | Earlier chapter, section 2, step 9 ("stated as assumptions") | Specification band 0.00044 to 0.00083; the cross-check from the Fairbanks side gives 0.00060. |
| 32 | Contract gradient point selection | 11 rows of one vendor and one award; flat-zone, Kenai, small-drop and remote rows left out; Willow kept | Assumed | Earlier chapter | Dropping Willow gives 0.00044; the three-point version gives 0.00083. |
| 33 | Which methods count as independent | Three: published leg, build-up, contract gradient | Assumed | Verifier | If the contract gradient is set aside, two points remain and the level would be Provisional. |
| 34 | The Chitina charge is a ceiling for another service, not a line-haul point | Ceiling | Assumed (judgement between two readings) | Verifier (the second-round analyst used it as a point) | Counted as a point, it produced the rejected 0.0011. |
| 35 | Point kept at 0.0007 as a carriage-only rate | Between the smallest allowed slope (0.00068) and the all-in figure (0.00076) | Assumed | Verifier; the earlier chapter chose the same value | The all-in alternative is 0.00076, and the geometric mean of the three points is 0.00076. |
| 36 | Fixed truck-side part | About $0.02 per gallon (range $0 to $0.03) | Assumed | Verifier, inside the limits of input 17 | Road-only routes carry none of it: an under-count of at most $0.03 per gallon. |
| 37 | Range ends | Low 0.00055; high 0.0011 | Assumed | Verifier. Low: a 13,000-gallon load at ATRI revenue with average empty share (0.00058), rounded down. High: the Nenana ceiling (0.00111) and the 7,300-gallon case (0.00116). | The applied low end of 0.00045 rests on the contract specification band (0.00044), which was not re-opened. |
| 38 | Inflation by CPI-U, not a trucking cost index | CPI-U | Owner decision | Accepted 2026-11-17 (re-derivation log, decision 5; made for the marine indexes and applied to road by the verifier) | The trucking survey's own series gives 0.00083 for point 1 (8% to 9% higher). |
| 39 | CPI-U 2026 value | 332.243 (January to September 2026 average) | Owner decision | JC, 2026-11-17 (log decision 10); series `shared/cpi/cpiai_datahub_mirror.csv` | The 330.0 basis is 0.68% lower; the rounded point is the same. |
| 40 | One rate for every road edge statewide | Statewide | Owner decision | JC, 2026-11-17 (log decision 6) | Gravel and remote corridors are under-priced. The earlier chapter puts the Dalton corridor at 0.0012 to 0.0015 from contract rows that were not re-opened. |
| 41 | Origins and dollar year for the price regression | Chitina from Anchorage, the other nine from Fairbanks; FY2025 prices carried by the 2025 CPI-U value | Assumed | Second-round analyst; kept by the verifier | Affects the ceiling only. The sign of the slope flips with the choice of origin. |

Quoted passages

- Q1. Econ One, slide 15. Title: "Cost of In-State Product Movement Can Be Significant". Legend: "Via Pipeline",
  "Via Barge", "Via Truck", "Via Rail". One green label "20 cpg" between two truck icons, on green lines that
  run from the Interior refineries to both Anchorage and Valdez. Other labels: red "16 cpg", light blue "2 cpg",
  dark blue "10 cpg".
- Q2. ATRI, Figure 27, "Average Respondent Revenue, Costs, and Profit per Mile": the Tanker bar is labelled
  "$4.001", with "61.7%" marginal costs, "1.9%" operating profit and "36.3%" other costs.
- Q3. ATRI, printed p. 44: "Deadhead mileage and its incurred costs are included in all of the cost metrics in
  this report (which carriers report as total cost divided by total mileage)." and "tank carriers spent an
  average of 43.8 percent of their mileage running deadhead."
- Q4. ISER 2010, PDF p. 17: "In the case of the Yukon River, fuel is trucked to the Nenana terminal from a North
  Pole refinery. This is a straightforward process with costs of less than $0.05 per gallon. There are a number
  of trucking companies active in this market."
- Q5. ISER 2008, printed p. 23: "The transportation cost per gallon of fuel trucked is determined by the distance
  and the quantity of fuel delivered. Delivery prices vary with the quantity of fuel shipped because most of the
  delivery costs are fixed, regardless of the amount of fuel carried."
- Q6. ISER 2008, printed p. 62: "Heating fuel #1 is delivered directly to homes in Chitina from fuel trucks."
  "As of November 2007 Fisher fuel reported selling #1 heating fuel for $3.41 a gallon. This price includes a
  $0.25 to $0.30 a gallon delivery charge from the fuel's source in Anchorage. Communication with Crowley
  indicates it charges similar amounts." "Chitina tends to face higher delivered fuel costs than other
  road-connected communities in the region, because its small size means fuel deliveries are also small, raising
  the fixed overhead costs per unit of fuel."
- Q7. ISER 2008, printed p. 27: "Anchorage's delivery costs are negative, because the bidding transporter was
  expecting to be able to buy fuel at a lower cost than the indexed price."

Assumed inputs that affect only the rejected or unusable items, not the point: Table 10 is treated as 2005
dollars, the midpoint of its 2003 and 2006 contract years, with North Pole as the origin (second-round
analyst); the rejected build-up assumed an 80,000-pound gross weight limit, Alaska cost multipliers of 1.10 to
1.5, a diesel price of $5.00 per gallon, 2.75 hours at the rack and terminal, and an 18% carve-out for dwell
(second-round analyst).

Which assumptions carry the most weight. The payload (input 24) is the largest: no supplied document states
how many gallons an Alaska highway tanker carries, and the build-up point runs from 0.00065 to 0.00116 across
the loads considered. The published point rests on one label read from a map image whose unit, leg length,
dollar year and scope were all supplied by the analysts (inputs 20 to 23); the leg length and dollar year
alone move it between 0.00074 and 0.00080.
Input 33 decides the status: the third method is carried from the earlier chapter and could not be re-opened,
and without it the level would be Provisional. Inputs 35 and 36 are one judgement seen from two sides: the
evidence allows either $0.0007 with about $0.02 per gallon of handling billed elsewhere, or $0.00076 with no
handling billed anywhere, and cannot tell them apart.

Public links, as listed in `DOWNLOAD_LIST.md` or the earlier chapter. None was opened in this session.

- State heating-oil contract: https://oppm.doa.alaska.gov/media/1337/08-heating-oil.pdf (earlier chapter)
- DEC Fairbanks cost analysis: https://dec.alaska.gov/media/16394/uls-hs-fairbanks-cost-analysis-finaldraft-05082019.pdf (earlier chapter)
- ISER 2008: https://scholarworks.alaska.edu/cgi/viewcontent.cgi?article=1348&context=uaa_iser_reports
- ISER 2010: https://iseralaska.org/static/legacy_publication_links/componentsoffuel3.pdf (earlier chapter)
- Trade article on tanker payloads: https://www.akbizmag.com/industry/transportation/keeping-alaska-fueled-up/ (earlier chapter)
- CPI-U mirror: https://github.com/datasets/cpi-us
- Econ One 2016, the ATRI 2025 update, the Port of Alaska assessment, ISER 2010 and the FY2025 PCE report are held
  locally on the harness `main` branch. ISER 2008 and the Bethel terminal rate sheet are on branch `cost-sources`.
  No link is recorded for Econ One, ATRI, the Port of Alaska assessment or the rate sheet.

### What the figure includes and excludes

Inside the $0.0007 per gallon per statute mile:

- Driver, tractor and tank trailer, truck fuel, maintenance, insurance, carrier overhead and margin.
- The empty return trip. The rate is per loaded one-way mile.
- Full bulk loads of about 10,000 to 13,000 gallons.

Not inside the rate:

- The truck's own loading and unloading time, about $0.02 per gallon (at most $0.03).
- The terminal's truck-rack throughput charge. The Bethel sheet lists "Truck Rack $0.2500 / gallon", effective
  10 August 2022 (`Bethel-Terminal-Storage-Rate-Sheet.pdf`, p. 1), which is $0.284 in 2026 dollars.
- Storage, wharfage, product cost and taxes.
- Small-drop retail distribution, about $0.25 to $0.27 per gallon. Two unrelated sources agree on it: the
  Chitina charge net of line-haul (input 19) and the contract intercept (input 18). The Bethel local delivery
  trucks ($0.25 to $0.35 per gallon in 2007; ISER 2008, PDF p. 67) are the same kind of service. It is household
  distribution beyond the hub tank and is outside the network.

How the pieces add, so that no handling is billed twice:

- Plane to road ($0.025 per gallon) and road to ice road ($0.022 per gallon). These fees bill the truck-side
  connect, pump and disconnect labour. That is the fixed part the Road rate leaves out, so they add to $0.0007
  without overlap.
- If the Road rate were raised to an all-in $0.00076 or more, those two fees would bill roughly $0.02 per
  gallon twice on long hauls. Raise the rate or keep the fees, not both.
- Barge to road ($0.24 per gallon). A terminal's rack charge is in no trucking figure, so it does not overlap
  with the Road rate. The truck's own time at the rack is then billed nowhere, an under-count of at most $0.03
  per gallon.
- Road-only routes carry no fixed part. The under-count is at most $0.03 per gallon.
- The second-round build-up's $0.053 per gallon per load must not be added. Its handling is already covered by
  the fees above.

Two notes for the transfer-fee segment. They come from the one verifier and have not had a second independent
review.

- The code comment restates the Bethel truck-rack fee as $0.276 in 2026 dollars. From the August 2022 sheet it
  is $0.284 at CPI-U 332.243 ($0.282 at the 330.0 basis).
- The barge-to-road fee does not depend on direction. Trucks unloading into the Nenana terminal for the river
  barges are billed $0.24 per gallon, although ISER 2010 puts the whole trucking process into Nenana below
  $0.05 per gallon in 2010 dollars, and the physical event there is the marine header ($0.15 per gallon on the
  Bethel sheet), not the truck rack.

### Compared with the applied value and the earlier chapter

What is applied today. `friction_costs.py` carries Road at $0.0007 per gallon per statute mile, with the range
$0.00045 to $0.0011, described as carriage cost with the empty return. The connector constant
`CONNECTOR_COST_PER_GALLON_MILE_USD` is set equal to the Road rate.

What the earlier chapter concluded (`01_road.md`, section 6). $0.0007, range $0.00045 to $0.0011, from three
methods: A, the DEC report citing Econ One, $0.00077; B, a build-up at $3.00 per truck mile, $0.00054; C, the
State contract gradient, $0.00067.

What this addendum does.

- It confirms the applied value and does not move it. Nothing needs to change in `friction_costs.py` for Road.
- It rejects both second-round blind figures, which stood 1.6 to 1.8 times above the applied value. Once
  corrected, the published legs fall back to $0.00076 and the build-up to about $0.00085.
- It tightens the earlier cluster. Method B was too low: it used $3.00 per truck mile where the trucking survey
  shows tank-carrier revenue of $4.001. Corrected with the earlier chapter's own load and return factor, it
  gives $0.00077, so the three earlier figures become $0.00077, $0.00077 and $0.00067.
- It adds two pieces of evidence the earlier chapter lacked. The Nenana ceiling independently supports the top
  of the applied range at $0.0011. The Chitina charge puts the small-drop distribution premium at about $0.27
  per gallon, matching the contract intercept.
- It records mild upward pressure. The geometric mean of the three points is $0.00076, and a trucking cost
  index in place of CPI-U gives $0.00083 for the published leg. The applied $0.0007 is about 7% below the mean
  and inside every range. That is consistent with it being a carriage-only rate, with about $0.02 per gallon of
  handling billed through the fees.
- It does not re-check the comment that the Dalton corridor runs about $0.0012 to $0.0015. That rests on the
  contract file that could not be re-opened.
- It notes, without changing anything, that the toolkit's self-test uses a weaker third road method than this
  record: $4.75 per truck mile over 9,000 gallons, from a heavy-equipment marketing page, with no empty return.

### Open evidence gaps

- A document that states an Alaska highway tanker payload in gallons: a carrier specification sheet, or the
  text of the State's vehicle size and weight regulation (17 AAC 25.013). This is the largest gap; it would fix
  the build-up point.
- The State heating-oil contract (`08-heating-oil.pdf`) added to `cost_derivation_resources/`, so that the third
  method can be checked from a held document.
- The DEC Fairbanks cost analysis and the paginated Econ One report it cites, which name the endpoints, the
  dollar year and the context of the 20 cents per gallon.
- A current carrier tariff, contract or quote in cents per gallon for a named lane with the load size. All
  Alaska line-haul evidence is of 2007 to 2016 vintage carried forward by CPI-U; one current lane rate would
  replace the whole chain.
- A measured Alaska cost premium over the contiguous-US survey and a sourced 2026 Alaska diesel price, if the
  build-up is to carry an Alaska adjustment.
- A sourced truck-side handling time or charge per load, to move the fixed part from a bound to a figure.
- A separate rate for gravel and remote corridors (Dalton, Steese, Taylor), if the owner later wants more than
  one statewide road rate.
- A second independent review of this verdict.

A network finding made along the way, outside the cost question and not re-confirmed for this record: the
verifier reports that the Anchorage hub node sits about 80 road miles from the port-area road node although it
is 4.3 miles away in a straight line, so road routes from that hub to the Interior come out about 25 miles
short. No distance used in this addendum starts from that node.

### Working files

All under `harness: blind_derivations/working_2026-11-17/`.

| Path | Holds |
|---|---|
| `derive2_results.json` (keys `verdicts.road`, `derivations.road-published-legs`, `derivations.road-cost-buildup`, `derivations.road-revealed-prices`) | The verifier's verdict and the three second-round blind derivations |
| `verify2/road/verify.py`, `dist.py`, `dist.json`, `pg.py` | Verifier's checks, distance recomputation and page finder (330.0 basis) |
| `verify2/road/img/econ-15.png`, `econzoom-15.png`, `atri-56.png`, `atri-48.png` | Rendered pages: Econ One slide 15, ATRI Figure 27 and ATRI Figure 22 |
| `derive2/road_published/calc.py`, `dist.py` | Second-round published-legs method |
| `derive2/road_buildup/build.py` | Second-round build-up |
| `derive2/road_revealed/build.py`, `dist.py`, `match.py`, `reg.py`, `road_sample.csv`, `G.npz`, `hubs_rc0.pkl`, `nodes.pkl` | Second-round price regression |
| `extracts/local_air_road_winter.md` (topic 4), `extracts/iser_2008.md`, `extracts/tariffs.md` | Fact sheets |
| `pdf_text/` | Full text of every source document |
| `shared/pce_prices_with_distances.csv` | FY2025 price table |
| `shared/index_basis_2026-11-17.md`, `shared/inflation_factors.md`, `shared/cpi/cpiai_datahub_mirror.csv` | Index basis and factors |
| `record/road_checks/restate_road_332243.py` and `restate_road_332243_output.txt` | Written for this record: restates every inflated road figure to 332.243, reruns the rejected build-up with only the index changed, and recomputes the spread ratios |
| `record/road_checks/verify_py_output_330basis.txt` | Output of the verifier's script as rerun for this record |
| `record/road_checks/dist_rerun_output.txt`, `dist.json` | Output of the verifier's distance script as rerun for this record (identical to the verifier's file) |
| `record/road_checks/pce_check.py` and `pce_check_output.txt` | Written for this record: reruns the price regression on the verifier's distances |
| `record/road_checks/find_quote_page.py` | Written for this record: finds a quoted passage and its PDF page in a text file |

Not re-confirmed for this record:

- The State heating-oil contract fees, the 11-point regression and the Dalton corridor figures. The contract is
  not among the supplied files; they are carried from the earlier chapter.
- The DEC Fairbanks report that names Valdez to Fairbanks, 364 miles and a 2015 vintage. It is not among the
  supplied files.
- The tanker payload figures of about 9,000 to 12,000 gallons. They come from web search snippets and a trade
  article that were not opened.
- The page numbers of the ten prices in the FY2025 PCE report. Prices and gallons were checked in the decoded
  price table only.
- The verdict's convergence figures of 1.25 and 0.00075 as printed by the saved script. The script prints 1.32
  and 0.00077 because it uses 9,500 gallons (see Methods and convergence).
- The verdict's ceiling of "$0.0080" from the price regression. Its own upper limit of 0.79 cents per
  gallon-mile gives $0.0081 at either index basis; the difference is immaterial.
- The verdict's statement that Table 15 of ISER 2008 shows 52 deliveries a year for Chitina. The row and the
  value are on PDF p. 60, but the column was not matched to Chitina.
- The verifier's finding about the Anchorage hub node.
