"""Proximity policies + connect-to-giant — the "before-policies" and shore-landing pass.

These are the connection rules the Stage-03 assembler (:func:`mmnet.assemble.connect_multimodal`)
applies AFTER the anchor transfers, to fold the leftover pieces into the giant the way real bulk-fuel
logistics do — short noding-gap welds, mode-to-mode bridges, and coastal barge landings:

  * :func:`within_mode_connectors` — road↔road and ice↔ice **welds**: join each non-largest component
    of one mode to its nearest node in a *different* component of the same mode, when the gap ≤ ``tol``.
  * :func:`cross_mode_connectors` — ice↔road **bridges**: one closest-approach connector per from-mode
    component to the nearest to-mode node (caller gates on ``gap_m``).
  * :func:`connect_to_giant` — the **shore-landing** pass: join every still-disconnected piece to the
    GIANT where it is physically close (≤ ``max_dist``). Where the giant side is the waterway it is a
    coastal barge landing (``shore:Barge↔{Road,IceRoad}``); where it is road/ice it is a noding weld
    (``weld:to-giant``). This is the root-cause fix for near-misses like the North Slope, which sat a
    few hundred metres from the green waterway yet welded internally instead of reaching it.

Pure (numpy / scipy / networkx); operates on a node-coordinate array ``xy`` and an edge table with
integer ``from``/``to`` + a ``type`` column. The algorithms are deterministic (components and
candidate nodes sorted by id before each arg-min) so ties resolve identically across runs. Ported
verbatim from the validated road-ice / connect-via-ports research prototypes so the engine
reproduces that result exactly.
"""
from __future__ import annotations

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree


def _mode_node_ids(edges, mode: str) -> list[int]:
    """Sorted set of node ids touched by edges of this `type`."""
    sub = edges[edges["type"] == mode]
    return sorted(set(sub["from"]).union(sub["to"]))


def within_mode_connectors(edges, xy, mode: str, tol: float, extra_pairs=()):
    """One connector per non-largest `mode` component → nearest node in a DIFFERENT component, gap ≤ tol.

    Returns (from_node, to_node, gap_m) tuples. `extra_pairs` (already-added connectors of this mode)
    fold into the component computation so welds chain. Deterministic (sorted). The within-mode weld
    used for road↔road and ice↔ice.
    """
    ids = _mode_node_ids(edges, mode)
    if not ids:
        return []
    sub = edges[edges["type"] == mode]
    g = nx.Graph()
    g.add_nodes_from(ids)
    g.add_edges_from(zip(sub["from"].to_numpy(), sub["to"].to_numpy()))
    g.add_edges_from((a, b) for a, b, *_ in extra_pairs)
    comps = [sorted(c) for c in nx.connected_components(g)]
    comps.sort(key=lambda c: (len(c), c[0]), reverse=True)
    comp_of = {n: i for i, c in enumerate(comps) for n in c}
    tree = cKDTree(xy[ids])
    k = min(16, len(ids))
    out = []
    for ci, comp in enumerate(comps):
        if ci == 0:
            continue
        qd, qi = tree.query(xy[comp], k=k)
        qd = np.atleast_2d(qd)
        qi = np.atleast_2d(qi)
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


def cross_mode_connectors(edges, xy, from_mode: str, to_mode: str, prefer_dangle: bool = True):
    """One closest-approach connector per `from_mode` component → nearest `to_mode` node.

    Returns a list of dicts (sorted by gap): {comp, size, n_dangles, from_node, to_node, gap_m,
    used_dangle}. No tolerance is applied here — the caller gates on `gap_m`. The cross-mode bridge
    used for ice↔road.
    """
    sub = edges[edges["type"] == from_mode]
    g = nx.Graph()
    g.add_edges_from(zip(sub["from"].to_numpy(), sub["to"].to_numpy()))
    comps = [sorted(c) for c in nx.connected_components(g)]
    comps.sort(key=lambda c: (len(c), c[0]), reverse=True)
    to_ids = _mode_node_ids(edges, to_mode)
    if not to_ids or not comps:
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


def connect_to_giant(allxy, edge_pairs, node_ids, ww_offset: int,
                     road_ids: set, max_dist: float):
    """Join every still-disconnected SURFACE component to the giant within `max_dist` — one each.

    `node_ids` is the surface universe (road ∪ ice ∪ waterway) and `edge_pairs` the surface pre-giant
    edges (modes + waterway + barge transfers + before-policies) — air is excluded, because bulk fuel
    moves over the surface, not by plane. For each non-giant surface component, connect its nearest
    node to the nearest GIANT node when the gap ≤ `max_dist`. Where the giant node is a waterway node
    (id ≥ `ww_offset`) it is a coastal barge landing (`shore:Barge↔Road` / `shore:Barge↔IceRoad`, by
    whether the component node is road); otherwise a noding weld to the giant (`weld:to-giant`).

    Returns a list of (from_node, to_node, source) connectors. Single pass — deterministic (components
    and nodes sorted by id). Ported verbatim from 02_connect_via_ports.py:134-152.
    """
    if not max_dist:
        return []
    g = nx.Graph()
    g.add_nodes_from(node_ids)
    g.add_edges_from(edge_pairs)
    comps = sorted(nx.connected_components(g), key=len, reverse=True)
    if not comps:
        return []
    giant_nodes = np.array(sorted(comps[0]))
    gtree = cKDTree(allxy[giant_nodes])
    out = []
    for comp in comps[1:]:
        cl = np.array(sorted(comp))
        d, idx = gtree.query(allxy[cl])
        j = int(np.argmin(d))
        if float(d[j]) <= max_dist:
            a = int(cl[j])
            b = int(giant_nodes[int(idx[j])])
            if b >= ww_offset:                 # giant side is a waterway node → barge shore landing
                src = f"shore:Barge↔{'Road' if a in road_ids else 'IceRoad'}"
            else:                              # giant side is road/ice → noding gap to the giant
                src = "weld:to-giant"
            out.append((a, b, src))
    return out
