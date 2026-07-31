---
name: derive-fuel-costs
description: Procedure and toolkit for deriving, updating, and verifying the
  per-modality fuel-delivery cost rates (BASELINE_RATES_PER_GALLON_MILE) and
  intermodal transfer fees (INTERMODAL_TRANSFER_FEES) in
  friction_surface/friction_costs.py. Use when the user wants to change a
  cost rate or transfer fee, re-derive a rate from new source documents, add
  a fee for a new modal boundary, or audit cost-model consistency. Enforces
  the three-round blind-derivation evidence standard, gallon-mile
  normalization, the no-double-count transfer-fee rule, and machine-checked
  ranges. Do NOT use for environmental friction multipliers — those live in
  friction_config.py (assign-friction-values skill).
---

# Derive fuel costs

The cost-side sibling of `assign-friction-values`. Everything here concerns
operational dollar cost ($/gallon-mile rates and $/gallon transfer fees);
environmental traversability stays in the friction surface.

## Core invariants (always true)

If a proposed change would break any of these, stop and surface the conflict
before proceeding.

1. **Single source of truth.** All rates, fees, ranges, and mode metadata
   live in `friction_surface/friction_costs.py`. Downstream consumers
   (`assemble_weighted_graph.py`, `outputs/tables/make_modality_cost_table.py`)
   import from it — never redefine a rate in a script, table builder, or notebook.

2. **Gallon-mile normalization, 2026 dollars.** Every modality rate is USD
   per **gallon-mile** in real 2026$. Source tariffs arrive as $/vehicle-mile
   (divide by payload capacity), $/lb (multiply by fuel density + surcharge),
   or $/gal over a route (divide by verified route miles) — use
   `scripts/cost_derivation_tools.py` for these conversions, never ad-hoc
   arithmetic.

3. **Dollar-year discipline.** State every source figure's dollar year and
   CPI-adjust to 2026$ via `cpi_adjust()` (canonical table in the toolkit;
   2010→2026 ≈ ×1.51). The single biggest verified error class in the old
   derivations was mixing 2010 and 2026 dollars.

4. **Convergence is the evidence standard.** A rate is applied only when ≥3
   genuinely independent methods (published tariff/contract, engineering
   build-up, revealed price differentials) converge — blind (no anchoring on
   the current value), then web primary-source verified, then verified
   against local documents. A spread ratio beyond ~3× across methods means
   the derivation is not ready. Record point, range, confidence, and what
   the figure includes/excludes.

5. **Transfer fees bill only uncounted handling.** Fees are atomic
   modal-boundary crossings, storage-free (no storage/drum pseudo-modes
   until hub storage becomes a graph node in Phase 6). The Barge, Plane,
   and IceRoad per-mile rates are ALL-IN (each already carries its own
   side's handling); the Road rate is CARRIAGE-ONLY. So a fee bills only
   the road-carriage-side handling — including an all-in side's handling
   in a fee is a double-count (the bug the 2026-07-28 re-derivation
   removed). Where no road mode is incident, the fee collapses to a thin
   facility-interface residual.

6. **No costless edge.** Every modal boundary that can appear as a Transfer
   edge must key a fee entry (either key order; never both).
   `assemble_weighted_graph._lookup_fee` hard-errors on a missing pair —
   keep latent boundaries priced rather than letting a future edge crash
   routing.

7. **Ranges are data, updated with the point.** Every rate has a
   `BASELINE_RATE_RANGES` band and every fee a `"range"` key. When a
   re-derivation moves a point estimate, move its range in the same edit,
   and update the provenance comment — the number, its band, and its
   citation travel together.

8. **Friction–cost separation.** Never fold a cost effect into a friction
   multiplier or vice versa. Per-mode operational factors (fuel price,
   labor, fleet) are cost; environmental traversability is friction.

## Where the canonical values live

- `friction_surface/friction_costs.py`
  - `BASELINE_RATES_PER_GALLON_MILE` + `BASELINE_RATE_RANGES` — the four
    modality rates and their documented bands
  - `INTERMODAL_TRANSFER_FEES` — one entry per modal boundary
    (`total`/`counts`/`range`); routing reads only `total`
  - `VEHICLE_MILE_RATES_REFERENCE` — raw carrier-tariff inputs (traceability
    only, not consumed by routing)
  - `MODE_METADATA` / `METHOD_TO_MODE` / `RATE_KEY_BY_MODE` — mode↔rate-key↔
    facility-method vocabulary
  - `STATE_CONTRACT_ADDERS_PER_GALLON` — validation targets ONLY (they
    bundle all transport + handling + margin; never an additive input)
  - `chain_cost_with_transfer_fees()` — multi-leg costing helper
- `assemble_weighted_graph.py` — `FEE_MODE` (edge_class → fee vocabulary),
  `infer_transfer_fees()` (prices live Transfer edges)

## Source registry

Derivation documents (the paper trail every value must trace to), under
`supplementary/`:

- `supplementary/cost-derivations/00_executive_summary.md` — methodology + final table
- `supplementary/cost-derivations/01_road.md` … `04_ice_road.md` — per-mode full
  derivations with verification addenda
- `supplementary/cost-derivations/05_transfer_fees.md` — per-leg fee decomposition
  (incl. the storage components deliberately NOT in the fee table)
- `supplementary/cost-derivations/06_connection_costs.md` — storage-free fee
  re-derivation + §6.6 coupling proof that fees don't alter per-mile rates
- `supplementary/cost-verification/Fuel Cost Blind Derivations.pdf` — compiled report
  (rebuild: `supplementary/cost-derivations/build_pdf.py` / `build_transfer_pdf.py`)
- `supplementary/cost-verification/Fuel Cost Derivation Verification.md` — round-2/3 verification log

Primary sources (third-party PDFs) are NOT included in this public repo —
they are internal/external only (originals kept outside the release, e.g.
`DOE_MAS-public-internal/cost_derivation_resources/`). Cited here for
provenance:

- `ATRI-Operational-Costs-of-Trucking-07-2025.pdf` — Road build-up floor
- `6_barry_pulliam-_econ_one_...refining_industry.pdf` — Road (Valdez→
  Fairbanks $0.20/gal transport map)
- `components of alaska fuel costs.pdf` (ISER 2010) — Barge linehaul/
  small-barge decomposition (2010$ — always CPI-adjust)
- `2026.03.01 FY2025 PCE Statistical Report...pdf` — margin-free revealed
  prices; ice-road regime traffic split; plane two-part regression
- `NorthSlopeBorough-Budget-Book-FY26-27-FINAL-1.pdf`,
  `NorthSlope_CommunityWinterTrails_2020.pdf`,
  `Northwest_Arctic_Borough_Noatak_Winter_Fuel_Haul_System.pdf` — ice-road
  operations (loads, speeds, equipment; no published rate exists)
- `08-marine-diesel-fuels.pdf`, `POA Economic Assessment_202405013.pdf` —
  marine context
- `inputs/fiscal_policy/FY2025-PowerCostEqualization-...by-Utility.pdf`,
  `inputs/market_data/Fuelcost_viability_final.pdf` — validation

## Scripts

- `scripts/cost_derivation_tools.py` — conversion/derivation functions
  (`cpi_adjust`, `gallon_mile_rate`, `per_lb_to_per_gallon`,
  `per_gallon_over_distance`, `nm_to_statute`, `ols`, `convergence`,
  `blend`). Import them when doing derivation arithmetic.
  `--selftest` re-derives every applied rate and fee from its documented
  inputs; exit 0 means code and derivation docs agree.
- `scripts/check_cost_invariants.py` — mechanical audit: rates in ranges,
  fee schema (canonical keys, no costless edge, no reversed duplicates),
  mode-metadata round-trips, derived-constant aliases, chain-cost smoke
  test, live-graph fee coverage against `fuel_network.duckdb`, workbook
  freshness. Exit 0 = pass.

## Procedure: update an existing rate or fee

1. **Read the current provenance.** The comment block above the value in
   `friction_costs.py` plus the matching `supplementary/cost-derivations/`
   chapter. Know what the current number includes/excludes before proposing
   a new one.
2. **Derive with ≥2 independent methods** (3 for a from-scratch rate) using
   the toolkit functions; log sources, arithmetic, and dollar-year
   conversions. Run `convergence()` on the method estimates.
3. **Check the no-double-count rule** (fees only): identify which incident
   side's handling is already inside an all-in per-mile rate and exclude
   it. Bill only handling with no home in a per-mile rate.
4. **Apply in `friction_costs.py` only** — point value, range, and
   provenance comment in one edit (invariant 7).
5. **Verify mechanically:**
   ```
   python .claude/skills/derive-fuel-costs/scripts/cost_derivation_tools.py --selftest
   python .claude/skills/derive-fuel-costs/scripts/check_cost_invariants.py
   ```
   If the selftest fails because the documented method inputs changed,
   update its method constants to the new documented derivation — never
   loosen a tolerance to make a stale derivation "pass".
6. **Update the derivation record**: append a dated addendum to the
   relevant `supplementary/cost-derivations/` chapter and rebuild the PDF.
7. **Refresh downstream artifacts**: rerun
   `outputs/tables/make_modality_cost_table.py` (workbook),
   `assemble_weighted_graph.py` (edge_costs), and `plot_cost_equation.py`
   if the cost-equation figure shows the changed value.
8. **Validate against revealed prices**: sanity-check a modeled route
   $/gal against `STATE_CONTRACT_ADDERS_PER_GALLON` (same order of
   magnitude; contract adders sit above modeled transport because they
   bundle margin/overhead).

## Procedure: add a fee for a new modal boundary

1. Confirm the boundary is real: which `edge_class` pair meets at the
   Transfer edge, mapped through `FEE_MODE`? Check whether the pair is
   temporally traversable (e.g. barge↔ice_road never is — months don't
   overlap) before investing derivation effort; an untraversable pair
   still needs a completeness entry, but a thin residual suffices.
2. Apply invariant 5 to decide what the fee bills, derive per the update
   procedure, and add the entry with `total`/`counts`/`range` in one key
   order only.
3. Run the checker — `graph.fee_coverage` proves every live Transfer edge
   still prices.

## What NOT to do

- Do NOT tune a rate to make a routing result look right. Rates come from
  derivations; if routing output looks wrong, suspect the graph or the
  friction weights first.
- Do NOT divide a fixed per-delivery cost by route miles to make it a
  per-mile rate (the "smearing" error) — fixed handling belongs in a
  transfer fee.
- Do NOT add a storage, drum, or per-leg fee entry before Phase 6 makes
  hub storage a graph node.
- Do NOT use `STATE_CONTRACT_ADDERS_PER_GALLON` as an input — validation
  only.
- Do NOT change a point value without its range and provenance comment,
  and never edit `VEHICLE_MILE_RATES_REFERENCE` to "agree" with a new rate
  — it records raw source tariffs, not conclusions.

## Related

- [[fuel_cost_rate_verification]] — the applied rates and their three-round
  history.
- [[friction_vs_cost_separation]] — the boundary this skill sits on the
  cost side of.
- [[bridge_edge_terminology]] — check `source` before assuming an edge
  type's fee semantics.
- `assign-friction-values` skill — the friction-side sibling; routes here
  for anything in `friction_costs.py`.
- `run-friction-pipeline` skill — the build-and-validate phase; after a
  cost change, rerun `run_friction_pipeline` to recompute graph edges
  (surfaces are unchanged by a cost-only edit; reuse them with
  `--skip-surfaces`), then validate.
