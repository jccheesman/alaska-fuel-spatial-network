import sys, importlib.util, zipfile
sys.path.insert(0, "source_scripts")
import geopandas as gpd, pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mmnet.config import load_profile
from mmnet.steps.consolidate import consolidate_facilities
from mmnet.steps.tag import passthrough_tag
from mmnet.steps.hubs import aggregate_hubs
from mmnet.assemble import connect_multimodal
SP = "/tmp/claude-0/-home-user/4c77f68e-28f7-50b1-ae12-e16f9b5239a9/scratchpad"

# --- inputs: the frozen network's lines (Road / IceRoad / Waterway) + hubs from the published table
z = "final_network/network_joined_edges.zip"
with zipfile.ZipFile(z) as zf: shp = [n for n in zf.namelist() if n.endswith(".shp")][0]
E = gpd.read_file(f"zip://{z}!{shp}", columns=["type"])
roads = E[E["type"].isin(["Road", "IceRoad", "Air"])].reset_index(drop=True)
water = E[E["type"] == "Waterway"].reset_index(drop=True)
spec = importlib.util.spec_from_file_location("nr", "workflows/02_network_build/00_normalize_raw.py"); nr = importlib.util.module_from_spec(spec); spec.loader.exec_module(nr)
nr.normalize_entry(next(e for e in nr.SPEC if e["name"] == "facilities"))
p = load_profile("workflows/02_network_build/profile.yaml"); cfg = p.to_pipeline_config(); pr = p.to_params(); cfg.delivery_fallback = None
fac = consolidate_facilities("data/interim/facilities.csv", pr, 4326, 3338, cfg)
hubs = aggregate_hubs(passthrough_tag(fac), pr)
print("hubs", len(hubs), hubs["delivery_method"].value_counts().head(6).to_dict())

def run(mode_aware):
    st = {"Road", "IceRoad"}
    sm = {"Road": "Road", "IceRoad": "IceRoad", "Waterway": "Barge", "Air": "Plane"} if mode_aware else None
    fb = {"Waterway", "Air"} if mode_aware else None
    nodes, edges, s = connect_multimodal(roads, hubs, {"Road"}, [], {}, snap_types=st, waterway=water,
                                         waterway_label="Waterway", max_snap_dist=25000, snap_modes=sm, snap_fallback_types=fb)
    hs = s["hub_snaps"].copy()
    hs = hs.merge(hubs[["hub_id", "hub_community", "delivery_method", "total_hub_capacity"]], on="hub_id")
    xy = nodes.set_index("node_id").geometry
    hs["hx"] = hubs.set_index("hub_id").geometry.x.reindex(hs.hub_id).values
    hs["hy"] = hubs.set_index("hub_id").geometry.y.reindex(hs.hub_id).values
    hs["nx"] = [xy[int(n)].x if pd.notna(n) else np.nan for n in hs.node_id]
    hs["ny"] = [xy[int(n)].y if pd.notna(n) else np.nan for n in hs.node_id]
    return hs

A, B = run(False), run(True)
for name, hs in (("current (road/ice only)", A), ("road-first + own-mode fallback", B)):
    print(name, hs.status.str.split(":").str[0].value_counts().to_dict(), "| surface:", hs.snap_surface.value_counts().to_dict(),
          "| median snap m (placed):", round(hs[hs.status == "placed"].snap_dist_m.median()), "| >10 km:", int((hs[hs.status == "placed"].snap_dist_m > 10000).sum()))
A.to_csv(f"{SP}/snap_current.csv", index=False); B.to_csv(f"{SP}/snap_fallback.csv", index=False)

# --- figure
def centre(name):
    h = hubs[hubs.hub_community.astype(str).str.upper() == name.upper()]
    return (h.geometry.x.iloc[0], h.geometry.y.iloc[0]) if len(h) else None
zooms = [("Prince William Sound (Cordova / Chenega)", centre("Cordova"), 120_000), ("Lower Yukon (Grayling / Holy Cross)", centre("Holy Cross"), 120_000), ("Alaska Peninsula (Port Moller / Ivanof Bay)", centre("Port Moller"), 160_000)]
fig, axes = plt.subplots(4, 2, figsize=(16, 30))
col = {"placed:Road": "#2e7d32", "placed:IceRoad": "#6a1b9a", "placed:Waterway": "#1565c0", "placed:Air": "#ef6c00", "unplaced": "#c62828", "merged": "#999999"}
def draw(ax, hs, title, c=None, half=None):
    water.plot(ax=ax, color="#9ecae1", linewidth=0.6, zorder=1)
    roads[roads["type"] != "Air"].plot(ax=ax, color="#bdbdbd", linewidth=0.5, zorder=2)
    roads[roads["type"] == "Air"].plot(ax=ax, color="#ffe0b2", linewidth=0.4, zorder=1)
    for r in hs.itertuples():
        k = "unplaced" if r.status.startswith("unplaced") else ("merged" if r.status.startswith("merged") else f"placed:{str(r.snap_surface).split('+')[0]}")
        if pd.notna(r.nx):
            ax.plot([r.hx, r.nx], [r.hy, r.ny], color=col.get(k, "k"), linewidth=0.8, alpha=0.8, zorder=3)
            ax.scatter(r.nx, r.ny, s=14, color=col.get(k, "k"), zorder=5, edgecolor="white", linewidth=0.3)
        ax.scatter(r.hx, r.hy, s=10, facecolor="none", edgecolor=col.get(k, "k"), zorder=4, linewidth=0.7)
        if c is not None and ((r.hx - c[0])**2 + (r.hy - c[1])**2) ** 0.5 < half * 0.95:
            ax.annotate(r.hub_community, (r.hx, r.hy), fontsize=6.5, xytext=(3, 3), textcoords="offset points")
    if c is not None:
        ax.set_xlim(c[0] - half, c[0] + half); ax.set_ylim(c[1] - half, c[1] + half)
    else:
        b = hubs.total_bounds; ax.set_xlim(b[0] - 50_000, b[2] + 50_000); ax.set_ylim(b[1] - 50_000, b[3] + 50_000)
    ax.set_title(title, fontsize=11, loc="left"); ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
    n = hs.status.str.startswith("placed").sum(); u = hs.status.str.startswith("unplaced").sum()
    ax.text(0.01, 0.01, f"placed {n} · unplaced {u} · placed >10 km from hub: {(hs[hs.status=='placed'].snap_dist_m>10000).sum()}", transform=ax.transAxes, fontsize=8, va="bottom")
draw(axes[0, 0], A, "CURRENT — hubs snap to road/ice only, 25 km cap")
draw(axes[0, 1], B, "ROAD-FIRST + FALLBACK — no road within 25 km? barge hub → waterway, fly-in hub → airport")
for i, (t, c, half) in enumerate(zooms, start=1):
    draw(axes[i, 0], A, f"current · {t}", c, half); draw(axes[i, 1], B, f"road-first + fallback · {t}", c, half)
from matplotlib.lines import Line2D
fig.legend(handles=[Line2D([0], [0], marker="o", color=v, label=k, linestyle="-") for k, v in col.items()] +
           [Line2D([0], [0], color="#9ecae1", label="waterway"), Line2D([0], [0], color="#bdbdbd", label="road / ice road"), Line2D([0], [0], color="#ffe0b2", label="air legs")],
           loc="lower center", ncol=7, fontsize=9, frameon=False)
fig.suptitle("Where each fuel hub attaches to the network: hollow circle = hub centroid, line = snap, dot = node it lands on", fontsize=13, y=0.995)
fig.tight_layout(rect=(0, 0.02, 1, 0.985))
fig.savefig(f"{SP}/snap_comparison.png", dpi=110, facecolor="white")
print("saved")
