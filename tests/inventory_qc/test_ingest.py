"""Committed facility-inventory releases are self-consistent and contact-free."""
import hashlib
import json
import csv
from pathlib import Path
import importlib.util
import pytest

ROOT = Path(__file__).resolve().parents[2]
RELEASES = ROOT / "inputs" / "raw_facility_data"
spec = importlib.util.spec_from_file_location("ingest", ROOT / "workflows" / "00_inventory_qc" / "01_ingest.py")
ingest = importlib.util.module_from_spec(spec); spec.loader.exec_module(ingest)
FOLDERS = sorted(p for p in RELEASES.iterdir() if (p / "snapshot_manifest.json").exists())
CONTACT_WORDS = ("Representative", "PhoneNumber", "Phone", "Email", "LandOwner", "FacilityOwner", "Operator", "Evaluator", "_user")


@pytest.mark.parametrize("folder", FOLDERS, ids=[p.name for p in FOLDERS])
def test_release_csv_matches_manifest(folder):
    man = json.loads((folder / "snapshot_manifest.json").read_text())
    got = hashlib.sha256((folder / man["snapshot_csv"]).read_bytes()).hexdigest()
    assert got == man["snapshot_csv_sha256"]


@pytest.mark.parametrize("folder", FOLDERS, ids=[p.name for p in FOLDERS])
def test_release_csv_has_only_schema_columns(folder):
    man = json.loads((folder / "snapshot_manifest.json").read_text())
    with open(folder / man["snapshot_csv"], newline="") as fh:
        header = next(csv.reader(fh))
    schema = [r["name"] for r in csv.DictReader(open(ingest.SCHEMA))]
    assert set(header) <= set(schema)
    assert not any(w.lower() in c.lower() for c in header for w in CONTACT_WORDS)


@pytest.mark.parametrize("folder", FOLDERS, ids=[p.name for p in FOLDERS])
def test_release_rederives_from_raw_when_present(folder):
    man = json.loads((folder / "snapshot_manifest.json").read_text())
    raw = ingest._reachable_raw(folder, man)
    if raw is None:
        pytest.skip(f"raw file for {folder.name} not present (sha256 {man['raw_sha256'][:12]}...)")
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == man["raw_sha256"]
    clean, _ = ingest.snapshot(raw, man["source"])
    sha = ingest.write_csv(clean, folder.parent.parent / "_tmp_rederive.csv")
    (folder.parent.parent / "_tmp_rederive.csv").unlink()
    assert sha == man["snapshot_csv_sha256"]


def test_column_map_never_reads_contact_fields():
    m = list(csv.DictReader(open(ingest.QC / "sources" / "aea" / "column_map.csv")))
    for r in m:
        if any(w.lower() in r["source_column"].lower() for w in CONTACT_WORDS):
            assert r["keep"] == "never", r["source_column"]


def test_corrections_reference_known_records():
    rows = list(csv.DictReader(open(ingest.QC / "corrections.csv")))
    latest = FOLDERS[-1]
    man = json.loads((latest / "snapshot_manifest.json").read_text())
    ids = {r["record_id"] for r in csv.DictReader(open(latest / man["snapshot_csv"]))}
    approved = [r for r in rows if r["status"] == "approved"]
    assert approved, "no approved corrections"
    for r in approved:
        assert r["record_id"] in ids, r
        assert r["reviewer"] and r["reviewed_on"], r
