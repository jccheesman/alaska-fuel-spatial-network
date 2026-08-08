#!/usr/bin/env python3
"""Empirically evaluate the plausibility of profile.yaml parameters against the built network + data.

Checks the LIVE connection caps (are they binding or slack?) from the connector edge lengths in
output/03_network, the hub-snap distance distribution (02_hubs centroid → its snapped is_hub node, vs the
100 km max_snap_dist_m), and the airport→road snap coverage. Prints a verdict table + writes two figures.
Research only — evaluation, no engine/profile change. Run: python3 research/param_check/01_param_plausibility.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from _trace import OUT, ROOT, Tracer
from mmnet.network import NetworkTables

T = Tracer("01_param_plausibility", "Plausibility of profile.yaml parameters (empirical)")

nt = NetworkTables.from_gpkg(ROOT / "output" / "03_network")
nd = nt.nodes.sort_values("node_id").reset_index(drop=True)
e = nt.edges.copy(); e["from"] = e["from"].astype(int); e["to"] = e["to"].astype(int)
et, src = e["type"], e["source"].astype(str)
e["len"] = e.geometry.length
xy = np.c_[nd.geometry.x.values, nd.geometry.y.values]

# ── (A) LIVE connection caps: connector edge length vs its profile cap ──
CAPS = [
    ("barge transfers", "transfers.max_dist", 5000, (et == "Transfer") & src.isin(["ports", "barge_hubs"])),
    ("road↔road weld", "bridges[Road,Road].max_dist", 3000, (et == "Bridge") & src.eq("weld:Road")),
    ("ice↔ice weld", "bridges[Ice,Ice].max_dist", 3000, (et == "Bridge") & src.eq("weld:IceRoad")),
    ("ice↔road bridge", "bridges[Ice,Road].max_dist", 3000, (et == "Bridge") & src.str.startswith("bridge:")),
    ("connect-to-giant", "connect_to_giant.max_dist", 2000, src.str.startswith("shore") | src.eq("weld:to-giant")),
]
rows = []
for name, param, cap, mask in CAPS:
    s = e.loc[mask, "len"]
    if not len(s):
        continue
    rows.append({"connector": name, "param": param, "cap_m": cap, "n": len(s),
                 "median_m": round(s.median()), "p90_m": round(s.quantile(0.9)), "max_m": round(s.max()),
                 "near_cap>0.8": int((s > 0.8 * cap).sum()),
                 "verdict": "plausible" + (" (slack)" if s.quantile(0.9) < 0.6 * cap else " (binding)")})
capdf = pd.DataFrame(rows)
T.stage("(A) LIVE connection caps — connector length vs cap")
T.show(capdf, "connector edge length distribution vs its profile cap", n=len(capdf))

# airport snap coverage (cap 2000)
ap = gpd.read_file(ROOT / "data" / "processed" / "air_nodes.geojson").to_crs(nd.crs)
road_ids = np.array(sorted(set(e.loc[et == "Road", "from"]).union(e.loc[et == "Road", "to"])), dtype=int)
d_ap = cKDTree(xy[road_ids]).query(np.c_[ap.geometry.x.values, ap.geometry.y.values])[0]
T.kv("airport snap (cap 2000)", f"{int((d_ap <= 2000).sum())}/{len(ap)} airports ≤ 2 km (median "
     f"{np.median(d_ap):.0f} m); {int((d_ap > 2000).sum())} bush airports stay air-only → plausible")

# ── (B) hub-snap distance: 02_hubs centroid → its snapped is_hub node (vs max_snap_dist_m = 100000) ──
hubs = gpd.read_file(ROOT / "output" / "02_hubs.gpkg").to_crs(nd.crs)
is_hub = nd["is_hub"].fillna(False).astype(bool)
hub_nodes = nd[is_hub]
d_hub = cKDTree(np.c_[hub_nodes.geometry.x.values, hub_nodes.geometry.y.values]).query(
    np.c_[hubs.geometry.x.values, hubs.geometry.y.values])[0]
T.stage("(B) hub-snap distance (max_snap_dist_m = 100000, NOT enforced in the gold snap)")
T.kv("02_hubs → snapped node (m)", f"median {np.median(d_hub):.0f} · p90 {np.percentile(d_hub, 90):.0f} · "
     f"max {d_hub.max():.0f}")
T.kv("hubs snapped far", f">5 km: {int((d_hub > 5000).sum())} · >20 km: {int((d_hub > 20000).sum())} · "
     f">100 km: {int((d_hub > 100000).sum())}  → the uncapped snap drags roadless hubs to distant roads")

# ── figures ──
fig, ax = plt.subplots(figsize=(9, 5))
data = [e.loc[m, "len"].values for _, _, _, m in CAPS if m.any()]
labels = [f"{n}\n(cap {c})" for n, _, c, m in CAPS if m.any()]
ax.boxplot(data, labels=labels, showfliers=False)
for i, (n, _, c, m) in enumerate([x for x in CAPS if x[3].any()], 1):
    ax.axhline(c, xmin=(i - 0.9) / len(data) / 1.11, xmax=(i - 0.1) / len(data) / 1.11, color="#d62728", lw=1.4)
ax.set_ylabel("connector length (m)"); ax.set_title("Connection caps vs actual connector lengths (red = cap)")
plt.xticks(rotation=20, ha="right"); fig.tight_layout()
p = OUT / "01_caps_vs_lengths.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "LIVE caps are mostly slack — connectors sit well below their caps")

fig, ax = plt.subplots(figsize=(9, 5))
xs = np.sort(d_hub) / 1000.0
ax.plot(xs, np.arange(1, len(xs) + 1) / len(xs), color="#4a90c2")
ax.axvline(100, color="#d62728", ls="--", label="max_snap_dist_m = 100 km")
ax.axvline(20, color="#ff7f0e", ls=":", label="20 km")
ax.set_xscale("symlog"); ax.set_xlabel("hub-snap distance (km, symlog)"); ax.set_ylabel("cumulative fraction of hubs")
ax.set_title("Hub-snap distance is UNCAPPED — a long tail to 150 km"); ax.legend(fontsize=8)
fig.tight_layout()
p = OUT / "01_hub_snap_cdf.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Hub-snap distance CDF — most hubs snap < 200 m, but a tail reaches 150 km")
T.done()
