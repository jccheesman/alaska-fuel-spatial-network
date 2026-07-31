# -*- coding: utf-8 -*-
"""validate_friction_stack.py — orchestrate the friction-surface QA chain.

The three friction QA entry points each run standalone and each speaks only
its own exit code. This runs them in dependency order (inputs before
outputs), and — the part no single script does — translates each failure
into a probable cause and the concrete fix (which upstream script or skill
owns it). It is the "I changed something, now rebuild and tell me what
broke" step every other friction skill hands off to.

Chain (each step gates the next unless --keep-going):

  1. check_grid_exports   — inputs sit on the canonical full-AK 28001x16567
                            grid (cheap, metadata only)
  2. friction_preflight   — every input the build will open matches the LULC
                            canonical grid + value ranges (fail-fast)
  3. [--rebuild only]     — run_friction_pipeline: build surfaces, compute
                            edges, write DuckDB  (MUTATES fuel_network.duckdb)
  4. qa_friction_stack    — the 14-file output contract, barge ice-gating
                            direction, overland value floor

Default is READ-ONLY validation (steps 1, 2, 4). Pass --rebuild to insert
step 3, which rebuilds the stack and writes the graph.

Usage (from the repo root):
    python .claude/skills/run-friction-pipeline/scripts/validate_friction_stack.py
    python .claude/skills/run-friction-pipeline/scripts/validate_friction_stack.py --rebuild
    python .claude/skills/run-friction-pipeline/scripts/validate_friction_stack.py \
        --inputs-dir path/to/inputs --output-dir path/to/friction_stack --keep-going

Exit 0 = every gating step passed; nonzero = at least one gating step
failed (see the interpretation printed under it).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]

# Interpretation per (step, exit code). "cause" and "fix" are printed only
# on failure — this is the domain knowledge that turns a bare nonzero exit
# into an action. Keyed by exit code where a step distinguishes them.
INTERP = {
    "grid": {
        2: (
            "One or more input rasters are NOT on the canonical full-AK grid "
            "(EPSG:3338, 28001x16567, origin -2130150), or a band is all-NoData.",
            "Re-pin the offending layer to the grid: GEE layers must export on "
            "the canonical crsTransform; sea_ice via pad_sea_ice_to_grid.py; "
            "river_ice via pad_river_ice_to_grid.py; permafrost via "
            "align_permafrost.py. For an arbitrary new raster use the "
            "align-to-ak-stack skill. (See memory ak_stack_reference_grid.)",
        ),
        1: (
            "No GeoTIFFs found in the inputs dir.",
            "Check --inputs-dir / the RASTER_DIR env var points at the "
            "preprocessed AK_Stack_150m inputs.",
        ),
    },
    "preflight": {
        1: (
            "An input layer failed fail-fast validation: missing file, CRS / "
            "resolution / origin / shape off the LULC canonical grid, or values "
            "out of range (LULC not 0..8, slope not 0..90, ice not 0..100).",
            "Grid drift -> snap upstream (align_permafrost / arcpy river_ice "
            "Step 7 / GEE crsTransform), then align-to-ak-stack. Out-of-range "
            "values -> wrong source or mis-scaled export; note the known "
            "river-ice winter zero-pocket data bug (memory "
            "river_ice_winter_zero_pockets) is upstream in the ArcGIS pipeline, "
            "not the stack.",
        ),
    },
    "rebuild": {
        None: (
            "The build/edge/DuckDB pipeline raised (surface build, edge "
            "computation, or graph write).",
            "Read the traceback above. A PreflightError here means step 2 "
            "should have caught it — rerun validation without --rebuild to "
            "isolate. A write error against fuel_network.duckdb usually means "
            "the DB is open elsewhere.",
        ),
    },
    "qa": {
        1: (
            "The built stack failed a hard QA check: the 14-file set / profile "
            "(overland.tif + road_base.tif + barge_01..12.tif on the canonical "
            "profile), barge July>January valid-pixel count (ice-gating "
            "direction), or the overland value floor (min valid >= "
            "min(SLOPE_FRICTION)).",
            "File-set/profile: build incomplete or FRICTION_DIR wrong, or a "
            "stray old overland_MM.tif — clean and rebuild. Ice-gating "
            "inverted: a swapped month or flipped sea/river-ice threshold "
            "direction. Value floor: a friction multiplier < 1.0 slipped into "
            "friction_config.py (multipliers must be >= 1.0) or a NoData "
            "sentinel leaked into the product -> assign-friction-values skill.",
        ),
        2: (
            "The friction output directory does not exist.",
            "Run with --rebuild to build it, or point --output-dir / the "
            "FRICTION_DIR env var at the existing friction_stack directory.",
        ),
    },
}


def run_step(label: str, key: str, cmd: list[str], env: dict | None = None) -> int:
    """Run one chain step as a subprocess; print an interpretation on failure."""
    print(f"\n{'=' * 68}\n▶ {label}\n  $ {' '.join(cmd)}\n{'=' * 68}")
    proc = subprocess.run(cmd, cwd=REPO_ROOT, env=env)
    code = proc.returncode
    if code == 0:
        print(f"✔ {label}: PASS")
        return 0
    cause, fix = INTERP[key].get(code) or INTERP[key].get(
        None, ("Unrecognized failure.", "Inspect the output above.")
    )
    print(f"✗ {label}: FAIL (exit {code})")
    print(f"  Likely cause: {cause}")
    print(f"  Fix:          {fix}")
    return code


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inputs-dir", default=None,
                    help="Preprocessed raster inputs (default: RASTER_DIR env / package default).")
    ap.add_argument("--output-dir", default=None,
                    help="Friction stack dir (default: FRICTION_DIR env / package default).")
    ap.add_argument("--rebuild", action="store_true",
                    help="Insert the build+edge+DuckDB pipeline (MUTATES fuel_network.duckdb).")
    ap.add_argument("--keep-going", action="store_true",
                    help="Run every step even after a failure (default: stop at first).")
    args = ap.parse_args()

    py = sys.executable
    env = os.environ.copy()
    if args.output_dir:
        env["FRICTION_DIR"] = str(Path(args.output_dir).resolve())

    grid_cmd = [py, "friction_surface/check_grid_exports.py"]
    preflight_cmd = [py, "-m", "friction_surface.friction_preflight"]
    if args.inputs_dir:
        resolved = str(Path(args.inputs_dir).resolve())
        grid_cmd += ["--inputs-dir", resolved]
        preflight_cmd.append(resolved)

    steps: list[tuple[str, str, list[str]]] = [
        ("Step 1/4  grid conformance (check_grid_exports)", "grid", grid_cmd),
        ("Step 2/4  input preflight (friction_preflight)", "preflight", preflight_cmd),
    ]
    if args.rebuild:
        rebuild_cmd = [py, "-m", "friction_surface.run_friction_pipeline"]
        if args.inputs_dir:
            rebuild_cmd += ["--input-dir", str(Path(args.inputs_dir).resolve())]
        if args.output_dir:
            rebuild_cmd += ["--output-dir", str(Path(args.output_dir).resolve())]
        steps.append(("Step 3/4  rebuild stack + edges + DuckDB (run_friction_pipeline)",
                      "rebuild", rebuild_cmd))
    steps.append(("Step 4/4  output QA (qa_friction_stack)", "qa",
                  [py, "-m", "friction_surface.qa.qa_friction_stack"]))

    failures = []
    for label, key, cmd in steps:
        code = run_step(label, key, cmd, env=env)
        if code != 0:
            failures.append(label)
            if not args.keep_going:
                print(f"\nStopping at first failure (use --keep-going to run the rest).")
                break

    print(f"\n{'=' * 68}")
    if failures:
        print(f"VALIDATION FAILED: {len(failures)} step(s) — {'; '.join(failures)}")
    else:
        mode = "rebuild + validate" if args.rebuild else "validate-only"
        print(f"VALIDATION PASSED ({mode}): friction stack is consistent.")
    print("=" * 68)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
