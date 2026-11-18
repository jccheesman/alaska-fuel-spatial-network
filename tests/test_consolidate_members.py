"""Phase 4 of the inventory QC plan: the build reads workflow 00's published table and keeps a
site-member trail (record_id) through the 50 m consolidation."""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

import repo_paths as rp

from mmnet.config import PipelineConfig, Params, load_profile  # noqa: E402
from mmnet.steps.consolidate import consolidate_facilities  # noqa: E402

PROFILE = rp.NETWORK_PROFILE
CLEAN = sorted(rp.INVENTORY_QC_OUT.glob("*/facilities_clean.csv"))


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
    spec = importlib.util.spec_from_file_location("nr", rp.WORKFLOWS / "02_network_build" / "00_normalize_raw.py")
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


# --------------------------------------------------------------------------
# reviewed anchor exclusions (inputs/network_qc/excluded_anchors.csv)
# --------------------------------------------------------------------------
def _normalize_module():
    spec = importlib.util.spec_from_file_location("nr_excl", rp.WORKFLOWS / "02_network_build" / "00_normalize_raw.py")
    nr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(nr)
    return nr


def test_anchor_exclusion_drops_the_reviewed_port_and_only_it(tmp_path, monkeypatch):
    import geopandas as gpd
    from shapely.geometry import Point

    nr = _normalize_module()
    src = tmp_path / "ports.geojson"
    gpd.GeoDataFrame({"Facility": ["Port of Anchorage", "Port MacKenzie", "Nome Harbor"], "Location": ["a", "b", "c"]},
                     geometry=[Point(-149.88, 61.24), Point(-149.92, 61.27), Point(-165.4, 64.5)], crs=4326).to_file(src, driver="GeoJSON")
    table = tmp_path / "excluded_anchors.csv"
    table.write_text("layer,column,value,reason,evidence,reviewer,date,status\n"
                     "ports,facility,Port MacKenzie,no barge landing,owner,JC,2026-11-18,approved\n"
                     "ports,facility,Nome Harbor,was wrong,owner,JC,2026-11-18,retired\n")
    monkeypatch.setattr(nr, "INTERIM", tmp_path)
    monkeypatch.setattr(nr, "EXCLUDED_ANCHORS", table)
    r = nr.normalize_entry({"name": "ports", "kind": "point", "status": "used", "src": src,
                            "rename": {"Location": "location", "Facility": "facility"}})
    kept = gpd.read_file(r["out"])
    assert sorted(kept["facility"]) == ["Nome Harbor", "Port of Anchorage"]      # the retired row excludes nothing
    assert r["rows"] == 2 and r["excluded"] == ["facility=Port MacKenzie (1)"]


def test_a_stale_anchor_exclusion_stops_the_stage(tmp_path, monkeypatch):
    import geopandas as gpd
    import pytest
    from shapely.geometry import Point

    nr = _normalize_module()
    g = gpd.GeoDataFrame({"facility": ["Port of Anchorage"]}, geometry=[Point(0, 0)], crs=3338)
    with pytest.raises(SystemExit, match="retire the row"):
        nr.apply_anchor_exclusions(g, "ports", {"ports": [("facility", "Port MacKenzie")]})
    with pytest.raises(SystemExit, match="no column"):
        nr.apply_anchor_exclusions(g, "ports", {"ports": [("name", "x")]})
    bad = tmp_path / "excluded_anchors.csv"
    bad.write_text("layer,column,value,reason,evidence,reviewer,date,status\nports,facility,X,why,ev,,2026-11-18,approved\n")
    with pytest.raises(SystemExit, match="required"):
        nr.load_anchor_exclusions(bad)


def test_the_tracked_anchor_exclusions_are_valid_and_name_real_layers():
    nr = _normalize_module()
    excl = nr.load_anchor_exclusions()
    points = {e["name"] for e in nr.SPEC if e["kind"] == "point"}
    assert set(excl) <= points, f"excluded_anchors.csv names layers that are not point layers: {set(excl) - points}"
    assert ("facility", "Port MacKenzie") in excl.get("ports", [])
