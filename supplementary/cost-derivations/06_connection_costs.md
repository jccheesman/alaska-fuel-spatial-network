# 06 — Storage-Free Modal Connection Costs

All figures in 2026 dollars. This chapter re-derives the four modal-boundary fuel CONNECTION costs after the storage pseudo-mode was removed from the fee table. Under the option-(a) architecture each fee is now a single atomic modal-boundary crossing cost — no intake+storage-rest+outbound chain. The per-mile Barge/Plane/IceRoad rates are ALL-IN (each carries its own side's handling); the Road rate is CARRIAGE-ONLY (ATRI Tables 8/9 verified: no rack/terminal/loading line). Each fee therefore prices ONLY handling that has no home in a per-mile rate — in practice the road-carriage-side out-loading/receiving, or (where no road mode is incident) a thin facility-interface residual.

Two blind derivations were produced per boundary (ops_direct operational build-up; rate_residual rate-aware residual), then an adversarial skeptic hunted for double-counts and drop-counts. Final values are weighted by what survived the skeptic: strip any double-count, restore any drop-count.

---

## 6.1 — Barge <-> Road tanker-truck connection (`("barge","overland")`, 205 Transfer edges)

**Method 1 — ops_direct ($0.025/gal, range $0.015-0.045).** Bottom-up marginal build on a 3,500-gal local hub load: 0.75-hr occupancy (14-min pump at 250 gpm + 30-min setup/teardown) x 1.5 crew x ~$55/hr fully-loaded Alaska labor + $20/hr standby equipment + consumables = ~$82/load = $0.023/gal. ISER cross-check ($0.04-0.06/gal 2010 shore-side offload, CPI x1.53, road-slice ~1/3-1/2) brackets it. A pure marginal FLOOR; omits rack metering/capital/overhead.

**Method 2 — rate_residual ($0.28/gal, range $0.18-0.33).** Crowley Bethel Terminal tariff (eff. 8/10/2022): Marine Header $0.15 + Truck Rack $0.25 = $0.40 two-sided. Barge all-in rate already carries the $0.15 marine header -> SUBTRACT (anti-double-count); road carriage-only carries none of the $0.25 rack -> KEEP (anti-drop-count). Residual = $0.25 x CPI 1.10 = $0.28/gal.

**Skeptic outcome.** Both derivations UPHELD; neither commits the double-count. The DEPLOYED $0.40 total does — its $0.15 marine header is already in the all-in barge rate (0.0010) and must be stripped. No drop-count: road-side rack handling correctly retained (ATRI has no rack line, so it has no other home). rate_residual is the stronger construction (exact-match Alaska tariff); ops_direct's $0.025 is a floor ~10x below every posted anchor. Point shaded from $0.28 toward low-$0.20s for embedded sole-provider margin.

- **Counted:** road-carriage-side out-loading only (positioning, connect/bond, pumped transfer into truck, gauge/meter/paperwork, disconnect, shore attendant).
- **Excluded:** barge-side marine header/lightering/tank-farm intake (in all-in barge rate); ISER $0.20 deficiency adder; storage rest.
- **Final value: $0.24/gal, range $0.15-0.30, high confidence.** Change: $0.40 -> $0.24 by stripping the double-counted $0.15 marine header and lightly shading the $0.25 rack.

---

## 6.2 — Barge <-> Ice-road truck connection (`("barge","ice_road")`, 8 Transfer edges, North Slope)

**Method 1 — ops_direct ($0.011/gal, range $0.00-0.021).** Full pump-through build = ~$0.054/gal (0.94 hr x 2 crew x $84.34/hr NSB fully-loaded + $60/hr equipment / 4,000-gal parcel). Architecture gate: barge intake is in the all-in barge rate; ice-road load dwell is in the ice_road +20% adder — EXCLUDE both physical legs -> strict floor $0.00. Thin genuinely-uncounted residual = cross-modal changeover coordination (0.5 operator-hr / 4,000 gal) = $0.011/gal.

**Method 2 — rate_residual ($0.010/gal, range $0.005-0.019).** Full both-sides physical stack ~$0.08-0.12/gal is dominated by barge intake ($0.061-0.092 CPI-adjusted ISER) and ice-road load ($0.02-0.03) — BOTH already in their all-in rates, subtract them, netting near-zero. Only defensible residual = the standalone vessel<->land-tanker facility interface: Port of Alaska Item 260 (pipeline transfer 0.145 c/gal floor to vessel<->truck fuel 1.90 c/gal ceiling), mid ~$0.010/gal.

**Skeptic outcome.** Both UPHELD, clean — no double-count, no drop-count. Dominant finding: this is a boundary where BOTH incident modes are all-in and there is NO carriage-only road mode, so the drop-count trap cannot occur and both physical legs are correctly excluded. All sources verified exactly (NSB $105,047 + 67% burden; ISER $0.04-0.06; Noatak 3,000-5,000 gal; POA Tariff 10.1 2026 column). Converged $0.011/gal.

- **Counted:** thin cross-modal changeover / facility interface handling only (gauging, sampling, bond/ground verification, pump-tender supervision).
- **Excluded:** barge intake (all-in barge rate); ice-road load/unload dwell (+20% adder); storage rest. No road rack leg exists here.
- **Final value: $0.011/gal, range $0.00-0.02, low confidence.** Change: $0.40 placeholder -> $0.011. The old $0.40 was inherited from the barge<->overland row and double-counted both all-in legs. Completeness-only edge — never traversed same-month (barge May-Oct vs ice road Jan-Mar); near-zero routing impact.

---

## 6.3 — Road tanker <-> Ice-road truck connection (`("overland","ice_road")`, latent boundary)

**Method 1 — ops_direct ($0.022/gal, range $0.013-0.034).** Continuous truck-to-truck pumped transfer of a 3,000-gal batch: ~$112.50 both-sides operation (1.0 boundary labor-hr x $90/hr fully-loaded North Slope + $30/hr transfer equipment). Bill only the road (carriage-only) side ~0.55 share = $61.9/3,000 gal = $0.021 (2024$) x CPI 1.05 = $0.022/gal. Drops the ice-road-side pump-in dwell (in the +20% adder).

**Method 2 — rate_residual ($0.03/gal, range $0.02-0.045).** Top-down: ISER $0.04-0.06/gal (2010) x1.47 CPI, halved to one side = $0.03-0.044. Bottom-up check: ATRI $90.89/hr -> ~$97/hr 2026 x ~0.5 hr dwell + FERC terminal $0.006/gal ≈ $0.02/gal. Point $0.03.

**Skeptic outcome.** ops_direct UPHELD (cleaner). rate_residual NOT UPHELD: its top-down ISER $0.04-0.06/gal anchor is a MARINE BARGE 24-hr linehaul offload into a tank farm — barge intake handling already in the all-in barge rate, and a storage-node cost — mis-applied as a truck-to-truck header analog and inflated. Halving it does not transmute a barge cost into a road cost. STRIP the top-down; rate_residual's own clean bottom-up (~$0.02) then agrees with ops_direct. The $0.03 point survived only by two offsetting errors canceling. Converged on ~$0.022.

- **Counted:** road-carriage-side share of the metered PTO pump-out + connect/disconnect, bond/ground, cold-weather transfer equipment (not the carriage truck).
- **Excluded:** ice-road-side load/unload dwell (+20% adder); both trucks' carriage economics; storage rest (the atomic crossing, not truck->tank->truck).
- **Final value: $0.022/gal, range $0.014-0.032, medium confidence.** Change: $0.25 -> $0.022. The old $0.25 was an explicit storage/tank-rack analog (two-leg chain, TODO seed); removing the storage rest and stripping the double-counted ISER marine anchor lands the atomic fee at ~$0.02. Latent Dalton-corridor boundary.

---

## 6.4 — Air-cargo fuel <-> Road tanker connection (`("plane","overland")`, latent boundary)

**Method 1 — ops_direct ($0.03/gal, range $0.015-0.10).** Tarmac hose transfer of a 3,000-gal parcel: road-side receiver labor 0.83 hr x $60/hr fully-loaded Alaska tanker CDL = $50 + road-side equipment (receiving tanker standby, PTO pump, hoses, grounding) ~$37 = $87/3,000 gal = $0.029/gal. Excludes the aircraft's own onboard pump, crew, and ground standby (all in the all-in charter rate).

**Method 2 — rate_residual ($0.038/gal, range $0.03-0.05).** ISER $0.04-0.06/gal (2010) as full both-sides handling; subtract ~50% aircraft side (in charter rate); road residual $0.02-0.03 x CPI 1.53 = $0.038/gal.

**Skeptic outcome.** ops_direct UPHELD. rate_residual NOT UPHELD: its ISER anchor is a barge linehaul offload INTO A TANK FARM — barge intake (already in the all-in barge rate) plus storage-node receiving labor — imported into an air<->truck fee; the 50% subtraction avoids the plane double-count but the residual still inherits the barge/tank-farm basis, over-stating road-only handling. Shaded down. ops_direct's road-side PTO-pump equipment leg is also softly over-attributed because Everts DC-6/C-46 carry their own onboard offload pumps (pumping already in the charter rate); trim the equipment leg. Converged on ~$0.025.

- **Counted:** road/ground-side receiving handling only — receiver/driver connect-monitor-disconnect labor (bond/ground, camlock, pump watch, breakaway) + modest fittings/grounding-gear charge (NOT an independent pumping engine).
- **Excluded:** aircraft onboard pump, flight crew, aircraft ground standby/positioning (all in the all-in plane charter rate 0.025); storage rest.
- **Final value: $0.025/gal, range $0.015-0.045, medium confidence.** Change: $0.157 -> $0.025 by removing aircraft-side handling (already in the plane rate) and the storage rest, and shading the barge/tank-farm-proxy anchor. Latent/low-frequency (air fuel economical only <~5,000 gal within a few hundred air-miles of a refinery).

---

## 6.5 — Summary table (2026$)

| Boundary | Old through-storage | New storage-free fee | Range | Confidence | Counts |
|---|---|---|---|---|---|
| `("barge","overland")` | 0.40 | **0.24** | 0.15-0.30 | high | road-carriage-side rack out-loading only |
| `("barge","ice_road")` | 0.40 | **0.011** | 0.00-0.02 | low | thin cross-modal changeover / facility interface only (no road mode incident) |
| `("overland","ice_road")` | 0.25 | **0.022** | 0.014-0.032 | medium | road-carriage-side share of truck-to-truck transfer |
| `("plane","overland")` | 0.157 | **0.025** | 0.015-0.045 | medium | road/ground-side receiving handling only |

Recurring construction rule: bill ONLY handling with no home in a per-mile rate. Because Road is carriage-only, that is the road-carriage side of every crossing; the all-in side (barge intake, aircraft pump/crew, ice-road +20% dwell) is excluded to prevent double-counting; storage rest is excluded entirely. Where no road mode is incident (barge<->ice_road), only a thin facility-interface residual remains, so the fee collapses near zero.

---

## 6.6 — Coupling to per-mile rates

The four per-gallon-mile transport rates and their includes-basis are UNCHANGED by removing the storage leg. The rates remain:

- **Barge 0.0010 — all-in.** Carries vessel-to-shore lightering, marine header, and marine-terminal/tank-farm intake handling.
- **Plane 0.025 — all-in charter.** Carries the aircraft's onboard offload pump, flight/ground crew during offload, and aircraft positioning/standby.
- **IceRoad 0.010 — all-in.** Carries an explicit +20% load/unload adder over the round-trip cycle (both origin fill and destination discharge dwell).
- **Road 0.0007 — carriage-only.** Fuel, tractor/trailer, R&M, tires, insurance, permits, driver wages over running miles. ATRI Tables 8/9 verified: NO rack/terminal/loading/unloading line.

The storage pseudo-mode that was deleted never lived inside any per-mile rate — it was an artifact of the old through-storage fee construction (intake + storage-rest + outbound). Re-scoping the fees to the atomic crossing moves nothing into or out of a per-mile rate; the change is confined to the fee table. Consequently:

- **All-in-side handling stays home in its all-in rate.** Marine intake in Barge; aircraft handling in Plane; ice-road load/unload dwell in IceRoad. This is exactly why those legs are EXCLUDED from the connection fees (double-count guard). The deployed $0.40 barge<->overland total violated this by re-billing the $0.15 marine header — corrected here to $0.24.
- **Road-carriage-side handling is the only genuinely-homeless handling, and it correctly lives in the connection fees.** Because Road is carriage-only, into-truck pumping, connect/disconnect, bond/ground, gauging/metering, and receiver dwell have no home in the Road rate. Every fee is scoped to exactly this (drop-count guard).
- **Hub storage is priced nowhere** — not in a per-mile rate, not in a boundary fee. It was never a node; if delivered-cost storage is later needed it must be added as a separate component, never folded into a rate or a crossing fee.

Net: no per-mile rate changes, no orphaned handling under option (a). The all-in side handling sits in its all-in rate; the road-carriage-side handling sits in the connection fee; storage is intentionally out of scope.
---

## 6.7 — Worked routing examples (sanity check)

To confirm the storage-free fees do not distort mode choice, six illustrative routes were priced end to end. **Distances are hypothetical but Alaska-plausible**; the point is the *ranking* between modes, not the exact dollar value. Route cost ($/gal) = Σ(leg miles × per-mile rate) + Σ(connection fee at each mode change), using the per-mile rates from Chapter 6.6 and the new connection fees from the summary table above.

| Route | Carriage | Handoff | **Total** | (old fees) |
|---|--:|--:|--:|--:|
| **A1** — Barge to a river village (1320 mi barge + 40 mi truck) | 1.348 | 0.240 | **1.588** | 1.748 |
| **A2** — Fly that same village instead (400 mi plane + 5 mi truck) | 10.004 | 0.025 | **10.029** | 10.161 |
| **B1** — Winter ice road to a North Slope village (500 mi truck + 68 mi ice road) | 1.030 | 0.022 | **1.052** | 1.280 |
| **B2** — Fly that village in winter instead (300 mi plane + 3 mi truck) | 7.502 | 0.025 | **7.527** | 7.659 |
| **C1** — Straight road delivery, no handoff (600 mi truck) | 0.420 | 0.000 | **0.420** | 0.420 |
| **C2** — Same town by barge + short truck (1100 mi barge + 15 mi truck) | 1.111 | 0.240 | **1.351** | 1.510 |

**Three checks, all pass:**

1. **The cheap-to-expensive order held.** In every head-to-head the expected mode still wins, and by a wide margin: barge beats plane ~6× (A1 vs A2), ice road beats plane ~7× (B1 vs B2), and road beats barge where a road exists (C1 vs C2, $0.42 vs $1.35). Plane remains the last resort; road remains cheapest.

2. **The lowered handoffs do not over-promote plane or ice road.** A plane costs $0.025 *per mile*, so even a short flight dwarfs its now-$0.025 handoff. The per-mile rates are far enough apart (plane 25×, ice road 14×, barge 1.4× the road rate) that shaving a connection fee never flips a mode choice over any realistic distance.

3. **The handoff fee matters only where it should.** On barge routes it is a real slice (~15% of the A1 total), because loading fuel off a barge onto a truck at a hub is genuine work. On the long, expensive plane and ice-road hauls it is a 2–3% rounding error. Correct shape.

**Net effect of the re-derivation:** every total fell modestly versus the old through-storage fees (right column), but **no ranking flipped** — old and new agree on which mode wins every comparison. The correction adjusted the *level* of cost without changing any *decision*, which is the expected signature of a fix that only removed double-charging. The one value that looks anomalous in isolation — `barge↔ice_road` at ~$0.01 — never appears in a real route, since barges (May–Oct) and ice roads (Jan–Mar) never share a month.
