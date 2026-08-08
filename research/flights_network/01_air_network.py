#!/usr/bin/env python3
"""STEP 01 — build the Alaska air-cargo network from the NEW self-contained Flights data.

The new dataset (`data/raw/connectivity/air/flight_paths_combined.csv`) carries embedded coordinates + FAA/ICAO IDs +
region/owner/status per endpoint (built by `data/raw/connectivity/air/build_map.py` from the AK DOT&PF airport registry),
so the network needs no external geocoding — unlike the old `data/raw/connectivity/air/` inputs, which
geocode bare codes against an 85k global airport DB (mis-matching some AK codes to the lower-48).

Builds the air network: nodes = airports (coords reprojected to the project CRS), edges = OD cargo legs;
then components/giant, degree, hubs vs spokes. Writes the node/edge GeoPackages + a network map + a
hub-degree chart. Research only. Run: python3 research/flights_network/01_air_network.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from shapely.geometry import LineString, Point

from _trace import OUT, ROOT, Tracer
from mmnet.config import load_config

HUB_DEGREE = 5            # degree ≥ this = a hub (trunk / regional hub); degree 1 = a spoke

T = Tracer("01_air_network", "STEP 01 — Build the Alaska air-cargo network (new Flights data)")
cfg = load_config()
TGT = cfg.crs.target
SRC = ROOT / "data" / "raw" / "connectivity" / "air" / "flight_paths_combined.csv"  # official location

df = pd.read_csv(SRC)
T.kv("source", f"{SRC.relative_to(ROOT)}  ({len(df)} legs)")


def _has_coords(row) -> bool:
    try:
        for c in ("Origin_Lat", "Origin_Lon", "Destination_Lat", "Destination_Lon"):
            float(row[c])
        return True
    except (ValueError, TypeError):
        return False


mask = df.apply(_has_coords, axis=1)
valid, dropped = df[mask].copy(), df[~mask]
drop_names = sorted(set(dropped["Origin"]).union(dropped["Destination"]) - set(valid["Origin"]) - set(valid["Destination"]))
T.kv("legs with coordinates", f"{len(valid)} of {len(df)}  (dropped {len(dropped)} legs; unmatched: {drop_names or 'none'})")

# ── nodes: unique airports from both endpoints, keyed FAA_ID → ICAO → name ──
nodes: dict[str, dict] = {}


def _endpoint(row, p):
    s = lambda c: ("" if pd.isna(row[f"{p}_{c}"]) else str(row[f"{p}_{c}"]).strip())
    return {"name": s("Airport_Name"), "faa": s("FAA_ID"), "icao": s("ICAO"),
            "status": s("Status"), "region": s("Region"), "owner": s("Owner"),
            "lat": float(row[f"{p}_Lat"]), "lon": float(row[f"{p}_Lon"]), "label": str(row[p]).strip()}


def _key(a) -> str:
    return a["faa"] or a["icao"] or a["name"] or a["label"]


leg_keys = []
for _, row in valid.iterrows():
    o, d = _endpoint(row, "Origin"), _endpoint(row, "Destination")
    ko, kd = _key(o), _key(d)
    nodes.setdefault(ko, o)
    nodes.setdefault(kd, d)
    leg_keys.append((ko, kd, str(row["Carrier"]).strip()))

keys = list(nodes)
idx = {k: i for i, k in enumerate(keys)}
pts = gpd.GeoSeries([Point(nodes[k]["lon"], nodes[k]["lat"]) for k in keys], crs=4326).to_crs(TGT)
ndf = gpd.GeoDataFrame({
    "node_id": [idx[k] for k in keys], "key": keys,
    "name": [nodes[k]["name"] for k in keys], "faa": [nodes[k]["faa"] for k in keys],
    "icao": [nodes[k]["icao"] for k in keys], "region": [nodes[k]["region"] for k in keys],
    "owner": [nodes[k]["owner"] for k in keys], "status": [nodes[k]["status"] for k in keys],
}, geometry=list(pts), crs=TGT)
xy = np.c_[ndf.geometry.x.values, ndf.geometry.y.values]

# ── edges: the OD legs (straight LineString in the project CRS) ──
g = nx.Graph()
erows, seen = [], set()
for ko, kd, carrier in leg_keys:
    a, b = idx[ko], idx[kd]
    if a == b:
        continue
    g.add_edge(a, b)
    key = (min(a, b), max(a, b))
    erows.append({"from": a, "to": b, "carrier": carrier, "geometry": LineString([xy[a], xy[b]])})
    seen.add(key)
edf = gpd.GeoDataFrame(erows, geometry="geometry", crs=TGT)
edf["length_km"] = (edf.geometry.length / 1000.0).round(1)

# ── connectivity + roles ──
deg = dict(g.degree())
comps = sorted(nx.connected_components(g), key=len, reverse=True)
giant = comps[0] if comps else set()
ndf["degree"] = [int(deg.get(i, 0)) for i in ndf["node_id"]]
ndf["role"] = np.where(ndf["degree"] >= HUB_DEGREE, "hub",
                       np.where(ndf["degree"] == 1, "spoke", "relay"))
ndf["in_giant"] = ndf["node_id"].isin(giant)

T.kv("airports (nodes)", f"{len(ndf)}  (hubs {int((ndf['role']=='hub').sum())} · relays "
     f"{int((ndf['role']=='relay').sum())} · spokes {int((ndf['role']=='spoke').sum())})")
T.kv("legs (edges)", f"{len(edf)}  (unique OD pairs {len(seen)})")
T.kv("components / giant", f"{len(comps)} / {len(giant)} airports ({len(giant)/max(len(ndf),1):.0%})")
T.kv("carriers", edf["carrier"].value_counts().to_dict())
T.kv("leg length km (min/median/max)", f"{edf['length_km'].min():.0f} / {edf['length_km'].median():.0f} / {edf['length_km'].max():.0f}")
top = ndf.sort_values("degree", ascending=False).head(10)[["name", "faa", "region", "degree"]]
T.show(top, "top airports by degree (the cargo hubs)", n=10)

ndf.to_file(OUT / "air_network__nodes.gpkg", driver="GPKG")
edf.to_file(OUT / "air_network__edges.gpkg", driver="GPKG")
T.kv("wrote", "air_network__{nodes,edges}.gpkg")

# ── map: hub-and-spoke network over the Alaska outline ──
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(TGT)
ext = boundary.total_bounds
fig, ax = plt.subplots(figsize=(12, 10))
boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
edf.plot(ax=ax, color="#1f77b4", linewidth=0.6, alpha=0.55, zorder=2)
sp = ndf[ndf["role"] == "spoke"]; rl = ndf[ndf["role"] == "relay"]; hb = ndf[ndf["role"] == "hub"]
ax.scatter(sp.geometry.x, sp.geometry.y, s=10, c="#2ca02c", alpha=0.7, zorder=3)
ax.scatter(rl.geometry.x, rl.geometry.y, s=22, c="#ff7f0e", zorder=4)
ax.scatter(hb.geometry.x, hb.geometry.y, s=hb["degree"] * 9, c="#d62728", edgecolor="white", linewidth=0.5, zorder=5)
for _, r in hb.iterrows():
    ax.annotate(r["faa"] or r["name"], (r.geometry.x, r.geometry.y), fontsize=7, fontweight="bold",
                xytext=(4, 3), textcoords="offset points", zorder=6)
ax.set_xlim(ext[0] - 1e5, ext[2] + 1e5); ax.set_ylim(ext[1] - 1e5, ext[3] + 1e5)
ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
ax.legend(handles=[Line2D([0], [0], color="#1f77b4", lw=2, label=f"cargo leg ({len(edf)})"),
                   Line2D([0], [0], marker="o", color="w", markerfacecolor="#d62728", markersize=9, label=f"hub (deg≥{HUB_DEGREE})"),
                   Line2D([0], [0], marker="o", color="w", markerfacecolor="#ff7f0e", markersize=7, label="relay"),
                   Line2D([0], [0], marker="o", color="w", markerfacecolor="#2ca02c", markersize=6, label="spoke (deg 1)")],
          loc="lower left", fontsize=8)
ax.set_title(f"Alaska air-cargo network (new Flights data) — {len(ndf)} airports, {len(edf)} legs, "
             f"{len(comps)} component(s)")
p = OUT / "01_air_network.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "The Alaska air-cargo hub-and-spoke network (hubs red, relays orange, spokes green)")

# ── hub-degree bar chart ──
fig, ax = plt.subplots(figsize=(11, 5))
hb_sorted = ndf.sort_values("degree", ascending=False).head(14)
labels = [(r["faa"] or r["name"][:10]) for _, r in hb_sorted.iterrows()]
ax.bar(labels, hb_sorted["degree"], color=np.where(hb_sorted["degree"] >= HUB_DEGREE, "#d62728", "#ff7f0e"))
ax.set_ylabel("degree (legs)"); ax.set_title("Air-cargo hubs by degree — the trunk + regional feed structure")
plt.xticks(rotation=45, ha="right")
fig.tight_layout()
p = OUT / "01_hub_degree.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Airport degree ranking — ANC/FAI trunk + the regional cargo hubs")
T.done()
