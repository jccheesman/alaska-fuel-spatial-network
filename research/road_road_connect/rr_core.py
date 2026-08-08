"""Road↔road proximity rule — single source of truth for the connection experiment.

Same idea as the ice study's `bridge_core`, applied WITHIN the road mode: connect each disconnected
road component to its closest OTHER road component, one connector per component, gated by a tolerance.
Because "nearest other component" chains, a single tolerance-gated pass transitively merges the stub
swarm. The far regional systems (200–900 km out) never qualify and stay isolated (they ride the
multimodal ferry/air anchors instead).

Operates on the built network (`output/03_network__{nodes,edges}.gpkg`): 0-based node ids, integer
`from`/`to`, a `type` column. This is the prototype of an engine within-mode weld if it ships.
"""

from __future__ import annotations

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

from _trace import ROOT  # noqa: E402

from mmnet.network import NetworkTables  # noqa: E402


def load_network(stem: str = "output/03_network"):
    nt = NetworkTables.from_gpkg(ROOT / stem)
    nodes = nt.nodes.sort_values("node_id").reset_index(drop=True)
    assert (nodes["node_id"].to_numpy() == np.arange(len(nodes))).all(), "node_id not 0..N-1"
    xy = np.c_[nodes.geometry.x.to_numpy(), nodes.geometry.y.to_numpy()]
    edges = nt.edges.copy()
    edges["from"] = edges["from"].astype(int)
    edges["to"] = edges["to"].astype(int)
    return nodes, edges, xy


def road_components(edges, mode: str = "Road"):
    """Return (sub_edges, node_ids, components[list,sorted-desc], comp_of[node->idx])."""
    sub = edges[edges["type"] == mode]
    ids = sorted(set(sub["from"]).union(sub["to"]))
    g = nx.Graph()
    g.add_edges_from(zip(sub["from"].to_numpy(), sub["to"].to_numpy()))
    comps = [sorted(c) for c in nx.connected_components(g)]
    comps.sort(key=lambda c: (len(c), c[0]), reverse=True)
    comp_of = {n: i for i, c in enumerate(comps) for n in c}
    return sub, ids, comps, comp_of


def closest_connectors(ids, xy, comps, comp_of, k: int = 16):
    """One closest-approach connector per non-backbone component → nearest node in a DIFFERENT component.

    Returns dicts sorted by gap: {comp, size, from_node, to_node, to_comp, to_backbone, gap_m}.
    No tolerance applied — the caller gates on gap_m.
    """
    tree = cKDTree(xy[ids])
    out = []
    for ci, comp in enumerate(comps):
        if ci == 0:                      # the backbone is the merge target, not a source
            continue
        arr = sorted(comp)
        qd, qi = tree.query(xy[arr], k=min(k, len(ids)))
        qd = np.atleast_2d(qd); qi = np.atleast_2d(qi)
        best, bf, bt = np.inf, -1, -1
        for li, nid in enumerate(arr):
            for kk in range(qi.shape[1]):
                other = ids[int(qi[li, kk])]
                if comp_of[other] != ci:        # first neighbour in a different component
                    if qd[li, kk] < best:
                        best, bf, bt = float(qd[li, kk]), nid, other
                    break
        out.append({"comp": ci, "size": len(comp), "from_node": int(bf), "to_node": int(bt),
                    "to_comp": comp_of.get(bt, -1), "to_backbone": comp_of.get(bt, -1) == 0,
                    "gap_m": best})
    out.sort(key=lambda r: r["gap_m"])
    return out


def apply_and_measure(ids, edges, comps, connectors, tol):
    """Add every connector with gap ≤ tol, return (n_components, backbone_nodes, backbone_frac)."""
    pairs = [(c["from_node"], c["to_node"]) for c in connectors if c["gap_m"] <= tol]
    g = nx.Graph()
    g.add_nodes_from(ids)
    road = edges[edges["type"] == "Road"]
    g.add_edges_from(zip(road["from"].to_numpy(), road["to"].to_numpy()))
    g.add_edges_from(pairs)
    cc = sorted(nx.connected_components(g), key=len, reverse=True)
    big = len(cc[0]) if cc else 0
    return len(cc), big, big / max(len(ids), 1), len(pairs)
