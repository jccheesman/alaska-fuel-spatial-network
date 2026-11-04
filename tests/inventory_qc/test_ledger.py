"""Stage 08: the inventory ledger is generated from the CSVs, has the documented tabs, and is
byte-deterministic (an unchanged inventory -> an identical workbook)."""
import hashlib

import pandas as pd
import pytest

import repo_paths as rp
from inventory_qc import ledger as led

ROOT = rp.ROOT
pytest.importorskip("openpyxl")
LABEL = led.latest_release()
TABS = ["README", "Summary", "Approved by owner", "Applied by rule", "Aliases", "Pending", "Rejected & retired", "Excluded", "Open review queue"]


def test_ledger_tabs_and_counts_match_the_csvs(tmp_path):
    tabs = led.build(LABEL)
    assert list(tabs) == TABS
    corr = led.corrections()
    assert len(tabs["Approved by owner"]) + len(tabs["Applied by rule"]) == (corr["status"] == "approved").sum()
    assert len(tabs["Pending"]) == (corr["status"] == "pending").sum()
    assert (tabs["Applied by rule"]["field"] == "exclude").all(), "the only rule so far is the stack exclusion"
    q = pd.read_csv(ROOT / "outputs" / "00_inventory_qc" / LABEL / "review_queue.csv", dtype=str, keep_default_na=False)
    assert len(tabs["Open review queue"]) == len(q) and "decision" in tabs["Open review queue"].columns


def test_ledger_is_byte_deterministic(tmp_path):
    tabs = led.build(LABEL)
    a, b = tmp_path / "a.xlsx", tmp_path / "b.xlsx"
    assert led.write(tabs, a) and led.write(tabs, b)
    assert hashlib.sha256(a.read_bytes()).hexdigest() == hashlib.sha256(b.read_bytes()).hexdigest()
    x = pd.ExcelFile(a)
    assert x.sheet_names == TABS
    assert "08_ledger.py" in x.parse("README").to_string()
