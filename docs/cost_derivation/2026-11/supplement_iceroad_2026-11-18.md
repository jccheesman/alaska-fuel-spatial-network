## Supplement 2026-11-18: Ice road and winter trail fuel haul (second batch of sources; proposal, nothing applied)

This supplement belongs to `addendum_ice_road.md` (2026-11-17). It reports an adversarial check of one new
blind derivation, made from the second batch of documents, for the model's `IceRoad` rate (dollars per gallon of
fuel per statute mile of model ice-road route, loaded one-way mile, empty return inside the figure). Nothing
here has been applied to `friction_costs.py`, and nothing in it calls for a change to the applied value. All
2026 figures are in 2026 dollars at CPI-U 332.243 (`index_basis_2026-11-17.md`); every source-year value is
shown next to its restated value. The check was made by one verifier and has not had a second review.

Short names. **ICAS CEDS** is the "Regional Comprehensive Economic Development Strategy, CEDS 2025-2030" of
the Iñupiat Community of the Arctic Slope (file `ICAS-CEDS-2025-2030-v1.0-compressed.pdf`). **Trails memo** is
the May 2019 draft "Winter Trails: Conditions, Issues, and Trends" of the Northwest Alaska Transportation Plan
(file `nwatpWinterTrailsTechMemo-2019.pdf`). **Marine memo** is the same plan's marine and riverine conditions
memo (file `nwatpMarineRiverineConditions.pdf`). **ACFR** is the North Slope Borough's annual comprehensive
financial report for fiscal year 2023 (file `FY23-NSB-ACFR.pdf`). **NSB** is the North Slope Borough. **CWAT**
is the borough's Community Winter Access Trails programme. **PAR** is not expanded in the ICAS CEDS. The new
files are in `batch2/src/` of the working folder; they were not found under `cost_derivation_resources/` on
the harness branch that was read. "PDF p." is the page of the PDF file.

### What the new documents add

The second batch holds no tariff, contract, invoice or quoted price for hauling fuel over an ice road, a snow
road or a winter trail. A keyword search of the nine source texts (ice road, snow road, winter trail, winter
road, rolligon, cat train, sled, tractor, overland, per cubic yard and others) found usable winter-haul
content in four documents only; the barge-landing report mentions a river ice road at two villages and gives
no figure. What the four add is this.

1. **One second-hand freight cost on a winter route.** The ICAS CEDS says that a 2014 North Slope Borough
   report estimated the cost of transporting gravel from Utqiaġvik to Atqasuk by ice road at $450 to $600 per
   cubic yard (PDF p. 76). The underlying report is not among the supplied documents, the sentence carries no
   footnote, and it does not say what vehicle was used, what load it carried, how much gravel the estimate
   covers, or whether the figure includes the gravel itself, loading, or building the ice road. This is the
   only transport cost in the batch that touches the segment, and it is for gravel, not fuel.
2. **A construction cost per mile for the borough's snow roads.** The trails memo says the borough built about
   300 miles of snow roads in the winters of 2017-18 and 2018-19 "at a cost of about $5,000 per mile" (PDF
   p. 5). That is $6,616 per mile in 2026 dollars (2018 dollars assumed, factor 1.3231). The addendum said the
   public cost of the trails could not be put on a per-mile basis because no mileage was given; it now can be,
   for construction only. It still cannot be put on a per-gallon basis, because no document gives the gallons
   or the share of trail traffic that is fuel.
3. **A budget line.** The ACFR lists "$4.7 million on community winter access trails" among the supplemental
   increases to the fiscal-year 2023 General Fund expenditure budget (PDF p. 26, printed p. 12). It is a
   budget increase, not an expenditure, and the report gives no miles, routes or split of the amount.
4. **Trail lengths.** The trails memo's Table 2 gives "Utqiagvik – Atqasuk 60" miles and "Deadhorse –
   Nuiqsut 60" miles (PDF p. 6). The ICAS CEDS says Atqasuk is "60 miles south of Barrow" (PDF p. 9) and
   "about 60 miles southwest of Utqiaġvik" (PDF p. 10). These are round figures; the model's ice path between
   the same two places is 68.46 statute miles and the straight line is 57.1 statute miles (addendum, input 37).
5. **Definitions and vehicles.** The trails memo defines a snow road as "constructed of packed snow suitable
   for snowmachines, dog teams, and four-wheel-drive automobiles" and says of both snow roads and ice roads
   that "construction methods dictate suitability for heavy equipment" (PDF p. 3). The ICAS CEDS says
   "Residents and organizations utilize snowmachines, rolligons, and trucks with mattrack conversions to
   traverse the ice roads and ice trails" (PDF p. 45). Neither gives a load, a speed or a cost.
6. **Which places are served in winter (no costs).** Nuiqsut: "Winter ice road access to the Dalton Highway
   allows bulk freight and fuel deliveries" (marine memo, PDF p. 34), and access to the Dalton Highway "four
   months out of the year via a restricted access ice road" (ICAS CEDS, PDF p. 44). Anaktuvuk Pass: "Fuel and
   cargo flown in. Seasonal use of ice road connection to the Dalton Highway" (marine memo, PDF p. 34).
   Bettles and Evansville: "Winter road access via trail to Dalton Highway" (marine memo, PDF p. 52).
   Kuskokwim River: "over 250 miles of ice road" in 2017, which "Allows residents of smaller villages to drive
   to Bethel and stock up on fuel and groceries" (trails memo, PDF p. 13). Atqasuk: "the community has
   maintained a supply of gravel by hauling gravel from Utqiaġvik via ice road" and "requires about 1,800
   cubic yards of gravel per year" (ICAS CEDS, PDF p. 75). No document in the batch says how Atqasuk's fuel
   is delivered, which is the gap the addendum already records (input 34).
7. **Retail prices the blind derivation did not use.** The ICAS CEDS reprints two state price surveys (PDF
   p. 57). Gasoline in winter 2024 was $9.02 per gallon in Atqasuk against $6.90 in Utqiaġvik and a mean of
   $7.33 in Kaktovik, Point Hope and Wainwright. Commercial heating fuel in summer 2023 was $9.32 in Atqasuk
   against a mean of $10.54 in the same three coastal villages. The gasoline differences are $2.12 and $1.69
   per gallon in 2024 dollars, which is $2.25 and $1.79 in 2026 dollars and 0.033 and 0.026 dollars per
   gallon per statute mile on the 68.46-mile path. The heating-fuel difference is negative (minus $1.22 per
   gallon in 2023 dollars). These are retail prices from different vendors, they belong to the same family as
   the addendum's Atqasuk price difference, and the two series disagree in sign, so they are recorded as a
   caution and are not a method.

The Noatak proposal and the borough's 2020 winter-trails sheet are in the batch folder again; both were
already used in the addendum and add nothing new.

### The new method, checked

The blind derivation converts the gravel estimate into a fuel rate. It restates the price to 2026 dollars,
assumes a weight for a cubic yard of gravel, assumes that a vehicle carries the same weight of fuel as of
gravel, and divides by the route length. Its arithmetic was rerun and reproduces exactly (`calc.py` gives the
same output as `out.txt`). Every quotation it relies on was found in the source text, and the three that carry
numbers were also read on the rendered page.

| Step | Value | Type | Reference |
|---|---|---|---|
| Gravel haul cost, Utqiaġvik to Atqasuk by ice road | $450 to $600 per cubic yard, midpoint $525 | Quoted | ICAS CEDS, PDF p. 76: "A 2014 NSB PAR estimated that transporting gravel from Utqiaġvik to Atqasuk via ice road cost between $450 and $600 per cubic yard." Confirmed in the text and on the page image. |
| Dollar year of that estimate | 2014 | Assumed (blind analyst) | The document gives only the year of the report. |
| Factor from 2014 to 2026 | 1.4034 (332.243 divided by 236.736) | Computed | `index_basis_2026-11-17.md` |
| Cost in 2026 dollars | $631.53 to $842.06 per cubic yard, midpoint $736.80 | Computed | From the three rows above |
| The estimate covers transport only: no gravel purchase, no loading, no ice-road construction | Yes at the point; $100 per cubic yard of gravel removed in the low case only | Assumed (blind analyst) | The source is silent. Checked: no supplied document states the scope. |
| Weight of one cubic yard of gravel | 2,800 pounds (range 2,200 to 3,400) | Assumed (blind analyst) | Not in any supplied document |
| Weight of one gallon of diesel | 7.1 pounds (range 7.0 to 7.2) | Assumed (blind analyst) | Not in any supplied document |
| The haul vehicle carries the same weight of fuel as of gravel | Yes | Assumed (blind analyst) | No vehicle or load is stated for the gravel haul |
| Gallons of fuel that weigh as much as one cubic yard | 394.4 gallons | Computed | 2,800 divided by 7.1 |
| Cost per gallon-equivalent over the route | $1.868 per gallon in 2026 dollars ($1.331 in 2014 dollars) | Computed | $736.80 divided by 394.4 |
| Route length used by the blind derivation | 60 statute miles | Quoted | Trails memo, PDF p. 6, Table 2: "Utqiagvik – Atqasuk" "60"; ICAS CEDS, PDF pp. 9 and 10. Confirmed. |
| Blind result | $0.0311 per gallon per statute mile (low case $0.0139, high case $0.0447) | Computed | Reproduced: 0.03114, 0.01387, 0.04465 |
| Route length in the model | 68.46 statute miles | Measured | Addendum input 37 (harness `fuel_network.duckdb`, ice path between transfer edges 92909 and 93034); read in `record/ice_road_checks/net2_rerun_output.txt`, not rerun |
| Result on the model's route length | $0.0273 per gallon per statute mile in 2026 dollars ($0.0194 in 2014 dollars); $7.69 per short ton per statute mile | Computed (this check) | $1.868 divided by 68.46; `batch2/verify/iceroad/verify.py` |
| The loaded one-way mile carries the empty return | Yes | Assumed (blind analyst and this check) | A gravel haul returns empty; the source does not say so |
| Snow-road construction cost | "about $5,000 per mile" for "approximately 300 miles", winters 2017-18 and 2018-19; $6,616 per mile in 2026 dollars | Quoted; restated value Computed; the 2018 dollar year is Assumed | Trails memo, PDF p. 5. Confirmed in the text and on the page image. |
| Fuel gallons carried over the snow roads each winter | 300,000 gallons at the point (100,000 to 709,859) | Assumed (blind analyst) | Not in any document. The upper figure is 1,800 cubic yards of gravel turned into gallons, which is not a fuel volume. |
| Construction spread over fuel | $0.011 per gallon per statute mile (range $0.005 to $0.066) | Computed from an Assumed volume | Reproduced: $6,616 divided by 300,000 gallons, halved for two winters |
| Fiscal-year 2023 trails budget line | $4.7 million in 2023 dollars ($5.12 million in 2026 dollars) | Quoted | ACFR, PDF p. 26 (printed p. 12). Confirmed in the text and on the page image. |

Errors and weak points found. None is an arithmetic error; the sums are right and the inflation factors match
the index sheet.

1. **Distance basis.** The rate is defined per statute mile of the model's route, and the addendum's Atqasuk
   price difference is divided by the measured 68.46 miles. The blind derivation divided by the documents'
   round 60 miles and did not query the network tables. On the same basis as the existing methods the figure
   is $0.0273, not $0.0311, per gallon per statute mile (14% lower).
2. **The point takes the most favourable reading of an unknown scope.** It assumes the estimate holds no
   gravel purchase, no loading and no road construction. Each of those, if it is inside the figure, lowers the
   haul rate, and none can raise it. The point is therefore an upper reading of the haul, not a centre.
3. **The regime label is an assumption.** The summary calls the evidence a "truck-type haul on a built ice
   road". The source does not name the vehicle. In the addendum this route is the example of the sled regime,
   and the converted figure lands at the sled regime's level, not the truck regime's. At the truck regime's
   $0.0068 per gallon per statute mile the same cubic yard would cost $184 in 2026 dollars, which is $131 in
   2014 dollars, or 22% to 29% of the quoted $450 to $600.
4. **The construction add-on is not a usable estimate.** Its unit is right (dollars per mile divided by
   gallons is dollars per gallon per mile), but the gallons are assumed, the whole cost is charged to fuel
   although the trails serve all traffic, and the choice between one winter and two winters is unresolved.
   With Atqasuk's measured utility gallons (274,877 gallons in fiscal year 2025, addendum input 31) in place
   of the assumed 300,000, the same sum gives $0.024 for one winter and $0.012 for two, which shows that the
   answer is set by the allocation and not by the evidence. Trail construction is also outside the scope of
   the model's rate (addendum, "What the figure includes and excludes").
5. **The fiscal-year 2023 cross-check is not valid.** It divides a 2023 supplemental budget increase by miles
   built in 2017 to 2019. The numerator is a budget increase, not a cost, and the two figures come from
   different years. The blind derivation showed it as a sensitivity only; it should be dropped.
6. **Page reference.** The Bettles and Evansville sentence is on PDF p. 52 (printed p. 46) of the marine
   memo, not p. 34. The Nuiqsut and Anaktuvuk Pass sentences are on PDF p. 34 (printed p. 28) as stated.
7. **Noatak capital.** The input list again reads the $425,000 request as the tractor. The addendum
   established from the image page that $350,000 is the tractor, sled and shipment and $75,000 is permitting.
   The figure is not used in the new rate, so nothing moves.
8. **The 1,800 cubic yards** is what Atqasuk "requires" each year (ICAS CEDS, PDF p. 75), not a volume hauled
   and not the volume behind the 2014 estimate.

How far the converted figure moves. The centre is $0.0273 per gallon per statute mile (midpoint price, 2,800
pounds per cubic yard, 68.46 miles). One input is changed at a time.

| Input changed | Result (dollars per gallon per statute mile, 2026 dollars) | Change |
|---|---|---|
| Price at $450 or $600 per cubic yard (2014 dollars) | 0.0234 or 0.0312 | minus 14% or plus 14% |
| Gravel at 3,400 or 2,200 pounds per cubic yard | 0.0225 or 0.0347 | minus 18% or plus 27% |
| Fuel vehicle carries 120% or 80% of the gravel load by weight | 0.0227 or 0.0341 | minus 17% or plus 25% |
| Route of 75, 60 or 57.1 statute miles | 0.0249, 0.0311 or 0.0327 | minus 9%, plus 14% or plus 20% |
| Figure includes the gravel, taken at $100 per cubic yard in 2014 dollars | 0.0221 | minus 19% |
| Figure includes a snow road built at $5,000 per mile (2018 dollars) over 60 miles for 1,800 cubic yards, which is $157 per cubic yard in 2014 dollars | 0.0191 | minus 30% |
| Figure includes both | 0.0139 | minus 49% |
| Dollar year 2013 in place of 2014 | 0.0277 | plus 2% |
| Diesel at 7.0 or 7.2 pounds per gallon | 0.0269 or 0.0277 | minus 1% or plus 1% |

Price range and gravel weight together, on the transport-only reading, give $0.019 to $0.040 per gallon per
statute mile. With the scope and load assumptions stacked as well the span is $0.008 to $0.050, about six
times, and is not a usable range. The $157 per cubic yard for road construction is an illustration: it uses
the snow-road cost of a later programme and the annual gravel need, and a road built for loaded gravel
vehicles may cost more.

What the new evidence is. The gravel conversion is a **consistency check** for the Utqiaġvik to Atqasuk route,
and a soft upper reading of the haul on that route. It is **not an independent point estimate**: it is not a
fuel price; three of its inputs (gravel weight, equal load by weight, transport-only scope) are in no
document; the source is a second-hand planning estimate with no vehicle, load or volume; and the underlying
report was not seen. The construction add-on is **nothing** for the rate: it is unidentified and outside the
rate's scope. Its only use is as a fact for the scope note, the construction cost per mile.

Independence. The gravel figure comes from a different document and a different underlying price than either
sled-regime method in the addendum (the Noatak cost build-up and the Atqasuk utility price difference). It is
not independent in route or operator: it is the same Utqiaġvik to Atqasuk leg as the price difference, and
both are North Slope Borough costs. It says nothing about the truck regime, about any other route, or about
how gallons divide between the regimes.

### Derived versus assumed (new inputs only)

| # | Input | Value | Type | Reference | What changes if it is wrong |
|---|---|---|---|---|---|
| S1 | Gravel haul estimate | $450 to $600 per cubic yard | Quoted (second-hand) | ICAS CEDS, PDF p. 76 | The check moves in proportion: minus 14% to plus 14% across the range. |
| S2 | Dollar year of S1 | 2014 | Assumed (blind analyst) | The source says "A 2014 NSB PAR" | One year earlier adds 2%. |
| S3 | CPI-U factor 2014 to 2026 | 1.4034 | Computed | `index_basis_2026-11-17.md` | None; checked. |
| S4 | Scope of S1: transport only | Yes | Assumed (blind analyst) | None | If the gravel or the road building is inside, the haul reading falls by 19% to 49%. This is the largest unknown. |
| S5 | Weight of gravel | 2,800 pounds per cubic yard | Assumed (blind analyst) | None | Minus 18% to plus 27% across 3,400 to 2,200 pounds. |
| S6 | Equal load by weight for gravel and fuel | Yes | Assumed (blind analyst) | None | Plus 25% if a fuel vehicle carries 80% of the gravel weight. |
| S7 | Weight of diesel | 7.1 pounds per gallon | Assumed (blind analyst) | None | About 1%. |
| S8 | Vehicle on the gravel haul | Not known | Assumed by the blind analyst to be a truck | ICAS CEDS, PDF p. 45, lists "snowmachines, rolligons, and trucks with mattrack conversions" for the region and does not link any of them to the gravel haul | The figure cannot be assigned to the truck regime or the sled regime on the documents. |
| S9 | Route length in the documents | 60 statute miles | Quoted | Trails memo, PDF p. 6, Table 2; ICAS CEDS, PDF pp. 9 and 10 | Used by the blind derivation; gives 0.0311. |
| S10 | Route length in the model | 68.46 statute miles | Measured | Addendum input 37 | Used here so that the check has the same basis as the price difference; gives 0.0273. |
| S11 | Converted gravel haul | $0.0273 per gallon per statute mile | Computed from S1 to S7 and S10 | `batch2/verify/iceroad/verify.py` | Follows its inputs; four of them are Assumed. |
| S12 | Snow-road construction | About $5,000 per mile for about 300 miles | Quoted | Trails memo, PDF p. 5 | Scope note only. |
| S13 | Dollar year of S12, and whether it is per winter | 2018; not known | Assumed (blind analyst) | The source names the winters 2017-18 and 2018-19 | The 2026 value is $6,616 per mile at 2018 dollars and $6,498 at 2019 dollars. The 2020 state sheet's request of $1,672,077 is $5,574 per mile if it covered the same 300 miles, which the sheet does not say. |
| S14 | Fuel gallons over the snow roads | 300,000 gallons a winter | Assumed (blind analyst) | None | The construction add-on is inversely proportional to it. Not used. |
| S15 | Trails budget line, fiscal year 2023 | $4.7 million | Quoted | ACFR, PDF p. 26 (printed p. 12) | Not used: a budget increase with no miles. |
| S16 | Atqasuk gravel need | About 1,800 cubic yards a year | Quoted | ICAS CEDS, PDF p. 75 (its footnote 74 cites the Atqasuk 2017 Comprehensive Plan) | Used only to illustrate S4. |
| S17 | Retail gasoline, winter 2024 | Atqasuk $9.02; Utqiaġvik $6.90; Kaktovik $7.50; Point Hope $7.60; Wainwright $6.89 per gallon | Quoted (second-hand, state price survey) | ICAS CEDS, PDF p. 57, Table 22 | Caution only; different vendors. |
| S18 | Commercial heating fuel, summer 2023 | Atqasuk $9.32; Kaktovik $10.00; Point Hope $10.36; Wainwright $11.25 | Quoted (second-hand; the table prints no unit) | ICAS CEDS, PDF p. 57, Table 23 | Caution only; the difference is negative. |

### Convergence after the new evidence

Values are in dollars per gallon per statute mile, 2026 dollars at CPI-U 332.243. The methods that count as
independent points are the same three as in the addendum: the truck build-up (0.0068), the corrected sled
build-up (0.0255) and the Atqasuk price difference (0.0257). The gravel conversion is shown in the tests so
that its effect can be seen, but it is not counted.

| Test | Points | Spread | Reading |
|---|---|---|---|
| Sled regime, as in the addendum | 0.0255; 0.0257 | 1.01 | Two families agree; there are only two |
| Sled regime with the gravel check on the model's 68.46 miles | adds 0.0273 | 1.07 | Consistent. Not a third independent method. |
| Sled regime with the gravel check as submitted (60 miles) | adds 0.0311 | 1.22 | Consistent |
| Sled regime with the gravel check at the ends of its conversion band | adds 0.019 or 0.040 | 1.33 or 1.56 | Consistent across the band |
| Statewide, the three points counted | 0.0068; 0.0255; 0.0257 | 3.81 | Fails about 3x, as before |
| Statewide with the gravel check on 68.46 miles | adds 0.0273 | 4.04 | Fails; slightly wider |
| Statewide with the gravel check as submitted | adds 0.0311 | 4.61 | Fails |

Against the standard (three or more genuinely independent methods within about 3x, inputs checked in the
documents):

- **Statewide single rate.** Not met, and the new evidence does not bring it closer. The disagreement is
  between the two regimes, and the new figure sits with the higher one.
- **Sled regime.** Two independent families as before. The gravel check agrees with them (ratio 1.07 on the
  same route length; $1.87 per gallon-equivalent for the route against the price difference of $1.76 per
  gallon). It cannot be the third method, because it is a converted figure for another commodity that rests
  on four assumptions, and because it shares its route and operator with the price difference.
- **Truck regime.** Nothing new. The documents confirm that Nuiqsut receives bulk fuel over a winter ice road
  and give no cost.

Bounds. None is broken. The converted figure (0.0273) is above the upper end of the range coded today (0.025)
and inside the verifier's range (0.006 to 0.030). It is a third reading on this route above 0.025, after the
straight-line Atqasuk reading (0.0308) and the slow sled variant (0.0351) named in the addendum. It is 2.7
times the carried $0.010, which is the bias the addendum already states for Atqasuk-type legs.

### Status before and after

| Part | Before | After | Reason |
|---|---|---|---|
| Statewide single rate (what the model uses) | **Assumed** | **Assumed** (no change) | No tariff, contract or invoice for a winter fuel haul was added. The counted points are the same three and still spread 3.81 times. |
| Sled regime level, about $0.026 per gallon per statute mile | Would be **Provisional** if the model carried it separately; it does not | The same | The gravel check agrees with the level on the same route but is not an independent method. |
| Truck regime level, about $0.007 per gallon per statute mile | **Assumed** | **Assumed** (no change) | No new evidence. |
| Fixed part per delivery | **Assumed**, not billed | **Assumed**, not billed (no change) | No new evidence; the blind derivation identifies none. |

Point and range. Nothing changes. The model keeps $0.010 per gallon per statute mile, labelled Assumed, with
the coded range of $0.004 to $0.025. The verifier's reading of $0.013 and range of $0.006 to $0.030 from the
addendum stand, not ready to apply. The evidence does not require a move: the new figure is inside the
verifier's range, and it bears on one route that the addendum already covers.

Proposed changes to the addendum's text (none to a number the model uses):

1. Add one row to the methods table: "Gravel haul, Utqiaġvik to Atqasuk, converted to fuel by weight.
   Counted as independent: no (consistency check). $0.0273 per gallon per statute mile on 68.46 miles
   ($0.0311 on the documents' 60 miles); conversion band $0.019 to $0.040; as low as $0.014 if the gravel and
   the road building are inside the figure. ICAS CEDS, PDF p. 76."
2. In "What the figure includes and excludes", replace the statement that trail construction cannot be put on
   a per-mile basis with: about $5,000 per mile for about 300 miles of snow road in the winters of 2017-18
   and 2018-19 (trails memo, PDF p. 5), which is $6,616 per mile in 2026 dollars; it stays outside the rate
   and cannot be turned into a per-gallon figure, because the gallons and the share of traffic that is fuel
   are not known. Add the fiscal-year 2023 budget line of $4.7 million (ACFR, PDF p. 26) beside the 2020
   sheet's figures.
3. In the open evidence gaps, add the 2014 North Slope Borough report that the ICAS CEDS cites (item 1 below).
4. Beside the Atqasuk price-difference row, note the two retail series from ICAS CEDS PDF p. 57: gasoline
   gives $0.026 to $0.033 per gallon per statute mile, commercial heating fuel gives a negative difference.
5. Beside the note on the season comments (January to April against January to March), add that the ICAS
   CEDS gives Nuiqsut road access "four months out of the year" (PDF p. 44).

### Still missing

A status above Assumed for the statewide rate, or a counted third method for either regime, still needs a
kind of evidence that neither batch holds. In order of value:

1. The 2014 North Slope Borough report behind the gravel figure. It would show the vehicle, the load per
   trip, the volume, the route length and whether the price holds the gravel, the loading and the ice road.
   With those, the gravel haul could become a real freight rate for this route. The Atqasuk 2017
   Comprehensive Plan, which the ICAS CEDS cites for the gravel supply, may hold the same detail.
2. A haul invoice, contract rate or purchase order for one Alaska winter fuel haul (addendum, gap 1). This
   remains the single missing piece for the skill's standard.
3. A record of how Atqasuk's fuel was delivered in fiscal year 2025, and a laid-in fuel price at Utqiaġvik
   (addendum, gap 3). The new documents describe gravel and residents' freight on this route and are silent
   on fuel.
4. Truck-regime price evidence: a laid-in price at Deadhorse for the Nuiqsut leg, or a carrier's ice-road
   surcharge from Bethel (addendum, gaps 2 and 4). The new documents confirm the modes and give no cost.
5. A regime flag on the network's ice edges and gallons by regime (addendum, gap 5). The trails memo's
   Figure 4 maps the borough's snow-road routes and could help draw the flag, but it prints no lengths for
   them.
6. Gallons or tons moved over the borough's snow roads each winter, and what the "$5,000 per mile" covers
   (one winter or two, construction only or upkeep as well). Without them the public cost of the trails stays
   a scope note.
7. A load figure for the vehicles that run on these routes, for fuel and for gravel (addendum, gap 7).

Not confirmed in this check. The 68.46-mile ice path was read from the addendum's rerun output and was not
recomputed from the network. The underlying 2014 report, the Atqasuk 2017 Comprehensive Plan and the state
price surveys reprinted in the ICAS CEDS were not seen. No link was opened, and none is recorded for the new
files.

Working files, all under `harness: blind_derivations/working_2026-11-17/`:
`batch2/derive/iceroad/calc.py` and `out.txt` (the blind derivation, as run);
`batch2/verify/iceroad/verify.py` and `verify_out.txt` (this check: rerun, restatement on 68.46 miles,
sensitivities, construction, retail prices, convergence); `batch2/verify/iceroad/find_quotes.py`, `find2.py`,
`kw.py` and `ctx.py` (quotation and keyword searches of the page-split texts);
`batch2/verify/iceroad/img/` (ICAS CEDS p. 76 and trails memo pp. 5 and 6, rendered);
`batch2/extracts/img/nsb_acfr_fy23_p26-026.png` (ACFR p. 26).
