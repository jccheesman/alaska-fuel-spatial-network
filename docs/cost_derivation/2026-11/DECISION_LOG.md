# Cost re-derivation log, November 2026

**Status of everything in this log: proposal.** No rate or fee in `friction_costs.py` (data repo) was changed.
The addenda dated 2026-11-17 (`docs/cost_derivation/2026-11/`, summarised at the end of chapter 00) hold the figures; this chapter records how the work went and
what was decided, in order, so a later reader can see why each choice was made.

Owner: JC. Conventions (status tiers, input types): `docs/cost_derivation/2026-11/CONVENTIONS.md`.
Index basis: `docs/cost_derivation/2026-11/index_basis_2026-11-17.md`.

## 1. Why the costs were reopened

| Date | What happened |
|---|---|
| 2026-11-16 | While reviewing the saved reference answers, the owner noticed that fuel for Nome was routed by road to Nenana and then 1,421 km down the Tanana and Yukon by barge, and expected an ocean route. |
| 2026-11-16 | Cause found: the model prices every waterway edge, ocean or river, at one blended barge rate ($0.0010 per gallon-mile). At that rate the river route from Nenana is cheaper than the sea route from Anchorage. Any single barge rate below about $0.00052 sends Nome's fuel by sea. |
| 2026-11-16 | Owner's question: since ocean and river costs are already distinguished in the derivation notes, should they be separate rates and not averaged? Answer: yes; the barge chapter itself (section 7) recommended that and it was never applied. |

## 2. Decisions, in order

| # | Date | Decision | Who | Reason |
|---|---|---|---|---|
| 1 | 2026-11-16 | Run a what-if with separate ocean and river rates, locally only. "Do not commit anywhere, only show locally." | Owner | See the effect before changing anything. |
| 2 | 2026-11-16 | Commission an outside deep-research report (Gemini) on each barge cost component. | Owner | An independent look at sources. |
| 3 | 2026-11-17 | Audit that report against the local documents before using it. Outcome: several of its claims confirmed, several rebutted (section 4). | Owner asked; assistant ran | The outside tool had no access to the local PDFs. |
| 4 | 2026-11-17 | Use the outside tool for finding documents only, not for derivation or verification. The owner downloads the documents; derivations are run blind on the documents themselves. | Owner, on the assistant's recommendation | Its first report went wrong where it could not open a source. A reader of the same documents is not independent evidence. |
| 5 | 2026-11-17 | Inflation convention stays CPI-U. Water-freight producer price indexes are reported as a sensitivity, not the base case. | Assistant's recommendation, accepted | The national coastal freight index may not represent Alaska tug-and-barge trade, and one convention across all modes keeps figures comparable. |
| 6 | 2026-11-17 | Derive **statewide** rates only, no village-specific rates, for: ocean line-haul barge, coastal small barge (lightering), river barge, road, plane, ice road; and re-derive the transfer fees. Splitting the barge rate into three segments is the priority. | Owner | "For now I want all just to be statewide segments and no village specific." |
| 7 | 2026-11-17 | Third-party source PDFs live in the private harness repo (`cost_derivation_resources/`, branch `cost-sources`), never in the public data repo. | Owner and assistant | Copyright and the data repo's rule on primary sources. |
| 8 | 2026-11-17 | A figure that does not meet the three-method standard is still carried in the model, under a weaker label and a wider range (tiers Derived / Provisional / Assumed). | Owner asked how a "not ready" cost can work; this is the answer adopted | The model needs a number for every mode; the label says how far to trust it. |
| 9 | 2026-11-17 | Separate what was derived from what was assumed, with a reference for every derived input. | Owner | Reviewability. |
| 10 | 2026-11-17 | Use downloaded index data as the most trustworthy basis. CPI-U 2026 = January to September 2026 average, 332.243, replacing the toolkit's projected 330.0. | Owner | A downloaded series over a projection. The series used is a public mirror of the BLS table; replace with the BLS file when available. |
| 11 | 2026-11-17 | Archive the working files as run and write this log. Restructure the record as dated addenda to the existing chapters. | Owner | The skill's procedure (step 6), and so nothing rests on session scratch. |
| 12 | 2026-11-17 | Do not apply the rates yet. Applying the barge split waits for the marine / river water label being built in the data repo, so that the network of record changes once. | Owner asked; assistant recommended | The ocean and river rates need each waterway edge classed, and the landing fees need each landing typed. Two separate changes would mean two workflow 03 reruns, two exports and two harness adoptions. |
| 13 | 2026-11-17 | Search for the missing sources (air charter, winter haul, river tariffs and others) with a retrieval-only prompt; the owner will also look for current plane charter and ice-road prices. | Owner | Three segments lack a third independent method. |

## 3. How the derivation was run

The data repo's `derive-fuel-costs` skill sets the standard: three or more genuinely independent methods that
agree within about 3x, derived blind (without sight of the applied value), then checked against the primary
sources.

| Step | What was done | Output |
|---|---|---|
| Text extraction | Every local document and the 15 newly supplied ones converted to text; the FY2025 PCE report's community pages decoded (171 communities). | `harness: blind_derivations/working_2026-11-17/shared/pce_prices_with_distances.csv` (the page texts are regenerable from the PDFs and are not archived) |
| Fact sheets | Seven readers each read a group of documents in full and wrote a fact sheet with pages and quotes. | `extracts/` |
| Blind derivation, round 1 (barge) | Ten methods on the barge components from ISER 2010 and the PCE report. | `blind_results.json` |
| Blind derivation, round 2 (all segments) | Thirteen methods across the six segments and the fees, each forbidden from reading the applied values or earlier conclusions. | `derive2_results.json` (derivations) |
| Adversarial verification | One verifier per segment, not blind: re-opened the cited pages, redid the arithmetic, judged which methods are independent, ran the convergence test, stated what handling is inside each rate. | `derive2_results.json` (verdicts) |
| Assembly check | The assistant assembled the pieces into one set and priced the September network, to see whole-route costs. | what-if files |

Limits to know about:

- **One verifier per segment.** The verdicts that overturn applied values (plane, the barge-to-road fee, the
  river rate) have not had a second independent review.
- **Web access.** Agency websites were blocked from the session. Web search returned snippets only, which were
  not used as evidence. All quoted evidence comes from documents the owner supplied or the project already held.
- **Documents that were missing or thinner than their titles:** the US Army Corps of Engineers Nome study came
  without its economics appendix; the Alaska Energy Authority 2015 model has no distance variable; the 2009 energy
  report says delivery costs are "not published for antitrust reasons"; the State heating-oil contract behind the
  road chapter's third method was not among the supplied files.
- **Blind derivations of round 2 and part of round 1 were run on a smaller model** after a usage limit; the
  verifiers ran on the session's main model.

## 4. The outside report: what held and what did not

| Claim in the outside report | Finding against the local documents |
|---|---|
| Nome is supplied by sea | Confirmed. |
| The blended barge rate should be retired | Confirmed. |
| The fixed per-delivery figure and the per-mile figure for village delivery are one cost, not two | Confirmed. |
| $0.011 per gallon-mile fails on long river hauls | Confirmed. |
| "$0.19 per gallon is variable cost only" | Rebutted: ISER 2010 calls $0.19 to $0.22 the current line-haul rate. |
| Coastal freight index up 74.5% since May 2022 | Rebutted: the May 2022 value is 196.345, not 150.652. |
| 250 river miles from Bethel to McGrath | Rebutted: that is close to the straight-line distance; the river distance is about 420 to 430 miles. |
| Lower-Yukon villages are supplied from the coast | Rebutted for 2010: ISER 2010 says Mountain Village was supplied mostly from Nenana. Current practice is an open question. |

## 5. What was assembled by the assistant and is NOT a derived figure

These exist only to check whole-route costs. They are labelled Assumed wherever they appear.

| Item | Value | Basis |
|---|---|---|
| Flat coastal village landing charge | $0.65 per gallon | The provisional $0.45 fixed part plus small-barge mileage at about 250 miles, less the line-haul miles the route already pays. |
| Flat river village landing charge | $0.50 per gallon | The provisional river fixed part. |
| Landing classes | road-system port / line-haul hub / coastal village / river village | Road-system ports found from the network (a landing road-connected to Anchorage). Line-haul hubs were a hand list of six (Nome, Bethel, Kotzebue, Dillingham, Naknek, Unalaska). A reviewed rule is still needed. |
| River or ocean class of each waterway edge | nearest source-line vote against the reviewed river allowlist | To be replaced by the marine / river water label. |
| Route costs in the what-if | for example Anchorage to Nome $0.47 | Follow from the items above; not evidence for any rate. |

## 6. Open items when this log was written

1. A second independent review of the three overturning verdicts.
2. The evidence gaps listed in each addendum; the source search in `harness: blind_derivations/working_2026-11-17/GEMINI_SOURCE_SEARCH_PROMPT.md`.
3. A reviewed rule for which barge landings are line-haul or dock-served ports.
4. The marine / river water label (data repo), on which the barge split depends.
5. The BLS CPI-U table itself, to replace the mirror.
6. Network findings made along the way, outside the cost question: 42 of 180 barge-coded hubs have no barge route
   open in July (26 with no barge link, 12 behind waterway edges closed all year, including Kodiak and Unalaska);
   six of seven hand-drawn barge lines have a segment closed in all 12 months.

## 7. What applying the result will involve (not started)

1. `friction_costs.py` only: point, range and provenance comment together, per the skill.
2. `cost_derivation_tools.py --selftest` and `check_cost_invariants.py`.
3. Workflow 03 costing rerun on the owner's machine; export; harness adoption; regenerated and re-reviewed
   reference answers; the community list re-approved (the adoption chain's rebuild resets the approval).

## 8. Record assembly (2026-11-18)

- Each segment's verdict was written up as an addendum by a separate drafter, who restated every inflated figure
  to the 332.243 index and re-confirmed quoted passages in the document texts. A consistency critic then read all
  of them together. Of about 120 quoted passages searched, all were found on the stated page except six that sit on
  image-only pages (confirmed on the page images) and the State heating-oil contract, which is not among the
  supplied files.
- An errata check confirmed all seven reported defects in the existing chapters and code comments, and found
  fifteen more (`docs/cost_derivation/2026-11/errata.md`). The chapters were not edited; each has a short dated addendum
  pointing to its errata.
- Editor's decisions when assembling: one headline status per rate (ocean Derived, coastal Provisional, river
  Provisional, road Derived, plane Provisional, ice road Assumed, fees Provisional or Assumed); the village
  landing fee is zero wherever a small-barge or river delivery charge is applied (chapter 00 addendum, "Assembly
  rules"). These are the assistant's, for the owner to confirm.
- Known inconsistency left in place: fiscal-year 2025 prices are converted with calendar 2025 in the coastal
  addendum and with the mid-point of 2024 and 2025 in the river and ocean addenda (a 1.3% difference). The
  mid-point is the better convention for a July-to-June fiscal year.

## 9. Second batch of sources (2026-11-18)

- The owner ran the source search (section 2, decision 13) and added eleven files; two were byte-identical copies
  of documents already held. The nine new ones: Everts Air and Lynden Air Cargo rate pages (2026), the Northwest
  Alaska Transportation Plan memos on winter trails and on marine and riverine conditions (2019 drafts), the Alaska
  Barge Landing System Design Phase 1 report (2009), the North Slope Borough FY2023 financial report, the ICAS
  economic development strategy 2025-2030, the Beaver community plan (2016) and the NSEDC Fall 2006 newsletter.
- Each was read in full by a separate reader. Plane, ice road, coastal and river were then re-derived blind from
  the new documents and checked by one verifier each. **No status, point or range changed.** The new figures are
  consistency checks or loose bounds; none is a price for moving fuel.
- Not in the batch: the State heating-oil contract, a second truck-rack rate sheet, a river carrier tariff, an air
  charter quote for bulk fuel, a winter fuel-haul contract or invoice, the BLS CPI-U table.
- Side result for the barge-link work: two of the reports state, community by community, how fuel arrives.
  White Mountain's barge service up the Fish River is documented in both.
