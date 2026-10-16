"""The hub handoff tables (mmnet.handoff): stage 02's hub membership and stage 03's placement,
written beside the final_network zips so consumers read the builder's answer instead of
inferring hub membership by distance or a hub's community by vote."""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source_scripts"))

from mmnet.handoff import HUB_MEMBERS_COLUMNS, hub_members_table, write_hub_handoff  # noqa: E402


def _hubs():
    return pd.DataFrame({
        "hub_id": ["Hub_1", "Hub_2", "Hub_10"],
        "hub_key": ["NOME", "GOLOVIN", "NOME"],
        "hub_community": ["Nome", "Golovin", "Nome"],
        "hub_kind": ["community", "community", "remote_site"],
        "delivery_method": ["Barge or Road", "Barge", "Road"],
        "hub_type": ["Receiver", "Receiver", "Receiver"],
        "member_site_ids": ["A;B", "SYN-3", None],
    })


def _site_members():
    return pd.DataFrame({"ast_facility_id": ["A", "A", "B", "SYN-3"],
                         "record_id": ["r1", "r2", "r3", "r4"]})


def _hub_snaps():
    return pd.DataFrame({"hub_id": ["Hub_1", "Hub_2", "Hub_10"],
                         "node_id": [10, 10, None],
                         "snap_dist_m": [120.0, 300.5, 40000.0],
                         "snap_surface": ["Road", "Road", None],
                         "status": ["placed", "merged:Hub_1", "unplaced:beyond_cap"]})


def test_one_row_per_hub_and_raw_record():
    t = hub_members_table(_hubs(), _site_members(), _hub_snaps())
    assert list(t.columns) == HUB_MEMBERS_COLUMNS
    # A has two raw records, B one, SYN-3 one, Hub_10 has no member -> an empty-site row
    assert len(t) == 5
    nome = t[t.hub_id == "Hub_1"]
    assert sorted(nome.record_id) == ["r1", "r2", "r3"]
    assert set(nome.node_id) == {10} and set(nome.snap_status) == {"placed"}
    golovin = t[t.hub_id == "Hub_2"].iloc[0]
    assert golovin.ast_facility_id == "SYN-3" and golovin.record_id == "r4"
    assert golovin.snap_status == "merged:Hub_1" and golovin.node_id == 10, "a merged hub names the node it shares"
    far = t[t.hub_id == "Hub_10"].iloc[0]
    assert far.ast_facility_id == "" and pd.isna(far.record_id)
    assert pd.isna(far.node_id) and far.snap_status == "unplaced:beyond_cap"
    assert far.hub_kind == "remote_site"


def test_hub_order_is_numeric_and_every_hub_present():
    t = hub_members_table(_hubs(), _site_members(), _hub_snaps())
    assert list(dict.fromkeys(t.hub_id)) == ["Hub_1", "Hub_2", "Hub_10"]
    assert t.hub_id.nunique() == 3


def test_builds_without_the_record_trail_or_snaps():
    t = hub_members_table(_hubs(), None, None)
    assert len(t) == 4 and t.record_id.isna().all() and t.node_id.isna().all()
    assert t.snap_status.isna().all()


def test_write_hub_handoff_from_stage_outputs(tmp_path):
    out = tmp_path / "output"; out.mkdir()
    final = tmp_path / "final_network"; final.mkdir()
    hubs = gpd.GeoDataFrame(_hubs(), geometry=[Point(0, 0), Point(1000, 0), Point(5000, 0)], crs=3338)
    hubs.to_file(out / "02_hubs.gpkg", driver="GPKG")
    _site_members().to_csv(out / "01_site_members.csv", index=False)
    _hub_snaps().to_csv(out / "02_hub_snaps.csv", index=False)
    written = write_hub_handoff(out, final)
    assert [p.name for p in written] == ["hub_members.csv", "hub_snaps.csv"]
    back = pd.read_csv(final / "hub_members.csv", dtype="string")
    assert list(back.columns) == HUB_MEMBERS_COLUMNS and len(back) == 5
    assert (final / "hub_members.csv").read_bytes().count(b"\r") == 0, "LF endings like the other trails"
    snaps = pd.read_csv(final / "hub_snaps.csv")
    assert list(snaps.columns) == ["hub_id", "node_id", "snap_dist_m", "snap_surface", "status"]


def test_write_hub_handoff_skips_an_older_build(tmp_path):
    assert write_hub_handoff(tmp_path, tmp_path) == []


# ----------------------------------------------------------------------------- the DuckDB loader side
def _loader():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "load02", ROOT / "workflows" / "03_multimodal_join" / "02_load_final_network.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def _db_with_hub_nodes(con):
    con.execute("CREATE TABLE network_nodes(node_id BIGINT, is_hub BOOLEAN, hub_id VARCHAR)")
    con.execute("INSERT INTO network_nodes VALUES (10, true, 'Hub_1+Hub_2'), (11, false, NULL), (12, true, 'Hub_7')")


def test_loader_writes_hub_members_and_hub_snaps(tmp_path):
    import duckdb
    load02 = _loader()
    final = tmp_path / "final_network"; final.mkdir()
    hubs = _hubs().assign(member_site_ids=["A;B", "SYN-3", "Z"])
    snaps = _hub_snaps().assign(node_id=[10, 10, 12], status=["placed", "merged:Hub_1", "placed"])
    members = hub_members_table(hubs, _site_members(), snaps)
    members.to_csv(final / "hub_members.csv", index=False, lineterminator="\n")
    snaps.to_csv(final / "hub_snaps.csv", index=False, lineterminator="\n")
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    _db_with_hub_nodes(con)
    written = load02.load_hub_handoff(con, final / "hub_members.csv", final / "hub_snaps.csv")
    assert written == {"hub_members": 5, "hub_snaps": 3}
    assert con.execute("SELECT count(DISTINCT hub_id) FROM hub_members").fetchone()[0] == 3
    assert con.execute("SELECT record_id FROM hub_members WHERE ast_facility_id = 'SYN-3'").fetchone()[0] == "r4"
    assert con.execute("SELECT typeof(node_id) FROM hub_members LIMIT 1").fetchone()[0] == "BIGINT"
    con.close()


def test_loader_refuses_handoff_from_another_build(tmp_path):
    import duckdb, pytest
    load02 = _loader()
    final = tmp_path / "final_network"; final.mkdir()
    # Hub_7 claims node 12 but the shapefile has only one hub node -> different builds
    snaps = _hub_snaps().assign(node_id=[10, 10, 12], status=["placed", "merged:Hub_1", "placed"])
    hub_members_table(_hubs(), _site_members(), snaps).to_csv(final / "hub_members.csv", index=False)
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    con.execute("CREATE TABLE network_nodes(node_id BIGINT, is_hub BOOLEAN, hub_id VARCHAR)")
    con.execute("INSERT INTO network_nodes VALUES (10, true, 'Hub_1+Hub_2'), (12, false, NULL)")
    with pytest.raises(SystemExit):
        load02.load_hub_handoff(con, final / "hub_members.csv", final / "hub_snaps.csv")
    con.close()


def test_loader_skips_an_older_export(tmp_path):
    import duckdb
    load02 = _loader()
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    _db_with_hub_nodes(con)
    assert load02.load_hub_handoff(con, tmp_path / "hub_members.csv", tmp_path / "hub_snaps.csv") == {}
    assert "hub_members" not in {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    con.close()
