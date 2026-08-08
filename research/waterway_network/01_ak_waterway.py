#!/usr/bin/env python3
"""STEP 01 — define the Alaska waterway network from the raw National Waterway Network (NWN).

The built network's waterway is only a facility-bbox clip (282 edges). Here we extract the real Alaska
waterway from the raw NWN and compare two extents, using mmnet's own data as-is for ports + barge hubs:
  AK-only      — the Alaska marine network (Gulf of Alaska, Cook Inlet, Bering Sea, Arctic Ocean spines)
  AK + spine   — also the Pacific deep-water spine linking Alaska to the Pacific NW (barge origin)
For each: connected components, giant, length, and how many ports / barge hubs it covers (1/5/20 km).
Writes the AK waterway network per extent for later road-connection work. Run:
python3 research/waterway_network/01_ak_waterway.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from scipy.spatial import cKDTree

from _trace import OUT, ROOT, Tracer
from mmnet.build import _load_anchor
from mmnet.config import load_config

RAW = ROOT / "data/raw/connectivity/barge/NWN_Waterway_Network_Lines/Waterway_Network.shp"

T = Tracer("01_ak_waterway", "STEP 01 — Define the Alaska waterway network (from raw NWN)")
cfg = load_config()
TGT = cfg.crs.target

# ── read raw NWN (national, EPSG:4269) and split into the two Alaska extents by bounds (lon/lat) ──
raw = gpd.read_file(RAW)
b = raw.bounds                       # in 4269
lat = (b.miny + b.maxy) / 2
spans_am = (b.maxx - b.minx) > 300   # antimeridian-spanning (Aleutian/Bering) features
west = b.maxx < -125                 # entirely west of -125° (AK mainland / SE)
faraleut = b.minx > 168              # western Aleutians
ak_only = raw[(lat > 50) & (west | faraleut | spans_am)].to_crs(TGT).reset_index(drop=True)
ak_spine = raw[(lat >= 46) & ((b.maxx < -120) | faraleut | spans_am)].to_crs(TGT).reset_index(drop=True)
T.kv("raw NWN features", len(raw))
T.kv("AK-only features", len(ak_only))
T.kv("AK+spine features", len(ak_spine))

# ── mmnet data, as-is: ports anchor + barge hubs ──
ports = _load_anchor("ports", cfg)
hubs = gpd.read_file(ROOT / "output" / "02_hubs.gpkg")
barge = hubs[hubs["delivery_method"].astype(str).str.contains("Barge", na=False)].to_crs(TGT)
T.kv("ports (mmnet anchor)", len(ports))
T.kv("barge hubs (delivery_method contains 'Barge')", f"{len(barge)} of {len(hubs)} hubs")


def analyze(gdf, name, tol=50.0):
    """Component graph (rounded vertices), giant, total length; tag components on the gdf copy."""
    g = nx.Graph()
    edge_comp = []          # component-key list parallel to gdf rows (first vertex's key)
    verts = []              # REAL vertex coords (metres) for coverage KDTree
    for geom in gdf.geometry:
        gg = [geom] if geom.geom_type == "LineString" else list(geom.geoms)
        first = None
        for ln in gg:
            raw_cs = [(x, y) for x, y, *_ in ln.coords]
            cs = [(round(x / tol), round(y / tol)) for x, y in raw_cs]
            for a, c in zip(cs[:-1], cs[1:]):
                g.add_edge(a, c)
            verts += raw_cs
            if first is None and cs:
                first = cs[0]
        edge_comp.append(first)
    comps = sorted(nx.connected_components(g), key=len, reverse=True)
    comp_of = {n: i for i, c in enumerate(comps) for n in c}
    out = gdf.copy()
    out["component"] = [comp_of.get(k, -1) for k in edge_comp]
    out["is_giant"] = out["component"] == 0
    out["length_m"] = out.geometry.length.round()
    giant_v = len(comps[0]) if comps else 0
    T.kv(f"{name}: vertices / components", f"{g.number_of_nodes():,} / {len(comps)}")
    T.kv(f"{name}: giant", f"{giant_v:,} vertices ({giant_v/max(g.number_of_nodes(),1):.0%})")
    T.kv(f"{name}: total length", f"{out['length_m'].sum()/1000:,.0f} km")
    return out, np.array(verts, dtype=float)


def coverage(verts, pts, label):
    if not len(verts) or not len(pts):
        return {}
    tree = cKDTree(verts)
    d, _ = tree.query(np.c_[pts.geometry.x, pts.geometry.y])
    cov = {f"≤{k//1000 if k>=1000 else k}{'km' if k>=1000 else 'm'}": int((d <= k).sum())
           for k in (1000, 5000, 20000)}
    T.kv(f"{label} coverage (of {len(pts)})", cov)
    return cov


T.stage("Extent A — AK-only (Alaska marine network)")
a_gdf, a_verts = analyze(ak_only, "AK-only")
coverage(a_verts, ports, "AK-only · ports")
coverage(a_verts, barge, "AK-only · barge hubs")

T.stage("Extent B — AK + Pacific spine")
b_gdf, b_verts = analyze(ak_spine, "AK+spine")
coverage(b_verts, ports, "AK+spine · ports")
coverage(b_verts, barge, "AK+spine · barge hubs")

# ── write the AK waterway networks (both extents) for later road-connection work ──
a_gdf.to_file(OUT / "ak_waterway_akonly__edges.gpkg", driver="GPKG")
b_gdf.to_file(OUT / "ak_waterway_akspine__edges.gpkg", driver="GPKG")
T.kv("wrote", "ak_waterway_{akonly,akspine}__edges.gpkg")

# ── figures: side-by-side map + coverage chart ──
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(TGT)


def panel(ax, gdf, title):
    boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
    gdf[gdf["is_giant"]].plot(ax=ax, color="#1f77b4", linewidth=0.7, zorder=2)
    gdf[~gdf["is_giant"]].plot(ax=ax, color="#9ecae1", linewidth=0.6, zorder=1)
    ports.plot(ax=ax, color="#2ca02c", markersize=8, zorder=4)
    barge.plot(ax=ax, color="#d62728", marker="*", markersize=14, zorder=5)
    bb = gdf.total_bounds
    ax.set_xlim(bb[0] - 1e5, bb[2] + 1e5); ax.set_ylim(bb[1] - 1e5, bb[3] + 1e5)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.set_title(title, fontsize=12)


fig, axs = plt.subplots(1, 2, figsize=(18, 9))
panel(axs[0], a_gdf, f"A — AK-only ({len(ak_only)} lines, {a_gdf['length_m'].sum()/1000:,.0f} km)")
panel(axs[1], b_gdf, f"B — AK + Pacific spine ({len(ak_spine)} lines, {b_gdf['length_m'].sum()/1000:,.0f} km)")
axs[0].legend(handles=[Line2D([0], [0], color="#1f77b4", lw=2, label="waterway giant"),
                       Line2D([0], [0], color="#9ecae1", lw=2, label="waterway (other comps)"),
                       Line2D([0], [0], marker="o", color="w", markerfacecolor="#2ca02c", label="ports (147)"),
                       Line2D([0], [0], marker="*", color="w", markerfacecolor="#d62728", label="barge hubs (202)")],
              loc="lower left", fontsize=8)
fig.suptitle("Alaska waterway network from the raw NWN — two extents (ports + barge hubs overlaid)", fontsize=14)
fig.tight_layout(rect=[0, 0, 1, 0.96])
p = OUT / "01_ak_waterway.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "AK-only vs AK+spine waterway network, with ports (green) + barge hubs (red stars)")
T.note("Both extents written as gpkg. AK-only = the Alaska marine network; AK+spine adds the Pacific "
       "deep-water spine to the lower-48 (barge origin). Pick the extent; the chosen one feeds the later "
       "waterway↔road connection study (ports = mmnet anchor, barge hubs = demand).")
T.done()
