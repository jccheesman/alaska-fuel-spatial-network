---
name: assign-friction-values
description: Procedure for safely assigning, modifying, or adding friction
  values in the environmental friction surface. Use when the user wants to
  change a LULC class multiplier, adjust a permafrost zone, add a new modifier
  layer, retune slope friction, or reclassify a raster into friction space.
  Enforces single source of truth in friction_config.py and the friction-vs-cost
  separation rule. Do NOT use for transport-mode cost rates — those live in
  friction_costs.py and are out of scope.
---

# Assign friction values

## Core invariants (always true)

These rules are non-negotiable. If a proposed change would break any of them,
stop and surface the conflict to the user before proceeding.

1. **Single source of truth.** All friction multipliers and thresholds live in
   `source_scripts/friction_surface/friction_config.py`. Never hardcode a friction value in a
   script, notebook, or new module — import it from `friction_config`.

2. **Friction is environmental only, baseline 1.0.** Friction values represent
   environmental traversability (slowdown vs. ideal-conditions reference). A
   value of 1.0 = no penalty. Operational/per-mode dollar cost lives in
   `friction_costs.BASELINE_RATES_PER_GALLON_MILE`. **Never fold cost into
   friction.** A faster mode (e.g. road truck vs. ice road) does not get a
   lower friction — it gets a lower cost rate.

3. **Multiplicative composition.** Modifiers compound by multiplication, not
   addition: `friction = slope × LULC × permafrost_mod`. Each modifier's
   baseline must be 1.0 so identity composition is a no-op.

4. **NoData propagates as NoData.** Use `FRICTION_NODATA` from
   `friction_config`. Never let a sentinel value (e.g. -9999) get multiplied
   into a real friction value.

5. **Justify every numeric change.** Slope, permafrost, and ice values in
   `friction_config.py` carry citations and rationale in comments (the
   permafrost block is the standard to follow); `LULC_FRICTION` multipliers
   currently have class labels only. Any change MUST add or update a comment
   explaining the new value's basis — and when touching an LULC value, add
   the missing rationale rather than perpetuating the gap.

## When to use this skill

Trigger when the user wants to:
- Add a new class to `LULC_FRICTION` (e.g. Dynamic World adds a new class)
- Modify an existing friction multiplier or threshold
- Add a new modifier layer (e.g. wildfire risk, water table, fire scars)
- Reclassify a new raster into friction space using the project's conventions
- Audit whether a friction-assignment change is internally consistent

Do NOT trigger for:
- Cost rate changes (`friction_costs.py`) — use the `derive-fuel-costs` skill
- Grid alignment (`align-to-ak-stack` skill handles that)
- Adding corridor masks (`workflows/01_friction_build/01_build_corridor_masks.py` already handles that)

## Where the canonical values live

- `source_scripts/friction_surface/friction_config.py` — all multipliers, thresholds, constants
  - `LULC_FRICTION` — Dynamic World class → multiplier
  - `PERMAFROST_ZONE_BREAKS` + `PERMAFROST_ZONE_MULTIPLIERS` — binned modifier
  - `SEA_ICE_THRESHOLD`, `RIVER_ICE_THRESHOLD` — ice gating cutoffs
  - `ROAD_FRICTION`, `ROAD_BRIDGE_FRICTION`, `WATER_FRICTION_BARGE` — baselines
  - `FRICTION_NODATA` — sentinel
- `friction_surface/friction_surface.py` — the functions that apply them
  - `compute_lulc_friction()` — LULC reclassification
  - `compute_slope_friction()` — slope → friction
  - `compute_permafrost_modifier()` — permafrost binning
  - `build_static_base()` — multiplicative composition
  - `build_mode_friction()` — per-mode (ice gating, road burn-in)

## Procedure: adding or changing a friction value

1. **Locate the canonical entry.** Confirm the value lives in `friction_config`
   and not somewhere else (grep for it first — orphaned hardcoded values are
   common bugs).

2. **Capture the rationale.** Before changing a number, surface to the user:
   - What is the current value?
   - What is the justification comment / citation in the config?
   - What is the proposed new value and its justification?
   If the user can't articulate a justification, push back — the friction
   surface is a published scientific product, not an ad-hoc tuning knob.

3. **Apply the change in `friction_config.py` only.** Update both the constant
   and its docstring comment so the rationale stays attached to the number.

4. **Check for downstream assumptions.** Search the repo for uses of the
   changed constant. If anything outside `friction_surface/` reads the value,
   confirm the change is intended for those callers too.

5. **Rebuild and validate** via the `run-friction-pipeline` skill, which
   regenerates the stack and runs the whole QA chain (grid conformance →
   preflight → output QA), interpreting any failure into a cause and fix:
   ```
   python .claude/skills/run-friction-pipeline/scripts/validate_friction_stack.py --rebuild
   ```
   Under the hood this runs `run_friction_pipeline` then
   `qa_friction_stack` (which you can still invoke directly:
   `python -m friction_surface.qa.qa_friction_stack`). It checks the 14-file
   output contract, profile match against the reference grid, barge
   ice-gating direction, and the value floor. Exit 0 =
   pass; any nonzero exit means the change broke an output invariant — report
   the failing check to the user, do not paper over it.

## Procedure: adding a new modifier layer

1. **Confirm it belongs in friction, not cost.** If the new factor varies
   per-mode operationally (fuel price, fleet age, labor), it is cost, not
   friction. Push back and route to `friction_costs.py`.

2. **Define the modifier with baseline 1.0.** At the "no penalty" reference
   condition, the modifier must be 1.0 so multiplicative composition is a
   no-op when the modifier is absent.

3. **Add the constant(s) to `friction_config.py`** with a docstring comment
   covering: data source, citation, rationale for the chosen multiplier
   range, how it interacts with existing modifiers.

4. **Add the reclassification function to `friction_surface.py`**, following
   the pattern of `compute_permafrost_modifier()` — accept a raster array,
   return the modifier array on the same shape, propagate NoData correctly.

5. **Wire it into `build_static_base()`** with explicit multiplication. Do
   not silently introduce conditional logic — every pixel gets the same
   composition formula.

6. **Add the input layer's path** to `friction_surface/friction_paths.py` and
   confirm the source raster is aligned to the LULC reference grid (see
   `align-to-ak-stack` skill).

## What NOT to do

- Do NOT define a parallel lookup table outside `friction_config.py` for any
  reason — including "just for this script" or "temporarily".
- Do NOT use additive composition (`a + b`) instead of multiplicative (`a * b`).
- Do NOT introduce per-mode friction adjustments to capture cost effects.
  Cost goes in `friction_costs.py`. Always.
- Do NOT change a documented friction value without also updating its
  rationale comment.
- Do NOT use a baseline other than 1.0 for a new modifier. If the modifier
  must penalize everything, that means the baseline reference condition
  hasn't been chosen correctly.

## Related

- [[ak_stack_reference_grid]] — LULC is the canonical grid for all friction
  inputs.
- [[friction_vs_cost_separation]] — the rule this skill enforces, with
  full rationale.
- [[friction_stack_output_contract]] — invariants the pipeline output must
  satisfy after any friction-value change; enforced mechanically by
  `python -m friction_surface.qa.qa_friction_stack`.
- `align-to-ak-stack` skill — handles grid alignment of new modifier rasters.
