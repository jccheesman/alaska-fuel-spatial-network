# Errata to the cost-derivation chapters and to the provenance comments in `friction_costs.py`

Checked 2026-11-18. This is a record of defects only. Nothing in either repository was edited, and the chapters
are not to be corrected silently: each item below is to be attached to the chapter as a dated erratum.

**What was checked.** Seven defects reported by the earlier review, each re-opened in the file itself. Other
defects met on the way are listed separately in the last section and marked "found while checking".

**Files, and the short names used below.**

| Short name | Full path |
|---|---|
| ch. 00 | `blind_derivations/00_executive_summary.md` |
| ch. 02 | `blind_derivations/02_barge.md` |
| ch. 04 | `blind_derivations/04_ice_road.md` |
| ch. 05 | `blind_derivations/05_transfer_fees.md` |
| ch. 06 | `blind_derivations/06_connection_costs.md` |
| costs file | `data repo: source_scripts/friction_surface/friction_costs.py` |
| toolkit | `data repo: .claude/skills/derive-fuel-costs/scripts/cost_derivation_tools.py` |
| tripwire | `data repo: source_scripts/fuel_network/load.py` |

The built copies of the chapters (`blind_derivations/combined.html`, `transfer_fees.html`, `transfer_fees.pdf`,
`Fuel Cost Blind Derivations.pdf`) carry the same text, so each erratum applies to them too.

**Other short names and units.** CPI-U is the consumer price index for all urban consumers. PCE is the Power
Cost Equalization program of the Alaska Energy Authority; its report for fiscal year 2025 (FY2025, July 2024 to
June 2025) gives each utility's fuel price and gallons. AVEC is the Alaska Village Electric Cooperative. ISER 2010
is the report "Components of Alaska Fuel Costs" by the Institute of Social and Economic Research, University of
Alaska Anchorage. NOAA is the National Oceanic and Atmospheric Administration. A rate written as a bare number
"per gallon-mile", such as 0.00023, is in United States dollars per gallon of fuel per statute mile; a fee
written as a bare number, such as 0.24, is in dollars per gallon.

**Index basis.** Project convention (owner decision 10, 2026-11-17): CPI-U, US city average, annual averages,
with 2026 = January to September 2026 average = 332.243. The toolkit still holds 2026 = 330.0. Where it helps,
both are shown. I recomputed the two averages from the downloaded series
(`shared/cpi/cpiai_datahub_mirror.csv`): eleven months of 2025 average 321.943, and January to September 2026
average 332.243.

**"Applied value"** means a number the model reads: the four rates and their ranges, and the four fee totals and
their ranges, in the costs file. Comments and chapter text are not applied values.

## Summary

| # | File | Defect | Verdict | Effect on an applied value | Changes a conclusion? |
|---|---|---|---|---|---|
| 1 | ch. 05, lines 39, 41, 43, 186 (and 57, 115) | Two inflation indexes are mixed. The chapter calls 327.075 the June 2026 CPI-U; the June 2026 CPI-U is 333.952, and 327.075 is the CPI-W value. | Confirmed. That 327.075 is not CPI-U is proved by the downloaded series; that it is CPI-W rests on a web snippet found by the earlier audit. | None. The largest shift in any chapter figure is $0.008 per gallon (truck rack $0.276 should be $0.284). The applied fee of $0.24 stays inside its range. | No. |
| 2 | ch. 06, lines 19 and 69; costs file, line 149 | The $0.24 barge-to-road fee is labelled "high confidence". Its two methods give $0.025 and $0.28, a ratio of 11.2. | Confirmed. | None on the number. The label is wrong. | Yes, for the label: it should read low confidence, single source. The number itself is a separate, open question. |
| 3 | ch. 02, lines 186 and 194 | "Three genuinely independent methods (A, B, C)" for the ocean line-haul rate. A and B are the same page of ISER 2010; C takes its largest input from ISER 2010. | Confirmed. C also has inputs that are not from ISER (tug fuel burn, fuel price), but they are 29% of its cost before mark-up. | None. 0.00023 is the low end of the applied Barge range and is unchanged. | Partly. The claim of three-method convergence and the "high" confidence fall. The level of about 0.00023 stands, because the November evidence from two other sources agrees with it. |
| 4 | ch. 02, lines 152, 186, 206, 241 | Aniak, McGrath and Sleetmute are treated as AVEC villages. The FY2025 PCE report lists them under Aniak Light & Power, McGrath Light & Power and Middle Kuskokwim Electric Cooperative. | Confirmed. The chapter's own table (lines 124, 129, 130) names the right utilities. | None on the applied point (0.0010). The upper end of the applied Barge range (0.011) loses the argument the chapter used to keep it. | Yes. The chapter's reason for setting the price evidence aside ("AVEC socializes distribution cost") does not apply to these villages. |
| 5a | costs file, lines 145-146 | The comment gives $0.276 as the 2022 truck-rack price of $0.25 in 2026 dollars. At the project index it is $0.284 ($0.282 at the toolkit's 330.0). | Confirmed. | None. $0.24 is still below the rack figure. | No. |
| 5b | costs file, lines 136-141 and 144 | Edge counts are stale: "289 + 2" and "291", on "the 2026-10-15 network-of-record". The current network (2026-11-16) has 286 + 2 = 288. | Confirmed. | None. No number is read from the comment. The tracked fee-table workbook also still prints 291. | No. |
| 6 | costs file, line 78 | The upper end of the applied IceRoad range (0.025) is below two readings in the November evidence (0.031 and 0.035), and below the chapter's own stated upper end (0.027). | Confirmed. | None on the point (0.010). The range's upper end should be about 0.030 when the entry is next edited. | No for the point. Yes for the documented range. |
| 7 | toolkit, lines 37-41 and 48 | The CPI table holds 2025 = 322.6 (preliminary) and 2026 = 330.0 (projected). The downloaded series gives 321.943 and 332.243. | Confirmed. | Every inflated figure rises 0.68% (0.89% for a 2025 source figure). No applied rate or fee leaves its range; the toolkit's self-test passes at both bases. | No. |

## 1. Chapter 05 mixes CPI-W and CPI-U

**Lines.**

- ch. 05, line 39: "Shared dollar-year nit: actual June-2026 CPI-U is 327.075 (not 330-334), so CPI-correct
  Crowley is $0.276 not $0.282 (immaterial)."
- ch. 05, line 41: "CPI-corrected (× 1.500) that is $0.105-0.225 and $0.045."
- ch. 05, line 43: "One verified exact-match Alaska tariff (Crowley $0.276 CPI-2026$) anchors everything".
- ch. 05, line 186: "Several derivations used a projected mid-2026 CPI-U of ~326-334; the actual June-2026 index
  is 327.075. The discrepancy moves any point estimate by <$0.006/gal and is below the rounding of every final
  value here."
- The same figure is behind "× 1.5" on line 57 and "× 1.50" on line 115.

**What is wrong.** The downloaded CPI-U series gives June 2026 = 333.952. No month of 2026 in that series
equals 327.075 (February is 326.785, March is 330.213). The earlier audit found the number in a Bureau of Labor
Statistics regional summary, where 333.952 is the June 2026 CPI-U and 327.075 is the June 2026 CPI-W, the index
for urban wage earners (web snippet, not held locally). The chapter then divides this CPI-W figure by CPI-U
figures for the source year:

- $0.276 = $0.25 × 327.075 / 296.171, where 296.171 is the CPI-U for August 2022 (the month of the Crowley rate
  sheet; confirmed in the downloaded series). The result is 0.2761.
- × 1.500 = 327.075 / 218.056, where 218.056 is the CPI-U annual average for 2010. The result is 1.49996.

So the "correction" on line 39 replaced a right figure with a wrong one. $0.282 is what the toolkit gives
($0.25 × 330.0 / 292.655 = 0.2819). Line 186 also has the direction wrong: the true June 2026 CPI-U (333.952)
is at the top of the "326-334" band, not near its bottom.

The chapter also inflates the same 2022 rate sheet with three factors (× 1.11 on line 13, × 1.114 on line 33,
× 1.104 behind line 39) and the same 2010 study with two (× 1.51 on lines 13 and 17; × 1.50 on lines 41, 57
and 115). The first group uses the August 2022 monthly value as the base; the project convention is annual
averages.

**Correct figures** (project convention: annual averages, 2026 = 332.243; factor from 2022 = 332.243 / 292.655
= 1.1353; factor from 2010 = 332.243 / 218.056 = 1.5237).

| Item | Chapter says | Correct at 332.243 | At the toolkit's 330.0 |
|---|---|---|---|
| Crowley truck rack, $0.25 in 2022 | $0.276 (lines 39, 43); $0.279 (line 33) | $0.284 | $0.282 |
| Crowley marine header, $0.15 in 2022 | $0.167 (line 13) | $0.170 | $0.169 |
| ISER third-party terminal fee, $0.07-0.15 in 2010 | $0.105-0.225 (lines 41, 115) | $0.107-0.229 | $0.106-0.227 |
| ISER terminal use, $0.03 in 2010 | $0.045 (line 41) | $0.046 | $0.045 |
| ISER shore labour, $0.04-0.06 in 2010 | $0.06-0.09 (line 57) | $0.061-0.091 | $0.061-0.091 |

If the August 2022 monthly value is kept as the base, the rack figure is $0.280 at 332.243. A CPI-W to CPI-W
restatement cannot be checked here, because no CPI-W series is held.

**Size of the effect.** The largest change is the truck rack: $0.284 against $0.276, a difference of $0.008
per gallon (2.8%). Of that, $0.004 comes from the wrong 2026 value and $0.003 from the monthly base. Line 186's
"<$0.006/gal" is therefore slightly too small, but every chapter figure still moves by less than one cent.

**Applied values and conclusions.** No applied value changes. The fee table in the costs file comes from
chapter 06, and its $0.24 stays inside its range of 0.15 to 0.30. The stated shading of $0.24 below the rack
price grows from 13% to 15%. No conclusion of the chapter changes.

## 2. "High confidence" on the $0.24 barge-to-road fee

**Lines.**

- ch. 06, line 11: "Method 1 — ops_direct ($0.025/gal, range $0.015-0.045)."
- ch. 06, line 13: "Method 2 — rate_residual ($0.28/gal, range $0.18-0.33)."
- ch. 06, line 15: "ops_direct's $0.025 is a floor ~10x below every posted anchor."
- ch. 06, line 19: "Final value: $0.24/gal, range $0.15-0.30, high confidence."
- ch. 06, line 69 (summary table): "`("barge","overland")` | 0.40 | **0.24** | 0.15-0.30 | high".
- costs file, line 149: "the 0.15 was a double-count. Range 0.15-0.30. Confidence high."

**What is wrong.** The two methods differ by 0.28 / 0.025 = 11.2 times. The skill's standard
(`derive-fuel-costs/SKILL.md`, rule 4) is three or more genuinely independent methods, and "a spread ratio
beyond ~3× across methods means the derivation is not ready". Here there are two methods, not three, and they
are 11 times apart. The stated range (0.15 to 0.30) lies wholly above the first method's range
(0.015 to 0.045), so the final range leaves one of the two methods out. If the first method is read as a floor only, as line 15 does, then one method is left, and
that method is one price on one terminal's rate sheet (Crowley, Bethel, 10 August 2022), moved from $0.28 to
$0.24 by judgement. Chapter 05 gave the same rack figure "medium confidence" (lines 45 and 66); chapter 06
raised it to "high" without new evidence.

**Correct statement.** Confidence is low: a single source, shaded by judgement, with no convergence test
passed. In the terms of the record's conventions it is Provisional at best.

**Applied values and conclusions.** The number $0.24 does not change because of this erratum. The label does,
in chapter 06 (lines 19 and 69) and in the costs file (line 149). The conclusion that changes is that the fee
cannot be treated as settled. The November fees verdict goes further and finds that $0.24 does not hold as a
statewide per-crossing figure; that is a proposal from one verifier with no second review, and it is recorded
in the addenda, not here.

## 3. "Three genuinely independent methods" for the ocean line-haul rate

**Lines.**

- ch. 02, line 85: "### Method B — Published/quoted rate history (all from ISER 2010 p. 17 ✓; DCCED
  reattributed)".
- ch. 02, line 94 (Method C): "Fixed cost: ISER $2.5M/season (2010$ ✓ p. 16) ×1.51 = $3.78M / 165-day season =
  $22.9k/day × 12.7 d = **$291k/trip**".
- ch. 02, line 186: "(i) three genuinely independent methods (A, B, C) converge on **$0.22–0.38/gal ⇒
  ~1.7–3.0×10⁻⁴ $/gal-mi**".
- ch. 02, line 194: "**Confidence: medium-high → high on the $/gal figure** (three-method convergence, now on
  verified primary numbers".

**What is wrong.**

- Method A's point is ISER 2010's market rate of $0.19 to $0.22 per gallon (lines 80-81). Method B's 2010 entry
  is the same $0.19 to $0.22 from the same page (line 86). In the ISER text the $0.19 arithmetic, the rate
  history and the "current $0.19-$0.22" sentence sit in three consecutive paragraphs. A and B are one source
  read twice.
- Method C is called independent, but its fixed cost is ISER's $2.5 million a season and its cargo volume is
  ISER's. That fixed cost is $291,000 of the $410,000 trip cost before mark-up, or 71% (64% at the higher fuel
  price). The rest is tug fuel from secondary sources, and a 40% mark-up that is an assumption.

So the three methods are one study (ISER 2010) plus the NOAA distance. Agreement among them shows the
arithmetic is consistent. It does not show that an independent source agrees.

**Correct statement.** In July the ocean line-haul figure rested on one source. Independent support arrived
only with the November documents (second-round ocean verdict; addendum to chapter 02): Econ One 2016 gives
0.000207 per gallon-mile and the oil-spill-response lightering guide gives about 0.00013 (weak: no year or
route stated), against ISER's 0.000205 on model miles. The spread across the three is about 1.6. There is still
no engineering build-up that is independent of ISER.

**Arithmetic check at the project index.** $0.19 × 1.5237 = $0.2895 per gallon; divided by 1,276 statute miles
this is 0.000227. The chapter's 0.00023 is unchanged at two figures.

**Applied values and conclusions.** 0.00023 is not applied to any edge. It is the lower end of the applied
Barge range (costs file, line 76) and the "ocean linehaul" figure in the comment (line 40). Neither moves. The
conclusion about the level stands. The claims of "three-method convergence" and "high" confidence do not: the
July evidence was a single source, and the right label for the figure as it stood then is medium at most.

## 4. Aniak, McGrath and Sleetmute are not AVEC villages

**Lines.**

- ch. 02, line 152: "the AVEC-served river villages (Upper Kalskag, Aniak, McGrath, plus AVEC's own
  Sleetmute-adjacent set) reveal an *incremental* river differential of only **≈ 1.0–1.5×10⁻³ $/gal-mi**",
  and "AVEC socializes river-distribution cost across its network, so an individual upriver AVEC village's
  *price* barely rises with distance even though its *freight cost* does."
- ch. 02, line 186 (iv): "the *realized* river-price gradient (~1×10⁻³ $/gal-mi across consolidated AVEC
  villages) runs ~10× below the invoice-based marginal freight rate because AVEC socializes distribution".
- ch. 02, line 206 and line 241 repeat it ("due to AVEC procurement consolidation"; "across consolidated AVEC
  river villages ... because AVEC socializes distribution cost across ~50 villages").
- The chapter's own table disagrees with its text: line 129 "**Aniak** | Aniak Light & Power", line 130
  "**McGrath** | McGrath Light & Power", line 124 "**Sleetmute** | Middle Kuskokwim Elec".

**What the FY2025 PCE report says** (`2026.03.01 FY2025 PCE Statistical Report by Community (Final)`; decoded
text and `work/pce/pce_fy2025_prices.csv`).

| Community | Utility on the community page | Report page | Fuel price | Gallons |
|---|---|---|---|---|
| Aniak | "Utility: ANIAK LIGHT & POWER" | 23 | $4.64 | 187,718 |
| McGrath | "Utility: MCGRATH LIGHT & POWER" | 105 | $4.96 | 151,194 |
| Sleetmute | "Utility: MIDDLE KUSKOKWIM ELECTRIC COOPERATIVE INC" | 154 | $4.49 | 31,312 |
| Upper Kalskag | Alaska Village Electric Cooperative | 177 | $4.57 | 96,294 |

The list of participating utilities (report page 11) shows the same thing: Aniak Light & Power Company,
McGrath Light & Power and Middle Kuskokwim Electric (Chuathbaluk, Crooked Creek, Red Devil, Sleetmute, Stony
River) are each listed as their own utility, separate from the Alaska Village Electric Cooperative list. Of the
four villages on line 152, only Upper Kalskag is an AVEC village.

**What follows.** The chapter used AVEC pooling to explain why prices rise so little with river distance, and
so to keep the invoice rate of 0.011 per gallon-mile on river edges despite the price evidence. That
explanation is not available for Aniak and McGrath, which buy their own fuel. On the chapter's own distances,
0.011 per gallon-mile predicts river freight of $1.02 to Aniak (93 miles) and $4.73 to McGrath (430 miles).
The whole price difference from Bethel is $0.19 and $0.51. The gap is five to nine times and is unexplained in
the chapter. It does not prove a lower rate, because the three utilities may buy at different times and from
different suppliers, but it can no longer be dismissed as a pooling effect.

**Applied values and conclusions.** The applied Barge point (0.0010) does not depend on this. The upper end of
the applied Barge range (0.011; costs file, line 76) and the "river distribution 0.011" figure in the comment
(line 42) lose the argument the chapter gave for holding them against the price evidence. The conclusion
"the physical river edge keeps the 1.1×10⁻² invoice rate" (line 186) is no longer supported by the reasoning
given. The November river verdict reaches the same point from other evidence (one verifier, no second review).

## 5. Provenance comment for the barge-to-road fee in `friction_costs.py`

### 5a. The $0.276 figure

**Lines.** Costs file, lines 144-146: "Bills the road-side truck-rack out-loading only (Crowley Bethel rack
$0.25 -> $0.276 CPI-2026, shaded to 0.24 for sole-provider margin)."

**Arithmetic.**

| Basis | Calculation | Result |
|---|---|---|
| Project index (2026 = 332.243, 2022 annual average 292.655) | 0.25 × 332.243 / 292.655 = 0.25 × 1.1353 | $0.284 |
| Toolkit as committed (2026 = 330.0) | 0.25 × 330.0 / 292.655 = 0.25 × 1.1276 | $0.282 |
| What reproduces the comment | 0.25 × 327.075 / 296.171 (June 2026 CPI-W over August 2022 CPI-U) | $0.276 |

**What is wrong.** $0.276 cannot be reproduced from the project's own table at either basis. On the annual
2022 base it implies a 2026 index of 323.1. It is the mixed-index figure of erratum 1, carried into the code
comment. The correct figure is $0.284 at the project index.

**Effect.** None on an applied value. The fee of $0.24 is still below the rack figure, by 15% instead of 13%.
The same $0.276 is repeated in two other places (see F9 below).

### 5b. Edge counts

**Lines.**

- Costs file, lines 136-141: "Live in the 2026-10-15 network-of-record (per-pair transfer types; counts are
  the EXPECTED tripwire in fuel_network/load.py): ("barge","overland") prices BargeRoadTransfer (289) +
  BargeAirTransfer (2)".
- Costs file, line 144: "291 transfer edges (BargeRoadTransfer + BargeAirTransfer)."

**What is current.** Tripwire, lines 95 and 99: `"BargeRoadTransfer": 286` and `"BargeAirTransfer": 2`, with
the note on lines 85-86 "dropping three BargeRoadTransfer handoffs (289 -> 286, edges 93,049 -> 93,046)".
The network of record is the 2026-11-16 export, not the 2026-10-15 one. The comment was last edited on
2026-10-23, before the two November exports.

**Correct statement.** 286 + 2 = 288 transfer edges on the 2026-11-16 network of record. The other counts in
the comment (21, 12 and 2) still match the tripwire.

**Effect.** None. The model takes the counts from the network, not from the comment. The figure-table script
(`figure_scripts/tables/build_combined_friction_tables.py`, lines 59-63) reads the tripwire, so it will print
288 when it is next run. The tracked workbook it last produced (`outputs/tables/combined_friction_tables.xlsx`,
built 2026-10-23) still prints "Prices 291 edges".

## 6. The applied IceRoad range stops below two November readings

**Lines.**

- Costs file, line 78: `"IceRoad": (0.004,   0.025),`
- Costs file, lines 70-71: "IceRoad bounds are the two verified regimes (engineered ice road ~0.004, tundra
  cat-train ~0.02) widened to the blind-derivation range."
- ch. 04, line 151: "**Range:** $0.004 (engineered ice road, full tanker loads, routine season) to $0.027
  (tundra snow-trail cat-train, difficult conditions)." Line 187 repeats "range $0.004–0.027".
- ch. 00, line 29 gives the range as "0.004–0.025".

**The two readings** (second-round ice-road verdict; restated in `record/ice_road_checks/`).

| Reading | Calculation | At 330.0 | At 332.243 |
|---|---|---|---|
| Atqasuk price premium over the straight-line distance | ($7.41 − $5.705) × factor from 2025, divided by 57.1 miles | 0.0306 | 0.0308 |
| Snow tractor and sled build-up at 8 miles an hour | corrected capital of $350,000, analyst's slow speed | 0.0349 | 0.0351 |

Both are upper readings, not central ones. The straight line is shorter than the 68.46-mile network path, and
8 miles an hour is below the source's 10 to 12. The central sled readings are 0.0255 to 0.0257 at 332.243
(0.0254 to 0.0255 at 330.0), which already sit just above 0.025.

**What is wrong.** The applied upper end (0.025) is below both readings. It is also below the upper end that
chapter 04 itself states (0.027), although the comment says the bounds were widened to the blind-derivation
range. Chapter 00 and the costs file say 0.025; chapter 04 says 0.027.

**Correct statement.** The verdict's range is 0.006 to 0.030. The upper end of the applied range should be
about 0.030 when the IceRoad entry is next edited.

**Effect.** None on the applied point: 0.010 is inside both the old and the new range, and the toolkit's range
check passes. No routing result changes. What changes is the documented uncertainty. The evidence behind the
new upper end is thin (two method families, one price case, one verifier), so this is a range correction and
not a reason to move the point.

## 7. The toolkit's CPI table

**Lines.** Toolkit, lines 37-41: "2025 is a preliminary annual average; 2026 is a projection (~2.5% over
2025)". Toolkit, line 48: `2025: 322.6,   2026: 330.0,`

**What the downloaded series gives.** (`shared/cpi/cpiai_datahub_mirror.csv`, recomputed here.)

| Year | Toolkit | Downloaded series | Difference |
|---|---|---|---|
| 2025 | 322.6 | 321.943, the average of the eleven published months (October 2025 was not published) | toolkit is 0.20% high |
| 2026 | 330.0 | 332.243, the average of January to September 2026 | toolkit is 0.68% low |

**Effect on factors.** Every factor from a year up to 2024 rises by 0.68% (332.243 / 330.0 = 1.0068). The
factor from 2025 rises by 0.89% (from 330.0 / 322.6 = 1.0229 to 332.243 / 321.943 = 1.0320).

**Effect on figures the toolkit reproduces** (run in memory with the table patched; nothing written).

| Figure | At 330.0 | At 332.243 | Documented or applied |
|---|---|---|---|
| Road, Econ One $0.20 (2015) over 364 miles | 0.000765 | 0.000770 | applied 0.0007, range 0.00045-0.0011 |
| Barge line-haul, $0.19 (2010) | $0.2875 | $0.2895 | documented $0.29 |
| River endpoint, $0.007 (2007) | 0.01114 | 0.01122 | documented 0.011; also the upper end of the Barge range |
| Truck rack, $0.25 (2022) | $0.2819 | $0.2838 | comment says $0.276 (erratum 5a) |
| Road-to-ice-road fee, $0.021 (2024) | 0.0221 | 0.0222 | applied 0.022, range 0.014-0.032 |

The self-test reports 16 passes and no failures at both bases. No applied rate or fee leaves its range. The
restated river endpoint (0.0112) is 2% above the 0.011 written as the upper end of the Barge range; the
self-test allows 5%.

**Correct statement.** The table should hold 2025 = 321.943 and 2026 = 332.243, the second marked as a
nine-month average to be replaced when the annual average is published. The series used is a public mirror of
the Bureau of Labor Statistics table, not the table itself, and should be replaced by it. The toolkit's own
rule is that the table is edited in one place only, with the next edit of the costs file.

**Conclusions.** None changes.

## Found while checking

These were not in the reported list. Each was seen in the files while checking the seven above.

| # | File and line | Defect (found while checking) | Effect on an applied value | Changes a conclusion? |
|---|---|---|---|---|
| F1 | ch. 02, lines 152, 186, 241 | The PCE table does not show AVEC pooling fuel cost. Its 46 AVEC communities with a fuel price report 44 different prices, from $2.78 (Minto) to $9.41 (Noatak). | None on the point. Same range question as erratum 4. | Yes. It removes the pooling explanation for Upper Kalskag as well. |
| F2 | ch. 02, lines 154 and 244; ch. 00, lines 19 and 27 | Sleetmute's $4.49 is not Sleetmute's own price. The five Middle Kuskokwim Electric villages report $4.48 or $4.49 each: one utility-wide average. | None. | Yes. "~310 river miles adds essentially zero realized freight" does not follow from this row. |
| F3 | ch. 02, line 137 | The fit across four ocean hubs is described as slope "≈ −7×10⁻⁴" with "R² near zero". On the chapter's own four points the slope is −6.0×10⁻⁴ and R² is 0.62. | None. | No. The slope is still negative, and four points prove little either way. |
| F4 | ch. 02, line 180 | Method C's per-mile figure (1.9–2.6×10⁻⁴) was computed over 1,224 miles but sits in a column headed "over 1,276 sm". Over 1,276 miles it is 1.8–2.5×10⁻⁴. | None. | No. |
| F5 | ch. 02, lines 104 and 202 | The river rate is said to rest on "two independent verified anchors ... that agree within 10%". They agree only at one chosen distance (82 miles × 0.011 = $0.90 against ISER's $0.91). ISER's figure has no distance. | Bears on the upper end of the Barge range (0.011). | Yes, for the "medium-high" confidence on the river rate. |
| F6 | ch. 00, line 35 | "Ocean barge (0.00026)". The results table eight lines above, and chapter 02, give 0.00023. The older figure was left in after the route distance was corrected. | None. | No. |
| F7 | ch. 05, line 143; ch. 00, lines 19, 29, 41 | Chapter 05 calls $350,000 "a $75k sub-line error" and chapter 00 writes "$425K tracked tractor". The Noatak proposal (page 5, Table 1) asks $350,000 for the tractor, sled and shipment and $75,000 for permitting: $425,000 in all. Chapter 04 (lines 42, 114, 172) has it right. | None. | No. |
| F8 | several chapters | One source year is inflated by different factors in different places. Details below. | None. The largest effect is about 3% on figures that are not applied. | No. |
| F9 | toolkit, line 253; `figure_scripts/tables/build_combined_friction_tables.py`, line 295 | The $0.276 of erratum 5a is repeated. The toolkit's self-test hard-codes `rack_2026 = 0.276` where its own function gives 0.2819 (0.2838 at the project index). The table script prints "$0.276", and so does the tracked workbook `outputs/tables/combined_friction_tables.xlsx`. | None. The check "fee is below the rack price" passes either way. | No. |
| F10 | ch. 06, line 113 | "plane 25×, ice road 14×, barge 1.4× the road rate". 0.025 / 0.0007 is 36 times, not 25. The other two are right. | None. | No. |
| F11 | ch. 06, lines 102, 107, 115 | The worked examples charge the barge-to-road fee once per barge route ($0.24). In the network a barge route crosses two transfer edges: in the shared distance table, 110 of the 112 routes from Anchorage that use barge cross exactly two. Example A1 is then $1.83, not $1.59, and the fee is 26% of it, not "~15%". | This is the applied fee charged twice per route, $0.48. | No ranking in the examples flips. The size of the fee's share is understated. |
| F12 | costs file, lines 170-171 against lines 139-140 | The comment on the plane-to-road fee calls it a "Latent modal boundary ... (a future plane<->overland connector)". The header comment says the same key prices two live AirRoadTransfer edges, and the tripwire agrees. | None. | No. |
| F13 | costs file, line 55 against line 157 | The rate comment says ice roads run "Jan-Apr"; the fee comment says "Jan-Mar". The pipeline notes say IceRoad rows exist only January to March. | None. | No. |
| F14 | ch. 05, line 99 | "Takotna $5.63 vs supply hub McGrath $4.96 → $0.68 gap". The difference is $0.67. | None. | No. |
| F15 | ch. 06, lines 9, 23, 37, 51 | Section headings carry the edge counts of the July network (205 and 8) and call two boundaries "latent". The current network has 288, 21, 12 and 2 edges on the four keys. | None. | No. The chapter is dated; this is noted so the counts are not read as current. |

**F1 and F2 in more detail.** These two matter most. If AVEC charged every village one pooled price, its
villages would report one price, as the five Middle Kuskokwim Electric villages do (Chuathbaluk $4.48; Crooked
Creek, Red Devil, Sleetmute and Stony River $4.49; together 123,520 gallons for $554,439, which is $4.489). The
AVEC villages do not: St. Mary's $4.06, Bethel $4.45, Hooper Bay $4.50, Emmonak $4.55, Upper Kalskag $4.57 and
Togiak $4.61 in the chapter's own table. So pooling is real for Sleetmute's utility and is not shown for AVEC.
The sentence the executive summary calls "the report's cleanest single fact" (ch. 00, line 19) compares
Bethel with a five-village average, not with a village 310 miles upriver.

**F8 in more detail.** Correct factors at the project index are × 1.5237 from 2010, × 1.4018 from 2015,
× 1.2261 from 2021 and × 1.1353 from 2022.

| Source year | Factors used | Where |
|---|---|---|
| 2010 | × 1.51 | ch. 02, lines 38 and 76; ch. 05, lines 13 and 17 |
| 2010 | × 1.50 or × 1.5 | ch. 05, lines 41, 57, 115 |
| 2010 | × 1.53 | ch. 06, lines 11 and 55 |
| 2010 | × 1.47 | ch. 06, line 41 |
| 2015 | × 1.409 | ch. 01, lines 24 and 35 |
| 2015 | × 1.36 | ch. 04, lines 47 and 69 |
| 2021 | × 1.20 | ch. 04, line 47 |
| 2022 | × 1.10 | ch. 06, line 13 ("$0.25 x CPI 1.10 = $0.28/gal"; the product is 0.275) |
| 2022 | × 1.11 and × 1.114 | ch. 04, line 47; ch. 05, lines 13 and 33 |

The chapters also state three different mid-2026 index levels: about 330 (ch. 02, ch. 03), 333.9 (ch. 01,
line 24) and 327.075 (ch. 05). The largest errors are × 1.47 (3.5% low, in a method the chapter did not
uphold) and × 1.36 (3.0% low; the Ontario ice-road figure of 0.0065 becomes 0.0067). The remedy is the
toolkit's rule: every restatement goes through the one table.

## Limits of this check

- Both repositories were read only. The data repository's working tree is clean after the check.
- I recomputed from local files: the two CPI averages; every inflation figure above; the toolkit self-test at
  both bases (in memory); the utility and price on the PCE pages for Aniak, McGrath, Sleetmute and the other
  Middle Kuskokwim villages; the count of distinct AVEC prices; the four-hub fit; the transfer count per route;
  the Noatak funding table (read from the page image); and the edge counts in the tripwire.
- I did not recompute the November readings quoted in errata 3 and 6. They are taken from the second-round
  verdicts and the restatement outputs in `record/`, which rest on one verifier per segment.
- That 327.075 is the CPI-W value rests on a web snippet recorded by the earlier audit. The local series
  proves only that it is not the CPI-U value for June 2026.
- The river distances in erratum 4 (93, 310 and 430 miles) are the chapter's own and were not re-measured.
