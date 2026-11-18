## Supplement 2026-11-18: River barge (shallow-draft tug and fuel barge from a river hub to a river village) (second batch of sources; proposal, nothing applied)

This supplement belongs to `addendum_river_barge.md` (2026-11-17). It reports an adversarial check of one new
blind derivation, made from the second batch of documents, for the river part of the model's `Barge` rate. Nothing
here has been applied to `friction_costs.py`, and nothing in it calls for a change to the applied value, the
provisional point or the provisional ranges. All 2026 figures are in 2026 dollars at CPI-U 332.243
(`shared/index_basis_2026-11-17.md`); every source-year value is shown next to its restated value. The check was
made by one verifier and has not had a second review.

Short names. **Phase 1 report** is "Alaska Barge Landing System Design, Statewide, Phase 1", final report of
January 2009, prepared by URS Corporation for the U.S. Army Engineer District, Alaska (file
`alaskabargelandingsystemdesignstatewidephase1.pdf`). **Marine memo** is the draft "Marine and Riverine
Transportation: Conditions, Issues, and Trends" of the Northwest Alaska Transportation Plan, 2019 (file
`nwatpMarineRiverineConditions.pdf`). **Beaver plan** is the 2016 draft Beaver Community Plan (file
`2016-DRAFT-Beaver-Community-Plan-V10.pdf`). **ISER** is the Institute of Social and Economic Research; "ISER 2010"
is its report "Components of Alaska Fuel Costs" used in the addendum. A **channel mile** is a statute mile along
the river in the project network, as in the addendum. "PDF p." is the page of the PDF file, with the printed page
in brackets. The new files are in `batch2/src/` of the working folder.

### What the new documents add

The second batch holds no tariff, contract, invoice or quoted price for carrying fuel on a river. It holds one
price that touches the segment at all, and a set of facts about vessels, draft, schedules and low water.

1. **One day rate, for construction barging.** The Phase 1 report says, in its chapter on construction costs:
   "Recently, barging costs in this region have run $12,000 to $15,000 per day" (PDF p. 166 [148]). The region is
   western Alaska (the same paragraph begins "Construction costs in western Alaska are notoriously high"). The
   sentence sits between a labour cost per worker and a list of construction unit prices. It does not say what
   vessels the rate covers, whether fuel and crew are inside it, or whether the barging is on a river or along the
   coast. With 2008 dollars assumed, it is 18,517 to 23,147 dollars per day in 2026 dollars, mid-point 20,832.
2. **Vessel sizes and drafts.** Village-delivery barges are "120 to 200 feet (ft) in length overall (LOA), and 40
   to 55-ft wide. Most have a draft of less than 6-ft of water"; operators use "80-ft by 24-ft lighter vessels
   with shallow drafts (3-ft) to reach shallow upper river locations" (Phase 1 report, PDF p. 26 [8]). "The Tanana
   River has a maximum draft of 4.5 feet for barges" (marine memo, PDF p. 30 [24]). "Barges that run up the
   Kuskokwim River usually draft about 3-feet" (Phase 1 report, PDF p. 93 [75]).
3. **A schedule for the middle Yukon.** The marine memo's Table 3 (PDF p. 22 [16]) gives Ruby Marine's sailings
   per year: Upper Yukon (Rampart) 3, Tanana to Galena 16, Galena to Kaltag 10, Koyukuk River communities 2. The
   same page says the company "provides both cargo and fuel service, utilizing vessels that haul both commodities
   as opposed to separate fuel and cargo barges". The table gives no year, no days per sailing and no gallons.
4. **Who supplies the middle Yukon.** "All of the Middle Yukon communities within the NWATP study area and
   Koyukuk River communities from Koyukuk to Hughes are served from Nenana" (marine memo, PDF p. 30 [24], citing a
   2013 plan). This bears on an assumption already in the addendum (the supply point of Tanana, Ruby and Koyukuk).
5. **Low-water statements, direction only.** River operators are "delivering lighter loads to reduce draft, which
   requires more trips" (marine memo, PDF p. 11 [5]). At Shungnak fuel barges "must lighten their loads to
   navigate shallow waters, often requiring 3 trips to deliver all fuel orders" (marine memo, PDF p. 41 [35], a
   table row that cites a 2008 village plan and the Phase 1 report). Ambler can be reached "approximately every
   other year" (Phase 1 report, PDF p. 131 [113]; marine memo, PDF p. 36 [30]); so can Shungnak (Phase 1 report,
   PDF p. 132 [114]). There is "only a 50 percent chance" of getting into Kiana (PDF p. 130 [112]). Construction
   contractors reach Kobuk village "approximately every 5 years" (PDF p. 133 [115]). On the Koyukuk River,
   delivery "beyond Hughes is difficult due to shallow water conditions" (marine memo, PDF p. 23 [17]).
6. **Seasons and one current speed.** The middle Yukon "is generally ice-free from mid-May through mid-October"
   (Phase 1 report, PDF p. 62 [44]); the upper Yukon "from mid- June through mid-September" (PDF p. 67 [49]). The
   Kobuk River "is about 280 miles long" and "has a current speed of 3 to 5 mph" (PDF p. 128 [110]).
7. **Beaver.** "Fuel is flown in by plane because of the tank farm's location. The Yukon River's current channel
   has changed and made it difficult to deliver fuel by barge" (Beaver plan, PDF p. 20 [19]). Crowley "makes two
   trips up the Yukon River from Nenana", for freight (PDF p. 21 [20]). The landing is "2.9 miles downstream from
   the community" (PDF p. 27 [26]).

Every quotation above was confirmed in the text layer of the document on 2026-11-18, and Table 3 was also read
from the rendered page image. No quotation that the blind derivation relies on failed to confirm. Three things
that the blind derivation needed are in no document and could not be confirmed: the dollar year of the day rate,
what the day rate covers, and whether the rows of Table 3 are separate round trips or overlap.

### The new method, checked

The blind derivation builds a cost per gallon as: day rate times round-trip days, divided by gallons per trip.
Round-trip days are the one-way channel miles divided by miles made per day on each leg, plus a fixed number of
days in port. The table gives each step as the blind derivation made it, with the type under `CONVENTIONS.md`.

| Step | Value | Type | Reference (document and page) |
|---|---|---|---|
| Day rate in source dollars | 12,000 to 15,000 dollars per day; mid-point 13,500 | Quoted | Phase 1 report, PDF p. 166 [148] |
| Dollar year of the day rate | 2008 | Assumed (blind analyst; the report says "Recently" and is dated January 2009) | Same page |
| Day rate in 2026 dollars | 18,517 to 23,147 dollars per day; mid-point 20,832 | Computed (times 1.5431) | `index_basis_2026-11-17.md` |
| What the day rate covers | A river tug and fuel barge with crew and tug fuel | Assumed (blind analyst). The document describes construction barging and names no vessel. | Same page |
| Barge size and draft | 120 to 200 feet by 40 to 55 feet; Tanana River limit 4.5 feet | Quoted | Phase 1 report, PDF p. 26 [8]; marine memo, PDF p. 30 [24] |
| Fuel a barge can carry at 4.5 feet | 118,445 gallons for a barge of 120 by 40 feet; 157,927 gallons for 160 by 40 feet | Assumed (block coefficient 0.9, empty weight 0.0375 long tons per square foot of deck, 7.1 pounds per gallon; none is in a document) | `batch2/derive/river/river_buildup.py` |
| Gallons per trip | 100,000 gallons (range 60,000 to 150,000) | Assumed (blind analyst) | Same script |
| Speed and running hours | 4.5 miles per hour against the current, 9 miles per hour with it, 20 hours a day | Assumed (blind analyst). The only speed in the documents is the Kobuk River's current. | Phase 1 report, PDF p. 128 [110] for the current only |
| Days in port per delivery | 3.0 days (range 1.5 to 7) | Assumed (blind analyst) | None |
| One-way channel miles from Nenana | Tanana 148.6; Galena 316.7; Kaltag 402.9 | Assumed winding factors (1.5 on the Tanana River, 1.15 on the Yukon River) applied to Measured straight segments between hubs | `hub_community` table of the harness database |
| Per-mile part | 0.0035 dollars per gallon per channel mile (0.00347; range 0.0015 to 0.0099) | Computed from one Quoted and three Assumed inputs | 20,832 times (1/90 + 1/180) days per mile, divided by 100,000 gallons |
| Fixed part per delivery | 0.63 dollars per gallon (0.625; range 0.19 to 2.70) | Computed from one Quoted and two Assumed inputs | 20,832 times 3.0 days, divided by 100,000 gallons |
| Totals | Tanana 1.14, Galena 1.72, Kaltag 2.02 dollars per gallon | Computed | Fixed part plus per-mile part times the miles above |
| Season and tows needed | 31 sailings need 270 tow-days in a season of about 150 days, or 1.8 tows | Quoted sailings and season; Computed on Assumed trip lengths | Marine memo, PDF p. 22 [16]; Phase 1 report, PDF p. 62 [44] |
| Low-water multiplier | 3 times (range 1 to 6) on the Kobuk River and upper Koyukuk River | Assumed reading of the Quoted statements in item 5 above | Marine memo, PDF p. 41 [35]; Phase 1 report, PDF p. 130 to 133 [112 to 115] |

**Re-run.** A copy of the blind script was run for this record and reproduces its printed output exactly. The
inflation factor is right (332.243 divided by 215.303 is 1.5431). A separate recomputation by the verifier
(`batch2/verify/river/check_river.py`) gives the same slope, fixed part and totals.

**Errors and corrections.**

1. **Distance basis.** The blind derivation's channel miles come from assumed winding factors, although the
   project network gives measured channel miles (`verify2/river/dist_check.json`). Its distances are short by
   9.3% at Tanana (148.6 against 163.8 miles), 4.1% at Galena (316.7 against 330.1), 2.7% at Kaltag (402.9 against
   413.9), 13.9% at Beaver (332.5 against 386.1), 21.5% at Huslia (442.1 against 562.9), 29.2% at Hughes (533.1
   against 752.6), 13.3% at Shungnak (211.2 against 243.6) and 12.1% at McGrath (367.4 against 418.2). On measured
   miles its base totals become 1.19 dollars per gallon at Tanana, 1.77 at Galena and 2.06 at Kaltag (up 2% to
   5%), 2.58 at Huslia (up 19%) and 3.24 at Hughes (up 31%).
2. **A unit slip in the summary.** The summary calls 0.0054 dollars per gallon a figure "per straight-line mile".
   It is the Galena total divided by the assumed channel miles (1.72 divided by 316.7). Per straight-line mile
   from Nenana (232.4 miles) the same total is 0.0074 dollars per gallon.
3. **Direction of the loaded leg.** The derivation describes the slow leg as loaded and upstream and the fast leg
   as "downstream empty". From Nenana to Tanana, Ruby, Galena and Kaltag the loaded leg runs downstream and the
   empty return runs upstream. The formula adds both legs, so no figure changes; the description is right only
   for Rampart, Beaver, the Koyukuk River, the Kobuk River and the Kuskokwim River.
4. **Salt-water constant in a river.** The payload formula uses 35 cubic feet per long ton, which is sea water.
   In fresh water (36 cubic feet) the 120 by 40 foot barge carries 113,577 gallons, 4.1% less than the 118,445
   stated. This does not reach the result, because the base load of 100,000 gallons is a round assumption and
   not the computed payload.
5. **Sailings are not fuel trips.** The count of 31 adds the four rows of Table 3 and treats each sailing as a
   separate round trip from Nenana carrying fuel only. The memo says the vessels carry cargo and fuel together,
   and does not say whether a sailing to Kaltag is also one of the sailings to "Tanana to Galena". The whole day
   rate is charged to fuel; no share is given to deck cargo.
6. **Low-water arithmetic.** The multiplier of 4.2 for "three trips and ten days of waiting" divides by the
   Galena trip length (8.3 days), a Yukon River figure, although the three trips are at Shungnak on the Kobuk
   River. With Shungnak's own trip length it is 4.4. "Three trips" is a multiplier of 3 on cost per gallon only if
   one normal load would otherwise fill the whole order, which no document says. The top of the range (6 times)
   also assumes that a failed attempt is paid for; no document says that either.
7. **The base case cannot be a floor.** The summary calls the per-mile estimate "a lower-bound-type vessel cost".
   Tested against bounds already in the addendum, the base case is too high to be a floor on the Yukon River. It
   gives 3.38 dollars per gallon at Mountain Village (793.4 channel miles) against a ceiling of 1.45 to 2.36 for
   all transport, storage and margin, and 2.23 at Fort Yukon against a ceiling of 2.15. It exceeds the whole
   fiscal year 2025 premium over the road-system price at five of seven villages between Tanana and Huslia
   (Galena 1.77 against 1.39; Koyukuk 1.89 against 1.36; Nulato 1.94 against 0.37; Kaltag 2.06 against 1.08;
   Huslia 2.58 against 1.57; not Tanana, 1.19 against 1.44, and not Ruby, 1.60 against 4.43). A cost of vessel
   time alone cannot exceed a price difference that also holds margin and storage, so at least one base
   assumption is too costly for the Yukon River.

**How far the result moves across reasonable values of each assumption** (one at a time, others at base;
totals at Tanana on 163.8 measured channel miles, base 1.19 dollars per gallon).

| Assumption | Range tried | Per-mile part (dollars per gallon per channel mile) | Fixed part (dollars per gallon) | Total at Tanana (dollars per gallon) |
|---|---|---|---|---|
| Gallons per trip | 60,000 to 150,000; ISER's 250,000 | 0.0058 to 0.0023; 0.0014 | 1.04 to 0.42; 0.25 | 1.99 to 0.80; 0.48 |
| Days in port | 1.5 to 7.0 days | 0.0035 (unchanged) | 0.31 to 1.46 | 0.88 to 2.03 |
| Running hours per day | 16 to 24 hours | 0.0043 to 0.0029 | 0.63 (unchanged) | 1.34 to 1.10 |
| Speed against the current | 3.5 to 6.0 miles per hour | 0.0041 to 0.0029 | 0.63 (unchanged) | 1.30 to 1.10 |
| Speed with the current | 8 to 11 miles per hour | 0.0036 to 0.0033 | 0.63 (unchanged) | 1.22 to 1.16 |
| Day rate (the quoted spread) | 18,517 to 23,147 dollars per day | 0.0031 to 0.0039 | 0.56 to 0.69 | 1.06 to 1.33 |
| Dollar year of the day rate | 2007 or 2009 instead of 2008 | plus 3.8% or plus 0.4% | the same | the same |
| Share of the tow's cost carried by deck cargo | not known | lower by that share | lower by that share | lower by that share |

The load per trip alone moves the result by a factor of 4.1 (60,000 against 250,000 gallons), and the days in
port move the fixed part by a factor of 4.7. The one quoted input, the day rate, moves it by 25%. All corners
together span 0.42 to 4.32 dollars per gallon at Tanana, a factor of 10.

**What the method is.** It is the same method as the addendum's independent method 3 (ISER's day cost times an
assumed voyage time), with a different source for the day rate and a smaller assumed load. The two use almost
the same time per mile (0.01667 against 0.01637 days per one-way mile). The whole difference between them is:

- day rate, 20,832 against 19,590 dollars per day (ISER's 12,857 dollars per day in 2010 dollars, times 1.5237),
  a ratio of 1.06;
- load, 100,000 gallons assumed against ISER's quoted 250,000 gallons per trip, a ratio of 2.5;
- days in port, 3.0 against 2.5.

With ISER's quoted load the blind build-up gives 0.25 dollars per gallon fixed plus 0.0014 dollars per gallon
per channel mile, which is method 3 again (0.20 and 0.0013). With its own assumed load it gives 0.63 and 0.0035.
The new documents do not say which load is right.

**What the new evidence is worth.**

- **As a cost estimate: nothing.** The fixed part and the per-mile part are both set by assumptions. The
  comparison of a near and a far village returns the assumed slope by construction, as the blind derivation says
  itself. It is not a point estimate, and after error 7 it is not a lower bound; its range (0.0015 to 0.0099
  dollars per gallon per channel mile; 0.19 to 2.70 dollars per gallon fixed) contains every existing method and
  so is not an upper bound that excludes anything.
- **As a consistency check on one input of method 3: usable, with a caveat.** A second document, by different
  authors and from contractor experience, puts a western Alaska barging day at 18,517 to 23,147 dollars in 2026
  dollars. ISER's day cost for a short-season set, 19,590 dollars, lies inside that span and 6% below its
  mid-point. The caveat is that the Phase 1 figure is for construction barging with no vessel described, so the
  agreement shows the same order of size and no more.
- **As facts for the record: usable.** The supply statement (item 4) supports an assumption. The draft limit and
  the combined cargo and fuel service bear on the load assumed in method 3. The low-water statements and the
  Beaver plan support, in direction only, the gaps the addendum already records for the Kobuk River and for
  upstream hauls.

**Independence.** The new documents are not used by any method in the addendum, and the day rate is a different
underlying figure from ISER's. The method built on it is not independent: it has the same form as method 3 and
stands on the same kind of assumed voyage.

**A check the verifier added, and what it does not show.** The nine villages Ruby Marine serves (Tanana, Ruby,
Galena, Koyukuk, Nulato, Kaltag, Huslia, Hughes, Rampart) bought 876,200 gallons of utility diesel in fiscal year
2025 (Measured, `shared/pce_prices_with_distances.csv`). Spread over 16 to 31 sailings that is 28,300 to 54,800
gallons of utility diesel per sailing. A fuel load of 100,000 gallons on every sailing would need all barged
fuel to be 1.8 to 3.5 times the utility diesel, and 250,000 gallons would need 4.6 to 8.9 times. No supplied
document gives total barged fuel, so this does not fix the load per sailing. It does show that the load is the
open quantity, and that a sailing carrying 250,000 gallons to one place is unlikely to be the typical case.

**A side observation on project data (not part of this segment's evidence).** The blind derivation reports that
the harness table `hub_community` holds two hubs labelled Noorvik, one of them at Kaltag. This was confirmed:
hub `h000757` ("Noorvik") is at x -228058, y 1603625, about 240 metres from the Kaltag hub and 299 kilometres
from Noorvik's facilities. The blind derivation used the Kobuk River hub, which is correct. The earlier distance
file's "Kotzebue to Noorvik, 1,007.4 channel miles" comes from the same mislabelled hub and should not be used.

### Derived versus assumed (new inputs only)

| Input | Value | Type | Reference | What changes if it is wrong |
|---|---|---|---|---|
| Barging day rate, western Alaska | 12,000 to 15,000 dollars per day | Quoted | Phase 1 report, PDF p. 166 [148] | The only price in the batch. Every figure of the build-up scales with it. |
| Dollar year of the day rate | 2008 | Assumed (blind analyst) | "Recently"; report dated January 2009 | 2007 dollars raise every figure 3.8%; 2009 dollars raise it 0.4%. |
| Day rate in 2026 dollars | 18,517 to 23,147 dollars per day; mid-point 20,832 | Computed | Times 1.5431 | Follows the two rows above. |
| What the day rate covers | River tug, fuel barge, crew and tug fuel | Assumed (blind analyst) | The document names no vessel and concerns construction work | If tug fuel is outside it, cost rises (the blind analyst puts this at 20% to 30%, itself assumed). If it is for a larger coastal construction tow, a river fuel tow costs less. |
| ISER day cost, for comparison | 12,857 dollars per day in 2010 dollars; 19,590 in 2026 dollars | Quoted, then Computed | ISER 2010, page 20, Table 3 (addendum, Q7) | It is inside the Phase 1 span; ratio of the Phase 1 mid-point to it is 1.06. |
| Village barge sizes | 120 to 200 feet long, 40 to 55 feet wide, draft under 6 feet | Quoted | Phase 1 report, PDF p. 26 [8] | Sets the span of possible loads. Statewide, not river-specific. |
| Draft limit on the Tanana River | 4.5 feet | Quoted | Marine memo, PDF p. 30 [24] | Limits the load of each barge leaving Nenana. |
| Fuel carried per barge at 4.5 feet | 113,577 to 118,445 gallons for 120 by 40 feet; up to about 260,000 to 271,000 gallons for 200 by 55 feet | Assumed (hull coefficients chosen by the blind analyst; fresh-water value by the verifier) | `river_buildup.py`; `check_river.py` | With an empty weight of 0.025 to 0.05 long tons per square foot the 120 by 40 foot barge carries 132,500 to 94,600 gallons. |
| Gallons per trip | 100,000 gallons | Assumed (blind analyst) | None | The largest single driver: 60,000 to 250,000 gallons moves every figure by a factor of 4.1. |
| Speeds and running hours | 4.5 and 9 miles per hour; 20 hours a day | Assumed (blind analyst) | None for a tow; the Kobuk River current (3 to 5 miles per hour) is Quoted, Phase 1 report, PDF p. 128 [110] | The per-mile part moves between 0.0029 and 0.0043 dollars per gallon per channel mile. |
| Days in port per delivery | 3.0 days | Assumed (blind analyst) | None; the 24-hour stops in the Phase 1 report are at coastal, tidal sites (PDF p. 79 [61]) | The fixed part moves between 0.31 and 1.46 dollars per gallon. |
| Channel miles | Winding factors 1.15 to 1.5 on straight segments | Assumed (blind analyst), where a Measured value exists | `verify2/river/dist_check.json` | Short by 0.4% to 29%; see error 1. |
| Ruby Marine sailings per year | Rampart 3; Tanana to Galena 16; Galena to Kaltag 10; Koyukuk River 2 | Quoted | Marine memo, PDF p. 22 [16], Table 3 | Used only as a check. Year not stated; the source is 2019 interviews. |
| Reading of a sailing | One round trip from Nenana, fuel only, rows added | Assumed (blind analyst) | Same page: the vessels "haul both commodities" | If rows overlap there are fewer trips; if cargo shares the tow, fuel bears less of the day rate. |
| Ice-free season, middle Yukon | Mid-May to mid-October, about 150 days | Quoted, then Computed | Phase 1 report, PDF p. 62 [44] | ISER uses 105 operating days; on that basis, and on measured miles, the same sailings need 2.7 tows where 150 days need 1.9. |
| Supply point of the middle Yukon and of the Koyukuk River as far as Hughes | Nenana | Quoted (for about 2013 to 2019) | Marine memo, PDF p. 30 [24] | Supports the addendum's Assumed supply point for today's prices; it says nothing about the contract years 2003 and 2006. |
| Low-water statements | "often requiring 3 trips" (Shungnak); "every other year" (Ambler, Shungnak); "50 percent chance" (Kiana); "every 5 years" (Kobuk village, contractor barges) | Quoted | Marine memo, PDF p. 41 [35] and p. 36 [30]; Phase 1 report, PDF p. 130 to 133 [112 to 115] | Direction only. |
| Low-water multiplier on cost | 3 times (1 to 6) | Assumed (blind analyst) | See error 6 | Not usable as a number. |
| Beaver fuel delivery | Flown in; barge delivery of fuel made difficult by a changed channel | Quoted | Beaver plan, PDF p. 20 [19] | Shows that a Yukon Flats village may take no barged fuel at all. |

### Convergence after the new evidence

**Which methods count as independent points.** The same four as in the addendum: (1) state contract delivery
charges fitted against channel miles; (2) the DEC 2007 invoice rate, usable as a total near 100 map miles;
(3) the ISER 2010 day-cost family; (4) fiscal year 2025 delivered utility prices. The new build-up is not a
fifth. It belongs inside method 3, as a variant with a different day rate and an assumed load, and method 3
already enters the tests once.

**Spread ratios against the standard** (three or more genuinely independent methods within about 3 times, inputs
checked in the documents).

| Quantity | Independent values (2026 dollars) | Spread ratio | Result | If the new figure were wrongly counted as a point |
|---|---|---|---|---|
| Per-mile part, dollars per gallon per channel mile | Contracts 0.0044; ISER family 0.0011; delivered prices 0.0014 | 3.9 | Fails, unchanged | New figure 0.0035 lies inside the existing span; ratio still 3.9 |
| Total at Tanana, 164 channel miles, dollars per gallon | Contracts 0.61; DEC 1.10; ISER family 0.63 | 1.8 | Passes, unchanged (3.2 to 3.5 with the fourth method) | New figure 1.19 on measured miles; ratio 2.0 (3.4 with the fourth method) |
| Fixed part per delivery, dollars per gallon | Contracts zero; ISER 0.20 or 0.82; delivered prices 0.08 to 1.03 | Not defined | Fails, unchanged | New figure 0.63 from an assumed 3.0 days in port; adds nothing |

**Effect of the day-rate check on method 3.** If the Phase 1 mid-point replaced ISER's day cost, the ISER family
would rise 6% (slope 0.0011 to 0.0012 dollars per gallon per channel mile; total at 164 miles 0.63 to 0.67
dollars per gallon). The evidence does not require that replacement, because the Phase 1 figure is for a
different kind of work, and it is not made. The spread ratios would not change at the precision reported.

**Result.** The convergence test stands exactly as the addendum left it: the total for a short haul agrees, and
the per-mile part and the fixed part do not. The new evidence adds no independent point to any of the three
tests.

### Status before and after

| Part | Status before | Status after | Point and range before | Point and range after |
|---|---|---|---|---|
| Total for a short haul | Provisional | Provisional | 0.71 dollars per gallon at 164 channel miles (low 0.35, high 1.13) | Unchanged |
| Per-mile part | Provisional | Provisional | 0.0013 dollars per gallon per channel mile; range 0.0009 to 0.0044 | Unchanged |
| Fixed part per delivery | Provisional | Provisional | 0.50 dollars per gallon; range 0.20 to 0.80 | Unchanged |
| Applied value in `friction_costs.py` | Barge 0.0010 dollars per gallon-mile | No change proposed | Range 0.00023 to 0.011 | No change proposed here |

**Why the status does not change.** "Derived" needs three or more genuinely independent methods within about 3
times. The new build-up is a variant of an existing method, it rests on four assumed quantities for one quoted
one, and it fails the addendum's own bounds at its base values. It therefore cannot be counted, and the count of
independent methods and their spread are as before. Nothing moves to "Assumed" either: the earlier evidence is
untouched.

**Why the point and the ranges do not change.** The new figure (0.63 dollars per gallon plus 0.0035 dollars per
gallon per channel mile) lies inside both existing ranges, so the ranges do not need widening, and a figure set
by assumptions is no reason to move a point.

**Proposed changes to the addendum's text (wording only; no number changes).**

1. Methods table: add a row "Phase 1 day rate times an assumed voyage (second batch)", marked "No. Same method as
   method 3", value 0.63 dollars per gallon plus 0.0035 dollars per gallon per channel mile on an assumed load of
   100,000 gallons (0.25 plus 0.0014 on ISER's 250,000 gallons), kept as a consistency check on the day cost only.
2. Derived-versus-assumed row "Short-season day cost": add that a second document gives 12,000 to 15,000 dollars
   per day for western Alaska construction barging (about 2008; 18,517 to 23,147 dollars in 2026 dollars) against
   ISER's 19,590 dollars.
3. Row "Supply point for Tanana, Ruby and Koyukuk": add the marine memo's statement that the middle Yukon and the
   Koyukuk River as far as Hughes are served from Nenana (PDF p. 30 [24]). The input stays Assumed for the
   contract years, because the statement dates from 2013 to 2019 and the Galena terminal objection is from 2007.
4. Rows "Whole load carried to the farthest point" and "Tug speed and running hours": add two cautions. The
   Tanana River limits barges to a draft of 4.5 feet, and the carrier's vessels haul cargo and fuel together on
   scheduled sailings to several villages. Both make a single 250,000-gallon fuel load to one place a best case,
   which supports reading method 3 as a floor.
5. "Not re-confirmed", first item (Ruby Marine, three trips a season to Emmonak): still not confirmed. Add that a
   supplied document now gives the company's middle-river schedule (3, 16, 10 and 2 sailings), which neither
   supports nor contradicts the Emmonak statement.
6. Open gaps for the Kobuk River and for upstream hauls: add the low-water statements and the Beaver statement
   as documented reasons, in direction only, why one statewide figure under-prices the Kobuk River and why
   Yukon Flats prices may reflect flown fuel.
7. Note that the distance pair "Kotzebue to Noorvik" in `dist_check.json` uses a mislabelled hub.

### Still missing

The list in the addendum stands. The new documents sharpen four items and close none.

- **Gallons per sailing and days per sailing for a river tow.** The schedule gives sailings per year only. What
  is needed is a carrier log, vessel-tracking record or delivery manifest giving days out and gallons delivered
  by village, and the number of tows the carrier runs. This is the quantity that separates 0.0014 from 0.0035
  dollars per gallon per channel mile.
- **A day rate or charter rate for a river fuel tow, with its scope.** A charter agreement or carrier quotation
  that names the tug, the barges, and whether crew and fuel are inside the rate. The Phase 1 figure is for
  construction barging and names none of these.
- **Fuel capacity of the barges that leave Nenana at 4.5 feet of draft**, in gallons, from a vessel
  specification or a spill-response plan, and the share of a sailing's cost that deck cargo carries.
- **A same-year charge schedule from one river hub covering short and long hauls** (carrier rate table or bid
  tabulation). This remains the single document that could make the figure Derived.
- **A contract, bid or invoice for a Kobuk River, Koyukuk River or upper Kuskokwim River village**, and a record
  of what a carrier charges when a low-water delivery needs extra trips or fails. The low-water statements give
  the direction and no price.
- **Unchanged from the addendum:** Appendix C of the DEC 2007 report; the 2003 and 2006 state contracts
  separately; the fiscal year 2025 supply point of each lower-Yukon utility; evidence for upstream hauls (the
  Beaver plan shows fuel flown in, and gives no charge); the dollar year of the ISER 2010 figures; the BLS
  download of the CPI-U series.

**Working files** (all under the working folder `costs/`): `batch2/derive/river/river_buildup.py` and
`river_buildup_output.txt` (the blind derivation); `batch2/verify/river/rerun_river_buildup.py` and
`rerun_river_buildup_output.txt` (the re-run, identical output); `batch2/verify/river/check_river.py` and
`check_river_output.txt` (the verifier's recomputation, sensitivities, bounds and convergence);
`batch2/verify/river/findq.py` and `findq2.py` (quote and page search); `batch2/extracts/` (fact sheets) and
`batch2/text/` (document text).
