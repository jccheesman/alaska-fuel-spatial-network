#!/usr/bin/env python3
"""Cross-platform driver for the four-act pipeline — the Windows-friendly twin
of run_all.sh. Pure stdlib; runs each numbered workflow script in a subprocess.

The bash drivers (run_all.sh + workflows/*/run_all.sh) remain the Linux/macOS
path and CI checks their contracts; this file mirrors them step for step, and
CI's "driver parity" step asserts both report the same skipped/failed summary.

Contracts mirrored from workflows/_lib.sh:
  1. Interpreter resolution — active $VIRTUAL_ENV, then the project .venv
     (bin/python on POSIX, Scripts/python.exe on Windows), then $PYTHON or the
     current interpreter with a warning. (One wording difference: the bash
     fallback names 'python3', this one names the concrete interpreter path.)
  2. run_step — child stdout+stderr merged and buffered, known-noisy lines
     filtered (stage 02 only), the child's REAL exit status preserved, and the
     stage aborted on failure.
  3. GATE_EXIT = 3 means "documented input absent — skip this stage, not a
     bug"; the summary reports skipped vs failed separately and the driver
     exits non-zero (1) only for real failures.

Usage:
    python run_all.py                 # all four stages, in order
    python run_all.py --only 03       # one stage (prefix or full name)
    python run_all.py --profile P     # alternate profile for stage 02

The interpreter is resolved once (bash resolves per stage script, but from the
same inputs, so the result is identical).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKFLOWS = ROOT / "workflows"
GATE_EXIT = 3

# Verbatim from workflows/02_network_build/run_all.sh (grep -vE semantics:
# a match anywhere on the line drops the whole line). Keep byte-identical —
# including the unescaped dot in "warnings.warn".
FILT_02 = r"Axes3D|warnings.warn|user_version|QStandardPaths|Application path"


class StageSkip(Exception):
    """A gate fired: documented input absent, stage exits GATE_EXIT."""


class StageFail(Exception):
    """A step failed: carries the child's real exit status."""

    def __init__(self, rc: int):
        super().__init__(rc)
        self.rc = rc


def out(line: str = "") -> None:
    print(line, flush=True)


def err(line: str = "") -> None:
    print(line, file=sys.stderr, flush=True)


def resolve_python() -> str:
    """Mirror _lib.sh resolve_python, plus the Windows venv layout."""
    layouts = ("bin/python", "Scripts/python.exe")
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        for rel in layouts:
            cand = Path(venv) / rel
            if cand.is_file() and os.access(cand, os.X_OK):
                return str(cand)
    for rel in layouts:
        cand = ROOT / ".venv" / rel
        if cand.is_file() and os.access(cand, os.X_OK):
            return str(cand)
    py = os.environ.get("PYTHON") or sys.executable
    err(f"WARNING: no project venv found; falling back to '{py}'.")
    err("         Create one with: uv venv && uv sync && uv pip install -e .")
    return py


def gate(msg: str, *lines: str) -> None:
    out(f"GATE: {msg}")
    for line in lines:
        out(f"  {line}")
    raise StageSkip()


def run_step(label: str, *cmd: str, filt: str | None = None) -> None:
    """Run one pipeline step; replay its merged output; keep its exit status."""
    proc = subprocess.run(
        list(cmd), cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    text = proc.stdout.decode("utf-8", errors="replace")
    for line in text.splitlines():
        if filt and re.search(filt, line):
            continue
        out(line)
    rc = proc.returncode
    if rc < 0:  # POSIX signal death: report like bash (128 + signal)
        rc = 128 - rc
    if rc != 0:
        err()
        err(f"ERROR: {label} failed (exit {rc}): {' '.join(cmd)}")
        raise StageFail(rc)


def dir_nonempty(p: Path) -> bool:
    """Mirror `[ -d p ] && [ -n "$(ls -A p)" ]`."""
    return p.is_dir() and any(p.iterdir())


def stage_01_friction_build(py: str) -> None:
    here = WORKFLOWS / "01_friction_build"
    if not (ROOT / "inputs/friction_rasters/lulc.tif").is_file():
        gate(
            "inputs/friction_rasters/lulc.tif missing.",
            "The ~7 GB friction rasters are not committed (regenerable only).",
            "Regenerate via source_scripts/friction_surface/friction_preprocessing/ (GEE + arcpy),",
            "then re-run. See EXTERNAL_DATA.md.",
        )
    if not (ROOT / "inputs/data_for_network_build").is_dir():
        gate(
            "inputs/data_for_network_build/ not extracted.",
            f"Run: {py} tools/extract_inputs.py",
        )
    run_step("00_preflight_inputs", py, str(here / "00_preflight_inputs.py"))
    run_step("01_build_corridor_masks", py, str(here / "01_build_corridor_masks.py"))
    run_step("02_build_friction_stack", py, str(here / "02_build_friction_stack.py"))
    run_step("03_qa_friction_stack", py, str(here / "03_qa_friction_stack.py"))
    out("Done. Friction stack in outputs/01_friction_build/friction_stack/.")


def stage_02_network_build(py: str, profile: str) -> None:
    here = WORKFLOWS / "02_network_build"
    if not dir_nonempty(ROOT / "data/raw"):
        gate(
            "data/raw is empty. Populate it first:",
            f"{py} tools/extract_inputs.py   (needs inputs/network_raw.zip — see inputs/README.md)",
        )

    if not dir_nonempty(ROOT / "data/interim"):
        out("######## 0-2. prep: normalize_raw -> prep_waterway -> prep_airways ########")
        run_step("00_normalize_raw", py, str(here / "00_normalize_raw.py"), filt=FILT_02)
        run_step("01_prep_waterway", py, str(here / "01_prep_waterway.py"), filt=FILT_02)
        run_step("02_prep_airways", py, str(here / "02_prep_airways.py"), filt=FILT_02)

    out()
    out("######## 3-4. validate + build (mmnet 01->04 + reports) ########")
    run_step("04_build_network", py, str(here / "04_build_network.py"), profile, filt=FILT_02)

    out()
    out("######## 5. verify the expected connected network ########")
    run_step("05_verify_north_slope", py, str(here / "05_verify_north_slope.py"), filt=FILT_02)

    out()
    out("######## 6. QGIS projects + components + figures ########")
    joined = ROOT / "outputs/02_network_build/output/04_network_joined__nodes.gpkg"
    run_step("viz/export_qgis", py, str(here / "viz/export_qgis.py"), filt=FILT_02)
    if joined.is_file():
        run_step(
            "viz/export_qgis (joined)",
            py, str(here / "viz/export_qgis.py"), "--stem", "04_network_joined",
            filt=FILT_02,
        )
    run_step(
        "viz/export_qgis_components", py, str(here / "viz/export_qgis_components.py"),
        filt=FILT_02,
    )
    run_step("viz/plot_components", py, str(here / "viz/plot_components.py"), filt=FILT_02)
    if joined.is_file():
        run_step("viz/plot_join", py, str(here / "viz/plot_join.py"), filt=FILT_02)

    out()
    out("######## 7. export the final_network/ handoff ########")
    if os.environ.get("EXPORT_FINAL_NETWORK", "0") == "1":
        out("EXPORT_FINAL_NETWORK=1 — regenerating the network-of-record.")
        out("  Together with these zips you MUST regenerate: the EXPECTED inventory in")
        out("  workflows/03_multimodal_join/02_load_final_network.py, edge_month_weights,")
        out("  and edge_costs. See final_network/README.md.")
        run_step(
            "06_export_final_network", py, str(here / "06_export_final_network.py"),
            filt=FILT_02,
        )
    else:
        out("SKIPPED (default). Step 7 replaces the frozen network-of-record and")
        out("  invalidates every edge_id-keyed table. To run it deliberately:")
        out("    EXPORT_FINAL_NETWORK=1 bash workflows/02_network_build/run_all.sh")

    out()
    out("Done. Artifacts in outputs/02_network_build/{output,reports}.")


def stage_03_multimodal_join(py: str) -> None:
    here = WORKFLOWS / "03_multimodal_join"
    run_step("01_extract_network_handoff", py, str(here / "01_extract_network_handoff.py"))
    run_step("02_load_final_network", py, str(here / "02_load_final_network.py"))

    if not (ROOT / "outputs/01_friction_build/friction_stack/road_base.tif").is_file():
        out("GATE: friction stack missing (outputs/01_friction_build/friction_stack/).")
        out("  Stages 03-04 need workflow 01's rasters — regenerate via")
        out("  bash workflows/01_friction_build/run_all.sh (see EXTERNAL_DATA.md).")
        out("  Stopping after the ingest stage (network_nodes + network_edges written).")
        raise StageSkip()

    run_step("03_weight_network_edges", py, str(here / "03_weight_network_edges.py"))
    run_step("04_assemble_weighted_graph", py, str(here / "04_assemble_weighted_graph.py"))
    out("Done. Tables in outputs/fuel_network.duckdb.")


def stage_04_duckdb_export(py: str) -> None:
    here = WORKFLOWS / "04_duckdb_export"
    if not (ROOT / "outputs/fuel_network.duckdb").is_file():
        gate(
            "outputs/fuel_network.duckdb missing.",
            "Run workflow 03 first: bash workflows/03_multimodal_join/run_all.sh",
        )
    run_step("01_run_validation_queries", py, str(here / "01_run_validation_queries.py"))
    run_step("02_inspect_schema", py, str(here / "02_inspect_schema.py"))
    out("Done.")


STAGES = {
    "01_friction_build": lambda py, profile: stage_01_friction_build(py),
    "02_network_build": lambda py, profile: stage_02_network_build(py, profile),
    "03_multimodal_join": lambda py, profile: stage_03_multimodal_join(py),
    "04_duckdb_export": lambda py, profile: stage_04_duckdb_export(py),
}


def resolve_stage_names(only: list[str]) -> list[str]:
    """Map --only values (full names or prefixes like '01') to stage keys."""
    chosen: list[str] = []
    for token in only:
        matches = [k for k in STAGES if k == token or k.startswith(token)]
        if len(matches) != 1:
            kind = "ambiguous" if matches else "unknown"
            sys.exit(f"run_all.py: {kind} --only value '{token}' (stages: {', '.join(STAGES)})")
        if matches[0] not in chosen:
            chosen.append(matches[0])
    return [k for k in STAGES if k in chosen]  # keep pipeline order


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:  # UTF-8 + LF everywhere (Windows consoles default to cp1252/CRLF)
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
        except AttributeError:
            pass

    parser = argparse.ArgumentParser(
        description="Run the pipeline stages (cross-platform twin of run_all.sh)."
    )
    parser.add_argument(
        "--only", action="append", default=[], metavar="STAGE",
        help="run only this stage; full name or unambiguous prefix (e.g. 01); repeatable",
    )
    parser.add_argument(
        "--profile", default=str(WORKFLOWS / "02_network_build" / "profile.yaml"),
        help="profile passed to stage 02's 04_build_network.py (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    selected = resolve_stage_names(args.only) if args.only else list(STAGES)
    py = resolve_python()

    skipped: list[str] = []
    failed: list[str] = []
    for wf in selected:
        out()
        out(f"================ workflows/{wf} ================")
        try:
            STAGES[wf](py, args.profile)
            rc = 0
        except StageSkip:
            rc = GATE_EXIT
        except StageFail as exc:
            rc = exc.rc
        if rc == 0:
            pass
        elif rc == GATE_EXIT:
            out(f"[run_all] {wf} SKIPPED — missing input (gate above explains what).")
            skipped.append(wf)
        else:
            err(f"[run_all] {wf} FAILED (exit {rc}).")
            failed.append(wf)

    out()
    out("================ summary ================")
    out("skipped (missing inputs): " + (" ".join(skipped) if skipped else "none"))
    out("failed  (real errors)   : " + (" ".join(failed) if failed else "none"))

    if failed:
        err(f"run_all: FAILED — {len(failed)} stage(s) errored.")
        return 1
    out("run_all complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
