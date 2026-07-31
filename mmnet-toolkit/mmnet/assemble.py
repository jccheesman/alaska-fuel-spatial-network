"""The Python connect assembler — hub aggregation/snapping + intermodal connection.

Given the per-mode lines the R / sfnetworks oracle has **noded** (the hard part), Python owns the
rest of the build. There is no redundancy with R: R nodes the geometry, Python connects it once.

:func:`connect_multimodal` is the current (no-redundancy) entry point used by
:func:`mmnet.build.build_network`. It derives the global node table from R's noded edge endpoints
(NO `unary_union` re-noding), then with spatial indices (`sjoin_nearest`, not brute-force loops):

  1. snap every Stage-02 HUB to its nearest GROUND node (Road ∪ Ice Road);
  2. add intermodal Transfer edges at the profile's ANCHORS (ports → barge↔road) where an anchor is
     within `max_dist` of both modes' nodes (airports SNAP onto the road upstream — a shared node);
  3. label connected components.

Modes connect ONLY at real anchors — a component with no anchor (ice roads, port-less barge) stays
isolated rather than joined by a fabricated edge.

Pure (geopandas / networkx / shapely); region-agnostic via the `road_types` / `transfers` /
`anchors` arguments derived from the profile.
"""
from __future__ import annotations

import geopandas as gpd


def snap_to_roads(hubs: gpd.GeoDataFrame, roads: gpd.GeoDataFrame,
                  dist_col: str = "road_snap_dist_m") -> gpd.GeoDataFrame:
    """Snap every hub onto the nearest point of the ROAD backbone, regardless of mode."""
    from shapely.ops import nearest_points

    h = hubs.copy().reset_index(drop=True)
    # reset roads too so sjoin's `index_right` is positional (0..n-1) and lines
    # up with roads.geometry.iloc[ri] below — a gapped index would mis-snap.
    roads = roads.reset_index(drop=True)
    j = gpd.sjoin_nearest(h[["geometry"]], roads[["geometry"]], how="left", distance_col="_d")
    j = j.sort_values("_d").groupby(level=0).first()
    geoms, dists = [], []
    for i in range(len(h)):
        ri = int(j.loc[i, "index_right"]); d = float(j.loc[i, "_d"])
        geoms.append(nearest_points(h.geometry.iloc[i], roads.geometry.iloc[ri])[1])
        dists.append(d)
    out = h.copy()
    out["geometry"] = geoms
    out[dist_col] = dists
    return gpd.GeoDataFrame(out, geometry="geometry", crs=h.crs)


def connect_multimodal(r_edges: gpd.GeoDataFrame, hubs: gpd.GeoDataFrame, road_types: set,
                       transfers: list, anchors: dict,
                       snap_types: set | None = None, node_tol: float = 1.0,
                       waterway: gpd.GeoDataFrame | None = None, waterway_label: str = "Waterway",
                       waterway_node_tol: float = 50.0, bridges: list | None = None,
                       connect_max_dist: float = 0.0):
    """Connect R's noded edges into one multimodal network — fast, spatial-indexed, once.

    This is the no-redundancy connector: R has already noded each mode's lines, so we DERIVE the
    global node table from the edge endpoints (no `unary_union` re-noding) and connect with spatial
    indices instead of brute-force loops:

      1. nodes = unique rounded edge endpoints; edges keep R's noded geometry + `type`. When a
         `waterway` layer is supplied it is noded here by rounding its vertices to `waterway_node_tol`
         (50 m), its node ids OFFSET past the road/ice/air nodes — the marine network is noded in
         Python (not R) so its node table reproduces the validated research scheme exactly.
      2. snap each Stage-02 hub to its nearest GROUND node (`sjoin_nearest`), where the ground
         surface is `snap_types` — the profile's snap-target layers (Road ∪ Ice Road); falls back
         to `road_types`. Records `snap_surface` (e.g. "Road", "IceRoad", "IceRoad+Road") per hub.
      3. anchor transfers: for each rule, add a Transfer edge between the nearest from-mode node and
         nearest to-mode node of each anchor point, when both are within `max_dist` (ports/barge-hubs →
         barge↔road & barge↔ice). Airports are NOT a transfer — they SNAP onto the road upstream
         (`build._snap_airways_to_road`), so air shares a node with road.
      3b. proximity `bridges` (before-policies): road↔road / ice↔ice welds (within-mode) and ice↔road
          bridges (cross-mode), each a short connector when the gap ≤ the rule's `max_dist`.
      3c. connect-to-giant (`connect_max_dist` > 0): join every still-disconnected piece to the GIANT
          where it is physically close — a coastal barge landing (`shore:Barge↔*`) when the giant side
          is the waterway, else a noding weld (`weld:to-giant`). The North-Slope fix.
      4. label connected components.

    Modes connect at real anchors + the proximity/shore policies; a component beyond every policy's
    reach stays isolated rather than joined by a fabricated long edge. Returns (nodes_gdf, edges_gdf,
    summary). Node ids are 0-based to match NetworkTables.to_nx.
    """
    import networkx as nx
    import numpy as np
    import pandas as pd
    from shapely.geometry import LineString, Point

    from .connect_extras import connect_to_giant, cross_mode_connectors, within_mode_connectors

    crs = r_edges.crs

    # 1. global node table from edge endpoints (rounded) — no re-noding.
    coord_id: dict = {}
    coords: list = []

    def _nid(xy):
        k = (round(xy[0] / node_tol) * node_tol, round(xy[1] / node_tol) * node_tol)
        if k not in coord_id:
            coords.append(k)
            coord_id[k] = len(coords) - 1          # 0-based
        return coord_id[k]

    edge_rows = []
    for geom, etype in zip(r_edges.geometry, r_edges["type"]):
        if geom is None or geom.is_empty:
            continue
        cs = list(geom.coords)
        a, b = _nid(cs[0]), _nid(cs[-1])
        if a != b:
            edge_rows.append({"from": a, "to": b, "type": etype, "source": etype, "geometry": geom})

    # 1b. waterway (Python-noded by rounding to `waterway_node_tol`): its node ids are OFFSET past the
    #     road/ice/air nodes, so the marine network reproduces the research node table exactly. The
    #     coastal/Arctic spines are already a clean network — R's planar subdivision is not needed.
    ww_offset = len(coords)
    if waterway is not None and len(waterway):
        wkey: dict = {}

        def _wid(xy):
            k = (round(xy[0] / waterway_node_tol), round(xy[1] / waterway_node_tol))
            if k not in wkey:
                wkey[k] = len(coords)
                coords.append((k[0] * waterway_node_tol, k[1] * waterway_node_tol))
            return wkey[k]

        for geom in waterway.geometry:
            if geom is None or geom.is_empty:
                continue
            parts = [geom] if geom.geom_type == "LineString" else list(geom.geoms)
            for ln in parts:
                cs = [_wid(c) for c in ln.coords]
                for a, b in zip(cs[:-1], cs[1:]):
                    if a != b:
                        edge_rows.append({"from": a, "to": b, "type": waterway_label,
                                          "source": waterway_label,
                                          "geometry": LineString([coords[a], coords[b]])})

    node_pt = [Point(c) for c in coords]
    nodes_gdf = gpd.GeoDataFrame({"node_id": list(range(len(coords)))}, geometry=node_pt, crs=crs)

    # node ids per edge type (for the ground backbone + per-mode transfer endpoints).
    ids_by_type: dict = {}
    for e in edge_rows:
        ids_by_type.setdefault(e["type"], set()).update((e["from"], e["to"]))
    # ground surface hubs may snap onto: profile snap-target layers (Road ∪ Ice Road), else road.
    snap_types = set(snap_types) if snap_types else set(road_types)
    snap_ids = set().union(*[ids_by_type.get(t, set()) for t in snap_types]) if snap_types else set()

    def _nodes_subset(ids):
        sub = nodes_gdf.iloc[sorted(ids)][["node_id", "geometry"]].copy() if ids else \
            nodes_gdf.iloc[:0][["node_id", "geometry"]].copy()
        return sub

    snap_nodes = _nodes_subset(snap_ids)

    # 2. snap hubs to nearest GROUND node (road ∪ ice road), recording which surface they land on.
    for col in ("is_hub", "hub_id", "delivery_method", "hub_type", "total_hub_capacity", "snap_surface"):
        nodes_gdf[col] = False if col == "is_hub" else None
    hub_attr_cols = [c for c in ("hub_id", "delivery_method", "hub_type", "total_hub_capacity")
                     if hubs is not None and c in hubs.columns]
    if hubs is not None and len(hubs) and len(snap_nodes):
        h = hubs[["geometry", *hub_attr_cols]].copy()
        j = gpd.sjoin_nearest(h, snap_nodes, how="left")
        j = j[~j.index.duplicated(keep="first")]
        for _, row in j.iterrows():
            ni = int(row["node_id"])
            nodes_gdf.loc[ni, "is_hub"] = True
            for c in hub_attr_cols:
                nodes_gdf.loc[ni, c] = row.get(c)
            surfaces = [t for t in sorted(snap_types) if ni in ids_by_type.get(t, set())]
            nodes_gdf.loc[ni, "snap_surface"] = "+".join(surfaces) or None

    # 3. anchor transfers (ports/barge-hubs → barge↔road & barge↔ice). Airports snap to road upstream.
    transfer_rows = []
    seen_pairs: set = set()
    for tr in transfers:
        an = anchors.get(tr["anchor"])
        if an is None or not len(an):
            continue
        fr = _nodes_subset(ids_by_type.get(tr["from_type"], set()))
        to = _nodes_subset(ids_by_type.get(tr["to_type"], set()))
        if not len(fr) or not len(to):
            continue
        a = an[["geometry"]].reset_index(drop=True)
        jf = gpd.sjoin_nearest(a, fr.rename(columns={"node_id": "f_node"}), how="left", distance_col="_df")
        jf = jf[~jf.index.duplicated(keep="first")]
        jt = gpd.sjoin_nearest(a, to.rename(columns={"node_id": "t_node"}), how="left", distance_col="_dt")
        jt = jt[~jt.index.duplicated(keep="first")]
        for idx in a.index:
            if float(jf.loc[idx, "_df"]) > tr["max_dist"] or float(jt.loc[idx, "_dt"]) > tr["max_dist"]:
                continue
            fn, tn = int(jf.loc[idx, "f_node"]), int(jt.loc[idx, "t_node"])
            key = (min(fn, tn), max(fn, tn))
            if fn == tn or key in seen_pairs:
                continue
            seen_pairs.add(key)
            transfer_rows.append({"from": fn, "to": tn, "type": "Transfer", "source": tr["anchor"],
                                  "geometry": LineString([node_pt[fn], node_pt[tn]])})

    allxy = np.asarray(coords, dtype=float)

    def _add_conn(fn, tn, etype, src, rows):
        key = (min(fn, tn), max(fn, tn))
        if fn != tn and key not in seen_pairs:
            seen_pairs.add(key)
            rows.append({"from": int(fn), "to": int(tn), "type": etype, "source": src,
                         "geometry": LineString([node_pt[fn], node_pt[tn]])})

    # 3b. proximity bridges (before-policies): road↔road / ice↔ice welds + ice↔road bridges. Each rule
    #     runs on the base mode edges (waterway/transfers excluded by the per-mode `type` filter).
    bridge_rows = []
    if bridges:
        edf = pd.DataFrame([(e["from"], e["to"], e["type"]) for e in edge_rows],
                           columns=["from", "to", "type"])
        for br in bridges:
            ft, tt, md = br["from_type"], br["to_type"], float(br["max_dist"])
            if ft == tt:                       # within-mode weld (road↔road, ice↔ice)
                for a, b, _ in within_mode_connectors(edf, allxy, ft, md):
                    _add_conn(a, b, "Bridge", f"weld:{ft}", bridge_rows)
            else:                              # cross-mode bridge (ice↔road)
                for c in cross_mode_connectors(edf, allxy, ft, tt):
                    if c["gap_m"] <= md:
                        _add_conn(c["from_node"], c["to_node"], "Bridge", f"bridge:{ft}→{tt}", bridge_rows)

    # 3c. connect-to-giant: join every still-disconnected SURFACE piece to the giant within
    #     connect_max_dist — a coastal barge landing (shore:Barge↔*) where it meets the waterway, else a
    #     noding weld. The giant is the SURFACE network (road ∪ ice ∪ waterway); air is excluded, because
    #     bulk fuel moves over the surface — a village reachable only by plane still needs a fuel route.
    shore_rows = []
    if connect_max_dist:
        road_ids = set().union(*[ids_by_type.get(t, set()) for t in road_types]) if road_types else set()
        surface_types = set(road_types) | set(snap_types) | {waterway_label}
        surface_ids = set().union(*[ids_by_type.get(t, set()) for t in surface_types])
        pre_pairs = [(e["from"], e["to"]) for e in (edge_rows + transfer_rows + bridge_rows)
                     if e["from"] in surface_ids and e["to"] in surface_ids]
        for a, b, src in connect_to_giant(allxy, pre_pairs, surface_ids, ww_offset, road_ids, connect_max_dist):
            etype = "Transfer" if src.startswith("shore") else "Bridge"
            _add_conn(a, b, etype, src, shore_rows)

    # 4. components + assemble outputs. Modes connect at real anchors + the proximity/shore policies; a
    #    component beyond every policy's reach stays isolated rather than joined by a fabricated edge.
    def _components(rows):
        g = nx.Graph()
        g.add_nodes_from(range(len(coords)))
        g.add_edges_from((e["from"], e["to"]) for e in rows)
        comps = sorted(nx.connected_components(g), key=len, reverse=True)
        return comps

    all_rows = edge_rows + transfer_rows + bridge_rows + shore_rows
    comps_a = _components(all_rows)
    giant_a = comps_a[0] if comps_a else set()
    comp_of = {n: ci for ci, c in enumerate(comps_a, 1) for n in c}
    nodes_gdf["component"] = [comp_of.get(i) for i in range(len(coords))]
    nodes_gdf["is_giant"] = [i in giant_a for i in range(len(coords))]

    edges_gdf = gpd.GeoDataFrame(all_rows, geometry="geometry", crs=crs)
    n = max(len(nodes_gdf), 1)
    summary = {
        "n_nodes": len(nodes_gdf), "n_edges": len(edges_gdf),
        "edge_types": edges_gdf["type"].value_counts().to_dict(),
        "n_components": len(comps_a), "giant_frac": round(len(giant_a) / n, 3),
        "n_transfers": len(transfer_rows),
        "n_waterway": sum(1 for e in edge_rows if e["type"] == waterway_label),
        "n_bridges": len(bridge_rows), "n_shore": len(shore_rows),
        "n_hubs": int(nodes_gdf["is_hub"].fillna(False).astype(bool).sum()),
    }
    return nodes_gdf, edges_gdf, summary


def _label_components(nodes, edges):
    """Recompute `component` (1-based, size-ranked) + `is_giant` on `nodes` from `edges`.

    Mirrors :func:`connect_multimodal` phase 4 exactly: a graph over every node id (row order) plus
    the edge `from`/`to` pairs; components sorted by size (largest = the giant = component 1).
    """
    import networkx as nx

    g = nx.Graph()
    g.add_nodes_from(range(len(nodes)))
    g.add_edges_from(zip(edges["from"].astype(int), edges["to"].astype(int)))
    comps = sorted(nx.connected_components(g), key=len, reverse=True)
    giant = comps[0] if comps else set()
    comp_of = {n: ci for ci, c in enumerate(comps, 1) for n in c}
    out = nodes.copy()
    out["component"] = [comp_of.get(i) for i in range(len(out))]
    out["is_giant"] = [i in giant for i in range(len(out))]
    return out, len(comps), len(giant)


def join_components_to_giant(nodes: gpd.GeoDataFrame, edges: gpd.GeoDataFrame, max_dist: float,
                             connector_type: str = "Join", connector_source: str = "join:to-giant"):
    """Join every non-giant component to the giant by a straight connector when it is within reach.

    Stage 04 — the distance-driven final join. For each connected component that is NOT the giant,
    find its nearest node to the nearest giant node (a straight-line gap, `scipy.cKDTree`); if the gap
    is ≤ `max_dist` (meters) add ONE connector edge from the component node to the giant node. Repeat
    until no non-giant component is within reach — the giant grows each round, so a piece can ride in
    via a component that joined the same round. Acts on the ALL-mode component structure (any mode).

    Pure function on GeoDataFrames (no I/O). Returns (nodes, edges, summary):
      * `nodes` — a copy with `component` (1-based) + `is_giant` recomputed after the joins;
      * `edges` — a copy with the new connector rows appended (`type=connector_type`,
        `source=connector_source`, `join_gap_m`=the gap in meters, geometry = the straight line);
      * `summary` — `{n_joined, rounds, n_components, giant_frac, joined:[{component,gap_m}...]}`.

    `node_id`/row order is assumed 0-based and contiguous (as produced by `connect_multimodal` +
    `NetworkTables.from_parts`), so a node's row index is its id used in edge `from`/`to`.
    """
    import networkx as nx
    import numpy as np
    import pandas as pd
    from scipy.spatial import cKDTree
    from shapely.geometry import LineString

    nd = nodes.copy().reset_index(drop=True)
    ed = edges.copy().reset_index(drop=True)
    xy = np.c_[nd.geometry.x.values, nd.geometry.y.values]
    pts = list(nd.geometry.values)
    N = len(nd)

    new_rows, joined = [], []
    rounds = 0
    if max_dist and max_dist > 0:
        # working edge endpoint arrays (extended as connectors are added)
        froms = ed["from"].astype(int).tolist()
        tos = ed["to"].astype(int).tolist()
        while True:
            g = nx.Graph()
            g.add_nodes_from(range(N))
            g.add_edges_from(zip(froms, tos))
            comps = sorted(nx.connected_components(g), key=len, reverse=True)
            if len(comps) <= 1:
                break
            giant_nodes = np.array(sorted(comps[0]))
            gtree = cKDTree(xy[giant_nodes])
            added = 0
            for comp in comps[1:]:
                cl = np.array(sorted(comp))
                d, idx = gtree.query(xy[cl])
                j = int(np.argmin(d))
                gap = float(d[j])
                if gap <= max_dist:
                    a = int(cl[j])                       # component node
                    b = int(giant_nodes[int(idx[j])])    # nearest giant node
                    new_rows.append({"from": a, "to": b, "type": connector_type,
                                     "source": connector_source, "join_gap_m": round(gap, 1),
                                     "geometry": LineString([pts[a], pts[b]])})
                    joined.append(round(gap, 1))
                    froms.append(a); tos.append(b)
                    added += 1
            rounds += 1
            if added == 0:
                break

    if new_rows:
        add_gdf = gpd.GeoDataFrame(new_rows, geometry="geometry", crs=ed.crs)
        ed = gpd.GeoDataFrame(pd.concat([ed, add_gdf], ignore_index=True),
                              geometry="geometry", crs=ed.crs)

    nd, n_comp, n_giant = _label_components(nd, ed)
    summary = {
        "n_joined": len(new_rows),
        "rounds": rounds,
        "n_components": n_comp,
        "giant_frac": round(n_giant / max(N, 1), 3),
        "gaps_m": sorted(joined),
    }
    return nd, ed, summary
