"""generate_grid_schema_public.py

Public-facing, plain-language companion to `generate_grid_schema.py`.

Same toy 5x5 world and the SAME computed grids (imported directly, so the
two figures can never drift apart), but rendered for a general audience:
community members, tribal / state / federal / private staff, and anyone
new to this space. Jargon and matrix math are replaced by a three-step
story with plain labels, colour categories instead of raw numbers, and a
"in plain terms" recap.

Story:
  STEP 1  What we measure        (the six ingredients)
  STEP 2  Combine into one map   (how hard the land is to cross)
  STEP 3  Routes change by season (summer vs winter Jan-Mar)

Output: friction_surface/friction_outputs/friction_grid_schema_public.png
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

# Reuse the exact geometry + computed grids from the technical schema so the
# public figure is guaranteed faithful to the real construction logic.
from generate_grid_schema import (
    LAND,  # noqa: F401 (kept for schema-tinkering convenience)
    OCEAN,  # noqa: F401 (kept for schema-tinkering convenience)
    PERMAFROST_MOD,
    RIVER,  # noqa: F401 (kept for schema-tinkering convenience)
    RIVER_ICE_WINTER,
    SEA_ICE_WINTER,
    SLOPE,
    WATER,
    barge,  # noqa: F401 (kept for schema-tinkering convenience)
    land_base,
    static_base,
    LULC,
)

# Route networks (toy geometry) live here. The overland raster does not
# encode roads / ice roads — they are priced by the network layer — so the
# technical schema omits these masks. This public, system-level figure shows
# them as routes drawn on top of the terrain-difficulty map.
ROAD_MASK = np.array([
    [0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1],
    [0, 0, 0, 1, 0],
    [0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0],
], dtype=int)

ICEROAD_MASK = np.array([
    [1, 1, 0, 0, 0],
    [1, 0, 0, 0, 0],
    [1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
], dtype=int)

# ---------------------------------------------------------------------------
# Public palette — plain difficulty categories (green = easy ... red = hard)
# ---------------------------------------------------------------------------
EASY = "#1a9850"       # green
MODERATE = "#a6d96a"   # light green
HARDER = "#fee08b"     # warm yellow (slightly deeper than schema for contrast)
HARD = "#fdae61"       # orange
VERY_HARD = "#d73027"  # red

BLOCKED = "#3b3b3b"          # can't cross by land
WATER_OPEN = "#2c7fb8"       # boatable open water
WATER_ICED = "#cfe0ea"       # frozen water, no boats
ROAD_GLYPH = "#222222"       # built road overlay
ICEROAD_GLYPH = "#4aa3df"    # winter ice-road overlay

INK = "#1B2631"
SUBTLE = "#566573"
PANEL_BG = "#F4F7FA"
PANEL_EDGE = "#c7d2dd"
EDGE = "#2c3e50"

# Season accent colours for the step-3 panel headers
SUMMER_C = "#1f7a3f"
WINTER_C = "#1f4e79"


def difficulty_color(v: float) -> str:
    """Map a friction value to a plain difficulty-category colour."""
    if np.isnan(v):
        return BLOCKED
    if v <= 1.3:
        return EASY
    if v <= 1.9:
        return MODERATE
    if v <= 2.4:
        return HARDER
    if v <= 3.2:
        return HARD
    return VERY_HARD


# ---------------------------------------------------------------------------
# Low-level cell / glyph drawing
# ---------------------------------------------------------------------------
def _cell(ax, cx, cy, cell, color, *, lw=0.6):
    ax.add_patch(Rectangle((cx, cy), cell, cell, facecolor=color,
                           edgecolor=EDGE, linewidth=lw))


def _draw_route_network(ax, mask, x, y, cell, color, *, dashed=False):
    """Render a route mask as a network that runs *continuously* across
    pixels AND fills each route pixel edge-to-edge.

    For every ON cell we draw from its centre out to each cell edge that
    either (a) faces an ON neighbour — so adjacent pixels join flush at
    the shared edge — or (b) is the open end of a straight run, so a
    terminal pixel is still fully covered rather than half-empty. Corners
    and T-junctions get no spurious spur into empty ground."""
    h = cell / 2
    on = mask == 1
    lw = cell * (5.2 if not dashed else 4.4)
    kw = dict(color=color, lw=lw, solid_capstyle="butt", zorder=5)
    if dashed:
        kw["dashes"] = (2.2, 1.6)

    # name -> (di, dj, edge dx, edge dy)
    DIRS = {"R": (0, 1, h, 0), "L": (0, -1, -h, 0),
            "D": (1, 0, 0, -h), "U": (-1, 0, 0, h)}
    OPP = {"R": "L", "L": "R", "U": "D", "D": "U"}
    PERP = {"R": ("U", "D"), "L": ("U", "D"),
            "U": ("L", "R"), "D": ("L", "R")}

    def is_on(i, j):
        return 0 <= i < 5 and 0 <= j < 5 and on[i, j]

    for i in range(5):
        for j in range(5):
            if not on[i, j]:
                continue
            cx = x + j * cell + h
            cy = y + (4 - i) * cell + h
            for d, (di, dj, ex, ey) in DIRS.items():
                if is_on(i + di, j + dj):
                    draw = True
                else:
                    odi, odj, _, _ = DIRS[OPP[d]]
                    p1, p2 = PERP[d]
                    perp_off = not is_on(i + DIRS[p1][0], j + DIRS[p1][1]) \
                        and not is_on(i + DIRS[p2][0], j + DIRS[p2][1])
                    draw = is_on(i + odi, j + odj) and perp_off
                if draw:
                    ax.plot([cx, cx + ex], [cy, cy + ey], **kw)
            # centre node fills the join so corners/T-joints stay solid
            ax.plot([cx], [cy], marker="o", markersize=lw, markeredgewidth=0,
                    color=color, zorder=6)


def _wave_glyph(ax, cx, cy, cell):
    ax.text(cx + cell / 2, cy + cell / 2, "≈", ha="center", va="center",
            fontsize=cell * 22, color="white", zorder=5)


def _ice_glyph(ax, cx, cy, cell):
    ax.text(cx + cell / 2, cy + cell / 2, "❄", ha="center", va="center",
            fontsize=cell * 15, color="#6b8ea8", zorder=5)


def _title(ax, x, y, w, cell, text, sub=None, size=10):
    ax.text(x + w * cell / 2, y + 5 * cell + 0.10, text, ha="center",
            va="bottom", fontsize=size, fontweight="bold", color=INK)
    if sub:
        ax.text(x + w * cell / 2, y - 0.07, sub, ha="center", va="top",
                fontsize=7.4, color=SUBTLE, style="italic")


# ---------------------------------------------------------------------------
# Ingredient mini-grids (STEP 1)
# ---------------------------------------------------------------------------
def draw_ingredient(ax, grid, x, y, cell, kind, title, sub):
    """kind: 'difficulty' | 'permafrost' | 'mask' | 'ice'."""
    for i in range(5):
        for j in range(5):
            v = grid[i, j]
            cx = x + j * cell
            cy = y + (4 - i) * cell
            if kind in ("difficulty", "permafrost") and WATER[i, j]:
                # water reads as water, not "can't cross" — see routes below
                color = WATER_OPEN
            elif kind == "difficulty":
                color = difficulty_color(v)
            elif kind == "permafrost":
                # permafrost modifier: low->green, high->orange
                color = difficulty_color(1.0 + (v - 1.0) * 3.2)
            elif kind == "mask":
                color = ROAD_GLYPH if v == 1 else "#e8edf2"
            elif kind == "iceroadmask":
                color = ICEROAD_GLYPH if v == 1 else "#e8edf2"
            elif kind == "ice":
                if WATER[i, j]:
                    color = WATER_ICED if v == 1 else WATER_OPEN
                else:
                    color = "#eef1f4"
            _cell(ax, cx, cy, cell, color, lw=0.5)
    _title(ax, x, y, 5, cell, title, sub, size=8.6)


# ---------------------------------------------------------------------------
# Combined difficulty map (STEP 2) and seasonal route maps (STEP 3)
# ---------------------------------------------------------------------------
def draw_land_difficulty(ax, land, x, y, cell, title, sub):
    for i in range(5):
        for j in range(5):
            cx = x + j * cell
            cy = y + (4 - i) * cell
            if WATER[i, j]:
                _cell(ax, cx, cy, cell, WATER_OPEN)
            else:
                _cell(ax, cx, cy, cell, difficulty_color(land[i, j]))
    _title(ax, x, y, 5, cell, title, sub, size=11)


def draw_season(ax, overland, x, y, cell, *, winter, title, sub, accent):
    """One integrated 'how you get around' panel for a season.

    Land cells coloured by difficulty; built roads + bridges overlaid;
    ice roads overlaid in winter; water shown open (summer) or iced
    (winter).
    """
    # 1) base fills — land difficulty + water (bridges carry a road, so
    #    they get no wave / ice glyph underneath)
    for i in range(5):
        for j in range(5):
            cx = x + j * cell
            cy = y + (4 - i) * cell
            is_water = WATER[i, j]
            is_bridge = is_water and ROAD_MASK[i, j] == 1
            if is_water:
                _cell(ax, cx, cy, cell, WATER_ICED if winter else WATER_OPEN)
                if not is_bridge:
                    if winter:
                        _ice_glyph(ax, cx, cy, cell)
                    else:
                        _wave_glyph(ax, cx, cy, cell)
            else:
                _cell(ax, cx, cy, cell, difficulty_color(overland[i, j]))

    # 2) route overlays drawn as continuous networks across pixels
    if winter:
        _draw_route_network(ax, ICEROAD_MASK, x, y, cell, ICEROAD_GLYPH,
                            dashed=True)
    _draw_route_network(ax, ROAD_MASK, x, y, cell, ROAD_GLYPH, dashed=False)

    # accent header bar
    ax.add_patch(FancyBboxPatch(
        (x, y + 5 * cell + 0.06), 5 * cell, 0.34,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        facecolor=accent, edgecolor="none", zorder=2))
    ax.text(x + 5 * cell / 2, y + 5 * cell + 0.23, title, ha="center",
            va="center", fontsize=11, fontweight="bold", color="white", zorder=3)
    if sub:
        ax.text(x + 5 * cell / 2, y - 0.07, sub, ha="center", va="top",
                fontsize=8.0, color=SUBTLE, style="italic")


# ---------------------------------------------------------------------------
# Shared decoration
# ---------------------------------------------------------------------------
def section_header(ax, x, y, num, text):
    ax.text(x, y, f"{num}", ha="center", va="center", fontsize=13,
            fontweight="bold", color="white",
            bbox=dict(boxstyle="circle,pad=0.32", fc=INK, ec="none"))
    ax.text(x + 0.42, y, text, ha="left", va="center", fontsize=13,
            fontweight="bold", color=INK)


def down_arrow(ax, x, ymid, label=None, length=0.62):
    y0, y1 = ymid + length / 2, ymid - length / 2
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>",
                                 mutation_scale=22, linewidth=2.4, color=SUBTLE))
    if label:
        ax.text(x + 0.28, ymid, label, ha="left", va="center",
                fontsize=8.4, color=SUBTLE, style="italic")


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------
def render(output_path: Path) -> None:
    static = static_base(SLOPE, LULC)
    land = land_base(static, PERMAFROST_MOD)
    # Overland terrain difficulty is season-invariant (pure terrain), so both
    # season panels share this base. What changes by season is water (open vs
    # frozen) and the winter ice-road overlay; roads / ice roads are routes
    # drawn on top, priced in the network layer.
    overland_summer = land
    overland_winter = land

    fig, ax = plt.subplots(figsize=(13, 16.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 16.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- Title block ----------------------------------------------------
    ax.text(6.5, 16.05,
            "Combining Geospatial Data to Represent Fuel Network Traversal in Alaska",
            ha="center", va="center", fontsize=16, fontweight="bold", color=INK)
    ax.text(6.5, 15.50,
            "The friction surface behind fuel-delivery routing",
            ha="center", va="center", fontsize=11, color=SUBTLE, style="italic")
    ax.text(6.5, 15.08,
            "Each square represents grid pixel that corresponds to a small patch of land; its color shows how hard it is to travel across that pixel. ",
            ha="center", va="center", fontsize=8.8, color=SUBTLE)

    # ---- STEP 1 : ingredients ------------------------------------------
    section_header(ax, 0.60, 14.45, "1", "Input Datasets")
    ax.text(1.05, 14.10, "Aligned on the same reference grid with a 150m resolution and Alaska Albers CRS ",
            ha="left", va="center", fontsize=8.8, color=SUBTLE)

    ing_cell = 0.26
    xs = [0.55, 2.55, 4.55, 6.55, 8.55, 10.55]
    ing_y = 12.30
    draw_ingredient(ax, SLOPE, xs[0], ing_y, ing_cell, "difficulty",
                    "Steepness", "flat is easier")
    draw_ingredient(ax, LULC, xs[1], ing_y, ing_cell, "difficulty",
                    "Land cover", "tundra, forest, bare")
    draw_ingredient(ax, PERMAFROST_MOD, xs[2], ing_y, ing_cell, "permafrost",
                    "Permafrost", "ice-rich soils")
    draw_ingredient(ax, ROAD_MASK, xs[3], ing_y, ing_cell, "mask",
                    "Roads & bridges", "built routes")
    draw_ingredient(ax, ICEROAD_MASK, xs[4], ing_y, ing_cell, "iceroadmask",
                    "Winter ice roads", "Jan–Mar only")
    draw_ingredient(ax, SEA_ICE_WINTER | RIVER_ICE_WINTER, xs[5], ing_y,
                    ing_cell, "ice", "River & sea ice", "blocks boats in winter")

    # ---- STEP 2 : combined difficulty map ------------------------------
    section_header(ax, 0.60, 11.35, "2", "Combined into a friction surface")
    map_cell = 0.5
    s2x, s2y = 1.30, 8.40
    draw_land_difficulty(ax, land, s2x, s2y, map_cell,
                         "Traversal difficulty",
                         "steepness + land cover + permafrost, together")

    # legend to the right of the step-2 map
    _draw_legend(ax, 5.55, 10.95)

    # ---- STEP 3 : seasonal routes --------------------------------------
    section_header(ax, 0.60, 7.85, "3", "Seasonality Considerations")
    s3y = 4.55
    draw_season(ax, overland_summer, 1.30, s3y, map_cell, winter=False,
                title="SUMMER (open water)", accent=SUMMER_C,
                sub="barge on rivers & coast + roads on land")
    draw_season(ax, overland_winter, 7.30, s3y, map_cell, winter=True,
                title="WINTER (Jan–Mar)", accent=WINTER_C,
                sub="ice blocks boats — ice roads open on land")

    # ---- Left-margin flow arrows ---------------------------------------
    down_arrow(ax, 0.32, (ing_y + (s2y + 5 * map_cell)) / 2)   # step1 -> step2
    down_arrow(ax, 0.32, (s2y + (s3y + 5 * map_cell)) / 2)     # step2 -> step3

    # ---- Plain-terms recap ---------------------------------------------
    ax.add_patch(FancyBboxPatch(
        (0.55, 0.30), 11.9, 3.62,
        boxstyle="round,pad=0.04,rounding_size=0.12",
        facecolor=PANEL_BG, edgecolor=PANEL_EDGE, linewidth=1.0))
    ax.text(0.85, 3.62, "In plain terms", ha="left", va="center",
            fontsize=12.5, fontweight="bold", color=INK)
    bullets = [
        "Every place gets a travel-difficulty (average friction value) score — flatter, firmer ground scores easy (1.0); steep, "
        " or ice-rich ground scores increase.",
        "Some ground can’t be crossed at all (DEM gaps, glaciers, open water for land travel) — shown in dark grey.",
        "Roads and bridges (drawn on top) add fast links across that terrain; a paved road isn’t slowed by the permafrost or land cover beneath it.",
        "In deep winter (Jan–Mar), packed-snow ice roads open new overland links — but they cost more time than a real road.",
        "Boats (barge) can travel open water in summer; when rivers and the sea freeze, those water routes close for the season.",
        "Plane delivery is an option in most cases but is the most expensive fuel delivery mode",
        "Combine all of this for every month and you get the map that decides how fuel can reach each community.",
    ]
    ty = 3.18
    line_h = 0.235
    for b in bullets:
        wrapped = textwrap.fill(b, width=132)
        nlines = wrapped.count("\n") + 1
        ax.text(0.95, ty, "•", ha="left", va="top", fontsize=11.5,
                color=SUMMER_C, fontweight="bold")
        ax.text(1.22, ty, wrapped, ha="left", va="top", fontsize=9.6,
                color=INK, linespacing=1.35)
        ty -= nlines * line_h + 0.13

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {output_path}")


def _draw_legend(ax, x, y):
    """Two-column key so it fits within the step-2 map's height."""
    sw = 0.30
    row = 0.40
    colB = x + 3.55

    ax.text(x, y, "Traversibility", ha="left", va="bottom",
            fontsize=10, fontweight="bold", color=INK)

    # Column A — land difficulty
    left = [
        (EASY, "Easy — flat, firm, or road"),
        (MODERATE, "Moderate"),
        (HARDER, "Harder"),
        (HARD, "Hard"),
        (VERY_HARD, "Very hard"),
        (BLOCKED, "Can’t cross by land"),
    ]
    cur = y - 0.22
    for col, lab in left:
        _cell(ax, x, cur - sw, sw, col)
        ax.text(x + sw + 0.14, cur - sw / 2, lab, ha="left", va="center",
                fontsize=8.6, color=INK)
        cur -= row

    # Column B — water + route markers
    ax.text(colB, y, "Water & routes", ha="left", va="bottom",
            fontsize=10, fontweight="bold", color=INK)
    cur = y - 0.22
    for col, lab in [(WATER_OPEN, "Open water — boatable (summer)"),
                     (WATER_ICED, "Frozen water — no boats (winter)")]:
        _cell(ax, colB, cur - sw, sw, col)
        ax.text(colB + sw + 0.14, cur - sw / 2, lab, ha="left", va="center",
                fontsize=8.6, color=INK)
        cur -= row

    cur -= 0.14
    yline = cur - sw / 2
    ax.plot([colB + 0.02, colB + sw - 0.02], [yline, yline], color=ROAD_GLYPH,
            lw=6, solid_capstyle="round")
    ax.text(colB + sw + 0.14, yline, "Built road / bridge", ha="left",
            va="center", fontsize=8.6, color=INK)
    cur -= row
    yline = cur - sw / 2
    ax.plot([colB + 0.02, colB + sw - 0.02], [yline, yline], color=ICEROAD_GLYPH,
            lw=5, dashes=(1.4, 1.1), solid_capstyle="round")
    ax.text(colB + sw + 0.14, yline, "Winter ice road", ha="left",
            va="center", fontsize=8.6, color=INK)


if __name__ == "__main__":
    out = (Path(__file__).parent.parent / "friction_outputs"
           / "friction_grid_schema_public.png")
    render(out)
