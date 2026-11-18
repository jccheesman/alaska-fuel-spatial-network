## Supplement 2026-11-18: Plane (bulk fuel flown to a village in a tanker aircraft) (second batch of sources; proposal, nothing applied)

This supplement adds to `addendum_plane.md` (2026-11-17). It reports an adversarial check of one new blind
derivation, made from two air-cargo rate pages that the owner supplied in the second batch. Nothing here has
been applied to `friction_costs.py`, and the addendum itself has not been edited.

Dollar basis. Every tariff figure below is a 2026 actual (Everts rates effective 16 April 2026, Lynden rates
effective 5 January 2026, surcharges effective November 2026). The source-year value and the 2026 value are
therefore the same number and the inflation factor is 1.0. Figures carried over from the addendum are in 2026
dollars at CPI-U 332.243 (`index_basis_2026-11-17.md`), as stated there. Unless another unit is given, a
"rate" is in United States dollars per gallon of fuel per one-way statute air mile.

**Result in one paragraph.** The new evidence is a loose ceiling, not a point estimate, and it is not a new
method: the Everts page is the same web page, with the same base prices, that the earlier chapter already
used and that the addendum already lists as "ceilings only". The ceiling it gives sits 1.5 to 2.3 times above
the ceiling the addendum already has on the same route, so it narrows nothing. The status, the point (0.016)
and the range (0.013 to 0.024) do not change.

### What the new documents add

Two documents concern air.

- **Everts Air, "Rates" web page** (`Alaska Cargo Transportation Rates _ Everts Air Alaska _ Everts Air,
  Airline in Alaska.pdf`, 4 pages, printed 17 November 2026). It gives general-freight prices in dollars per
  pound from Anchorage to nine airports and from Fairbanks to nine airports, each at four weight breaks, and a
  one-price table headed "SMALL PLANE CARGO" from Fairbanks to eleven villages. It states "Rates effective
  April 16, 2026", a minimum general freight charge of $40.00, and "Fuel Surcharge — 42%, effective November
  11, 2026".
- **Lynden Air Cargo, "Rates" web page** (`Rates for Scheduled Service in Alaska _ Lynden Air Cargo.pdf`, 6
  pages, printed 17 November 2026). It gives prices by weight break from Anchorage to Bethel, Emmonak,
  Kotzebue, Nome and St. Mary's in three service classes, "Effective January 5, 2026", with a hazardous
  material fee of "$70.00 per shipment", a "Federal Transportation Tax" of "6.25%" and a fuel related surcharge
  "Effective November 18, 2026: 41%".

Neither page prices fuel. Neither names an aircraft, a payload, a distance, a charter rate or a price per
gallon. On the Everts page the words "Fuel" (under "Charters"), "Charter Quote" and "Dangerous
Goods/Hazardous Materials" are link labels with nothing behind them in the file. The Lynden list of special
commodities has no row for fuel or filled drums; its only tank or drum row is "Tanks, Empty Drums", priced
"Contact Sales".

The Everts page is not new to this record. The earlier chapter (`03_plane.md`, Method C-i) fetched the same
page on 15 July 2026 and used the same prices: Fairbanks to Allakaket $0.80 per pound, Arctic Village $0.83,
Anaktuvuk Pass $0.92, Fort Yukon $0.60, Kaktovik $2.12, and Anchorage to Bethel $1.01 to $1.07. The code
records the same figures (`VEHICLE_MILE_RATES_REFERENCE["Plane"]`: $0.80 to $2.12 per pound). The addendum
already carries them in its methods table as "per-pound freight tariffs", kept as "Ceilings only" and marked
"Not re-verified" because no file was on hand. What the second batch adds is therefore:

1. The Everts tariff as a saved document, so that row of the addendum can now be marked as checked against
   the page. All base prices agree with what the chapter recorded.
2. One changed number. The chapter and the code record the Everts fuel surcharge as 26%, effective 15 July
   2026. The saved page says 42%, effective 11 November 2026. The surcharge rose 16 points in four months, so
   any figure "with surcharge" is a November 2026 spot value, 12.7% above the July value. The 26% figure is
   from the repository's record and was not checked against a saved document.
3. A second carrier (Lynden) on five Anchorage lanes. The chapter had cited two other carriers (Wright Air
   Service and Northern Air Cargo) from web pages that are still not on file.

Two other documents in the batch mention air supply without any price. The Northwest Arctic transportation
plan's marine and riverine report says of Anaktuvuk Pass: "Fuel and cargo flown in. Seasonal use of ice road
connection to the Dalton Highway." (`nwatpMarineRiverineConditions.pdf`, PDF p. 34). That confirms the village
has two supply modes and so does not settle how it was supplied in fiscal year 2025, which is one of the
addendum's open gaps. The Beaver community plan says "Fuel is flown in by plane because of the tank farm's
location" (`2016-DRAFT-Beaver-Community-Plan-V10.pdf`, PDF p. 20) and gives no freight price.

### The new method, checked

The blind analyst converted each tariff price to dollars per gallon (price per pound times 7.1 pounds per
gallon, times one plus the surcharge), divided by the straight-line miles between the project's hub points,
and fitted a fixed part plus a per-mile part to each table. The analyst classed the result as an upper bound
for bulk fuel and not a point estimate. I re-read every quoted input in the PDF text layer and the page
images, re-extracted the text from the two PDFs myself, and recomputed every figure with my own script.
Every quoted price, date and percentage is in the documents on the stated page, and the arithmetic reproduces
to the last printed digit. The faults are in what was left out and in what the fits are claimed to show.

| Step | Value | Type | Reference (document and page) |
|---|---|---|---|
| Everts, Anchorage to eight western hubs, 5,000-pound break | $0.97 to $1.25 per pound (Aniak 1.03, Bethel 1.01, Dillingham 0.97, Galena 1.25, King Salmon 0.97, Kotzebue 1.07, Nome 1.07, Unalakleet 1.05); 2026 | Quoted | Everts page, p. 1, table "Anchorage To:", column "5000 #" |
| Everts, Anchorage to Fairbanks and Fairbanks to Anchorage | $0.40 per pound at every weight break; 2026 | Quoted | Everts page, p. 1 and p. 2. **Left out by the blind derivation without saying so.** |
| Everts, Fairbanks to the same eight hubs, 5,000-pound break | $1.25 to $1.42 per pound; 2026 | Quoted | Everts page, p. 2, table "Fairbanks To:" |
| Fairbanks price minus Anchorage price, same destination | Exactly $0.35 per pound at all four weight breaks for seven of the eight destinations; $0.00 for Galena | Computed | From the two rows above. Found in this check, not by the blind derivation. |
| Everts "SMALL PLANE CARGO", Fairbanks to eleven villages | $0.60 to $2.12 per pound (Allakaket 0.80, Anaktuvuk Pass 0.92, Arctic Village 0.83, Barter Island/Kaktovik 2.12, Eagle 0.73, Fort Yukon 0.60, Galena 0.85, Huslia 0.84, Nulato 0.95, Ruby 0.74, Venetie 0.70); one price, no weight breaks | Quoted | Everts page, p. 2 |
| Everts fuel surcharge | 42%, effective 11 November 2026. Printed under the Anchorage table and the main Fairbanks table; not printed under the small-plane table. | Quoted | Everts page, p. 1 and p. 2 |
| Everts minimum charge and weight rule | "Minimum General Freight Charge - $40.00"; charges are on the greater of "actual gross weight" and "cubic dimensional weight" | Quoted | Everts page, p. 1 and p. 2 |
| Lynden, Anchorage to five hubs, General class | 5,000-pound break: Bethel $1.12, Emmonak $1.25, Kotzebue $1.17, Nome $1.17, St. Mary's $1.14. 10,000-pound break: $1.10, $1.23, $1.15, $1.15, $1.12. 2026. | Quoted | Lynden page, p. 1 (Bethel; Emmonak General row), p. 2 (Kotzebue, Nome), p. 3 (St. Mary's). The last cell of the Emmonak row is covered by a pop-up in the page image and was read from the text layer. |
| The Lynden cells are dollars per pound | Per pound | Assumed (reader's inference; the page never prints "per pound") | Supported by a computation: the backhaul table charges $68.00 flat for "0-137 lbs" and "$0.50" for "138+ lbs", and 137 pounds times $0.50 is $68.50 (Lynden page, p. 5). |
| Lynden fees | "Hazardous Material" "$70.00 per shipment"; "Federal Transportation Tax" "6.25%"; "Effective November 18, 2026: 41%"; "Tanks, Empty Drums" "Contact Sales" | Quoted | Lynden page, p. 5 (fees, surcharge) and p. 4 (drums). The hazardous-material row is covered by the site header in the page image and was read from the text layer. |
| Weight of fuel | 7.1 pounds per gallon, no container | Assumed (blind analyst). It equals the toolkit constant `FUEL_DENSITY_LB_PER_GAL`. | `cost_derivation_tools.py` |
| Distances | Straight line between hub points, for example Fairbanks to Allakaket 183.5 miles and Anchorage to Bethel 397.1 miles | Measured | Project table `hub_community` (x, y in EPSG:3338). Checked here against the model's own air routes (table `network_edges`, class "Air"): 181.8 miles and 397.7 miles. |
| Price per gallon on the one lane shared with the existing evidence, Fairbanks to Allakaket | $0.80 per pound times 7.1 is $5.68 per gallon. With the 42% surcharge $8.07. With the 6.25% tax as well $8.57. All 2026 dollars. | Computed | Rows above |
| The same per mile | 0.031 at base, 0.044 with the surcharge, 0.047 with surcharge and tax (183.5 miles) | Computed | Rows above |
| Per-mile ratios by table, base price | Everts Anchorage mainline, 8 hubs: mean 0.0200, lowest 0.0140, highest 0.0274. Everts Fairbanks mainline, 8 hubs: 0.0221, 0.0176, 0.0328. Everts small plane, 11 villages: 0.0275, 0.0220, 0.0397. Lynden, 5 hubs: 0.0176, 0.0153, 0.0200. | Computed | Reproduces the blind derivation exactly |
| Per-mile ratios with the November 2026 surcharge | Everts Anchorage mainline 0.0284 (0.0198 to 0.0389). Everts Fairbanks mainline 0.0313 (0.0250 to 0.0465). Small plane 0.0390 (0.0313 to 0.0564). Lynden 0.0248 (0.0215 to 0.0282), and 0.0264 with the tax. | Computed | Reproduces the blind derivation exactly |
| Fits of fixed part plus per-mile part, base price | Everts Anchorage mainline: $7.21 per gallon plus 0.0007 per mile (R-squared 0.01). Small plane without Kaktovik: $2.87 per gallon plus 0.0125 per mile (R-squared 0.81). Small plane with Kaktovik: minus $1.63 per gallon plus 0.0345 per mile (R-squared 0.67). | Computed | Reproduces the blind derivation exactly. See faults 1 to 3 below for why none of these is usable. |
| Test against the ceiling already in the addendum | The tariff at Allakaket ($5.68 to $8.07 per gallon) is 1.5 to 2.3 times the fiscal-year 2025 price ceiling there ($3.48 to $3.70 per gallon, at most 0.019 to 0.020 per mile), and 2.2 to 3.4 times the November 2007 delivery ($2.40 to $2.56 per gallon in 2026 dollars; $1.50 per gallon in 2007 dollars). At Anaktuvuk Pass the base tariff alone ($6.53 per gallon) is about equal to the whole delivered utility price, fuel included ($6.58 to $6.67 per gallon in 2026 dollars; $6.38 in fiscal-year 2025 dollars). | Computed | Addendum rows 20, 29 and 33; rows above |

**Faults found in the blind derivation.**

1. **Two printed rows were dropped without a word.** Each Everts mainline table has nine rows; the derivation
   uses eight. The missing row is Anchorage to Fairbanks at $0.40 per pound, which is $2.84 per gallon over
   257 miles: 0.0110 per gallon per mile at base and 0.0157 with the surcharge. With it, the low end of the
   "upper bound" falls from 0.0140 to 0.0110, below the addendum's point of 0.016. The fits also change
   character: the Fairbanks mainline slope goes from 0.0019 to 0.0142 per mile (R-squared 0.17 to 0.44) and the
   Anchorage fixed part from $7.21 to $4.25 per gallon. The statement that the mainline slope "is not
   distinguishable from zero" holds only after this unstated omission.
2. **The Fairbanks mainline table is the Anchorage table plus a constant.** For seven of eight destinations
   the Fairbanks price is the Anchorage price plus exactly $0.35 per pound at every weight break. These are
   through prices built on the Anchorage prices, not eight separate prices, and the freight very probably
   travels by way of Anchorage. Straight-line miles from Fairbanks are then the wrong distance: on miles by
   way of Anchorage the seven ratios average 0.0151 per gallon per mile, not 0.0205. The pooled fit of sixteen
   "hubs" counts the same eight prices twice.
3. **The one fit offered as a real distance signal exists only after one village is removed.** Dropping
   Kaktovik is a choice made after looking at the data; no document gives a reason. With all eleven printed
   rows the slope is 0.0345 per mile and the fixed part is negative. Dropping any other single village leaves
   the slope between 0.034 and 0.038. The slope is therefore somewhere between 0.0125 and 0.0345, a factor of
   2.75, and the "medium" confidence given to the ten-village fit is not earned. The fit also describes boxed
   freight handled at two terminals. Its fixed part cannot be read as a fixed part for a tanker that pumps
   straight into the village tank. That its slope (0.0125) resembles the variable part of the earlier chapter's
   rejected build-up (0.0126) is a coincidence and corroborates nothing: at Allakaket the fit gives $5.15 per
   gallon at base and $7.31 with the surcharge, 1.4 to 2.1 times the ceiling.
4. **The pooled "point" is not a statistic the script prints.** The derivation reports 0.022 without and 0.031
   with the surcharge. The mean of the 32 pairs it uses is 0.0227 and 0.0322 (median 0.0225 and 0.0319); the
   pooled mainline mean is 0.0210 and 0.0299. The stated values lie between the two and match neither.
5. **"Base as the floor of the upper bound, surcharge as its ceiling" is not a sound construction.** Nobody can
   buy at the base price in November 2026. If the tariff is a ceiling, the ceiling is what is payable:
   the price with the surcharge and with the federal tax. The tax was applied to Lynden only; it is a federal
   tax, and Everts simply does not print it. Applying it to both raises the Everts figures by 6.25%.
6. **The surcharge is a moving spot value.** The repository's record of the same Everts page shows 26%
   effective 15 July 2026 against 42% effective 11 November 2026. The blind analyst could not see that record.
   The "with surcharge" figures are November 2026 values, not 2026 averages.
7. **The distance cross-check does not check what it claims.** Agreement "within about 1%" was between the
   hub point and the community's own longitude and latitude, which are two placements of the same community,
   not of the airport. Against the model's own air routes, which are the miles the rate is multiplied by, the
   blind miles are 3.0% short to Fort Yukon (138.1 against 142.3), 2.7% short to Eagle and 2.0% short to
   Venetie, and 1.3% to 1.9% long to Huslia, Nulato and Ruby. The effect on any ratio is at most 3%.
8. **The central case carries no container.** The tariff bills gross weight, and neither carrier lists bulk
   liquid. Read as a ceiling for fuel moved under this tariff, the drum case (7.81 pounds per gallon) is the
   relevant one and is 10% higher than the central figures.
9. **Small slips.** "Rates at lower breaks are 2 to 4% higher" understates the basic rate, which is 6% above
   the 5,000-pound rate for both carriers ($1.07 against $1.01; $1.19 against $1.12). The "one standard error"
   bounds on the slope are given as 0.0100 and 0.0150; the exact values are 0.0104 and 0.0147.

**How far the result moves across reasonable values of each assumption.**

| Assumption | Reasonable values | Movement |
|---|---|---|
| Fuel surcharge | none, 26% (July 2026, repository record), 42% (November 2026) | Times 1.00, 1.26 or 1.42 |
| Federal transportation tax | not applied, or 6.25% | Plus 6.25% |
| Weight of a gallon as billed | 6.1 pounds (gasoline) to 7.81 pounds (diesel in a drum) | Minus 14% to plus 10% |
| Weight break | basic rate, 5,000 pounds, 10,000 pounds | Plus 6% to minus 2% |
| Distance basis for the village table | hub points or the model's air routes | Minus 3% to plus 2% |
| Distance basis for Fairbanks mainline | straight line or by way of Anchorage | Minus 6% to minus 44%; the mean falls 26% |
| Which rows count | with or without Anchorage to Fairbanks; with or without Kaktovik | Lowest ratio 0.0140 or 0.0110; small-plane slope 0.0125 or 0.0345 |
| Distance of the lane | 138 to 544 miles | On the mainline tables the price is $7 to $10 per gallon whatever the distance, so the per-mile ratio falls by about 40% between 290 and 544 miles |

Taken together, on the single lane Fairbanks to Allakaket the tariff-implied figure runs from $4.88 per gallon
(6.1 pounds per gallon, no surcharge) to $9.43 per gallon (7.1 pounds, surcharge, tax and drum weight), which
is 0.027 to 0.051 per gallon per mile, a factor of 1.9. Across all printed lanes the ratio runs from 0.011 to
0.056, a factor of 5. A quantity that moves this much with choices the documents do not settle is not a point.

**What the evidence is.** It is an upper bound of the loosest kind, and a consistency check. I agree with the
blind analyst that it is not a point estimate. Three qualifications apply.

- It is a bound by inference, not by anything the pages say. A scheduled freight price is a one-way price on
  an aircraft that also earns from mail, passengers and backhaul (Lynden sells backhaul to Anchorage at $0.50
  per pound). A fuel charter pays for the empty return. The pages do not show which effect is larger.
- Where it can be tested it does behave as a bound: at Allakaket and Anaktuvuk Pass the tariff is far above
  what bulk fuel freight can have cost. Where it cannot be tested it is not safe: the Anchorage to Fairbanks
  row (0.011 at base) and the long Anchorage lanes to Kotzebue and Nome (0.014 to 0.016 at base) lie at or
  below the addendum's point.
- It is not binding. On the model's air-served village lanes the payable tariff (0.031 to 0.046 with the
  surcharge, Kaktovik 0.056) is above the proposed point (0.016), above the top of the proposed range (0.024)
  and above the applied 0.025. It therefore cannot tell 0.016 from 0.025 and adds no test that either fails.

Working files for this check are in
`harness: blind_derivations/working_2026-11-17/batch2_2026-11-18/verify/plane/`:
`verify_plane.py` with `verify_plane_output.txt` (distances four ways, every ratio and fit, leave-one-out,
the ceiling test, the convergence runs), `extra_checks.py` with `extra_checks_output.txt` (the $0.35
constant, miles by way of Anchorage, every multiplier on one lane, the toolkit functions), and
`everts_recheck.txt` and `lynden_recheck.txt` (my own text extraction of the two PDFs). The blind
derivation's script and output are in `batch2/derive/plane/`.

### Derived versus assumed (new inputs only)

| # | Input | Value | Type | Reference | What changes if it is wrong |
|---|---|---|---|---|---|
| S1 | Everts general-freight prices, three tables | $0.40 to $2.12 per pound; "Rates effective April 16, 2026" | Quoted | Everts page, p. 1 and p. 2 | The ceiling moves in proportion. |
| S2 | The Everts numbers are dollars per pound | "Rate Per #", bare numbers | Assumed (reader; "#" read as pounds, dollars inferred from the "$40.00" minimum on the same page) | Everts page, p. 1 | Every Everts figure is wrong by the same factor. The chapter read the page the same way. |
| S3 | The Lynden numbers are dollars per pound | "$1.12" under "5000" in a table headed "WEIGHT (LBS)" | Assumed (reader), supported by the backhaul table (137 pounds times $0.50 is $68.50 against a $68.00 flat charge) | Lynden page, p. 1 to p. 3 and p. 5 | Every Lynden figure is wrong by the same factor. |
| S4 | Everts fuel surcharge | 42%, effective 11 November 2026 | Quoted | Everts page, p. 1 and p. 2 | Times 1.42 on every Everts figure. |
| S5 | The surcharge applies to the per-pound price, and to the small-plane table | Applied to both | Assumed (blind analyst). The page does not say what the 42% is a percentage of, and does not print it under the small-plane table. | Everts page, p. 2 | Without it the small-plane figures are 30% lower (0.022 to 0.040 in place of 0.031 to 0.056). |
| S6 | Lynden surcharge and tax | 41% effective 18 November 2026; 6.25% | Quoted. That each applies to the price before it is Assumed. | Lynden page, p. 5 | Times 1.41 and times 1.0625. |
| S7 | Everts surcharge in July 2026 | 26%, effective 15 July 2026 | Measured from the repository's own record, not from a supplied document | `friction_costs.py`, `VEHICLE_MILE_RATES_REFERENCE["Plane"]`; `03_plane.md`, Method C-i | It only shows that the surcharge moves. No figure rests on it. |
| S8 | Weight of fuel as billed | 7.1 pounds per gallon; 6.1 to 7.81 as the span | Assumed (blind analyst) | Toolkit constant for 7.1 | Minus 14% to plus 10%. |
| S9 | The 5,000-pound price applies | Heaviest Everts break | Assumed (blind analyst) | Everts page, p. 1 | The basic rate is 6% higher. |
| S10 | The carriers would accept fuel at these prices | Yes | Assumed (blind analyst). No page says so; Lynden prices "Tanks, Empty Drums" as "Contact Sales" and charges $70.00 per hazardous shipment. | Lynden page, p. 4 and p. 5 | If fuel is refused or priced by quotation, the tariff is not even a ceiling for fuel. |
| S11 | A general-freight tariff is at or above what a tanker charter costs per gallon | Upper bound | Assumed (blind analyst; kept here with the qualifications above). Tested at Allakaket and Anaktuvuk Pass only. | Addendum rows 20, 29, 33 | If scheduled freight is cross-subsidised by mail, passengers or backhaul, the tariff could lie below a charter on some lanes. |
| S12 | Straight-line miles between hub points | 138.1 to 544.0 miles | Measured | `hub_community`; checked against `network_edges` air routes | At most 3% on any village lane. |
| S13 | Fairbanks mainline freight flies direct | Direct | Assumed (blind analyst). The constant $0.35 per pound difference (Computed) points the other way. | Everts page, p. 1 and p. 2 | By way of Anchorage the Fairbanks mainline ratios fall by 26% on average. |
| S14 | Kaktovik is left out of the small-plane fit | Left out | Assumed (blind analyst, after seeing the data) | Everts page, p. 2 | With it the slope is 0.0345 per mile and the fixed part is negative. |
| S15 | Dollar year | 2026 for every tariff figure; factor 1.0 | Quoted (effective dates on both pages) | Everts page, p. 1; Lynden page, p. 1 and p. 5 | None. The base prices and the surcharges are from different months of 2026. |

### Convergence after the new evidence

Which methods count as independent points. Nothing changes.

| Method | Counts as an independent point? | Value (2026 dollars) |
|---|---|---|
| Published per-mile statements (DEC 2007 and ISER 2010, one method) | Yes | 0.0190 (1.25 cents in 2010 dollars) |
| One real delivery, Fairbanks to Allakaket, 13 November 2007 | Yes | 0.0136 (0.82 to 0.88 cents in 2007 dollars) |
| Fiscal-year 2025 utility price at Allakaket less a road-system price | No. Independent, but a ceiling. | At most 0.019 to 0.020 |
| Earlier chapter's engineering build-up | No. Its inputs are in no supplied document. | 0.0246 at 182 miles |
| **New: general-freight tariffs (Everts, Lynden)** | **No. A ceiling, and the same source as the chapter's Method C-i.** | At most 0.031 at base and 0.044 to 0.047 payable on the Allakaket lane; 0.011 to 0.056 across all printed lanes |

Why the tariffs are not a new independent method.

- The same documents: the Everts page is the page the earlier chapter already used, with identical base
  prices. The addendum already has this evidence as a "ceilings only" row.
- The same underlying price: Lynden and Everts sell the same service on the same lanes in competition
  (Anchorage to Bethel $1.12 and $1.01 per pound; to Nome $1.17 and $1.07). They are two readings of one
  market price for boxed freight and count once.
- A different quantity: boxed freight on scheduled flights, not fuel in a tanker. It is independent of the two
  counted points in documents and in year, but it measures something else, so it cannot stand beside them.

The test. Two independent verified points, 0.0190 and 0.0136; ratio of highest to lowest 1.40; geometric
mean 0.0161 (re-run with the toolkit's `convergence()`). The standard asks for three or more genuinely
independent methods within about 3 times, with inputs checked in the documents. The spread passes. The count
fails, as before: two, not three.

For openness, if a tariff figure were wrongly counted as a third point, the answer would depend entirely on
which figure was picked: the Lynden base mean (0.0176) leaves the spread at 1.40; the Everts small-plane mean
with the surcharge (0.0373) gives 2.74; the Allakaket lane with the surcharge (0.0440) gives 3.23, outside
the standard; Kaktovik with the surcharge (0.0564) gives 4.15. A "method" that can be made to pass or fail
by the choice of row and multiplier is not a method.

Ceiling test. On the route where both can be compared, the tariff ceiling ($5.68 to $8.57 per gallon) is
looser than the price ceiling the addendum already uses ($3.48 to $3.70 per gallon). It does not narrow the
range, does not move its top (0.024), and does not add to the case for or against the applied 0.025.

One thing the pages do support, in direction only. The addendum notes that an aviation-fuel price well above
the general price trend would push the true 2026 level toward the top of the range. Two carriers charging
fuel surcharges of 41% and 42% in November 2026, and one of them 26% four months earlier, is consistent with
that note. It gives no size for a tanker charter and is no reason to move the point.

### Status before and after

| | Before (addendum 2026-11-17) | After (this supplement) |
|---|---|---|
| Level and range | Provisional | Provisional (unchanged) |
| Form (pure per-mile rate, no fixed part) | Provisional | Provisional (unchanged) |
| Best estimate | 0.016 | 0.016 (unchanged) |
| Range | 0.013 to 0.024; 0.013 to 0.019 for full DC-6 or DC-4 loads over about 180 to 250 miles | Unchanged |
| Fixed part | None proposed; limited to between $0 and about $0.5 per gallon on one route | Unchanged |
| Small aircraft | Not represented; 0.05 to 0.11 | Unchanged |
| What the code carries | Applied 0.025, range 0.015 to 0.042, until the owner decides | Unchanged |

Reason. The status is held back by the count of independent point methods, and the new evidence does not add
one. It is a ceiling, it repeats a source the addendum already holds, and it lies above the ceiling already
in use. Nothing in it requires a different point or range, so none is proposed.

Proposed changes to the wording of the addendum (none applied here):

1. Methods table, row "Earlier chapter, Methods A, A-prime and C-i". Say that the Everts per-pound tariff has
   now been checked against a saved copy of the page (base prices identical to the chapter's; surcharge 42%
   effective 11 November 2026 where the chapter had 26%), and that a second carrier, Lynden, is on file.
   Recomputed on the addendum's basis, the village lanes give 0.022 to 0.032 at base and 0.031 to 0.046
   payable, with Kaktovik at 0.040 and 0.056. The row stays "Ceilings only". The Wright Air Service and
   Northern Air Cargo pages, the retail premiums and the charter award stay unverified.
2. "Ceiling test" paragraph. Add one sentence: the tariff ceiling at Allakaket is 1.5 to 2.3 times looser than
   the fiscal-year 2025 price ceiling and does not bind.
3. "Open evidence gaps", last item. The Everts tariff page is now a saved file; the other web sources are not.
4. "Open evidence gaps", short hops. Record that the two pages' minimum charges ($40.00 and $68.00 per
   shipment, reached at 37 and 57 pounds) are parcel minimums and do not size a per-flight floor.
5. "Not re-confirmed" list. Take the Everts per-pound tariff out; leave the other carriers' tariffs in.

No change is proposed to `friction_costs.py`. Its reference entry records the Everts surcharge as 26%, dated
15 July 2026. That entry is a dated record of a raw source, is not read by routing, and stays true for its
date; if the owner refreshes it, the date and the value should change together.

### Still missing

To reach Derived the segment still needs a third independent point estimate for tanker-class bulk fuel, with
its inputs in a document on file. The second batch did not supply one.

- **A charter price for bulk fuel.** A quotation, rate sheet or paid invoice from an air-fuel carrier for a
  named route and load, for example Fairbanks to Anaktuvuk Pass with 4,000 gallons. The Everts page shows
  where to ask: its links "Charters: Fuel" and "Charter Quote" lead to pages that are not in the saved file.
- **A second route.** A village utility's fuel purchase order or freight invoice that shows air freight apart
  from product (Allakaket, Anaktuvuk Pass or Noatak, with the origin airport named).
- **How Anaktuvuk Pass was supplied in fiscal year 2025.** The new plan document confirms both air and a
  seasonal ice-road link, which leaves the split unknown.
- **A measured fixed charge for a tanker flight.** The tariff fits cannot supply it (fault 3). The form stays
  Provisional until a charter invoice shows ground time or a per-flight fee.
- **Whether and how either carrier carries fuel on scheduled service.** The dangerous-goods and shipping
  guideline pages are links only. Without them the tariff is a ceiling by inference.
- **What the surcharges are a percentage of, and their history through 2026.** A surcharge schedule or the
  Lynden "Rates & Schedule PDF" (a link, not fetched) would say whether the base prices already contain fuel.
- **Routing of Fairbanks mainline freight.** A schedule or route map would confirm that it moves by way of
  Anchorage.
- **The other carriers' tariff pages and the chapter's other web sources as saved files** (Wright Air Service,
  Northern Air Cargo, the January 2026 price survey, the federal charter award).
- **An aviation cost series from 2007 to 2026**, as in the addendum. The surcharge percentages point the same
  way as that gap but do not fill it.

Not confirmed in this check: the Lynden cells hidden under the site header or the pop-up in the page images
(the last cell of the Emmonak General row, and the hazardous-material fee row) were confirmed in the PDF text
layer only; the 26% July 2026 surcharge is from the repository's record and not from a saved document.
