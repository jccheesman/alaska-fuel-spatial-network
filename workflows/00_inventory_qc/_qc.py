"""Shared helpers for workflow 00 (inventory QC): paths, config loaders, name canonicalisation.

Every stage imports from here so the config files under inputs/inventory_qc/ are the single
source of truth (no stage carries its own threshold, alias or schema copy).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
QC = ROOT / "inputs" / "inventory_qc"
RELEASES = ROOT / "inputs" / "raw_facility_data"
OUT = Path(os.environ["INVENTORY_QC_OUT"]) if os.environ.get("INVENTORY_QC_OUT") else ROOT / "outputs" / "00_inventory_qc"
SCHEMA = QC / "facility_schema.csv"
CORRECTIONS = QC / "corrections.csv"
ALIASES = QC / "aliases.csv"
THRESHOLDS = QC / "thresholds.csv"

DERIVED_COLUMNS = QC / "derived_columns.csv"


def derived() -> pd.DataFrame:
    """Columns the published table adds to the schema, declared in inputs/inventory_qc/derived_columns.csv
    (name, produced_by, type, description). Adding a derived variable = add a row here + produce it
    in the named stage; the publish step fails if a declared column is missing or an undeclared one appears."""
    return pd.read_csv(DERIVED_COLUMNS, dtype=str).fillna("")


# Back-compat name used by the stages.
DERIVED = list(derived()["name"])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def schema() -> pd.DataFrame:
    return pd.read_csv(SCHEMA, dtype=str).fillna("")


def thresholds() -> dict[str, float]:
    t = pd.read_csv(THRESHOLDS, dtype=str)
    return {r.name: float(r.value) for r in t.itertuples()}


def corrections() -> pd.DataFrame:
    c = pd.read_csv(CORRECTIONS, dtype=str, keep_default_na=False)
    need = {"record_id", "field", "old_value", "new_value", "status", "reviewer", "reviewed_on"}
    missing = need - set(c.columns)
    if missing:
        raise SystemExit(f"corrections.csv is missing columns {sorted(missing)}")
    bad = set(c["status"]) - {"approved", "pending", "rejected", "retired"}
    if bad:
        raise SystemExit(f"corrections.csv: unknown status values {sorted(bad)}")
    return c


def aliases() -> pd.DataFrame:
    return pd.read_csv(ALIASES, dtype=str, keep_default_na=False)


def latest_release() -> str:
    labels = sorted(p.name for p in RELEASES.iterdir() if (p / "snapshot_manifest.json").exists())
    if not labels:
        raise SystemExit("no release folder under inputs/raw_facility_data/")
    return labels[-1]


def release_manifest(label: str) -> dict:
    return json.loads((RELEASES / label / "snapshot_manifest.json").read_text())


def read_release(label: str) -> pd.DataFrame:
    man = release_manifest(label)
    return read_csv(RELEASES / label / man["snapshot_csv"])


def read_csv(path: Path) -> pd.DataFrame:
    """Read a stage table as strings, blanks -> NaN (round-trips write_csv exactly)."""
    return pd.read_csv(path, dtype=str, keep_default_na=False).replace({"": np.nan})


def write_csv(df: pd.DataFrame, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")
    return sha256(path)


_PUNCT = re.compile(r"[.'`,]")
_WS = re.compile(r"\s+")


def canon(name) -> str | None:
    """Canonical community key: upper-case, punctuation stripped, SAINT->ST, single spaces.

    Absorbs spelling and punctuation variants (Clark's Point / Clarks Point; Saint Marys /
    St. Mary's) but NOT genuinely different names — those go through aliases.csv.
    """
    if name is None or (isinstance(name, float) and np.isnan(name)):
        return None
    s = _PUNCT.sub("", str(name).upper())
    s = re.sub(r"\bSAINT\b", "ST", s)
    s = re.sub(r"\bMOUNT\b", "MT", s)
    s = _WS.sub(" ", s).strip()
    return s or None
