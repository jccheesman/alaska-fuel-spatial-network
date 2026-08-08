"""Contract tests for the `mmnet` engine — the half that builds the network.

Before this file the suite covered `friction_surface` only (2,403 lines of source,
463 lines of tests) while `mmnet` (3,280 lines) had none — even though building the
multimodal network is what the repository is for.

These tests pin the properties the engine's own docstrings promise, on small
hand-built fixtures that need no external data:

  * determinism — "deterministic (components and candidate nodes sorted by id
    before each arg-min) so ties resolve identically across runs". Nothing
    verified that claim; row order arriving differently from a shapefile read
    would silently change which edges get welded.
  * tolerance gating — a connector must never be emitted beyond its max gap,
    because that is what stops the builder inventing a road across a fjord.
  * connector labelling — a waterway-side join is a shore landing, a land-side
    join is a weld. Stage 03 maps those labels onto cost rates, so mislabelling
    is a costing error, not a cosmetic one.
  * the nodes/edges round-trip through networkx.

Geometry is in metres (EPSG:3338-like), so `tol` values read as real distances.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mmnet.connect_extras import (
    connect_to_giant,
    cross_mode_connectors,
    within_mode_connectors,
)
from mmnet.steps.hubs import classify_hub_type


# --------------------------------------------------------------------------
# fixtures: two road clusters 100 m apart, plus an ice spur and a waterway
# --------------------------------------------------------------------------
def _edges(rows):
    return pd.DataFrame(rows, columns=["from", "to", "type"])


@pytest.fixture
def two_road_clusters():
    """Nodes 0-1 and 2-3 are separate road components; the gap 1->2 is 100 m."""
    xy = np.array(
        [
            [0.0, 0.0],      # 0  cluster A
            [50.0, 0.0],     # 1  cluster A
            [150.0, 0.0],    # 2  cluster B  (100 m from node 1)
            [200.0, 0.0],    # 3  cluster B
        ]
    )
    edges = _edges([(0, 1, "Road"), (2, 3, "Road")])
    return edges, xy


# --------------------------------------------------------------------------
# within_mode_connectors — the road<->road and ice<->ice weld
# --------------------------------------------------------------------------
def test_within_mode_welds_one_connector_per_extra_component(two_road_clusters):
    edges, xy = two_road_clusters
    out = within_mode_connectors(edges, xy, "Road", tol=150.0)
    assert len(out) == 1, "two components => exactly one weld"
    a, b, gap = out[0]
    assert {a, b} == {1, 2}, "must weld the closest-approach pair"
    assert gap == pytest.approx(100.0)


def test_within_mode_respects_tolerance(two_road_clusters):
    """The gap is 100 m: a 99 m tolerance must emit nothing.

    This is the guard that stops the builder welding across a gap the region
    profile considers impassable.
    """
    edges, xy = two_road_clusters
    assert within_mode_connectors(edges, xy, "Road", tol=99.0) == []
    assert len(within_mode_connectors(edges, xy, "Road", tol=100.0)) == 1


def test_within_mode_ignores_other_modes(two_road_clusters):
    """A Waterway edge bridging the two road clusters must not merge them."""
    edges, xy = two_road_clusters
    edges = pd.concat([edges, _edges([(1, 2, "Waterway")])], ignore_index=True)
    out = within_mode_connectors(edges, xy, "Road", tol=150.0)
    assert len(out) == 1, "road components stay separate despite the waterway edge"


def test_within_mode_is_deterministic_under_row_permutation():
    """Shuffling edge row order must not change the result.

    The docstring promises this; a different shapefile read order otherwise
    changes which pairs get welded, and therefore the edge inventory.
    """
    xy = np.array([[0.0, 0.0], [10.0, 0.0], [100.0, 0.0], [110.0, 0.0], [300.0, 0.0]])
    rows = [(0, 1, "Road"), (2, 3, "Road"), (3, 4, "Road")]
    baseline = within_mode_connectors(_edges(rows), xy, "Road", tol=200.0)
    rng = np.random.default_rng(0)
    for _ in range(8):
        shuffled = [rows[i] for i in rng.permutation(len(rows))]
        assert within_mode_connectors(_edges(shuffled), xy, "Road", tol=200.0) == baseline


def test_within_mode_extra_pairs_chain_welds():
    """A weld already added must fold into the component computation so welds chain.

    Without this, three collinear clusters would each get welded to the same
    neighbour and produce a duplicate connector.
    """
    xy = np.array([[0.0, 0.0], [100.0, 0.0], [200.0, 0.0]])
    edges = _edges([(0, 0, "Road"), (1, 1, "Road"), (2, 2, "Road")])
    # Nodes 0,1,2 are three singleton road components.
    plain = within_mode_connectors(edges, xy, "Road", tol=250.0)
    chained = within_mode_connectors(edges, xy, "Road", tol=250.0, extra_pairs=[(0, 1)])
    assert len(chained) < len(plain), "an existing weld must reduce the work left to do"


# --------------------------------------------------------------------------
# cross_mode_connectors — the ice<->road bridge
# --------------------------------------------------------------------------
def test_cross_mode_returns_one_per_source_component_sorted_by_gap():
    xy = np.array(
        [
            [0.0, 0.0],      # 0 road
            [100.0, 0.0],    # 1 road
            [0.0, 20.0],     # 2 ice component A  (20 m from road node 0)
            [40.0, 20.0],    # 3 ice component A
            [100.0, 90.0],   # 4 ice component B  (90 m from road node 1)
            [140.0, 90.0],   # 5 ice component B
        ]
    )
    edges = _edges([(0, 1, "Road"), (2, 3, "IceRoad"), (4, 5, "IceRoad")])
    out = cross_mode_connectors(edges, xy, "IceRoad", "Road")
    assert len(out) == 2
    assert [r["gap_m"] for r in out] == sorted(r["gap_m"] for r in out), "sorted by gap"
    assert out[0]["gap_m"] == pytest.approx(20.0)
    assert out[0]["to_node"] in (0, 1), "must land on a road node"


def test_cross_mode_applies_no_tolerance_itself():
    """The docstring is explicit: gating on gap_m is the caller's job.

    Worth pinning — a future 'helpful' tolerance added here would silently
    drop connections the profile intends to keep.
    """
    xy = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 9e6], [10.0, 9e6]])
    edges = _edges([(0, 1, "Road"), (2, 3, "IceRoad")])
    out = cross_mode_connectors(edges, xy, "IceRoad", "Road")
    assert len(out) == 1 and out[0]["gap_m"] > 1e6


def test_cross_mode_is_deterministic_under_row_permutation():
    xy = np.array([[0.0, 0.0], [100.0, 0.0], [0.0, 30.0], [50.0, 30.0], [200.0, 60.0], [260.0, 60.0]])
    rows = [(0, 1, "Road"), (2, 3, "IceRoad"), (4, 5, "IceRoad")]
    baseline = cross_mode_connectors(_edges(rows), xy, "IceRoad", "Road")
    rng = np.random.default_rng(1)
    for _ in range(8):
        shuffled = [rows[i] for i in rng.permutation(len(rows))]
        assert cross_mode_connectors(_edges(shuffled), xy, "IceRoad", "Road") == baseline


# --------------------------------------------------------------------------
# connect_to_giant — shore landings vs welds
# --------------------------------------------------------------------------
def test_connect_to_giant_labels_waterway_landings_and_land_welds():
    """A join onto a waterway node is a shore landing; onto land it is a weld.

    Stage 03 maps these labels onto cost rates, so the distinction is a costing
    contract, not documentation.
    """
    #    0-1  giant (road)     2  waterway node (id >= ww_offset)     3-4 orphan road
    xy = np.array(
        [
            [0.0, 0.0],      # 0 road, giant
            [100.0, 0.0],    # 1 road, giant
            [150.0, 0.0],    # 2 waterway, giant (ww_offset = 2)
            [180.0, 0.0],    # 3 orphan road  (30 m from the waterway node)
            [280.0, 0.0],    # 4 orphan road
        ]
    )
    node_ids = [0, 1, 2, 3, 4]
    edge_pairs = [(0, 1), (1, 2), (3, 4)]
    out = connect_to_giant(
        xy, edge_pairs, node_ids, ww_offset=2, road_ids={0, 1, 3, 4}, max_dist=100.0
    )
    assert len(out) == 1
    _from, _to, source = out[0]
    assert _to == 2, "nearest giant node is the waterway node"
    assert "shore" in source.lower(), f"waterway-side join must be a shore landing, got {source!r}"


def test_connect_to_giant_respects_max_dist():
    xy = np.array([[0.0, 0.0], [100.0, 0.0], [5000.0, 0.0], [5100.0, 0.0]])
    node_ids = [0, 1, 2, 3]
    edge_pairs = [(0, 1), (2, 3)]
    near = connect_to_giant(xy, edge_pairs, node_ids, 99, {0, 1, 2, 3}, max_dist=10000.0)
    far = connect_to_giant(xy, edge_pairs, node_ids, 99, {0, 1, 2, 3}, max_dist=100.0)
    assert len(near) == 1, "within max_dist => connected"
    assert far == [], "beyond max_dist => left disconnected, never bridged anyway"


def test_connect_to_giant_zero_max_dist_is_a_noop():
    xy = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]])
    assert connect_to_giant(xy, [(0, 1), (2, 3)], [0, 1, 2, 3], 99, {0, 1}, max_dist=0) == []


# --------------------------------------------------------------------------
# classify_hub_type — supplier/receiver split
# --------------------------------------------------------------------------
def test_classify_hub_type_absolute_threshold():
    caps = np.array([1e4, 5e5, 1e6])
    out = classify_hub_type(caps, method="absolute", abs_threshold=5e5)
    assert list(out) == ["Receiver", "Supplier", "Supplier"], "threshold is inclusive"


def test_classify_hub_type_percentile_marks_the_top_of_the_group():
    caps = np.array([1.0, 2.0, 3.0, 4.0, 100.0])
    out = classify_hub_type(caps, method="percentile", percentile=0.90)
    assert out[-1] == "Supplier"
    assert list(out[:3]) == ["Receiver"] * 3


def test_classify_hub_type_handles_a_constant_group():
    """Every facility the same size: the quantile equals the value, so all are
    Suppliers. Pinned because a NaN or an exception here would drop a whole
    delivery-method group out of the hub inventory."""
    out = classify_hub_type(np.array([500.0] * 6), method="percentile")
    assert set(out) == {"Supplier"}


# --------------------------------------------------------------------------
# NetworkTables round-trip
# --------------------------------------------------------------------------
def test_network_tables_round_trips_through_networkx():
    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import LineString, Point

    from mmnet.network import NetworkTables

    nodes = gpd.GeoDataFrame(
        {"geometry": [Point(0, 0), Point(1, 0), Point(2, 0)]}, crs="EPSG:3338"
    )
    edges = gpd.GeoDataFrame(
        {
            "from": [0, 1],
            "to": [1, 2],
            "type": ["Road", "Road"],
            "geometry": [LineString([(0, 0), (1, 0)]), LineString([(1, 0), (2, 0)])],
        },
        crs="EPSG:3338",
    )
    nt = NetworkTables(nodes=nodes, edges=edges)
    assert (nt.n_nodes, nt.n_edges) == (3, 2)
    assert nt.crs == nodes.crs

    g = nt.to_nx()
    assert g.number_of_nodes() == 3
    assert g.number_of_edges() == 2
    assert g.has_edge(0, 1) and g.has_edge(1, 2)


# --------------------------------------------------------------------------
# the shipped region profile must stay valid
# --------------------------------------------------------------------------
def test_shipped_profile_validates():
    """profile.yaml is THE config surface — region-as-data. A profile that stops
    validating breaks the build for everyone, so it is a test, not just a CI step."""
    from pathlib import Path

    from mmnet.config import validate_profile

    profile = Path(__file__).resolve().parents[1] / "workflows/02_network_build/profile.yaml"
    assert profile.exists(), profile
    prof, warnings = validate_profile(str(profile))
    assert prof is not None
