#!/usr/bin/env python3
"""Stage 02 — apply the owner-approved corrections to a release snapshot.

Reads inputs/raw_facility_data/<release>/ and inputs/inventory_qc/corrections.csv.
Only rows with status=approved are applied, and only when the record's CURRENT value
still equals the row's old_value (the guard that lets an upstream fix retire a
correction instead of being applied twice). Nothing is dropped: a `field=exclude`
correction moves the record to excluded.csv with its reason.

Writes outputs/00_inventory_qc/<release>/
    facilities_corrected.csv   the snapshot with approved corrections applied
    excluded.csv               records removed by an approved exclude correction (+ reason)
    corrections_log.csv        one line per corrections.csv row: applied / skipped-<why> / pending / rejected

Exit 1 if an approved correction could not be applied (record missing, or old_value no
longer matches) — that is a real signal, not a warning: review the row, then mark it
`retired` (upstream fixed it) or update it.

Run:  python workflows/00_inventory_qc/02_apply_corrections.py [--release 2025]
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from _qc import OUT, canon, corrections, latest_release, read_release, write_csv

COORD_FIELDS = {"latitude", "longitude"}


def _close(a: str, b: str, tol: float = 1e-6) -> bool:
    try:
        return abs(float(a) - float(b)) < tol
    except (TypeError, ValueError):
        return False


def apply(label: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fac = read_release(label).set_index("record_id", drop=False)
    corr = corrections()
    log, excluded_ids, applied = [], {}, {}

    for r in corr.itertuples(index=False):
        entry = dict(record_id=r.record_id, field=r.field, old_value=r.old_value, new_value=r.new_value,
                     status=r.status, reviewer=r.reviewer, reviewed_on=r.reviewed_on, outcome="", note="")
        if r.status != "approved":
            entry["outcome"] = r.status
            log.append(entry)
            continue
        if r.record_id not in fac.index:
            entry["outcome"] = "skipped-record-absent"
            entry["note"] = "record is not in this release (deleted upstream?) — mark retired if so"
            log.append(entry)
            continue
        if r.field == "exclude":
            excluded_ids[r.record_id] = r.evidence if "evidence" in corr.columns else r.reason
            entry["outcome"] = "applied"
            log.append(entry)
            continue
        if r.field not in fac.columns:
            entry["outcome"] = "skipped-unknown-field"
            log.append(entry)
            continue
        cur = fac.at[r.record_id, r.field]
        cur_s = "" if (cur is None or (isinstance(cur, float) and np.isnan(cur))) else str(cur)
        same = (cur_s == r.old_value) or (r.field in COORD_FIELDS and _close(cur_s, r.old_value))
        if not same:
            entry["outcome"] = "skipped-old-value-mismatch"
            entry["note"] = f"current value is {cur_s!r}, correction expected {r.old_value!r} — upstream changed it; review then retire/update"
            log.append(entry)
            continue
        fac.at[r.record_id, r.field] = r.new_value
        applied.setdefault(r.record_id, []).append(r.field)
        entry["outcome"] = "applied"
        log.append(entry)

    fac["corrections_applied"] = fac.index.map(lambda i: ";".join(applied.get(i, [])) or np.nan)
    excl = fac.loc[list(excluded_ids)].copy()
    excl["exclusion_reason"] = [excluded_ids[i] for i in excl.index]
    fac = fac.drop(index=list(excluded_ids)).reset_index(drop=True)
    excl = excl.reset_index(drop=True)
    return fac, excl, pd.DataFrame(log)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--release", default=None)
    a = ap.parse_args(argv)
    label = a.release or latest_release()
    fac, excl, log = apply(label)
    out = OUT / label
    write_csv(fac, out / "facilities_corrected.csv")
    write_csv(excl, out / "excluded.csv")
    write_csv(log, out / "corrections_log.csv")
    counts = log["outcome"].value_counts().to_dict()
    print(f"release {label}: {len(fac)} records kept, {len(excl)} excluded; corrections {counts}")
    bad = log[log["outcome"].str.startswith("skipped")]
    if len(bad):
        print("\nAPPROVED CORRECTIONS NOT APPLIED:")
        for r in bad.itertuples():
            print(f"  {r.record_id} {r.field}: {r.outcome} — {r.note}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
