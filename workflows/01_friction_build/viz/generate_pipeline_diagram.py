"""Render a two-page PDF documenting the friction-surface pipeline.

Page 1 — visual data-flow diagram from inputs → 24 monthly raster outputs.
Page 2 — file-by-file responsibilities legend.

Output: outputs/figures/friction_pipeline_diagram.pdf
Re-run after structural changes to keep the diagram current.

    python workflows/01_friction_build/viz/generate_pipeline_diagram.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
COL_INPUT     = "#E3EAF2"
COL_VALIDATE  = "#FCF3CF"
COL_COMPUTE   = "#D4E6F1"
COL_BRANCH    = "#D5E8D4"
COL_OUTPUT    = "#C8E6C9"
COL_QA        = "#FAD7A0"
COL_SUPPORT   = "#EAEDED"
COL_EDGE      = "#566573"
COL_TITLE     = "#1B2631"
COL_TEXT      = "#1B2631"

# Body text uses sans-serif (not monospace) so bullets fit comfortably.
BODY_FAMILY   = "DejaVu Sans"
MONO_FAMILY   = "DejaVu Sans Mono"


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def box(ax, x, y, w, h, title, body, *, fc, title_size=10.5, body_size=8.2,
        family=BODY_FAMILY):
    """Rounded-rect box with bold title and body text."""
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.2, edgecolor=COL_EDGE, facecolor=fc,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2, y + h - 0.22, title,
        ha="center", va="top",
        fontsize=title_size, fontweight="bold", color=COL_TITLE,
        family=BODY_FAMILY,
    )
    ax.text(
        x + 0.20, y + h - 0.58, body,
        ha="left", va="top",
        fontsize=body_size, color=COL_TEXT, family=family,
        linespacing=1.4,
    )


def arrow(ax, x0, y0, x1, y1, *, style="-|>", lw=1.4):
    ax.add_patch(FancyArrowPatch(
        (x0, y0), (x1, y1),
        arrowstyle=style, mutation_scale=14,
        linewidth=lw, color=COL_EDGE,
    ))


# ---------------------------------------------------------------------------
# Page 1 — flowchart (single-column vertical flow, full-width)
# ---------------------------------------------------------------------------

def render_flowchart(pdf: PdfPages) -> None:
    fig, ax = plt.subplots(figsize=(11, 14))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 14)
    ax.set_axis_off()

    fig.text(
        0.5, 0.972, "Friction Surface Construction Pipeline",
        ha="center", fontsize=18, fontweight="bold", color=COL_TITLE,
        family=BODY_FAMILY,
    )
    fig.text(
        0.5, 0.948,
        "friction_surface/ package  ·  2 modes × 12 months = 24 monthly raster surfaces",
        ha="center", fontsize=10.5, color=COL_TITLE, style="italic",
        family=BODY_FAMILY,
    )

    x = 0.6
    w = 9.8

    stages = [
        # (y, h, title, body, colour)
        (11.40, 1.70,
         "1.  INPUTS  (friction_inputs/ + outputs/)",
         "•  slope.tif   — per-pixel slope from FabDEM (degrees, float32)\n"
         "•  lulc.tif    — Dynamic World modal class (0–8)\n"
         "•  permafrost.tif — Pastick et al. extent (0–1 or 0–100, auto-detected)\n"
         "•  sea_ice/sea_ice_{01..12}.tif    — AOOS monthly climatology\n"
         "•  river_ice/river_ice_{01..12}.tif — Brown et al. monthly probability\n"
         "•  waterway_mask_150m.tif  — widens barge navigability (build_corridor_masks.py)",
         COL_INPUT),

        (9.80, 1.35,
         "2.  PREFLIGHT VALIDATION   →   friction_preflight.py",
         "•  Establishes canonical grid from lulc.tif (CRS, transform, shape, res)\n"
         "•  Per-layer status: OK  /  WARPABLE  /  FATAL\n"
         "•  Spot-checks value ranges (LULC 0–8, slope 0–90°, ice 0–100 or 0–1)\n"
         "•  Raises PreflightError before any computation begins",
         COL_VALIDATE),

        (8.55, 1.10,
         "3.  STATIC BASE   →   friction_surface.py",
         "•  slope  →  SLOPE_FRICTION  (flat 1.0  |  rolling 1.4  |  mountain 1.75)\n"
         "•  lulc   →  LULC_FRICTION dict;  class 0 (water) ⇒ NoData in overland base\n"
         "•  static_base = slope_friction × lulc_friction   (multiplicative)",
         COL_COMPUTE),

        (7.05, 1.30,
         "4.  PERMAFROST + PER-MONTH ICE LOADERS   (× 12 for ice)",
         "•  load_permafrost_base  →  fraction; same-grid only (alignment is upstream)\n"
         "•  compute_permafrost_modifier (per-pixel, year-round — Pastick p, IPA bins):\n"
         "       p<0.10 → 1.00   p<0.50 → 1.15   p<0.90 → 1.30   p≥0.90 → 1.50\n"
         "•  _load_ice  →  sea_ice_present, river_ice_present (auto-normalises 0–1 vs 0–100)",
         COL_COMPUTE),

        (5.05, 1.85,
         "5.  build_mode_friction(mode)   —   2 BRANCHES   (× 12 ⇒ 24 surfaces)",
         "OVERLAND    static_base × permafrost_mod   (pure terrain; water → NoData)\n"
         "            roads / ice roads are NOT burned in — priced by the network layer\n"
         "            (road_base.tif sampling; IceRoad × 2.0, Jan–Mar, in weight_network_edges)\n"
         "BARGE       navigable = water_mask  &  ¬sea_ice_present  &  ¬river_ice_present\n"
         "            out = WATER_FRICTION_BARGE (1.0);  else NoData  (ice IS the gate)",
         COL_BRANCH),

        (3.55, 1.25,
         "6.  OUTPUTS   →   write_friction_stack  →  friction_outputs/friction_stack/",
         "•  24 GeoTIFFs:  {overland, barge}_{01..12}.tif   +   road_base.tif (static)\n"
         "•  float32, NoData = -9999, LZW-compressed, EPSG:3338 @ 150 m\n"
         "•  Friction stays environmental-only; cost rates applied separately downstream",
         COL_OUTPUT),

        (1.65, 1.65,
         "7.  POST-BUILD QA   →   qa_friction_stack.py",
         "•  Exactly 24 files ({overland, barge}_{01..12}.tif); profile matches reference\n"
         "•  Monthly barge: July valid-pixel count > January  (sea-ice gating sanity)\n"
         "•  Overland min ≥ min(SLOPE_FRICTION)  (pure terrain, no burn-in)\n"
         "•  Reports ice-road geometry coverage near Bethel (informational)\n"
         "•  Exit 0 on all-pass; nonzero on any hard-fail check",
         COL_QA),
    ]

    bodies_use_mono = {  # branch box benefits from column alignment
        "5.  build_mode_friction(mode)   —   2 BRANCHES   (× 12 ⇒ 24 surfaces)"
    }

    for y, h, title, body, fc in stages:
        family = MONO_FAMILY if title in bodies_use_mono else BODY_FAMILY
        box(ax, x, y, w, h, title, body, fc=fc, family=family)

    # Arrows down the spine (between adjacent stage boxes).
    spine_x = x + w / 2
    transitions = list(zip(stages[:-1], stages[1:]))
    for top, bot in transitions:
        y_top = top[0]                    # bottom of upper box (= y coord)
        y_bot = bot[0] + bot[1]           # top of lower box (= y + h)
        arrow(ax, spine_x, y_top, spine_x, y_bot)

    fig.text(
        0.5, 0.02,
        "Regenerable artifact — run  python workflows/01_friction_build/viz/generate_pipeline_diagram.py  "
        "after structural changes.",
        ha="center", fontsize=8, style="italic", color="#566573",
        family=BODY_FAMILY,
    )

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Page 2 — file responsibilities (2-column grid, 10 cards)
# ---------------------------------------------------------------------------

FILE_CARDS = [
    {
        "name": "friction_config.py",
        "role": "Constants only — no I/O.",
        "bullets": [
            "CRS_TARGET = EPSG:3338, TARGET_RESOLUTION = 150 m",
            "SLOPE_FRICTION, LULC_FRICTION reclass tables",
            "PERMAFROST_ZONE_BREAKS = (0.10, 0.50, 0.90)",
            "PERMAFROST_ZONE_MULTIPLIERS = (1.00, 1.15, 1.30, 1.50)",
            "SEA/RIVER_ICE_THRESHOLD = 0.15 (NSIDC open-water limit)",
            "ROAD_FRICTION = 1.0   ROAD_BRIDGE_FRICTION = 1.0",
            "ICEROAD_TIME_PENALTY = 2.0  (UAF/INE 2023 Tbl 8.1)",
            "SEASON_MONTHS: ice road {1..3}, marine linehaul {6..10}",
            "MODES = ('overland', 'barge')  (was 3, ice_road folded in)",
            "FRICTION_NODATA = -9999.0",
        ],
    },
    {
        "name": "friction_paths.py",
        "role": "Single source of truth for filesystem layout.",
        "bullets": [
            "RASTER_DIR (env override)",
            "FRICTION_OUTPUT_DIR (env override)",
            "Raster paths: slope, lulc, permafrost, sea/river_ice",
            "Corridor mask: WATERWAY_MASK_TIF",
            "Networks: roads, waterways, airports, ports, flights",
            "Ice-road: ICE_ROADS_SHP, FUEL_DELIVERY_METHOD_SHP",
            "No import-time side effects (paths anchored to repo root)",
        ],
    },
    {
        "name": "friction_io.py",
        "role": "Generic raster I/O helpers shared by builders.",
        "bullets": [
            "load_and_ensure_crs(path, target_crs)",
            "load_raster_profile(path)",
            "Consumed by friction_surface, build_corridor_masks",
        ],
    },
    {
        "name": "friction_preflight.py",
        "role": "Fail-fast validation of every raster before any work.",
        "bullets": [
            "Establishes canonical grid from lulc.tif",
            "LayerReport per file: OK / WARPABLE / FATAL",
            "Catches missing files, CRS / resolution / shape mismatches",
            "Sub-pixel offsets caught at ORIGIN_TOL_M = 0.01 m",
            "Value spot-checks: LULC ∈ 0..8, slope ∈ 0..90°,",
            "    ice ∈ 0..100",
            "Raises PreflightError on any FATAL",
        ],
    },
    {
        "name": "friction_surface.py",
        "role": "The actual surface builder — pure numpy / rasterio.",
        "bullets": [
            "load_permafrost_base — same-grid permafrost loader",
            "compute_permafrost_modifier — Pastick p binned by IPA thresholds",
            "_load_ice — same-grid sea/river ice loader, auto-normalises units",
            "build_mode_friction(mode):",
            "    OVERLAND  static_base × permafrost_mod (pure terrain)",
            "    BARGE     navigable water; sea/river-ice gates",
            "compute_road_base → road_base.tif (network edge sampling)",
            "write_friction_stack(input_dir, output_dir)  →  24 TIFs",
        ],
    },
    {
        "name": "friction_costs.py",
        "role": "Cost rates & intermodal fees — env / econ split from friction.",
        "bullets": [
            "BASELINE_RATES_PER_GALLON_MILE (per mode)",
            "VEHICLE_MILE_RATES_REFERENCE (provenance)",
            "INTERMODAL_TRANSFER_FEES (per-handoff $/gal)",
            "INTERMODAL_TRANSFER_ADDONS (blending, lightering)",
            "FUEL_DENSITY_LB_PER_GAL = 7.1",
            "STATE_CONTRACT_ADDERS_PER_GALLON (validation)",
            "MODE_METADATA, chain_cost_with_transfer_fees",
            "load_ice_road_communities(as_of) — historical-aware",
        ],
    },
    {
        "name": "run_friction_pipeline.py",
        "role": "Friction-surface build entry point.",
        "bullets": [
            "CLI: --input-dir, --output-dir",
            "Validates inputs, calls write_friction_stack",
            "Per-edge weighting is a separate step:",
            "    load_final_network -> weight_network_edges",
        ],
    },
    {
        "name": "qa_friction_stack.py",
        "role": "Post-build acceptance checks on the 24-raster stack.",
        "bullets": [
            "Exactly 24 files; profile matches reference",
            "Monthly barge: July > January valid pixels",
            "Overland: no negative values other than NoData",
            "Reports ice-road geometry near Bethel (info only)",
            "Exit 0 on all-pass; nonzero on hard-fail",
        ],
    },
    {
        "name": "test_friction_surface.py",
        "role": "Pytest suite covering the surface builder.",
        "bullets": [
            "load_permafrost_base: same-grid pass; raises on mismatch",
            "_load_ice: same-grid pass; raises on mismatch",
            "Ice threshold split invariant at equal thresholds",
            "Overland is pure terrain: static_base × permafrost",
            "Overland water pixels stay NoData",
            "Loader errors name the upstream align_* fix script",
        ],
    },
    {
        "name": "viz/plot_friction_stack.py",
        "role": "Monthly-stack renderer — one 3x4 PNG per mode.",
        "bullets": [
            "Decimated read (~800 rows); shared 1-99 pct color scale",
            "Two-tone NoData underlay keyed on LULC water class:",
            "    water = ice blue, land = light gray",
            "Mode-specific legend spells out what NoData means —",
            "    barge: iced water above SEA/RIVER_ICE_THRESHOLD",
            "    (impassable); overland: open water vs glaciers/DEM gaps",
            "Thresholds read live from friction_config (never hard-coded)",
            "Writes {mode}_monthly_friction.png to friction_outputs/",
        ],
    },
]


def render_file_legend(pdf: PdfPages) -> None:
    fig, ax = plt.subplots(figsize=(11, 18))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 18)
    ax.set_axis_off()

    fig.text(
        0.5, 0.972, "File-by-file responsibilities",
        ha="center", fontsize=17, fontweight="bold", color=COL_TITLE,
        family=BODY_FAMILY,
    )
    fig.text(
        0.5, 0.948,
        "friction_surface/ package — 11 modules",
        ha="center", fontsize=10, color=COL_TITLE, style="italic",
        family=BODY_FAMILY,
    )

    # Two-column grid. Cards: width 4.8, gap 0.4, left margin 0.4 → right margin 0.4.
    # y_top is the TOP edge of each card; the patch is drawn downward from it
    # so no row can extend past the axes limit.
    col_w = 4.8
    col_x = [0.40, 5.80]
    row_h = 2.70
    top_y = 16.60

    for idx, card in enumerate(FILE_CARDS):
        col = idx % 2
        row = idx // 2
        x = col_x[col]
        y_top = top_y - row * row_h

        card_h = row_h - 0.20
        # Background card
        patch = FancyBboxPatch(
            (x, y_top - card_h), col_w, card_h,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            linewidth=1.1, edgecolor=COL_EDGE, facecolor=COL_SUPPORT,
        )
        ax.add_patch(patch)

        # Filename (monospace so it reads as code)
        ax.text(
            x + 0.18, y_top - 0.22, card["name"],
            ha="left", va="top",
            fontsize=11, fontweight="bold", color=COL_TITLE,
            family=MONO_FAMILY,
        )
        # Role
        ax.text(
            x + 0.18, y_top - 0.58, card["role"],
            ha="left", va="top",
            fontsize=8.5, style="italic", color="#34495E",
            family=BODY_FAMILY,
        )
        # Bullets
        bullet_block = "\n".join(f"•  {b}" for b in card["bullets"])
        ax.text(
            x + 0.22, y_top - 0.92, bullet_block,
            ha="left", va="top",
            fontsize=7.9, color=COL_TEXT, family=BODY_FAMILY,
            linespacing=1.35,
        )

    fig.text(
        0.5, 0.018,
        "Each card lists the file's primary role and the main constants / functions it exposes.",
        ha="center", fontsize=8, style="italic", color="#566573",
        family=BODY_FAMILY,
    )

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    out_path = Path(__file__).parent / "friction_pipeline_diagram.pdf"
    with PdfPages(out_path) as pdf:
        render_flowchart(pdf)
        render_file_legend(pdf)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
