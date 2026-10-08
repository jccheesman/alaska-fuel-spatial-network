#!/usr/bin/env python3
"""Stage 07 — publish the clean facility table and prove the output contract.

Writes outputs/00_inventory_qc/<release>/
    facilities_clean.csv   the table both repositories read (schema columns + derived columns)
    qc_report.md           counts, corrections applied, checks

Publish checks (any failure -> exit 1; never loosen one to pass — see docs/INVENTORY_QC_PLAN.md):
  1. row reconciliation: release rows == clean rows + excluded rows, every exclusion has a reason
  2. every applied correction carries a reviewer and a date
  3. only schema + derived columns in the output; no contact-field name anywhere
  4. regression fixtures stay fixed (known errors from the 2026-10 audit)
  5. determinism: a second run reproduces facilities_clean.csv byte-for-byte

Run:  python workflows/00_inventory_qc/07_publish.py [--release 2025]
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from _qc import DERIVED, OUT, RELEASES, corrections, latest_release, read_csv, release_manifest, schema, write_csv

CONTACT_WORDS = ("representative", "phone", "email", "landowner", "facilityowner", "operator", "evaluator", "_user")

# Regression fixtures: (description, predicate over the clean table). Each is a confirmed error
# from the 2026-10 audit that an approved correction fixes; the check fails if it reappears.
FIXTURES = [
    ("Bethel record f000283 is not above 66°N",
     lambda d: not ((d.community_name == "Bethel") & (d.latitude.astype(float) > 66)).any()),
    ("no Unalaska-labelled record sits on Norton Sound (lat > 60)",
     lambda d: not ((d.community_name == "Unalaska") & (d.latitude.astype(float) > 60)).any()),
    ("no Unalakleet-labelled record sits in the Aleutians (lat < 60)",
     lambda d: not ((d.community_name == "Unalakleet") & (d.latitude.astype(float) < 60)).any()),
    ("no Kodiak-labelled record is in the open Pacific (lat < 56)",
     lambda d: not ((d.community_name == "Kodiak") & (d.latitude.astype(float) < 56)).any()),
    ("no Coldfoot-labelled record is in Yukon, Canada (lon > -141)",
     lambda d: not ((d.community_name == "Coldfoot") & (d.longitude.astype(float) > -141)).any()),
    ("spelling variants resolved (no 'Saint Marys', 'Clarks Point', 'Dutch Harbor' labels)",
     lambda d: not d.community_name.isin(["Saint Marys", "Clarks Point", "Dutch Harbor", "Saint Paul Island", "Saint George Island"]).any()),
]


def publish(label: str) -> tuple[Path, list[tuple[str, bool, str]]]:
    out = OUT / label
    rel = read_csv(RELEASES / label / release_manifest(label)["snapshot_csv"])
    fac = read_csv(out / "facilities_normalised.csv")
    excl = read_csv(out / "excluded.csv")
    log = read_csv(out / "corrections_log.csv")
    # km from the record to its own community's boundary (05_boundary_check): 0-ish = inside,
    # blank = untested (no label / no boundary). The hub builder's remote-site rule reads it.
    # `located_in_place` = the city/CDP polygon the point physically sits in; `community_relation`
    # = inside / adjacent / remote / elsewhere / untested (see 05). The label is never changed.
    bd = out / "boundary_distance.csv"
    D = read_csv(bd).set_index("record_id") if bd.exists() else pd.DataFrame(columns=["own_boundary_km", "located_in_place", "community_relation"])
    fac["community_distance_km"] = fac["record_id"].map(D["own_boundary_km"])
    fac["located_in_place"] = fac["record_id"].map(D["located_in_place"])
    fac["community_relation"] = fac["record_id"].map(D["community_relation"]).fillna("untested")
    fac["qc_release"] = label
    allowed = list(schema()["name"]) + DERIVED
    fac = fac[[c for c in allowed if c in fac.columns]]
    checks: list[tuple[str, bool, str]] = []

    ok = len(rel) == len(fac) + len(excl)
    checks.append(("row reconciliation", ok, f"{len(rel)} release = {len(fac)} clean + {len(excl)} excluded"))
    ok = excl.empty or excl["exclusion_reason"].notna().all()
    checks.append(("every exclusion has a reason", ok, f"{len(excl)} excluded"))
    applied = log[log["outcome"] == "applied"] if len(log) else log
    ok = applied.empty or (applied["reviewer"].notna() & applied["reviewed_on"].notna()).all()
    checks.append(("every applied correction has reviewer + date", ok, f"{len(applied)} applied"))
    extra = [c for c in fac.columns if c not in allowed]
    contact = [c for c in fac.columns if any(w in c.lower() for w in CONTACT_WORDS)]
    checks.append(("only schema + derived columns; no contact columns", not extra and not contact, f"extra={extra} contact={contact}"))
    located = fac.dropna(subset=["latitude", "longitude"])
    for desc, pred in FIXTURES:
        try:
            ok = bool(pred(located))
        except Exception as e:  # noqa: BLE001
            ok = False
            desc += f" (error: {e})"
        checks.append((f"fixture: {desc}", ok, ""))
    pending = int((corrections()["status"] == "pending").sum())

    clean = out / "facilities_clean.csv"
    sha = write_csv(fac, clean)
    # determinism: write again and compare
    sha2 = write_csv(fac, out / "_determinism_probe.csv")
    (out / "_determinism_probe.csv").unlink()
    checks.append(("deterministic output", sha == sha2, sha[:12]))

    man = release_manifest(label)
    lines = [f"# Inventory QC report — release {label}", "",
             f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} by workflows/00_inventory_qc/07_publish.py", "",
             f"- raw release: `{man['raw_file']}` sha256 `{man['raw_sha256']}` ({man['rows']} rows, {man['rows_with_coordinates']} located)",
             f"- clean table: `facilities_clean.csv` sha256 `{sha}` ({len(fac)} rows, {len(fac.dropna(subset=['latitude','longitude']))} located)",
             f"- excluded: {len(excl)} (see `excluded.csv`)",
             f"- corrections: {len(applied)} applied · {pending} pending · "
             f"{int((log['outcome']=='rejected').sum()) if len(log) else 0} rejected · "
             f"{int(log['outcome'].str.startswith('skipped').sum()) if len(log) else 0} skipped",
             f"- community keys: {fac['community_key'].nunique()} · unlabelled records: {int(fac['community_name'].isna().sum())}",
             "", "## Checks", "", "| check | result | detail |", "|---|---|---|"]
    for name, ok, detail in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")
    if len(applied):
        lines += ["", "## Corrections applied", "", "| record_id | field | old | new | reviewer | date |", "|---|---|---|---|---|---|"]
        for r in applied.itertuples():
            lines.append(f"| `{r.record_id}` | {r.field} | {r.old_value} | {r.new_value} | {r.reviewer} | {r.reviewed_on} |")
    (out / "qc_report.md").write_text("\n".join(lines) + "\n")
    return clean, checks


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--release", default=None)
    a = ap.parse_args(argv)
    label = a.release or latest_release()
    clean, checks = publish(label)
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    failed = [c for c in checks if not c[1]]
    print(f"{'PUBLISHED' if not failed else 'NOT PUBLISHED (checks failed)'}: {clean.relative_to(OUT.parent.parent)}")
    if failed:
        clean.unlink(missing_ok=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
