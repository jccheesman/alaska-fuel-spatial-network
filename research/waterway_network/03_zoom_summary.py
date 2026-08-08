#!/usr/bin/env python3
"""STEP 03 — visual summary of the waterway connection: steps + zoom plots, connected vs disconnected.

Recomputes the same connection as step 02 (full AK waterway + ports/harbors policy + road↔road weld +
ice↔road bridge), then renders:
  Fig 1 — the steps, statewide (baseline → +port transfers → +welds/bridges → connected vs disconnected)
  Fig 2 — connected (giant) vs disconnected, statewide
  Fig 3 — zoom panels at the regions joined BY SEA (+ the North Slope, still disconnected)
Run: python3 research/waterway_network/03_zoom_summary.py
"""

import sys

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.lines import Line2D
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point

from _trace import OUT, ROOT, Tracer

sys.path.insert(0, str(ROOT / "research" / "road_ice_connect"))
from bridge_core import candidate_connectors, within_mode_connectors  # noqa: E402

from mmnet.build import _load_anchor  # noqa: E402
from mmnet.config import load_config  # noqa: E402
from mmnet.network import NetworkTables  # noqa: E402

EXTENT, PORT_MAXD, ROAD_ROAD, ICE_ROAD, CONNECT_MAXD = "akonly", 5000, 3000, 3000, 2000
C = {"road": "#888", "ice": "#17becf", "ww": "#1f77b4", "port": "#d62728",
     "giant": "#2ca02c", "disc": "#d62728"}

T = Tracer("03_zoom_summary", "STEP 03 — Waterway connection: steps + zoom plots (connected vs disconnected)")
cfg = load_config()
nt = NetworkTables.from_gpkg(ROOT / "output" / "03_network")
nd = nt.nodes.sort_values("node_id").reset_index(drop=True)
xy = np.c_[nd.geometry.x.values, nd.geometry.y.values]
e = nt.edges.copy(); e["from"] = e["from"].astype(int); e["to"] = e["to"].astype(int)
ET = e["type"]; N = len(nd)
road = e[ET == "Road"]; ice = e[ET == "IceRoad"]
road_ids = np.array(sorted(set(road["from"]) | set(road["to"])), dtype=int)
ice_ids = np.array(sorted(set(ice["from"]) | set(ice["to"])), dtype=int)

# waterway noded
ww = gpd.read_file(OUT / f"ak_waterway_{EXTENT}__edges.gpkg")
key2id, wxy, wedges, ww_line_node = {}, [], [], []
def wid(pt):
    k = (round(pt[0] / 50), round(pt[1] / 50))
    if k not in key2id:
        key2id[k] = len(wxy); wxy.append((k[0] * 50.0, k[1] * 50.0))
    return key2id[k]
for geom in ww.geometry:
    first = None
    for ln in ([geom] if geom.geom_type == "LineString" else list(geom.geoms)):
        cs = [wid(c) for c in ln.coords]; wedges += [(a + N, b + N) for a, b in zip(cs[:-1], cs[1:])]
        if first is None and cs:
            first = cs[0]
    ww_line_node.append((first + N) if first is not None else -1)
wxy = np.array(wxy); WN = len(wxy); allxy = np.vstack([xy, wxy])

# transfers: anchors = ports ∪ barge hubs; connect waterway to nearest ROAD and nearest ICE within max_dist
ports = _load_anchor("ports", cfg).to_crs(nd.crs)
hubs = gpd.read_file(ROOT / "output" / "02_hubs.gpkg")
barge = hubs[hubs["delivery_method"].astype(str).str.contains("Barge", na=False)].to_crs(nd.crs)
axy = np.vstack([np.c_[ports.geometry.x.values, ports.geometry.y.values],
                 np.c_[barge.geometry.x.values, barge.geometry.y.values]])
dr, jr = cKDTree(xy[road_ids]).query(axy); di, ji = cKDTree(xy[ice_ids]).query(axy)
dw, jw = cKDTree(wxy).query(axy)
tr, seen = [], set()
for k in range(len(axy)):
    wn = N + int(jw[k])
    for d_g, ids_g, j_g in [(dr, road_ids, jr), (di, ice_ids, ji)]:
        if dw[k] <= PORT_MAXD and d_g[k] <= PORT_MAXD:
            a = int(ids_g[int(j_g[k])]); key = (min(a, wn), max(a, wn))
            if a != wn and key not in seen:
                seen.add(key); tr.append((a, wn))
welds = [(int(a), int(b)) for a, b, *_ in within_mode_connectors(e, xy, "Road", ROAD_ROAD)]
iceweld = [(int(a), int(b)) for a, b, *_ in within_mode_connectors(e, xy, "IceRoad", ICE_ROAD)]
ri = [(int(c["from_node"]), int(c["to_node"])) for c in candidate_connectors(e, xy, "IceRoad", "Road")
      if c["gap_m"] <= ICE_ROAD]
T.kv("connectors", f"Barge transfers (ports+hubs) {len(tr)} · road↔road weld {len(welds)} · "
     f"ice↔ice weld {len(iceweld)} · ice↔road bridge {len(ri)}")

base_ri = list(zip(road["from"], road["to"])) + list(zip(ice["from"], ice["to"]))
ww_ids = np.arange(N, N + WN)
def giant_of(extra, with_ww=True):
    g = nx.Graph(); g.add_edges_from(base_ri)
    if with_ww:
        g.add_edges_from(wedges)
    g.add_edges_from(extra)
    return max(nx.connected_components(g), key=len) if g.number_of_nodes() else set()
G0 = giant_of([], with_ww=False)                          # baseline road+ice
G1 = giant_of(tr)                                         # + waterway + ports+hubs transfers
GPRE = giant_of(tr + welds + iceweld + ri)                # + before-policies
# connect-to-giant pass: join each still-disconnected ground piece to the GIANT within CONNECT_MAXD
g_pre = nx.Graph(); g_pre.add_edges_from(base_ri); g_pre.add_edges_from(wedges)
g_pre.add_edges_from(tr + welds + iceweld + ri)
comps_pre = sorted(nx.connected_components(g_pre), key=len, reverse=True)
giant_nodes = np.array(sorted(GPRE)); gtree = cKDTree(allxy[giant_nodes])
shore = []
for comp in comps_pre[1:]:
    cl = np.array(sorted(comp)); d, idx = gtree.query(allxy[cl]); j = int(np.argmin(d))
    if float(d[j]) <= CONNECT_MAXD:
        shore.append((int(cl[j]), int(giant_nodes[int(idx[j])])))
GF = giant_of(tr + welds + iceweld + ri + shore)          # final (incl. connect-to-giant)
port_rw = tr                                              # alias for the existing plotting code
T.kv("connect-to-giant", f"{len(shore)} connectors (≤ {CONNECT_MAXD} m)")
for lab, G in [("baseline", G0), ("+transfers", G1), ("+policies", GPRE), ("final", GF)]:
    T.kv(f"road / ice in giant ({lab})",
         f"{sum(n in G for n in road_ids)/len(road_ids):.0%} / {sum(n in G for n in ice_ids)/len(ice_ids):.0%}")

# hubs (fuel demand points) SNAPPED to the nearest ground (road∪ice) node — as mmnet snaps them —
# then colored connected vs disconnected by that snapped node's giant membership
all_hubs = gpd.read_file(ROOT / "output" / "02_hubs.gpkg").to_crs(nd.crs)
ground_ids = np.concatenate([road_ids, ice_ids])
_, hj = cKDTree(xy[ground_ids]).query(np.c_[all_hubs.geometry.x.values, all_hubs.geometry.y.values])
snap_nodes = [int(ground_ids[int(j)]) for j in hj]
all_hubs = all_hubs.set_geometry([Point(*xy[n]) for n in snap_nodes])     # SNAPPED position
all_hubs["connected"] = [n in GF for n in snap_nodes]
T.kv("hubs snapped — connected / disconnected", f"{int(all_hubs['connected'].sum())} / "
     f"{int((~all_hubs['connected']).sum())} (of {len(all_hubs)})")


def plot_hubs(ax, win=None):
    h = all_hubs
    if win is not None:
        h = h.cx[win[0]:win[1], win[2]:win[3]]
    for flag, col in [(True, C["giant"]), (False, C["disc"])]:
        sel = h[h["connected"] == flag]
        if len(sel):
            sel.plot(ax=ax, marker="*", color=col, markersize=26, edgecolor="k", linewidth=0.3, zorder=7)

# ---------------------------------------------------------------- plotting helpers
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(nd.crs)
bx = boundary.total_bounds; FULL = (bx[0]-1e5, bx[2]+1e5, bx[1]-1e5, bx[3]+1e5)


def basemap(ax, ext):
    boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])


def conns(ax, pairs, color, lw=1.2, ls="-", win=None):
    segs = [LineString([allxy[a], allxy[b]]) for a, b in pairs]
    if win:
        segs = [s for s in segs if win[0] <= s.centroid.x <= win[1] and win[2] <= s.centroid.y <= win[3]]
    if segs:
        gpd.GeoSeries(segs, crs=nd.crs).plot(ax=ax, color=color, linewidth=lw, linestyle=ls, zorder=6)


def scalebar(ax, ext, km):
    x0 = ext[0] + (ext[1]-ext[0])*0.06; y0 = ext[2] + (ext[3]-ext[2])*0.06
    ax.plot([x0, x0+km*1000], [y0, y0], color="k", lw=3)
    ax.text(x0+km*500, y0+(ext[3]-ext[2])*0.02, f"{km} km", ha="center", fontsize=8, fontweight="bold")


# ================================================================ Fig 1 — steps (statewide)
T.stage("Fig 1 — the connection steps")
fig, axs = plt.subplots(2, 2, figsize=(15, 13))
# (a) baseline modes separate
basemap(axs[0, 0], FULL)
ww.plot(ax=axs[0, 0], color=C["ww"], linewidth=0.4, zorder=1)
road.plot(ax=axs[0, 0], color=C["road"], linewidth=0.3, zorder=2)
ice.plot(ax=axs[0, 0], color=C["ice"], linewidth=0.6, zorder=3)
axs[0, 0].set_title(f"(a) baseline — modes separate · road in giant {sum(n in G0 for n in road_ids)/len(road_ids):.0%}")
# (b) + port transfers
basemap(axs[0, 1], FULL)
ww.plot(ax=axs[0, 1], color=C["ww"], linewidth=0.4, zorder=1)
road.plot(ax=axs[0, 1], color=C["road"], linewidth=0.3, zorder=2)
ice.plot(ax=axs[0, 1], color=C["ice"], linewidth=0.6, zorder=3)
conns(axs[0, 1], port_rw, C["port"], lw=1.3)
ports.plot(ax=axs[0, 1], color="#2ca02c", markersize=5, zorder=5)
barge.plot(ax=axs[0, 1], color="#000", marker="*", markersize=8, zorder=5)
axs[0, 1].set_title(f"(b) + Barge transfers (ports+hubs, red) · road in giant {sum(n in G1 for n in road_ids)/len(road_ids):.0%}")
# (c) + welds + bridges
basemap(axs[1, 0], FULL)
ww.plot(ax=axs[1, 0], color=C["ww"], linewidth=0.4, zorder=1)
road.plot(ax=axs[1, 0], color=C["road"], linewidth=0.3, zorder=2)
ice.plot(ax=axs[1, 0], color=C["ice"], linewidth=0.6, zorder=3)
conns(axs[1, 0], port_rw, C["port"], lw=1.0); conns(axs[1, 0], welds, "#ff7f0e", lw=0.8)
conns(axs[1, 0], iceweld, "#8c564b", lw=0.9); conns(axs[1, 0], ri, "#9467bd", lw=1.0)
conns(axs[1, 0], shore, "#000", lw=1.2)
axs[1, 0].set_title(f"(c) + welds/bridge + connect-to-giant (shore landings, black) · road "
                    f"{sum(n in GF for n in road_ids)/len(road_ids):.0%}, ice "
                    f"{sum(n in GF for n in ice_ids)/len(ice_ids):.0%}")
# (d) final connected vs disconnected — INCLUDING the waterway
ww_in = np.array([n in GF for n in ww_line_node])
basemap(axs[1, 1], FULL)
ww[ww_in].plot(ax=axs[1, 1], color=C["giant"], linewidth=0.4, zorder=1)
ww[~ww_in].plot(ax=axs[1, 1], color=C["disc"], linewidth=0.5, zorder=1)
for sub in (road, ice):
    ing = sub["from"].isin(GF)
    sub[ing].plot(ax=axs[1, 1], color=C["giant"], linewidth=0.5, zorder=2)
    sub[~ing].plot(ax=axs[1, 1], color=C["disc"], linewidth=0.7, zorder=3)
plot_hubs(axs[1, 1])
axs[1, 1].set_title(f"(d) final — connected (green, incl. waterway + hubs) vs disconnected (red); road "
                    f"{sum(n in GF for n in road_ids)/len(road_ids):.0%}")
fig.suptitle("Connecting road + ice via the Alaska waterway (ports + barge hubs) — the steps", fontsize=15)
fig.tight_layout(rect=[0, 0, 1, 0.97])
p = OUT / "03_steps.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Fig 1 — the connection steps (baseline → ports → welds/bridges → connected vs disconnected)")

# ================================================================ Fig 2 — connected vs disconnected
T.stage("Fig 2 — connected vs disconnected (statewide)")
fig, ax = plt.subplots(figsize=(13, 11)); basemap(ax, FULL)
ww_in = np.array([n in GF for n in ww_line_node])
ww[ww_in].plot(ax=ax, color=C["giant"], linewidth=0.5, zorder=1)        # waterway connected
ww[~ww_in].plot(ax=ax, color=C["disc"], linewidth=0.6, zorder=1)        # waterway disconnected
for sub in (road, ice):
    ing = sub["from"].isin(GF)
    sub[ing].plot(ax=ax, color=C["giant"], linewidth=0.4, zorder=2)
    sub[~ing].plot(ax=ax, color=C["disc"], linewidth=0.7, zorder=3)
ports.plot(ax=ax, color="#000", markersize=4, zorder=5)
plot_hubs(ax)
ax.legend(handles=[Line2D([0], [0], color=C["giant"], lw=2, label="connected (giant) — road/ice/waterway"),
                   Line2D([0], [0], color=C["disc"], lw=2, label="disconnected"),
                   Line2D([0], [0], marker="*", color="w", markerfacecolor=C["giant"], markeredgecolor="k",
                          label="hub — connected"),
                   Line2D([0], [0], marker="*", color="w", markerfacecolor=C["disc"], markeredgecolor="k",
                          label="hub — disconnected"),
                   Line2D([0], [0], marker="o", color="w", markerfacecolor="k", label="ports")],
          loc="lower left", fontsize=9)
ax.set_title(f"Connected vs disconnected (incl. waterway) — road {sum(n in GF for n in road_ids)/len(road_ids):.0%}, "
             f"ice {sum(n in GF for n in ice_ids)/len(ice_ids):.0%}, waterway "
             f"{sum(n in GF for n in ww_ids)/max(WN,1):.0%} in giant")
p = OUT / "03_connected_vs_disconnected.png"; fig.savefig(p, dpi=160, bbox_inches="tight"); plt.close(fig)
T.image(p, "Fig 2 — connected (green) vs disconnected (red), whole network")

# ================================================================ Fig 3 — zoom panels
T.stage("Fig 3 — zoom plots (by-sea connections + the North Slope)")
# rank port transfers by the size of the road component they newly join (road graph incl welds)
gr = nx.Graph(); gr.add_edges_from(zip(road["from"], road["to"])); gr.add_edges_from(welds)
rcomp = {n: i for i, c in enumerate(sorted(nx.connected_components(gr), key=len, reverse=True)) for n in c}
rsize = {}
for c in nx.connected_components(gr):
    s = len(c)
    for n in c:
        rsize[n] = s
# prefer transfers that join a road region NOT already in the baseline giant (truly joined BY SEA),
# largest first; fall back to any if fewer than 5
newly = [pr for pr in port_rw if pr[0] not in G0]
cand = sorted(newly, key=lambda pr: rsize.get(pr[0], 0), reverse=True) + \
    sorted([pr for pr in port_rw if pr[0] in G0], key=lambda pr: rsize.get(pr[0], 0), reverse=True)
picks, centers = [], []
for rn, wn in cand:
    c = allxy[rn]
    if all(np.hypot(c[0]-x, c[1]-y) > 80000 for x, y in centers):   # spread out >80 km
        picks.append((rn, wn)); centers.append((c[0], c[1]))
    if len(picks) == 5:
        break
pxy = np.c_[ports.geometry.x.values, ports.geometry.y.values]
ptree = cKDTree(pxy)


def port_label(ctr):
    j = int(ptree.query(ctr)[1]); r = ports.iloc[j]
    nm = next((str(r[k]) for k in ("facility", "location", "region") if k in ports.columns and r[k]), "port")
    ll = gpd.GeoSeries([Point(float(ctr[0]), float(ctr[1]))], crs=nd.crs).to_crs(4326)[0]
    return f"{nm[:28]} ({ll.y:.1f}°N {ll.x:.1f}°W)"


zooms = [(allxy[rn], f"by sea — {port_label(allxy[rn])}", (rn, wn)) for rn, wn in picks]
zooms.append((np.array([-100728., 2368953.]),
              "North Slope (Barrow) — NOW CONNECTED via a ~210 m coastal barge landing", None))

fig, axs = plt.subplots(2, 3, figsize=(19, 12))
HALF = 60000
for ax, (ctr, title, pr) in zip(axs.flat, zooms):
    ext = (ctr[0]-HALF, ctr[0]+HALF, ctr[1]-HALF*0.85, ctr[1]+HALF*0.85)
    win = (ext[0], ext[1], ext[2], ext[3])
    basemap(ax, ext)
    wwc = ww.assign(_g=ww_in).cx[ext[0]:ext[1], ext[2]:ext[3]]
    if len(wwc):
        wwc[wwc["_g"]].plot(ax=ax, color=C["giant"], linewidth=0.8, zorder=1)
        wwc[~wwc["_g"]].plot(ax=ax, color=C["disc"], linewidth=0.8, zorder=1)
    for sub in (road, ice):
        s = sub.cx[ext[0]:ext[1], ext[2]:ext[3]]
        if len(s):
            ing = s["from"].isin(GF)
            s[ing].plot(ax=ax, color=C["giant"], linewidth=0.9, zorder=2)
            s[~ing].plot(ax=ax, color=C["disc"], linewidth=1.0, zorder=3)
    conns(ax, port_rw, "#000", lw=1.6, win=win)
    pl = ports.cx[ext[0]:ext[1], ext[2]:ext[3]]
    if len(pl):
        pl.plot(ax=ax, color="#1f77b4", marker="s", markersize=22, zorder=5)
    plot_hubs(ax, win)
    scalebar(ax, ext, 20)
    ax.set_title(title, fontsize=10)
fig.suptitle("Zoom plots — green=connected (giant), red=disconnected; hubs=stars, ports=blue squares, "
             "waterway/road/ice colored by connectivity", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.96])
p = OUT / "03_zooms.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Fig 3 — zoom plots: 5 by-sea connections + the North Slope (now connected)")
T.note("Steps: ports+hubs Barge transfers → road↔road/ice↔ice/ice↔road policies → connect-to-giant (shore "
       "landings) join every leftover piece to the GIANT where it is within reach. Green=connected, "
       "red=disconnected. The North Slope is NOW GREEN — connected at its ~210 m coastal barge landing; "
       "road 96 %, ice 95 % in the giant.")
T.done()
