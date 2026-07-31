#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_weighted_network.py

Publication figure: the multimodal network with each edge colored by its
combined traversal intensity — environmental friction x operational cost
per mile (edge_month_weights.avg_friction x edge_costs.cost_per_gallon /
edge length). Twelve monthly panels; only edges passable in the rendered
month are drawn.

Per-mile, not per-edge: the total routing weight scales with edge length,
so coloring by it makes long segments bright and dense short segments
dark — encoding the noding segmentation instead of conditions. The
per-mile intensity is length-independent: mode rate sets the band (road/
barge cheap, ice road and air expensive) and friction modulates within it.

Style prototypes for this figure live in viz_weighted_network_prototypes.py;
this is the camera-ready version: serif fonts, light background, shared
log color scale across all months, 300 dpi PNG plus PDF (line work
rasterized inside the PDF so it stays a reasonable size).

No CLI args. Writes outputs/figures/weighted_network_monthly.{png,pdf}
(landscape, 4x3) and weighted_network_monthly_portrait.{png,pdf} (6x2).

Usage:
    python plot_weighted_network.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import duckdb
import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.lines import Line2D

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "fuel_network.duckdb"
EDGES_SHP = ROOT / "final_network" / "network_joined_edges" / "network_joined_edges.shp"
NODES_SHP = ROOT / "final_network" / "network_joined_nodes" / "network_joined_nodes.shp"
STATES_SHP = ROOT / "inputs" / "region_and_census_data" / "tiger" / "cb_2023_us_state_500k.shp"
OUT_DIR = ROOT / "outputs" / "figures"

SIMPLIFY_TOL_M = 300  # rendering only
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Formal / print styling, matching plot_combined_friction.py.
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Times New Roman", "Nimbus Roman"],
    "mathtext.fontset": "dejavuserif",
    "figure.dpi": 150,
    "savefig.dpi": 300,
})

# plasma trimmed to each background: on white the brightest yellow washes
# out, on dark the deepest purple vanishes. Low = cheap/easy, high = costly.
STYLES = {
    "light": {
        "suffix": "",
        "cmap": LinearSegmentedColormap.from_list(
            "plasma_print", plt.get_cmap("plasma")(np.linspace(0.0, 0.9, 256))),
        "bg": "#ffffff", "fg": "#1a1a1a",
        "land_face": "#e9e9e9", "land_edge": "#c8c8c8", "hub": "#1a1a1a",
    },
    "dark": {
        "suffix": "_dark",
        "cmap": LinearSegmentedColormap.from_list(
            "plasma_screen", plt.get_cmap("plasma")(np.linspace(0.2, 1.0, 256))),
        "bg": "#0d1117", "fg": "#d0d7de",
        "land_face": "#1c232e", "land_edge": "#303c4a", "hub": "white",
    },
}

# (filename suffix, grid cols, grid rows, figure width in inches)
LAYOUTS = (
    ("", 4, 3, 22.0),
    ("_portrait", 2, 6, 14.0),
)


def load_weighted_edges() -> gpd.GeoDataFrame:
    """Edges shapefile with per-month weight/passable columns from DuckDB.

    weight = avg_friction x cost_per_gallon per mile of edge; an edge-month
    is passable only if both the friction gate and the cost table agree.
    edge_id is the 0-based row order of the edges shapefile.
    """
    edges = gpd.read_file(EDGES_SHP)
    edges["geometry"] = edges.geometry.simplify(SIMPLIFY_TOL_M)

    con = duckdb.connect(str(DB_PATH), read_only=True)
    w = con.sql(
        "SELECT w.edge_id, w.month,"
        "       w.avg_friction * c.cost_per_gallon"
        "         / (e.length_m / 1609.344) AS weight,"
        "       (w.passable AND c.passable) AS passable "
        "FROM edge_month_weights w "
        "JOIN edge_costs c USING (edge_id, month) "
        "JOIN network_edges e USING (edge_id)"
    ).df()
    con.close()

    idx = np.arange(len(edges))
    for month, grp in w.groupby("month"):
        g = grp.set_index("edge_id").reindex(idx)
        edges[f"pass_{month:02d}"] = g["passable"].fillna(False).to_numpy(bool)
        edges[f"wt_{month:02d}"] = g["weight"].to_numpy()
    return edges


def shared_norm(edges: gpd.GeoDataFrame) -> LogNorm:
    """One log color scale across every rendered month.

    The per-mile intensity spans ~3 decades (road ~0.001 to transfer ~0.5
    $/gal-mi) with modes in distinct bands, so the scale runs nearly
    edge-to-edge; only extreme outliers are clipped.
    """
    vals = np.concatenate([
        edges.loc[edges[f"pass_{m:02d}"], f"wt_{m:02d}"].to_numpy()
        for m in range(1, 13)
    ])
    vals = vals[np.isfinite(vals) & (vals > 0)]
    return LogNorm(vmin=np.quantile(vals, 0.005),
                   vmax=np.quantile(vals, 0.995))


def mode_medians(edges: gpd.GeoDataFrame) -> dict[str, float]:
    """Median passable per-mile intensity per edge type, for annotating the
    colorbar with where each delivery mode sits on the shared scale."""
    frames = []
    for m in range(1, 13):
        ok = edges[f"pass_{m:02d}"].to_numpy()
        frames.append(pd.DataFrame({
            "type": edges.loc[ok, "type"].to_numpy(),
            "v": edges.loc[ok, f"wt_{m:02d}"].to_numpy(),
        }))
    df = pd.concat(frames)
    df = df[np.isfinite(df["v"]) & (df["v"] > 0)]
    return df.groupby("type")["v"].median().to_dict()


# Colorbar annotation labels per edge type. Bridge/Join are synthetic
# connectors priced as road; labeling them would only clutter the bar.
MODE_LABELS = {
    "Road": "road",
    "Waterway": "barge",
    "IceRoad": "ice road",
    "Air": "air",
    "Transfer": "transfer",
}


def annotate_mode_bands(cbar, norm: LogNorm, medians: dict[str, float],
                        fg: str) -> None:
    """Mark each mode's median intensity beside the colorbar.

    Positions are clamped into the bar and nudged apart when modes nearly
    coincide (air at 0.025 vs in-season ice road at ~0.03 on a log scale).
    """
    span = np.log10(norm.vmax) - np.log10(norm.vmin)
    marks = sorted(
        (np.clip((np.log10(v) - np.log10(norm.vmin)) / span, 0.02, 0.97),
         MODE_LABELS[t])
        for t, v in medians.items() if t in MODE_LABELS
    )
    # De-collide: push up from the bottom, then cap at the bar top and push
    # back down so out-of-range modes (clamped to 0.97) stay on the bar.
    min_gap = 0.05
    for i in range(1, len(marks)):
        if marks[i][0] - marks[i - 1][0] < min_gap:
            marks[i] = (marks[i - 1][0] + min_gap, marks[i][1])
    marks[-1] = (min(marks[-1][0], 0.97), marks[-1][1])
    for i in range(len(marks) - 2, -1, -1):
        if marks[i + 1][0] - marks[i][0] < min_gap:
            marks[i] = (marks[i + 1][0] - min_gap, marks[i][1])
    for y, label in marks:
        cbar.ax.annotate(
            f"{label} —", xy=(0, y), xytext=(-0.4, y),
            xycoords="axes fraction", textcoords="axes fraction",
            ha="right", va="center", fontsize=8.5, color=fg,
            annotation_clip=False,
        )


def plot_grid(edges: gpd.GeoDataFrame, hubs: gpd.GeoDataFrame,
              land: gpd.GeoDataFrame, norm: LogNorm,
              ncols: int, nrows: int, fig_w: float, stem: Path,
              style: dict, medians: dict[str, float]) -> None:
    """Render one 12-month grid in the given style and save PNG + PDF."""
    pad = 50_000
    xmin, ymin, xmax, ymax = edges.total_bounds
    w, h = xmax - xmin + 2 * pad, ymax - ymin + 2 * pad
    fig_h = fig_w / ncols / (w / h) * nrows
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(fig_w, fig_h), facecolor=style["bg"],
        gridspec_kw={"wspace": 0.01, "hspace": 0.01,
                     "left": 0.003, "right": 0.997,
                     "top": 0.985, "bottom": 0.03},
    )
    for month, ax in enumerate(axes.flat, start=1):
        ax.set_facecolor(style["bg"])
        land.plot(ax=ax, facecolor=style["land_face"],
                  edgecolor=style["land_edge"], linewidth=0.3, zorder=0)
        sub = edges[edges[f"pass_{month:02d}"].to_numpy()]
        is_air = (sub["type"] == "Air").to_numpy()
        # Air legs dashed: on the log scale they sit in the same band as
        # in-season ice roads, so line style is what separates them.
        sub[~is_air].plot(ax=ax, column=f"wt_{month:02d}",
                          cmap=style["cmap"], norm=norm,
                          linewidth=0.55, rasterized=True)
        sub[is_air].plot(ax=ax, column=f"wt_{month:02d}",
                         cmap=style["cmap"], norm=norm, linewidth=0.6,
                         linestyle=(0, (4, 3)), rasterized=True)
        ax.scatter(hubs.geometry.x, hubs.geometry.y, s=4, c=style["hub"],
                   alpha=0.8, linewidths=0, zorder=5)
        ax.set_xlim(xmin - pad, xmax + pad)
        ax.set_ylim(ymin - pad, ymax + pad)
        ax.set_aspect("equal")
        ax.set_axis_off()
        ax.text(0.02, 0.97, MONTH_NAMES[month - 1], transform=ax.transAxes,
                va="top", ha="left", fontsize=12, fontweight="bold",
                color=style["fg"])

    cbar = fig.colorbar(ScalarMappable(norm=norm, cmap=style["cmap"]),
                        ax=axes, fraction=0.015, pad=0.005)
    cbar.set_label("combined traversal intensity — friction × cost rate "
                   "($/gal·mi, log)",
                   fontsize=10, color=style["fg"])
    cbar.ax.tick_params(labelsize=8, color=style["fg"],
                        labelcolor=style["fg"])
    cbar.outline.set_edgecolor(style["fg"])
    annotate_mode_bands(cbar, norm, medians, style["fg"])

    fig.legend(
        handles=[
            Line2D([0], [0], color=style["fg"], lw=1.2,
                   label="surface / marine edge"),
            Line2D([0], [0], color=style["fg"], lw=1.2,
                   linestyle=(0, (4, 3)), label="air-cargo leg (dashed)"),
            Line2D([0], [0], marker="o", color="none",
                   markerfacecolor=style["hub"], markersize=4,
                   label="fuel hub"),
        ],
        loc="lower center", ncol=3, frameon=False, fontsize=9,
        labelcolor=style["fg"],
    )

    for ext in ("png", "pdf"):
        out = stem.with_suffix(f".{ext}")
        fig.savefig(out, bbox_inches="tight", facecolor=style["bg"])
        logger.info("wrote %s", out)
    plt.close(fig)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    edges = load_weighted_edges()
    nodes = gpd.read_file(NODES_SHP)
    hubs = nodes[nodes["is_hub"] == 1]
    states = gpd.read_file(STATES_SHP)
    land = states[states["STUSPS"] == "AK"].to_crs(edges.crs)
    land["geometry"] = land.geometry.simplify(1000)
    logger.info("%d edges, %d hubs", len(edges), len(hubs))

    norm = shared_norm(edges)
    medians = mode_medians(edges)
    logger.info("mode medians ($/gal-mi): %s",
                {k: round(v, 4) for k, v in medians.items()})
    for style in STYLES.values():
        for suffix, ncols, nrows, fig_w in LAYOUTS:
            stem = OUT_DIR / (
                f"weighted_network_monthly{suffix}{style['suffix']}")
            plot_grid(edges, hubs, land, norm, ncols, nrows, fig_w, stem,
                      style, medians)
    return 0


if __name__ == "__main__":
    sys.exit(main())
