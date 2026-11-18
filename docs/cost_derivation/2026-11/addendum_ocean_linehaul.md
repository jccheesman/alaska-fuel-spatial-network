## Addendum 2026-11-17: Ocean line-haul barge (proposal; nothing applied)

Segment: a tug-and-barge set of about 3 million gallons sailing from Cook Inlet to the coastal and Western Alaska
hubs. Nothing in this addendum has been applied to `friction_costs.py`. All 2026 figures are in 2026 dollars at
CPI-U 332.243 (`index_basis_2026-11-17.md`). The working files used 330.0; every inflated figure below was
recomputed from its source-year value. The verdict summarised here comes from one adversarial verifier and has
not had a second independent review.

Short names used below. **ISER 2010** is the February 2010 report "Components of Alaska Fuel Costs" by the
Institute of Social and Economic Research, University of Alaska Anchorage, and **ISER 2008** its June 2008 report
"Components of Delivered Fuel Prices in Alaska". **Econ One 2016** is the December 2016 slide deck "The State of
Alaska's Refining Industry" by Barry Pulliam of Econ One; its labels are in "cpg", read as cents per gallon. **OSRO** stands
for oil spill response organization; the "lightering guide" is Alaska OSRO's 2026 guide to transferring fuel from
tankers to barges in Western Alaska. **DEC 2007** is the December 2007 cost assessment by the Alaska Department of
Environmental Conservation and Northern Economics. **PCE** is the Power Cost Equalization program; its report for
fiscal year 2025 (FY2025, July 2024 to June 2025) gives each utility's fuel price. **NOAA** is the National
Oceanic and Atmospheric Administration, which publishes port-to-port sailing distances. **CPI-U** is the consumer
price index for all urban consumers. A "hub" is a regional port with a tank farm; "model miles" are statute miles
along the water route in the project network.

### Status

**Headline status for the rate as it would be applied: Derived** (the weakest of the Derived figures: the third method is weak, and the zero fixed part is Provisional). Detail follows.

**Level: Derived, with a weak third method.** Three sources that do not cite one another give a per-mile rate
within a factor of about 1.6 on a coastwise leg of 1,500 to 1,700 statute miles, and their quoted inputs were
re-opened in the source documents. The first two agree within 1%. The third (the lightering guide) describes
tankers on an unstated route in an unstated year, so the count of three is reached only by admitting it. All
three are published charges; there is no independent engineering build-up and no usable estimate from delivered
prices.

**Form (pure per-mile, no fixed part): Provisional.** The sources agree on the total charge at about 1,500
miles but not on how it splits into a fixed part and a per-mile part. The two sources that speak to short legs
disagree on the sign of the fixed part.

**What the model should carry meanwhile.** Today every waterway edge is priced at the blended barge rate of
$0.0010 per gallon per statute mile, and that stays until the owner decides to split ocean from river edges.
When the split is made, marine line-haul edges should carry $0.00021 per gallon per statute mile with the range
$0.00013 to $0.00028. A result that depends on a short ocean leg (under about 600 miles) should be reported with
the range, not the point alone.

### Result

| Item | Value |
|---|---|
| Form | Pure per-mile, charged on the model's water-route statute miles. No fixed part. |
| Point | $0.00021 per gallon per statute mile |
| Range | $0.00013 to $0.00028 per gallon per statute mile |
| Tug-and-barge band inside the range | $0.00016 to $0.00028; the tail down to $0.00013 is the tanker figure from the lightering guide |
| Upper bound (not part of the range) | $0.00033 per gallon per statute mile (the full-cost reading of ISER 2010) |
| Fixed part | $0 with the pure per-mile rate |
| Unit | United States dollars per gallon of fuel per statute mile of model water route |
| Dollar basis | 2026 dollars, CPI-U 332.243 |
| Same charge per gallon | About $0.32 per gallon at the mean hub distance of 1,527 statute miles |
| Source-year figures | ISER 2010: $0.205 per gallon (band $0.19 to $0.22), which is $0.000134 per gallon per statute mile in 2010 dollars. Econ One 2016: $0.25 per gallon, which is $0.000150 per gallon per statute mile in 2016 dollars. |

Restatement note. At the 330.0 basis the two main estimates were $0.000203 and $0.000206 per gallon per statute
mile; at 332.243 they are $0.000205 and $0.000207. The rounded point ($0.00021) and the rounded range ends do
not change. The low end of the tug-and-barge band is $0.000163 (the Econ One two-part slope on the analyst's
distances) to $0.000166 (ISER's $3.5 million over seven trips); the working files had $0.000162 to $0.000165 and
wrote it as $0.00016, which is kept.

Marine-freight-index sensitivity. If the national coastal water-freight producer price index is used in place
of CPI-U, the rate is $0.00023 to $0.00024 per gallon per statute mile (ISER 2010 times 1.749 gives $0.000235;
Econ One 2016 times 1.538 gives $0.000230). Whether Alaska tug-and-barge trade is inside that index is not
established, so this is a sensitivity and not the base case.

Low-confidence alternative, not recommended: $0.06 per gallon per ocean voyage (range $0 to $0.09) together with
$0.00017 per gallon per statute mile (range $0.00012 to $0.00020). The two must be used as a pair. With these
rounded figures the pair equals the pure rate of $0.00021 at 1,500 statute miles ($0.06 divided by the $0.00004
difference). The verdict says "about 1,200 miles", which holds only against a pure rate of $0.00022; that
statement is not repeated here as fact. A fixed part must never be added on top of the pure rate.

### Methods and convergence

Values are pure per-mile equivalents in dollars per gallon per statute mile, 2026 dollars.

| Method | Counted as independent? | Value (2026 dollars) | Source documents with page | How it was checked | Kept or rejected and why |
|---|---|---|---|---|---|
| ISER 2010 charged line-haul rate, divided by model miles | Yes (point 1) | 0.000205 (0.000190 to 0.000220 across the $0.19 to $0.22 band) | `components of alaska fuel costs.pdf`, pp. 16-17 | Verifier read pp. 16-17 in full and recomputed the five hub distances from the network tables. Quotes re-confirmed in the text file for this record. | Kept as a point estimate. Single study; its authors call the figures "best estimates and memories" (p. 12). |
| Econ One 2016 transport charge, Pacific Northwest to Southcentral | Yes (point 2) | 0.000207 (0.000180 to 0.000211 across leg and distance readings) | `6_barry_pulliam-_econ_one_-_the_state_of_alaskas_refining_industry.pdf`, slides 14-15 | Read from the slide images by two analysts and the verifier; images re-read for this record. | Kept as a point estimate. The slide gives no source, vessel, parcel size or scope. |
| Alaska OSRO lightering guide, West Coast to Alaska range | Yes, but weak (point 3) | 0.00013 (0.000055 to 0.000226 across distance and year readings) | `Alaska-OSRO-2026-Western-Alaska-Tanker-Lightering-Best-Practices-Guide-1.pdf`, p. 8 (also pp. 7, 10, 22) | Verbatim quote confirmed on p. 8. | Kept as a weak third point. Tankers, not barges; no origin, destination or year stated. |
| Voyage-day build-up from ISER 2010 seasonal costs (first round) | No. Same study and informants as point 1. | Brackets 0.000166 to 0.000333; central 0.000244 | `components of alaska fuel costs.pdf`, pp. 16-19 | Quoted costs confirmed; results file reproduces the fits. | Bound only. The central case adds unsourced judgement (other operating cost, fuel burn, speeds, a $25 million set). |
| Second-round composite: $0.00012 per mile plus $0.08 fixed | No | None carried | OSRO p. 8; Econ One slides 14-15; ISER 2008 Table 10 | Scripts rerun by the verifier; inputs confirmed. | Rejected. The "five slopes" are not five estimates; the slope and fixed part were medians taken separately, so the pair is not a fitted line; it gives $0.26 per gallon at 1,527 miles, below both published charges. |
| ISER 2008 Table 10 state-contract delivery charges | No (bound) | Upper bounds per gallon: Ketchikan $0.22, Kodiak $0.27, Homer $0.31, Klawock $0.34, Unalaska $0.53, Nome $1.07, Naknek $1.58 | `Components of Delivered Fuel Prices in Alaska.pdf`, Table 10, printed p. 27 | Table read in the text file. | Bound only. The charge bundles line-haul, terminal, local delivery, margin and a purchase term; origins are not stated; no slope is identified. |
| DEC 2007 price build-up, Anchorage to coastal hub | No (bound) | Upper bound $1.20 to $1.24 per gallon for everything between Anchorage and the hub | `cost-assessment-fordiesel-fuel-transition-in-western-and-northern-alaska-communities.pdf`, Table 35, printed p. 100 | Table read in the text file. | Bound only. A model archetype, not an observed route. |
| FY2025 utility fuel prices against ocean miles (first round) | No (bound) | Upper bound 0.0009 on the distance-proportional part of the delivered price | `2026.03.01 FY2025 PCE Statistical Report by Community (Final).pdf`; `pce_prices_with_distances.csv` | Slope recomputed by the verifier: negative and not distinguishable from zero. | Bound only. Kotzebue, the farthest hub, is the cheapest. |

Spread. Across the three independent points the ratio of highest to lowest is about 1.6 (1.58 in the working
files at the 330.0 basis; 1.58 to 1.60 restated). At the widest reading (ISER with its forecast rise, OSRO not
inflated) it is 2.0. Across the two clean points it is 1.01. All are inside the 3x standard. The standard asks
for different kinds of method (published rate, engineering build-up, revealed prices). Here the three points are
all published charges, the build-up is not independent of ISER, and revealed prices give only a bound. That is
why the third method is called weak.

Form check. A straight-line fit to the five published coastwise leg charges on model miles gives $0.00022 per
gallon per statute mile through the origin. With the fixed part left free it is minus $0.03 per gallon with
$0.00024 per mile. On Econ One alone the fixed part is plus $0.057 per gallon; on ISER alone it is about minus
$0.09 per gallon. A fixed part is therefore not identified. (This fit is not in the verifier's saved script; it
was reproduced for this record, see Working files.)

Bounds. The full-cost reading of ISER ($0.00033), revealed prices ($0.0009), DEC ($1.20 to $1.24 per gallon to a
coastal hub) and the Table 10 contract charges are all respected at $0.00021. The one exception is Ketchikan
when routed from Anchorage ($0.23 to $0.25 per gallon against a bundled $0.22), which is a supply-origin issue
and not a rate issue.

### Derived versus assumed

| # | Input | Value | Type | Reference | What changes if it is wrong |
|---|---|---|---|---|---|
| 1 | ISER current line-haul rate, Cook Inlet to Western Alaska | $0.19 to $0.22 per gallon | Quoted | `components of alaska fuel costs.pdf`, p. 17; passage Q1 | The level moves in proportion. It is one of the two clean points. |
| 2 | Parcel and season behind the ISER rate | 3 million gallons per trip; six trips; 18 million gallons | Quoted | Same, p. 17; passage Q2 | Defines the vessel class the rate applies to. |
| 3 | ISER seasonal costs | $2.5 million fixed; "another $3.5 million" | Quoted | Same, pp. 16-17; passage Q2 | Used only for the upper bound ($0.00033) and the low end of the barge band. |
| 4 | Destinations the ISER rate covers | Dillingham, Naknek, Bethel, Nome, Kotzebue | Quoted | Same, p. 17: "The tank farms in that class in Western Alaska are Dillingham, Naknek, Bethel, Nome, and Kotzebue." | Sets which distances go into the divisor. |
| 5 | Econ One import charge | 25 cpg | Quoted | Econ One, slide 14, label beside the vessel on the Pacific Northwest arrows | The second clean point moves in proportion. |
| 6 | Econ One in-state barge charge | 10 cpg, "Via Barge" | Quoted | Econ One, slide 15, label on the barge loop from Tesoro (Kenai) to Petro Star (Valdez) | Used only in the form check and the two-part alternative. |
| 7 | OSRO West Coast to Alaska transport cost | $0.15 to $0.29 per gallon | Quoted | OSRO guide, p. 8; passage Q3 | The low tail of the range ($0.00013) moves. |
| 8 | Model water miles, Anchorage hub to the five hubs | 1,339.6; 1,343.7; 1,375.9; 1,623.4; 1,951.7; mean 1,526.9 statute miles | Measured | Harness `fuel_network.duckdb`, tables `network_nodes` and `network_edges`, shortest water path; saved in `verify2/ocean/netdist.json` | The per-mile rate changes inversely. Distances change if the network is re-exported. |
| 9 | CPI-U factors to 2026 | 2010: 1.5237; 2016: 1.3843 | Computed | 332.243 divided by 218.056 and by 240.007 (`index_basis_2026-11-17.md`) | See inputs 26 and 27. |
| 10 | ISER rate per mile | $0.000205 | Computed | $0.205 times 1.5237 = $0.312 per gallon, divided by 1,526.9 miles | Follows inputs 1, 8, 12 to 18. |
| 11 | Econ One rate per mile | $0.000207 | Computed | $0.25 times 1.3843 = $0.346 per gallon, divided by 1,669 miles | Follows inputs 5, 19 to 22. |
| 12 | Midpoint of the ISER band | $0.205 per gallon | Assumed | First-round analyst; accepted by the verifier | Band ends give $0.000190 and $0.000220 (7% either way). |
| 13 | The $0.19 to $0.22 is the charged rate; the $0.33 full cost ($6.0 million over 18 million gallons) is only a ceiling | Charged-rate reading | Assumed (judgement between two readings) | Earlier chapter, section 6; kept by the verifier | If carriers now charge full cost, the rate is $0.00033 (about 60% higher). |
| 14 | ISER's forecast rise ("over $0.25 per gallon") is not applied | CPI only | Assumed | Verifier (the first-round analyst applied it) | Applied as a 2015 figure: $0.000230. Applied as 2010 dollars over Bethel's distance: $0.000277 (the top of the range). |
| 15 | ISER dollar year | 2010 | Assumed | Earlier chapter (report dated February 17, 2010; the rate is called "current") | Reading it as 2009 dollars raises the figure by 1.6%. |
| 16 | Divisor for the ISER rate: simple mean of the five hub distances | 1,526.9 statute miles | Assumed | First-round analyst; ISER gives no distance | Volume-weighted means (1,500 to 1,545 miles) move it under 2%. Bethel alone: plus 11%. Kotzebue alone: minus 22%. |
| 17 | Voyage origin is Anchorage | Anchorage hub | Assumed | Model design; ISER p. 14 says "either Nikiski or Anchorage" | A Nikiski origin shortens every route by 99.2 miles and raises the rate about 7%. |
| 18 | Per-gallon charges are divided by model miles, not charted sailing miles | Model routes about 7.5% longer than the NOAA distances in the earlier chapter | Assumed | Verifier | Correct only if the model multiplies the rate by the same model miles. On the NOAA mean (1,420 miles) the same charge is $0.00022. |
| 19 | "cpg" means cents per gallon | Cents per gallon | Assumed | Both analysts; the slide does not define it | If it is another unit the Econ One point is void. |
| 20 | The 25 cpg label belongs to the Pacific Northwest to Southcentral leg | Leg ends at Cook Inlet | Assumed (reading of an image) | Both analysts and the verifier | If it is Pacific Northwest to Dutch Harbor (about 1,928 miles) the rate is $0.000180. |
| 21 | Length of that leg | 1,669 statute miles | Assumed | Second-round analyst's great-circle waypoint estimate, Anacortes to Nikiski | A web search snippet of the NOAA table gives 1,428 nautical miles (1,643 statute miles), which gives $0.000211. |
| 22 | Econ One dollar year, and that its charge covers the same things as the ISER rate | 2016 dollars; comparable scope | Assumed | Analysts and verifier; slides are dated December 2016 and state no scope | If the charge includes terminal costs or is a tanker rate, it does not confirm the barge level. |
| 23 | OSRO route | West Coast (Anacortes) to Dutch Harbor, 1,928 statute miles | Assumed | Second-round analyst; the guide names no ports | Across 1,669 to 2,730 miles and the year readings the point runs $0.000055 to $0.000226. |
| 24 | OSRO dollar year | Unknown; carried midway between 2026 dollars and 2019-2020 dollars | Assumed | Verifier (the second-round analyst's 2019 rested on a misreading; the text says the rule "went into effect on January 1, 2020") | Factor 1.00 to 1.30; the point runs $0.000114 to $0.000148. |
| 25 | A tanker charge is admitted as evidence on a barge rate | Counted as a weak third point | Assumed | Verifier | If it is excluded only two independent points remain, and the level would be Provisional. |
| 26 | Inflation by CPI-U, not a marine freight index | CPI-U | Owner decision | Accepted 2026-11-17 (re-derivation log, decision 5) | The coastal freight index gives $0.00023 to $0.00024 (about 12% higher). |
| 27 | CPI-U 2026 value | 332.243 (January to September 2026 average) | Owner decision | JC, 2026-11-17 (log decision 10); series `shared/cpi/cpiai_datahub_mirror.csv` | The 330.0 basis is 0.68% lower; the rounded point is the same. |
| 28 | Point rounded to $0.00021 | Between the two clean estimates ($0.000205 and $0.000207) | Assumed | Verifier | The geometric mean of all three points is $0.000177; the pooled leg fit is $0.00022. |
| 29 | Range ends | Low $0.00013 (OSRO); high $0.00028 (ISER forecast in 2010 dollars over Bethel's distance) | Assumed | Verifier | A narrower range would follow if OSRO were dropped ($0.00016 to $0.00028). |
| 30 | Form: pure per-mile, fixed part zero | $0 fixed | Assumed | Verifier | At 470 miles the pure rate gives $0.10 per gallon. Econ One shows $0.14 for that leg; ISER says "a few cents" for Valdez to Anchorage (read as 3 to 5 cents, which is $0.05 to $0.08 in 2026 dollars). |
| 31 | One rate for all marine line-haul edges statewide | Statewide | Owner decision | JC, 2026-11-17 (log decision 6) | Southeast is supplied from Puget Sound or British Columbia; routed from Anchorage, Ketchikan's line-haul is overstated. |
| 32 | Fuel reaches Western Alaska by barge from Cook Inlet | Cook Inlet supply | Assumed | Model design | OSRO p. 10 says seasonal resupply is now imported by tanker from the Far East and Canada, with barges distributing. If so, ocean cost into Western Alaska may be nearer $0.10 to $0.29 per gallon for the whole leg. |

Quoted passages

- Q1. ISER 2010, p. 17: "we expect the linehaul cost of shipping fuel from Cook Inlet to Western Alaska to rise
  inevitably, from the current $0.19-$0.22 per gal to over $0.25 per gallon or higher in the near future."
- Q2. ISER 2010, pp. 16-17: "Current fuel distributors estimate the fixed cost of a tug and barge set at $2.5
  million for the season." and "In addition to these fixed costs, the costs of tug fuel and other miscellaneous
  items for a six-to-seven trip season between Cook Inlet and the Bering Sea ports is another $3.5 million. A
  typical linehaul barge carries three million gallons of fuel, for a total of eighteen million gallons for a
  six-trip season. This results in approximately $0.19 per gallon in cost for transportation only."
- Q3. OSRO guide, p. 8: "Transportation Costs (dependent upon market, vessel size, and cargo parcel size
  carried) o Asia to Alaska $0.10-$0.21 per gallon o West Coast to Alaska $0.15-$0.29 per gallon".
- Q4. ISER 2010, p. 16: "The current rates range from a few cents per gallon between Valdez and Anchorage to
  over 40 cents per gallon for transportation to the Beaufort Sea."
- Q5. ISER 2010, p. 12: "The numbers used in this report reflect the best estimates and memories of historical
  costs but should not be considered exact without confirming data with current fuel distribution companies."

Assumed inputs that affect only the bounds and the form check, not the point: the Table 10 charges are treated
as 2005 dollars, the midpoint of the 2003 and 2006 contract years (second-round analyst); the FY2025 prices are
converted with the mean of the 2024 and 2025 CPI-U values (first-round analyst); in the form check the Beaufort
leg is set at 2,580 statute miles and ISER's "a few cents" is read as $0.04 per gallon (verifier). DEC Table 35
states its own dollar year (2006).

Which assumptions carry the most weight. The level rests on two per-gallon charges that had to be given a
distance by the analysts, because neither source states one. For ISER that is the choice of divisor and origin
(inputs 16 and 17); for Econ One it is the reading of which arrow the label belongs to and how long that leg is
(inputs 20 and 21). The largest single judgement is input 13: taking the $0.19 to $0.22 as what carriers
charge and treating the $0.33 full cost as a ceiling. If carriers now recover full cost the rate is about 60%
higher, which is why $0.00033 is recorded as an upper bound. Input 25 decides the status: without the tanker
figure there are two independent points, not three. Input 30 (no fixed part) matters only for short ocean legs,
where the pure rate may be too low by a few cents per gallon.

Public links, as listed in `DOWNLOAD_LIST.md` or the earlier chapter. None was opened in this session.

- OSRO guide: https://alaskaosro.org/wp-content/uploads/2026-Western-Alaska-Tanker-Lightering-Best-Practices-Guide-1.pdf
- ISER 2008: https://scholarworks.alaska.edu/cgi/viewcontent.cgi?article=1348&context=uaa_iser_reports
- DEC 2007: dec.alaska.gov/media/8915/ulsd-cost-rpt-1207.pdf (earlier chapter, section 5)
- Coastal water-freight index: https://fred.stlouisfed.org/series/PCU483113483113
- CPI-U mirror: https://github.com/datasets/cpi-us
- ISER 2010, Econ One 2016 and the FY2025 PCE report are held locally on the harness `main` branch; no link is
  recorded for them. The OSRO guide, ISER 2008, DEC 2007 and the port tariffs are on branch `cost-sources`.

### What the figure includes and excludes

Inside the rate (ISER calls it "transportation only"; its charge formula is daily cost times voyage days times
margin, divided by gallons):

- Tug and barge capital as far as the market charge recovers it, crew, tug fuel, insurance and maintenance.
- The vessel's own time alongside while loading and discharging, and its own pumps and crew. The Port of Nome
  tariff says "Petroleum transfers must be performed by the Marine Carrier delivering product to the facility"
  (`PON Tariff No 16.6 - 03.12.26 Final.pdf`, PDF p. 18).
- Weather and tide waits, the empty return leg and the carrier's margin.
- The line-haul set standing by during draft-relief lightering. This is the verifier's reading of the charge
  formula (voyage days); ISER does not say so in words.

None of these may be billed again as a fee. A per-voyage fixed part must not be added to the pure rate; that
would count about $0.06 to $0.09 per gallon twice.

Not inside the rate, so each needs a home in a fee if it is to be modelled:

- Destination wharfage. Port of Bethel: $0.06 per gallon inbound petroleum plus a $0.06 per gallon fuel transfer
  charge (`2026 UPDATED Tariff 005 with Pics.pdf`, PDF pp. 39 and 58). Port of Nome: $0.05 per gallon inbound
  (`PON Tariff No 16.6 - 03.12.26 Final.pdf`, PDF p. 25). These are 2026 tariff figures and are not inflated.
  ISER 2010 p. 18 gave $0.02 to $0.04, which is $0.03 to $0.06 in 2026 dollars.
- Shore-side after-hours receiving labour: ISER 2010 p. 18, $0.04 to $0.06 per gallon (2010), $0.06 to $0.09 in
  2026 dollars.
- Third-party terminal or marine-header throughput, only where the fuel passes through another company's
  terminal: ISER 2010 p. 18, $0.07 to $0.15 per gallon (2010), $0.11 to $0.23 in 2026 dollars. The Bethel
  terminal rate sheet lists a marine header fee of $0.15 per gallon (2022), $0.17 in 2026 dollars
  (`Bethel-Terminal-Storage-Rate-Sheet.pdf`, p. 1).
- Origin charges at Anchorage: wharfage 20.49 cents, valve-yard transfer 6.08 cents and modernization surcharge
  14 cents, all per barrel, about $0.01 per gallon in total
  (`POA_Terminal_Tariff_10.2_Effective_January_1_2026.pdf`, PDF pp. 48 and 51; 2026 tariff, not inflated).
- The shallow-draft barge that lighters Bethel, Dillingham and Kotzebue. It belongs to the coastal small-barge
  segment.
- Purchase differential ($0.06 per gallon), working capital ($0.03 per gallon), administration, storage and
  taxes (the two figures are as printed in ISER 2010 Table 4, p. 22, taken as 2010 dollars and not inflated).
  These are not handling and stay unmodelled under the storage-free fee design.

Consequence for the fee table. This point comes from the one verifier and has not had a second review.

- The barge-to-overland fee of $0.24 per gallon bills only the truck rack and leaves out the marine header on the
  grounds that the blended $0.0010 barge rate already carries it. That holds only while ocean edges are priced at
  $0.0010. If they are repriced at $0.00021, hub intake (wharfage at least, and the header and receiving labour
  where they apply) is in no rate and must be billed once per hub landing. The transfer-fee addendum prices that
  event at $0.12 per gallon for a distributor's own terminal (range $0.05 to $0.20); it is to be billed there
  and nowhere else.
- Every Anchorage-to-hub route in the network crosses two transfer edges, so $0.48 per gallon of truck-rack fee
  is charged per ocean delivery. The crossing at the origin is not a truck-rack event; the published origin
  charges are about $0.01 per gallon.

### Compared with the applied value and the earlier chapter

What is applied today. `friction_costs.py` prices every waterway edge, ocean or river, at the blended barge rate
of $0.0010 per gallon per statute mile, with the range $0.00023 to $0.011. The ocean line-haul value of $0.00023
appears there only as a documented decomposition and as the lower range bound. It is not applied to ocean edges.

What the earlier chapter concluded (`02_barge.md`, section 7). Ocean line-haul $0.00023 per gallon per statute
mile, range $0.00017 to $0.00039, from $0.29 per gallon over the NOAA Anchorage to Bethel distance of 1,276
statute miles. It also recommended not blending: $0.00023 on ocean edges, a hub fee, and $0.011 on river edges.

What this addendum does.

- It confirms the level. The ISER rate on model miles ($0.000205) and Econ One ($0.000207) sit about 10% under
  $0.00023, inside the earlier range, and the marine-index reading equals $0.00023. The difference comes mainly
  from dividing by model miles (mean 1,527) and using the middle of the ISER band. The verifier would write
  $0.00021 if the figure is re-derived on model miles with CPI-U only, and regards leaving $0.00023 as
  defensible.
- It corrects the earlier claim of three independent methods. Methods A, B and C of that chapter all rest on
  ISER 2010. Econ One and the OSRO guide are the first independent sources for this segment.
- It changes the range. The low end drops from $0.00017 to $0.00013. The old top of $0.00039 was the full-cost
  reading on NOAA miles; on model miles it is $0.00033 and is recorded as a bound, with $0.00028 as the top of
  the range.
- It rejects the second-round blind figure ($0.00012 per mile plus $0.08 fixed).
- It tightens the case against the blended $0.0010 on ocean edges. At the mean hub distance $0.0010 gives $1.53
  per gallon. That is 4.4 to 5.3 times the ISER rate and Econ One's long leg in 2026 dollars ($0.29 to $0.35 per
  gallon), and at least 4 times every OSRO whole-leg charge ($0.10 to $0.38). At Nome ($1.62) and Kotzebue
  ($1.95) it exceeds the DEC bound of $1.20 to $1.24 for everything between Anchorage and a coastal hub.

No applied value is overturned by this segment. The decision to split ocean from river edges is the owner's and
is recorded in the re-derivation log as waiting on the marine and river water label.

### Open evidence gaps

- An independent engineering build-up: a tug-and-barge charter day rate, or the vessel operating cost tables of
  the US Army Corps of Engineers Port of Nome study, Appendix D (cited, but not in the supplied PDF).
- A current carrier tariff, contract or invoice that states line-haul freight separately from the fuel price.
  The newest on-point rate is from 2010; the newest independent one is an unsourced 2016 slide.
- One sourced short-leg barge charge (for example Cook Inlet to Valdez or Kodiak). It would settle whether there
  is a fixed part.
- The source behind the Econ One slide labels, and a published port-distance table entry for the Pacific
  Northwest to Cook Inlet leg (the NOAA "Distances Between United States Ports" table).
- The year, route and vessel class behind the OSRO cost ranges (an earlier edition of the guide, or the
  committee's source).
- Evidence on how Western Alaska is supplied now: tanker import from the Far East and Canada, or barge from Cook
  Inlet. The model has no tanker supply point.
- A Southeast supply point (Puget Sound or British Columbia), or a note that Southeast ocean cost is overstated
  when routed from Anchorage.
- Evidence on whether Alaska tug-and-barge trade is inside the national coastal water-freight index.
- A second independent review of this verdict.

### Working files

All under `harness: blind_derivations/working_2026-11-17/`.

| Path | Holds |
|---|---|
| `derive2_results.json` (keys `verdicts.ocean`, `derivations.ocean-tanker-and-contract`) | The verifier's verdict and the second-round blind derivation |
| `blind_results.json` (keys `ocean-market-rate`, `ocean-voyage-buildup`, `ocean-revealed-prices`) | The three first-round blind derivations |
| `verify2/ocean/netdist.py`, `netdist.json`, `verify.py` | Verifier's distance recomputation and checks (330.0 basis) |
| `derive2/ocean_published/dist.py`, `fit.py`, `final.py` | Second-round distances and fits |
| `derive/ocean_market/` (`calc.py`, `dist.py`, `weights.py`, `img/econ-14.png`, `img/econ-15.png`) | First-round market-rate method and the Econ One slide images |
| `derive/ocean_buildup/` (`buildup.py`, `buildup_results.json`, `dist.py`, `model_distances.json`) | First-round voyage build-up |
| `derive/ocean_revealed/` (`analyse.py`, `analyse2.py`, `analyse3.py`, `dist_check.py`, `extended_set.csv`) | First-round revealed-price method |
| `extracts/tariffs.md`, `extracts/iser_2008.md`, `extracts/dec_2007.md`, `extracts/bering_strait_lightering.md` | Fact sheets |
| `pdf_text/` | Full text of every source document |
| `shared/index_basis_2026-11-17.md`, `shared/inflation_factors.md`, `shared/cpi/cpiai_datahub_mirror.csv` | Index basis and factors |
| `record/ocean_linehaul_checks/restate_ocean_332243.py` and `restate_ocean_332243_output.txt` | Written for this record: restates every inflated figure to 332.243 and reproduces the pooled leg fit |
| `record/ocean_linehaul_checks/find_quote_page.py` | Written for this record: finds a quoted passage and its PDF page in a text file |

Not re-confirmed for this record: the page numbers of the hub prices in the FY2025 PCE report (prices and gallons
were checked in `shared/pce_prices_with_distances.csv` only); the model distances (taken from `netdist.json`, not
recomputed); the web-snippet distance of 1,428 nautical miles from Seattle to Anchorage; the NOAA distances used by
the earlier chapter (that document is not among the supplied files); DEC 2007 Tables 20 and 22; and the
verifier's statement that the second-round scripts rerun to the reported numbers.
