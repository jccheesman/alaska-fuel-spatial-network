"""Phase 4 of the inventory QC plan: the build reads workflow 00's published table and keeps a
site-member trail (record_id) through the 50 m consolidation."""
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source_scripts"))

from mmnet.config import PipelineConfig, Params, load_profile  # noqa: E402
from mmnet.steps.consolidate import consolidate_facilities  # noqa: E402

PROFILE = ROOT / "workflows" / "02_network_build" / "profile.yaml"
CLEAN = sorted((ROOT / "outputs" / "00_inventory_qc").glob("*/facilities_clean.csv"))


def _config(record_id: bool) -> PipelineConfig:
    cols = {"id": "ast_facility_id", "community": "community_name", "delivery_method": "delivery_method",
            "total_capacity": "total_capacity", "longitude": "longitude", "latitude": "latitude"}
    if record_id:
        cols["record_id"] = "record_id"
    return PipelineConfig(roots={}, layers=[], raw={}, facility_columns=cols,
                          capacity_columns=["total_capacity"], routable_modes=["Road", "Barge", "Plane"])


def _inventory(tmp_path) -> Path:
    # two records 10 m apart (merge), one 5 km away (its own site); one blank id -> SYN
    df = pd.DataFrame({
        "id": ["A1", "A2", "", "B1"],
        "record_id": ["{r1}", "{r2}", "{r3}", "{r4}"],
        "community": ["X", "X", "Y", "Y"],
        "delivery_method": ["Road", "Barge", "Road", "Road"],
        "total_capacity": [100, 200, 50, 75],
        "longitude": [-150.0, -150.0001, -150.1, -150.1],
        "latitude": [61.0, 61.0, 61.0, 61.0001],
    })
    p = tmp_path / "facilities.csv"
    df.to_csv(p, index=False)
    return p


def test_record_id_trail_survives_consolidation(tmp_path):
    fac = consolidate_facilities(_inventory(tmp_path), Params(dedup_tol_m=50), 4326, 3338, _config(True))
    trail = dict(zip(fac["ast_facility_id"], fac["member_record_ids"]))
    assert trail["A1"] == "{r1};{r2}"                       # merged pair, ids sorted
    assert trail["B1"] == "{r3};{r4}"                       # blank-id record merged into B1 (10 m apart)
    assert fac.set_index("ast_facility_id").loc["A1", "n_members"] == 2
    members = sorted(r for ids in fac["member_record_ids"] for r in ids.split(";"))
    assert members == ["{r1}", "{r2}", "{r3}", "{r4}"]      # nothing disappears silently


def test_without_record_id_nothing_changes(tmp_path):
    fac = consolidate_facilities(_inventory(tmp_path), Params(dedup_tol_m=50), 4326, 3338, _config(False))
    assert "member_record_ids" not in fac.columns and "n_members" not in fac.columns


def test_shipped_profile_maps_record_id():
    cfg = load_profile(PROFILE).to_pipeline_config()
    assert cfg.facility_columns.get("record_id") == "record_id"
    assert "av_gas_capacity" not in cfg.capacity_columns                  # dropped: empty in every release


@pytest.mark.skipif(not CLEAN, reason="no published facility table")
def test_normalize_raw_reads_published_table_with_profile_columns(tmp_path):
    spec = importlib.util.spec_from_file_location("nr", ROOT / "workflows" / "02_network_build" / "00_normalize_raw.py")
    nr = importlib.util.module_from_spec(spec); spec.loader.exec_module(nr)
    e = next(e for e in nr.SPEC if e["name"] == "facilities")
    assert e["src"] == CLEAN[-1]                                            # latest release, never data/raw
    nr.INTERIM = tmp_path
    r = nr.normalize_entry(e)
    cfg = load_profile(PROFILE).to_pipeline_config()
    assert set(cfg.facility_columns) <= set(r["columns"])                  # every profile key is present
    df = pd.read_csv(r["out"], dtype=str)
    assert r["rows"] == len(pd.read_csv(CLEAN[-1], dtype=str))             # one row per published record
    assert not {"phone", "email", "contact"} & {c.lower() for c in df.columns}
