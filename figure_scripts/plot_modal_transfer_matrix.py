#!/usr/bin/env python3
"""Publication figure: the 4x4 modal interchange matrix.

Renders Plane / Road / IceRoad / Barge on both axes and marks every synthetic
connector and priced transfer that actually exists in the network-of-record.
A traced "route" line threads Plane -> Road -> IceRoad -> Barge to show, at a
glance, that Road is the hub nearly every mode reaches the network through:
the two non-Road interfaces are Barge<->IceRoad (never traversable because ice
roads and barges never share a month) and the two Barge<->Plane connectors.

Counts are the EXPECTED tripwire values (CLAUDE.md / stage-02 load); fees are
the INTERMODAL_TRANSFER_FEES totals in friction_costs.py. Both are restated as
literals here so the figure is a standalone artifact -- update alongside a
re-export.

Outputs (outputs/final_network_plots/):
    modal_transfer_matrix.pdf   vector, for the paper
    modal_transfer_matrix.svg   vector, editable
    modal_transfer_matrix.png   300 dpi raster, for slides/preview
"""
from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

# --------------------------------------------------------------------------- #
# Data (network-of-record, refine-synthetic-connectors)                       #
# --------------------------------------------------------------------------- #
# Axis order: index 0..3. Road sits at index 1 so its row/column is the spine.
MODES = ["Plane", "Road", "IceRoad", "Barge"]
LABELS = ["PLANE", "ROAD", "ICE ROAD", "BARGE"]
IDX = {m: i for i, m in enumerate(MODES)}

# Per-mode accent colors (used for the axis label bars).
MODE_COLOR = {
    "Plane":   "#6a1b9a",  # purple
    "Road":    "#37474f",  # dark slate — the hub
    "IceRoad": "#0288d1",  # ice blue
    "Barge":   "#00695c",  # marine teal
}

# One record per connection that exists. kind drives color/legend:
#   weld      within-mode synthetic connector (no fee)
#   transfer  cross-mode priced handoff, exercised by routing
#   latent    priced handoff that exists but is never traversed
CONNECTIONS = [
    ("Road",    "Road",    1498, None,   "weld",     "RoadConnector"),
    ("IceRoad", "IceRoad",   34, None,   "weld",     "IceRoadConnector"),
    ("Barge",   "Road",     286, 0.24,   "transfer", "BargeRoadTransfer"),
    ("IceRoad", "Road",      12, 0.022,  "transfer", "IceRoadRoadTransfer"),
    ("Plane",   "Road",       2, 0.025,  "transfer", "AirRoadTransfer"),
    ("Plane",   "Barge",      2, 0.24,   "transfer", "BargeAirTransfer"),
    ("IceRoad", "Barge",     21, 0.011,  "latent",   "BargeIceRoadTransfer"),
]

KIND_COLOR = {
    "weld":     "#2e7d32",  # green
    "transfer": "#ef6c00",  # orange
    "latent":   "#9e9e9e",  # gray
}
GRID_LINE = "#d7dbdf"

# --------------------------------------------------------------------------- #
# Delivery routes                                                             #
# --------------------------------------------------------------------------- #
# Each route is a continuous multimodal journey: fuel is line-hauled on a mode
# (a diagonal "station"), then handed off at a priced transfer, then line-hauled
# on the next mode. Both routes pass through the Road station, so Road reads as
# the hub every mode spokes into. `legs` are (from_mode, to_mode); `bow` bends
# the arrow off the anti-diagonal so it never overlaps an intervening station or
# the never-traversed Barge<->IceRoad cell; `fee_xy` places the transfer diamond.
ROUTES = [
    {
        "name": "Barge–Road–Ice Road  (marine resupply to winter village)",
        "color": "#1a4f8b",
        "legs": [
            {"from": "Barge", "to": "Road",    "bow":  0.32},
            {"from": "Road",  "to": "IceRoad", "bow": -0.30},
        ],
    },
    {
        "name": "Plane–Road  (air delivery to ground)",
        "color": "#8e24aa",
        "legs": [
            {"from": "Plane", "to": "Road", "bow": -0.28},
        ],
    },
]

# Fee lookup keyed by unordered mode pair (mirrors CONNECTIONS).
FEE = {frozenset((a, b)): fee for a, b, _c, fee, _k, _n in CONNECTIONS}

# --------------------------------------------------------------------------- #
# Figure                                                                      #
# --------------------------------------------------------------------------- #
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
})

N = len(MODES)


def _marker_size(count: int) -> float:
    """Marker area scaled by sqrt(count) so 2 and 1498 both stay legible."""
    return 90.0 + 70.0 * math.sqrt(count)


def build() -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8.2, 8.2))

    # Cell coordinates: column = x, row = y. Row 0 at the TOP.
    def xy(row_mode: str, col_mode: str):
        return IDX[col_mode], (N - 1) - IDX[row_mode]

    # --- grid backdrop ---------------------------------------------------- #
    for k in range(N + 1):
        ax.plot([-0.5, N - 0.5], [k - 0.5, k - 0.5], color=GRID_LINE, lw=1.0, zorder=0)
        ax.plot([k - 0.5, k - 0.5], [-0.5, N - 0.5], color=GRID_LINE, lw=1.0, zorder=0)

    # Highlight the Road diagonal cell — the hub every route converges on.
    hub_x, hub_y = xy("Road", "Road")
    ax.add_patch(plt.Rectangle((hub_x - 0.5, hub_y - 0.5), 1, 1,
                               facecolor="#fbe9e7", edgecolor="none", zorder=0.3))

    # --- mode "stations" on the diagonal (route endpoints / line-haul) ----- #
    # Every diagonal cell is a mode travelling on itself. Draw a soft station
    # node so all four route endpoints are visible; Road/IceRoad also carry
    # their green weld-count markers (drawn later, on top).
    for m in MODES:
        sx, sy = xy(m, m)
        ax.scatter([sx], [sy], s=2000, facecolor="white",
                   edgecolor=MODE_COLOR[m], linewidth=2.2, zorder=2)

    # --- delivery routes: continuous multimodal journeys ------------------- #
    for route in ROUTES:
        for leg in route["legs"]:
            (x0, y0) = xy(leg["from"], leg["from"])   # from-mode station
            (x1, y1) = xy(leg["to"], leg["to"])       # to-mode station
            bow = leg["bow"]
            ax.add_patch(FancyArrowPatch(
                (x0, y0), (x1, y1), connectionstyle=f"arc3,rad={bow}",
                arrowstyle="-|>", mutation_scale=22, lw=3.2,
                color=route["color"], zorder=6,
                shrinkA=24, shrinkB=24, capstyle="round"))
            # Transfer point sits on the arc's midpoint (t=0.5 of the quadratic
            # Bezier matplotlib uses for arc3): mid + 0.5*bow*perp.
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            perp = (y1 - y0, -(x1 - x0))
            fx, fy = mx + 0.5 * bow * perp[0], my + 0.5 * bow * perp[1]
            fee = FEE[frozenset((leg["from"], leg["to"]))]
            ax.scatter([fx], [fy], s=210, marker="D", facecolor="white",
                       edgecolor=route["color"], linewidth=2.0, zorder=7)
            ax.annotate(f"${fee:g}/gal", (fx, fy), xytext=(0, 13),
                        textcoords="offset points", ha="center", va="bottom",
                        fontsize=8, fontweight="bold", color=route["color"], zorder=8,
                        bbox=dict(boxstyle="round,pad=0.18", fc="white",
                                  ec=route["color"], lw=1.0))

    # Faint dashed thread for the never-traversed non-Road interface.
    bx, by = xy("Barge", "IceRoad")
    ix, iy = xy("IceRoad", "Barge")
    ax.plot([bx, ix], [by, iy], color=KIND_COLOR["latent"], lw=1.6,
            ls=(0, (4, 3)), zorder=1.5)

    # --- connection markers (symmetric) ----------------------------------- #
    for a, b, count, fee, kind, _name in CONNECTIONS:
        color = KIND_COLOR[kind]
        cells = {(a, b), (b, a)}  # mirror across the diagonal
        for row_mode, col_mode in cells:
            x, y = xy(row_mode, col_mode)
            ax.scatter([x], [y], s=_marker_size(count), color=color,
                       edgecolor="white", linewidth=1.4, zorder=4)
            label = f"{count:,}"
            if fee is not None:
                label += f"\n${fee:g}/gal"
            ax.text(x, y, label, ha="center", va="center", fontsize=7.5,
                    fontweight="bold", color="white", zorder=5, linespacing=1.1,
                    path_effects=[pe.withStroke(linewidth=2.2, foreground="#333")])

    # --- axis labels with per-mode color bars ----------------------------- #
    ax.set_xlim(-0.5, N - 0.5)
    ax.set_ylim(-0.5, N - 0.5)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    for i, (m, lab) in enumerate(zip(MODES, LABELS)):
        # top (columns)
        ax.text(i, N - 0.66, lab, ha="center", va="bottom",
                fontsize=11, fontweight="bold", color=MODE_COLOR[m])
        ax.plot([i - 0.32, i + 0.32], [N - 0.74, N - 0.74],
                color=MODE_COLOR[m], lw=3.0, solid_capstyle="round")
        # left (rows), top row = Plane
        y = (N - 1) - i
        ax.text(-0.62, y, lab, ha="right", va="center", rotation=90,
                fontsize=11, fontweight="bold", color=MODE_COLOR[m])
        ax.plot([-0.44, -0.44], [y - 0.32, y + 0.32],
                color=MODE_COLOR[m], lw=3.0, solid_capstyle="round")

    # --- legend ----------------------------------------------------------- #
    handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=KIND_COLOR["weld"],
               markeredgecolor="white", markersize=13,
               label="Within-mode connector (weld, no fee)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=KIND_COLOR["transfer"],
               markeredgecolor="white", markersize=13,
               label="Cross-mode transfer connectors (count)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=KIND_COLOR["latent"],
               markeredgecolor="white", markersize=13,
               label="Interface present but never traversed"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor="white",
               markeredgecolor="#555", markeredgewidth=1.6, markersize=11,
               label="Transfer point ($/gal handoff fee)"),
    ]
    for route in ROUTES:
        handles.append(Line2D([0], [0], color=route["color"], lw=3.2,
                              marker=">", markersize=8, markevery=[-1],
                              label=f"Route: {route['name']}"))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02),
              ncol=2, frameon=False, fontsize=8.5, handletextpad=0.6,
              columnspacing=1.8)

    ax.text(0.5, 1.085, "Alaska Multimodal Fuel Network — Modal Interchange Matrix",
            transform=ax.transAxes, ha="center", va="bottom",
            fontsize=14, fontweight="bold", color="#222")
    ax.text(0.5, 1.045,
            "Marker area scales with number of connectors; label gives count and per-gallon transfer fee",
            transform=ax.transAxes, ha="center", va="bottom",
            fontsize=9.5, color="#555")

    fig.subplots_adjust(left=0.10, right=0.97, top=0.86, bottom=0.12)
    return fig


def main() -> None:
    import repo_paths as rp
    out_dir = rp.NETWORK_PLOTS
    out_dir.mkdir(parents=True, exist_ok=True)
    fig = build()
    stem = out_dir / "modal_transfer_matrix"
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    for ext in ("pdf", "svg", "png"):
        print(f"wrote {stem.with_suffix('.' + ext)}")


if __name__ == "__main__":
    main()
