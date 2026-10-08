#!/usr/bin/env python3
"""Turn a returned review queue (review_queue.xlsx / .csv with the decision columns filled) into
rows of inputs/inventory_qc/corrections.csv and remote_sites.csv — the scripted half of the
record-facility-corrections skill. It records decisions; it never makes one.

    # dry run: show the rows it would write and every question it would ask
    python .claude/skills/record-facility-corrections/scripts/record_corrections.py REVIEW.xlsx

    # append the rows (then run validate-facility-inventory --publish)
    python .claude/skills/record-facility-corrections/scripts/record_corrections.py REVIEW.xlsx --write

Decision vocabulary (column `decision`, case-insensitive):
    approve                 the flag's `suggestion` ("field -> value") becomes the correction
    approve with my value   `your_value` is the new value: a label for a label flag, "lat, lon" (decimal
                            degrees, west negative) for a coordinate flag, or the word `exclude`
    exclude                 field=exclude with `notes` as the reason
    reject                  a `(no change)` row with status rejected
    remote site             a remote_sites.csv row (keep as labelled; suppresses the boundary flag)
    ask publisher | skip    a pending row (the queue keeps showing it)
Blank decision = not decided; the row is skipped. Every written row needs reviewed_by + reviewed_on
(not in the future); old_value is read from the base release snapshot. Anything ambiguous (a
reject with a value, a coordinate out of range, a value the field cannot take) is a QUESTION and
nothing is written for that record until the owner answers.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
WF = ROOT / "workflows" / "00_inventory_qc"
spec = importlib.util.spec_from_file_location("_qc", WF / "_qc.py")
qc = importlib.util.module_from_spec(spec); spec.loader.exec_module(qc)

CORR_COLS = ["record_id", "facility_pid_2022", "source_row_2022", "community_name", "field", "old_value", "new_value",
             "reason", "evidence", "reviewer", "reviewed_on", "status", "decided_in", "present_in_2025"]
LABEL_DETECTORS = {"boundary_mismatch", "boundary_outside", "spelling_variants", "shared_point_labels"}
COORD_DETECTORS = {"one_digit_typo", "map_point_disagrees", "shared_farm_id"}


def _norm(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def _coords(v: str):
    m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*[,; ]\s*(-?\d+(?:\.\d+)?)\s*$", v)
    if not m:
        return None
    lat, lon = float(m.group(1)), float(m.group(2))
    if not (51 <= lat <= 72 and -180 <= lon <= -129):
        return None
    return f"{lat:.6f}".rstrip("0").rstrip("."), f"{lon:.6f}".rstrip("0").rstrip(".")


def plan(review: pd.DataFrame, label: str, decided_in: str):
    rel = qc.read_release(label).set_index("record_id")
    rows, remote, questions = [], [], []
    for r in review.itertuples(index=False):
        d = _norm(getattr(r, "decision", "")).lower()
        if not d:
            continue
        rid = r.record_id
        who, when = _norm(getattr(r, "reviewed_by", "")), _norm(getattr(r, "reviewed_on", ""))
        notes, val = _norm(getattr(r, "notes", "")), _norm(getattr(r, "your_value", ""))
        det, sugg = _norm(getattr(r, "detector", "")), _norm(getattr(r, "suggestion", ""))
        if rid not in rel.index:
            questions.append((rid, f"record not in release {label}")); continue
        if not who or not when:
            questions.append((rid, "reviewed_by / reviewed_on missing (row stays undecided)")); continue
        try:
            if dt.date.fromisoformat(when[:10]) > dt.date.today():
                questions.append((rid, f"reviewed_on {when} is in the future")); continue
        except ValueError:
            questions.append((rid, f"reviewed_on {when!r} is not an ISO date")); continue
        rec = rel.loc[rid]
        base = dict(record_id=rid, facility_pid_2022="", source_row_2022="", community_name=rec.get("community_name", ""),
                    reason=d, evidence=notes, reviewer=who, reviewed_on=when, decided_in=decided_in, present_in_2025="True")

        def add(field, old, new, status):
            rows.append({**base, "field": field, "old_value": old, "new_value": new, "status": status})

        if d == "reject":
            if val:
                questions.append((rid, f"reject but your_value={val!r} given — which is it?")); continue
            add("(no change)", "", "", "rejected")
        elif d in ("remote site", "remote site (keep as labelled)"):
            remote.append(dict(record_id=rid, community_name=rec.get("community_name", ""),
                               reason=notes or f"owner: remote site of {rec.get('community_name', '')}", reviewer=who, reviewed_on=when))
        elif d in ("ask publisher", "skip", "skip for now"):
            field = sugg.split("->")[0].strip() if "->" in sugg else ("community_name" if det in LABEL_DETECTORS else "latitude;longitude")
            add(field, "", "", "pending")
        elif d == "exclude" or (d == "approve with my value" and val.lower() == "exclude"):
            if not notes:
                questions.append((rid, "exclude needs a reason in notes")); continue
            add("exclude", "", "true", "approved")
        elif d == "approve":
            if "->" not in sugg or not sugg.split("->", 1)[1].strip():
                questions.append((rid, "approve but the flag carries no suggestion — use 'approve with my value'")); continue
            field, new = (x.strip() for x in sugg.split("->", 1))
            for f_, n_ in zip(field.split(";"), new.split(";")):
                add(f_, str(rec.get(f_, "")), n_, "approved")
        elif d == "approve with my value":
            if not val:
                questions.append((rid, "approve with my value but your_value is blank")); continue
            c = _coords(val)
            if c:
                add("latitude", str(rec.get("latitude", "")), c[0], "approved")
                add("longitude", str(rec.get("longitude", "")), c[1], "approved")
            elif det in COORD_DETECTORS and not c:
                questions.append((rid, f"coordinate flag but your_value {val!r} is not 'lat, lon' in decimal degrees (west negative, 51-72 N)")); continue
            else:
                add("community_name", str(rec.get("community_name", "")), val, "approved")
        else:
            questions.append((rid, f"unknown decision {d!r}")); continue
    return pd.DataFrame(rows, columns=CORR_COLS), pd.DataFrame(remote, columns=["record_id", "community_name", "reason", "reviewer", "reviewed_on"]), questions


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("review", help="returned review_queue .xlsx or .csv")
    ap.add_argument("--release", default=None)
    ap.add_argument("--write", action="store_true", help="append to corrections.csv / remote_sites.csv (default: dry run)")
    a = ap.parse_args(argv)
    p = Path(a.review)
    review = pd.read_excel(p, dtype=str) if p.suffix.lower() in (".xlsx", ".xlsm") else pd.read_csv(p, dtype=str)
    review = review.fillna("")
    label = a.release or qc.latest_release()
    corr, remote, questions = plan(review, label, f"{p.name}")
    existing = qc.corrections()
    dup = corr[corr.set_index(["record_id", "field"]).index.isin(existing.set_index(["record_id", "field"]).index) & (corr["status"] != "pending")]
    print(f"review rows: {len(review)} · decided: {int((review['decision'].str.strip() != '').sum())} · "
          f"correction rows: {len(corr)} ({corr['status'].value_counts().to_dict()}) · remote sites: {len(remote)} · questions: {len(questions)}")
    if len(dup):
        print("\nALREADY DECIDED (record_id+field exists in corrections.csv) — not written; retire the old row first if this reverses it:")
        for r in dup.itertuples():
            print(f"  {r.record_id} {r.field}")
        corr = corr.drop(dup.index)
    if questions:
        print("\nQUESTIONS for the owner (nothing written for these records):")
        for rid, q in questions:
            print(f"  {rid}: {q}")
    if len(corr):
        print("\nrows:\n" + corr[["record_id", "community_name", "field", "old_value", "new_value", "status"]].to_string(index=False))
    if not a.write:
        print("\n(dry run — add --write to append)")
        return 0 if not questions else 2
    if len(corr):
        pd.concat([existing, corr], ignore_index=True).to_csv(qc.CORRECTIONS, index=False, lineterminator="\n")
    if len(remote):
        rs = qc.QC / "remote_sites.csv"
        old = pd.read_csv(rs, dtype=str, keep_default_na=False) if rs.exists() else remote.iloc[:0]
        pd.concat([old, remote], ignore_index=True).to_csv(rs, index=False, lineterminator="\n")
    print(f"\nwrote {len(corr)} correction row(s) and {len(remote)} remote-site row(s). Next: validate-facility-inventory --publish")
    return 0 if not questions else 2


if __name__ == "__main__":
    sys.exit(main())
