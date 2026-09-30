#!/usr/bin/env python3
"""Four-panel "how do we connect the data?" story figure + editable deck.

Layout: three maps across the top (A bulk fuel facilities, B spatial network,
C tank capacity at hubs) and one full-width "long box" beneath (D), reserved
for the socio-economic / cost context that would let us reason about *fuel
disruptions*.

    +-----------+-----------+-----------+
    |  A. sites |  B. net   |  C. hubs  |
    +-----------+-----------+-----------+
    |  D. socio-economic & cost context |
    +-----------------------------------+

Outputs (all under outputs/figures/):
  * data_connection_story.png        — the combined 300-dpi figure
  * panels/panel_{A,B,C}.png         — each map on its own (for slides)
  * data_connection_story.pptx       — EDITABLE deck: upload to Google Slides
                                        (File > Import slides) and the titles
                                        and the D box become native, editable
                                        text; the maps are placed images you
                                        can move/resize.

Panels A-C are the real repo data (EPSG:3338 Alaska Albers); D is a
deliberate placeholder.

Run with the project venv:
    .venv/bin/python workflows/03_multimodal_join/viz/plot_data_connection_story.py
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[3]

NODES_SHP = ROOT / "final_network/network_joined_nodes/network_joined_nodes.shp"
EDGES_SHP = ROOT / "final_network/network_joined_edges/network_joined_edges.shp"
FUEL_CSV = ROOT / "inputs/bulk_fuel_data/processed/bulk_fuel_sites_clean.csv"
TIGER_SHP = ROOT / "inputs/region_and_census_data/tiger/cb_2023_us_state_500k.shp"

OUT_DIR = ROOT / "outputs/figures"
PANEL_DIR = OUT_DIR / "panels"
OUT_PNG = OUT_DIR / "data_connection_story.png"
OUT_PPTX = OUT_DIR / "data_connection_story.pptx"

CRS = 3338

# Colour per transport mode for the network panel.
MODE_COLORS = {
    "Road": "#444444",
    "Waterway": "#1f77b4",
    "Air": "#e377c2",
    "IceRoad": "#17becf",
    "IceRoadConnector": "#17becf",
    "Transfer": "#ff7f0e",
    "Bridge": "#8c564b",
}

LAND_FACE = "#f2efe9"
LAND_EDGE = "#c9c3b8"
CAPTION_COLOR = "#555555"

# The reserved-panel narrative, kept as data so the PNG and the editable
# .pptx stay in sync.
D_TITLE = "D. Socio-economic & cost context  (reserved)"
D_LEAD = "Reserved for the missing link:"
D_CHIPS = [
    "community demand & population",
    "cost of energy burden",
    "delivery cost per gallon",
    "disruption / outage events",
]
D_NOTE = ("The data exists — qualitative and quantitative — "
          "but is not yet joined to the network above.")
D_QUESTION = "how do we connect them?"

PANEL_TITLES = {
    "A": "A. Bulk fuel facilities",
    "B": "B. Multimodal spatial network",
    "C": "C. Tank capacity at hubs",
}

# Red callout pointing at the whole assemblage.
CALLOUT = ("Fuel disruption & community impacts ignite an urgent need\n"
           "for data deliverables built on this geospatial data")
CALLOUT_RED = "#d62728"


# --------------------------------------------------------------------------
# Shared map helpers
# --------------------------------------------------------------------------
def load_land() -> gpd.GeoDataFrame:
    """Alaska outline in EPSG:3338, simplified for fast rendering."""
    land = gpd.read_file(TIGER_SHP)
    land = land[land["STUSPS"] == "AK"].to_crs(CRS).copy()
    land["geometry"] = land.geometry.simplify(1000)
    return land


def draw_land(ax, land) -> None:
    land.plot(ax=ax, facecolor=LAND_FACE, edgecolor=LAND_EDGE, linewidth=0.4, zorder=0)


def style_map_axis(ax, land, caption: str, *, title: str | None) -> None:
    """Common map framing: Alaska extent, no ticks, caption as an x-label.

    When ``title`` is given it is drawn on the axis (combined figure); pass
    None for the standalone panel exports so the title can live as native,
    editable text in the slide deck.
    """
    minx, miny, maxx, maxy = land.total_bounds
    padx = (maxx - minx) * 0.02
    pady = (maxy - miny) * 0.02
    ax.set_xlim(minx - padx, maxx + padx)
    ax.set_ylim(miny - pady, maxy + pady)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel(caption, fontsize=8.5, color=CAPTION_COLOR, labelpad=6)
    if title is not None:
        ax.set_title(title, fontsize=12, fontweight="bold", pad=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#999999")
        spine.set_linewidth(0.6)


# --------------------------------------------------------------------------
# Panel A — bulk fuel facilities
# --------------------------------------------------------------------------
def panel_facilities(ax, land, *, title: str | None) -> int:
    fuel = pd.read_csv(FUEL_CSV)
    fuel = fuel.dropna(subset=["lon", "lat"])
    gdf = gpd.GeoDataFrame(
        fuel,
        geometry=gpd.points_from_xy(fuel["lon"], fuel["lat"]),
        crs=4326,
    ).to_crs(CRS)

    draw_land(ax, land)
    gdf.plot(
        ax=ax,
        color="#d62728",
        markersize=5,
        alpha=0.65,
        edgecolor="white",
        linewidth=0.15,
        zorder=3,
    )
    style_map_axis(ax, land, f"{len(gdf):,} tank-farm sites  ·  ASTF inventory", title=title)
    return len(gdf)


# --------------------------------------------------------------------------
# Panel B — spatial network
# --------------------------------------------------------------------------
def panel_network(ax, land, *, title: str | None) -> tuple[int, int]:
    edges = gpd.read_file(EDGES_SHP).to_crs(CRS)
    nodes = gpd.read_file(NODES_SHP).to_crs(CRS)

    draw_land(ax, land)

    # Draw roads first (densest) so the sparser marine/air modes stay legible.
    draw_order = ["Road", "Waterway", "IceRoad", "IceRoadConnector", "Air", "Transfer", "Bridge"]
    present = [t for t in draw_order if t in set(edges["type"])]
    for t in present:
        sub = edges[edges["type"] == t]
        sub.plot(
            ax=ax,
            color=MODE_COLORS.get(t, "#777777"),
            linewidth=0.3 if t == "Road" else 0.55,
            alpha=0.8,
            zorder=1,
        )

    style_map_axis(ax, land, f"{len(nodes):,} nodes  ·  {len(edges):,} edges", title=title)

    # Horizontal legend BELOW the map (collapse the two ice classes), so it
    # never sits on top of the geography.
    seen: list[str] = []
    handles = []
    for t in present:
        label = "IceRoad" if t in ("IceRoad", "IceRoadConnector") else t
        if label in seen:
            continue
        seen.append(label)
        handles.append(Line2D([0], [0], color=MODE_COLORS.get(t, "#777"), lw=2.0, label=label))
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=len(handles),
        fontsize=7.5,
        frameon=False,
        handlelength=1.4,
        columnspacing=1.1,
        handletextpad=0.5,
    )
    return len(nodes), len(edges)


# --------------------------------------------------------------------------
# Panel C — tank capacity at hubs (size encodes capacity)
# --------------------------------------------------------------------------
def panel_hub_capacity(ax, land, *, title: str | None) -> int:
    nodes = gpd.read_file(NODES_SHP).to_crs(CRS)
    hubs = nodes[nodes["is_hub"] == 1].copy()
    hubs["cap"] = pd.to_numeric(hubs["hub_cap"], errors="coerce").fillna(0.0)
    hubs = hubs[hubs["cap"] > 0]

    draw_land(ax, land)

    # Capacity is shown by point size ALONE. Marker area scales with
    # sqrt(capacity) so it reads as area, not radius.
    cap = hubs["cap"].to_numpy()
    cap_max = cap.max()

    def cap_to_size(c):
        return 8 + 300 * np.sqrt(np.asarray(c) / cap_max)

    ax.scatter(
        hubs.geometry.x,
        hubs.geometry.y,
        s=cap_to_size(cap),
        color="#2c7fb8",
        alpha=0.65,
        edgecolor="white",
        linewidth=0.25,
        zorder=3,
    )

    total_gal = cap.sum()
    style_map_axis(ax, land, f"{len(hubs):,} hubs  ·  {total_gal/1e6:,.0f}M gal total", title=title)

    # Size legend: a few representative capacities, so size reads quantitatively.
    ref_caps = [c for c in (100_000, 1_000_000, 5_000_000) if c <= cap_max]
    handles = [
        Line2D([0], [0], marker="o", linestyle="none",
               markerfacecolor="#2c7fb8", markeredgecolor="white",
               markeredgewidth=0.25, alpha=0.65,
               markersize=np.sqrt(cap_to_size(c)),
               label=f"{c/1e6:g}M gal" if c >= 1e6 else f"{c/1e3:g}k gal")
        for c in ref_caps
    ]
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=len(handles),
        title="Hub capacity",
        fontsize=7.5,
        title_fontsize=8,
        frameon=False,
        labelspacing=1.0,
        handletextpad=0.6,
        columnspacing=1.6,
        borderpad=0.4,
    )
    return len(hubs)


# --------------------------------------------------------------------------
# Panel D — reserved socio-economic / cost context (full-width long box)
# --------------------------------------------------------------------------
def panel_reserved(ax) -> None:
    ax.set_facecolor("#f6f6f4")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor("#bbbbbb")
        spine.set_linewidth(1.0)
        spine.set_linestyle((0, (5, 4)))

    ax.set_title(D_TITLE, fontsize=12, fontweight="bold", pad=6, loc="left", x=0.02)

    # Left: the "? -> $" motif.
    ax.text(0.06, 0.55, "?", fontsize=40, ha="center", va="center",
            color="#9a9a9a", fontweight="bold")
    ax.add_patch(FancyArrowPatch(
        (0.10, 0.55), (0.16, 0.55),
        arrowstyle="-|>", mutation_scale=20, color="#b0b0b0", lw=2.2,
    ))
    ax.text(0.20, 0.55, "$", fontsize=40, ha="center", va="center",
            color="#9a9a9a", fontweight="bold")

    # Middle: the candidate layers as a 2x2 chip grid.
    ax.text(0.30, 0.82, D_LEAD, fontsize=10, ha="left", va="center",
            color=CAPTION_COLOR, fontweight="bold")
    xs = [0.31, 0.31, 0.55, 0.55]
    ys = [0.52, 0.28, 0.52, 0.28]
    for label, x, y in zip(D_CHIPS, xs, ys):
        ax.text(x, y, f"•  {label}", fontsize=10, ha="left", va="center", color=CAPTION_COLOR)

    # Right: the note and the question.
    ax.text(0.80, 0.66, D_NOTE.replace(" — ", " —\n").replace("but", "\nbut"),
            fontsize=9.5, ha="center", va="center", color=CAPTION_COLOR, linespacing=1.5)
    ax.text(0.80, 0.22, D_QUESTION, fontsize=12, ha="center", va="center",
            style="italic", color="#777777")


# --------------------------------------------------------------------------
# Whole-diagram brace + red callout
# --------------------------------------------------------------------------
def _add_brace_and_callout(fig) -> None:
    """Wrap the whole diagram in { } and point a red arrow at it."""
    # Big curly braces hugging the left/right edges of the whole figure.
    brace_kw = dict(fontsize=560, color="#666666", family="serif",
                    va="center", ha="center")
    fig.text(0.008, 0.46, "{", **brace_kw)
    fig.text(0.992, 0.46, "}", **brace_kw)

    # Red callout above the diagram, arrow pointing down into it.
    fig.text(0.5, 1.075, CALLOUT, color=CALLOUT_RED, fontsize=16,
             fontweight="bold", ha="center", va="top")
    arrow = FancyArrowPatch(
        (0.5, 1.045), (0.5, 0.965),
        transform=fig.transFigure, color=CALLOUT_RED,
        arrowstyle="-|>", mutation_scale=34, lw=3.2,
    )
    fig.add_artist(arrow)


# --------------------------------------------------------------------------
# Combined figure (the PNG)
# --------------------------------------------------------------------------
def build_combined_png(land) -> dict:
    fig = plt.figure(figsize=(19, 10.5))
    gs = fig.add_gridspec(2, 3, height_ratios=[3.2, 1.0], hspace=0.30, wspace=0.10)
    axA = fig.add_subplot(gs[0, 0])
    axB = fig.add_subplot(gs[0, 1])
    axC = fig.add_subplot(gs[0, 2])
    axD = fig.add_subplot(gs[1, :])

    stats = {}
    stats["facilities"] = panel_facilities(axA, land, title=PANEL_TITLES["A"])
    stats["nodes"], stats["edges"] = panel_network(axB, land, title=PANEL_TITLES["B"])
    stats["hubs"] = panel_hub_capacity(axC, land, title=PANEL_TITLES["C"])
    panel_reserved(axD)

    _add_brace_and_callout(fig)

    fig.savefig(OUT_PNG, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return stats


# --------------------------------------------------------------------------
# Standalone panel exports (for the editable deck)
# --------------------------------------------------------------------------
def build_panel_pngs(land) -> dict[str, Path]:
    """Render A/B/C each to its own PNG with NO title (title is native in the
    deck). Identical figure size => identical aspect => clean alignment."""
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    specs = [
        ("A", lambda ax: panel_facilities(ax, land, title=None)),
        ("B", lambda ax: panel_network(ax, land, title=None)),
        ("C", lambda ax: panel_hub_capacity(ax, land, title=None)),
    ]
    for key, draw in specs:
        fig = plt.figure(figsize=(5.6, 5.2))
        ax = fig.add_axes((0.02, 0.16, 0.96, 0.80))
        draw(ax)
        out = PANEL_DIR / f"panel_{key}.png"
        fig.savefig(out, dpi=200, facecolor="white")
        plt.close(fig)
        paths[key] = out
    return paths


# --------------------------------------------------------------------------
# Editable deck (.pptx -> Google Slides)
# --------------------------------------------------------------------------
def build_pptx(panel_paths: dict[str, Path]) -> None:
    from PIL import Image
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Emu, Inches, Pt

    GREY = RGBColor(0x55, 0x55, 0x55)
    DARKGREY = RGBColor(0x33, 0x33, 0x33)
    LIGHTGREY = RGBColor(0x9A, 0x9A, 0x9A)
    BOXFILL = RGBColor(0xF6, 0xF6, 0xF4)
    BOXLINE = RGBColor(0xBB, 0xBB, 0xBB)

    RED = RGBColor(0xD6, 0x27, 0x28)
    BRACE = RGBColor(0x66, 0x66, 0x66)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank

    sw = prs.slide_width
    sh = prs.slide_height

    def textbox(left, top, width, height, text, *, size, bold=False,
                italic=False, color=GREY, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.TOP):
        tb = slide.shapes.add_textbox(left, top, width, height)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = Pt(2)
        tf.margin_top = tf.margin_bottom = Pt(1)
        p = tf.paragraphs[0]
        p.alignment = align
        r = p.add_run()
        r.text = text
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
        return tb

    # --- Red callout (native, editable) pointing at the whole diagram ------
    textbox(Inches(1.0), Inches(0.08), int(sw - Inches(2.0)), Inches(0.6),
            CALLOUT.replace("\n", " "), size=16, bold=True, color=RED,
            align=PP_ALIGN.CENTER)
    down = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW,
                                  int(sw / 2 - Inches(0.28)), Inches(0.7),
                                  Inches(0.56), Inches(0.34))
    down.fill.solid()
    down.fill.fore_color.rgb = RED
    down.line.fill.background()
    down.shadow.inherit = False

    # --- Top row: three panel images + native titles -----------------------
    margin = Inches(0.35)
    gap = Inches(0.2)
    img_w = int((sw - 2 * margin - 2 * gap) / 3)
    title_top = Inches(1.12)
    title_h = Inches(0.38)
    img_top = Inches(1.55)

    for i, key in enumerate(["A", "B", "C"]):
        left = int(margin + i * (img_w + gap))
        with Image.open(panel_paths[key]) as im:
            iw, ih = im.size
        img_h = int(img_w * ih / iw)
        textbox(left, title_top, img_w, title_h, PANEL_TITLES[key],
                size=16, bold=True, color=DARKGREY)
        slide.shapes.add_picture(str(panel_paths[key]), left, img_top,
                                 width=img_w, height=img_h)

    # --- Bottom: the editable D box ----------------------------------------
    box_left = margin
    box_top = Inches(5.45)
    box_w = int(sw - 2 * margin)
    box_h = Inches(1.7)

    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 box_left, box_top, box_w, box_h)
    box.fill.solid()
    box.fill.fore_color.rgb = BOXFILL
    box.line.color.rgb = BOXLINE
    box.line.width = Pt(1.25)
    box.line.dash_style = 2  # dashed
    box.shadow.inherit = False
    # Drop the default centered placeholder text.
    box.text_frame.paragraphs[0].text = ""

    # D title (native, editable), top-left of the box.
    textbox(box_left + Inches(0.15), box_top + Inches(0.05),
            box_w - Inches(0.3), Inches(0.35), D_TITLE,
            size=14, bold=True, color=DARKGREY, align=PP_ALIGN.LEFT)

    # "?  ->  $" motif on the left.
    textbox(box_left + Inches(0.2), box_top + Inches(0.55),
            Inches(2.4), Inches(0.9), "?    →    $",
            size=40, bold=True, color=LIGHTGREY, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)

    # Middle: lead + bullet chips (native, editable text — fill in later).
    mid_left = box_left + Inches(2.9)
    textbox(mid_left, box_top + Inches(0.45), Inches(5.6), Inches(0.3),
            D_LEAD, size=11, bold=True, color=GREY, align=PP_ALIGN.LEFT)
    chips_box = slide.shapes.add_textbox(mid_left, box_top + Inches(0.75),
                                         Inches(5.8), Inches(0.85))
    ctf = chips_box.text_frame
    ctf.word_wrap = True
    for j, chip in enumerate(D_CHIPS):
        p = ctf.paragraphs[0] if j == 0 else ctf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = f"•  {chip}"
        r.font.size = Pt(11)
        r.font.color.rgb = GREY

    # Right: the note + the question (native, editable).
    right_left = box_left + box_w - Inches(3.9)
    textbox(right_left, box_top + Inches(0.5), Inches(3.7), Inches(0.7),
            D_NOTE, size=10, color=GREY, align=PP_ALIGN.CENTER)
    textbox(right_left, box_top + Inches(1.2), Inches(3.7), Inches(0.4),
            D_QUESTION, size=13, italic=True, color=RGBColor(0x77, 0x77, 0x77),
            align=PP_ALIGN.CENTER)

    # --- Braces wrapping the whole diagram ---------------------------------
    brace_top = title_top
    brace_h = int(box_top + box_h - brace_top)
    for shape_type, x in ((MSO_SHAPE.LEFT_BRACE, Inches(0.02)),
                          (MSO_SHAPE.RIGHT_BRACE, int(sw - Inches(0.32)))):
        br = slide.shapes.add_shape(shape_type, x, brace_top, Inches(0.3), brace_h)
        br.fill.background()
        br.line.color.rgb = BRACE
        br.line.width = Pt(2.0)
        br.shadow.inherit = False

    prs.save(str(OUT_PPTX))


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "figure.dpi": 150,
        "savefig.dpi": 300,
    })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    land = load_land()

    stats = build_combined_png(land)
    panel_paths = build_panel_pngs(land)
    build_pptx(panel_paths)

    print(f"wrote {OUT_PNG}")
    print(f"wrote {panel_paths['A']}, panel_B.png, panel_C.png")
    print(f"wrote {OUT_PPTX}  (upload to Google Slides: File > Import slides)")
    print(f"  A facilities={stats['facilities']:,}  "
          f"B nodes={stats['nodes']:,} edges={stats['edges']:,}  "
          f"C hubs={stats['hubs']:,}")


if __name__ == "__main__":
    main()
