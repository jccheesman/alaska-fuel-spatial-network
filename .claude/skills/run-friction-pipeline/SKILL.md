---
name: run-friction-pipeline
description: Rebuild the friction stack after an input or config change and
  run the full QA chain, interpreting each failure into a cause and a fix.
  Use when the user has changed a friction value, a cost rate, or an input
  raster and asks to regenerate/rebuild the stack, run QA, validate the
  friction outputs, or debug a QA failure (grid conformance, preflight, the
  14-file output contract, barge ice-gating direction, overland value
  floor). This is the build-and-validate phase the align-to-ak-stack,
  assign-friction-values, and derive-fuel-costs skills hand off to. Do NOT
  use to change friction values (assign-friction-values), cost rates
  (derive-fuel-costs), or to align a single new raster (align-to-ak-stack).
---

# Run friction pipeline

The build-and-validate phase of the friction-surface skill set. The other
three skills each *change* one thing and then say "now rebuild and validate"
— this skill owns that step and, critically, interprets what a QA failure
means and where to fix it.

## The friction-surface skill set

Each skill owns one phase; this one closes the loop.

| Phase | Skill | Changes |
|---|---|---|
| Intake | `align-to-ak-stack` | snap a raster to the canonical grid |
| Friction config | `assign-friction-values` | multipliers in `friction_config.py` |
| Cost config | `derive-fuel-costs` | rates/fees in `friction_costs.py` |
| **Build + validate** | **`run-friction-pipeline`** (this) | regenerate the stack, run QA, interpret failures |

After finishing in any of the first three, come here.

## Core invariants (always true)

1. **Validate before trusting an output.** A friction stack is only
   consistent if it passes the whole chain — grid conformance → input
   preflight → output QA. A green build with a red QA is not done.
2. **Inputs gate outputs.** Never debug an output-QA failure before the
   input checks pass: a bad grid or out-of-range input produces a
   downstream QA failure whose real cause is upstream. Run the chain in
   order; fix the earliest failure first.
3. **A rebuild mutates the graph.** `--rebuild` runs
   `run_friction_pipeline`, which writes `fuel_network.duckdb`
   (mode_specific_edges + connects_to). Validation without `--rebuild` is
   read-only. Only rebuild when the surfaces or edges actually need
   regenerating, and never while the DB is open elsewhere.
4. **Fix at the source, not the symptom.** Every grid/preflight failure
   traces to an upstream producer (a GEE export, a preprocessing pad/align
   script, a `friction_config.py` value). Fix it there and re-run — never
   patch the built raster in place.
5. **Don't loosen a check to make it pass.** The QA thresholds (14-file
   contract, July>January ice gating, value floor) encode the output
   contract. A failing check is a real defect; surface it, don't relax it.

## The orchestrator

`scripts/validate_friction_stack.py` runs the chain and prints, under any
failing step, the probable cause and the concrete fix (which upstream
script or sibling skill owns it) — the domain knowledge no single QA script
carries.

```
# read-only validation (default): grid -> preflight -> output QA
python .claude/skills/run-friction-pipeline/scripts/validate_friction_stack.py

# rebuild first, then validate (writes fuel_network.duckdb)
python .claude/skills/run-friction-pipeline/scripts/validate_friction_stack.py --rebuild

# run every step even after a failure; custom dirs
python .claude/skills/run-friction-pipeline/scripts/validate_friction_stack.py \
    --keep-going --inputs-dir INPUTS --output-dir STACK
```

Exit 0 = every gating step passed. `--inputs-dir` / `--output-dir` override
the `RASTER_DIR` / `FRICTION_DIR` defaults (the latter is passed through as
the env var the QA script reads).

## The chain (what each step gates)

1. **`check_grid_exports.py`** — every input raster sits on the canonical
   full-AK grid (EPSG:3338, 28001×16567, origin −2130150). Metadata-only,
   cheap. Fail → a layer isn't grid-pinned.
2. **`friction_preflight`** — every raster the build will open matches the
   LULC canonical grid (CRS/res/origin/shape) and has sane value ranges
   (LULC 0..8, slope 0..90, ice 0..100). Fail-fast; raises `PreflightError`
   inside the build too.
3. **`run_friction_pipeline`** *(only with `--rebuild`)* — builds the 14
   on-disk surfaces (`overland.tif` + `road_base.tif` + `barge_01..12.tif`,
   backing the 24 logical (mode, month) entries), computes edge costs, and
   writes the graph.
4. **`qa_friction_stack`** — the deduped 14-file set + profile match; barge
   July valid-pixels > January (ice-gating direction); overland min valid ≥
   `min(SLOPE_FRICTION)`. Exit 1 = hard fail, 2 = output dir missing.

## Interpreting failures

The orchestrator prints cause+fix inline; the summary below is the routing
map.

- **Grid conformance (step 1) fails** — a layer is off the canonical grid or
  all-NoData. Re-pin it: GEE layers export on the canonical crsTransform;
  `pad_sea_ice_to_grid.py` / `pad_river_ice_to_grid.py` for the ice stacks;
  `align_permafrost.py` for permafrost; the `align-to-ak-stack` skill for an
  arbitrary new raster.
- **Preflight (step 2) fails** — grid drift → snap upstream then
  `align-to-ak-stack`; out-of-range values → wrong/mis-scaled source. The
  mid-Yukon river-ice winter zero pockets are a *known upstream data bug*
  (memory `river_ice_winter_zero_pockets`), fixed in the ArcGIS pipeline, not
  the stack.
- **QA file-set / profile (step 4) fails** — build incomplete, `FRICTION_DIR`
  wrong, or a stray old `overland_MM.tif`. Clean and rebuild.
- **QA barge ice-gating fails** (July ≤ January) — a swapped month or a
  flipped sea/river-ice threshold direction in `friction_config.py`.
- **QA overland value floor fails** — a friction multiplier < 1.0 slipped
  into `friction_config.py` (multipliers must be ≥ 1.0) or a NoData sentinel
  leaked into the product → fix via `assign-friction-values`.

## Procedure

1. **Identify what changed** and confirm it landed in the single source of
   truth (`friction_config.py` for friction, `friction_costs.py` for cost) —
   not hardcoded in a script.
2. **Decide rebuild scope.** Friction-value or input-raster change → needs a
   surface rebuild (`--rebuild`). Cost-rate-only change → surfaces are
   unchanged; the graph edges still need recomputing (rerun
   `run_friction_pipeline`; surfaces can be reused via its `--skip-surfaces`
   flag).
3. **Run the chain.** Start read-only to see current state, then `--rebuild`
   once inputs pass. Fix the earliest failure first (invariant 2) and re-run
   until exit 0.
4. **Refresh downstream artifacts** if values changed: `viz/` figures
   (`plot_friction_stack`, `plot_combined_friction`, the schema/pipeline
   diagrams) and, for cost changes, the `derive-fuel-costs` downstream list
   (workbook, `assemble_weighted_graph`, cost-equation figure).
5. **Report the result** — which steps passed, what any failure was, and
   what you changed to fix it. Never report "done" on a nonzero exit.

## What NOT to do

- Do NOT edit a built raster to make QA pass — fix the upstream producer.
- Do NOT `--rebuild` to "see if it helps" while chasing a preflight failure;
  the build will just re-raise the same `PreflightError`. Fix inputs first.
- Do NOT relax a QA threshold or delete a stray-file check to get a green.
- Do NOT change friction or cost values here — route to the owning skill.

## Related

- `align-to-ak-stack`, `assign-friction-values`, `derive-fuel-costs` — the
  three change-phase siblings that hand off to this skill.
- [[friction_stack_output_contract]] — the 14-file / 24-entry contract QA
  enforces.
- [[ak_stack_reference_grid]] — the canonical grid every input must sit on.
- [[river_ice_winter_zero_pockets]] — a known upstream data bug that
  surfaces as a preflight/QA anomaly, fixed in the ArcGIS pipeline.
