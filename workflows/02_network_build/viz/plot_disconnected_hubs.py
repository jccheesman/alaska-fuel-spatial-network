#!/usr/bin/env python3
"""Visualize the previously-disconnected fuel hubs and the manual connections that (try to) fix them.

"Previously disconnected" = hubs OFF the giant component in the frozen final_network (the old
deliverable). We colour each by whether the rebuilt network (with the manual_connections layer) now
pulls it into the giant, and overlay the hand-drawn manual lines coloured by mode.

Outputs: outputs/figures/disconnected_hubs.png  (+ a per-region zoom panel)
Run (in the project .venv):
    python workflows/02_network_build/viz/plot_disconnected_hubs.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "figures" / "disconnected_hubs.png"

OLD_NODES = ROOT / "final_network" / "network_joined_nodes" / "network_joined_nodes.shp"
NEW_NODES = ROOT / "outputs" / "02_network_build" / "output" / "04_network_joined__nodes.gpkg"
NEW_EDGES = ROOT / "outputs" / "02_network_build" / "output" / "04_network_joined__edges.gpkg"
HUBS = ROOT / "outputs" / "02_network_build" / "output" / "02_hubs.gpkg"
MANUAL = ROOT / "inputs" / "mannual_connections" / "mannual_connections.shp"
BOUNDARY = ROOT / "data" / "boundary.geojson"

MODE_COLOR = {"Barge": "#1f77b4", "Plane": "#ff7f0e", "Road": "#8c564b"}


def _int(s):
    return pd.to_numeric(s, errors="coerce").fillna(0).astype(int)


def _hub_giant(nodes):
    h = nodes[_int(nodes["is_hub"]) == 1].copy()
    h["is_giant"] = _int(h["is_giant"])
    h["hub_id"] = h["hub_id"].astype(str)
    return h.groupby("hub_id")["is_giant"].max()


def main():
    hubs = gpd.read_file(HUBS).to_crs(3338)
    hubs["hub_id"] = hubs["hub_id"].astype(str)
    old_g = _hub_giant(gpd.read_file(OLD_NODES))
    new_g = _hub_giant(gpd.read_file(NEW_NODES))
    edges = gpd.read_file(NEW_EDGES).to_crs(3338)
    manual = gpd.read_file(MANUAL).to_crs(3338)
    bnd = gpd.read_file(BOUNDARY).to_crs(3338)

    disc_ids = [h for h in old_g[old_g == 0].index if h in set(hubs["hub_id"])]
    d = hubs[hubs["hub_id"].isin(disc_ids)].copy()
    d["rescued"] = d["hub_id"].map(lambda h: new_g.get(h, 0) == 1)

    ww = edges[edges["type"] == "Waterway"]
    rd = edges[edges["type"] == "Road"]

    def draw(ax, label_fs=8, marker_scale=1.0):
        bnd.boundary.plot(ax=ax, color="0.8", linewidth=0.6, zorder=0)
        ww.plot(ax=ax, color="#cfe0ee", linewidth=0.25, zorder=1)
        rd.plot(ax=ax, color="0.85", linewidth=0.15, zorder=1)
        for mode, sub in manual.groupby("Mode"):
            sub.plot(ax=ax, color=MODE_COLOR.get(mode, "k"), linewidth=2.0, zorder=3)
        resc, still = d[d["rescued"]], d[~d["rescued"]]
        resc.plot(ax=ax, color="#2ca02c", markersize=70 * marker_scale, edgecolor="k",
                  linewidth=0.5, zorder=5)
        still.plot(ax=ax, marker="X", color="#d62728", markersize=95 * marker_scale,
                   edgecolor="k", linewidth=0.5, zorder=6)
        for _, r in d.iterrows():
            ax.annotate(r["hub_community"], (r.geometry.x, r.geometry.y),
                        xytext=(5, 3), textcoords="offset points", fontsize=label_fs,
                        color=("#1a6b1a" if r["rescued"] else "#8a1a1a"),
                        fontweight="bold", zorder=7)

    fig = plt.figure(figsize=(17, 10))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.15, 1])
    ax = fig.add_subplot(gs[0, 0])
    axz = fig.add_subplot(gs[0, 1])
    draw(ax)
    draw(axz, label_fs=10, marker_scale=1.8)

    # Kodiak-Island zoom: frame the rescued barge cluster (Larsen Bay / Karluk / Akhiok)
    kod = d[d["hub_community"].isin(["Larsen Bay", "Karluk", "Akhiok"])]
    if len(kod):
        pad = 90_000
        xmin, ymin, xmax, ymax = kod.total_bounds
        # include the barge routes' seaward ends
        mb = manual[manual["Mode"] == "Barge"]
        mb_near = mb[mb.geometry.intersects(kod.buffer(pad).union_all())]
        if len(mb_near):
            bx0, by0, bx1, by1 = mb_near.total_bounds
            xmin, ymin = min(xmin, bx0), min(ymin, by0)
            xmax, ymax = max(xmax, bx1), max(ymax, by1)
        axz.set_xlim(xmin - pad, xmax + pad)
        axz.set_ylim(ymin - pad, ymax + pad)
        import matplotlib.patches as mpatches
        ax.add_patch(mpatches.Rectangle((xmin - pad, ymin - pad), (xmax - xmin) + 2 * pad,
                     (ymax - ymin) + 2 * pad, fill=False, edgecolor="k", linewidth=1.0,
                     linestyle="--", zorder=8))
    axz.set_title("Kodiak Island — rescued barge hubs\n(routes weld to the marine spine)", fontsize=11)

    legend = [
        plt.Line2D([], [], color=MODE_COLOR["Barge"], lw=2, label="manual Barge line"),
        plt.Line2D([], [], color=MODE_COLOR["Plane"], lw=2, label="manual Plane line"),
        plt.Line2D([], [], color=MODE_COLOR["Road"], lw=2, label="manual Road line"),
        plt.Line2D([], [], marker="o", color="w", markerfacecolor="#2ca02c", markeredgecolor="k",
                   markersize=10, label=f"rescued by manual layer ({int(d['rescued'].sum())})"),
        plt.Line2D([], [], marker="X", color="w", markerfacecolor="#d62728", markeredgecolor="k",
                   markersize=11, label=f"still off-giant ({int((~d['rescued']).sum())})"),
    ]
    ax.legend(handles=legend, loc="lower left", fontsize=9, framealpha=0.9)
    ax.set_title(f"Previously disconnected fuel hubs ({len(d)}) — "
                 f"{int(d['rescued'].sum())} rescued, {int((~d['rescued']).sum())} still off-giant\n"
                 f"(off giant in frozen final_network → status in rebuild with manual_connections)",
                 fontsize=12)
    for a in (ax, axz):
        a.set_axis_off()
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=170, bbox_inches="tight")
    print(f"wrote {OUT.relative_to(ROOT)}  "
          f"({int(d['rescued'].sum())} rescued / {int((~d['rescued']).sum())} still off)")


if __name__ == "__main__":
    main()
