---
name: build-and-verify-network
description: Run the mmnet build pipeline from a profile.yaml and PROVE the result is a correct,
  connected multimodal network. Use after authoring or editing a profile (see
  define-network-profile), or whenever you need to (re)produce output/03_network and confirm
  connectivity. Do NOT use to change what the network contains (that's a profile edit), and do NOT
  treat a build as done until the connectivity proof passes.
---

# Build and verify the network

`mmnet` turns a `profile.yaml` into a connected multimodal graph via a **hybrid R↔Python** build,
then you must PROVE it. Running is nearly deterministic; the judgment is in the prerequisites and in
reading/verifying the result.

## Core invariants (non-negotiable)

1. **The R↔Python seam — no redundancy.** R nodes each land mode's lines (planar noding/subdivision
   via `mmnet/r_oracle/build_network.R --node-only`; needs **`Rscript` + sf/sfnetworks/tidygraph/dplyr**
   on PATH). Python nodes the waterway (50 m rounding) and **connects everything once**
   (`mmnet.assemble.connect_multimodal`). If `Rscript`/the R stack is missing, the build fails at
   Stage 03 — report that plainly; it is an environment problem, not a profile problem.
2. **`run_pipeline` returns the canonical Stage-03 network** → `output/03_network__{nodes,edges}.gpkg`
   + `reports/03_network.md`. Stage-04 (`join_components.max_dist > 0`) writes a SEPARATE
   `output/04_network_joined__*` — 03 stays canonical.
3. **Outputs are regenerable, not source.** `output/` and `reports/` are gitignored; never commit them.
4. **A build is not done until the connectivity proof passes.** Reproduce the region's proof (for the
   Alaska example, `examples/alaska/verify_north_slope.py`: the North Slope must be in the giant,
   waterway 100 %, road/ice ≥ 95 %, barge transfers present). A green pipeline with a failed proof is a
   FAILED build.

## Where the canonical values live

- `mmnet/pipeline.py::run_pipeline(profile_path)` — the entry point (sets `MMNET_PROFILE`/`MMNET_PROJECT`;
  legacy `NETWEAVE_*` still accepted).
- `mmnet/inspect.py` — `connectivity_report`, `mode_contribution`, `write_network_report`.
- `mmnet/build.py::node_layers_via_r`, `mmnet/r_oracle/CONTRACT.md` — the R build + file contract.
- `examples/alaska/verify_north_slope.py` — the worked example's proof gate (a template for your region).

## Procedure

1. **Check prerequisites.** `python -c "import mmnet"` imports; `Rscript --version` works and
   sf/sfnetworks/tidygraph/dplyr are installed. Confirm the profile validates
   (`define-network-profile` step 5).
2. **Run the build:**
   ```
   python -c "import mmnet; net = mmnet.run_pipeline('profile.yaml'); print(net.summary())"
   ```
   Outputs land next to the profile (`output/`, `reports/`) unless `MMNET_PROJECT` overrides.
3. **Read connectivity.** Inspect the printed `connectivity_report` headline + `reports/03_network.md`:
   component count, giant %, per-mode reachability, fuel-hub reachability, and (if an Air mode exists)
   `mode_contribution("Air")`. Sanity-check against expectations.
4. **Run the proof gate** for the region (e.g. `python examples/alaska/verify_north_slope.py`). It must
   print PASS.
5. **If the proof FAILS,** decide which case it is and surface the evidence — do NOT silently loosen a
   cap to force a pass:
   - a bad/incomplete profile edit (missing layer, wrong `edge_label`, missing connection rule) → fix
     the profile (`define-network-profile`); or
   - a tolerance genuinely too tight for the geography (a real gap) → report the gap distance and
     propose a justified `max_dist`/rule change, then re-run.
6. **Report** the final numbers (nodes/edges/components/giant %/hubs reachable) + the proof result.

## What NOT to do

- Do NOT commit `output/` or `reports/` (regenerable, gitignored).
- Do NOT call a build "done" without the connectivity proof passing.
- Do NOT loosen a `max_dist`/threshold just to make the proof pass — justify every change with the
  measured gap.
- Do NOT hand-edit the built GeoPackages; change the `profile.yaml` and rebuild.

## Related

- `define-network-profile` — author/extend the profile that this build consumes.
- `mmnet/r_oracle/CONTRACT.md` — the R↔Python file contract (WORKDIR, params/registry, node-only mode).
- `examples/alaska/` — a full worked profile + proof to model your region on.
