#!/usr/bin/env python3
"""STEP 02 — connect road + ice via the full Alaska waterway, in the mmnet framework.

Complete multimodal connection:
  • anchors = PORTS ∪ BARGE HUBS (the 202 hubs whose delivery_method contains "Barge", already snapped to
    the road∪ice ground surface). At each anchor, link the nearest waterway node to the nearest ROAD node
    AND the nearest ICE node within `ANCHOR_MAXD` (mmnet's transfer policy) → Barge↔Road / Barge↔IceRoad.
  • before-policies: road↔road weld, ice↔ice weld, ice↔road bridge (from bridge_core).
So coastal regional road/ice systems join the giant BY SEA, not by fabricated long edges.
Run: python3 research/waterway_network/02_connect_via_ports.py
"""

import sys

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point

from _trace import OUT, ROOT, Tracer

sys.path.insert(0, str(ROOT / "research" / "road_ice_connect"))
from bridge_core import candidate_connectors, within_mode_connectors  # noqa: E402

from mmnet.build import _load_anchor  # noqa: E402
from mmnet.config import load_config  # noqa: E402
from mmnet.network import NetworkTables  # noqa: E402

# ───────────────────────────── configurable ─────────────────────────────
EXTENT = "akonly"          # "akonly" or "akspine"
ANCHOR_MAXD = 5000         # ports/hubs transfer max_dist (m) — mmnet transfer_max_dist
ROAD_ROAD = 3000           # road↔road weld tolerance (m)
ICE_ICE = 3000             # ice↔ice weld tolerance (m)
ICE_ROAD = 3000            # ice↔road bridge tolerance (m)
CONNECT_MAXD = 2000        # connect-to-giant: join each disconnected piece to the giant within this (m)
# ─────────────────────────────────────────────────────────────────────────

T = Tracer("02_connect_via_ports", "STEP 02 — Connect road+ice via the waterway (mmnet framework)")
cfg = load_config()
T.kv("config", f"extent={EXTENT}, anchor_maxd={ANCHOR_MAXD}, road↔road={ROAD_ROAD}, ice↔ice={ICE_ICE}, ice↔road={ICE_ROAD}")

# ── road + ice from the built network ──
nt = NetworkTables.from_gpkg(ROOT / "output" / "03_network")
nd = nt.nodes.sort_values("node_id").reset_index(drop=True)
xy = np.c_[nd.geometry.x.values, nd.geometry.y.values]
e = nt.edges.copy(); e["from"] = e["from"].astype(int); e["to"] = e["to"].astype(int)
ET = e["type"]                                   # NOTE: e["type"] — e.type is the geometry-type trap
N = len(nd)
road = e[ET == "Road"]; ice = e[ET == "IceRoad"]
road_ids = np.array(sorted(set(road["from"]) | set(road["to"])), dtype=int)
ice_ids = np.array(sorted(set(ice["from"]) | set(ice["to"])), dtype=int)

# ── full AK waterway (step 01), noded by rounding vertices to 50 m; node ids offset by N ──
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
        cs = [wid(c) for c in ln.coords]
        wedges += [(a + N, b + N) for a, b in zip(cs[:-1], cs[1:])]
        if first is None and cs:
            first = cs[0]
    ww_line_node.append((first + N) if first is not None else -1)
wxy = np.array(wxy); WN = len(wxy)
allxy = np.vstack([xy, wxy]); ww_ids = np.arange(N, N + WN)
T.kv("nodes", f"road {len(road_ids):,} · ice {len(ice_ids):,} · waterway {WN:,} (full AK, {EXTENT})")

# ── anchors = ports ∪ barge hubs; transfers connect waterway to nearest ROAD and nearest ICE ──
ports = _load_anchor("ports", cfg).to_crs(nd.crs)
hubs = gpd.read_file(ROOT / "output" / "02_hubs.gpkg")
barge = hubs[hubs["delivery_method"].astype(str).str.contains("Barge", na=False)].to_crs(nd.crs)
anchor_xy = np.vstack([np.c_[ports.geometry.x.values, ports.geometry.y.values],
                       np.c_[barge.geometry.x.values, barge.geometry.y.values]])
anchor_kind = ["port"] * len(ports) + ["hub"] * len(barge)
trd, tic, twr = cKDTree(xy[road_ids]), cKDTree(xy[ice_ids]), cKDTree(wxy)
dr, jr = trd.query(anchor_xy); di, ji = tic.query(anchor_xy); dw, jw = twr.query(anchor_xy)
transfers, seen = [], set()


def add_t(a, b, src):
    key = (min(a, b), max(a, b))
    if a != b and key not in seen:
        seen.add(key); transfers.append((a, b, src))


for k in range(len(anchor_xy)):
    wn = N + int(jw[k]); kind = anchor_kind[k]
    if dw[k] <= ANCHOR_MAXD and dr[k] <= ANCHOR_MAXD:
        add_t(int(road_ids[int(jr[k])]), wn, f"{kind}:Barge↔Road")
    if dw[k] <= ANCHOR_MAXD and di[k] <= ANCHOR_MAXD:
        add_t(int(ice_ids[int(ji[k])]), wn, f"{kind}:Barge↔IceRoad")
n_rw = sum(1 for *_, s in transfers if "Road" in s and "Ice" not in s)
n_iw = sum(1 for *_, s in transfers if "IceRoad" in s)
T.kv("anchors", f"ports {len(ports)} + barge hubs {len(barge)}")
T.kv("transfers", f"Barge↔Road {n_rw} · Barge↔IceRoad {n_iw} (ports+hubs, within {ANCHOR_MAXD} m)")

# ── before-policies (bridge_core): road↔road weld, ice↔ice weld, ice↔road bridge ──
rr = [(int(a), int(b)) for a, b, *_ in within_mode_connectors(e, xy, "Road", ROAD_ROAD)]
ii = [(int(a), int(b)) for a, b, *_ in within_mode_connectors(e, xy, "IceRoad", ICE_ICE)]
ri = [(int(c["from_node"]), int(c["to_node"])) for c in candidate_connectors(e, xy, "IceRoad", "Road")
      if c["gap_m"] <= ICE_ROAD]
T.kv("before-policies", f"road↔road weld {len(rr)} · ice↔ice weld {len(ii)} · ice↔road bridge {len(ri)}")

# ── connectivity evolution ──
base_ri = list(zip(road["from"], road["to"])) + list(zip(ice["from"], ice["to"]))
tr_pairs = [(a, b) for a, b, _ in transfers]


def metrics(extra):
    g = nx.Graph(); g.add_edges_from(base_ri); g.add_edges_from(wedges); g.add_edges_from(extra)
    comps = sorted(nx.connected_components(g), key=len, reverse=True)
    G = comps[0] if comps else set()
    return (len(comps), G, sum(n in G for n in road_ids) / len(road_ids),
            sum(n in G for n in ice_ids) / len(ice_ids), sum(n in G for n in ww_ids) / max(WN, 1))


nc0, _, rg0, ig0, wg0 = metrics([])                          # waterway present, no transfers/policies
nc1, _, rg1, ig1, wg1 = metrics(tr_pairs)                    # + ports+hubs transfers
ncP, GPRE, rgP, igP, wgP = metrics(tr_pairs + rr + ii + ri)  # + before-policies

# ── connect-to-giant pass: join every still-disconnected ground piece to the GIANT within CONNECT_MAXD ──
# (the root-cause fix: welds connect to the nearest *component*, not the giant — so a piece 210 m from the
#  green waterway giant stayed red. Here each leftover piece connects to the GIANT directly. Where it meets
#  the waterway → a coastal barge landing (shore:Barge↔mode); where it meets road/ice → a noding weld.)
g_pre = nx.Graph(); g_pre.add_edges_from(base_ri); g_pre.add_edges_from(wedges); g_pre.add_edges_from(tr_pairs + rr + ii + ri)
comps_pre = sorted(nx.connected_components(g_pre), key=len, reverse=True)
giant_nodes = np.array(sorted(GPRE)); gtree = cKDTree(allxy[giant_nodes])
road_set = set(road_ids.tolist())
shore = []
for comp in comps_pre[1:]:
    cl = np.array(sorted(comp)); d, idx = gtree.query(allxy[cl])
    j = int(np.argmin(d))
    if float(d[j]) <= CONNECT_MAXD:
        a = int(cl[j]); b = int(giant_nodes[int(idx[j])])
        if b >= N:                                # giant side is a waterway node → barge shore landing
            src = f"shore:Barge↔{'Road' if a in road_set else 'IceRoad'}"
        else:                                     # giant side is road/ice → noding gap to the giant
            src = "weld:to-giant"
        shore.append((a, b, src))
shore_pairs = [(a, b) for a, b, _ in shore]
ncF, GIANT, rgF, igF, wgF = metrics(tr_pairs + rr + ii + ri + shore_pairs)   # final
T.kv("connect-to-giant", f"{len(shore)} connectors (≤ {CONNECT_MAXD} m): "
     f"{sum(1 for *_, s in shore if s.startswith('shore'))} shore landings · "
     f"{sum(1 for *_, s in shore if s.startswith('weld'))} weld-to-giant")

rows = [
    {"stage": "waterway only (no transfers/policies)", "road_in_giant_pct": round(rg0 * 100, 1),
     "ice_in_giant_pct": round(ig0 * 100, 1), "waterway_in_giant_pct": round(wg0 * 100, 1), "components": nc0},
    {"stage": "+ ports+hubs transfers (Barge↔Road & IceRoad)", "road_in_giant_pct": round(rg1 * 100, 1),
     "ice_in_giant_pct": round(ig1 * 100, 1), "waterway_in_giant_pct": round(wg1 * 100, 1), "components": nc1},
    {"stage": "+ before-policies (road↔road, ice↔ice, ice↔road)", "road_in_giant_pct": round(rgP * 100, 1),
     "ice_in_giant_pct": round(igP * 100, 1), "waterway_in_giant_pct": round(wgP * 100, 1), "components": ncP},
    {"stage": f"+ connect-to-giant ≤{CONNECT_MAXD//1000}km (shore landings + welds)",
     "road_in_giant_pct": round(rgF * 100, 1), "ice_in_giant_pct": round(igF * 100, 1),
     "waterway_in_giant_pct": round(wgF * 100, 1), "components": ncF},
]
ev = pd.DataFrame(rows)
T.show(ev, "connectivity evolution (mmnet framework: waterway + ports/hubs + policies + connect-to-giant)", n=len(ev))
ev.to_csv(OUT / "connect_evolution.csv", index=False)
T.note(f"road {rg0:.0%}→{rg1:.0%}→{rgP:.0%}→{rgF:.0%}, ice {ig0:.0%}→{ig1:.0%}→{igP:.0%}→{igF:.0%}, waterway "
       f"{wgF:.0%} in the giant. The connect-to-giant pass fixes the near-misses: each leftover piece joins "
       "the GIANT (not the nearest stray component) where it is within reach — the North Slope connects at "
       "its ~210 m coastal barge landing.")

# ── North Slope check ──
br = int(road_ids[int(cKDTree(xy[road_ids]).query([-100728., 2368953.])[1])])
T.kv("North Slope", f"Barrow road in giant: {br in GIANT} (connected via a coastal barge landing)")

# ── write the connected multimodal network gpkg (waterway is_giant included) ──
def lines(pairs_src):
    return [{"source": s, "is_giant": a in GIANT, "geometry": LineString([allxy[a], allxy[b]])}
            for a, b, s in pairs_src]


road_e = road[["from", "geometry"]].assign(source="Road", is_giant=lambda d: d["from"].isin(GIANT))
ice_e = ice[["from", "geometry"]].assign(source="IceRoad", is_giant=lambda d: d["from"].isin(GIANT))
ww_e = ww[["geometry"]].assign(source="Waterway", is_giant=[n in GIANT for n in ww_line_node])
conn = gpd.GeoDataFrame(
    lines(transfers) + lines([(a, b, "weld:Road") for a, b in rr]) + lines([(a, b, "weld:IceRoad") for a, b in ii])
    + lines([(a, b, "bridge:Ice→Road") for a, b in ri]) + lines(shore), geometry="geometry", crs=nd.crs)
cols = ["source", "is_giant", "geometry"]
final = pd.concat([road_e[cols], ice_e[cols], ww_e[cols], conn[cols]], ignore_index=True)
gpd.GeoDataFrame(final, geometry="geometry", crs=nd.crs).to_file(
    OUT / "connected_via_ports__edges.gpkg", driver="GPKG")
T.kv("wrote", "connected_via_ports__edges.gpkg")

# ── hubs SNAPPED to the nearest ground (road∪ice) node — as mmnet snaps them — tagged connected status ──
ground_ids = np.concatenate([road_ids, ice_ids])
all_hubs = gpd.read_file(ROOT / "output" / "02_hubs.gpkg").to_crs(nd.crs)
_, hj = cKDTree(xy[ground_ids]).query(np.c_[all_hubs.geometry.x.values, all_hubs.geometry.y.values])
snap_nodes = [int(ground_ids[int(j)]) for j in hj]
keep_h = [c for c in ["hub_id", "delivery_method", "hub_type", "total_hub_capacity"] if c in all_hubs.columns]
hubs_snap = gpd.GeoDataFrame(
    all_hubs[keep_h].assign(
        snap_surface=np.where(np.isin(snap_nodes, road_ids), "Road", "IceRoad"),
        status=np.where([n in GIANT for n in snap_nodes], "connected", "disconnected")),
    geometry=[Point(*xy[n]) for n in snap_nodes], crs=nd.crs)
hubs_snap.to_file(OUT / "connected_hubs__snapped.gpkg", driver="GPKG")
T.kv("hubs snapped (connected / disconnected)",
     f"{int((hubs_snap['status']=='connected').sum())} / {int((hubs_snap['status']=='disconnected').sum())} "
     f"→ connected_hubs__snapped.gpkg")

# ── maps ──
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(nd.crs)
ext = boundary.total_bounds; EXT = (ext[0] - 1e5, ext[2] + 1e5, ext[1] - 1e5, ext[3] + 1e5)


def base_map(ax):
    boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
    ax.set_xlim(EXT[0], EXT[1]); ax.set_ylim(EXT[2], EXT[3])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])


def draw(ax, pairs, color, lw=1.2):
    if pairs:
        gpd.GeoSeries([LineString([allxy[a], allxy[b]]) for a, b in pairs], crs=nd.crs).plot(
            ax=ax, color=color, linewidth=lw, zorder=6)


# (1) connected network
fig, ax = plt.subplots(figsize=(12, 10)); base_map(ax)
ww.plot(ax=ax, color="#1f77b4", linewidth=0.5, zorder=1)
road.plot(ax=ax, color="#888", linewidth=0.3, zorder=2)
ice.plot(ax=ax, color="#17becf", linewidth=0.7, zorder=3)
draw(ax, tr_pairs, "#d62728", lw=1.2)
ports.plot(ax=ax, color="#2ca02c", markersize=6, zorder=5)
barge.plot(ax=ax, color="#000", marker="*", markersize=10, zorder=5)
ax.legend(handles=[Line2D([0], [0], color="#1f77b4", lw=2, label="waterway"),
                   Line2D([0], [0], color="#888", lw=2, label="road"),
                   Line2D([0], [0], color="#17becf", lw=2, label="ice road"),
                   Line2D([0], [0], color="#d62728", lw=2, label=f"Barge transfers ({len(tr_pairs)})"),
                   Line2D([0], [0], marker="o", color="w", markerfacecolor="#2ca02c", label="ports"),
                   Line2D([0], [0], marker="*", color="w", markerfacecolor="k", label="barge hubs")],
          loc="lower left", fontsize=8)
ax.set_title("Connected multimodal network — road + ice + waterway joined via ports + barge hubs")
p = OUT / "02_connected_network.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Road + ice + waterway connected via port/hub Barge transfers (red)")

# (2) before/after — road+ice+waterway connected vs disconnected
g0 = nx.Graph(); g0.add_edges_from(base_ri); giant0 = max(nx.connected_components(g0), key=len)
fig, axs = plt.subplots(1, 2, figsize=(17, 8))
base_map(axs[0])
for sub in (road, ice):
    sub[sub["from"].isin(giant0)].plot(ax=axs[0], color="#444", linewidth=0.4, zorder=2)
    sub[~sub["from"].isin(giant0)].plot(ax=axs[0], color="#d62728", linewidth=0.6, zorder=3)
axs[0].set_title(f"BEFORE — road {rg0:.0%} in giant (road+ice only, no waterway)")
base_map(axs[1])
ww_giant = ww["geometry"].index[[n in GIANT for n in ww_line_node]]
ww.loc[ww_giant].plot(ax=axs[1], color="#2ca02c", linewidth=0.4, zorder=1)
for sub in (road, ice):
    sub[sub["from"].isin(GIANT)].plot(ax=axs[1], color="#2ca02c", linewidth=0.5, zorder=2)
    sub[~sub["from"].isin(GIANT)].plot(ax=axs[1], color="#d62728", linewidth=0.7, zorder=3)
axs[1].set_title(f"AFTER — connected (green) vs disconnected (red); road {rgF:.0%}, ice {igF:.0%}, waterway {wgF:.0%}")
axs[1].legend(handles=[Line2D([0], [0], color="#2ca02c", lw=2, label="connected (giant, incl. waterway)"),
                       Line2D([0], [0], color="#d62728", lw=2, label="disconnected")],
              loc="lower left", fontsize=8)
fig.suptitle("Connecting road + ice via the waterway (ports + barge hubs) — before vs after", fontsize=14)
fig.tight_layout(rect=[0, 0, 1, 0.95])
p = OUT / "02_before_after.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Before vs after — connected (green, incl. waterway) vs disconnected (red)")
T.done()
