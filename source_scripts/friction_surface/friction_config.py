# -*- coding: utf-8 -*-
"""friction_config.py

Constants for the friction-surface and multi-modal-network layers. Path
construction lives in friction_paths.py; cost rates and intermodal fees
live in friction_costs.py.Both layers operate in EPSG:3338 (NAD83 Alaska Albers). 
"""

# Coordinate Reference System
# ---------------------------------------------------------------------------
# The whole project (friction surfaces, network shapefiles, facility
# coordinates for spatial joins, exports) operates in EPSG:3338 - NAD83
# Alaska Albers Equal Area. 

CRS_TARGET = "EPSG:3338"
TARGET_RESOLUTION = 150       # meters
METERS_PER_MILE = 1609.344

# NoData and modes
# ---------------------------------------------------------------------------
FRICTION_NODATA = -9999.0

# Ice roads are burned into the overland surface as a pixel-level seasonal extension (Jan-Mar) — see
# friction_surface.build_mode_friction's overland branch and
# ICE_ROAD_SEASON_MONTHS below. Cost-per-mile differentiation for ice-road
# vs. regular-road segments must be handled downstream of routing via a
# surface_type lookup; the friction surface itself encodes time only.
MODES = ("overland", "barge")

# ---------------------------------------------------------------------------
# Slope friction (degrees -> unitless friction)
# ---------------------------------------------------------------------------
# flat (<2°): 1.0  |  rolling (2-8°): 1.4  |  mountain (>=8°): 1.75
#
# Thresholds at 2° / 8° terrain slope correspond to ~3.5% / ~14% grade.
# Justification against AKDOT HPMS 2024 (607 segments, 2,076 mi mainline)
# is in outputs/analysis/road_grade_distribution.md:
#   - 33.7% of mileage <3% grade, 41.7% 3-5%, 14.1% 5-8%, 10.5% >8%, 1.0% >15%
#   - Network length-weighted mean grade = 4.29% (~2.46°), sitting at the
#     flat/rolling boundary.
#   - "Mountain" class intentionally aggregates 8-15° (Atigun, Thompson)
#     with the rare >15° tail; F-bin (>=15% grade) is only 1.0% of
#     mileage and traversable for loaded fuel tankers, so a separate
#     "severe" class is not warranted.
# Aligned with the AASHTO Green Book topographic classes (level: 0-2%,
# rolling: 3-5%, mountainous: 5-8% typical / >8% severe), recognizing
# the model operates on terrain slope rather than engineered road grade.
SLOPE_THRESHOLDS = (2.0, 8.0)
SLOPE_FRICTION = (1.0, 1.4, 1.75)

# ---------------------------------------------------------------------------
# Land use / land cover (Dynamic World v1 modal class codes)
# ---------------------------------------------------------------------------
# value=None marks NoData in the overland base; mode-specific surfaces
# handle water themselves (barge / ice_road).
LULC_WATER_CLASS = 0
LULC_FRICTION = {
    0: None,    # water -> NoData in overland base
    1: 2.00,    # trees
    2: 1.15,    # grass
    3: 2.50,    # flooded_vegetation
    4: 1.10,    # crops
    5: 1.60,    # shrub_scrub - alder in Alaska
    6: 1.05,    # built_area  
    7: 1.10,    # bare_ground
    8: 5.00,    # snow_ice
}

# ---------------------------------------------------------------------------
# Permafrost zonal modifier (year-round)
# ---------------------------------------------------------------------------
# Per-pixel multiplier looked up by permafrost probability bin, applied
# year-round. Source: Pastick et al. 2015, "Distribution of near-surface
# permafrost in Alaska: Estimates of present and future conditions",
# Remote Sensing of Environment 168, 301-315
# (DOI 10.1016/j.rse.2015.07.019). The raster is a per-pixel probability
# p in [0, 1] of near-surface (<=1 m depth) permafrost presence across
# Alaska, which is a more direct signal for transport-subgrade cost than
# the hemispheric zonal IPA product (Brown et al. 1997).
#
# Rationale: the transport cost of permafrost is engineering-persistent
# (frost heave, thaw settlement, ice-rich subgrade maintenance), not
# seasonal at the day-to-day routing scale. The ice-road burn-in (Jan-Mar)
# and barge sea-ice gating already carry the seasonal signal for overland
# and barge modes respectively; a seasonal permafrost term was double-
# counting that signal with too gentle a magnitude to drive routing.
#
# Bin assignment via np.digitize(p, PERMAFROST_ZONE_BREAKS, right=False):
#   p in [0.00, 0.10)  -> "none / isolated"  -> 1.00
#   p in [0.10, 0.50)  -> "sporadic"         -> 1.15
#   p in [0.50, 0.90)  -> "discontinuous"    -> 1.30
#   p in [0.90, 1.00]  -> "continuous"       -> 1.50
# Bin labels use IPA-convention terminology (Brown et al. 1997's standard
# four-zone scheme) applied to Pastick per-pixel probability — i.e. a
# "discontinuous" pixel here means the probability of permafrost at this
# location is in the 50-90% range, NOT that the pixel falls inside an IPA
# discontinuous-zone polygon. Thresholds match IPA breakpoints so the bin
# labels and multipliers stay comparable to other permafrost-aware
# transport models in the literature.
# The "isolated" probability range (<10%) is folded into "none": at that
# probability the transport-cost premium is negligible and sits within the
# Pastick classifier's uncertainty.
PERMAFROST_ZONE_BREAKS = (0.10, 0.50, 0.90)
PERMAFROST_ZONE_MULTIPLIERS = (1.00, 1.15, 1.30, 1.50)

# ---------------------------------------------------------------------------
# Ice and water friction (per-mode)
# ---------------------------------------------------------------------------
# Both products are 12-month climatological medians of fractional ice
# cover in [0, 1] — sea_ice from the GEE friction-surface script
# (passive-microwave concentration), river_ice from Brown et al. 2026
# (DOI 10.18739/A2SB3X15X) processed by friction_surface/friction_preprocessing/river_ice_full_pipeline.py
# as p_ice = clamp(1 - areaPropMedWater, 0, 1), median across 3 periods
# per reach over 2000-2023. Because they are dimensionally identical
# (fractional ice cover), they share the same conservative-operational
# threshold.
#
# SEA_ICE_THRESHOLD = 0.15 — canonical NSIDC ice-edge threshold
#   (Cavalieri et al. 1984, 1999; Parkinson et al.; NASA Team algorithm),
#   used by NSIDC for Arctic SIE since the 1970s and validated against
#   MODIS/ship observations (Ji et al. 2018). Operational limit for
#   unreinforced (non-ice-class) AK fuel barges — Crowley/Vitus/AML.
#
# RIVER_ICE_THRESHOLD = 0.15 — same conservative-operational stance,
#   given dimensional parity. Rationale
#   from qa_river_ice_thresholds.py against the actual 12 monthly
#   river_ice rasters:
#     - Deep winter and deep summer are saturated (Jan-Apr ~93% of
#       pixels already >0.50; Jul-Sep ~99% <0.05) — threshold choice
#       barely affects those months.
#     - Shoulder months (May, Jun, Oct, Nov) have ~27% of pixel-months
#       in the marginal [0.05, 0.50) range. A 0.5 threshold reads these as
#       navigable; October alone has 29.67% of pixels in [0.15, 0.30) —
#       meaningful ice presence that 0.15 correctly gates.
#     - Relative to a 0.5 threshold, 0.15 blocks 17.66 pp more shoulder-
#       pixel-months (~400k pixels), almost all in October at the freeze-up
#       transition; tightening further to 0.10 adds only 2.73 pp more,
#       below the Brown-product signal-to-noise.

SEA_ICE_THRESHOLD = 0.15
RIVER_ICE_THRESHOLD = 0.15

# Ice-free open-water baseline under barge mode. Set to 1.0 so the
# barge surface has the same "ideal-conditions" baseline as ROAD_FRICTION
# in overland mode — both represent "this is the reference mode-pixel,
# no environmental penalty." Cross-mode cost differentiation lives in
# friction_costs.BASELINE_RATES_PER_GALLON_MILE, not in the friction
# surface. 
WATER_FRICTION_BARGE = 1.0

# Road bridges over water keep highway-grade friction = 1.0. Intentionally
# skips the permafrost modifier — engineered crossings (concrete decks on
# pilings) don't freeze-thaw like tundra and shouldn't carry a seasonal
# penalty. Used by friction_surface.build_mode_friction overland branch
# to burn the road mask back across water pixels that would otherwise be
# NoData (severing the network at every river crossing).
ROAD_BRIDGE_FRICTION = 1.0

# Roads on land: highway-grade friction, applied to every on-road pixel
# (not just bridges over water). Unlike ROAD_BRIDGE_FRICTION, this DOES
# carry the permafrost modifier AND the slope friction — interior AK
# highways genuinely cost more in continuous-permafrost corridors
# and on grade.The burn-in form is max(ROAD_FRICTION, slope_friction) × permafrost_mod,
# so a flat road = 1.0 × pf, a rolling road = 1.4 × pf, a mountain road
# = 1.75 × pf. The LULC class along the road is discarded — a paved
# highway through boreal forest should not inherit the 2.0 trees
# friction value when consumed by sampled-along-edge routing.
ROAD_FRICTION = 1.0

# Ice-road travel-time penalty relative to a paved-highway pixel. Under
# travel-time semantics, friction is proportional to time-per-pixel: 2.0
# means an ice-road pixel takes ~2x as long to traverse as a highway pixel.
# Applied inside the overland mode as a pixel-level burn-in on ice-road
# mask pixels during ICE_ROAD_SEASON_MONTHS (Jan-Mar). Out of season the
# ice-road pixels revert to their underlying terrain cost (off-road tundra,
# effectively impassable), which collapses the ice-road extension and
# leaves the overland network at its year-round road-only topology.
# Derivation:
#   * Loaded ice-road max speed = 15 mph (25 km/h) at minimum ice
#     thickness, 25 mph (35 km/h) at 2x minimum thickness
#     (UAF/INE 2023, "Design and Operation of Ice Roads", Table 8.1,
#     p. 8.3, INE/AIDC 23.01, sponsored by FHWA). The 15 mph limit is a
#     physics constraint: above ~70% of the critical wave speed in the
#     ice cover, deflection becomes asymmetric and the ice cracks.
#     Corroborated by Tibbitt-to-Contwoyto Winter Road (NWT) loaded limit
#     of 25 km/h.
#   * Alaska heavy-truck highway baseline ~50 mph (Dalton 50, Richardson
#     65, capped at 35 mph for >95 ft loads per AK DOT&PF).
#   * 50/25 = 2.0. We use 25 mph (2x-thickness limit) rather than the
#     strict 15 mph floating-ice number because AK ice roads serving
#     Atqasuk/Nuiqsut are overland packed-snow tundra routes
#     (North Slope / NPR-A style), not floating ice over deep water.
# The friction surface intentionally stays environmental-only.
# Manual: https://aidc.uaf.edu/media/1580/ice-road-manual_final.pdf
ICEROAD_TIME_PENALTY = 2.0
CORRIDOR_BUFFER_M = 75.0            # half-pixel buffer on corridor LineStrings (ice_road, road, waterway) for 150 m grid connectivity

# ---------------------------------------------------------------------------
# Freshwater vs. salt water on the waterway network
# ---------------------------------------------------------------------------
# River ice is a RIVER phenomenon. The Brown et al. river-ice product covers
# main-stem Alaskan rivers only, and friction_surface.extend_ice_nearest fills
# its p_ice onto uncovered waterway cells from the nearest covered cell. That
# fill has no business reaching salt water: run unrestricted it hands Chatham
# Strait the ice probability of whatever interior river happens to be nearest,
# which closes the entire marine network Nov-Apr (February: 0 of 501,684
# waterway cells navigable, Gulf/SE included). Ground truth is the opposite —
# Alaska Marine Lines runs year-round twice-weekly to Juneau, Ketchikan,
# Petersburg, Sitka, Haines, Skagway and Wrangell, and Southcentral is
# ice-free year-round. The genuine seasonal window is Bering/Beaufort, and
# that is already handled per-pixel by the sea-ice climatology.
#
# So: a waterway segment is river-ice-gated only if it is a genuine Alaskan
# freshwater watercourse. The NWN's own attributes get close but no single
# column is trustworthy on its own, so the domain is a REVIEWED ALLOWLIST of
# KEY_ID values, with a heuristic kept alongside purely as a drift detector.
#
# Why not a live predicate. Every attribute considered has counterexamples in
# this 320-row table:
#
#   GEO_CLASS == "I"    The NWN files sheltered salt water as "inland": Cook
#                       Inlet, Chatham Strait, Lynn Canal, Prince William
#                       Sound, the whole Inside Passage. 144 marine features
#                       / 108,862 cells carry GEO_CLASS "I".
#   WTWY_TYPE == 6      Carries saltwater Cook Inlet, Norton Sound, Kotzebue
#                       Sound and Bering Sea Access segments; and UGASHIK
#                       RIVER is filed as type 1.
#   RIVERNAME           Misses 451 km of the LOWER YUKON, which is filed
#                       under RIVERNAME "NORTON SOUND" (its LINKNAME is
#                       "YUKON RIVER, AK"). Sea-ice gating that stretch would
#                       leave the lower Yukon open all winter.
#   LINKNAME            Misses CHENA RIVER (FAIRBANKS) and INNOKO RIVER, AK
#                       (JCT YUKON RIVER) under an end-anchored match, and
#                       admits DRIFT RIVER PLATFORMS, AK — a Cook Inlet oil
#                       terminal, not a river.
#
# The table also carries plain spelling noise ("ARCTRIC OCEAN", "KOZEBUL
# SOUND", "METROFANIA BAY" for Mitrofania), which is another reason not to
# trust a string predicate at build time.
#
# The allowlist below is the union heuristic (STATE == "AK" AND RIVER|CREEK
# as a whole word in either RIVERNAME or LINKNAME) after a feature-by-feature
# review of all 28 candidates. Four were rejected — see RIVER_SEGMENT_REJECTED.
# Result: 24 features / 5,764 km / 86,789 grid cells (17.3% of the waterway
# mask). The other 414,895 cells are salt water and are sea-ice gated.
#
# KEY_ID is unique across all 28 candidates (317 distinct values over 320
# features overall), which is why it is the join key rather than WTWY_UNIQ
# (311 distinct) or row order.
RIVER_SEGMENT_KEY_IDS = frozenset({
    "827700_4899-R5-1",      # Ambler River
    "825100_4890-R5-1",      # Black River
    "824900_4843-R5-1",      # Chena River (Fairbanks)
    "829100_4545-R5-1000",   # Dahl Creek
    "821800_4872-R5-1000",   # Egegik River
    "889600_4996-R5-1",      # Innoko River (jct Yukon)
    "827800_4895-R5-1",      # Kobuk River, lower
    "827600_4895-R5-2",      # Kobuk River, upper
    "824500_4867-R5-1",      # Koyukuk River
    "824300_4819-R5-1",      # Kuskokwim River
    "822200_4880-R5-1",      # Kvichak River
    "822000_4828-R5-1",      # Naknek River
    "827900_4892-R5-1",      # Noatak River
    "822400_4879-R5-1",      # Nushagak River
    "803400_4874-R5-1",      # Stikine River
    "814600_4851-R5-1",      # Susitna River
    "824800_4891-R5-1",      # Tanana River, lower
    "824700_4891-R5-1",      # Tanana River, upper
    "821600_4881-R5-1",      # Ugashik Bay and River
    "889700_4860-R5-1",      # Yukon River, Holy Cross - Koyukuk jct
    "825200_4860-R5-1",      # Yukon River, RIVERNAME reads "NORTON SOUND"
    "825000_4860-R5-1",      # Yukon River, Koyukuk jct - Tanana jct
    "824600_4860-R5-1",      # Yukon River, Tanana jct - Fort Yukon
    "824400_4860-R5-1",      # Yukon River, Fort Yukon - Eagle
})

# Candidates the heuristic proposes that a human review rejected. Kept as data
# so the drift check can tell "a new segment appeared" from "a known
# rejection reappeared", and so the reasoning is not lost.
RIVER_SEGMENT_REJECTED = {
    "814000_4849-R5-1000":
        "DRIFT RIVER PLATFORMS, AK — Cook Inlet oil terminal, salt water",
    "824200_9270-R5-1000":
        "YUKON RIVER, AK ACCESS — offshore approach across Norton Sound",
    "827200_9294-R5-1000":
        "BUCKLAND RIVER, AK ACCESS — marine approach, GEO_CLASS O",
    "827300_4894-R5-1000":
        "BUCKLAND RIVER, AK — NWN geometry sits mid-Kotzebue Sound (67.12N "
        "164.60W), ~120 km from the real river mouth; GEO_CLASS O. Sea-ice "
        "gated either way there, so the choice is not load-bearing",
}

# Drift detector only — NOT the selection. 01_build_corridor_masks.py runs
# this against the shapefile and hard-errors if the candidate set stops
# matching ALLOWLIST | REJECTED, which means the NWN changed and the review
# above needs redoing.
RIVER_SEGMENT_STATE = "AK"
RIVER_SEGMENT_NAME_RE = r"\b(?:RIVER|CREEK)\b"   # non-capturing: pandas .str.contains warns on groups
RIVER_SEGMENT_NAME_FIELDS = ("RIVERNAME", "LINKNAME")

# ---------------------------------------------------------------------------
# River-ice fill: how far a cell may borrow, and what happens when it cannot
# ---------------------------------------------------------------------------
# The Brown IDW covers 77,657 of the 86,789 river-domain cells (89.5%), once
# the four marine NHDArea polygons are excluded from its mask (see
# build_brown_polygon_mask.py). The other 9,132 have no interpolated value,
# and friction_surface fills them from the nearest covered cell.
#
# The distance figures below were measured against the FLOWLINE-ONLY footprint
# (200 m buffer of brown_river_flowlines, 68,311 cells), i.e. before the
# NHDArea polygons were available. They therefore OVERSTATE the borrow
# distances that the full mask produces — with polygons included the tier-2
# median is 1.17 km. They are kept because the shape of the distribution is
# what justifies the cap, and that shape is unchanged: the two regimes are
# still same-river metres versus cross-watershed hundreds of kilometres.
#
#     median 18.5 km · p75 52.2 · p90 99.3 · p99 239.3 · max 251.0
#     44% borrow from >25 km away, 26% from >50 km
#
# That single number hides two completely different behaviours:
#
#   Yukon    median  1.5 km   Tanana  0.8 km   Chena   0.1 km
#   Black    median  1.7 km   Innoko  1.8 km   Noatak  2.7 km
#       -> a covered cell just downstream on the SAME river. Genuine
#          interpolation, exactly what the fill was written for.
#
#   Egegik   median 90.7 km   Ugashik 149.6 km   "Dahl Creek" 227.5 km
#       -> a DIFFERENT WATERSHED. Not interpolation but fabrication — the
#          same mechanism as the marine leak, undetected only because the
#          result stayed on land and looked plausible.
#
# So the fill is capped. 25 km keeps every short-range case intact (every
# river listed above sits far inside it) and cuts the cross-watershed ones.
# At this cap the river domain splits three ways:
#
#     77,657  interpolated (Brown IDW)                    89.5%
#      4,734  nearest-filled, within the cap (median 1.17 km)   5.5%
#      4,398  beyond the cap -> latitude-band fallback below    5.1%
#
# The cap does NOT replace the river-domain restriction and cannot. An
# unbounded fill with a 25 km cap would still have leaked into the Gulf,
# because Chatham Strait has frozen interior cells well within 25 km. The
# river/marine split stops leakage into salt water; the cap stops fabrication
# across watersheds. Both are load-bearing and they guard different failures.
RIVER_ICE_FILL_MAX_KM = 25.0

# Beyond the cap, p_ice is the MEDIAN OF THE K NEAREST COVERED CELLS.
#
# Zero was rejected: it means "never freezes", and the uncovered cells are
# regionally clustered rather than scattered — Egegik, Naknek and Ugashik have
# no coverage at all — so zero would open all of Bristol Bay to February barge
# traffic and manufacture cheap winter deliveries to exactly the high-cost
# communities this model exists to study.
#
# A LATITUDE BAND was tried first and FAILED in the field. The reasoning was
# that Alaska's freeze gradient is north-south, so a +/-0.75 deg band would
# preserve it. It is not: the maritime/continental gradient is at least as
# strong. Measured against the real flowlines, Egegik's band (57.35-58.85N)
# contained only Taku (1,339 km east), the mislabelled "Porcupine" polygon in
# Chatham Strait (1,182 km) and Stikine (1,431 km) — every one a Southeast
# Alaska rainforest river — because Kvichak (58.88N) and Nushagak (59.0N) sit
# just above the band ceiling. Ugashik was worse: Stikine and "Porcupine"
# only. The build that resulted had Egegik navigable in January, November and
# December and Ugashik navigable in January and November.
#
# The irony is instructive: a fallback introduced to stop 227 km borrowing
# reached 1,400 km instead. It merely did so as a median rather than a copy.
#
# K-nearest is bounded by geography on BOTH axes with no band to fall out of.
# Verified source selection on the same data: Egegik now draws 100% from
# Nushagak/Kvichak (median neighbour 89 km, same Bristol Bay regime), Ugashik
# 100% from Nushagak/Kvichak (149 km), Naknek 100% from Kvichak (29 km), and
# "Dahl Creek" 85% from Buckland River (228 km — the nearest real watercourse
# to Port Clarence, and the right regime).
#
# K = 200 covered cells is ~4.5 km2 of river surface: large enough that one
# anomalous reach cannot swing the median, small enough to stay inside one
# drainage in every case measured. It is a statistical reach, not a spatial
# one — that is the whole point of the tier.
RIVER_ICE_FALLBACK_K = 200

# ---------------------------------------------------------------------------
# Hard seasonal windows
# ---------------------------------------------------------------------------
# Ice roads: per Alaska Fuel Delivery Cost Analysis, viable Jan-Mar only.
# Outside this window, ice-road pixels are not burned into the overland
# surface, so they revert to off-road terrain cost and the routing graph
# naturally drops the ice-road extension. The gate lives inside the overland
# branch of friction_surface.build_mode_friction.
#
# Marine linehaul: Jun-Oct outer operator-activity envelope. The regional
# difference between the Bering/Kuskokwim (Jun-Oct) and Beaufort
# (~Jul-mid-Sep) is handled per-pixel by the monthly sea_ice climatology
# raster against SEA_ICE_THRESHOLD, so this constant only needs to cover
# the union. May is excluded — no operator runs in May: Crowley's
# "180-day window" starts in June and the 2026 Bethel first-arrival was
# early June (KYUK, 4 Jun 2026). For Beaufort coastal deliveries the
# sea-ice raster does the real gating.
ICE_ROAD_SEASON_MONTHS = {1, 2, 3}
# CAUTION: currently UNUSED (no consumer in the codebase as of this commit),
# and it must stay that way unless it is applied REGIONALLY. The Jun-Oct
# envelope describes western and northern Alaska. Applied as a blanket gate it
# would close Southeast and Southcentral Alaska for seven months of the year —
# the same false winter closure the RIVER_SEGMENT_* classification above
# exists to prevent, arriving by a different route. Gulf/SE marine linehaul is
# year-round; let the sea-ice raster do the gating.
MARINE_LINEHAUL_SEASON_MONTHS = {6, 7, 8, 9, 10}

# ---------------------------------------------------------------------------
# Facility delivery method -> canonical modes
# ---------------------------------------------------------------------------
# Maps a facility's delivery_method string (from Utilities_Bulk_Fuel_Inventory.csv,
# AEA data, or Fuel_Delivery_Method.shp) to a tuple of canonical mode
# names. Multi-method strings expand to multiple modes - one connector
# per mode is generated per facility.
#
# "Ice Road" (with space and capital R) is the verbatim value used by
# the Fuel_Delivery_Method dataset (shp shipped zipped at
# inputs/bulk_fuel_data/raw/Fuel_Delivery_Method.zip; csv at
# inputs/literature_sources_for_agent_analysis/market_data/).
DELIVERY_METHOD_TO_MODES = {
    "Barge":          ("barge",),
    "Road":           ("overland",),
    "Plane":          ("plane",),
    "Ice Road":       ("overland",),
    "Plane or Road":  ("plane", "overland"),
    "Barge or Road":  ("barge", "overland"),
    "Plane or Barge": ("plane", "barge"),
}

# Maps canonical mode names to NETWORK_FILES keys (which network layer
# a facility with this mode connects to). Retained for network-layer lookups.
MODE_TO_NETWORK = {
    "barge":    "waterways",
    "overland": "roads",
    "plane":    "airports",
}


# ---------------------------------------------------------------------------
# Path re-exports (backward compatibility)
# ---------------------------------------------------------------------------
# Existing call sites import RASTER_DIR / RASTER_FILES / NETWORK_DIR /
# NETWORK_FILES / NETWORK_CRS from friction_config; they now live in
# friction_paths but are re-exported here so the migration is non-breaking.
# New code should import directly from friction_paths.
from .friction_paths import (  # noqa: E402 (intentional re-export at bottom)
    RASTER_DIR,  # noqa: F401
    RASTER_FILES,  # noqa: F401
    NETWORK_DIR,  # noqa: F401
    NETWORK_FILES,  # noqa: F401
    NETWORK_CRS,  # noqa: F401
)
