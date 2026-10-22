#!/usr/bin/env python3
"""Stage 03 — normalise community names and delivery methods.

Runs AFTER corrections (stage 02) so an alias can never move a correction's target.

- community_key: canonical form of community_name (upper, punctuation stripped, SAINT->ST),
  then inputs/inventory_qc/aliases.csv maps known variants to one canonical key
  (e.g. DUTCH HARBOR -> UNALASKA). community_name itself is left as corrected.
- delivery_barge / delivery_plane / delivery_road: parsed from delivery_method
  ("Plane or Barge" -> plane+barge).

Writes outputs/00_inventory_qc/<release>/facilities_normalised.csv and
name_report.csv (labels with no key, and keys that several raw spellings collapse into —
candidates for a new alias or a correction). Never fails on a new name: it reports.

Run:  python workflows/00_inventory_qc/03_normalise.py [--release 2025]
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from _qc import OUT, aliases, canon, latest_release, read_csv, write_csv

MODES = {"barge": "Barge", "plane": "Plane", "road": "Road"}


def normalise(label: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    fac = read_csv(OUT / label / "facilities_corrected.csv")
    al = aliases()
    amap = {canon(r.variant): canon(r.canonical) for r in al.itertuples()}
    key = fac["community_name"].map(canon)
    fac["community_key"] = key.map(lambda k: amap.get(k, k) if isinstance(k, str) else np.nan)
    dm = fac["delivery_method"].fillna("").astype(str)
    for col, word in MODES.items():
        fac[f"delivery_{col}"] = dm.str.contains(rf"\b{word}\b", regex=True).map({True: "true", False: "false"})
        fac.loc[dm == "", f"delivery_{col}"] = np.nan

    # name report: spellings per key (after aliases) and unlabelled count
    rep = (fac.dropna(subset=["community_key"]).groupby("community_key")["community_name"]
           .agg(lambda s: " | ".join(sorted(set(s)))).reset_index())
    rep["n_spellings"] = rep["community_name"].str.count(r" \| ") + 1
    rep = rep[rep["n_spellings"] > 1].rename(columns={"community_name": "spellings"})
    rep["note"] = "several raw spellings collapse into this key: add an alias or a correction"
    unl = int(fac["community_name"].isna().sum())
    rep = pd.concat([rep, pd.DataFrame([dict(community_key="(blank)", spellings="", n_spellings=unl,
                                             note="records with no community label (kept; boundary check cannot test them)")])],
                    ignore_index=True)
    return fac, rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--release", default=None)
    a = ap.parse_args(argv)
    label = a.release or latest_release()
    fac, rep = normalise(label)
    write_csv(fac, OUT / label / "facilities_normalised.csv")
    write_csv(rep, OUT / label / "name_report.csv")
    print(f"release {label}: {fac['community_key'].nunique()} community keys, "
          f"{int(fac['community_name'].isna().sum())} unlabelled, "
          f"{int((rep['n_spellings'] > 1).sum()) - 1 if len(rep) else 0} keys with several spellings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
