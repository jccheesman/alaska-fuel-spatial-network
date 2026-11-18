"""fuel_network.landings — what kind of place does each barge landing sit at?

The barge-to-land fee is priced by the kind of place the barge lands at, not by one
value for every crossing (friction_costs.LANDING_CLASS_FEES, re-derived 2026-11):

    road_port        a landing on the road system (Anchorage, Valdez, Whittier, Nenana ...)
    hub              a remote line-haul hub or dock-served port (Nome, Bethel, Kotzebue ...)
    coastal_village  a coastal village served by small-barge delivery
    river_village    a river village served by river barge

Each BargeRoadTransfer / BargeAirTransfer edge is assigned one class. The rules, in order:

  1. TABLE. The place the landing serves is the NEAREST named hub within
     PLACE_RADIUS_M of the landing's land-side node. If that place is in the reviewed table
     inputs/network_qc/landing_classes.csv, the table's class wins (rule "table").
  2. ROAD SYSTEM. A land-side node on the same road component as Anchorage is a
     road_port (rule "road_system").
  3. WATER CLASS. Otherwise the landing is a village, river or coastal by the mean river
     share of the Waterway edges at its water-side node, from edge_water_class (workflow 03
     stage 05): river_frac >= RIVER_SHARE -> river_village, else coastal_village (rule
     "water_class"; "no_water_class" when the node has no classified edge, coastal assumed).

The classification only picks a fee. It does not move, add or remove any edge. A hub that sits
ON a water node has no landing edge and so pays no landing fee; that is a known gap, reported
by `summary()`.

Pure functions over DataFrames so they are testable without a database; `compute_landing_classes`
reads the DuckDB tables. Everything is EPSG:3338 metres.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

import repo_paths as rp
from friction_surface.friction_costs import LANDING_CLASS_FEES, LANDING_PRICED_TYPES

PLACE_RADIUS_M = 12_000.0       # a landing within this of a named hub serves that hub
RIVER_SHARE = 0.5               # mean river share at the water node that makes a river village
ROAD_CLASSES = ("Road", "RoadConnector")
TABLE_PATH = rp.INPUTS / "network_qc" / "landing_classes.csv"
APPROVED_STATUSES = ("proposed", "approved")      # "rejected" rows are ignored


def load_landing_table(path: Path | str = TABLE_PATH) -> dict[str, str]:
    """community (lower case) -> landing class, from the reviewed table. Absent file = empty."""
    path = Path(path)
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("status") or "").strip().lower() not in APPROVED_STATUSES:
                continue
            cls = row["landing_class"].strip()
            if cls not in LANDING_CLASS_FEES:
                raise ValueError(f"{path}: {row['community']!r} has unknown landing_class {cls!r}; "
                                 f"expected one of {sorted(LANDING_CLASS_FEES)}")
            out[row["community"].strip().lower()] = cls
    return out


class _UnionFind:
    def __init__(self):
        self.p: dict[int, int] = {}

    def find(self, a: int) -> int:
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def classify_landings(nodes: pd.DataFrame, edges: pd.DataFrame, hubs: pd.DataFrame,
                      water: pd.DataFrame, table: dict[str, str] | None = None,
                      radius_m: float = PLACE_RADIUS_M) -> pd.DataFrame:
    """Assign a landing class to every barge landing edge.

    Args:
        nodes: node_id, x, y.
        edges: edge_id, from_node, to_node, edge_class.
        hubs:  node_id, hub_community (one row per hub node and community name; may repeat).
        water: edge_id, river_frac (and marine_frac) for the Waterway edges (edge_water_class).
        table: community (lower case) -> landing class; None loads the reviewed table.

    Returns a DataFrame indexed by position with columns
    edge_id, landing_class, place, place_distance_m, rule.
    """
    table = load_landing_table() if table is None else table
    xy = nodes.set_index("node_id")[["x", "y"]]

    # --- road system component of Anchorage ---------------------------------------------
    uf = _UnionFind()
    for a, b in edges.loc[edges["edge_class"].isin(ROAD_CLASSES), ["from_node", "to_node"]].itertuples(index=False):
        uf.union(int(a), int(b))
    anchorage = hubs.loc[hubs["hub_community"].astype(str).str.lower() == "anchorage", "node_id"]
    anchorage_root = uf.find(int(anchorage.iloc[0])) if len(anchorage) else None

    # --- named hub points ----------------------------------------------------------------
    named = hubs.dropna(subset=["hub_community"]).drop_duplicates(["node_id", "hub_community"])
    named = named[named["node_id"].isin(xy.index)]
    hub_xy = xy.loc[named["node_id"]].to_numpy()
    hub_names = named["hub_community"].astype(str).to_numpy()
    tree = None
    if len(hub_xy):
        from scipy.spatial import cKDTree
        tree = cKDTree(hub_xy)

    # --- water side of each landing ---------------------------------------------------------
    ww = edges[edges["edge_class"] == "Waterway"]
    ww_nodes = set(ww["from_node"].astype(int)) | set(ww["to_node"].astype(int))
    incident: dict[int, list[int]] = {}
    for eid, a, b in ww[["edge_id", "from_node", "to_node"]].itertuples(index=False):
        incident.setdefault(int(a), []).append(int(eid))
        incident.setdefault(int(b), []).append(int(eid))
    river = water.set_index("edge_id")["river_frac"] if len(water) else pd.Series(dtype=float)

    rows = []
    landing = edges[edges["edge_class"].isin(LANDING_PRICED_TYPES)]
    for eid, a, b in landing[["edge_id", "from_node", "to_node"]].itertuples(index=False):
        a, b = int(a), int(b)
        if a in ww_nodes and b not in ww_nodes:
            water_node, land_node = a, b
        elif b in ww_nodes and a not in ww_nodes:
            water_node, land_node = b, a
        elif a in ww_nodes:               # both ends on water: take the first as water
            water_node, land_node = a, b
        else:                             # neither: no waterway at the landing (should not happen)
            water_node, land_node = None, a

        place, dist = None, np.nan
        if tree is not None and land_node in xy.index:
            d, i = tree.query(xy.loc[land_node].to_numpy())
            if d <= radius_m:
                place, dist = hub_names[i], float(d)

        if place is not None and place.lower() in table:
            cls, rule = table[place.lower()], "table"
        elif anchorage_root is not None and uf.find(land_node) == anchorage_root:
            cls, rule = "road_port", "road_system"
        else:
            shares = [river.get(e) for e in incident.get(water_node, [])] if water_node is not None else []
            shares = [s for s in shares if s is not None and not pd.isna(s)]
            if shares:
                cls = "river_village" if float(np.mean(shares)) >= RIVER_SHARE else "coastal_village"
                rule = "water_class"
            else:
                cls, rule = "coastal_village", "no_water_class"
        rows.append({"edge_id": int(eid), "landing_class": cls, "place": place,
                     "place_distance_m": dist, "rule": rule})
    return pd.DataFrame(rows, columns=["edge_id", "landing_class", "place", "place_distance_m", "rule"])


def compute_landing_classes(db_path: Path | str = rp.DUCKDB) -> pd.DataFrame:
    """Read the network tables from DuckDB and classify every barge landing."""
    import duckdb
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        nodes = con.execute("SELECT node_id, x, y FROM network_nodes").df()
        edges = con.execute("SELECT edge_id, from_node, to_node, edge_class FROM network_edges").df()
        have = {r[0] for r in con.execute("SELECT table_name FROM information_schema.tables").fetchall()}
        hubs = (con.execute("SELECT DISTINCT node_id, hub_community FROM hub_members").df()
                if "hub_members" in have else pd.DataFrame(columns=["node_id", "hub_community"]))
        if "edge_water_class" not in have:
            raise RuntimeError(
                "edge_water_class is missing from the database: the barge cost split needs the "
                "marine / river class of every Waterway edge. Run "
                "workflows/03_multimodal_join/05_edge_water_class.py first (it needs workflow 01's "
                "water_class_150m.tif).")
        water = con.execute("SELECT edge_id, marine_frac, river_frac FROM edge_water_class").df()
    finally:
        con.close()
    return classify_landings(nodes, edges, hubs, water)


def summary(landings: pd.DataFrame) -> str:
    """One-paragraph description for logs and reports."""
    if landings.empty:
        return "no barge landing edges"
    by = landings.groupby(["landing_class", "rule"]).size().unstack(fill_value=0)
    return "barge landings by class and rule:\n" + by.to_string()
