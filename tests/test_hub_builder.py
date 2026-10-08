"""Phase 5 of the inventory QC plan (docs/INVENTORY_QC_PLAN.md): the hub builder's five fixes,
each pinned on a small hand-built fixture in metres (EPSG:3338-like).

  R5  cannot-link: a 50 m stack of records from different communities stays several sites
  R2  tag: a labelled facility outside every place is still tested; a conflict is kept + flagged
  R3  hubs: one hub per canonical community label (spelling variants merge; place polygons don't split)
  R6  hubs: unlabelled sites outside places group by buffer blob, never by borough
  R4  assemble: a snap beyond max_snap_dist leaves the hub unplaced; two hubs on one node merge
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point, box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source_scripts"))

from mmnet.assemble import connect_multimodal  # noqa: E402
from mmnet.config import Params  # noqa: E402
from mmnet.steps.consolidate import split_clusters_by_label  # noqa: E402
from mmnet.steps.hubs import aggregate_hubs, hub_members  # noqa: E402
from mmnet.steps.tag import assign_community_region  # noqa: E402

CRS = 3338


def _pts(xy, **cols):
    return gpd.GeoDataFrame(cols, geometry=[Point(x, y) for x, y in xy], crs=CRS)


# ----------------------------------------------------------------------------- R5 cannot-link
def test_split_clusters_by_label_keeps_villages_apart():
    g = _pts([(0, 0), (10, 0), (12, 0), (5000, 0)],
             community_name=["Atmautluak", "Chefornak", None, "Atmautluak"])
    one_cluster = np.array([1, 1, 1, 2])                   # the 50 m linkage merged the stack
    new, n_split = split_clusters_by_label(g, one_cluster)
    assert n_split == 1
    assert new[0] != new[1], "two labels -> two sites"
    assert new[2] == new[1], "the unlabelled record follows its nearest labelled neighbour"
    assert new[3] not in (new[0], new[1])
    assert sorted(set(new)) == [1, 2, 3], "dense, deterministic renumbering"


def test_split_is_a_noop_on_single_label_clusters():
    g = _pts([(0, 0), (10, 0)], community_name=["Kaltag", "KALTAG"])   # canonical-equal
    new, n_split = split_clusters_by_label(g, np.array([1, 1]))
    assert n_split == 0 and new[0] == new[1]


# ----------------------------------------------------------------------------- R2 tag
def _layers():
    places = gpd.GeoDataFrame({"place_name": ["Unalaska", "Nome"], "place_geoid": ["1", "2"]},
                              geometry=[box(0, 0, 100, 100), box(10_000, 0, 10_100, 100)], crs=CRS)
    regions = gpd.GeoDataFrame({"region_name": ["Aleutians West", "Nome CA"], "economic_region": ["SW", "NW"]},
                               geometry=[box(-1000, -1000, 5000, 1000), box(5000, -1000, 20_000, 1000)], crs=CRS)
    return places, regions


def test_labelled_facility_outside_every_place_is_tested_and_kept():
    places, regions = _layers()
    fac = _pts([(50, 50), (12_000, 50), (3000, 50)],
               ast_facility_id=["1", "2", "3"], cluster_id=[1, 2, 3],
               community_name=["Unalaska", "Unalaska", "Unalaska"], total_capacity=[1.0, 1.0, 1.0],
               delivery_method=["Barge"] * 3)
    out = assign_community_region(fac, places, regions)
    assert len(out) == 3, "conflicts are reported, never dropped"
    m = out.set_index("ast_facility_id")["name_match"]
    assert m["1"] == "agree"
    assert m["2"] == "conflict", "labelled Unalaska, sits in Nome CA, outside any place -> still tested"
    assert m["3"] == "neighbor", "same borough, outside the place polygon"
    assert out.set_index("ast_facility_id").loc["2", "label_borough"] == "Aleutians West"


# ----------------------------------------------------------------------------- R3 / R6 hubs
def _tagged(xy, **cols):
    n = len(xy)
    base = dict(ast_facility_id=[str(i) for i in range(n)], total_capacity=[100.0] * n,
                delivery_method=["Road"] * n, place_name=[None] * n, region_name=["B"] * n)
    base.update(cols)
    g = _pts(xy, **base)
    g["assigned_community"] = g["community_name"]
    return g


def test_one_hub_per_canonical_label_across_place_polygons():
    g = _tagged([(0, 0), (20_000, 0), (40_000, 0)],
                community_name=["St. Mary's", "Saint Marys", "ST MARYS"],
                place_name=["St. Marys", None, "Pitkas Point"])        # inside/outside/other place
    hubs = aggregate_hubs(g, Params(group_by=["community"], buffer_dist=5000))
    assert len(hubs) == 1
    assert hubs.loc[0, "num_facilities"] == 3 and hubs.loc[0, "member_site_ids"] == "0;1;2"
    assert hubs.loc[0, "hub_key"] == "ST MARYS" and hubs.loc[0, "hub_community"] == "St. Mary's"


def test_unlabelled_sites_group_by_blob_not_borough():
    g = _tagged([(0, 0), (3000, 0), (300_000, 0)], community_name=[None] * 3)   # 3 km apart, then 300 km
    hubs = aggregate_hubs(g, Params(group_by=["community"], buffer_dist=5000))
    assert len(hubs) == 2, "two blobs; the old borough fallback made ONE 300 km hub"
    assert set(hubs["hub_key"]) == {"blob:1", "blob:2"}
    assert hub_members(hubs).groupby("hub_id").size().tolist() == [2, 1]


def test_unlabelled_site_inside_a_place_takes_the_place_name():
    g = _tagged([(0, 0), (10, 0)], community_name=[None, "Nome"], place_name=["Nome", None])
    hubs = aggregate_hubs(g, Params(group_by=["community"]))
    assert len(hubs) == 1 and hubs.loc[0, "hub_key"] == "NOME"


# ----------------------------------------------------------------------------- R4 assemble
def _road():
    return gpd.GeoDataFrame({"type": ["Road", "Road"]},
                            geometry=[LineString([(0, 0), (1000, 0)]), LineString([(1000, 0), (2000, 0)])], crs=CRS)


def _hubs(xy):
    n = len(xy)
    return _pts(xy, hub_id=[f"Hub_{i + 1}" for i in range(n)], delivery_method=["Road", "Barge", "Road"][:n],
                hub_type=["Receiver", "Supplier", "Receiver"][:n], total_hub_capacity=[10.0, 20.0, 5.0][:n])


def test_snap_cap_leaves_far_hub_unplaced_and_reports_it():
    nodes, _, s = connect_multimodal(_road(), _hubs([(0, 10), (0, 90_000)]), {"Road"}, [], {},
                                     max_snap_dist=25_000)
    hs = s["hub_snaps"].set_index("hub_id")
    assert hs.loc["Hub_1", "status"] == "placed" and hs.loc["Hub_1", "snap_dist_m"] == 10.0
    assert hs.loc["Hub_2", "status"] == "unplaced:beyond_cap" and pd.isna(hs.loc["Hub_2", "node_id"])
    assert s["n_hubs"] == 1 and "Hub_2" not in set(nodes["hub_id"].dropna())


def test_no_cap_keeps_legacy_behaviour():
    _, _, s = connect_multimodal(_road(), _hubs([(0, 10), (2000, 90_000)]), {"Road"}, [], {})
    assert (s["hub_snaps"]["status"] == "placed").all(), "max_snap_dist=0 -> no cap"
    assert s["hub_snaps"].set_index("hub_id").loc["Hub_2", "snap_dist_m"] == 90_000.0


def test_two_hubs_on_one_node_merge_instead_of_overwriting():
    nodes, _, s = connect_multimodal(_road(), _hubs([(0, 10), (0, 20), (2000, 5)]), {"Road"}, [], {})
    hs = s["hub_snaps"].set_index("hub_id")
    assert hs.loc["Hub_2", "status"] == "merged:Hub_1"
    n0 = nodes.set_index("node_id").loc[0]
    assert n0["hub_id"] == "Hub_1+Hub_2" and n0["total_hub_capacity"] == 30.0
    assert n0["delivery_method"] == "Barge or Road" and n0["hub_type"] == "Supplier"
    assert s["n_hubs"] == 2 and len(hs) == 3, "every hub is accounted for"


# ----------------------------------------------------------------------------- remote-site rule
def test_remote_site_forms_its_own_hub_but_keeps_its_label():
    g = _tagged([(0, 0), (100, 0), (300_000, 0)], community_name=["Prudhoe Bay"] * 3,
                community_distance_km=[0.0, 0.0, 1078.2])
    hubs = aggregate_hubs(g, Params(group_by=["community"], remote_site_km=20))
    assert len(hubs) == 2
    by = hubs.set_index("hub_key")
    assert by.loc["PRUDHOE BAY", "num_facilities"] == 2 and by.loc["PRUDHOE BAY", "hub_kind"] == "community"
    assert by.loc["remote:2", "hub_kind"] == "remote_site" and by.loc["remote:2", "hub_community"] == "Prudhoe Bay"
    assert abs(by.loc["PRUDHOE BAY"].geometry.x - 50) < 1e-6, "the town hub no longer drags toward the remote site"


def test_remote_site_rule_off_by_default_and_without_distance():
    g = _tagged([(0, 0), (300_000, 0)], community_name=["Prudhoe Bay"] * 2, community_distance_km=[0.0, 1078.2])
    assert len(aggregate_hubs(g, Params(group_by=["community"]))) == 1
    g2 = _tagged([(0, 0), (300_000, 0)], community_name=["Prudhoe Bay"] * 2)
    assert len(aggregate_hubs(g2, Params(group_by=["community"], remote_site_km=20))) == 1


# ----------------------------------------------------------------------------- withhold pending review
def test_withhold_pending_review_is_an_on_off_flag(tmp_path):
    from mmnet.config import PipelineConfig
    from mmnet.steps.consolidate import consolidate_facilities
    cols = {"id": "ast_facility_id", "community": "community_name", "delivery_method": "delivery_method",
            "total_capacity": "total_capacity", "longitude": "longitude", "latitude": "latitude",
            "record_id": "record_id", "qc_status": "qc_status"}
    cfg = PipelineConfig(roots={}, layers=[], raw={}, facility_columns=cols, capacity_columns=["total_capacity"],
                         routable_modes=["Road"])
    df = pd.DataFrame({"id": ["A", "B"], "record_id": ["{a}", "{b}"], "community": ["X", "Y"], "delivery_method": ["Road"] * 2,
                       "total_capacity": [100, 200], "longitude": [-150.0, -150.5], "latitude": [61.0, 61.0],
                       "qc_status": ["clean", "pending_review"]})
    p = tmp_path / "f.csv"; df.to_csv(p, index=False)
    on = consolidate_facilities(p, Params(withhold_pending_review=True), 4326, 3338, cfg)
    assert list(on["ast_facility_id"]) == ["A"] and list(on.attrs["withheld"]["record_id"]) == ["{b}"]
    off = consolidate_facilities(p, Params(withhold_pending_review=False), 4326, 3338, cfg)
    assert len(off) == 2 and len(off.attrs["withheld"]) == 0
