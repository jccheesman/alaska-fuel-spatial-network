"""The 2026-11 cost split: ocean / river barge rates by water class, barge landing fees by place.

Synthetic networks only; no rasters and no network of record are needed.
"""
from __future__ import annotations

import duckdb
import pandas as pd
import pytest

from friction_surface import friction_costs as fc
from friction_surface.friction_config import METERS_PER_MILE
from fuel_network import graph, landings

MILE = METERS_PER_MILE


def _network():
    """Anchorage (road port) -- ocean -- Nome (hub) ; ocean -- Wales (coastal village) ;
    Nenana (road port, on the Anchorage road system) -- river -- Tanana (river village)."""
    nodes = pd.DataFrame({
        "node_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        #            anc anc_w nome_w nome wales_w wales nen nen_w tan_w tan  far
        "x": [0, 100, 500_000, 500_100, 600_000, 600_100, 0, 100, 200_000, 200_100, 900_000],
        "y": [0, 0, 0, 0, 0, 0, 300_000, 300_000, 300_000, 300_000, 900_000],
    })
    edges = pd.DataFrame([
        # edge_id, from, to, class, length_m
        (1, 1, 2, "BargeRoadTransfer", 100.0),      # Anchorage landing
        (2, 2, 3, "Waterway", 100 * MILE),          # ocean
        (3, 3, 4, "BargeRoadTransfer", 100.0),      # Nome landing
        (4, 3, 5, "Waterway", 50 * MILE),           # ocean
        (5, 5, 6, "BargeAirTransfer", 100.0),       # Wales landing (barge to an airport node)
        (6, 1, 7, "Road", 200 * MILE),              # Anchorage -- Nenana road
        (7, 7, 8, "BargeRoadTransfer", 100.0),      # Nenana landing
        (8, 8, 9, "Waterway", 80 * MILE),           # river
        (9, 9, 10, "BargeRoadTransfer", 100.0),     # Tanana landing
        (10, 9, 5, "Waterway", 10 * MILE),          # a river-mouth edge, half river half marine
    ], columns=["edge_id", "from_node", "to_node", "edge_class", "length_m"])
    hubs = pd.DataFrame({"node_id": [1, 4, 6, 7, 10], "hub_community": ["Anchorage", "Nome", "Wales", "Nenana", "Tanana"]})
    water = pd.DataFrame({"edge_id": [2, 4, 8, 10], "marine_frac": [1.0, 1.0, 0.0, 0.5], "river_frac": [0.0, 0.0, 1.0, 0.5]})
    return nodes, edges, hubs, water


def test_waterway_rates_marine_river_and_mixed():
    ocean, river = fc.BASELINE_RATES_PER_GALLON_MILE["Barge"], fc.BASELINE_RATES_PER_GALLON_MILE["BargeRiver"]
    got = graph.waterway_rates(pd.Series([1.0, 0.0, 0.5, None]), pd.Series([0.0, 1.0, 0.5, None]))
    assert got.tolist() == pytest.approx([ocean, river, (ocean + river) / 2, ocean])


def test_ocean_rate_is_not_the_retired_blend():
    assert fc.BASELINE_RATES_PER_GALLON_MILE["Barge"] < 0.0005 < fc.BASELINE_RATES_PER_GALLON_MILE["BargeRiver"]
    assert set(fc.RATE_STATUS) == set(fc.BASELINE_RATES_PER_GALLON_MILE)


def test_landing_classes_by_table_road_system_and_water_class():
    nodes, edges, hubs, water = _network()
    got = landings.classify_landings(nodes, edges, hubs, water, table={"nome": "hub"}).set_index("edge_id")
    assert got.loc[1, ["landing_class", "rule"]].tolist() == ["road_port", "road_system"]     # Anchorage
    assert got.loc[3, ["landing_class", "rule", "place"]].tolist() == ["hub", "table", "Nome"]
    assert got.loc[5, ["landing_class", "rule"]].tolist() == ["coastal_village", "water_class"]  # Wales: mean river share 0.25
    assert got.loc[7, ["landing_class", "rule"]].tolist() == ["road_port", "road_system"]     # Nenana is on the road system
    assert got.loc[9, ["landing_class", "rule"]].tolist() == ["river_village", "water_class"]  # Tanana: mean river share 0.75
    assert set(got.index) == {1, 3, 5, 7, 9}


def test_table_beats_the_road_system_rule():
    nodes, edges, hubs, water = _network()
    got = landings.classify_landings(nodes, edges, hubs, water, table={"nenana": "hub"}).set_index("edge_id")
    assert got.loc[7, "landing_class"] == "hub"


def test_landing_without_water_class_is_reported():
    nodes, edges, hubs, water = _network()
    got = landings.classify_landings(nodes, edges, hubs, water.iloc[0:0], table={}).set_index("edge_id")
    assert got.loc[5, ["landing_class", "rule"]].tolist() == ["coastal_village", "no_water_class"]


def test_landing_table_rejects_an_unknown_class(tmp_path):
    p = tmp_path / "landing_classes.csv"
    p.write_text("community,landing_class,evidence,source,status,reviewer,date\nNome,harbour,x,y,approved,JC,2026-11-18\n")
    with pytest.raises(ValueError, match="unknown landing_class"):
        landings.load_landing_table(p)
    p.write_text("community,landing_class,evidence,source,status,reviewer,date\n"
                 "Nome,hub,x,y,approved,JC,2026-11-18\nBethel,hub,x,y,rejected,JC,2026-11-18\nKotzebue,hub,x,y,proposed,,2026-11-18\n")
    assert landings.load_landing_table(p) == {"nome": "hub", "kotzebue": "hub"}      # rejected rows are ignored
    assert landings.load_landing_table(tmp_path / "absent.csv") == {}


def test_the_tracked_landing_table_is_valid():
    table = landings.load_landing_table()
    assert table and set(table.values()) <= set(fc.LANDING_CLASS_FEES)


def test_fee_inference_uses_the_class_and_falls_back():
    edges = pd.DataFrame({"edge_id": [1, 2, 3], "from_node": [0, 0, 0], "to_node": [1, 1, 1],
                          "edge_class": ["BargeRoadTransfer", "BargeAirTransfer", "IceRoadRoadTransfer"]})
    fallback = fc.INTERMODAL_TRANSFER_FEES[("barge", "overland")]["total"]
    assert fc.infer_transfer_fees(edges).to_dict() == {1: fallback, 2: fallback, 3: 0.022}
    got = fc.infer_transfer_fees(edges, {1: "hub", 3: "hub"}).to_dict()          # class on a non-landing edge is ignored
    assert got == {1: fc.LANDING_CLASS_FEES["hub"]["total"], 2: fallback, 3: 0.022}
    with pytest.raises(KeyError, match="Unknown landing class"):
        fc.infer_transfer_fees(edges, {1: "harbour"})


def _db(tmp_path, with_water=True):
    nodes, edges, hubs, water = _network()
    db = tmp_path / "net.duckdb"
    con = duckdb.connect(str(db))
    con.register("n", nodes); con.register("e", edges); con.register("h", hubs); con.register("w", water)
    con.execute("CREATE TABLE network_nodes AS SELECT * FROM n")
    con.execute("CREATE TABLE network_edges AS SELECT * FROM e")
    con.execute("CREATE TABLE hub_members AS SELECT * FROM h")
    if with_water:
        con.execute("CREATE TABLE edge_water_class AS SELECT *, 0.0 AS notwater_frac, 'x' AS water_class FROM w")
    mode = {"Waterway": "Barge", "Road": "Road"}
    rows = [(int(e.edge_id), m, mode.get(e.edge_class, "Transfer"), 1.0, True)
            for e in edges.itertuples() for m in range(1, 13)]
    weights = pd.DataFrame(rows, columns=["edge_id", "month", "mode", "avg_friction", "passable"])
    con.register("wt", weights)
    con.execute("CREATE TABLE edge_month_weights AS SELECT * FROM wt")
    con.close()
    return db


def test_edge_costs_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(landings, "load_landing_table", lambda path=None: {"nome": "hub"})
    db = _db(tmp_path)
    costs = graph.build_edge_costs(db)
    july = costs[costs.month == 7].set_index("edge_id")["cost_per_gallon"]
    r = fc.BASELINE_RATES_PER_GALLON_MILE
    f = fc.LANDING_CLASS_FEES
    assert july[2] == pytest.approx(100 * r["Barge"])                    # ocean
    assert july[8] == pytest.approx(80 * r["BargeRiver"])                # river
    assert july[10] == pytest.approx(10 * (r["Barge"] + r["BargeRiver"]) / 2)   # river mouth
    assert july[6] == pytest.approx(200 * r["Road"])
    assert july[1] == f["road_port"]["total"] and july[3] == f["hub"]["total"]
    assert july[5] == f["coastal_village"]["total"] and july[9] == f["river_village"]["total"]
    # Anchorage -> Nome by sea: origin port + ocean miles + hub discharge
    assert july[1] + july[2] + july[3] == pytest.approx(0.01 + 100 * r["Barge"] + 0.12)
    assert len(costs) == 10 * 12 and costs["cost_per_gallon"].gt(0).all()


def test_edge_costs_need_the_water_class_table(tmp_path):
    db = _db(tmp_path, with_water=False)
    with pytest.raises(RuntimeError, match="edge_water_class is missing"):
        graph.build_edge_costs(db)
    costs = graph.build_edge_costs(db, require_water_class=False)       # synthetic use only
    july = costs[costs.month == 7].set_index("edge_id")["cost_per_gallon"]
    assert july[8] == pytest.approx(80 * fc.BASELINE_RATES_PER_GALLON_MILE["Barge"])
    assert july[3] == fc.INTERMODAL_TRANSFER_FEES[("barge", "overland")]["total"]
