"""Map figures for the multimodal pipeline — the package's plotting layer.

Three share-ready maps on a sea/land + transport-network basemap:

  - `plot_before_after` — two stacked panels (input vs output) for any step.
  - `plot_hubs`         — aggregated facilities + hub centroids, then the hubs placed on the road.
  - `plot_network`      — the final network: edges by type, all nodes, hubs by delivery method.

Basemap (`data/boundary.geojson`, optional `data/coastline.geojson`) and the default figure
directory (`reports/figs`) resolve under the project root (:func:`mmnet.config.project_root`);
pass `out_dir` to write elsewhere. Pure presentation — no build step is called here.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

# Basemap palette + per-layer line colors (shared by every map).
_LINE_COLORS = {"roads": "#6b6b6b", "water": "#1f77b4", "airways": "#9467bd"}
_SEA_COLOR = "#cfe8f5"
_LAND_COLOR = "#f1ead6"
_COAST_COLOR = "#34699a"

# Distinct styles for named reference overlays (ports, airports, ...), cycled by order.
_OVERLAY_STYLES = [
    {"color": "#1565c0", "marker": "s", "markersize": 70},   # blue square
    {"color": "#2e7d32", "marker": "^", "markersize": 80},   # green triangle
    {"color": "#6a1b9a", "marker": "D", "markersize": 55},   # purple diamond
    {"color": "#ef6c00", "marker": "P", "markersize": 80},   # orange plus
]

_HUB_SHAPES = ["o", "s", "^", "D", "v", "P", "X", "*"]
_EDGE_TYPE_COLORS = {"Road": "#6b6b6b", "Waterway": "#1f77b4", "Air": "#9467bd",
                     "IceRoad": "#17becf", "Transfer": "#d62728", "Bridge": "#ff7f0e"}
_EDGE_TYPE_ORDER = ["Road", "Waterway", "Air", "IceRoad", "Transfer", "Bridge"]


def _project() -> Path:
    from .config import project_root

    return project_root()


def _has_geom(df) -> bool:
    return isinstance(df, gpd.GeoDataFrame) and "geometry" in df.columns and df.geometry.notna().any()


def _bounds_union(frames) -> tuple[float, float, float, float] | None:
    bs = [f.total_bounds for f in frames if _has_geom(f)]
    if not bs:
        return None
    minx = min(b[0] for b in bs); miny = min(b[1] for b in bs)
    maxx = max(b[2] for b in bs); maxy = max(b[3] for b in bs)
    padx = (maxx - minx) * 0.05 or 100.0
    pady = (maxy - miny) * 0.05 or 100.0
    return (minx - padx, miny - pady, maxx + padx, maxy + pady)


def _reproject_layers(layers, target_crs) -> dict:
    out = {}
    for name, g in (layers or {}).items():
        try:
            gg = g.to_crs(target_crs) if (target_crs is not None and getattr(g, "crs", None) is not None) else g
            if gg is not None and len(gg):
                out[name] = gg
        except Exception:
            pass
    return out


def _load_basemap(target_crs):
    """Return (land, sea, coast) for the sea/land basemap (or Nones)."""
    project = _project()
    land = sea = coast = None
    try:
        b = gpd.read_file(project / "data" / "boundary.geojson")
        if target_crs is not None:
            b = b.to_crs(target_crs)
        if "part" in b.columns:
            land, sea = b[b["part"] == "land"], b[b["part"] == "sea"]
        else:
            land = b
    except Exception:
        pass
    cpath = project / "data" / "coastline.geojson"
    if cpath.exists():
        try:
            coast = gpd.read_file(cpath)
            if target_crs is not None:
                coast = coast.to_crs(target_crs)
        except Exception:
            coast = None
    return land, sea, coast


def _draw_basemap(ax, land, sea, coast, line_layers):
    """Sea + land fill, coastline, then the transport network lines — all under the data."""
    if sea is not None and len(sea):
        sea.plot(ax=ax, color=_SEA_COLOR, edgecolor="none", zorder=0)
    if land is not None and len(land):
        land.plot(ax=ax, color=_LAND_COLOR, edgecolor="none", zorder=0)
    if coast is not None and len(coast):
        coast.plot(ax=ax, color=_COAST_COLOR, linewidth=1.3, zorder=1)
    for name, g in (line_layers or {}).items():
        if g is not None and len(g):
            g.plot(ax=ax, color=_LINE_COLORS.get(name, "#7a7a7a"), linewidth=1.4, zorder=2)


def _fit_extent(extent, asp):
    """Grow the shorter side of `extent` so its height/width ratio == asp (keeps it centered)."""
    minx, miny, maxx, maxy = extent
    dx, dy = maxx - minx, maxy - miny
    cur = (dy / dx) if dx > 0 else asp
    if cur < asp:
        ny = dx * asp; cy = (miny + maxy) / 2
        miny, maxy = cy - ny / 2, cy + ny / 2
    elif cur > asp:
        nx = dy / asp; cx = (minx + maxx) / 2
        minx, maxx = cx - nx / 2, cx + nx / 2
    return (minx, miny, maxx, maxy)


def _stacked_fig(extent, n_rows, width=10.5):
    """A vertically-stacked figure sized to the (clamped) data aspect, so axes fill it with
    aspect='equal' and there is no whitespace between the title and the panels.

    Returns (fig, axes, fitted_extent). Panels are stacked top-to-bottom (taller figure).
    """
    dx = (extent[2] - extent[0]) if extent else 1.0
    dy = (extent[3] - extent[1]) if extent else 1.0
    asp = (dy / dx) if dx > 0 else 0.7
    asp = min(max(asp, 0.6), 1.4)
    fitted = _fit_extent(extent, asp) if extent else extent
    fig, axes = plt.subplots(n_rows, 1, figsize=(width, width * asp * n_rows),
                             squeeze=False, constrained_layout=True)
    return fig, axes[:, 0], fitted


def _savefig(fig, slug: str, dpi: int = 120, out_dir: str | Path | None = None) -> Path:
    """Save a figure to <out_dir or reports/figs>/<slug>.png at the given dpi."""
    project = _project()
    base = Path(out_dir) if out_dir else project / "reports" / "figs"
    base.mkdir(parents=True, exist_ok=True)
    png = base / f"{slug}.png"
    fig.savefig(png, dpi=dpi, bbox_inches="tight")
    try:
        rel = png.relative_to(project)
    except ValueError:
        rel = png
    print(f"map -> {rel}")
    return png


def plot_before_after(before, after, title: str = "", slug: str = "step",
                      boundary_path: str | Path | None = None,
                      before_label: str = "input", after_label: str = "output",
                      overlays: dict | None = None, label_col: str | None = None,
                      lines: dict | None = None, dpi: int = 120,
                      out_dir: str | Path | None = None) -> Path | None:
    """Two stacked maps (top = before, bottom = after) on a sea/land + network basemap.

    `before` may be None (single panel). `overlays` = {label: GeoDataFrame} of point
    reference layers (ports/airports) drawn on both panels. `lines` = {name: GeoDataFrame}
    of network line layers (roads/water/airways) drawn under the data. `label_col`
    annotates each point with that column. Panels stack vertically and the figure is sized
    to the data aspect, so it is tall with no whitespace between the title and the maps.
    """
    from matplotlib.lines import Line2D

    target_crs = getattr(after, "crs", None) or getattr(before, "crs", None)
    land, sea, coast = _load_basemap(target_crs)
    line_layers = _reproject_layers(lines, target_crs)
    ov = _reproject_layers(overlays, target_crs)

    panels = [(before_label, before), (after_label, after)]
    panels = [(lbl, df) for lbl, df in panels if df is not None]
    # include the water layer in the extent so the offshore waterway (in the sea) is visible
    water = [line_layers["water"]] if "water" in line_layers else []
    extent = _bounds_union([df for _, df in panels] + list(ov.values()) + water)

    fig, axes, extent = _stacked_fig(extent, len(panels))
    for ax, (lbl, df) in zip(axes, panels):
        _draw_basemap(ax, land, sea, coast, line_layers)
        if _has_geom(df):
            if any("Line" in g for g in df.geom_type.unique()):
                df.plot(ax=ax, color="#c1272d", linewidth=2.0, zorder=4)
            else:
                df.plot(ax=ax, color="#c1272d", markersize=36, zorder=4, edgecolor="white", linewidth=0.5)
                if label_col and label_col in df.columns:
                    for geom, val in zip(df.geometry, df[label_col]):
                        if geom is not None and not geom.is_empty:
                            ax.annotate(str(val), (geom.x, geom.y), xytext=(3, 3),
                                        textcoords="offset points", fontsize=6, color="#222", zorder=6)
        for i, (name, gdf) in enumerate(ov.items()):
            st = _OVERLAY_STYLES[i % len(_OVERLAY_STYLES)]
            gdf.plot(ax=ax, color=st["color"], marker=st["marker"], markersize=st["markersize"],
                     edgecolor="white", linewidth=0.6, zorder=5)
        # legend: network lines + point overlays
        handles = [Line2D([0], [0], color=_LINE_COLORS.get(n, "#7a7a7a"), lw=2, label=n) for n in line_layers]
        handles += [Line2D([0], [0], marker=_OVERLAY_STYLES[i % len(_OVERLAY_STYLES)]["marker"], color="w",
                           markerfacecolor=_OVERLAY_STYLES[i % len(_OVERLAY_STYLES)]["color"],
                           markeredgecolor="white", markersize=9, label=n) for i, n in enumerate(ov)]
        if handles:
            ax.legend(handles=handles, fontsize=7, loc="best", framealpha=0.9)
        ax.set_title(f"{lbl}  (n={len(df)})", fontsize=11)
        if extent:
            ax.set_xlim(extent[0], extent[2]); ax.set_ylim(extent[1], extent[3])
        ax.set_aspect("equal"); ax.tick_params(labelsize=7)
    fig.suptitle(title, fontsize=13)

    return _savefig(fig, slug, dpi=dpi, out_dir=out_dir)


def _shape_map(values) -> dict:
    uniq = sorted({str(v) for v in values})
    return {v: _HUB_SHAPES[i % len(_HUB_SHAPES)] for i, v in enumerate(uniq)}


def _size_scale(values, lo: float = 80, hi: float = 420):
    import numpy as np

    a = np.asarray([float(v) for v in values], dtype=float)
    if a.size == 0:
        return a
    rng = a.max() - a.min()
    if rng <= 0:
        return np.full_like(a, (lo + hi) / 2)
    return lo + (hi - lo) * (a - a.min()) / rng


def plot_hubs(facilities, hubs_centroid, hubs_snapped, title: str = "", slug: str = "hubs",
              boundary_path: str | Path | None = None, size_col: str = "total_hub_capacity",
              shape_col: str = "delivery_method", hub_id_col: str = "hub_id",
              lines: dict | None = None, point_overlays: dict | None = None,
              dpi: int = 120, out_dir: str | Path | None = None) -> Path | None:
    """Two stacked hub-diagnostic maps on the sea/land + network basemap.

    Top    -- aggregated facilities (marker SHAPE = delivery_method, COLOR = hub membership)
              + hub CENTROIDS (marker SIZE proportional to total_capacity), with thin
              facility->centroid lines showing which facilities formed each hub.
    Bottom -- the SNAPPED hubs (same shape/size) with dashed centroid->snap displacement
              lines annotated by snap_dist_m.

    `lines` draws the transport network; `point_overlays` draws ports/airports. Panels
    stack vertically and the figure is sized to the data aspect (tall, no whitespace).
    """
    from matplotlib.lines import Line2D

    target_crs = getattr(hubs_snapped, "crs", None) or getattr(hubs_centroid, "crs", None)

    def _to(g):
        try:
            return g.to_crs(target_crs) if target_crs is not None and getattr(g, "crs", None) is not None else g
        except Exception:
            return g

    fac = _to(facilities.copy()); cen = _to(hubs_centroid.copy()); snp = _to(hubs_snapped.copy())
    land, sea, coast = _load_basemap(target_crs)
    line_layers = _reproject_layers(lines, target_crs)
    pt_overlays = _reproject_layers(point_overlays, target_crs)

    shp = _shape_map(list(fac.get(shape_col, [])) + list(cen.get(shape_col, [])))
    palette = plt.get_cmap("tab10")
    hub_color = {h: palette(i % 10) for i, h in enumerate(list(cen[hub_id_col]))}
    cen_by_id = {r[hub_id_col]: r.geometry for _, r in cen.iterrows()}

    # facility -> hub: nearest centroid sharing the same delivery_method
    fac["_hub"] = None
    for i, frow in fac.iterrows():
        if frow.geometry is None:
            continue
        cand = cen[cen[shape_col] == frow.get(shape_col)]
        if len(cand) == 0:
            continue
        fac.at[i, "_hub"] = cand.loc[cand.geometry.distance(frow.geometry).idxmin(), hub_id_col]

    cen["_size"] = _size_scale(cen[size_col]); snp["_size"] = _size_scale(snp[size_col])

    # Extent from points + the water layer, so the offshore waterway (in the sea) is visible
    # while the wide road/air lines (which would flatten the panels) stay out of the extent.
    water = [line_layers["water"]] if "water" in line_layers else []
    extent = _bounds_union([fac, cen, snp] + list(pt_overlays.values()) + water)
    fig, axes, extent = _stacked_fig(extent, 2)
    axT, axB = axes[0], axes[1]

    def _basemap(ax):
        _draw_basemap(ax, land, sea, coast, line_layers)
        for i, (name, g) in enumerate(pt_overlays.items()):
            st = _OVERLAY_STYLES[i % len(_OVERLAY_STYLES)]
            g.plot(ax=ax, color=st["color"], marker=st["marker"], markersize=st["markersize"],
                   edgecolor="white", linewidth=0.6, zorder=6)

    # TOP panel: facilities + centroids + membership lines
    _basemap(axT)
    for _, frow in fac.iterrows():
        c = cen_by_id.get(frow["_hub"])
        if c is not None and frow.geometry is not None:
            axT.plot([frow.geometry.x, c.x], [frow.geometry.y, c.y],
                     color=hub_color.get(frow["_hub"], "#999"), linewidth=0.6, alpha=0.5, zorder=3)
    for dm, grp in fac.groupby(shape_col):
        axT.scatter(grp.geometry.x, grp.geometry.y, marker=shp.get(str(dm), "o"),
                    c=[hub_color.get(h, "#999") for h in grp["_hub"]], s=30,
                    edgecolor="white", linewidth=0.3, zorder=4)
    for dm, grp in cen.groupby(shape_col):
        axT.scatter(grp.geometry.x, grp.geometry.y, marker=shp.get(str(dm), "o"),
                    c=[hub_color.get(h, "#999") for h in grp[hub_id_col]], s=grp["_size"],
                    edgecolor="black", linewidth=1.1, zorder=5)
    for _, r in cen.iterrows():
        axT.annotate(f"{r[hub_id_col]} (n={int(r['num_facilities'])})", (r.geometry.x, r.geometry.y),
                     xytext=(4, 4), textcoords="offset points", fontsize=6, zorder=7)
    axT.set_title("aggregated facilities + hub CENTROIDS", fontsize=11)

    # BOTTOM panel: snapped hubs + centroid->snap displacement
    _basemap(axB)
    axB.scatter(cen.geometry.x, cen.geometry.y, marker="x", c="#666", s=45, zorder=4)
    for _, srow in snp.iterrows():
        c = cen_by_id.get(srow[hub_id_col])
        if c is not None and srow.geometry is not None:
            axB.plot([c.x, srow.geometry.x], [c.y, srow.geometry.y],
                     color="#c1272d", linewidth=1.0, linestyle="--", zorder=4)
            d = srow.get("snap_dist_m")
            if d is not None:
                axB.annotate(f"{d:.0f} m", ((c.x + srow.geometry.x) / 2, (c.y + srow.geometry.y) / 2),
                             fontsize=6, color="#c1272d", zorder=7)
    for dm, grp in snp.groupby(shape_col):
        axB.scatter(grp.geometry.x, grp.geometry.y, marker=shp.get(str(dm), "o"),
                    c=[hub_color.get(h, "#999") for h in grp[hub_id_col]], s=grp["_size"],
                    edgecolor="black", linewidth=1.1, zorder=5)
    axB.set_title("hubs placed on the road (x = centroid; dashed = centroid→on-road)", fontsize=11)

    shape_handles = [Line2D([0], [0], marker=m, color="w", markerfacecolor="#555",
                            markeredgecolor="black", markersize=8, label=dm) for dm, m in shp.items()]
    axT.legend(handles=shape_handles, title="delivery_method", fontsize=7, title_fontsize=7, loc="best")
    net_handles = [Line2D([0], [0], color=_LINE_COLORS.get(n, "#7a7a7a"), linewidth=2, label=n)
                   for n in line_layers]
    net_handles += [Line2D([0], [0], marker=_OVERLAY_STYLES[i % len(_OVERLAY_STYLES)]["marker"],
                           color="w", markerfacecolor=_OVERLAY_STYLES[i % len(_OVERLAY_STYLES)]["color"],
                           markeredgecolor="white", markersize=9, label=n)
                    for i, n in enumerate(pt_overlays)]
    if net_handles:
        axB.legend(handles=net_handles, title="network / connectors", fontsize=7, title_fontsize=7, loc="best")
    for ax in (axT, axB):
        if extent:
            ax.set_xlim(extent[0], extent[2]); ax.set_ylim(extent[1], extent[3])
        ax.set_aspect("equal"); ax.tick_params(labelsize=7)
    fig.suptitle(f"{title}   (marker size ∝ {size_col})", fontsize=13)

    return _savefig(fig, slug, dpi=dpi, out_dir=out_dir)


def plot_network(nodes, edges, title: str = "", slug: str = "03_build",
                 type_col: str = "type", component_col: str = "component",
                 hub_col: str = "is_hub", hub_id_col: str = "hub_id",
                 shape_col: str = "delivery_method", size_col: str = "total_hub_capacity",
                 point_overlays: dict | None = None, lines: dict | None = None,
                 dpi: int = 120, out_dir: str | Path | None = None) -> Path | None:
    """One map of the built network on the sea/land basemap.

    EDGES colored by type (Road / Waterway / Air / Transfer); all NODES shown; ports/airports
    as reference markers; HUBS drawn as marker shapes by delivery_method, colored by the same
    palette as the other plots and sized by total_hub_capacity.
    """
    from matplotlib.lines import Line2D

    target_crs = getattr(nodes, "crs", None) or getattr(edges, "crs", None)

    def _to(g):
        try:
            return g.to_crs(target_crs) if target_crs is not None and getattr(g, "crs", None) is not None else g
        except Exception:
            return g

    nd, ed = _to(nodes.copy()), _to(edges.copy())
    land, sea, coast = _load_basemap(target_crs)
    pt_overlays = _reproject_layers(point_overlays, target_crs)

    extent = _bounds_union([nd, ed] + list(pt_overlays.values()))
    fig, axes, extent = _stacked_fig(extent, 1)
    ax = axes[0]

    _draw_basemap(ax, land, sea, coast, {})
    types_present = [t for t in _EDGE_TYPE_ORDER if t in set(ed.get(type_col, []))]
    types_present += [t for t in ed.get(type_col, pd.Series(dtype=object)).dropna().unique() if t not in types_present]
    for t in types_present:
        grp = ed[ed[type_col] == t]
        col = _EDGE_TYPE_COLORS.get(t, "#333")
        grp.plot(ax=ax, color=col, linewidth=1.6 if t == "Transfer" else 2.4,
                 linestyle="--" if t == "Transfer" else "-", zorder=3)
    nd.plot(ax=ax, color="#444", markersize=14, zorder=4)   # all nodes
    for i, (name, g) in enumerate(pt_overlays.items()):
        st = _OVERLAY_STYLES[i % len(_OVERLAY_STYLES)]
        g.plot(ax=ax, color=st["color"], marker=st["marker"], markersize=st["markersize"],
               edgecolor="white", linewidth=0.6, zorder=7)

    # HUBS: shapes + colors by delivery_method (same palette idea as the other plots), sized by capacity
    hubs = nd[nd[hub_col].fillna(False).astype(bool)].copy() if hub_col in nd else nd.iloc[:0].copy()
    dm_handles = []
    if len(hubs) and shape_col in hubs.columns and hubs[shape_col].notna().any():
        dms = sorted(hubs[shape_col].dropna().astype(str).unique())
        shp = _shape_map(dms)
        palette = plt.get_cmap("tab10")
        dm_color = {dm: palette(i % 10) for i, dm in enumerate(dms)}
        cap = pd.to_numeric(hubs.get(size_col), errors="coerce") if size_col in hubs.columns else None
        hubs["_s"] = _size_scale(cap.fillna(cap.median())) if cap is not None and cap.notna().any() else 240.0
        for dm, grp in hubs.groupby(shape_col):
            ax.scatter(grp.geometry.x, grp.geometry.y, marker=shp.get(str(dm), "o"),
                       color=dm_color.get(str(dm), "#555"), s=grp["_s"],
                       edgecolor="black", linewidth=1.7, zorder=6)
        if hub_id_col in hubs.columns:
            for _, r in hubs.iterrows():
                if r.geometry is not None and r.get(hub_id_col) is not None:
                    ax.annotate(str(r[hub_id_col]), (r.geometry.x, r.geometry.y), xytext=(5, 5),
                                textcoords="offset points", fontsize=6, zorder=8)
        dm_handles = [Line2D([0], [0], marker=shp[dm], color="w", markerfacecolor=dm_color[dm],
                             markeredgecolor="black", markersize=11, label=dm) for dm in dms]

    edge_handles = [Line2D([0], [0], color=_EDGE_TYPE_COLORS.get(t, "#333"),
                           lw=2.4, linestyle="--" if t == "Transfer" else "-", label=t)
                    for t in types_present]
    edge_handles += [Line2D([0], [0], marker="o", color="w", markerfacecolor="#444",
                            markeredgecolor="white", markersize=7, label="node")]
    edge_handles += [Line2D([0], [0], marker=_OVERLAY_STYLES[i % len(_OVERLAY_STYLES)]["marker"], color="w",
                            markerfacecolor=_OVERLAY_STYLES[i % len(_OVERLAY_STYLES)]["color"],
                            markeredgecolor="white", markersize=9, label=n) for i, n in enumerate(pt_overlays)]
    leg1 = ax.legend(handles=edge_handles, title="edges / points", fontsize=8, title_fontsize=8, loc="upper left")
    ax.add_artist(leg1)
    if dm_handles:
        ax.legend(handles=dm_handles, title="hub delivery_method", fontsize=8, title_fontsize=8, loc="lower left")
    ax.set_title(f"edges by type + hubs  ({len(ed)} edges, {len(nd)} nodes)", fontsize=11)

    if extent:
        ax.set_xlim(extent[0], extent[2]); ax.set_ylim(extent[1], extent[3])
    ax.set_aspect("equal"); ax.tick_params(labelsize=7)
    fig.suptitle(f"{title}   (hub marker size ∝ {size_col})", fontsize=13)

    return _savefig(fig, slug, dpi=dpi, out_dir=out_dir)
