"""The proximity-bridge rule — single source of truth for the sandbox.

This is the prototype of the engine helper `mmnet.assemble._proximity_bridges`. Keep the rule here so
`01_gaps`, `02_candidates_map`, and `03_sensitivity` all evaluate the EXACT rule that will ship:

  For each disconnected component of `from_mode`, connect it to `to_mode` at their single CLOSEST
  approach — one connector per component — attaching at a degree-1 dangle endpoint of the component
  when `prefer_dangle` (the natural ramp end). The connector is emitted only when the real gap is
  <= a tolerance (applied by the caller via `gap_m`). Deterministic: components and candidate nodes
  are sorted by node id before the arg-min, so ties resolve identically across runs.

Operates on the built network tables (`output/03_network__{nodes,edges}.gpkg`): node ids are 0-based
and index the node table; edges carry integer `from`/`to` + a `type` column (Road, IceRoad, ...).
"""

from __future__ import annotations

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

from _trace import ROOT  # noqa: E402

from mmnet.network import NetworkTables  # noqa: E402


def load_network(stem: str = "output/03_network"):
    """Return (nodes_sorted, edges, xy) where `xy[node_id]` is the (x, y) of that node."""
    nt = NetworkTables.from_gpkg(ROOT / stem)
    nodes = nt.nodes.sort_values("node_id").reset_index(drop=True)
    assert (nodes["node_id"].to_numpy() == np.arange(len(nodes))).all(), "node_id not 0..N-1"
    xy = np.c_[nodes.geometry.x.to_numpy(), nodes.geometry.y.to_numpy()]
    edges = nt.edges.copy()
    edges["from"] = edges["from"].astype(int)
    edges["to"] = edges["to"].astype(int)
    return nodes, edges, xy


def mode_subgraph(edges, mode: str):
    """Undirected graph + deterministic component list (largest first) for one edge `type`."""
    sub = edges[edges["type"] == mode]
    g = nx.Graph()
    g.add_edges_from(zip(sub["from"].to_numpy(), sub["to"].to_numpy()))
    comps = [sorted(c) for c in nx.connected_components(g)]
    comps.sort(key=lambda c: (len(c), c[0]), reverse=True)   # size desc, then id — deterministic
    return g, comps, sub


def mode_node_ids(edges, mode: str) -> list[int]:
    """Sorted set of node ids touched by edges of this `type`."""
    sub = edges[edges["type"] == mode]
    return sorted(set(sub["from"]).union(sub["to"]))


def candidate_connectors(edges, xy, from_mode: str, to_mode: str, prefer_dangle: bool = True):
    """One closest-approach connector per `from_mode` component → nearest `to_mode` node.

    Returns a list of dicts (sorted by gap): {comp, size, n_dangles, from_node, to_node, gap_m,
    used_dangle}. No tolerance is applied here — the caller gates on `gap_m`.
    """
    g, comps, _ = mode_subgraph(edges, from_mode)
    to_ids = mode_node_ids(edges, to_mode)
    if not to_ids:
        return []
    tree = cKDTree(xy[to_ids])
    deg = dict(g.degree())
    out = []
    for ci, comp in enumerate(comps):
        dangles = [n for n in comp if deg.get(n, 0) == 1]
        used_dangle = bool(prefer_dangle and dangles)
        cand = sorted(dangles) if used_dangle else sorted(comp)
        dist, idx = tree.query(xy[cand])
        dist = np.atleast_1d(dist)
        idx = np.atleast_1d(idx)
        j = int(np.argmin(dist))
        out.append({
            "comp": ci, "size": len(comp), "n_dangles": len(dangles),
            "from_node": int(cand[j]), "to_node": int(to_ids[int(idx[j])]),
            "gap_m": float(dist[j]), "used_dangle": used_dangle,
        })
    out.sort(key=lambda r: r["gap_m"])
    return out


def giant_fraction(edges, n_nodes: int, extra_pairs=()):
    """Largest-connected-component fraction over ALL edges plus optional `extra_pairs` (from,to)."""
    g = nx.Graph()
    g.add_nodes_from(range(n_nodes))
    g.add_edges_from(zip(edges["from"].to_numpy(), edges["to"].to_numpy()))
    g.add_edges_from((a, b) for a, b, *_ in extra_pairs)
    comps = sorted(nx.connected_components(g), key=len, reverse=True)
    giant = len(comps[0]) if comps else 0
    return len(comps), giant / max(n_nodes, 1)


def within_mode_connectors(edges, xy, mode: str, tol: float, extra_pairs=()):
    """One connector per non-largest `mode` component → nearest node in a DIFFERENT component, gap ≤ tol.

    Returns (from_node, to_node, gap_m) tuples. `extra_pairs` (already-added connectors of this mode)
    are folded into the component computation so welds chain. Deterministic (sorted). This is the
    within-mode weld used for road↔road and ice↔ice.
    """
    ids = mode_node_ids(edges, mode)
    sub = edges[edges["type"] == mode]
    g = nx.Graph(); g.add_nodes_from(ids)
    g.add_edges_from(zip(sub["from"].to_numpy(), sub["to"].to_numpy()))
    g.add_edges_from((a, b) for a, b, *_ in extra_pairs)
    comps = [sorted(c) for c in nx.connected_components(g)]
    comps.sort(key=lambda c: (len(c), c[0]), reverse=True)
    comp_of = {n: i for i, c in enumerate(comps) for n in c}
    tree = cKDTree(xy[ids]); K = min(16, len(ids))
    out = []
    for ci, comp in enumerate(comps):
        if ci == 0:
            continue
        qd, qi = tree.query(xy[comp], k=K)
        qd = np.atleast_2d(qd); qi = np.atleast_2d(qi)
        best = (np.inf, -1, -1)
        for li, nid in enumerate(sorted(comp)):
            for kk in range(qi.shape[1]):
                other = ids[int(qi[li, kk])]
                if comp_of[other] != ci:
                    if qd[li, kk] < best[0]:
                        best = (float(qd[li, kk]), nid, other)
                    break
        if best[0] <= tol:
            out.append((int(best[1]), int(best[2]), best[0]))
    return out


def component_graph(edges, xy, modes=("IceRoad", "Road"), max_edge_m=40000.0):
    """Meta-graph over all components of the given `modes`: nodes = ('I'/'R', idx), edges = exact min
    distance between component point sets (only kept if < `max_edge_m`). Returns (meta_graph, comps)
    where comps[(tag,idx)] is the sorted node-id list. Used for the bottleneck/minimax chain analysis."""
    tagmap = {"IceRoad": "I", "Road": "R"}
    comps = {}
    pts = {}
    for mode in modes:
        _, cl, _ = mode_subgraph(edges, mode)
        for k, c in enumerate(cl):
            key = (tagmap[mode], k)
            comps[key] = c
            pts[key] = xy[np.array(c)]
    trees = {k: cKDTree(p) for k, p in pts.items()}
    keys = list(comps)
    meta = nx.Graph(); meta.add_nodes_from(keys)
    # restrict pairwise work to northern components + the backbone to stay fast
    north = {k for k in keys if pts[k][:, 1].max() > 2.10e6} | {("R", 0)}
    nl = [k for k in north if k in comps]
    for i in range(len(nl)):
        for j in range(i + 1, len(nl)):
            a, b = nl[i], nl[j]
            w = float(trees[a].query(pts[b])[0].min())
            if w < max_edge_m:
                meta.add_edge(a, b, w=w)
    return meta, comps


def bottleneck_path(meta, src, dst):
    """Minimax (widest-path) from src to dst: minimize the largest single edge. Returns (bottleneck_m,
    path[list of meta-nodes]) or (None, None)."""
    import heapq
    best = {src: 0.0}; prev = {}; pq = [(0.0, src)]
    while pq:
        b, u = heapq.heappop(pq)
        if u == dst:
            break
        if b > best.get(u, float("inf")):
            continue
        for v in meta[u]:
            nb = max(b, meta[u][v]["w"])
            if nb < best.get(v, float("inf")):
                best[v] = nb; prev[v] = u; heapq.heappush(pq, (nb, v))
    if dst != src and dst not in prev:
        return None, None
    path = [dst]
    while path[-1] != src:
        path.append(prev[path[-1]])
    return best.get(dst), path[::-1]
