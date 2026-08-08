"""Within-mode proximity core (shared with the road↔road study; mode-generic).

Same rule as the road study's `rr_core`, here defaulting to the IceRoad mode: merge components of one
mode whose closest approach ≤ a distance. Used to find the distance that minimizes ice components.
Operates on the built network (`output/03_network__{nodes,edges}.gpkg`).
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


def mode_components(edges, mode: str):
    """Return (sub_edges, node_ids, components[list,sorted-desc], comp_of[node->idx])."""
    sub = edges[edges["type"] == mode]
    ids = sorted(set(sub["from"]).union(sub["to"]))
    g = nx.Graph()
    g.add_edges_from(zip(sub["from"].to_numpy(), sub["to"].to_numpy()))
    comps = [sorted(c) for c in nx.connected_components(g)]
    comps.sort(key=lambda c: (len(c), c[0]), reverse=True)
    comp_of = {n: i for i, c in enumerate(comps) for n in c}
    return sub, ids, comps, comp_of


def component_min_distances(ids, xy, comp_of, k: int = 24):
    """{(ci,cj): min distance} between every pair of components reachable via k-NN, plus the
    representative node pair achieving it: {(ci,cj): (dist, from_node, to_node)}."""
    tree = cKDTree(xy[ids])
    K = min(k, len(ids))
    qd, qi = tree.query(xy[ids], k=K)
    qd = np.atleast_2d(qd); qi = np.atleast_2d(qi)
    node_comp = np.array([comp_of[n] for n in ids])
    best: dict = {}
    for i in range(len(ids)):
        ci = node_comp[i]
        for kk in range(1, K):
            cj = node_comp[qi[i, kk]]
            if cj != ci:
                key = (ci, cj) if ci < cj else (cj, ci)
                d = float(qd[i, kk])
                if key not in best or d < best[key][0]:
                    a, b = ids[i], ids[int(qi[i, kk])]
                    best[key] = (d, a, b) if ci < cj else (d, b, a)
    return best


def merge_at(comps, cc_best, tol):
    """(n_components, giant_nodes, giant_frac) after merging every pair with min distance ≤ tol."""
    sizes = np.array([len(c) for c in comps])
    g = nx.Graph(); g.add_nodes_from(range(len(comps)))
    g.add_edges_from(k for k, v in cc_best.items() if v[0] <= tol)
    supers = list(nx.connected_components(g))
    giant = max((int(sizes[list(s)].sum()) for s in supers), default=0)
    total = int(sizes.sum())
    return len(supers), giant, giant / max(total, 1)
