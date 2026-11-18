## Addendum 2026-11-17: Transfer fees (fixed dollars per gallon at each change of mode) (proposal; nothing applied)

Segment: the fixed fee, in dollars per gallon, that the model charges each time fuel crosses from one mode to
another on a transfer edge. There are four fee keys in `friction_costs.py`: barge to overland (286
barge-to-road edges and 2 barge-to-air edges), barge to ice road (21 edges), overland to ice road (12 edges) and
plane to overland (2 edges). Nothing in this addendum has been applied to `friction_costs.py`. All 2026 figures
are in 2026 dollars at CPI-U 332.243 (`index_basis_2026-11-17.md`). The working files used 330.0; every inflated
figure below was recomputed from its source-year value, and the text says where a rounded value differs from the
working files. Port tariff figures are 2026 schedules and are not inflated.

**The verdict summarised here overturns the applied barge-to-overland fee of $0.24 per gallon. It comes from ONE
adversarial verifier and has not had a second independent review.**

In the tables, "PDF p." is the page of the PDF file and "printed p." is the number printed on the page. "Q1" to
"Q27" refer to the quoted passages listed under the tables; each was found on the stated page for this record
(`transfer_fees_checks/quote_confirmation_output.txt`). An "event" is one physical handling step, for example
discharging a barge into a hub tank farm. A "crossing" is one transfer edge on a route in the model. "Line-haul
barge" means the large ocean barge that carries fuel from the road system to a regional hub; "small barge" means
the shallow-draft barge that carries it on to villages.

Short names used below. **ISER 2010** and **ISER 2008** are the reports "Components of Alaska Fuel Costs"
(February 2010) and "Components of Delivered Fuel Prices in Alaska" (June 2008) by the Institute of Social and
Economic Research, University of Alaska Anchorage. **DEC** is the Alaska Department of Environmental
Conservation. **PCE** is the Power Cost Equalization program; its report for fiscal year 2025 (FY2025, July 2024
to June 2025) gives each utility's fuel price. FY26 is the State fiscal year from July 2025 to June 2026.
**CPI-U** is the consumer price index for all urban consumers. In quoted tariff text "bbl" is a barrel of 42
gallons and "N.O.S." is "not otherwise specified".

### Status

**Mixed: Provisional for the barge-to-overland fee in every part; Assumed for the other three fees. No part of
the fee table is Derived.** Each fee carries one status; the barge-to-overland fee is given part by part because
its parts rest on different evidence.

| Fee or part | Status | Why |
|---|---|---|
| Barge to overland, discharge of a line-haul barge at a remote hub, distributor's own terminal ($0.12) | **Provisional** | Two independent methods whose inputs were checked agree within a factor of 1.43: the 2026 port tariffs of Bethel and Nome, and the itemised terminal costs in ISER 2010. The standard asks for three. The two also share one component (the city dock fee), so only the shore-labour item is new information. |
| Barge to overland, loading at a road-system origin port ($0.01) | **Provisional** | One published 2026 tariff at one port (Anchorage), tested only against a zero inferred from sale terms. |
| Barge to overland, village landing ($0.046) | **Provisional**, at the weak end | One study figure (ISER 2010 Table 4, an average over all gallons in a hypothetical example). Placing it on the village crossing is a modelling judgement by the verifier. |
| Barge to overland, single value for every crossing ($0.04) | **Provisional** | Computed from the three parts above and an assumed share of gallons that pass through a hub terminal. |
| Truck rack at a remote hub ($0.28) | **Provisional**, single source; not for the base case | One list price at one terminal in one year (the Bethel terminal rate sheet, 2022). It is the price to a storage customer, not a cost. |
| Barge to ice road ($0.011) | **Assumed**, unchanged | No source prices this event. The applied value is a carried-over engineering residual. The crossing cannot be used in any month. |
| Overland to ice road ($0.022) | **Assumed**, unchanged | No source prices this event. The applied value is an engineering build-up with assumed inputs. |
| Plane to overland ($0.025) | **Assumed**, unchanged | No source prices this event. The applied value is an engineering build-up with assumed inputs. |

**What the model should carry meanwhile.** The code keeps the applied values until the owner decides; this
record changes nothing. For the barge-to-overland fee the best estimate on the evidence is $0.04 per gallon per
crossing (range $0.01 to $0.10) if one value must serve every crossing, or $0.01, $0.12 and $0.046 by type of
place, all labelled provisional. Until a decision is made, a result that depends on the fixed fees of a barge
route should be reported for the range of $0.01 to $0.20 per gallon per route, with a note that the applied
values give $0.48. The three Assumed fees keep their applied values and ranges and are not changed on this
evidence. The verifier marked the segment "ready to apply, with caveats"; under the record's conventions that is
Provisional, not Derived.

### Result

| Item | Value |
|---|---|
| Form | Fixed fee per gallon per crossing. There is no per-mile part. The verifier prefers one value per type of place (origin port, remote line-haul hub, village landing) to one value for every barge-to-road edge. |
| Point, by type of place (preferred) | Origin port on the road system: $0.01. Remote line-haul hub (Bethel, Nome, Kotzebue, Dillingham, Naknek class): $0.12. Village landing: $0.046. |
| Range, by type of place | Origin port: $0.00 to $0.03. Hub, own terminal: $0.05 to $0.20. Village landing: $0.00 to $0.12, plus $0.15 to $0.30 where there is no marine header or dock. |
| Point, one value for every crossing | $0.04 per gallon per crossing |
| Range, one value | $0.01 to $0.10 per crossing; up to $0.15 where a third-party terminal or a missing header applies |
| Fixed part | The whole fee is fixed. A barge route has two crossings, so about $0.08 per gallon per route at the single value (range $0.01 to $0.20), and about $0.30 through a third-party hub terminal. The applied values bill $0.48 per route. |
| Unchanged fees | Barge to ice road $0.011 (range $0.00 to $0.02). Overland to ice road $0.022 (range $0.014 to $0.032). Plane to overland $0.025 (range $0.015 to $0.045). |
| Not for the base case | Third-party hub terminal $0.29 (range $0.20 to $0.38). Truck rack at a remote third-party hub $0.28 (range $0.05 to $0.32; $0.00 to $0.07 on the road system). Missing-header surcharge plus $0.19 (range $0.15 to $0.30). Reload at a hub onto a small barge $0.045 (range $0.017 to $0.12; the network has no edge for it). Dockage about $0.001 (range $0.0003 to $0.015; not billed). |
| Unit | United States dollars per gallon of fuel, once per crossing |
| Dollar basis | 2026 dollars, CPI-U 332.243. Tariff figures are 2026 actuals. |
| Source-year figures | Origin: 20.49 cents plus 14 cents per barrel, which is $0.0082 per gallon (2026 tariff). Hub: Bethel $0.12 and Nome $0.05 (2026 tariffs); ISER labour plus dock fee $0.08 (2010 dollars, year assumed). Village landing: $0.03 (2010 dollars, year assumed). Truck rack: $0.25 (August 2022). Third-party terminal fee: $0.15 (August 2022) and $0.07 to $0.15 (2010 dollars). Missing header: $0.10 to $0.15, "easily" $0.20 (2010 dollars). The single value and the hub point combine sources of different years and have no single source year. The three unchanged fees are stated by the earlier chapter in 2026 dollars and are not restated. |

Restatement note. Moving from 330.0 to 332.243 does not change the rounded origin point ($0.01, a tariff
figure), the hub point ($0.12), the single value ($0.04; unrounded $0.034 to $0.041), the per-route figure
(about $0.08) or any stated range end. It changes one rounded point: the village landing goes from $0.045
($0.0454) to $0.046 ($0.0457). It also moves the last digit of several working figures: the ISER own-terminal
figure from $0.121 to $0.122, the Bethel marine header from $0.169 to $0.170, the truck rack from $0.282 to
$0.284, the third-party discharge from $0.289 to $0.290, and the hub-discharge spread ratio from 1.42 to 1.43.

Marine-freight-index sensitivity. Using the coastal and Great Lakes freight index in place of CPI-U moves only
the parts that come from ISER 2010 (factor 1.749 from 2010, which is 1.148 times the CPI-U factor; the working
file gives 1.146). The hub figure goes from $0.12 to about $0.13, the village landing from $0.046 to $0.052, and
the single value from $0.04 to about $0.045. The truck rack would be $0.318 by that index. The verifier calls a
national freight index applied to a terminal service a weak sensitivity. It is never the base case.

### Methods and convergence

| Method | Counted as independent? | Value (2026 dollars per gallon) | Source documents with page | How it was checked | Kept or rejected and why |
|---|---|---|---|---|---|
| Published port tariffs: discharge of a line-haul barge at a remote hub, distributor's own tank farm (second round, "fees-tariff-build") | Yes (hub point 1) | Bethel $0.12 ($0.06 if only wharfage applies); Nome $0.05; mean $0.085. Not inflated. | `2026 UPDATED Tariff 005 with Pics.pdf`, PDF pp. 39 and 58 (Q1 to Q3). `PON Tariff No 16.6 - 03.12.26 Final.pdf`, PDF pp. 2, 18 and 25 (Q6 to Q8) | Verifier re-read the pages and redid the sums. For this record the quotes were found on the stated pages. | Kept as a point estimate. Municipal charges only: it leaves out the terminal owner's shore labour. Two hubs only. |
| ISER 2010 itemised terminal costs (first round "handling-iser-terminal" and second round "fees-studies-build"; one method, same study) | Yes (hub point 2), in part. Its dock-fee item is the same city charge the tariffs publish; only the labour item is new. | Own terminal $0.122 (range $0.061 to $0.152). Third-party customer $0.290 (range $0.198 to $0.381). | `components of alaska fuel costs.pdf`, p. 18 (Q14, Q15), p. 22 (Q16), p. 17 (Q17), p. 12 (Q18) | Verifier confirmed the quotes and factor. For this record the quotes were found and the figures recomputed at 332.243. | Kept as a point estimate. The figures are recollections; the dollar year is assumed. |
| Port of Alaska tariff: loading a barge at a road-system origin | Yes, but it is the only point method for this event | $0.0082 by pipeline ($0.0082 to $0.0097); $0.0223 from a tank truck or rail car ($0.0223 to $0.0255). Statewide origin $0.01 ($0.00 to $0.03). Not inflated. | `POA_Terminal_Tariff_10.2_Effective_January_1_2026.pdf`, PDF pp. 22, 48 and 51 (Q10 to Q12); `POA_Terminal_Tariff_10.0_AO_2023-34-S.pdf`, PDF p. 51 | Verifier recomputed. For this record the table cells were found and the division by 42 redone. | Kept as a point estimate. One port. ISER 2010 says fuel is sold free on board at the dock, so the wharfage may already be in the product price; $0.008 is then an upper reading. |
| Port tariffs: reload at a hub onto a small barge | One source type (tariffs); not a second method | Nome $0.032 from shore tanks, $0.017 over-side; Bethel $0.06, or $0.09 to $0.12 vessel to vessel. Point $0.045 (range $0.017 to $0.12; the mean of $0.032 and $0.06 is $0.046). Not inflated. | Nome tariff PDF pp. 21 and 25 (Q6, Q9); Bethel tariff PDF pp. 39, 58 and 62 (Q2, Q4) | Quotes found for this record, including the Bethel tariff's two conflicting over-side rules. | Kept as a point estimate with nowhere to bill it: the network has no edge at an intermediate hub. |
| Bethel terminal rate sheet: marine header and truck rack (second round; also the first-round web search) | No. Bound only. | Header $0.170; truck rack $0.284; third-party discharge $0.12 plus header, $0.290. | `Bethel-Terminal-Storage-Rate-Sheet.pdf`, PDF pp. 1, 2 and 4 (Q13) | Quotes and date found for this record; inflation redone. | Point estimate only for a third-party customer at a Bethel-type hub; an upper bound for everything else. It is a list price under a 12-month storage contract, not a cost. |
| Port tariffs: dockage per vessel call | No. Bound only. | $0.0003 to $0.004 line-haul; $0.001 to $0.015 small barge; typical about $0.001. | Bethel tariff PDF pp. 48 and 50; Nome tariff PDF p. 23; Port of Alaska 10.2 PDF p. 34 | Tariff cells found for this record. Vessel lengths, stays and parcels are the analyst's assumptions. | Rejected as a fee. Dockage is a vessel cost and belongs inside the barge rates. |
| US Army Corps of Engineers Nome study: "exports" fee | No | $0.0156 by CPI-U (1.2 cents, 2019). The current tariff gives $0.017 over-side and $0.032 outbound. | `DraftPortofNomeModificationIFREA31Dec2019.pdf`, PDF p. 196, printed p. 168 (Q25) | Quote found for this record. | Not usable. It is the Nome fee schedule at an earlier date, so it is not independent. Use the tariff values. |
| ISER 2010: village landing and the missing-header surcharge | No. Single source; bound only. | With a header: no separate fee. Without: plus $0.19 (range $0.15 to $0.30). | ISER 2010, p. 18 (Q20), pp. 22 to 23 and p. 7 (Q21); `Components of Delivered Fuel Prices in Alaska.pdf`, PDF p. 60 (Q27) | Quotes found for this record. | Sensitivity only. ISER states it as a difference in the distributor's transport charge, and no list of villages without a header exists. |
| ISER 2010 sale terms and ISER 2008 Table 10 truck contracts: no separable origin or truck-rack fee on the road system | No. Bound only. | Rack loading plus the whole truck haul: at most $0.017 to $0.068 (Delta Junction, Chitina, Nenana) | ISER 2010, pp. 14 to 15 (Q19) and p. 17 (Q22); ISER 2008, PDF p. 33, printed p. 27 (Q24) | Quotes and table cells found for this record. | Kept as an upper bound. A zero is an inference from price terms, not a measured fee. |
| ISER 2008 Table 10 barge contracts: the whole delivery charge at ice-free ports | No. Bound only. | Ketchikan $0.22, Kodiak $0.27, Klawock $0.34, Dutch Harbor $0.53 (2005 factor). With the 2003 and 2006 factors: $0.21 to $0.24, $0.26 to $0.29, $0.33 to $0.36, $0.51 to $0.56. | ISER 2008, PDF p. 33 (Q24) | Table cells found; recomputed with all three factors for this record. | Kept as a bound that two crossings must not exceed. |
| State marine-diesel contract: Dockside fee less Terminal fee, same vendor and place (added by the verifier) | Independent source. Bound only. | Cordova and Whittier $0.113; Homer $0.123; Seward $0.098; Juneau $0.033; Ketchikan $0.00; Sitka $0.00. Median $0.066. FY26 fees, not inflated. | `08-marine-diesel-fuels.pdf`, PDF p. 2 (Q26) | Table rows found and differences recomputed for this record. | Upper bound on truck loading plus local delivery at ice-free ports. The document does not define the two words; the reading is the verifier's inference. |
| First-round web search of tariffs (22 searches) | No | Other Alaska port wharfage $0.02 to $0.05; Dillingham $0.036 to $0.043 (unit not labelled) | Search snippets only; no supplied document | Not re-confirmed for this record. Its two main items were replaced by the documents above. | Corroboration only. Its Port of Alaska figure ($0.0096) is superseded by the tariff text ($0.0082). |
| Applied value: earlier chapter 06, "rate residual" (Bethel truck rack, inflated and shaded to $0.24) | No. Bound only. | $0.284 before shading ($0.282 at the 330.0 basis; the code comment says $0.276) | `06_connection_costs.md`, section 6.1; Bethel rate sheet PDF p. 1 (Q13); `friction_costs.py` lines 143 to 153 | Rate sheet quote found; code and edge counts read for this record. | Usable only as the upper bound for a third-party truck-rack event at a remote hub. See "Compared with the applied value". |
| Earlier chapter 05.1 operations build-up for hub discharge | Not verified | $0.086 as the chapter states it; not restated | `05_transfer_fees.md`, section 05.1; no supplied document gives its inputs | The verifier could not verify its inputs. Not re-confirmed for this record. | Shown in the spread only for openness. Its wharfage part comes from the same tariffs. |
| Earlier chapter 06 build-ups for the three minor fees | Not re-opened | $0.011, $0.022, $0.025 as the chapter states them | `06_connection_costs.md`, sections 6.2 to 6.4 | The verifier confirmed only the Port of Alaska Item 260 figures behind $0.011. No new source prices these events. | Carried over unchanged as Assumed. |

Spread, by event.

- **Hub discharge, distributor's own terminal** (the only event with two independent point methods): $0.085
  from the tariffs and $0.122 from ISER 2010. The ratio of highest to lowest is 1.43 (1.42 at the 330.0 basis)
  and the geometric mean is $0.102. Adding the earlier chapter's unverified build-up ($0.086) leaves the ratio
  at 1.43. If Bethel's transfer charge does not apply, the tariff mean is $0.055 and the ratio is 2.22 (2.20 at
  the 330.0 basis).
- **Third-party customer at a hub:** tariff plus the Bethel header $0.290 against ISER's three items $0.290,
  ratio 1.00 (1.01 at the 330.0 basis). The header fee alone: $0.170 against $0.168, ratio 1.02. These two are
  not fully independent: the ISER section was written by people who had worked for the same operators (Q18).
- **City inbound fuel charge:** Bethel $0.06, Nome $0.05, ISER dock-fee midpoint $0.046; ratio 1.31 (1.32 at
  the 330.0 basis). The older figures ($0.04 in 2007; 3.5 cents in 2019) are the same fee schedules at earlier
  dates and count as corroboration, not as methods.
- **Hub reload:** Nome $0.032 against Bethel $0.06, ratio 1.9, but one source type.
- **No ratio can be computed** for the truck rack (one source), origin loading (one tariff against an inferred
  zero), the village landing (one source), or the air and ice-road fees (no source).

What this means against the 3x standard. Every ratio that can be computed is well inside 3x, so the evidence
does not disagree. The weakness is that it is thin: the best-supported event has two independent methods where
the standard asks for three, and the other events have one or none. No part of the fee table is Derived.

Bounds. The recommended values respect all three bounds in the table (road-system truck contracts, the
marine-diesel fee difference, and the whole barge delivery charge at ice-free ports). The applied $0.24 does
not: two crossings ($0.48) exceed the whole delivery charge at Ketchikan, Kodiak and Klawock at any of the three
candidate dollar years, and are 86% to 94% of Dutch Harbor's.

### Derived versus assumed

| # | Input | Value | Type | Reference | What changes if it is wrong |
|---|---|---|---|---|---|
| | **Origin port ($0.01)** | | | | |
| 1 | Port of Alaska petroleum wharfage, vessel tanks to or from storage tanks | 20.49 cents per barrel (2026 column) | Quoted | Port of Alaska tariff 10.2, PDF p. 48, Item 260 (Q10) | The origin figure moves in proportion; it is under one cent either way. |
| 2 | Port of Alaska modernization surcharge on petroleum | $0.14 per barrel (2026); $0.02 in tariff 10.0 | Quoted | Tariff 10.2, PDF p. 51, Item 272 (Q11); tariff 10.0, PDF p. 51 | With the old surcharge the origin figure is $0.0054. |
| 3 | Gallons per barrel | 42 | Quoted | Tariff 10.2, PDF p. 22 (Q12) | None. |
| 4 | Origin charge by pipeline | $0.0082 per gallon | Computed | Rows 1 to 3: (20.49 cents plus 14 cents) divided by 42 | See rows 5 to 9. |
| 5 | Loading from a tank truck or rail car | 1.90 cents per gallon; $0.0223 with the surcharge | Quoted and Computed | Tariff 10.2, PDF p. 48 (Q10) | It sets the upper part of the origin range. |
| 6 | The valve-yard transfer line (6.08 cents per barrel) is not added to the wharfage | Not added | Assumed (blind analyst; the tariff is silent) | Tariff 10.2, PDF p. 48 (Q10) | If cumulative, $0.0097 in place of $0.0082. |
| 7 | The security fee ($0.89 per ton) is left out | Left out | Assumed (verifier) | Tariff 10.2, PDF p. 50. Whether it applies to petroleum is not stated; the density used to convert it (7.05 pounds per gallon) is not from a source. | If it applies, about $0.003 more. |
| 8 | Anchorage stands for every road-system and ice-free origin; private docks (Nikiski, Valdez) charge nothing | One port | Assumed (verifier) | No tariff for any other origin is among the supplied files. | An unpublished operator loading charge could be much larger than the port charge. |
| 9 | Fuel is sold free on board at the refinery or the Port of Anchorage dock | Loading is in the product price | Quoted for the sale terms (Q19). That this makes $0.008 an upper reading is Assumed (verifier). | ISER 2010, pp. 14 to 15 | If the wharfage is inside the product price, the separate origin fee is zero. |
| 10 | Origin point and range | $0.01; $0.00 to $0.03 | Assumed: judgement (verifier), rounding $0.0082 up within rows 4 to 9 | `derive2_results.json`, `verdicts.fees` | At most $0.02 per route either way. |
| | **Remote hub ($0.12)** | | | | |
| 11 | Bethel inbound petroleum wharfage | $0.06 per gallon, flat 2026 to 2030 | Quoted | Bethel tariff, PDF p. 58, section 206 D (Q1) | Tariff method point 1 moves cent for cent. |
| 12 | Bethel fuel transfer charge | $0.06 per gallon | Quoted | Bethel tariff, PDF p. 39, section 200 E (Q2) | See row 14. |
| 13 | Bethel wharfage is added to other charges | Additive | Quoted | Bethel tariff, PDF p. 58, section 206 A (Q3) | None beyond row 14. |
| 14 | Both Bethel charges are billed on a line-haul discharge through a header that is not the city's Petroleum Dock pipeline | Both apply ($0.12) | Assumed (blind analyst; flagged by the verifier). The tariff does not say. | Bethel tariff, PDF p. 39 | If only wharfage applies: Bethel $0.06, tariff mean $0.055, spread 2.22. |
| 15 | Nome inbound bulk-liquid wharfage | $0.05 per gallon, after the 3.76% increase of 12 March 2026 | Quoted | Nome tariff 16.6, PDF p. 25 (Q6) and PDF p. 2 (Q7) | Tariff method point 1 moves by half as much. |
| 16 | Nome prints no transfer or header rate; the carrier does the transfer | No further city charge | Quoted | Nome tariff, PDF p. 18 (Q8) | A private tank-farm charge at Nome is unpublished and would add to $0.05. |
| 17 | Tariff mean of the two hubs | $0.085 | Computed. Equal weight for two hubs is Assumed (blind analyst). | Rows 11 to 15 | Weighted toward Nome it falls toward $0.05; toward Bethel it rises toward $0.12. |
| 18 | Shore-side labour for a line-haul offload | $0.04 to $0.06 per gallon | Quoted | ISER 2010, p. 18, item 1 (Q14) | It is the only item not also in the tariffs. Without it the hub figure is the city charge alone ($0.05 to $0.12). |
| 19 | City dock fee paid by the terminal owner | $0.02 to $0.04 per gallon | Quoted | ISER 2010, p. 18, item 2 (Q14) | It overlaps rows 11 and 15, which are the same kind of charge. |
| 20 | Midpoints used | Labour $0.05; dock fee $0.03 | Assumed (blind analysts) | Rows 18 and 19 | Ends of the ISER figure: $0.061 (labour only, low) to $0.152. |
| 21 | Dollar year of the ISER 2010 figures | 2010 | Assumed (blind analysts; kept by the verifier) | ISER 2010 calls them "best estimates and memories of historical costs" (Q18); the report is dated 17 February 2010. | Read as 2007 dollars the own-terminal figure is $0.128; as 2005 dollars $0.136. The spread rises to 1.51 or 1.60. |
| 22 | Factors to 2026 | 2010: 1.5237; 2022: 1.1353; 2007: 1.6024; 2019: 1.2996 | Computed | `index_basis_2026-11-17.md` | None beyond row 23. |
| 23 | Carrying terminal labour and city fees to 2026 by general consumer prices | CPI-U, all items | Owner decision for the index (2026-11-17). That it fits these charges is Assumed. | `index_basis_2026-11-17.md`. Check: $0.04 in 2007 inflates to $0.064, against today's $0.06 at Bethel and $0.05 at Nome; 3.5 cents in 2019 inflates to $0.045, against today's $0.05 at Nome. | The check is 7% high at Bethel, 28% high and 9% low at Nome (the verdict says "within about 10%"). An error of that size moves the hub figure by about one cent. |
| 24 | ISER own-terminal figure | $0.122 | Computed | Rows 18 to 22: $0.08 times 1.5237 | It is hub point 2. |
| 25 | These terminal costs are not inside the line-haul rate | Outside | Quoted | ISER 2010, p. 17 "transportation only" (Q17); p. 18 "in addition to" (Q14); Table 4 lists terminal use on its own line (Q16) | If the line-haul rate carried them, the hub fee would bill them twice. |
| 26 | Hub point and range | $0.12; $0.05 to $0.20 | Assumed: judgement (verifier). Low is Nome wharfage alone; high is Bethel $0.12 plus labour $0.076. | Rows 11 to 24. Current port charge plus ISER labour gives Nome $0.126 and Bethel $0.136 to $0.196. | The geometric mean of the two methods is $0.102; the tariff mean alone is $0.085. |
| 27 | The distributor at the hub owns its terminal, so no third-party fee is due | Own terminal | Assumed (verifier) | ISER 2010, p. 18, item 3 (Q14) gives the fee where it applies. The earlier chapter says most hub tank farms are carrier-owned; not re-confirmed. | A third-party customer pays $0.29 (range $0.20 to $0.38). |
| 28 | Which landings count as remote line-haul hubs | Bethel, Nome, Kotzebue, Dillingham, Naknek "class" | Assumed (verifier) | The model holds no such label. Published charges exist for Bethel and Nome only. | The fee by type of place cannot be applied until each landing is typed. |
| | **Village landing ($0.046)** | | | | |
| 29 | Average terminal use over all delivered gallons | $0.03 per gallon | Quoted | ISER 2010, p. 22, Table 4 (Q16) | The village figure moves in proportion. ISER calls the table an example for "a hypothetical community". |
| 30 | Not all gallons pass through a terminal | "avoid terminal use whenever possible" | Quoted | ISER 2010, p. 18 (Q15) | It is why row 29 is an average and not a fee per event. |
| 31 | Discharge through the customer's header is inside the small-barge rate | No separate fee where a header exists | The risk statement is Quoted (Q20). That it puts the discharge inside the small-barge cost is Assumed (blind analysts; verifier). | ISER 2010, p. 18 | If the small-barge rate stopped at the vessel's rail, a discharge fee would be due at every village. |
| 32 | The Table 4 average is placed on the village crossing | $0.046 on each village landing | Assumed (verifier), because the network has no edge for hub transshipment | `verdicts.fees`, "double_count_and_scope" | It belongs either here or in a fixed part of the coastal rate, never both. For a gallon that goes straight from line-haul vessel to small barge to a village header the true fee is zero. |
| 33 | Village point and range | $0.046; $0.00 to $0.12 | Point Computed (row 29 times 1.5237). Range Assumed (verifier); the verdict does not say how the top was built. | Rows 29 to 32 | The single value in row 41 moves by about three quarters of any change. |
| 34 | Missing-header surcharge | $0.10 to $0.15 per gallon; "easily" $0.20 | Quoted | ISER 2010, pp. 22 to 23 and p. 7 (Q21) | Left out of the base case. Where it applies the village fee is about $0.24, not $0.046. |
| 35 | Villages without a header are treated as the exception | Sensitivity only | Assumed (verifier) | In ISER 2008's sample all seven barge-served communities have moorage or a header (Q27). No list of villages without one exists. | If many villages lack a header, the village fee is too low by $0.15 to $0.30 there. |
| | **One value for every crossing ($0.04)** | | | | |
| 36 | Transfer edges priced by this key | 286 barge-to-road and 2 barge-to-air | Measured | `fuel_network.duckdb`, table `network_edges` (`transfer_fees_checks/net_rerun_output.txt`) | None. The code comment's counts (289 and 2) are stale. |
| 37 | A transfer edge costs exactly the fee, with no mileage | Fee only | Measured (read from the code) | `source_scripts/fuel_network/graph.py`, lines 101 to 104 | None. |
| 38 | Crossings per barge route | Two (origin and destination) | Measured | 93 of 95 barge-served rows in `shared/pce_prices_with_distances.csv` (110 of all 112 routed rows); the other two cross once. 16 of 17 sampled paths; Kodiak crosses four (`paths_rerun_output.txt`). | Routes with one or four crossings are billed half or twice the per-route figure. |
| 39 | Share of gallons that pass through a hub's own terminal | 17% to 25% | 17% is Measured: Nome plus Kotzebue are 17.2% of the gallons in the barge-served rows of the FY2025 price table (utility fuel only; Bethel, Dillingham and Naknek are not in that table). 25% is Assumed (verifier). | `shared/pce_prices_with_distances.csv`; `transfer_fees_checks/pce_hub_share_output.txt` | With no hub gallons the value is $0.027 per crossing; with all hub gallons $0.085. |
| 40 | Hub route and village route sums | Hub: origin plus hub. Village: origin plus the Table 4 average. | Computed | Rows 10, 26, 33 | See row 41. |
| 41 | Single value and range | $0.04 per crossing; $0.01 to $0.10 | Computed from rows 38 to 40 ($0.034 to $0.041 unrounded). The rounding and the range are Assumed (verifier). | `transfer_fees_checks/restate_transfer_fees_332243_output.txt` | A table keyed by type of place removes the dependence on row 39. |
| | **Truck rack and third-party terminal (not in the base case)** | | | | |
| 42 | Bethel terminal throughput fees | Truck rack $0.2500; marine header $0.1500 per gallon; effective 10 August 2022 | Quoted | `Bethel-Terminal-Storage-Rate-Sheet.pdf`, PDF p. 1 (Q13) | These are the only published terminal-operator prices in the evidence. |
| 43 | The sheet's prices carried to 2026 by CPI-U | Factor 1.1353 | Assumed (blind analyst; verifier). The sheet prints no escalator. | Row 22 | A later sheet could differ either way. |
| 44 | The rack price is a list price to a storage customer, not the operator's cost, and not a charge on the operator's own gallons | Upper bound only | Assumed (verifier). The contract terms are Quoted: 12 months and 1,000 barrels minimum. | Rate sheet, PDF p. 2 (Q13) | If racks at most hubs charged this to all gallons, the truck-rack event would cost $0.28 where it occurs. |
| 45 | Third-party terminal fee | $0.07 to $0.15 per gallon, in addition to the dock fee | Quoted | ISER 2010, p. 18, item 3 (Q14) | It agrees with the Bethel header ($0.168 against $0.170). |
| | **Bounds** | | | | |
| 46 | State contract delivery charges, 2003 and 2006 | Truck: Delta Junction $0.01, Chitina $0.04, Nenana $0.04. Barge: Ketchikan $0.13, Kodiak $0.16, Klawock $0.20, Dutch Harbor $0.31. | Quoted | ISER 2008, PDF p. 33, printed p. 27, Table 10 (Q24) | They are bounds, not inputs to the points. |
| 47 | Dollar year for row 46 | 2005 (between the two contract years) | Assumed (verifier) | The table combines 2003 and 2006 contracts. | With the 2003 or 2006 factor the bounds move by 3% to 6%; the conclusion does not change. |
| 48 | Trucking from North Pole to Nenana | "less than $0.05 per gallon" | Quoted | ISER 2010, p. 17 (Q22) | It bounds any road-system rack fee from above ($0.076 with the whole haul). |
| 49 | Marine-diesel management fees, Dockside and Terminal | See the methods table | Quoted | `08-marine-diesel-fuels.pdf`, PDF p. 2 (Q26) | Bound only. |
| 50 | The fee difference in row 49 is truck loading plus a short delivery to the dock | Reading of two undefined words | Assumed (verifier) | The document does not define "Dockside" or "Terminal". | If the difference is something else, this bound falls away; the Table 10 bounds remain. |
| | **Unchanged fees** | | | | |
| 51 | Barge to ice road: facility-interface residual | $0.011; range $0.00 to $0.02 | Assumed (earlier chapter 06; carried over). The two tariff figures it sits between are Quoted: 6.08 cents per barrel (0.145 cents per gallon) and 1.90 cents per gallon. | `06_connection_costs.md`, section 6.2; Port of Alaska tariff 10.2, PDF p. 48 (Q10). Taking the midpoint and applying an Anchorage tariff to river and Arctic landings are assumptions. | Nothing in routing: see row 52. |
| 52 | The barge-to-ice-road crossing cannot be used in any month | No month with open water and an open ice road at any of the 21 edges | Measured | `fuel_network.duckdb`, tables `network_edges` and `edge_month_weights` (`transfer_fees_checks/minor_keys_network_check_output.txt`) | If a later network gave any edge a shared month, the fee would start to matter and would need a source. |
| 53 | Overland to ice road: road side of a pumped truck-to-truck transfer | $0.022; range $0.014 to $0.032 | Assumed (earlier chapter 06; carried over). Every input is assumed: a 3,000-gallon batch, one labour hour at $90, $30 of equipment, a 55% road-side share, a factor of 1.05. | `06_connection_costs.md`, section 6.3 | It is billed on 12 edges. A Barrow to Atqasuk delivery crosses two of them ($0.044). |
| 54 | Plane to overland: ground-side receiving at the ramp | $0.025; range $0.015 to $0.045 | Assumed (earlier chapter 06; carried over). Every input is assumed: a 3,000-gallon parcel, 0.83 hours at $60, $37 of equipment, then shaded from $0.029. | `06_connection_costs.md`, section 6.4 | It is billed on 2 edges. It is small beside any air leg. |
| 55 | Which side of each crossing a fee may bill: the barge, plane and ice-road rates carry their own handling; the road rate is carriage only | Fee bills only handling with no home in a rate | Assumed (project convention) | Skill rule 5; `friction_costs.py` fee comment (re-derivation dated 2026-07-28); `06_connection_costs.md`, section 6.6. The ice-road addendum lists this as an owner decision. | If the barge rate is split into ocean, coastal and river rates, the rule changes for hub handling: see the overlap rules below. |
| 56 | Index basis | CPI-U 2026 = 332.243 | Owner decision (2026-11-17) | `index_basis_2026-11-17.md` | 0.68% on inflated figures only. |

Quoted passages (exact words; each was found on the stated page for this record):

- **Q1.** Bethel tariff, PDF p. 58, section 206 D, schedule of rates with columns 2026 to 2030: "Inbound
  Petroleum Products $0.06 per Gal $0.06 $0.06 $0.06 $0.06" (the commodity name wraps over two lines in the
  table). PDF p. 1: "Amended by Ordinance 26-08 Effective April 28, 2026".
- **Q2.** Bethel tariff, PDF p. 39, section 200 E: "There will be assessed a six cent charge ($0.06) PER GALLON
  of fuel transferred from vessel to tanker, tanker to vessel, vessel to vessel, vessel to pipeline and/or
  pipeline to vessel. This will be in addition to dockage charges."
- **Q3.** Bethel tariff, PDF p. 58, section 206 A: "Wharfage rates named in this tariff will be charged for all
  freight/cargo [...] and will be in addition to all other charges made under this provisions of this tariff";
  "Fuel handled over wharf will not be considered as ship's stores and will be subject to wharfage and other
  charges that may be incurred."
- **Q4.** Bethel tariff, PDF p. 58, section 206 B: "Full wharfage named herein will be charged to merchandise
  discharged or loaded overside of vessel directly to or from another vessel or to the water when vessel is
  berthed at wharf." PDF p. 62, item 4: "Over-side cargo being discharged or loaded between vessels when one
  vessel is berthed at a Port of Bethel Facility shall be charged exactly one-half (1/2) the typical wharfage
  rate for that cargo." The two rules conflict as printed.
- **Q5.** Bethel tariff, PDF p. 11: "All rates in this Tariff, except wharfage, will have city sales taxes
  applied." The tax rate is not in the document.
- **Q6.** Nome tariff 16.6, PDF p. 25, section 05.020(a)(1): "Bulk liquid products - Inbound only [...] $0.05
  per gal Outbound only [...] $0.032 per gal Over-side only [...] $0.017 per gal** Inter-facility transfer [...]
  $0.05 per gal"; "(**See Section 03.050 and 03.080 for restrictions)".
- **Q7.** Nome tariff, PDF p. 2: "effective March 12, 2026, an increase of 3.76% increase has been assigned to
  rates in Port of Nome Tariff No. 16.6."
- **Q8.** Nome tariff, PDF p. 18: "Petroleum transfers must be performed by the Marine Carrier delivering
  product to the facility."
- **Q9.** Nome tariff, PDF p. 21, section 03.080: "Over-side transfer of Petroleum Products is allowed only for
  the purpose of moving cargo between barge carriers for inbound delivery to shore or outbound delivery to
  coastal communities."
- **Q10.** Port of Alaska tariff 10.2, PDF p. 48, Item 260, heading "Wharfage Rate in Cents", 2026 column:
  "INBOUND/OUTBOUND Liquids, Petroleum or Petroleum Products, N.O.S., in bulk, discharged or loaded direct from
  or to vessels' tanks to or from storage tanks, per bbl." 20.49; "TRANSFER [...] transferred via pipeline
  through the Port of Alaska Valve Year, per bbl." 6.08; "FUEL [...] discharged or loaded between mobile motor
  freight tank vehicles or railroad tank cars and vessel's tanks, per gallon." 1.90.
- **Q11.** Port of Alaska tariff 10.2, PDF p. 51, Item 272: "PETROLEUM VESSELS Not withstanding any other
  schedule of charges, the Port of Alaska shall assess a modernization surcharge fee per barrel [...] for all
  commodities crossing the Port of Alaska facilities." Columns 2024 to 2029: "$.02 $.11 $.14 $.14 $.14 $.14".
  Tariff 10.0, PDF p. 51, prints "$.02" for every year from 2024.
- **Q12.** Port of Alaska tariff 10.2, PDF p. 22: "42 gallons per barrel of bulk petroleum products corrected to
  60 degrees Fahrenheit".
- **Q13.** Bethel terminal rate sheet, PDF p. 1: "Effective Date: 10 August 2022 Crowley Fuels LLC Schedule of
  Terminal Storage and Throughput Rates"; "Table 2 Terminal Throughput Fees Truck Rack $0.2500 / gallon Marine
  Header $0.1500 / gallon Internal Tank Transfers and Blending $0.2500 / gallon". PDF p. 2: "Minimum Storage
  Term shall be 12 Months. Minimum Storage Quantity shall be 1,000 Barrels." PDF p. 4: "Company will be deemed
  to have custody of the Fuel delivered by a vessel from the time it enters the permanent shoreside pipeline
  header at Company's dock until it passes through the loading arm at the truck loading rack".
- **Q14.** ISER 2010, p. 18: "The costs described here are in addition to those normal local operating costs: 1.
  [...] A linehaul offload can take as long as 24 hours and requires multiple people/shifts to work the
  shore-side end of the delivery. These incremental costs are in the range of $0.04-$0.06 per gallon. 2. In
  several cases in Western Alaska, a distribution company owning the terminal must pay the city, which owns the
  dock, a per gallon fee. This fee is usually in the range of $0.02-$0.04 per gallon. 3. [...] This terminal
  fee, which is in addition to the fee described in number two above, typically ranges from $0.07 - $0.15 per
  gallon."
- **Q15.** ISER 2010, p. 18: "Not all fuel being delivered to Western Alaska goes through a terminal. The fuel
  off-loaded from the linehaul to the small barges often goes directly to the customer. In general, the delivery
  strategy is to avoid terminal use whenever possible."
- **Q16.** ISER 2010, p. 22, "Table 4. Distribution Cost Structure Example (per gallon)": "Purchase differential
  $ 0.06 Linehaul $ 0.19 Terminal use $ 0.03 Small barge operations $ 0.60 Working capital $ 0.03 Administration
  $ 0.07 Total Distribution Cost $ 0.98". The text above it says the table is for "a hypothetical community".
- **Q17.** ISER 2010, p. 17: "This results in approximately $0.19 per gallon in cost for transportation only."
- **Q18.** ISER 2010, p. 12: "The numbers used in this report reflect the best estimates and memories of
  historical costs but should not be considered exact without confirming data with current fuel distribution
  companies." Footnote 5: "The majority of this Western Alaska section was researched and written by Justin
  Charon and Mark Smith who worked for Crowley Marine Services and Yukon Fuel."
- **Q19.** ISER 2010, p. 14: "The product is sold "free on board"". Footnote 9, p. 15: "Indicating "FOB port"
  means that the seller pays for transportation of the goods to the port of shipment, plus loading costs."
- **Q20.** ISER 2010, p. 18: "All risk of a fuel spill is borne by the fuel distribution company until the fuel
  passes through the customer's header pipe upon delivery."
- **Q21.** ISER 2010, pp. 22 to 23: "Missing header or pipelines and docking issues are not uncommon. This could
  represent a $0.10-0.15 per gallon difference in the price the fuel distribution company charges a community."
  P. 7: "These costs can easily increase by $0.20 per gallon for docking and fuel off-loading deficiencies that
  increase the time, safety, and environmental risks of fuel handling."
- **Q22.** ISER 2010, p. 17: "In the case of the Yukon River, fuel is trucked to the Nenana terminal from a
  North Pole refinery. This is a straightforward process with costs of less than $0.05 per gallon."
- **Q23.** ISER 2008, PDF p. 67 (printed p. 61): "The Port of Bethel levies a $0.04 wharfage fee per gallon on
  all fuel that enters its port." PDF p. 71 (printed p. 65): "The City of Nome charges $0.04 per gallon for fuel
  that passes through the Port of Nome."
- **Q24.** ISER 2008, PDF p. 33 (printed p. 27), "Table 10. State of Alaska fuel contract delivery charges per
  gallon": "Anchorage $ (0.01) Truck Delta Junction $ 0.01 Truck Chitina $ 0.04 Truck Nenana $ 0.04 Truck [...]
  Ketchikan $ 0.13 Ice Free Barge Kodiak $ 0.16 Ice Free Barge Homer $ 0.18 Ice Free Barge Klawock $ 0.20 Ice
  Free Barge Dutch Harbor/Unalaska $ 0.31 Ice Free Barge". The text above says the table "shows the delivery
  cost component of 2003 and 2006 State of Alaska fuel contracts".
- **Q25.** US Army Corps of Engineers Nome study, PDF p. 196 (printed p. 168): "The City charges a 3.5¢ per
  gallon inbound fee on imports and 1.2¢ on exports of fuel, which would increase the transportation cost of
  regional fuel deliveries by adding another handling location to the process."
- **Q26.** State marine-diesel contract 2022-0200-4927, PDF p. 2, FY26 management fee: Cordova Dockside $1.1040
  and Terminal $0.9913 (Whittier the same); Homer $0.9058 and $0.7832; Juneau $0.2190 and $0.1858; Ketchikan
  $0.6073 and $0.6073; Seward $0.4281 and $0.3300; Sitka $1.0664 and $1.0664.
- **Q27.** ISER 2008, PDF p. 60 (printed p. 54), Table 15, row "Moorage/header": "n/a y y n/a y y n/a y y y".
  Read from the text file; the page image was not viewed for this record.

Public links. `DOWNLOAD_LIST.md` gives links for the ISER 2008 report
(https://scholarworks.alaska.edu/cgi/viewcontent.cgi?article=1348&context=uaa_iser_reports), the Port of Bethel
page (https://www.cityofbethel.org/200/Port-of-Bethel), the Port of Alaska tariff page
(https://www.portofalaska.com/business/finances/) and the Corps of Engineers Nome study
(https://www.poa.usace.army.mil/Portals/34/docs/civilworks/publicreview/portofnome/DraftPortofNomeModificationIFREA31Dec2019.pdf).
None of these links was opened in the session. The list gives no link for the Bethel terminal rate sheet or the
Nome tariff. The local copies are under `cost_derivation_resources/` (ISER 2010 and the marine-diesel contract on
the main branch; the others on branch `cost-sources`).

Which assumptions carry the most weight. Five decide the result. First, what each crossing stands for (rows 28
and 32): the evidence prices events, the model has crossings, and the mapping from one to the other is the
verifier's judgement; no landing in the model is yet typed as origin, hub or village. Second, that both Bethel
charges apply to a line-haul discharge (row 14): it is the difference between $0.06 and $0.12 at the larger of
the two hubs with a published tariff. Third, the share of gallons that pass through a hub terminal (row 39),
which sets the single value and rests on a measured 17% for two hubs and an assumed 25%. Fourth, the dollar
year of the ISER 2010 recollections and the use of consumer prices to carry them to 2026 (rows 21 and 23); this
matters less, because today's tariffs confirm the city-fee part directly. Fifth, that hub distributors own
their terminals (row 27); where they do not, the fee is more than twice as large. For the three unchanged fees
every input is an assumption (rows 51, 53 and 54), which is why they are labelled Assumed and left alone.

### What the figure includes and excludes

Fee table by event (2026 dollars per gallon). "Bill?" says whether the event should be charged as a fee.

| Event | Point | Range | Already carried by a rate? | Bill? |
|---|---|---|---|---|
| 1. Load a barge at a road-system origin | 0.01 | 0.00 to 0.03 | Vessel time alongside is in the line-haul rate. Shore loading is in the free-on-board product price (Q19). | Port wharfage and surcharge only |
| 2. Discharge a line-haul barge at a remote hub, own terminal | 0.12 | 0.05 to 0.20 | Vessel pumping and waiting are in the line-haul rate. Shore labour and city charges are not (Q14, Q16, Q17). | Yes |
| 2a. The same, as a customer of a third-party terminal | 0.29 | 0.20 to 0.38 | As above | Sensitivity only |
| 3a. Reload at a hub onto a small barge | 0.045 | 0.017 to 0.12 | The small barge's loading time is in its own cost. The city outbound or transfer charge is not. | Yes in principle, but the network has no edge at an intermediate hub |
| 3b. Line-haul vessel to small barge at sea | 0.00 | None published | The time of both vessels is in their rates. | No |
| 4. Truck rack at a hub | 0.28 third-party list price; about 0 on the road system | 0.05 to 0.32 remote; 0.00 to 0.07 road system | Not in the road rate, which is carriage only. On the road system it is inside the rack price. | Only for a gallon that leaves a tank farm by tank truck for a road or ice-road haul; never at a village landing |
| 5. Dockage | 0.001 | 0.0003 to 0.015 | A vessel cost, in the barge rates | No |
| 6. Village landing with a header | 0.00 | 0.00 to 0.05 | Inside the small-barge rate, which runs to the customer's header pipe (Q20) | No separate fee |
| 6a. Village landing with no header or dock | Plus 0.19 | 0.15 to 0.30 | A time-based addition to the small-barge rate | Sensitivity only |
| 7. Plane to ground | 0.025 applied | 0.015 to 0.045 | The aircraft side is in the air rate. | Not verified; keep |
| 8. Road to ice road | 0.022 applied | 0.014 to 0.032 | The ice-road side is in that rate's loading allowance. | Not verified; keep |
| 9. Barge to ice road | 0.011 applied | 0.00 to 0.02 | Both sides carry their own handling. | Completeness only; never used |

How the pieces add in the network. A barge route has two fee edges, one at the origin and one at the
destination. Hub transshipment (events 2 and 3a) has no edge. Its average over all gallons, ISER's $0.03 in
2010 dollars or $0.046 today, therefore has to sit either on the village-landing crossing or in a fixed part of
the coastal rate, and not in both.

Inside the proposed barge-to-overland fee:

- At an origin port: the port's wharfage and surcharge.
- At a remote hub: the city's inbound charges (wharfage and, at Bethel, the fuel transfer charge) and the
  terminal owner's shore-side labour to receive a line-haul offload.
- At a village landing: the all-gallon average of terminal use, standing in for hub transshipment.

Not inside it, and not to be billed as a fee:

- Vessel time while loading, pumping or waiting, and dockage. These are in the barge rates.
- Discharge by the small barge through the village's marine header. It is in the small-barge rate.
- The third-party terminal fee, the truck rack and the missing-header surcharge. Each is a sensitivity for the
  places where it applies.
- Tank-farm storage, capital and operations ($0.33 per gallon at Bethel in ISER 2010's 2003 case, p. 53; $2.25
  per barrel per month on the Bethel sheet, which is $0.061 per gallon per month in 2026 dollars).
- Working capital and administration.
- Retail truck delivery to customers ($0.25 to $0.35 per gallon at Bethel in 2007; ISER 2008, PDF p. 67).
- The fuel-segregation costs in the 2007 DEC study, which are specific to the change of fuel grade.
- City sales tax on the Bethel transfer charge (Q5); the rate is not in the tariff.

Three overlap rules (the verifier's; they need agreeing with the barge addenda before anything is applied):

- If a barge rate keeps a fixed part fitted from delivered prices (the intercept of price against distance),
  that fixed part already contains all fixed handling, and the matching crossing fee must be zero. The coastal
  small-barge addendum proposes a fixed part of $0.45 per gallon per village delivery and the river addendum
  one of $0.50 per gallon per river delivery, both Provisional. Both addenda say that discharge at a village
  with a header carries no separate fee, and both fixed parts rest in part on delivered prices or contract
  charges. Under this rule the village-landing fee is therefore zero wherever one of those fixed parts is
  applied, and $0.046 is the proposal only for a barge rate with no fixed part. The verifiers did not settle
  this between them (the coastal verdict describes its fixed part as vessel-side cost only, which would leave
  room for the $0.046), so it stays an open item; the difference is at most $0.046 per gallon. The fee and a
  fixed part must not be added together without saying so. The hub discharge fee ($0.12) is not affected: none
  of the proposed ocean, coastal or river rates or fixed parts contains it, and it is billed once per hub
  landing.
- If the blended barge rate of $0.0010 per gallon-mile is kept, it recovers more than line-haul costs ($1.28
  per gallon from Anchorage to Bethel on the earlier chapter's 1,276 charted statute miles, or $1.38 on the
  model's 1,375.9 water miles used in the ocean addendum, against a line-haul charge of $0.29 to $0.34; the
  working file gives $0.29 to $0.33 at the 330.0 basis). It then
  notionally carries lightering and terminal use, and only the origin charge ($0.01) and a hub's city charge
  ($0.05 to $0.12) may be added.
- If the barge segment is split into ocean, coastal and river rates, the hub fee ($0.12) and the terminal
  average ($0.046) must be billed, because no per-mile rate holds them. This rule speaks of per-mile rates
  only; where a split rate also keeps a fixed part, the first rule decides the $0.046.

River rate. The verifier did not check what handling the river carriers' invoices behind the 2007 DEC rate
bundle. It assumed that delivery to the village header is inside that rate, as for the coastal small barge. The
river addendum does not use the DEC rate as its per-mile rate: it proposes $0.0013 per gallon per channel mile
for carriage only and puts loading at the river hub and discharge through the village header inside its
provisional fixed part ($0.50 per gallon per river delivery). The assumption here and that addendum agree that
no separate fee is due at a village with a header.

The three unchanged fees. The plane-to-overland fee bills only the ground side of the transfer and the
overland-to-ice-road fee only the road side; the aircraft's and the ice-road vehicle's own handling stay in
their rates (plane and ice-road addenda). The barge-to-ice-road fee sits on 21 edges, 14 of them on the lower
Kuskokwim, 2 on the Yukon and Tanana and 5 on the North Slope. At none of them is there a month with both open
water and an open ice road, so routing by month never uses it. The ice-road addendum notes that the edges near
Bethel skip the terminal's truck rack; that would matter only if fuel storage between seasons were modelled.

### Compared with the applied value and the earlier chapter

What is applied today (`source_scripts/friction_surface/friction_costs.py`, `INTERMODAL_TRANSFER_FEES`):

| Key | Applied | Range in the code | Described as | This record |
|---|---|---|---|---|
| Barge to overland | $0.24 | $0.15 to $0.30, "confidence high" | Road-side truck-rack loading | **Overturned** by the verdict (one verifier). Proposed $0.04 per crossing ($0.01 to $0.10), or $0.01, $0.12 and $0.046 by type of place. |
| Barge to ice road | $0.011 | $0.00 to $0.02 | Thin facility-interface residual | Unchanged; Assumed |
| Plane to overland | $0.025 | $0.015 to $0.045 | Ground-side receiving labour and fittings | Unchanged; Assumed |
| Overland to ice road | $0.022 | $0.014 to $0.032 | Road side of a pumped changeover | Unchanged; Assumed |

Barge to overland: overturned. This comes from ONE verifier and has not had a second independent review.

- The proposed single value ($0.04; $0.01 to $0.10) lies wholly below the applied range. Even the hub value
  ($0.12) is below its low end.
- The source figure is confirmed. The Bethel sheet lists the truck rack at $0.25 per gallon in August 2022,
  which is $0.284 in 2026 dollars ($0.282 at the 330.0 basis). The code comment's $0.276 implies an index near
  323.
- What fails is the step in chapter 06 that made it the fee for every barge-to-road crossing. Four reasons:
  - Wrong event. It is one third-party list price for loading a tank truck from a contracted storage tank at
    Bethel. The model charges it at the origin port and at the destination landing, where no such event occurs.
  - Charged twice. Of the 95 barge-served rows in the shared distance table, 93 cross exactly two such edges,
    so the model bills $0.48 per gallon in fixed fees on a barge route.
  - The evidence per route is far lower: about $0.008 at the origin, $0.05 to $0.20 at a hub, and about $0.00
    to $0.05 at a village with a header, which is $0.01 to $0.20 per route.
  - A bound is broken. $0.48 exceeds the whole delivery charge in the State contracts at Ketchikan ($0.22),
    Kodiak ($0.27) and Klawock ($0.34), and is nearly all of Dutch Harbor's ($0.53).
- The "confidence high" label is not warranted: one source, one terminal, one year. The audit of the earlier
  work also noted that chapter 06's own two methods for this fee were $0.025 and $0.28, a ratio of about 11,
  which fails the 3x test.
- Effect if adopted: fixed fees on a barge route fall from $0.48 to about $0.06 at a village and $0.13 at a hub.

Earlier chapter 05 (`05_transfer_fees.md`):

- Hub discharge (section 05.1, $0.12, range $0.07 to $0.17): **confirmed**. Its inputs are found word for word
  in the tariffs and in ISER 2010, and this record gives $0.12 with a wider range ($0.05 to $0.20).
- Truck rack (section 05.2): its warning that the fee has two levels (about $0.05 on the road system against
  about $0.25 at a remote hub) is **confirmed and sharpened** by the State contract bounds.
- Direct barge-to-truck landing (section 05.3, reading b, about $0.10): close to the hub figure, and a better
  description of the crossing than chapter 06's rack fee.
- Its drum and storage keys are not in the fee table and are not treated here.

Earlier chapter 06 (`06_connection_costs.md`):

- Section 6.1 ($0.24): overturned as above.
- Section 6.2 ($0.011): its Port of Alaska inputs are confirmed (Q10). No change.
- Sections 6.3 and 6.4 ($0.022 and $0.025): neither confirmed nor moved. None of the new sources prices these
  events.

Corrections to the provenance text, for the next edit of that block (nothing was edited):

- The comment's "$0.276" should be $0.284 at the record's index.
- The comment's edge counts (291; 289 plus 2) are stale; the network of record has 286 plus 2.
- The comment places the 21 barge-to-ice-road edges "at North Slope hubs"; 16 of the 21 are on the Kuskokwim,
  Yukon and Tanana.
- Chapter 06 calls the overland-to-ice-road and plane-to-overland boundaries "latent"; they now price 12 and 2
  live edges.
- Chapter 06 cites Port of Alaska "Tariff 10.1" (chapter 05 says "10.1/10.2"); the tariff in force from 1
  January 2026 is 10.2. The two Bethel cites in chapter 05 (section 206 D and section 200 E) are two different
  charges of $0.06 each, not one charge cited twice.

### Open evidence gaps

- **A third independent method for hub discharge.** A terminal operator's cost statement, or a fuel delivery
  invoice that shows port charges and shore-side charges on separate lines.
- **Port tariffs for the other hubs.** City or borough tariff pages for Kotzebue, Dillingham (Item 290, with
  its unit), Naknek, Unalaska (Item 274), Kodiak, Nenana and the Southeast ports. Published per-gallon charges
  are in hand for Bethel and Nome only.
- **How Bethel bills a line-haul discharge.** A port invoice or a written statement from the Port of Bethel on
  whether the $0.06 transfer charge is billed with the $0.06 wharfage when the barge discharges through a
  private header; and the city sales tax rate on that charge (city code chapter 4.16).
- **Shore-side labour.** It rests on ISER 2010 alone. A terminal payroll or staffing record for a line-haul
  offload would test it.
- **Truck rack.** A second rate sheet from another remote-hub terminal, a later Bethel sheet, or an operator's
  own cost for rack loading. The contract solicitation that defines "Dockside" and "Terminal" in the State
  marine-diesel contract.
- **Origin loading.** A terminal loading charge or refinery supply contract at Nikiski, Valdez, North Pole or
  Nenana.
- **Share of gallons through hub terminals.** Carrier or State fuel-flow statistics by hub; the FY2025 price
  table covers utility fuel only and omits Bethel, Dillingham and Naknek.
- **Missing headers.** A list of villages without a marine header or dock (for example a bulk-fuel facility
  inventory), and a delivery contract that states the surcharge.
- **Plane to ground.** An airport fuel-handling charge, or an air-cargo contract price schedule that shows
  ground or standby time.
- **Road to ice road.** An operator's invoice for a truck-to-truck or tank transfer at a North Slope or
  Kuskokwim staging point, or a borough fuel-division cost line per gallon.
- **A decision for the owner.** Whether to key the barge-to-overland fee by type of place or keep one value.
  With one value the fee is charged twice on nearly every barge route.

Not re-confirmed for this record:

- The verdict says all 19 sampled shortest paths cross exactly two barge-to-road edges. Re-running the
  verifier's script gives 19 destinations, of which 2 have no path in the sampled part of the network, 16 cross
  two edges and 1 (Kodiak) crosses four. The count of 93 of 95 in the shared distance table was confirmed.
- The web-search snippets behind three statements: that the Kotzebue dock is privately owned with no city
  per-gallon wharfage, that Dillingham's Item 290 is $0.036 rising to $0.0432, and that Unalaska's Item 274
  could not be retrieved. No supplied document covers them.
- The inputs of the earlier chapters' engineering build-ups (wage rates, pump rates, crew sizes, the Port of
  Nome 16.5 rate of $0.048) and chapter 05's statement that most hub tank farms are carrier-owned. Tariff 16.6
  in hand gives $0.05 for Nome.
- The second-round analyst's statement that the 2007 DEC study found no rack fee.
- Table 15 of ISER 2008 (Q27) was read in the text file only; which seven communities the "y" entries belong to
  was not checked against the page image.

### Working files

All paths are under `harness: blind_derivations/working_2026-11-17/`.

- `derive2_results.json`: `verdicts.fees` (the verdict) and `derivations["fees-tariff-build"]`,
  `derivations["fees-studies-build"]` (second-round blind derivations).
- `blind_results.json`: `handling-iser-terminal` and `handling-tariff-search` (first-round derivations).
- `audit_results.json`: `port-tariffs-handling` (audit of the outside report against the fee chapters).
- `derive2/fees_tariffs/calc.py` and `derive2/fees_studies/calc.py`: the second-round arithmetic.
- `derive/handling_iser/paged.txt`: the first-round paged text of ISER 2010.
- `verify2/fees/verify.py`, `net.py`, `paths.py`, `paths.json`, `pg.py`: the verifier's scripts and path counts.
- `extracts/tariffs.md`, `extracts/iser_2008.md`, `extracts/usace_nome_2019.md`, `extracts/dec_2007.md`,
  `extracts/bering_strait_lightering.md`: fact sheets.
- `pdf_text/`: full text of the source documents.
- `shared/index_basis_2026-11-17.md`, `shared/inflation_factors.md`, `shared/pce_prices_with_distances.csv`.
- `record/transfer_fees_checks/`, written for this record:
  - `confirm_quotes.sh`, `find_quote_page.py`, `quote_confirmation_output.txt`: every quoted passage re-found,
    with its PDF page.
  - `restate_transfer_fees_332243.py` and its output: every inflated figure at the 330.0 and 332.243 bases.
  - `verify_py_output_330basis.txt`: the verifier's script re-run unchanged.
  - `net_rerun_output.txt`, `paths_rerun_output.txt`, `paths.json`: edge counts and path counts re-run.
  - `pce_transfer_count.py`, `pce_hub_share.py` and their outputs: crossings per route and the hub share of
    gallons.
  - `minor_keys_network_check.py` and its output: where the minor-fee edges are, and the month test for the
    barge-to-ice-road edges.
