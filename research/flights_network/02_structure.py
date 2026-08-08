#!/usr/bin/env python3
"""STEP 02 — characterize the Alaska air-cargo network: hierarchy, degree, region, coverage.

Reads the network built by 01 (`out/air_network__{nodes,edges}.gpkg`) plus the AK DOT&PF airport registry
(`data/raw/connectivity/air/airports_ak_dotpf.csv`, 285 airports) and reports the trunk → regional-hub → spoke hierarchy, the
degree distribution, the breakdown by region/owner/status, and how much of the registry the cargo network
actually serves. Research only. Run: python3 research/flights_network/02_structure.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from _trace import OUT, ROOT, Tracer
from mmnet.config import load_config

TRUNK = {"ANC", "FAI"}     # the mainline origins that feed the regional hubs

T = Tracer("02_structure", "STEP 02 — Characterize the Alaska air-cargo network (structure + coverage)")
cfg = load_config()
TGT = cfg.crs.target

ndf = gpd.read_file(OUT / "air_network__nodes.gpkg").to_crs(TGT)
edf = gpd.read_file(OUT / "air_network__edges.gpkg").to_crs(TGT)
ndf["faa"] = ndf["faa"].fillna("").astype(str)

# ── hierarchy: trunk → regional hub → relay → spoke ──
def _tier(r):
    if r["faa"] in TRUNK:
        return "trunk"
    if r["degree"] >= 5:
        return "regional hub"
    if r["degree"] == 1:
        return "spoke"
    return "relay"


ndf["tier"] = ndf.apply(_tier, axis=1)
T.stage("Hub-and-spoke hierarchy")
for tier in ("trunk", "regional hub", "relay", "spoke"):
    sub = ndf[ndf["tier"] == tier].sort_values("degree", ascending=False)
    names = ", ".join(f"{r['faa'] or r['name'][:8]}({r['degree']})" for _, r in sub.head(8).iterrows())
    T.kv(tier, f"{len(sub)} airports — {names}{' …' if len(sub) > 8 else ''}")

# ── degree distribution + region/owner/status ──
T.stage("Distribution + attributes")
T.kv("degree (min/median/mean/max)", f"{ndf['degree'].min()} / {ndf['degree'].median():.0f} / "
     f"{ndf['degree'].mean():.1f} / {ndf['degree'].max()}")
T.kv("airports by region", ndf["region"].replace("", "—").value_counts().to_dict())
T.kv("airports by owner", ndf["owner"].replace("", "—").value_counts().to_dict())
T.kv("airports by status", ndf["status"].replace("", "—").value_counts().to_dict())
T.kv("components", f"giant {int(ndf['in_giant'].sum())} / {len(ndf)}; "
     f"off-giant: {', '.join(sorted((ndf.loc[~ndf['in_giant'], 'faa'].replace('', '?')))) or 'none'}")

# ── coverage vs the AK DOT&PF registry (285 airports) ──
reg = pd.read_csv(ROOT / "data" / "raw" / "connectivity" / "air" / "airports_ak_dotpf.csv", encoding="utf-8-sig")
reg.columns = [c.strip() for c in reg.columns]
reg["FAA_ID"] = reg["FAA_ID"].astype(str).str.strip().str.upper()
reg = reg.dropna(subset=["LAT_DD", "LONG_DD"])
served = set(ndf["faa"].str.upper()) - {""}
reg["served"] = reg["FAA_ID"].isin(served)
T.stage("Coverage of the AK airport registry")
T.kv("registry airports", f"{len(reg)} (AK DOT&PF)")
T.kv("served by cargo network", f"{int(reg['served'].sum())} ({reg['served'].mean():.0%}) — "
     f"{len(reg) - int(reg['served'].sum())} airports have NO cargo leg in this dataset")
by_reg = reg.groupby("REGION")["served"].agg(["sum", "count"])
T.show(by_reg.assign(pct=(100 * by_reg["sum"] / by_reg["count"]).round(0)).rename(columns={"sum": "served", "count": "total"}),
       "coverage by region (served / total registry airports)", n=len(by_reg))
north = ndf.loc[ndf.geometry.y.idxmax()]
T.kv("northernmost served field", f"{north['name']} ({north['faa']}, region {north['region']})")

# ── figure: degree distribution ──
fig, ax = plt.subplots(figsize=(9, 5))
ax.hist(ndf["degree"], bins=range(1, int(ndf["degree"].max()) + 2), color="#4a90c2", align="left", rwidth=0.85)
ax.set_xlabel("degree (cargo legs at an airport)"); ax.set_ylabel("airports")
ax.set_title("Degree distribution — a few high-degree hubs, a long tail of degree-1 spokes")
fig.tight_layout()
p = OUT / "02_degree_dist.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Degree distribution — hub-and-spoke signature")

# ── figure: coverage map (registry grey vs served colored, by tier) ──
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(TGT)
ext = boundary.total_bounds
reg_g = gpd.GeoDataFrame(reg, geometry=gpd.points_from_xy(reg["LONG_DD"], reg["LAT_DD"]), crs=4326).to_crs(TGT)
fig, ax = plt.subplots(figsize=(12, 10))
boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
edf.plot(ax=ax, color="#1f77b4", linewidth=0.5, alpha=0.4, zorder=2)
reg_g[~reg_g["served"]].plot(ax=ax, color="#bbbbbb", markersize=8, zorder=3)
tier_c = {"spoke": "#2ca02c", "relay": "#ff7f0e", "regional hub": "#d62728", "trunk": "#7b1fa2"}
for tier, col in tier_c.items():
    s = ndf[ndf["tier"] == tier]
    ax.scatter(s.geometry.x, s.geometry.y, s=(s["degree"] * 8 + 12), c=col, edgecolor="white", linewidth=0.4, zorder=4)
ax.set_xlim(ext[0] - 1e5, ext[2] + 1e5); ax.set_ylim(ext[1] - 1e5, ext[3] + 1e5)
ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
ax.legend(handles=[Line2D([0], [0], marker="o", color="w", markerfacecolor="#bbbbbb", markersize=7, label=f"registry, no cargo leg ({int((~reg_g['served']).sum())})"),
                   Line2D([0], [0], marker="o", color="w", markerfacecolor="#7b1fa2", markersize=8, label="trunk (ANC/FAI)"),
                   Line2D([0], [0], marker="o", color="w", markerfacecolor="#d62728", markersize=8, label="regional hub"),
                   Line2D([0], [0], marker="o", color="w", markerfacecolor="#ff7f0e", markersize=7, label="relay"),
                   Line2D([0], [0], marker="o", color="w", markerfacecolor="#2ca02c", markersize=6, label="spoke")],
          loc="lower left", fontsize=8)
ax.set_title(f"Air-cargo coverage of the AK airport registry — {int(reg['served'].sum())}/{len(reg)} served")
p = OUT / "02_coverage.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Coverage — cargo-served airports (by tier) vs the registry airports with no cargo leg (grey)")
T.done()
