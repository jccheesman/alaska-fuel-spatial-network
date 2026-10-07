#!/usr/bin/env python3
"""Orchestrator for the facility-inventory QC chain (workflow 00), with cause + fix per failure.

Runs, in order, 01 --check -> 02 apply corrections -> 03 normalise -> 04 detect ->
05 boundary check -> 06 review queue -> 07 publish, stopping at the first failing gate and
printing what it means and which config file or sibling skill owns the fix.

    # read-only: run the chain into a temp dir and compare with the committed published table
    python .claude/skills/validate-facility-inventory/scripts/validate_inventory.py

    # write: refresh outputs/00_inventory_qc/<release>/ (what run_all.sh does)
    python .claude/skills/validate-facility-inventory/scripts/validate_inventory.py --publish

    # keep going after a failure; pick a release
    python .claude/skills/validate-facility-inventory/scripts/validate_inventory.py --keep-going --release 2025

Exit 0 = every gating step passed (and, read-only, the committed facilities_clean.csv is
byte-identical to a fresh run). Any other exit is a real defect; never loosen a check to pass.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
WF = ROOT / "workflows" / "00_inventory_qc"
OUT = ROOT / "outputs" / "00_inventory_qc"
PY = sys.executable

# step -> (script, args, cause + fix shown when it fails)
STEPS = [
    ("01 ingest --check", "01_ingest.py", ["--check"],
     "A committed release snapshot no longer matches its manifest, or re-deriving it from the raw file\n"
     "   differs. Someone hand-edited inputs/raw_facility_data/<release>/ or the column map changed.\n"
     "   Fix: re-run `01_ingest.py RAW.csv --release <label>` from the pinned raw file (sha256 in SOURCE.md);\n"
     "   never edit a snapshot CSV by hand. Owning skill: ingest-facility-inventory."),
    ("02 apply corrections", "02_apply_corrections.py", [],
     "An APPROVED row in inputs/inventory_qc/corrections.csv could not be applied: the record is absent\n"
     "   from this release, or its current value no longer equals the row's old_value (upstream changed it).\n"
     "   Fix: review the row; mark it `retired` if the publisher fixed it, or update old_value/new_value\n"
     "   with evidence. Never apply a correction by editing data. Owning skill: record-facility-corrections."),
    ("03 normalise", "03_normalise.py", [],
     "aliases.csv is malformed (needs variant,canonical,...) or a stage-02 output is missing.\n"
     "   Fix: run 02 first; check inputs/inventory_qc/aliases.csv columns."),
    ("04 detect", "04_detect.py", [],
     "thresholds.csv is missing a value a detector needs, or corrections.csv has an unknown status.\n"
     "   Fix: inputs/inventory_qc/thresholds.csv (one row per threshold with a reason); statuses are\n"
     "   approved | pending | rejected | retired."),
    ("05 boundary check", "05_boundary_check.py", [],
     "The boundary zips under inputs/inventory_qc/boundaries/ are missing, unreadable, or not EPSG:3338,\n"
     "   or geopandas/pyogrio is not installed. Fix: restore the zips (sha256 in boundaries/SOURCE.md and\n"
     "   inputs/MANIFEST.md); never substitute a different boundary layer without updating both."),
    ("06 review queue", "06_review_queue.py", [],
     "A flags file from 04/05 is missing or malformed. Fix: re-run 04 and 05."),
    ("07 publish", "07_publish.py", [],
     "A publish check failed: row reconciliation (a record vanished without an exclusion reason),\n"
     "   a correction without reviewer/date, a non-schema or contact column in the output, a regression\n"
     "   fixture (a known 2026-10 error re-appeared: a correction was retired/removed or its target moved),\n"
     "   or non-deterministic output. Fix at the source — corrections.csv / column_map.csv — never by\n"
     "   editing facilities_clean.csv or relaxing a fixture. Owning skill: record-facility-corrections."),
]


def run_step(label: str, script: str, args: list[str], env: dict, keep_going: bool) -> bool:
    print(f"\n==> {label}")
    p = subprocess.run([PY, str(WF / script), *args], cwd=ROOT, env=env, text=True, capture_output=True)
    out = (p.stdout + p.stderr).strip()
    if out:
        print("\n".join("   " + line for line in out.splitlines()[-25:]))
    if p.returncode != 0:
        cause = next(c for l, s, a, c in STEPS if l == label)
        print(f"\nFAILED ({label}, exit {p.returncode}). Probable cause + fix:\n   {cause}")
        return False
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--publish", action="store_true", help="write outputs/00_inventory_qc/ (default: temp dir, read-only)")
    ap.add_argument("--keep-going", action="store_true")
    ap.add_argument("--release", default=None)
    a = ap.parse_args(argv)
    sys.path.insert(0, str(WF))
    import importlib.util
    spec = importlib.util.spec_from_file_location("_qc", WF / "_qc.py")
    qc = importlib.util.module_from_spec(spec); spec.loader.exec_module(qc)
    label = a.release or qc.latest_release()

    tmp = None
    env = dict(os.environ)
    if not a.publish:
        tmp = Path(tempfile.mkdtemp(prefix="inventory_qc_"))
        env["INVENTORY_QC_OUT"] = str(tmp)
    rel_args = ["--release", label]
    ok_all = True
    for step, script, args, _ in STEPS:
        ok = run_step(step, script, args + ([] if script == "01_ingest.py" else rel_args), env, a.keep_going)
        ok_all &= ok
        if not ok and not a.keep_going:
            break

    if ok_all and not a.publish:
        fresh = tmp / label / "facilities_clean.csv"
        committed = OUT / label / "facilities_clean.csv"
        if committed.exists():
            same = hashlib.sha256(fresh.read_bytes()).hexdigest() == hashlib.sha256(committed.read_bytes()).hexdigest()
            print(f"\n==> committed facilities_clean.csv vs fresh run: {'identical' if same else 'DIFFERS'}")
            if not same:
                print("   The published table under outputs/00_inventory_qc/ is stale (corrections, aliases or\n"
                      "   thresholds changed since it was published). Fix: re-run with --publish and commit the\n"
                      "   refreshed outputs together with the config change.")
                ok_all = False
        else:
            print(f"\n==> no committed facilities_clean.csv for release {label} yet (first run?) — run with --publish")
    if tmp is not None:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nRESULT:", "all gating steps passed" if ok_all else "FAILED — see the first failure above")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
