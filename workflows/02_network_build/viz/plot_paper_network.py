#!/usr/bin/env python3
"""Publication figure: the Alaska multimodal network as small multiples (one facet per mode).

Each facet highlights ONE mode — its edges + its hubs (sized by fuel capacity) + its nodes — in an
Okabe-Ito colourblind-safe colour, over a GREY, transparent context of the rest of the network, on a
sea / land / Canada basemap. Six facets: Road, Waterway (barge), Air (plane), Ice Road, the intermodal
connectors, and a full-network overview.

Best practices baked in: equal-area EPSG:3338; colourblind-safe + grayscale-distinct palette; shared
extent + basemap across panels (comparability); de-emphasised context vs highlighted layer;
area-proportional hub sizing with a size legend; one shared figure legend; a scale bar; embedded fonts;
vector PDF + 600-dpi PNG.

Prereq: run `python3 workflows/02_network_build/03_fetch_basemap.py` once (auto-invoked here if data/basemap is missing).
Run:    python3 workflows/02_network_build/viz/plot_paper_network.py   ->  outputs/02_network_build/reports/figs/network_facets.{pdf,png}
"""
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[3]  # repo root
PROJ = ROOT / "outputs" / "02_network_build"  # mmnet project dir: engine writes PROJ/output + PROJ/reports
os.environ.setdefault("MMNET_PROJECT", str(ROOT))  # mmnet.viz basemap reads <project>/data/
from mmnet.network import NetworkTables  # noqa: E402

warnings.filterwarnings("ignore")
CRS = 3338
FIGS = PROJ / "reports" / "figs"
DPI = int(os.environ.get("PAPER_DPI", "600"))       # set PAPER_DPI=150 for fast previews
SIMPLIFY_M = 250.0                                   # geometry simplification for plotting (state scale)

# ── palette (Okabe-Ito, colourblind-safe; distinct in grayscale) ──────────────
COL = {
    "Road":     "#111111",   # near-black backbone
    "Waterway": "#0072B2",   # blue (barge)
    "Air":      "#CC79A7",   # reddish purple
    "IceRoad":  "#56B4E9",   # sky blue
    "Transfer": "#D55E00",   # vermillion
    "Bridge":   "#E69F00",   # orange
}
CONTEXT = "#B9BBBD"          # de-emphasised "other modes"
SEA = "#EAF3F8"              # very light blue (axes background)
LAND = "#F1EAD9"            # tan
BORDER = "#B4AC93"           # muted country border

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 9, "axes.titlesize": 10,
    "legend.fontsize": 8, "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 600,
})


def _load_basemap(extent):
    """Natural Earth land + country borders, reprojected to 3338 (AK + Canada window). None if absent."""
    d = ROOT / "data" / "basemap"
    land_p, bord_p = d / "ne_10m_land.geojson", d / "ne_10m_admin_0_boundary_lines_land.geojson"
    if not land_p.exists():
        import subprocess
        print("[basemap] fetching Natural Earth (one-time)…")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "fetch_basemap.py")], check=False)
    if not land_p.exists():
        print("[basemap] unavailable — falling back to the Alaska outline only.")
        b = ROOT / "data" / "boundary.geojson"
        return (gpd.read_file(b).to_crs(CRS) if b.exists() else None), None

    def _ak(path):
        g = gpd.read_file(path)
        # antimeridian-safe: main AK+Canada window + the Aleutian tail west of 180°
        g = pd.concat([g.cx[-180:-105, 48:75], g.cx[168:180, 50:62]])
        g = gpd.GeoDataFrame(g, crs="EPSG:4326").to_crs(CRS)
        g["geometry"] = g.geometry.simplify(300)          # 10 m coastline is far finer than needed
        return g

    return _ak(land_p), _ak(bord_p)


def _alaska_extent(nodes, pad=0.03):
    """(x0, x1, y0, y1) covering ALL of Alaska — the dissolved-state boundary bounds (no clipping of
    the Aleutians or the SE panhandle). Off-Alaska air-leg outliers simply fall outside the frame.
    Falls back to the node 0.5–99.5 percentile if the boundary file is absent."""
    b = ROOT / "data" / "boundary.geojson"
    if b.exists():
        x0, y0, x1, y1 = gpd.read_file(b).to_crs(CRS).total_bounds
    else:
        x, y = nodes.geometry.x.values, nodes.geometry.y.values
        x0, x1 = np.percentile(x, [0.5, 99.5]); y0, y1 = np.percentile(y, [0.5, 99.5])
    dx, dy = x1 - x0, y1 - y0
    return (x0 - pad * dx, x1 + pad * dx, y0 - pad * dy, y1 + pad * dy)


def _build_graticule():
    """A light lon/lat graticule (10° meridians, 5° parallels) over Alaska, incl. the Aleutian tail."""
    from shapely.geometry import LineString
    lat, lon = np.arange(48, 73.01, 0.5), np.arange(-180, -124.99, 0.5)
    segs = [LineString([(m, la) for la in lat]) for m in range(-180, -124, 10)]
    segs += [LineString([(lo, p) for lo in lon]) for p in range(50, 73, 5)]
    lat2, lon2 = np.arange(50, 56.01, 0.5), np.arange(168, 180.01, 0.5)   # west of the dateline
    segs += [LineString([(m, la) for la in lat2]) for m in (170, 180)]
    segs += [LineString([(lo, p) for lo in lon2]) for p in (50, 55)]
    return gpd.GeoDataFrame(geometry=segs, crs="EPSG:4326").to_crs(CRS)


def _north_arrow(ax, extent):
    """A simple north pointer (top-right of the panel)."""
    x0, x1, y0, y1 = extent
    x = x0 + 0.95 * (x1 - x0); yb = y0 + 0.12 * (y1 - y0); h = 0.10 * (y1 - y0)
    ax.annotate("", xy=(x, yb + h), xytext=(x, yb),
                arrowprops=dict(arrowstyle="-|>", color="#222", lw=1.6), zorder=8)
    ax.text(x, yb + h + 0.015 * (y1 - y0), "N", ha="center", va="bottom",
            fontsize=10, fontweight="bold", zorder=8)


def _hub_sizes(cap):
    """Area-proportional marker sizes (radius ∝ √capacity), robustly clipped so no giant hub dominates.

    Kept small so the hubs annotate — not obscure — the network edges.
    """
    c = pd.to_numeric(cap, errors="coerce").astype(float)
    lo, hi = c.quantile(0.05), c.quantile(0.95)
    r = np.sqrt(c.clip(lo, hi))
    rn = (r - r.min()) / (r.max() - r.min() + 1e-9)
    return 5.0 + rn * 55.0


def _scalebar(ax, extent, km=500):
    x0, x1, y0, y1 = extent
    L = km * 1000
    x = x0 + 0.06 * (x1 - x0); y = y0 + 0.09 * (y1 - y0)
    ax.plot([x, x + L], [y, y], color="#222", lw=2.2, solid_capstyle="butt", zorder=7)
    ax.text(x + L / 2, y + 0.018 * (y1 - y0), f"{km} km", ha="center", va="bottom", fontsize=7, zorder=7)


def _basemap(ax, land, border, grat, extent):
    ax.set_facecolor(SEA)
    if land is not None and len(land):
        land.plot(ax=ax, color=LAND, edgecolor="none", zorder=0)
    if grat is not None and len(grat):
        grat.plot(ax=ax, color="#BCC6CE", linewidth=0.3, alpha=0.7, zorder=0.2)
    if border is not None and len(border):
        border.plot(ax=ax, color=BORDER, linewidth=0.5, zorder=0.5)
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor("#888"); s.set_linewidth(0.6)
    # rasterize every layer BELOW the hubs (basemap + edges + node dots) in the vector PDF, so the
    # detailed coastline + 90k edges become a light raster while hubs/anchors/scale bar/text stay vector.
    ax.set_rasterization_zorder(4)


def main() -> None:
    nt = NetworkTables.from_gpkg(PROJ / "output" / "03_network")
    nd = nt.nodes.copy(); nd["node_id"] = nd["node_id"].astype(int)
    e = nt.edges.copy(); e["from"] = e["from"].astype(int); e["to"] = e["to"].astype(int)
    hubs = nd[nd["is_hub"].fillna(False).astype(bool)].copy()
    dm = hubs["delivery_method"].astype(str)
    ss = hubs["snap_surface"].astype(str)
    htype = hubs["hub_type"].astype(str)

    extent = _alaska_extent(nd)
    land, border = _load_basemap(extent)
    grat = _build_graticule()

    # simplified geometry for FAST, crisp plotting at state scale (attributes preserved)
    e_plot = e.copy()
    e_plot["geometry"] = e.geometry.simplify(SIMPLIFY_M)

    # facet spec: (tag, title, edge-type predicate, hub mask, colour)
    def etype(*types):
        return e_plot[e_plot["type"].isin(types)]

    facets = [
        ("a", "Road",             etype("Road"),     dm.str.contains("Road"),  COL["Road"]),
        ("b", "Waterway (barge)", etype("Waterway"), dm.str.contains("Barge"), COL["Waterway"]),
        ("c", "Air (plane)",      etype("Air"),      dm.str.contains("Plane"), COL["Air"]),
        ("d", "Ice road",         etype("IceRoad"),  ss.eq("IceRoad"),         COL["IceRoad"]),
    ]

    # 3 rows × 2 cols suits the wide full-Alaska panels (a page-shaped figure, larger panels)
    panel_aspect = (extent[3] - extent[2]) / (extent[1] - extent[0])
    pw = 4.9
    fig, axes = plt.subplots(3, 2, figsize=(2 * pw, 3 * pw * panel_aspect + 0.2),
                             constrained_layout=True)
    axes = axes.ravel()

    def draw_context(ax):
        e_plot.plot(ax=ax, color=CONTEXT, linewidth=0.25, alpha=0.35, zorder=1, rasterized=True)

    def draw_hubs(ax, mask, color):
        h = hubs[mask.values]
        if not len(h):
            return
        sz = _hub_sizes(h["total_hub_capacity"])
        for mk, sub_m in (("^", htype[mask.values].eq("Supplier")), ("o", htype[mask.values].eq("Receiver"))):
            g = h[sub_m.values]
            if len(g):
                ax.scatter(g.geometry.x, g.geometry.y, s=sz[sub_m.values], marker=mk,
                           facecolor=color, edgecolor="white", linewidth=0.5, alpha=0.95, zorder=5)

    # ── the four mode facets ──
    for ax, (tag, title, sub, mask, color) in zip(axes, facets):
        _basemap(ax, land, border, grat, extent)
        draw_context(ax)
        ids = set(sub["from"]).union(sub["to"])
        mn = nd[nd["node_id"].isin(ids)]
        ax.scatter(mn.geometry.x, mn.geometry.y, s=0.6, color=color, alpha=0.28, zorder=3,
                   linewidths=0, rasterized=True)
        sub.plot(ax=ax, color=color, linewidth=0.55, zorder=2, rasterized=True)
        draw_hubs(ax, mask, color)
        ax.set_title(f"({tag}) {title}", loc="left", fontweight="bold")

    # ── (e) full-network overview ──
    ax = axes[4]; _basemap(ax, land, border, grat, extent)
    for t in ("Waterway", "IceRoad", "Road", "Air"):
        etype(t).plot(ax=ax, color=COL[t], linewidth=0.35, zorder=2, alpha=0.9, rasterized=True)
    for t in ("Transfer", "Bridge"):
        etype(t).plot(ax=ax, color=COL[t], linewidth=0.5, zorder=3, rasterized=True)
    sz = _hub_sizes(hubs["total_hub_capacity"])
    ax.scatter(hubs.geometry.x, hubs.geometry.y, s=sz * 0.5, marker="o", facecolor="white",
               edgecolor="black", linewidth=0.4, alpha=0.9, zorder=5)
    _scalebar(ax, extent)
    _north_arrow(ax, extent)
    ax.set_title("(e) Full multimodal network", loc="left", fontweight="bold")

    # ── shared legend in the 6th cell ──
    lax = axes[5]; lax.axis("off")
    modes_h = [Line2D([0], [0], color=COL[m], lw=2.6, label=lbl) for m, lbl in
               [("Road", "Road"), ("Waterway", "Waterway (barge)"), ("Air", "Air (plane)"),
                ("IceRoad", "Ice road"), ("Transfer", "Transfer edge"), ("Bridge", "Bridge / weld")]]
    ctx_h = [Line2D([0], [0], color=CONTEXT, lw=2.6, alpha=0.7, label="other modes (context)")]
    hub_h = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#555", markeredgecolor="k",
               markersize=7, label="hub — Receiver"),
        Line2D([0], [0], marker="^", color="w", markerfacecolor="#555", markeredgecolor="k",
               markersize=8, label="hub — Supplier"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="none", markeredgecolor="k",
               markersize=5, label="marker size ∝ fuel capacity"),
    ]
    lax.legend(handles=modes_h + ctx_h + hub_h, loc="upper center", frameon=False,
               ncol=2, handletextpad=0.7, labelspacing=0.8, columnspacing=1.3, fontsize=10,
               bbox_to_anchor=(0.5, 0.98))
    lax.text(0.5, 0.06, "Projection: NAD83 / Alaska Albers (EPSG:3338)  ·  graticule 10° / 5°",
             transform=lax.transAxes, ha="center", va="bottom", fontsize=8, style="italic", color="#555")

    FIGS.mkdir(parents=True, exist_ok=True)
    pdf, png = FIGS / "network_facets.pdf", FIGS / "network_facets.png"
    pdf_dpi = min(DPI, 350)                          # cap PDF raster layers (markers/text stay vector) → light file
    fig.savefig(pdf, dpi=pdf_dpi, bbox_inches="tight")
    fig.savefig(png, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"extent (3338): {[round(x) for x in extent]}  ·  png dpi={DPI} · pdf raster dpi={pdf_dpi}")
    print(f"wrote {pdf.relative_to(ROOT)}")
    print(f"wrote {png.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
