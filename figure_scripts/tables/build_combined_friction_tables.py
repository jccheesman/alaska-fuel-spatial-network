"""Build outputs/tables/combined_friction_tables.xlsx — publication-style tables
of the friction parameters and the per-mode cost model. It replaces the
hand-exported friction_config.xlsx (retired 2026-10): every value is read from
friction_config.py / friction_costs.py, so the workbook cannot drift from the
model. Run it again after changing either module.

  Table 1 (sheet 'Table 1'), panels side by side to save vertical space:
    (a) Land-cover friction        (left block)
    (b) Permafrost zonal modifier  (right block, top)
    (c) Slope friction reclass     (right block, below (b))

  Table 2 (sheet 'Table 2'), stacked panels:
    (a) Ice & water constants      (was 'Ice & Water',   Table 6)
    (b) Friction-surface equations (was 'Equations',     Table 10)

  Table 3 (sheet 'Table 3'), stacked panels:
    (a) Per-mode delivery cost rates ($/gallon-mile)
    (b) Intermodal transfer fees ($/gallon)
    (c) Sources, read from docs/cost_derivation/2026-11/SOURCES.md
  Values mirror friction_surface/friction_costs.py (the 2026-11 re-derivation:
  ocean and river barge rates, barge landing fees by place type, each with its
  evidence status; supersedes the 2026-07-17 rate set).

Every Table 1 panel is three columns wide: land cover fills the left block,
permafrost and slope stack in the right block (separated by a spacer column),
with the notes below the panels. Styling mirrors build_input_datasets_xlsx.py (12 pt bold title,
double-border header row, thin bottom rule, wrapped top-aligned text).

Publication cleanup vs. the source sheets: internal changelog notes and
calibration-bug narration are stripped, leaving only the scientific rationale
and data sources. Numeric friction/multiplier values are shown to two
decimals.
"""


from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side

# Single source of truth: every friction value comes from friction_config.py and
# every rate and fee from friction_costs.py, so this workbook can never drift.
from friction_surface import friction_config as fc
from friction_surface.friction_costs import (
    BASELINE_RATE_RANGES as RANGES,
    BASELINE_RATES_PER_GALLON_MILE as RATES,
    INTERMODAL_TRANSFER_FEES as FEES,
    LANDING_CLASS_FEES as LANDING,
    RATE_STATUS,
    TRANSFER_TYPE_TO_MODES,
)
from fuel_network.load import EXPECTED   # edge-type counts of the network-of-record


def _rate(mode_key: str, prec: int) -> str:
    """Per-mile rate string from friction_costs.py (prec preserves display)."""
    return f"{RATES[mode_key]:.{prec}f}"


def _fee(a: str, b: str) -> str:
    """Transfer-fee total string from friction_costs.py."""
    return "%g" % FEES[(a, b)]["total"]


def _n_edges(a: str, b: str) -> str:
    """How many network-of-record transfer edges a fee prices (either direction)."""
    n = sum(EXPECTED["edge_types"].get(t, 0)
            for t, pair in TRANSFER_TYPE_TO_MODES.items() if set(pair) == {a, b})
    return f"{n:,}"


def _range(mode_key: str) -> str:
    lo, hi = RANGES[mode_key]
    return f"{lo:g}–{hi:g}"


def _status(mode_key: str) -> str:
    return RATE_STATUS[mode_key].capitalize()


def _landing(key: str) -> str:
    return "%g" % LANDING[key]["total"]


def _landing_range(key: str) -> str:
    lo, hi = LANDING[key]["range"]
    return f"{lo:g}–{hi:g}"


# Where the derivation record lives (the 2026-11 re-derivation). The earlier chapters it
# corrects are in the private harness repository and in this repo's git history (b35b730).
DERIVATIONS = "docs/cost_derivation/2026-11/"
SOURCES_MD = "docs/cost_derivation/2026-11/SOURCES.md"
NOT_REDISTRIBUTED = "third-party PDF, not redistributed with the repo"


import repo_paths as rp  # noqa: E402
OUT = rp.TABLES / "combined_friction_tables.xlsx"

# --- house style (matches build_input_datasets_xlsx.py) -----------------------
TITLE_FONT = Font(size=12, bold=True)
SUBTITLE_FONT = Font(size=10, italic=True)
SECTION_FONT = Font(size=11, bold=True)
HEADER_FONT = Font(size=11, bold=True)
BODY_FONT = Font(size=10)
NOTE_FONT = Font(size=8, italic=True)

DOUBLE = Side(style="double")
THIN = Side(style="thin")
HEADER_BORDER = Border(top=DOUBLE, bottom=DOUBLE)
LAST_ROW_BORDER = Border(bottom=THIN)

LEFT_TOP_WRAP = Alignment(horizontal="left", vertical="top", wrap_text=True)
LEFT_CENTER_WRAP = Alignment(horizontal="left", vertical="center", wrap_text=True)

# Table 1: land cover (A:C) | spacer (D) | permafrost, then slope (E:G).
T1_COL_WIDTHS = {"A": 7, "B": 20, "C": 10, "D": 3, "E": 21, "F": 14, "G": 11}
T1_NCOLS = 7
LULC_SPANS = [(1, 1), (2, 2), (3, 3)]
PERMAFROST_SPANS = [(5, 5), (6, 6), (7, 7)]
SLOPE_SPANS = PERMAFROST_SPANS

# Table 2: four columns, equations panel merges B:C for the formula.
T2_COL_WIDTHS = {"A": 22, "B": 22, "C": 20, "D": 52}
T2_NCOLS = 4
SPANS_4 = [(1, 1), (2, 2), (3, 3), (4, 4)]    # A | B | C | D      (constants)
SPANS_EQ = [(1, 1), (2, 3), (4, 4)]           # A | B:C | D        (equations)

# --- panel content (publication-cleaned) --------------------------------------
LULC_HEADERS = ("Class", "Class name", "Friction")
LULC_CLASS_NAMES = {0: "water", 1: "trees", 2: "grass", 3: "flooded_vegetation",
                    4: "crops", 5: "shrub_scrub", 6: "built_area", 7: "bare_ground",
                    8: "snow_ice"}   # Dynamic World v1 labels
LULC_ROWS = [
    (str(code), LULC_CLASS_NAMES[code], "NoData" if f is None else f"{f:.2f}")
    for code, f in sorted(fc.LULC_FRICTION.items())
]
LULC_NOTE = (
    "(a) LULC friction applies only to off-network (off-road) pixels; "
    "on-network edges use ROAD_FRICTION × slope × permafrost. Values represent "
    "light-vehicle / ATV / snowmachine mobility as a continuous friction across "
    "classes. Water (class 0) is NoData in overland mode. Source: Dynamic World "
    "v1 (Brown et al. 2022)."
)

PERMAFROST_HEADERS = ("Zone (IPA convention)", "Extent fraction p", "Multiplier")
_PF_EDGES = (0.0, *fc.PERMAFROST_ZONE_BREAKS, 1.0)
PERMAFROST_ROWS = [
    (label, f"[{lo:.2f}, {hi:.2f}{']' if i == 3 else ')'}", f"{m:.2f}")
    for i, (label, lo, hi, m) in enumerate(zip(
        ("none / isolated", "sporadic", "discontinuous", "continuous"),
        _PF_EDGES[:-1], _PF_EDGES[1:], fc.PERMAFROST_ZONE_MULTIPLIERS))
]
PERMAFROST_NOTE = (
    "(b) Applied year-round. Zone breaks ("
    + ", ".join(f"{x:.2f}" for x in fc.PERMAFROST_ZONE_BREAKS) + ") and the four-zone "
    "naming follow the IPA convention (Brown et al. 1997, Circum-Arctic Map of "
    "Permafrost). Per-pixel near-surface (≤1 m) permafrost probability from "
    "Pastick et al. 2015 (Remote Sens. Environ. 168, doi:10.1016/j.rse.2015.07.019). "
    "Bin labels describe the probability range at the pixel, not IPA-polygon "
    "membership."
)

_S1, _S2 = fc.SLOPE_THRESHOLDS
SLOPE_HEADERS = ("Class", "Slope range (°)", "Friction")
SLOPE_ROWS = [
    (label, rng, f"{f:.2f}")
    for label, rng, f in zip(("flat", "rolling", "mountain"),
                             (f"< {_S1:g}", f"{_S1:g} to < {_S2:g}", f"≥ {_S2:g}"),
                             fc.SLOPE_FRICTION)
]
SLOPE_NOTE = (
    f"(c) Terrain slope from FABDEM V1, reclassified at {_S1:g}° / {_S2:g}° "
    "(≈ 3.5% / 14% grade), in line with the AASHTO Green Book level / rolling / "
    "mountainous classes. Checked against AKDOT HPMS 2024 road grades: the "
    "length-weighted mean grade is 4.29% (≈ 2.5°), at the flat/rolling boundary, "
    "and only 1.0% of mileage exceeds 15% grade, so no separate severe class. "
    "Applies to every land pixel; on roads it enters as max(ROAD_FRICTION, f_slope)."
)

ICE_HEADERS = ("Constant", "Value", "Units", "Rationale / source")
ICE_ROWS = [
    ("SEA_ICE_THRESHOLD", f"{fc.SEA_ICE_THRESHOLD:.2f}", "fraction [0, 1]",
     "NSIDC ice-edge definition; POLARIS limit for unreinforced barges."),
    ("RIVER_ICE_THRESHOLD", f"{fc.RIVER_ICE_THRESHOLD:.2f}", "fraction [0, 1]",
     "Conservative operational threshold, consistent with the sea-ice value; "
     "matches Yukon / Kuskokwim practice of sailing only after breakup."),
    ("WATER_FRICTION_BARGE", f"{fc.WATER_FRICTION_BARGE:.2f}", "unitless",
     "Ice-free open-water baseline; shares the reference-pixel baseline of "
     "ROAD_FRICTION. Cross-mode cost differentiation is carried separately by "
     "the per-mode $/gallon-mile rates."),
    ("ROAD_FRICTION", f"{fc.ROAD_FRICTION:.2f}", "unitless",
     "Highway-grade on-road friction, combined as "
     "max(ROAD_FRICTION, f_slope) × permafrost."),
    ("ROAD_BRIDGE_FRICTION", f"{fc.ROAD_BRIDGE_FRICTION:.2f}", "unitless",
     "Highway-grade friction at bridges; slope and permafrost are skipped "
     "(engineered crossings)."),
    ("ICEROAD_TIME_PENALTY", f"{fc.ICEROAD_TIME_PENALTY:.2f}", "× highway",
     "Loaded ice-road ≈ 25 mph vs. ≈ 50 mph highway baseline "
     "(UAF/INE 2023, Table 8.1)."),
    ("CORRIDOR_BUFFER_M", f"{fc.CORRIDOR_BUFFER_M:g}", "m",
     f"Half-pixel buffer on corridor centerlines (road, ice road, waterway) for "
     f"{fc.TARGET_RESOLUTION} m grid connectivity."),
]
ICE_NOTE = None

EQ_HEADERS = ("Step", "Formula", "Where applied")
EQ_ROWS = [
    ("1a. Slope reclass",
     f"f_slope = {fc.SLOPE_FRICTION[0]:.2f} (slope < {_S1:g}°); "
     f"{fc.SLOPE_FRICTION[1]:.2f} ({_S1:g} ≤ slope < {_S2:g}°); "
     f"{fc.SLOPE_FRICTION[2]:.2f} (slope ≥ {_S2:g}°)",
     "Every land pixel"),
    ("1b. LULC reclass",
     "f_lulc = LULC_FRICTION[class]   (class 0 water → NoData)",
     "Every land pixel"),
    ("2a. Permafrost normalize",
     "p = p_src / 100 if max(p_src) > 1, else p_src; clip to [0, 1]",
     "Permafrost source (once)"),
    ("2b. Permafrost modifier",
     "pm = " + " / ".join(f"{m:.2f}" for m in fc.PERMAFROST_ZONE_MULTIPLIERS)
     + " for p in " + " / ".join(r[1] for r in PERMAFROST_ROWS),
     "Every land pixel (year-round)"),
    ("3a. Ice normalize",
     "ice = ice_src / 100 if max(ice_src) > 1, else ice_src",
     "Each ice raster (×12 per type)"),
    ("3b. Ice present",
     f"sea_ice_present = sea_ice > {fc.SEA_ICE_THRESHOLD:.2f}; "
     f"river_ice_present = river_ice > {fc.RIVER_ICE_THRESHOLD:.2f}",
     "Per month"),
    ("4a. Static base",
     "static_base = f_slope × f_lulc; NoData on water pixels",
     "Every pixel (once); off-network base for the monthly overland stack "
     "(step 5a)"),
    ("4b. Road base",
     "road_base = max(ROAD_FRICTION, f_slope) × pm; no LULC, no water mask; "
     "NoData-free",
     "Every pixel (once); standalone static raster (road_base.tif) sampled "
     "along network road edges"),
    ("5a. Overland: base",
     "out = static_base × pm",
     "Land + valid LULC, all months"),
    ("5b. Overland: roads",
     "out = max(ROAD_FRICTION, f_slope) × pm",
     "Road ∧ land, all months"),
    ("5c. Overland: bridges",
     f"out = ROAD_BRIDGE_FRICTION = {fc.ROAD_BRIDGE_FRICTION:.2f}",
     "Road ∧ water, all months"),
    ("5d. Overland: ice-road",
     f"out = max(ROAD_FRICTION, f_slope) × {fc.ICEROAD_TIME_PENALTY:.2f} × pm",
     "Ice-road ∧ land, Jan–Mar (LULC dropped)"),
    ("6a. Barge: navigable",
     "navigable = water ∧ ¬sea_ice_present ∧ ¬river_ice_present",
     "Per month"),
    ("6b. Barge: friction",
     f"out = {fc.WATER_FRICTION_BARGE:.2f} on navigable; NoData elsewhere",
     "Per month"),
]
EQ_NOTE = (
    "Steps are applied in sequence within the overland branch; later steps "
    "overwrite the value at their target pixels. Static base (4a) and road "
    "base (4b) are distinct products: static base carries land cover and is "
    "NoData on water, seeding the monthly overland rasters; road base drops "
    "land cover (roads through forest would otherwise read as impassable) "
    "and is NoData-free, emitted once per run as road_base.tif for "
    "network-edge sampling."
)

# Table 3: mode costs. Panel (a) four columns; panel (b) merges C:D for notes.
T3_COL_WIDTHS = {"A": 22, "B": 13, "C": 17, "D": 64}
T3_NCOLS = 4

RATE_HEADERS = ("Mode", "Rate ($/gal-mi)", "Season (model)", "Derivation / source")
RATE_ROWS = [
    ("Road", _rate("Road", 4), "Year-round",
     f"Status: {_status('Road')}. Range {_range('Road')}. Highway-tanker carriage incl. empty "
     "backhaul. Three methods of different kinds agree within 1.25×: Econ One "
     "Valdez–Fairbanks truck leg ($0.20/gal over ~364 mi, 2016$) = 0.00076 [S04]; "
     "ATRI tank-carrier build-up = 0.00085 [S13]; State heating-oil contract "
     "gradient = 0.00068 [S35, not re-opened in 2026-11]. Confirmed, unchanged."),
    ("Barge, ocean line-haul", _rate("Barge", 5), "Ice-free months (monthly ice gating)",
     f"Status: {_status('Barge')}. Range {_range('Barge')}. Transportation only, no fixed "
     "part; applies to MARINE waterway edges (edge_water_class). Two published "
     "charges agree within 1%: ISER 2010 charged rate $0.19–0.22/gal over the "
     "1,527-mile mean model distance = 0.000205 [S02]; Econ One 2016 25 cpg over "
     "~1,669 mi = 0.000207 [S04]; a weak third, the lightering guide's tanker "
     "range = 0.00013 [S05]. Replaces the blended 0.0010, which routed Nome's fuel "
     "by river."),
    ("Barge, river", _rate("BargeRiver", 4), "Ice-free months (monthly ice gating)",
     f"Status: {_status('BargeRiver')}. Range {_range('BargeRiver')}. Per CHANNEL mile, carriage "
     "only; applies to RIVER waterway edges; its fixed part is the river-village "
     "landing fee in panel (b). The total for a 164-mile haul agrees across three "
     "methods (1.8×): State contracts [S01], DEC 2007 invoice rate [S03], ISER 2010 "
     "build [S02]; the per-mile part does not (0.0044 / 0.0011 / 0.0014, 3.9×). "
     "The earlier 0.011 river figure is overturned (a per-map-mile average at "
     "~100 miles, not a marginal rate)."),
    ("Plane", _rate("Plane", 3), "Year-round",
     f"Status: {_status('Plane')}. Range {_range('Plane')}. Per one-way statute air mile, "
     "no fixed part. Two verified independent methods agree within 1.4×: published "
     "statements, DEC 2007 and ISER 2010 = 0.0190 [S03, S02]; the November 2007 "
     "Fairbanks–Allakaket delivery = 0.0136 [S01]. Lowered from 0.025, which "
     "implied $4.54/gal to Allakaket against a FY2025 ceiling of $3.48–3.70 [S15]. "
     "General-freight tariffs are a ceiling only [S16, S17]. Small aircraft "
     "(150–200 gal) cost 0.05–0.11 and are not represented."),
    ("Ice road", _rate("IceRoad", 3), "Winter (Jan–Mar)",
     f"Status: {_status('IceRoad')}. Range {_range('IceRoad')}. Kept: no tariff, contract or "
     "invoice for an Alaska winter fuel haul exists. Two regimes ~3.8× apart: "
     "truck on an ice road ≈ 0.007 (build-up) [S13]; snow tractor and sled ≈ 0.026 "
     "(Noatak request build-up [S24]; Atqasuk price difference [S15]; gravel-haul "
     "check [S25]). One statewide rate by owner decision."),
]
RATE_NOTE = (
    "(a) Rates in USD per gallon-mile, 2026$ at CPI-U 332.243, mirroring "
    "friction_costs.py; re-derived 2026-11-17/18 from owner-supplied documents: "
    "blind derivations, then one adversarial verifier per rate "
    f"({DERIVATIONS}; one addendum per rate with a derived-versus-assumed table "
    "for every input). Status: Derived = three or more independent methods "
    "within ~3×, inputs checked in the documents; Provisional = best estimate on "
    "evidence that falls short, carried with a wide range; Assumed = no source "
    "evidence, earlier value kept. Bracketed IDs refer to panel (c). Rates are "
    "operational costs kept strictly separate from the environmental friction "
    "surface (baseline 1.0); seasonal availability is enforced by the friction "
    "rasters and edge-month weights, not by the rates."
)

FEE_HEADERS = ("Transfer (from ↔ to)", "Fee ($/gal)", "What it counts / note")
FEE_SPANS = [(1, 1), (2, 2), (3, 4)]
FEE_ROWS = [
    ("barge landing: road-system port", _landing("road_port"),
     f"Provisional. Range {_landing_range('road_port')}. Loading at a road-system port: "
     "wharfage 20.49¢/bbl + valve-yard transfer 6.08¢/bbl + modernization surcharge "
     "$0.14/bbl, Port of Alaska Tariff 10.2 [S09]. Class rule: the landing is on "
     "the Anchorage road system."),
    ("barge landing: hub or dock-served port", _landing("hub"),
     f"Provisional. Range {_landing_range('hub')}. Line-haul discharge at the distributor's own "
     "terminal: Bethel wharfage $0.06 + fuel transfer $0.06 [S07]; Nome inbound "
     "wharfage $0.05 [S08]; ISER 2010 shore labour [S02]. Class rule: the place is "
     "listed in inputs/network_qc/landing_classes.csv."),
    ("barge landing: coastal village", _landing("coastal_village"),
     f"Provisional, ASSEMBLED. Range {_landing_range('coastal_village')}. Small-barge delivery "
     "incl. discharge to the village header. Derived form $0.45 per delivery + "
     "0.0010 per sailing mile [S02, S15, S03]; the network has no edge for the "
     "sailing leg, so it is carried flat: 0.45 + 0.0010 × ~250 mi − the ocean "
     "line-haul already paid over those miles ≈ 0.65. Class rule: mostly marine "
     "water at the landing."),
    ("barge landing: river village", _landing("river_village"),
     f"Provisional. Range {_landing_range('river_village')}. The river fixed part per delivery, "
     "incl. discharge [S01, S03, S02]. Class rule: mostly river water at the "
     "landing."),
    ("barge ↔ overland (fallback)", _fee("barge", "overland"),
     "Provisional. Used only where a landing has no class. Single-key value: "
     "gallon-mix average of the classes, per crossing. "
     f"The four landing classes price the {_n_edges('barge', 'overland')} "
     "BargeRoadTransfer + BargeAirTransfer edges. Was 0.24 at every crossing "
     "(a truck-rack list price [S12], billed at both ends of a barge route)."),
    ("plane ↔ overland", _fee("plane", "overland"),
     "Assumed, unchanged: no source prices this event. Road-side tarmac "
     "receiving labor + fittings. "
     f"Prices {_n_edges('plane', 'overland')} edges."),
    ("overland ↔ ice road", _fee("overland", "ice_road"),
     "Assumed, unchanged: no source prices this event. Road-carriage side of a "
     "truck↔ice-road-truck pumped changeover. "
     f"Prices {_n_edges('overland', 'ice_road')} edges."),
    ("barge ↔ ice road", _fee("barge", "ice_road"),
     "Assumed, unchanged. Thin facility-interface residual. "
     f"Prices {_n_edges('barge', 'ice_road')} edges, expected never to be "
     "traversed: ice roads run Jan–Mar, barges only in the ice-free window. "
     "Completeness only."),
]
FEE_NOTE = (
    "(b) Fees in USD per gallon per crossing, 2026$ (tariff figures are 2026 "
    f"actuals), re-derived 2026-11 ({DERIVATIONS}addendum_transfer_fees.md and "
    "the barge addenda). A barge-to-land crossing is priced by the kind of place "
    "the barge lands at (fuel_network.landings; the class used for each edge is "
    "the edge_landing_class table). Rules that prevent double counting: no "
    "separate village fee where a delivery charge applies; hub discharge is "
    "billed once; the ocean rate carries no fixed part. Total path cost ($/gal) "
    "= Σ(rate × miles × friction) + the fee at every modal handoff."
)

# Panel (c): full citations for every source behind the rates and the fees.
SOURCE_HEADERS = ("Source", "Full citation + link / locator")
SOURCE_SPANS = [(1, 1), (2, 4)]           # A | B:D
def _load_sources() -> list[tuple[str, str]]:
    """(ID, citation + file + link) rows parsed from the tracked sources register."""
    import re
    rows = []
    for line in (rp.ROOT / SOURCES_MD).read_text().splitlines():
        if not re.match(r"^\| S\d\d \|", line):
            continue
        sid, doc, pub, link, _cited = [c.strip() for c in line.strip().strip("|").split("|")]
        title, _, fname = doc.partition("<br>")
        link = re.sub(r"<br>", " ", link).replace("<", "").replace(">", "")
        fname = fname.replace("`", "")
        where = (fname if fname.startswith("(") else
                 f"{fname} ({NOT_REDISTRIBUTED}; held in the private harness repository)")
        rows.append((sid, f"{title}. {pub}.\nFile: {where}\nLink: {link}"))
    return rows


SOURCE_ROWS = _load_sources()
SOURCE_LINKS: dict[str, str] = {}      # links are inside each row since the 2026-11 register
SOURCE_NOTE = (
    f"(c) The sources register of the 2026-11 re-derivation, read from {SOURCES_MD} "
    "(which also lists the addenda that cite each source). Third-party documents "
    "are not redistributed with this repository. Link basis is given for each "
    "link: printed in the document, from the project's notes, or from a web "
    "search result; no link was opened from the analysis session. Agreement "
    "between independent methods, not any single source, is the evidence "
    f"standard; per-figure page cites are in the addenda ({DERIVATIONS})."
)


def _char_width(span: tuple[int, int], widths: dict[str, float]) -> float:
    """Total Excel char-width of a (possibly merged) column span."""
    letters = [chr(ord("A") + c - 1) for c in range(span[0], span[1] + 1)]
    return sum(widths[l] for l in letters)


def _bump_row_height(ws, row: int, cells: list[tuple[str, tuple[int, int]]],
                     widths: dict[str, float]) -> None:
    """Size a row to fit the tallest wrapped cell (merged cells don't auto-fit).

    Only ever grows the row, so side-by-side panels sharing a row can each
    call this without shrinking the other's fit.
    """
    max_lines = 1
    for text, span in cells:
        if not text:
            continue
        width = _char_width(span, widths)
        # ~1.05 fudge for proportional font; +1 line per explicit break.
        est = max(1, int(len(str(text)) / max(width - 2, 1) * 1.05) + 1)
        max_lines = max(max_lines, est)
    height = 12.5 * max_lines + 3
    existing = ws.row_dimensions[row].height
    if existing is None or height > existing:
        ws.row_dimensions[row].height = height


def write_panel(ws, start_row, panel_title, headers, rows, spans, widths):
    """Write one labeled sub-panel into the column block covered by *spans*.

    Returns the row index of the last data row (the thin-rule row).
    """
    block_start = min(cs for cs, _ in spans)
    block_end = max(ce for _, ce in spans)

    # Panel title (merged across the panel's own column block).
    t = ws.cell(start_row, block_start, panel_title)
    t.font = SECTION_FONT
    t.alignment = LEFT_TOP_WRAP
    ws.merge_cells(start_row=start_row, end_row=start_row,
                   start_column=block_start, end_column=block_end)
    _bump_row_height(ws, start_row, [(panel_title, (block_start, block_end))],
                     widths)

    # Header row.
    hr = start_row + 1
    for (cs, ce), head in zip(spans, headers):
        c = ws.cell(hr, cs, head)
        c.font = HEADER_FONT
        c.alignment = LEFT_TOP_WRAP
        if cs != ce:
            ws.merge_cells(start_row=hr, end_row=hr, start_column=cs, end_column=ce)
    for col in range(block_start, block_end + 1):
        ws.cell(hr, col).border = HEADER_BORDER
    _bump_row_height(ws, hr, list(zip(headers, spans)), widths)

    # Data rows.
    for i, row_vals in enumerate(rows):
        rr = hr + 1 + i
        for (cs, ce), val in zip(spans, row_vals):
            c = ws.cell(rr, cs, val)
            c.font = BODY_FONT
            c.alignment = LEFT_TOP_WRAP
            if cs != ce:
                ws.merge_cells(start_row=rr, end_row=rr,
                               start_column=cs, end_column=ce)
        _bump_row_height(ws, rr, list(zip(row_vals, spans)), widths)

    # Thin rule under the last data row, across the panel's block.
    last = hr + len(rows)
    for col in range(block_start, block_end + 1):
        ws.cell(last, col).border = LAST_ROW_BORDER

    return last


def write_note(ws, row, note, ncols, widths):
    """Full-width table note; returns the next free row index."""
    n = ws.cell(row, 1, note)
    n.font = NOTE_FONT
    n.alignment = LEFT_TOP_WRAP
    ws.merge_cells(start_row=row, end_row=row, start_column=1, end_column=ncols)
    _bump_row_height(ws, row, [(note, (1, ncols))], widths)
    return row + 1


def write_caption(ws, title, subtitle, ncols, widths):
    """Table title (row 1) and subtitle (row 2), merged full width."""
    t = ws.cell(1, 1, title)
    t.font = TITLE_FONT
    t.alignment = LEFT_CENTER_WRAP
    ws.merge_cells(start_row=1, end_row=1, start_column=1, end_column=ncols)
    sub = ws.cell(2, 1, subtitle)
    sub.font = SUBTITLE_FONT
    sub.alignment = LEFT_TOP_WRAP
    ws.merge_cells(start_row=2, end_row=2, start_column=1, end_column=ncols)
    _bump_row_height(ws, 2, [(subtitle, (1, ncols))], widths)


def _finish_sheet(ws, widths):
    for letter, width in widths.items():
        ws.column_dimensions[letter].width = width
    # Freeze the title/subtitle so the panels scroll under a fixed caption.
    ws.freeze_panes = "A3"
    ws.sheet_view.showGridLines = False


def main() -> None:
    wb = Workbook()

    # --- Table 1: land cover + permafrost, side by side -----------------------
    ws1 = wb.active
    ws1.title = "Table 1"
    write_caption(
        ws1,
        "Table 1.  Land-cover, permafrost and slope friction factors",
        "Off-network land-cover friction, the year-round permafrost zonal "
        "modifier and the terrain-slope reclass. Friction is unitless "
        "(baseline 1.0).",
        T1_NCOLS, T1_COL_WIDTHS,
    )
    lulc_last = write_panel(ws1, 4, "(a)  Land-cover friction (Dynamic World v1)",
                            LULC_HEADERS, LULC_ROWS, LULC_SPANS, T1_COL_WIDTHS)
    pf_last = write_panel(ws1, 4, "(b)  Permafrost zonal modifier (year-round)",
                          PERMAFROST_HEADERS, PERMAFROST_ROWS, PERMAFROST_SPANS,
                          T1_COL_WIDTHS)
    slope_last = write_panel(ws1, pf_last + 2, "(c)  Slope friction reclass",
                             SLOPE_HEADERS, SLOPE_ROWS, SLOPE_SPANS, T1_COL_WIDTHS)
    r = max(lulc_last, slope_last) + 2
    r = write_note(ws1, r, LULC_NOTE, T1_NCOLS, T1_COL_WIDTHS)
    r = write_note(ws1, r, PERMAFROST_NOTE, T1_NCOLS, T1_COL_WIDTHS)
    write_note(ws1, r, SLOPE_NOTE, T1_NCOLS, T1_COL_WIDTHS)
    _finish_sheet(ws1, T1_COL_WIDTHS)

    # --- Table 2: ice/water constants + equations, stacked --------------------
    ws2 = wb.create_sheet("Table 2")
    write_caption(
        ws2,
        "Table 2.  Ice / water constants and friction-surface equations",
        "Ice and water friction constants, and the sequenced equations used to "
        "build the monthly overland and barge friction stacks.",
        T2_NCOLS, T2_COL_WIDTHS,
    )
    last = write_panel(ws2, 4, "(a)  Ice and water friction constants",
                       ICE_HEADERS, ICE_ROWS, SPANS_4, T2_COL_WIDTHS)
    last = write_panel(ws2, last + 2, "(b)  Friction-surface equations",
                       EQ_HEADERS, EQ_ROWS, SPANS_EQ, T2_COL_WIDTHS)
    write_note(ws2, last + 1, EQ_NOTE, T2_NCOLS, T2_COL_WIDTHS)
    _finish_sheet(ws2, T2_COL_WIDTHS)

    # --- Table 3: mode cost rates + intermodal transfer fees, stacked ---------
    ws3 = wb.create_sheet("Table 3")
    write_caption(
        ws3,
        "Table 3.  Per-mode delivery cost rates and intermodal transfer fees",
        "Operational delivery costs for the multimodal routing layer, kept "
        "separate from the environmental friction surface. Total path cost "
        "($/gal) = Σ(mode rate × miles along route) + transfer fees at each "
        "modal handoff.",
        T3_NCOLS, T3_COL_WIDTHS,
    )
    last = write_panel(ws3, 4, "(a)  Baseline delivery cost rates ($/gallon-mile)",
                       RATE_HEADERS, RATE_ROWS, SPANS_4, T3_COL_WIDTHS)
    r = write_note(ws3, last + 1, RATE_NOTE, T3_NCOLS, T3_COL_WIDTHS)
    last = write_panel(ws3, r + 1, "(b)  Intermodal transfer fees ($/gallon)",
                       FEE_HEADERS, FEE_ROWS, FEE_SPANS, T3_COL_WIDTHS)
    r = write_note(ws3, last + 1, FEE_NOTE, T3_NCOLS, T3_COL_WIDTHS)
    src_rows = [
        (tag, cit + (f"\nLink: {SOURCE_LINKS[tag]}" if SOURCE_LINKS.get(tag) else ""))
        for tag, cit in SOURCE_ROWS
    ]
    last = write_panel(ws3, r + 1, "(c)  Sources (full citations + links)",
                       SOURCE_HEADERS, src_rows, SOURCE_SPANS, T3_COL_WIDTHS)
    write_note(ws3, last + 1, SOURCE_NOTE, T3_NCOLS, T3_COL_WIDTHS)
    _finish_sheet(ws3, T3_COL_WIDTHS)

    wb.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
