#!/usr/bin/env python3
"""
Comprehensive static plots of the final Stage-04 joined multimodal network.

Reads final_network/network_joined_{nodes,edges}.shp (EPSG:3338) and writes three
300-dpi PNGs to outputs/final_network_plots/:

  01_statewide_overview.png  - all modes muted + bold intermodal connectors + hubs
  02_connectors_detail.png   - 2x2: Bridges | Transfers | Joins | Combined seams
  03_hubs.png                - hubs by delivery method + by snap surface/type

Style: faint base transport modes, bold/bright connectors so the seams pop.
No new deps beyond geopandas + matplotlib.
"""
from pathlib import Path

import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent
NODES_SHP = ROOT / "final_network" / "network_joined_nodes" / "network_joined_nodes.shp"
EDGES_SHP = ROOT / "final_network" / "network_joined_edges" / "network_joined_edges.shp"
OUTDIR = ROOT / "outputs" / "final_network_plots"

# ---- colours -------------------------------------------------------------
BASE_STYLE = {  # faint context modes: (colour, linewidth, alpha, zorder)
    "Road":     ("#9e9e9e", 0.30, 0.35, 1),
    "Waterway": ("#7ba7c9", 0.30, 0.35, 1),
    "IceRoad":  ("#57c7d4", 0.45, 0.55, 2),
    "Air":      ("#d9c9a3", 0.25, 0.30, 1),
}
CONN = {  # bold connectors
    "Bridge_weld":   ("#ff8c00", "Bridge: within-mode weld"),
    "Bridge_cross":  ("#e21414", "Bridge: IceRoad->Road"),
    "Transfer_port": ("#1f6fd6", "Transfer: ports"),
    "Transfer_barge":("#17a54a", "Transfer: barge_hubs"),
    "Transfer_shore":("#d61fb0", "Transfer: shore:Barge<->Road"),
    "Join":          ("#7b1fa2", "Join: to-giant (<=20km)"),
}


def load():
    print(f"reading {NODES_SHP.name} ...")
    nodes = gpd.read_file(NODES_SHP)
    print(f"reading {EDGES_SHP.name} ...")
    edges = gpd.read_file(EDGES_SHP)
    nodes["hub_cap_num"] = pd.to_numeric(nodes["hub_cap"], errors="coerce")
    # node_id -> (x, y) for connector endpoint markers
    nx = nodes.set_index("node_id").geometry
    coords = {nid: (g.x, g.y) for nid, g in nx.items()}
    print(f"  nodes={len(nodes):,}  edges={len(edges):,}  CRS={edges.crs}")
    return nodes, edges, coords


def tidy(ax, title):
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(title, fontsize=11, fontweight="bold")


def plot_faint_base(ax, edges, alpha_mult=1.0, lw_mult=1.0):
    """Draw the four transport modes muted, as spatial context."""
    for t, (c, lw, a, z) in BASE_STYLE.items():
        sub = edges[edges["type"] == t]
        if len(sub):
            sub.plot(ax=ax, color=c, linewidth=lw * lw_mult,
                     alpha=a * alpha_mult, zorder=z)


def endpoint_markers(ax, edges_sub, coords, color, size=14, z=10):
    xs, ys = [], []
    for f, t in zip(edges_sub["from"], edges_sub["to"]):
        for nid in (f, t):
            if nid in coords:
                xs.append(coords[nid][0]); ys.append(coords[nid][1])
    ax.scatter(xs, ys, s=size, c=color, edgecolors="white",
               linewidths=0.3, zorder=z)


# ---- Figure 1: statewide overview ---------------------------------------
def fig_overview(nodes, edges, coords):
    fig, ax = plt.subplots(figsize=(15, 13))
    plot_faint_base(ax, edges)

    bridges = edges[edges["type"] == "Bridge"]
    b_weld = bridges[bridges["source"].str.startswith("weld")]
    b_cross = bridges[bridges["source"] == "bridge:IceRoad->Road"]
    if not len(b_cross):  # unicode arrow variant safety
        b_cross = bridges[bridges["source"].str.startswith("bridge")]
    transfers = edges[edges["type"] == "Transfer"]
    joins = edges[edges["type"] == "Join"]

    b_weld.plot(ax=ax, color=CONN["Bridge_weld"][0], linewidth=0.8, alpha=0.8, zorder=4)
    transfers.plot(ax=ax, color=CONN["Transfer_barge"][0], linewidth=1.4, alpha=0.9, zorder=5)
    joins.plot(ax=ax, color=CONN["Join"][0], linewidth=1.8, alpha=0.95, zorder=6)
    b_cross.plot(ax=ax, color=CONN["Bridge_cross"][0], linewidth=2.2, alpha=1.0, zorder=7)

    # hubs sized by capacity
    hubs = nodes[nodes["is_hub"]].copy()
    cap = hubs["hub_cap_num"].fillna(0)
    cap_max = cap.max() or 1  # avoid div-by-zero when no hub has a capacity
    sizes = 8 + 120 * (cap / cap_max)
    ax.scatter(hubs.geometry.x, hubs.geometry.y, s=sizes, c="#111111",
               marker="o", alpha=0.7, edgecolors="white", linewidths=0.3,
               zorder=8, label="fuel hub")

    legend = [
        Line2D([0], [0], color=BASE_STYLE["Road"][0], lw=2, label="Road"),
        Line2D([0], [0], color=BASE_STYLE["Waterway"][0], lw=2, label="Waterway"),
        Line2D([0], [0], color=BASE_STYLE["IceRoad"][0], lw=2, label="IceRoad"),
        Line2D([0], [0], color=BASE_STYLE["Air"][0], lw=2, label="Air"),
        Line2D([0], [0], color=CONN["Bridge_weld"][0], lw=2.5, label=f"Bridge weld ({len(b_weld)})"),
        Line2D([0], [0], color=CONN["Bridge_cross"][0], lw=2.5, label=f"Bridge IceRoad->Road ({len(b_cross)})"),
        Line2D([0], [0], color=CONN["Transfer_barge"][0], lw=2.5, label=f"Transfer ({len(transfers)})"),
        Line2D([0], [0], color=CONN["Join"][0], lw=2.5, label=f"Join ({len(joins)})"),
        Line2D([0], [0], color="#111111", marker="o", lw=0, label=f"Fuel hub ({len(hubs)})"),
    ]
    ax.legend(handles=legend, loc="upper left", fontsize=9, framealpha=0.9)
    tidy(ax, "Alaska final multimodal network (Stage-04 joined) — statewide overview")
    ax.text(0.99, 0.01, "EPSG:3338 (Alaska Albers, m)", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8, color="#666")
    out = OUTDIR / "01_statewide_overview.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


# ---- Figure 2: connector detail 2x2 -------------------------------------
def fig_connectors(nodes, edges, coords):
    fig, axes = plt.subplots(2, 2, figsize=(18, 16))
    axA, axB, axC, axD = axes.ravel()

    bridges = edges[edges["type"] == "Bridge"]
    b_weld = bridges[bridges["source"].str.startswith("weld")]
    b_cross = bridges[bridges["source"].str.startswith("bridge")]
    transfers = edges[edges["type"] == "Transfer"]
    t_port = transfers[transfers["source"] == "ports"]
    t_barge = transfers[transfers["source"] == "barge_hubs"]
    t_shore = transfers[transfers["source"].str.startswith("shore")]
    joins = edges[edges["type"] == "Join"]

    # Panel A - Bridges
    plot_faint_base(axA, edges, alpha_mult=0.6)
    b_weld.plot(ax=axA, color=CONN["Bridge_weld"][0], linewidth=0.6, alpha=0.7, zorder=4)
    b_cross.plot(ax=axA, color=CONN["Bridge_cross"][0], linewidth=2.6, alpha=1.0, zorder=6)
    endpoint_markers(axA, b_cross, coords, CONN["Bridge_cross"][0], size=45, z=8)
    axA.legend(handles=[
        Line2D([0], [0], color=CONN["Bridge_weld"][0], lw=2, label=f"weld:* ({len(b_weld)})"),
        Line2D([0], [0], color=CONN["Bridge_cross"][0], lw=3, label=f"bridge:IceRoad->Road ({len(b_cross)})"),
    ], loc="upper left", fontsize=9)
    tidy(axA, f"Bridges — ground stitches ({len(bridges)})")

    # Panel B - Transfers
    plot_faint_base(axB, edges, alpha_mult=0.6)
    t_port.plot(ax=axB, color=CONN["Transfer_port"][0], linewidth=1.6, alpha=0.9, zorder=5)
    t_barge.plot(ax=axB, color=CONN["Transfer_barge"][0], linewidth=1.6, alpha=0.9, zorder=5)
    t_shore.plot(ax=axB, color=CONN["Transfer_shore"][0], linewidth=2.2, alpha=1.0, zorder=6)
    for sub, col in ((t_port, CONN["Transfer_port"][0]),
                     (t_barge, CONN["Transfer_barge"][0]),
                     (t_shore, CONN["Transfer_shore"][0])):
        endpoint_markers(axB, sub, coords, col, size=18, z=7)
    axB.legend(handles=[
        Line2D([0], [0], color=CONN["Transfer_port"][0], lw=2.5, label=f"ports ({len(t_port)})"),
        Line2D([0], [0], color=CONN["Transfer_barge"][0], lw=2.5, label=f"barge_hubs ({len(t_barge)})"),
        Line2D([0], [0], color=CONN["Transfer_shore"][0], lw=2.5, label=f"shore:Barge<->Road ({len(t_shore)})"),
    ], loc="upper left", fontsize=9)
    tidy(axB, f"Transfers — intermodal barge handoffs ({len(transfers)})")

    # Panel C - Joins (with gap labels)
    plot_faint_base(axC, edges, alpha_mult=0.6)
    joins.plot(ax=axC, color=CONN["Join"][0], linewidth=2.4, alpha=0.95, zorder=6)
    endpoint_markers(axC, joins, coords, CONN["Join"][0], size=30, z=8)
    for _, row in joins.iterrows():
        c = row.geometry.centroid
        gap_km = (row["join_gap_m"] or 0) / 1000.0
        axC.annotate(f"{gap_km:.1f}", (c.x, c.y), fontsize=6, color="#4a148c",
                     ha="center", va="center", zorder=9)
    axC.legend(handles=[
        Line2D([0], [0], color=CONN["Join"][0], lw=3, label=f"Join ({len(joins)}), label=gap km"),
    ], loc="upper left", fontsize=9)
    tidy(axC, f"Joins — component welds <=20 km ({len(joins)}) — median gap ~7 km")

    # Panel D - Combined seams
    plot_faint_base(axD, edges, alpha_mult=0.6)
    b_weld.plot(ax=axD, color=CONN["Bridge_weld"][0], linewidth=0.6, alpha=0.6, zorder=4)
    transfers.plot(ax=axD, color=CONN["Transfer_barge"][0], linewidth=1.4, alpha=0.9, zorder=5)
    joins.plot(ax=axD, color=CONN["Join"][0], linewidth=1.8, alpha=0.95, zorder=6)
    b_cross.plot(ax=axD, color=CONN["Bridge_cross"][0], linewidth=2.4, alpha=1.0, zorder=7)
    axD.legend(handles=[
        Line2D([0], [0], color=CONN["Bridge_weld"][0], lw=2, label="Bridge weld"),
        Line2D([0], [0], color=CONN["Bridge_cross"][0], lw=2.5, label="Bridge IceRoad->Road"),
        Line2D([0], [0], color=CONN["Transfer_barge"][0], lw=2, label="Transfer"),
        Line2D([0], [0], color=CONN["Join"][0], lw=2, label="Join"),
    ], loc="upper left", fontsize=9)
    tidy(axD, "All intermodal seams combined")

    fig.suptitle("Final network — intermodal connector detail", fontsize=15, fontweight="bold")
    out = OUTDIR / "02_connectors_detail.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


# ---- Figure 3: hubs ------------------------------------------------------
def fig_hubs(nodes, edges, coords):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 11))
    hubs = nodes[nodes["is_hub"]].copy()

    # Left: by delivery method
    plot_faint_base(ax1, edges, alpha_mult=0.5)
    dm_order = ["Road", "Barge", "Barge or Road", "Plane", "Barge or Plane",
                "Plane or Road", "Barge or Plane or Road"]
    dm_colors = ["#7b1fa2", "#1f6fd6", "#17a54a", "#e21414",
                 "#ff8c00", "#00897b", "#5d4037"]
    for dm, col in zip(dm_order, dm_colors):
        sub = hubs[hubs["deliv_meth"] == dm]
        ax1.scatter(sub.geometry.x, sub.geometry.y, s=28, c=col, alpha=0.85,
                    edgecolors="white", linewidths=0.3, zorder=8,
                    label=f"{dm} ({len(sub)})")
    ax1.legend(loc="upper left", fontsize=8, title="delivery method", framealpha=0.9)
    tidy(ax1, f"Fuel hubs by delivery method (n={len(hubs)})")

    # Right: by snap surface + hub_type marker
    plot_faint_base(ax2, edges, alpha_mult=0.5)
    for htype, marker in (("Receiver", "o"), ("Supplier", "^")):
        road = hubs[(hubs["snap_surf"] == "Road") & (hubs["hub_type"] == htype)]
        ax2.scatter(road.geometry.x, road.geometry.y, s=22, c="#9e9e9e",
                    marker=marker, alpha=0.7, edgecolors="#555", linewidths=0.3,
                    zorder=7, label=f"Road / {htype} ({len(road)})")
    ice = hubs[hubs["snap_surf"] != "Road"]
    ax2.scatter(ice.geometry.x, ice.geometry.y, s=240, c="#e21414", marker="*",
                edgecolors="black", linewidths=0.6, zorder=10,
                label=f"IceRoad-snapped ({len(ice)})")
    for _, row in ice.iterrows():
        ax2.annotate(row["hub_id"], (row.geometry.x, row.geometry.y),
                     fontsize=8, color="#b71c1c", fontweight="bold",
                     xytext=(6, 6), textcoords="offset points", zorder=11)
    ax2.legend(loc="upper left", fontsize=8, title="snap surface / type", framealpha=0.9)
    tidy(ax2, "Fuel hubs by snap surface — the 4 IceRoad snaps highlighted")

    fig.suptitle("Final network — fuel hubs (384)", fontsize=15, fontweight="bold")
    out = OUTDIR / "03_hubs.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    nodes, edges, coords = load()
    fig_overview(nodes, edges, coords)
    fig_connectors(nodes, edges, coords)
    fig_hubs(nodes, edges, coords)
    print("done ->", OUTDIR)


if __name__ == "__main__":
    main()
