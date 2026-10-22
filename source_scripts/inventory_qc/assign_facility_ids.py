#!/usr/bin/env python3
"""Stage 03b — assign the stable facility_id every located record carries into both repositories.

facility_id is the number the harness keys its facility tables on and that its element registry
fingerprints (with the coordinates) to mint every public facility id, so for a given record it
must never move. It is the AEA ASTFacilityID where the release carries one, else a synthetic id
above the largest AEA id, minted ONCE per record and written down.

The written record is the LEDGER inputs/inventory_qc/facility_ids.csv
(record_id, facility_id, id_source, minted_from, minted_on, note): append-only, owner data like
corrections.csv. It was seeded 2026-10-31 from the retired harness rule (2022 release: located
rows keep their AEA id, the 681 without one are numbered 1263..1943 in file order), so no
existing id — and therefore no public id — changed when the rule moved here.

Rules (owner decision 2026-10-31, docs/INVENTORY_QC_PLAN.md decision 16):
  - the ledger wins: a record in the ledger keeps its ledger id even if its AEA id changed
    upstream (the change is reported, never applied silently);
  - only located records (latitude + longitude) carry an id; unlocated rows publish blank;
  - this stage never writes the ledger on its own. A located record absent from the ledger is a
    MISSING id and the stage fails naming it; `--mint` appends the missing rows (AEA id where
    present, else the next free synthetic id, in source_row order) and is the deliberate owner
    action, like recording a correction;
  - ids are unique across the release; a collision (an AEA id landing on a synthetic one) fails
    the stage for the owner to resolve — it is never renumbered by code.

Writes outputs/00_inventory_qc/<release>/facility_ids_assigned.csv (every record: record_id,
facility_id, id_source, aea_id_differs) — the publish step carries facility_id into the clean
table and checks it against the ledger.

Run:  python workflows/00_inventory_qc/03b_assign_facility_ids.py [--release 2025] [--mint]
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

import numpy as np
import pandas as pd

from .core import OUT, QC, latest_release, read_csv, write_csv

LEDGER = QC / "facility_ids.csv"
LEDGER_COLUMNS = ["record_id", "facility_id", "id_source", "minted_from", "minted_on", "note"]


def ledger() -> pd.DataFrame:
    if not LEDGER.exists():
        return pd.DataFrame(columns=LEDGER_COLUMNS)
    led = pd.read_csv(LEDGER, dtype=str, keep_default_na=False)
    missing = [c for c in LEDGER_COLUMNS if c not in led.columns]
    if missing:
        raise SystemExit(f"{LEDGER.name} is missing columns {missing}")
    led["facility_id"] = pd.to_numeric(led["facility_id"], errors="raise").astype(int)
    if led["record_id"].duplicated().any():
        dup = sorted(led.loc[led["record_id"].duplicated(), "record_id"])
        raise SystemExit(f"{LEDGER.name}: a record is listed twice {dup[:5]} — the ledger is append-only, one row per record")
    if led["facility_id"].duplicated().any():
        dup = sorted(led.loc[led["facility_id"].duplicated(), "facility_id"])
        raise SystemExit(f"{LEDGER.name}: a facility_id is used twice {dup[:5]}")
    return led


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def assign(label: str, mint: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """(assignment table for every record, ledger rows appended, problems). `problems` is empty
    when every located record has a unique id; with mint=False a missing id is a problem."""
    fac = read_csv(OUT / label / "facilities_normalised.csv")
    led = ledger()
    by_record = dict(zip(led["record_id"], led["facility_id"]))
    located = fac["latitude"].notna() & fac["longitude"].notna()
    ast = _num(fac["ast_facility_id"])
    rows = []
    walk = fac.assign(aea=ast, row=_num(fac["source_row"]), loc=located).sort_values("row")
    for r in walk.itertuples():
        if not r.loc:
            rows.append((r.record_id, np.nan, "unlocated", ""))
        elif r.record_id in by_record:
            fid = by_record[r.record_id]
            differs = "true" if (pd.notna(r.aea) and int(r.aea) != fid) else ""
            rows.append((r.record_id, fid, "ledger", differs))
        else:
            rows.append((r.record_id, np.nan, "missing", ""))
    A = pd.DataFrame(rows, columns=["record_id", "facility_id", "id_source", "aea_id_differs"])
    A = A.set_index("record_id").loc[fac["record_id"]].reset_index()      # release order

    problems: list[str] = []
    new_rows = pd.DataFrame(columns=LEDGER_COLUMNS)
    missing = A[A["id_source"] == "missing"]
    if len(missing):
        if not mint:
            problems.append(f"{len(missing)} located record(s) have no facility_id in {LEDGER.name} "
                            f"(first: {missing['record_id'].iloc[0]}); run with --mint to append them")
        else:
            taken = set(led["facility_id"].tolist()) | set(int(v) for v in ast.dropna())
            nxt = (max(taken) if taken else 0) + 1
            minted = []
            today = date.today().isoformat()
            astm = dict(zip(fac["record_id"], ast))
            for rid in missing["record_id"]:
                a = astm.get(rid)
                if pd.notna(a) and int(a) not in set(led["facility_id"].tolist()):
                    fid, src, note = int(a), "aea", f"AEA ASTFacilityID of the {label} release"
                else:
                    fid, src, note = nxt, "synthetic", f"no AEA id in the {label} release; next free id"
                    nxt += 1
                minted.append((rid, fid, src, label, today, note))
                A.loc[A["record_id"] == rid, ["facility_id", "id_source"]] = [fid, src]
            new_rows = pd.DataFrame(minted, columns=LEDGER_COLUMNS)
    ids = A.loc[A["facility_id"].notna(), "facility_id"].astype(int)
    if ids.duplicated().any():
        dup = sorted(ids[ids.duplicated()].unique())
        problems.append(f"facility_id used by two located records: {dup[:5]} — resolve in {LEDGER.name}, never by renumbering")
    synthetic_owner = {fid: rid for rid, fid, src in zip(led["record_id"], led["facility_id"], led["id_source"])
                       if src == "synthetic"}
    clash = sorted({int(a) for rid, a, loc in zip(fac["record_id"], ast, located)
                    if loc and pd.notna(a) and int(a) in synthetic_owner and synthetic_owner[int(a)] != rid})
    if clash:
        problems.append(f"an AEA id now collides with a synthetic ledger id: {clash[:5]} — owner decision needed")
    A["facility_id"] = A["facility_id"].map(lambda v: "" if pd.isna(v) else str(int(v)))
    return A, new_rows, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--release", default=None)
    ap.add_argument("--mint", action="store_true",
                    help=f"append located records that have no id to {LEDGER.relative_to(QC.parent.parent)} (owner action)")
    a = ap.parse_args(argv)
    label = a.release or latest_release()
    A, new_rows, problems = assign(label, mint=a.mint)
    if len(new_rows):
        led = ledger()
        out = pd.concat([led, new_rows], ignore_index=True)
        out.to_csv(LEDGER, index=False, lineterminator="\n")
        print(f"minted {len(new_rows)} id(s) into {LEDGER.name}: "
              f"{int((new_rows['id_source'] == 'aea').sum())} AEA, {int((new_rows['id_source'] == 'synthetic').sum())} synthetic")
    write_csv(A, OUT / label / "facility_ids_assigned.csv")
    n_loc = int((A["facility_id"] != "").sum())
    n_diff = int((A["aea_id_differs"] == "true").sum())
    print(f"release {label}: {n_loc} located records with a facility_id, "
          f"{int((A['id_source'] == 'unlocated').sum())} unlocated (blank), "
          f"{n_diff} whose AEA id differs from the ledger (ledger kept)")
    for p in problems:
        print(f"  [FAIL] {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
