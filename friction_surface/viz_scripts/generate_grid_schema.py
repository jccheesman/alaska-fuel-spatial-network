"""generate_grid_schema.py

Render a cell-by-cell schematic of how friction-surface input rasters are
combined into the final mode-month outputs.

Each grid is 5x5 with a coastline geometry: bottom-left = ocean,
middle column = a river flowing in from the coast, rest = land. Every
cell carries a coloured border indicating its geometry class (land /
ocean / river) so the land vs water dichotomy is visible at a glance
regardless of the fill value. One land pixel is deliberately set to
NoData on the slope input to illustrate ND-on-land (DEM holes,
glaciers, impassable terrain) as a distinct case from ND-on-water-
in-overland-context.

Output: friction_surface/friction_outputs/friction_grid_schema.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import FancyArrowPatch, Rectangle


# Sentinel for NoData / impassable in display grids
ND = np.nan

# Friction colour scale (low cost = green, high cost = red)
FRICTION_CMAP = LinearSegmentedColormap.from_list(
    "friction",
    ["#1a9850", "#a6d96a", "#ffffbf", "#fdae61", "#d73027"],
)
FRICTION_NORM = Normalize(vmin=1.0, vmax=3.5)

# Fills
NODATA_COLOR = "#3b3b3b"          # NoData / impassable
NAVIGABLE_WATER_COLOR = "#1a9850" # barge navigable (matches friction-1.0 green)
MASK_ON_COLOR = "#1f4e79"
MASK_OFF_COLOR = "#e8edf2"
EDGE_DEFAULT = "#2c3e50"

# Domain-badge colours (LAND / SEA NETWORK ONLY tags under outputs)
LAND_BADGE_COLOR = "#5b8a3a"
OCEAN_BADGE_COLOR = "#0e3656"


# ---------------------------------------------------------------------------
# Coastline geometry (fixed across all grids — defines the toy world)
# ---------------------------------------------------------------------------
# 5x5 layout, rows top-to-bottom:
#   rows 0-2:   inland to coastal land
#   col   2:    a river running from the coast up into the land
#   rows 3-4:   ocean (bottom-left quadrant + bottom row)
#   row 0 col 4: a DEM hole on land (slope = ND -> impassable)
OCEAN = np.array([
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0],
    [1, 1, 1, 1, 1],
], dtype=bool)

RIVER = np.array([
    [0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0],   # river-mouth pixel where it joins the coast
    [0, 0, 0, 0, 0],
], dtype=bool)

WATER = OCEAN | RIVER
LAND = ~WATER


# ---------------------------------------------------------------------------
# Toy input grids — values keyed off the geometry above
# ---------------------------------------------------------------------------
# Slope friction (reclassed from degrees). One land pixel is ND to
# represent a DEM hole / glacier-crevasse — propagates to static_base.
SLOPE = np.array([
    [1.00, 1.00, 1.40, 1.75, ND  ],   # (0,4) = DEM hole
    [1.00, 1.00, 1.40, 1.40, 1.75],
    [1.00, 1.00, 1.40, 1.40, 1.40],
    [1.00, 1.00, 1.00, 1.40, 1.40],
    [1.00, 1.00, 1.00, 1.00, 1.40],
], dtype=float)

# LULC friction. Water (ocean + river) is NaN. Land cells carry a
# class-specific friction; the (0,4) DEM-hole cell still has a LULC
# value (bare_ground 1.16) — the impassability comes from slope, not
# LULC. This is the realistic case.
LULC = np.full((5, 5), np.nan, dtype=float)
LULC[~WATER] = 1.16          # baseline land = bare_ground
LULC[0, 0] = 1.46            # trees
LULC[0, 1] = 1.46
LULC[1, 0] = 1.46
LULC[1, 1] = 1.15            # shrub
LULC[2, 0] = 1.15
LULC[2, 1] = 1.15
LULC[1, 3] = 1.05            # built area near coast
LULC[0, 4] = 1.16            # bare (but slope is ND here)

# Permafrost zonal modifier — full grid, year-round.
PERMAFROST_MOD = np.array([
    [1.50, 1.50, 1.50, 1.50, 1.50],
    [1.50, 1.50, 1.50, 1.30, 1.30],
    [1.30, 1.30, 1.30, 1.30, 1.30],
    [1.30, 1.15, 1.15, 1.15, 1.15],
    [1.15, 1.15, 1.15, 1.00, 1.00],
], dtype=float)


# Per-month ice rasters (a winter snapshot)
SEA_ICE_WINTER = (OCEAN.astype(int))           # all ocean iced in winter
RIVER_ICE_WINTER = (RIVER.astype(int))         # all river iced in winter


WATER_FRICTION_BARGE = 1.0    # matches friction_config — reference mode-pixel


# ---------------------------------------------------------------------------
# Derived grids
# ---------------------------------------------------------------------------
def static_base(slope: np.ndarray, lulc: np.ndarray) -> np.ndarray:
    base = slope * lulc
    base[WATER] = ND
    base[np.isnan(slope)] = ND   # propagate DEM holes
    return base


def land_base(static: np.ndarray, perma: np.ndarray) -> np.ndarray:
    out = static * perma
    out[np.isnan(static)] = ND
    return out


def road_base(slope: np.ndarray, perma: np.ndarray) -> np.ndarray:
    """Static road_base.tif: max(ROAD_FRICTION, slope) × permafrost.

    No LULC, no water mask, NoData-free — fmax heals the DEM hole to the
    flat-road baseline, mirroring compute_road_base in friction_surface.py.
    """
    ROAD_FRIC = 1.0
    return np.fmax(ROAD_FRIC, slope) * perma


def overland(static, perma):
    """Overland_MM.tif: static_base × permafrost — pure terrain.

    Identical every month: no road / ice-road burn-in (those are priced by
    the network layer via road_base.tif). This is exactly `land_base`; kept
    as a named function so the outputs row reads cleanly.
    """
    out = static * perma
    out[np.isnan(static)] = ND
    return out


def barge(sea_ice, river_ice):
    out = np.full(WATER.shape, ND, dtype=float)
    navigable = WATER & ~((sea_ice == 1) | (river_ice == 1))
    out[navigable] = WATER_FRICTION_BARGE
    return out


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
def draw_grid(ax, grid, x, y, cell=0.4, *, title=None, subtitle=None,
              mode="friction", show_values=True):
    """Draw a 5x5 grid at (x, y) (bottom-left in axis coords).

    mode:
      'friction'   — fill from FRICTION_CMAP; NaN -> NODATA_COLOR.
      'permafrost' — same as friction.
      'mask'       — 1 = MASK_ON_COLOR, 0 = MASK_OFF_COLOR.
      'navigable'  — NaN -> NoData; positive value -> green.
    """
    h, w = grid.shape
    for i in range(h):
        for j in range(w):
            v = grid[i, j]
            cx = x + j * cell
            cy = y + (h - 1 - i) * cell

            if mode == "mask":
                color = MASK_ON_COLOR if v == 1 else MASK_OFF_COLOR
                label = "1" if v == 1 else "0"
                text_color = "white" if v == 1 else "#888"
            elif mode == "navigable":
                if np.isnan(v):
                    color = NODATA_COLOR
                    label = "ND"
                    text_color = "white"
                else:
                    color = NAVIGABLE_WATER_COLOR
                    label = f"{v:.2f}"
                    text_color = "white"
            else:
                if np.isnan(v):
                    color = NODATA_COLOR
                    label = "ND"
                    text_color = "white"
                else:
                    color = FRICTION_CMAP(FRICTION_NORM(v))
                    label = f"{v:.2f}"
                    r, g, b, _ = color
                    luminance = 0.299 * r + 0.587 * g + 0.114 * b
                    text_color = "black" if luminance > 0.55 else "white"

            ax.add_patch(Rectangle(
                (cx, cy), cell, cell,
                facecolor=color, edgecolor=EDGE_DEFAULT, linewidth=0.6,
            ))
            if show_values:
                ax.text(
                    cx + cell / 2, cy + cell / 2, label,
                    ha="center", va="center", fontsize=6.2, color=text_color,
                )

    if title:
        ax.text(
            x + w * cell / 2, y + h * cell + 0.10, title,
            ha="center", va="bottom", fontsize=10, fontweight="bold",
            color="#1B2631",
        )
    if subtitle:
        ax.text(
            x + w * cell / 2, y - 0.08, subtitle,
            ha="center", va="top", fontsize=7.8, color="#566573",
            style="italic",
        )


def draw_op(ax, x, y, symbol, *, fontsize=22):
    ax.text(x, y, symbol, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color="#1B2631")


def draw_arrow(ax, x0, y0, x1, y1, *, label=None, label_offset=(0, 0.08)):
    ax.add_patch(FancyArrowPatch(
        (x0, y0), (x1, y1),
        arrowstyle="-|>", mutation_scale=14,
        linewidth=1.4, color="#566573",
    ))
    if label:
        mx, my = (x0 + x1) / 2 + label_offset[0], (y0 + y1) / 2 + label_offset[1]
        ax.text(mx, my, label, ha="center", va="center",
                fontsize=8.5, color="#1B2631",
                bbox=dict(boxstyle="round,pad=0.2", fc="white",
                          ec="#aab2bd", lw=0.6))


def draw_legend(ax, x, y):
    """Vertical legend (top of right column): friction ramp, ND, masks."""
    sw = 0.32
    row = 0.40

    ax.text(x, y + 0.45, "Legend",
            ha="left", va="bottom", fontsize=11, fontweight="bold",
            color="#1B2631")

    ax.text(x, y + 0.06, "Friction value", ha="left", va="bottom",
            fontsize=9, fontweight="bold", color="#1B2631")
    levels = [(1.0, "1.0  flat / road / open water"),
              (1.4, "1.4  rolling"),
              (1.75, "1.75 mountain"),
              (2.5, "2.5  mixed"),
              (3.5, "≥3.5 severe")]
    cur_y = y - row
    for val, lab in levels:
        ax.add_patch(Rectangle(
            (x, cur_y), sw, sw,
            facecolor=FRICTION_CMAP(FRICTION_NORM(val)),
            edgecolor=EDGE_DEFAULT, linewidth=0.6,
        ))
        ax.text(x + sw + 0.10, cur_y + sw / 2, lab,
                ha="left", va="center", fontsize=8.5, color="#1B2631")
        cur_y -= row

    cur_y -= 0.30
    ax.text(x, cur_y + sw + 0.10, "Other cell fills",
            ha="left", va="bottom", fontsize=9, fontweight="bold",
            color="#1B2631")
    other = [
        (NODATA_COLOR,            " NoData / impassable"),
        (MASK_ON_COLOR,           " Mask present (sea / river ice)"),
        (NAVIGABLE_WATER_COLOR,   " Navigable water "),
    ]
    for col, lab in other:
        ax.add_patch(Rectangle(
            (x, cur_y), sw, sw,
            facecolor=col, edgecolor=EDGE_DEFAULT, linewidth=0.6,
        ))
        ax.text(x + sw + 0.10, cur_y + sw / 2, lab,
                ha="left", va="center", fontsize=8.5, color="#1B2631")
        cur_y -= row


def draw_domain_badge(ax, x, y, text, color):
    """Small coloured badge sitting under an output grid to flag its
    domain — 'LAND NETWORK ONLY' or 'SEA NETWORK ONLY'."""
    ax.text(
        x, y, text,
        ha="center", va="center", fontsize=8, fontweight="bold",
        color="white",
        bbox=dict(boxstyle="round,pad=0.30", fc=color, ec=color, lw=0),
    )


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------
def render(output_path: Path) -> None:
    static = static_base(SLOPE, LULC)
    land = land_base(static, PERMAFROST_MOD)
    road = road_base(SLOPE, PERMAFROST_MOD)
    overland_mm = overland(static, PERMAFROST_MOD)  # == land; all 12 months
    barge_open = barge(np.zeros_like(SEA_ICE_WINTER), np.zeros_like(RIVER_ICE_WINTER))
    barge_winter = barge(SEA_ICE_WINTER, RIVER_ICE_WINTER)

    fig, ax = plt.subplots(figsize=(15, 18))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 18)
    ax.set_aspect("equal")
    ax.axis("off")

    # Title
    ax.text(
        7.5, 17.5,
        "Friction-Surface Construction: Per-Pixel Grid Composition",
        ha="center", va="center", fontsize=15, fontweight="bold",
        color="#1B2631",
    )
    ax.text(
        7.5, 17.05,
        "5×5 toy grids: overland is pure terrain; barge is ice-gated water; roads & ice roads are priced via road_base + network edges",
        ha="center", va="center", fontsize=9.5, color="#566573",
        style="italic",
    )

    # Op-symbol x positions are the exact midpoints of the gaps between
    # adjacent 5-cell (0.4 m) grids placed at x = 0.6 / 3.5 / 6.4.
    OP_TIMES_X = (0.6 + 2.0 + 3.5) / 2   # = 3.05
    OP_EQUAL_X = (3.5 + 2.0 + 6.4) / 2   # = 5.95

    # -------------------------------------------------------------- Row 1
    y1 = 13.7
    draw_grid(ax, SLOPE, 0.6, y1,
              title="Slope friction", subtitle="reclassified from slope (°)")
    draw_op(ax, OP_TIMES_X, y1 + 1.0, "×")
    draw_grid(ax, LULC, 3.5, y1,
              title="LULC friction", subtitle="lookup; water → NoData")
    draw_op(ax, OP_EQUAL_X, y1 + 1.0, "=")
    draw_grid(ax, static, 6.4, y1,
              title="static_base", subtitle="terrain only")

    # -------------------------------------------------------------- Row 2
    y2 = 11.0
    draw_grid(ax, static, 0.6, y2,
              title="static_base", subtitle="(from Step 1)")
    draw_op(ax, OP_TIMES_X, y2 + 1.0, "×")
    draw_grid(ax, PERMAFROST_MOD, 3.5, y2,
              title="permafrost_mod", subtitle="IPA zones")
    draw_op(ax, OP_EQUAL_X, y2 + 1.0, "=")
    draw_grid(ax, land, 6.4, y2,
              title="land base", subtitle="terrain × permafrost")
    draw_grid(ax, road, 9.3, y2,
              title="road_base.tif  (static)",
              subtitle="max(ROAD_FRICTION, slope) × permafrost\n"
                       "no LULC; NoData-free; sampled along network edges")

    # -------------------------------------------------------------- Row 3
    y3 = 8.3
    draw_grid(ax, SEA_ICE_WINTER, 0.6, y3, mode="mask",
              title="sea_ice (month M)", subtitle="thresholded > 0.15")
    draw_grid(ax, RIVER_ICE_WINTER, 3.5, y3, mode="mask",
              title="river_ice (month M)", subtitle="thresholded > 0.15")
    # Roads / ice roads are not a friction-raster input — say where they are
    # handled so the diagram doesn't read as "roads dropped".
    ax.text(
        8.35, y3 + 1.0,
        "Roads & ice roads are NOT burned into the overland\n"
        "raster. They are priced by the network layer, which\n"
        "samples road_base.tif (Row 2) along Road / IceRoad /\n"
        "Join edges — IceRoad × ICEROAD_TIME_PENALTY (2.0)\n"
        "and gated to Jan–Mar in weight_network_edges, not here.",
        ha="center", va="center", fontsize=8.8, color="#1B2631",
        linespacing=1.6,
        bbox=dict(boxstyle="round,pad=0.6", fc="#F2E9E3",
                  ec="#566573", lw=0.8),
    )

    # -------------------------------------------------------------- Row 4
    y4 = 5.2
    draw_grid(ax, overland_mm, 0.6, y4,
              title="overland_MM.tif  (all months)",
              subtitle="static_base × permafrost — pure terrain")
    draw_grid(ax, barge_open, 3.5, y4,
              mode="navigable",
              title="barge_MM.tif  (open)",
              subtitle="water & no ice → navigable")
    draw_grid(ax, barge_winter, 6.4, y4,
              mode="navigable",
              title="barge_MM.tif  (ice month)",
              subtitle="ice gates → ND on every water cell")

    # Domain badges — explicit "this output only lives on land / water"
    draw_domain_badge(ax, 1.6, y4 - 0.40, "LAND NETWORK ONLY",
                      LAND_BADGE_COLOR)
    draw_domain_badge(ax, 4.5, y4 - 0.40, "SEA NETWORK ONLY",
                      OCEAN_BADGE_COLOR)
    draw_domain_badge(ax, 7.4, y4 - 0.40, "SEA NETWORK ONLY",
                      OCEAN_BADGE_COLOR)

    # Vertical-flow arrows on the left margin. Fixed length so all three
    # are visually identical regardless of inter-row spacing; each arrow
    # is centered in the gap between consecutive rows.
    arrow_x = 0.25
    ARROW_LEN = 0.55
    GRID_H = 2.0   # 5 cells × 0.4
    for y_upper, y_lower in ((y1, y2), (y2, y3), (y3, y4)):
        gap_center = (y_upper + (y_lower + GRID_H)) / 2
        draw_arrow(
            ax, arrow_x, gap_center + ARROW_LEN / 2,
            arrow_x, gap_center - ARROW_LEN / 2,
        )

    # Legend on the right column, top-aligned with the first row of grids
    draw_legend(ax, 11.7, 14.6)

    # Per-pixel formula recap — placed just below the row-4 domain badges
    ax.text(
        0.6, 4.0,
        "Per-pixel composition rules",
        ha="left", va="center", fontsize=10, fontweight="bold",
        color="#1B2631",
    )
    formulas = (
        "OVERLAND        :  static_base × permafrost_mod                         "
        "(pure terrain; roads / ice roads are NOT burned in)\n"
        "BARGE           :  WATER_FRICTION_BARGE   where  water ∧ ¬sea_ice ∧ ¬river_ice;   "
        "NoData elsewhere\n"
        "ROAD_BASE static:  max(ROAD_FRICTION, slope_friction) × permafrost_mod   "
        "(no LULC, no water mask; NoData-free; road_base.tif, once per run)\n"
        "  → the network layer samples road_base along Road / IceRoad / Join edges;   "
        "IceRoad × ICEROAD_TIME_PENALTY (2.0), gated to Jan–Mar (weight_network_edges)"
    )
    ax.text(
        0.6, 2.6, formulas,
        ha="left", va="center", fontsize=8.5, color="#1B2631",
        family="DejaVu Sans Mono", linespacing=1.6,
        bbox=dict(boxstyle="round,pad=0.5", fc="#E3EAF2",
                  ec="#566573", lw=0.8),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print(f"wrote {output_path}")


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "friction_outputs" / "friction_grid_schema.png"
    render(out)
