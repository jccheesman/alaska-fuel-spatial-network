"""Which inventory community labels are not DCRA community names, and what is each one?

Reads the published 2025 table (outputs/00_inventory_qc/<release>/facilities_clean.csv), the
DCRA community reference (inputs/community_reference/dcra_community_reference.csv) and
inputs/inventory_qc/aliases.csv. Writes one review row per label that is not a DCRA name, plus
one per alias whose canonical is not a DCRA name, with the evidence an owner needs to decide:
the records, the DCRA code they carry, the DCRA polygon they sit in (stage 05), the nearest DCRA
communities, the harness's current proposal (if a harness checkout is given), and a suggestion.
The decision columns are blank; nothing here changes a label.

    python diagnostics/00_inventory_qc/community_label_review.py [--release 2025]
        [--harness-review PATH/okf/catalogs/community_review.csv] [--out DIR]

Output: <out>/community_label_review.csv and .xlsx (default outputs/diagnostics/00_inventory_qc/).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

import repo_paths as rp

NOT_PLACES = {"State", "Census Area", "Non-Unified Home Rule Borough", "2nd Class Borough",
              "1st Class Borough"}   # unified city-boroughs (Anchorage, Juneau, ...) stay: they are communities

# Reviewer's reading of each label (2026-11-16): the DCRA name it most likely means and why.
# Evidence columns are computed; this is the one hand-written part, and only a suggestion.
SUGGEST = {
    "Barrow": ("Utqiagvik", "alias Barrow -> Utqiagvik",
               "City renamed Utqiagvik in 2016 (DCRA spells it without the dot). Every record carries the Utqiagvik code and sits inside the Utqiagvik boundary."),
    "Bettles Field": ("Bettles", "reverse the alias: Bettles Field -> Bettles",
                      "DCRA's community is Bettles (2nd Class City); Bettles Field is the airfield. All records carry the Bettles code. The 2026-10-05 alias chose Bettles Field (owner decision) before the DCRA list was the reference, so this reverses an owner decision and needs one."),
    "Chandalar": ("", "keep the label; no DCRA community (remote site)",
                  "FAA Chandalar Lake station. DCRA has no Chandalar; the record carries no community code and the nearest DCRA communities are far away. Keep as a named remote site."),
    "Deadhorse": ("Prudhoe Bay", "alias Deadhorse -> Prudhoe Bay",
                  "Deadhorse is the service camp of the Prudhoe Bay CDP (DCRA Place of Interest); the record sits inside the Prudhoe Bay boundary but carries no community code."),
    "Denali National Park": ("Denali Park", "alias Denali National Park -> Denali Park",
                             "NPS Denali headquarters; carries the Denali Park code. DCRA's CDP is Denali Park."),
    "Eielson Afb": ("Eielson AFB", "no change (the existing alias already gives the DCRA name)",
                    "Casing only. aliases.csv maps it to Eielson AFB, which IS a DCRA name (CDP, Place of Interest), so the community key already matches. All seven are Air Force radar, relay and range sites 68 to 247 km from the base (their median position is meaningless), kept as remote-site hubs."),
    "Fort Richardson": ("Joint Base Elmendorf-Richardson", "alias Fort Richardson -> Joint Base Elmendorf-Richardson (or -> Anchorage)",
                        "Carries the JBER code. DCRA lists Joint Base Elmendorf-Richardson as its own Place of Interest inside Anchorage; the harness review proposed Anchorage. One record, no hub."),
    "Point McKenzie": ("Point MacKenzie", "name correction Point McKenzie -> Point MacKenzie (as record 384, 2026-11-16)",
                       "Port MacKenzie; a third spelling of Point MacKenzie. The record has no latitude/longitude (map point only) and no community code, so it is not in the network today."),
    "Point Thomson": ("", "keep the label; no DCRA community",
                      "ExxonMobil Point Thomson gas field. DCRA has no such community; the record has no latitude/longitude (map point only) and no community code, so it is not in the network today."),
    "Sutton": ("Sutton-Alpine", "alias Sutton -> Sutton-Alpine",
               "Palmer Correctional Facility; carries the Sutton-Alpine code and sits inside the Sutton-Alpine CDP."),
}

DECISION_COLS = ["decision", "your_value", "notes", "reviewed_by", "reviewed_on"]


def nearest(ref: pd.DataFrame, x: float, y: float, k: int = 2) -> list[tuple[str, str, float]]:
    places = ref[(ref["is_active"] == "1") & ~ref["community_type"].isin(NOT_PLACES)]
    d = np.hypot(places["x_3338"].astype(float) - x, places["y_3338"].astype(float) - y) / 1000
    top = d.sort_values().head(k).index
    return [(places.at[i, "community_name"], places.at[i, "community_type"], round(float(d[i]), 1)) for i in top]


def build(release: str, harness_review: Path | None) -> pd.DataFrame:
    ref = pd.read_csv(rp.COMMUNITY_REFERENCE / "dcra_community_reference.csv", dtype=str, keep_default_na=False)
    by_id = ref.set_index("community_id")
    names = set(ref["community_name"])
    fac = pd.read_csv(rp.INVENTORY_QC_OUT / release / "facilities_clean.csv", dtype=str, keep_default_na=False)
    al = pd.read_csv(rp.INVENTORY_QC / "aliases.csv", dtype=str, keep_default_na=False)
    alias_of = dict(zip(al["variant"], al["canonical"]))
    hr = {}
    if harness_review and harness_review.exists():
        h = pd.read_csv(harness_review, dtype=str, keep_default_na=False)
        hr = {r.db_name: f"{r.handling} -> {r.official_name} ({r.status})" for r in h.itertuples()}
    to3338 = Transformer.from_crs(4326, 3338, always_xy=True)

    labels = sorted({n for n in fac["community_name"] if n and n not in names})
    labels += sorted(c for c in set(al["canonical"]) if c not in names and c not in labels)
    rows = []
    for lab in labels:
        recs = fac[(fac["community_name"] == lab) | (fac["community_name"].map(alias_of) == lab)] \
            if lab in set(al["canonical"]) else fac[fac["community_name"] == lab]
        located = recs[recs["latitude"] != ""]
        if len(located):
            xs, ys = to3338.transform(located["longitude"].astype(float).values, located["latitude"].astype(float).values)
            pos = "median of the records' latitude/longitude"
        else:
            xs, ys = recs["map_x"].astype(float).values, recs["map_y"].astype(float).values
            pos = "AEA map point (the records have no latitude/longitude)"
        x, y = float(np.median(xs)), float(np.median(ys))
        codes = sorted({c.upper() for c in recs["community_id"] if c})
        code_names = [by_id.at[c, "community_name"] if c in by_id.index else f"{c} (not in DCRA)" for c in codes]
        cand, action, why = SUGGEST.get(lab, ("", "", ""))
        cand_row = ref[ref["community_name"] == cand]
        cand_km = (round(float(np.hypot(float(cand_row["x_3338"].iloc[0]) - x, float(cand_row["y_3338"].iloc[0]) - y)) / 1000, 1)
                   if len(cand_row) else "")
        near = nearest(ref, x, y)
        rows.append({
            "label": lab,
            "kind": "alias canonical not a DCRA name" if lab in set(al["canonical"]) else "inventory label not a DCRA name",
            "records": len(recs),
            "located_records": len(located),
            "facility_ids": "; ".join(sorted({f for f in recs["facility_id"] if f}, key=int)) or "(none: unlocated)",
            "entity_names": "; ".join(sorted(set(recs["entity_name"])))[:400],
            "located_in_place": "; ".join(sorted({p for p in recs["located_in_place"] if p})),
            "community_relation": "; ".join(f"{k} {v}" for k, v in recs["community_relation"].value_counts().items()),
            "carried_community_code": "; ".join(codes) or "(blank)",
            "carried_code_dcra_name": "; ".join(code_names),
            "current_alias": alias_of.get(lab, "") or "; ".join(f"{v} -> {lab}" for v, c in alias_of.items() if c == lab),
            "harness_review_today": hr.get(lab, ""),
            "candidate_dcra_name": cand,
            "candidate_dcra_type": cand_row["community_type"].iloc[0] if len(cand_row) else "",
            "candidate_dcra_id": cand_row["community_id"].iloc[0] if len(cand_row) else "",
            "candidate_km": cand_km,
            "nearest_dcra_1": f"{near[0][0]} ({near[0][1]}, {near[0][2]} km)",
            "nearest_dcra_2": f"{near[1][0]} ({near[1][1]}, {near[1][2]} km)",
            "position_from": pos,
            "suggested_action": action,
            "evidence": why,
            **{c: "" for c in DECISION_COLS},
        })
    return pd.DataFrame(rows)


def write_xlsx(df: pd.DataFrame, path: Path) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    wb = Workbook(); ws = wb.active; ws.title = "Community labels"
    hdr, fill, inp = Font(name="Arial", size=10, bold=True, color="FFFFFF"), PatternFill("solid", fgColor="305496"), PatternFill("solid", fgColor="FFFF00")
    wide = {"entity_names": 50, "evidence": 70, "suggested_action": 40, "notes": 36, "harness_review_today": 34,
            "carried_community_code": 40, "candidate_dcra_id": 40, "nearest_dcra_1": 34, "nearest_dcra_2": 34,
            "facility_ids": 24, "position_from": 28, "your_value": 22, "label": 20, "kind": 24}
    cols = list(df.columns)
    for j, c in enumerate(cols, 1):
        x = ws.cell(row=1, column=j, value=c); x.font = hdr; x.fill = fill; x.alignment = Alignment(wrap_text=True)
        ws.column_dimensions[get_column_letter(j)].width = wide.get(c, 16)
    for i, row in enumerate(df.itertuples(index=False), 2):
        for j, (c, v) in enumerate(zip(cols, row), 1):
            x = ws.cell(row=i, column=j, value=v if v != "" else None)
            x.font = Font(name="Arial", size=10); x.alignment = Alignment(wrap_text=True, vertical="top")
            if c in DECISION_COLS:
                x.fill = inp
    dcol = get_column_letter(cols.index("decision") + 1)
    dv = DataValidation(type="list", formula1='"approve,approve with my value,reject,skip for now"', allow_blank=True)
    dv.add(f"{dcol}2:{dcol}{len(df) + 1}"); ws.add_data_validation(dv)
    ws.freeze_panes = "B2"; ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{len(df) + 1}"
    readme = wb.create_sheet("README")
    for r, (a, b) in enumerate([
        ("What", "Inventory community labels (2025 release, published table) that are not a DCRA community name, and aliases whose canonical is not one."),
        ("Reference", "inputs/community_reference/dcra_community_reference.csv (DCRA locations 2026-11-16 joined to the Community Overview 2026-10-10)."),
        ("Computed", "records, facility_ids, entity_names, located_in_place / community_relation (stage 05), carried code and its DCRA name, nearest DCRA communities, candidate distance."),
        ("Suggested", "candidate_dcra_name, suggested_action and evidence are the reviewer's reading, not a decision."),
        ("Your part", "Fill the yellow columns. decision: approve | approve with my value | reject | skip for now. Nothing changes until a decision is recorded (aliases.csv / corrections.csv in this repo, community_review.csv in the harness)."),
        ("Where it lands", "An alias or a name correction here changes the hub label at the next network re-export; the harness community list can resolve the name now without any network change."),
    ], 1):
        readme.cell(row=r, column=1, value=a).font = Font(name="Arial", size=10, bold=True)
        readme.cell(row=r, column=2, value=b).font = Font(name="Arial", size=10)
    readme.column_dimensions["A"].width = 16; readme.column_dimensions["B"].width = 140
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--release", default="2025")
    ap.add_argument("--harness-review", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=rp.DIAGNOSTICS_OUT / "00_inventory_qc")
    a = ap.parse_args(argv)
    df = build(a.release, a.harness_review)
    a.out.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out / "community_label_review.csv", index=False, lineterminator="\n")
    write_xlsx(df, a.out / "community_label_review.xlsx")
    print(f"{len(df)} review rows -> {a.out / 'community_label_review.xlsx'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
