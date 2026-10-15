#!/usr/bin/env python3
"""Stage 01 — ingest a facility-inventory release onto the clean schema.

Reads ONLY the raw columns the source adapter marks keep/fold (contact fields
are never parsed), renames + types them to inputs/inventory_qc/facility_schema.csv,
and writes a tracked release folder:

    inputs/raw_facility_data/<release>/
        aea_inventory_<release>.csv   clean-schema columns, raw row order (source_row)
        snapshot_manifest.json        raw sha256, counts, columns kept/dropped/never read
        diff_<prev>_to_<release>.csv  per-record added / removed / edited vs the previous release

The raw CSV itself is NOT written anywhere inside the repo (the 2022 copy lives
inside the tracked bulk_fuel_data.zip; later releases are checksummed only).

Run:
    python workflows/00_inventory_qc/01_ingest.py RAW.csv --release 2025
    python workflows/00_inventory_qc/01_ingest.py --check      # verify committed releases
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
QC = ROOT / "inputs" / "inventory_qc"
RELEASES = ROOT / "inputs" / "raw_facility_data"
SCHEMA = QC / "facility_schema.csv"
KEEP_VALUES = {"yes", "fold", "no", "never"}
TEXT_BREAK = " | "   # internal line breaks in text fields become this (AEA flips CR/LF between releases)


# ----------------------------------------------------------------------------- config
def load_schema() -> pd.DataFrame:
    s = pd.read_csv(SCHEMA, dtype=str).fillna("")
    if s["name"].duplicated().any():
        raise SystemExit("facility_schema.csv: duplicate column names")
    return s


def load_column_map(source: str) -> pd.DataFrame:
    path = QC / "sources" / source / "column_map.csv"
    m = pd.read_csv(path, dtype=str).fillna("")
    bad = set(m["keep"]) - KEEP_VALUES
    if bad:
        raise SystemExit(f"{path}: unknown keep values {sorted(bad)}")
    if m["source_column"].duplicated().any():
        raise SystemExit(f"{path}: duplicate source columns")
    schema_cols = set(load_schema()["name"])
    kept = m[m["keep"] == "yes"]
    unknown = sorted(set(kept["schema_column"]) - schema_cols)
    if unknown:
        raise SystemExit(f"{path}: schema_column(s) not in facility_schema.csv: {unknown}")
    return m


# ----------------------------------------------------------------------------- typing
def _type(s: pd.Series, t: str) -> pd.Series:
    if t == "float":
        return pd.to_numeric(s, errors="coerce").astype("float64")
    if t == "int":
        return pd.to_numeric(s, errors="coerce").round().astype("Int64")
    if t == "zip":
        z = pd.to_numeric(s, errors="coerce").round().astype("Int64").astype("string")
        return z.str.zfill(5).where(z.notna(), pd.NA)
    if t == "bool":
        return (s.astype("string").str.strip().str.upper()
                .map({"Y": True, "N": False, "YES": True, "NO": False}).astype("boolean"))
    if t == "date":
        return pd.to_datetime(s, errors="coerce", utc=True).dt.strftime("%Y-%m-%d")
    if t == "datetime":
        return pd.to_datetime(s, errors="coerce", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    out = (s.astype("string")
           .str.replace(r"\r\n|\r|\n", TEXT_BREAK, regex=True)
           .str.replace(r"\s+", " ", regex=True).str.strip().str.strip("| ").str.strip())
    return out.where(out != "", pd.NA)


# ----------------------------------------------------------------------------- snapshot
def snapshot(raw: Path, source: str = "aea") -> tuple[pd.DataFrame, dict]:
    """Raw CSV -> (clean-schema DataFrame in raw row order, manifest dict)."""
    m = load_column_map(source)
    with open(raw, encoding="utf-8-sig", newline="") as fh:
        header = next(csv.reader(fh))
    wanted = m[m["keep"].isin(["yes", "fold"])]
    missing = [c for c in wanted["source_column"] if c not in header]
    if missing:
        raise SystemExit(f"{raw.name}: missing mapped columns {missing} — the source schema changed; "
                         f"update inputs/inventory_qc/sources/{source}/column_map.csv")
    unknown = [c for c in header if c not in set(m["source_column"])]

    df = pd.read_csv(raw, usecols=list(wanted["source_column"]), dtype=str, encoding="utf-8-sig")
    clean = pd.DataFrame(index=df.index)
    clean["source_row"] = df.index + 2            # line number in the raw CSV (header = line 1)
    for r in wanted[wanted["keep"] == "yes"].itertuples():
        clean[r.schema_column] = _type(df[r.source_column], r.type)
    folds: dict[str, int] = {}
    for r in wanted[wanted["keep"] == "fold"].itertuples():
        if not r.fold_into or r.fold_into not in clean.columns:
            raise SystemExit(f"column_map: fold column {r.source_column} needs a valid fold_into target")
        fill = _type(df[r.source_column], r.type or "string")
        folds[r.source_column] = int((clean[r.fold_into].isna() & fill.notna()).sum())
        clean[r.fold_into] = clean[r.fold_into].fillna(fill)
    if clean["record_id"].isna().any() or clean["record_id"].duplicated().any():
        raise SystemExit("record_id must be present and unique on every row")

    # schema order
    order = [c for c in load_schema()["name"] if c in clean.columns]
    clean = clean[order]
    manifest = {
        "source": source,
        "raw_file": raw.name,
        "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows": int(len(clean)),
        "rows_with_coordinates": int(clean[["latitude", "longitude"]].notna().all(axis=1).sum()),
        "columns_kept": list(clean.columns),
        "columns_dropped": sorted(m.loc[m["keep"] == "no", "source_column"]),
        "columns_never_read": sorted(m.loc[m["keep"] == "never", "source_column"]),
        "unknown_columns_in_raw": unknown,
        "folded_fills": folds,
        "column_map_sha256": hashlib.sha256((QC / "sources" / source / "column_map.csv").read_bytes()).hexdigest(),
        "schema_sha256": hashlib.sha256(SCHEMA.read_bytes()).hexdigest(),
    }
    return clean, manifest


def write_csv(df: pd.DataFrame, path: Path) -> str:
    df.to_csv(path, index=False, float_format="%.10g", lineterminator="\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_release_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False).replace({"": np.nan})


# ----------------------------------------------------------------------------- diff
MAP_JITTER_M = 2.0   # AEA re-projects map points by ~1 m between releases; not an edit


def diff_releases(prev: pd.DataFrame, cur: pd.DataFrame) -> pd.DataFrame:
    a, b = prev.set_index("record_id"), cur.set_index("record_id")
    rows = []
    cmp = [c for c in a.columns if c != "source_row" and c in b.columns]
    both = a.index.intersection(b.index)
    A, B = a.loc[both, cmp].fillna(""), b.loc[both, cmp].fillna("")
    changed = (A != B)
    for rid in both[changed.any(axis=1)]:
        for c in cmp:
            if A.at[rid, c] != B.at[rid, c]:
                rows.append(dict(record_id=rid, change="edited", field=c, old_value=A.at[rid, c],
                                 new_value=B.at[rid, c], community_name=b.at[rid, "community_name"],
                                 source_row_old=a.at[rid, "source_row"], source_row_new=b.at[rid, "source_row"]))
    for rid in a.index.difference(b.index):
        rows.append(dict(record_id=rid, change="removed", field="", old_value="", new_value="",
                         community_name=a.at[rid, "community_name"], source_row_old=a.at[rid, "source_row"], source_row_new=""))
    for rid in b.index.difference(a.index):
        rows.append(dict(record_id=rid, change="added", field="", old_value="", new_value="",
                         community_name=b.at[rid, "community_name"], source_row_old="", source_row_new=b.at[rid, "source_row"]))
    cols = ["record_id", "change", "field", "old_value", "new_value", "community_name", "source_row_old", "source_row_new"]
    return pd.DataFrame(rows, columns=cols).sort_values(["change", "record_id", "field"]).reset_index(drop=True)


def diff_summary(d: pd.DataFrame) -> dict:
    ed = d[d["change"] == "edited"]
    isxy = ed["field"].isin(["map_x", "map_y"])
    jitter = pd.Series(False, index=ed.index)
    jitter[isxy] = (pd.to_numeric(ed.loc[isxy, "old_value"]) - pd.to_numeric(ed.loc[isxy, "new_value"])).abs() <= MAP_JITTER_M
    big = ed[~jitter]
    return {
        "removed": int((d["change"] == "removed").sum()),
        "added": int((d["change"] == "added").sum()),
        "edited_records": int(ed["record_id"].nunique()),
        "edited_records_beyond_map_jitter": int(big["record_id"].nunique()),
        "edited_fields_beyond_map_jitter": big["field"].value_counts().to_dict(),
    }


# ----------------------------------------------------------------------------- releases
def previous_release(label: str) -> str | None:
    labels = sorted(p.name for p in RELEASES.iterdir() if p.is_dir() and p.name != label and (p / "snapshot_manifest.json").exists())
    labels = [l for l in labels if l < label]
    return labels[-1] if labels else None


def ingest(raw: Path, label: str, source: str = "aea") -> dict:
    folder = RELEASES / label
    folder.mkdir(parents=True, exist_ok=True)
    clean, man = snapshot(raw, source)
    csv_path = folder / f"{source}_inventory_{label}.csv"
    man["snapshot_csv"] = csv_path.name
    man["snapshot_csv_sha256"] = write_csv(clean, csv_path)
    prev = previous_release(label)
    if prev:
        pm = json.loads((RELEASES / prev / "snapshot_manifest.json").read_text())
        d = diff_releases(read_release_csv(RELEASES / prev / pm["snapshot_csv"]), read_release_csv(csv_path))
        dname = f"diff_{prev}_to_{label}.csv"
        write_csv(d, folder / dname)
        man["diff_from"] = prev
        man["diff_file"] = dname
        man["diff_summary"] = diff_summary(d)
    (folder / "snapshot_manifest.json").write_text(json.dumps(man, indent=2) + "\n")
    src = folder / "SOURCE.md"
    if not src.exists():
        src.write_text(
            f"# Facility inventory — release {label}\n\n"
            f"- **Source:** (fill in: publisher, service/URL)\n"
            f"- **Raw file:** `{raw.name}` — **NOT committed** (contains personal contact fields)\n"
            f"- **Raw SHA-256:** `{man['raw_sha256']}`\n"
            f"- **Raw rows:** {man['rows']} ({man['rows_with_coordinates']} with coordinates)\n"
            f"- **Downloaded:** (fill in: date, by whom)\n- **Note:** (fill in)\n")
    return man


def check() -> int:
    """Verify every committed release: CSV sha256 matches its manifest; re-derive when the raw file is reachable."""
    rc = 0
    for folder in sorted(p for p in RELEASES.iterdir() if p.is_dir()):
        mf = folder / "snapshot_manifest.json"
        if not mf.exists():
            continue
        man = json.loads(mf.read_text())
        csv_path = folder / man["snapshot_csv"]
        got = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        ok = got == man["snapshot_csv_sha256"]
        print(f"{folder.name}: {man['snapshot_csv']} sha256 {'OK' if ok else 'MISMATCH'}")
        rc |= (not ok)
        raw = _reachable_raw(folder, man)
        if raw is not None:
            clean, _ = snapshot(raw, man["source"])
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                sha = write_csv(clean, Path(td) / "x.csv")
            same = sha == man["snapshot_csv_sha256"]
            print(f"{folder.name}: re-derived from raw -> {'identical' if same else 'DIFFERS'}")
            rc |= (not same)
        else:
            print(f"{folder.name}: raw file not present (sha256 {man['raw_sha256'][:12]}…) — skipped re-derivation")
    return rc


def _reachable_raw(folder: Path, man: dict) -> Path | None:
    """The raw CSV if it sits next to the manifest or inside a zip in the release folder."""
    cand = folder / man["raw_file"]
    if cand.exists():
        return cand
    for z in folder.glob("*.zip"):
        with zipfile.ZipFile(z) as zf:
            for name in zf.namelist():
                if name.endswith(man["raw_file"]):
                    out = ROOT / "inputs" / "bulk_fuel_data" / "raw" / Path(name).name  # the extract_inputs.py location
                    if out.exists() and hashlib.sha256(out.read_bytes()).hexdigest() == man["raw_sha256"]:
                        return out
                    import tempfile
                    td = Path(tempfile.mkdtemp())
                    zf.extract(name, td)
                    return td / name
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raw", nargs="?", type=Path, help="raw inventory CSV (never committed)")
    ap.add_argument("--release", help="release label, e.g. 2025 or 2025-12")
    ap.add_argument("--source", default="aea", help="adapter under inputs/inventory_qc/sources/")
    ap.add_argument("--check", action="store_true", help="verify the committed release folders")
    a = ap.parse_args(argv)
    if a.check:
        return check()
    if not a.raw or not a.release:
        ap.error("RAW.csv and --release are required (or use --check)")
    man = ingest(a.raw, a.release, a.source)
    print(json.dumps({k: man[k] for k in ("raw_sha256", "rows", "rows_with_coordinates", "unknown_columns_in_raw", "folded_fills") if k in man}, indent=2))
    if "diff_summary" in man:
        print(f"diff vs {man['diff_from']}: {json.dumps(man['diff_summary'])}")
    print(f"wrote inputs/raw_facility_data/{a.release}/ — fill in SOURCE.md and add the raw sha256 to inputs/MANIFEST.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
