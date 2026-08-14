"""NetworkTables — the explicit, QGIS-writable analogue of an R sfnetwork.

Two GeoDataFrames: `nodes` (point geometry, integer index 0..N-1) and `edges` (linestring geometry
with integer `from`/`to` columns indexing into nodes). snkit's table shape is the single source of
truth for node ids; `to_nx()/from_nx()` round-trip to networkx for graph algorithms without a second
conversion library.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import networkx as nx
import pandas as pd


@dataclass
class NetworkTables:
    nodes: gpd.GeoDataFrame
    edges: gpd.GeoDataFrame

    # --- basic properties ------------------------------------------------
    @property
    def crs(self):
        """The nodes-layer CRS (the network's coordinate reference system)."""
        return self.nodes.crs

    @property
    def n_nodes(self) -> int:
        """Number of nodes."""
        return len(self.nodes)

    @property
    def n_edges(self) -> int:
        """Number of edges."""
        return len(self.edges)

    # --- graph round-trip ------------------------------------------------
    def to_nx(self) -> nx.Graph:
        """Build an undirected networkx graph. Node ids are the nodes index; node/edge attribute
        columns (minus geometry) become attributes. `length`/`length_m` is the default weight."""
        g = nx.Graph()
        for idx, row in self.nodes.drop(columns=self.nodes.geometry.name).iterrows():
            g.add_node(int(idx), **row.to_dict())
        f, t = self.edges["from"].to_numpy(), self.edges["to"].to_numpy()
        attr_cols = [c for c in self.edges.columns if c not in {"from", "to", self.edges.geometry.name}]
        recs = self.edges[attr_cols].to_dict("records")
        for u, v, attrs in zip(f, t, recs):
            g.add_edge(int(u), int(v), **attrs)
        return g

    @classmethod
    def from_parts(cls, nodes: gpd.GeoDataFrame, edges: gpd.GeoDataFrame) -> "NetworkTables":
        """Build a NetworkTables from node/edge GeoDataFrames (resets both indices to 0..N-1)."""
        nodes = nodes.reset_index(drop=True)
        return cls(nodes=nodes, edges=edges.reset_index(drop=True))

    # --- (de)serialization -----------------------------------------------
    def to_gpkg(self, stem: str | Path) -> tuple[Path, Path]:
        """Write two layers: <stem>__nodes.gpkg and <stem>__edges.gpkg (QGIS-openable)."""
        stem = Path(stem)
        nodes_path = stem.with_name(stem.name + "__nodes.gpkg")
        edges_path = stem.with_name(stem.name + "__edges.gpkg")
        nodes_path.parent.mkdir(parents=True, exist_ok=True)
        self.nodes.to_file(nodes_path, driver="GPKG")
        self.edges.to_file(edges_path, driver="GPKG")
        return nodes_path, edges_path

    @classmethod
    def from_gpkg(cls, stem: str | Path) -> "NetworkTables":
        """Load a NetworkTables from `<stem>__nodes.gpkg` + `<stem>__edges.gpkg`."""
        stem = Path(stem)
        nodes = gpd.read_file(stem.with_name(stem.name + "__nodes.gpkg"))
        edges = gpd.read_file(stem.with_name(stem.name + "__edges.gpkg"))
        return cls(nodes=nodes, edges=edges)

    def summary(self) -> dict:
        """Counts dict: `n_nodes`, `n_edges`, `n_components`, `n_hubs`."""
        n_comp = nx.number_connected_components(self.to_nx()) if self.n_nodes else 0
        is_hub = self.nodes["is_hub"] if "is_hub" in self.nodes.columns else pd.Series(dtype=bool)
        return {
            "n_nodes": self.n_nodes,
            "n_edges": self.n_edges,
            "n_components": n_comp,
            "n_hubs": int(is_hub.fillna(False).astype(bool).sum()),
        }
