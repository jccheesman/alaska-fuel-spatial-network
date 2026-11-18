# -*- coding: utf-8 -*-
"""friction_costs.py

Cost rates, intermodal-transfer fees, and mode metadata for the friction-
and routing layers. Pulled out of friction_config.py so the config module
can shrink to pure constants and the cost model has a single home.

All transport rates are USD per gallon-mile, derived from the "Alaska Fuel
Delivery Cost Analysis" research dossier. Gallon-mile normalization makes
modes comparable despite a ~1000x capacity spread (3K-gallon ice-road
truck vs. 3M-gallon linehaul barge). Total path cost =
sum(gallon-mile rate * miles along route) + intermodal transfer fees,
units $/gallon.
"""

from __future__ import annotations

import os

from .friction_config import METERS_PER_MILE, TARGET_RESOLUTION


# ===========================================================================
# Baseline delivery cost rates (USD per gallon-mile, 2026$ at CPI-U 332.243)
# ===========================================================================
# RE-DERIVED 2026-11-17/18 (owner-approved migration; the figures are a PROPOSAL
# the owner chose to apply, with their statuses carried in RATE_STATUS below).
# Record: docs/cost_derivation/2026-11/ (one addendum per rate with a derived-
# versus-assumed table for every input, SOURCES.md for every document, errata,
# decision log). Method: >=3 blind derivations per rate from owner-supplied
# documents, then one adversarial verifier per rate (skill derive-fuel-costs).
# Index basis: CPI-U, January-September 2026 average = 332.243 (downloaded
# series; replaces the former projected 330.0).
#
#   Road (highway tanker): carriage-only, empty backhaul inside. 0.0007
#       CONFIRMED (Derived): Econ One Valdez->Fairbanks $0.20/gal over ~364 mi
#       = 0.00076; ATRI tank-carrier build-up 0.00085; State heating-oil
#       contract gradient 0.00068 (document not re-opened in 2026-11). Range
#       0.00045-0.0011 (evidence this round 0.00055-0.0011).
#   Barge: SPLIT in 2026-11 into three segments; the blended 0.0010 is retired
#       ("Barge" now means OCEAN LINE-HAUL; river is "BargeRiver"):
#       "Barge"      ocean line-haul, transportation only: 0.00021, range
#           0.00013-0.00028, NO fixed part. DERIVED (ISER 2010 charged rate
#           0.000205, Econ One 2016 0.000207, OSRO tanker midpoint 0.00013;
#           spread 1.6; the OSRO route/year are undocumented, so the third
#           method is weak). Port/terminal handling, wharfage and village
#           delivery are NOT inside it: they are the landing-class fees
#           (LANDING_CLASS_FEES below).
#       "BargeRiver" river barge, carriage only: 0.0013 per CHANNEL mile, range
#           0.0009-0.0044. PROVISIONAL: the total for a short haul agrees (3
#           methods, 1.8x) but the per-mile part does not (3.9x). Its fixed
#           part ($0.50 per river delivery) is the "river_village" landing fee.
#       Coastal small-barge delivery to a village ($0.45 per delivery + 0.0010
#           per sailing mile; PROVISIONAL) has no edges of its own: it is the
#           "coastal_village" landing fee (ASSEMBLED, see LANDING_CLASS_FEES).
#       Which waterway edge is ocean or river comes from edge_water_class
#       (workflow 03 stage 05: marine/river label sampled along each edge);
#       a mixed edge pays the length-weighted blend. Seasonality is not in the
#       rate: each waterway cell is gated by its monthly sea/river-ice cover.
#   Plane: 0.016 per one-way statute air mile, no fixed part, range 0.013-0.024.
#       PROVISIONAL, lowered from 0.025: two verified independent methods
#       (published DEC 2007/ISER 2010 statements 0.0190; the Nov 2007 Fairbanks->
#       Allakaket delivery 0.0136, spread 1.4) where the standard asks for
#       three; the applied 0.025 implied $4.54/gal to Allakaket against a FY2025
#       price ceiling of $3.48-3.70. Small aircraft (150-200 gal) cost 0.05-0.11
#       and are not represented. General freight tariffs (Everts, Lynden) are a
#       ceiling only.
#   Ice road: 0.010 KEPT (ASSUMED): no tariff, contract or invoice for any
#       Alaska winter fuel haul exists. Two regimes ~3.8x apart (truck on ice
#       road ~0.007; snow tractor and sled ~0.026); one statewide rate per user
#       decision (no regime split). Range 0.004-0.030 (upper bound raised from
#       0.025: three readings above it). Season Jan-Mar (ICE_ROAD_SEASON_MONTHS).
# Never tune a rate to make routing look right; change a point only with its
# range and provenance in one edit and rerun check_cost_invariants.py.
BASELINE_RATES_PER_GALLON_MILE = {
    "Road":       0.0007,
    "Barge":      0.00021,    # ocean line-haul (see above); NOT the retired blended 0.0010
    "BargeRiver": 0.0013,     # river barge, per channel mile; fixed part = river_village landing fee
    "Plane":      0.016,
    "IceRoad":    0.010,
}

# Evidence status of each rate (see docs/cost_derivation/2026-11/CONVENTIONS.md):
#   derived     >=3 independent methods within ~3x, inputs checked in documents
#   provisional best estimate on evidence that falls short; carried with a wide range
#   assumed     no tariff/contract/invoice evidence; applied value kept
# Results that depend on a provisional or assumed rate should be reported with the range.
RATE_STATUS = {
    "Road":       "derived",
    "Barge":      "derived",
    "BargeRiver": "provisional",
    "Plane":      "provisional",
    "IceRoad":    "assumed",
}

# Documented uncertainty ranges for the baseline rates — same units and
# provenance as the comment block above, restated as data so the
# derive-fuel-costs skill checker can enforce point-in-range mechanically.
# Update these together with the rate whenever a re-derivation shifts a
# point estimate.
BASELINE_RATE_RANGES = {
    "Road":       (0.00045, 0.0011),
    "Barge":      (0.00013, 0.00028),
    "BargeRiver": (0.0009,  0.0044),
    "Plane":      (0.013,   0.024),
    "IceRoad":    (0.004,   0.030),
}

# Rate keys that price the same canonical mode on different surfaces. A rate
# key not named by MODE_METADATA must appear here as a variant of a mode.
RATE_VARIANTS = {"barge": ("Barge", "BargeRiver")}

# Raw vehicle-mile rates from carrier tariffs - reference only, not consumed
# by routing. Kept here so future updates can trace back to source data.
VEHICLE_MILE_RATES_REFERENCE = {
    "Road":    {"low": 3.50, "high": 6.00, "point": 4.75, "capacity_gal": 9000,
                "note": "AK heavy-transport range (heavyequipmenttransport.com); "
                        "tanker payloads 9,000-13,000 gal (Dalton semis/A-trains)"},
    "Barge":   {"low": None, "high": None, "point": 0.32, "capacity_gal": 3_000_000,
                "note": "ocean line-haul: ISER 2010 $0.205/gal (2010$) x1.52 CPI-U = $0.31 "
                        "over the 1,527 sm mean model distance to the Western hubs; "
                        "Econ One 2016 25 cpg x1.38 over ~1,669 sm = $0.34"},
    "BargeRiver": {"low": None, "high": None, "point": 0.50, "capacity_gal": 100_000,
                "note": "river barge fixed part per delivery $0.50 (provisional; "
                        "range 0.20-0.80) + 0.0013/gal per channel mile; barge payload "
                        "assumed 100,000-250,000 gal (no document states it)"},
    "Plane":   {"low_per_lb": 0.80, "high_per_lb": 2.12, "fuel_surcharge": 0.42,
                "fuel_density_lb_per_gal": 7.05, "capacity_gal": 4000,
                "note": "Everts general-freight tariff re-read 2026-11-17 (rates effective "
                        "2026-04-16; 42% fuel surcharge from 2026-11-11); Lynden Air Cargo "
                        "similar (41% from 2026-11-18). General freight, NOT a bulk-fuel "
                        "rate: a ceiling only. DC-6 diesel payload ~4,000 gal (28,000 lb); "
                        "bulk fuel actually flies charter-only"},
    "IceRoad": {"low": 10.00, "high": 30.00, "point": 20.00, "capacity_gal": 3000,
                "note": "engineering estimate, no published source exists; "
                        "Noatak proposal confirms 3,000-5,000 gal loads at "
                        "10-12 mph but publishes no rate"},
}


# ===========================================================================
# Intermodal transfer fees (USD per gallon)
# ===========================================================================
# Structured to mirror the routing graph. Every transfer edge joins exactly
# two line-haul modes, so every key here is one (mode_a, mode_b) modal boundary
# in the {overland, barge, ice_road, plane} vocabulary. A per-pair transfer type
# maps straight to its pair via TRANSFER_TYPE_TO_MODES (infer_transfer_fees,
# below). One entry == one kind of modal handoff.
# Routing reads only "total"; the "counts" sub-key records which handling the
# fee actually pays for (provenance, not separately charged); the "range"
# sub-key is the documented uncertainty band from the blind re-derivation,
# enforced mechanically by the derive-fuel-costs skill checker.
#
# STORAGE-FREE, RATE-AWARE VALUES (blind re-derivation, supplementary/cost-derivations/
# 06_connection_costs.md, 2026-07-28). Each fee prices the ATOMIC modal-
# boundary crossing only — there is no intake+storage-rest+outbound chain,
# because hub storage is not a graph node. The construction rule: bill ONLY
# handling with no home in a per-mile rate. The per-mile Barge/Plane/IceRoad
# rates are ALL-IN (each already carries its own side's handling — marine
# intake/lightering, aircraft onboard pump/crew, ice-road +20% load/unload
# adder), so that side is EXCLUDED to avoid double-counting. The Road rate is
# CARRIAGE-ONLY, so the road-carriage-side out-loading/receiving is the only
# genuinely uncounted handling and is what each fee bills. Where no road mode
# is incident (barge<->ice_road) only a thin facility-interface residual
# remains, so the fee collapses near zero. See §6.6 for the coupling proof
# that the four per-mile rates are unchanged by this re-derivation.
#
# There is deliberately NO "storage" or "drums" pseudo-mode key: the graph
# has no storage or drum node. The per-leg storage/drum decomposition is
# documented in supplementary/cost-derivations/05_transfer_fees.md; add explicit per-leg
# fees only when the inventory-dynamics phase (Phase 6) makes hub storage an
# explicit node. Fees are direction-insensitive (a graph edge is traversed
# both ways), so _lookup_fee tries either key ordering.
#
# Live in the 2026-11-16 network-of-record (per-pair transfer types; counts are
# the EXPECTED tripwire in fuel_network/load.py): ("barge","overland") prices
# BargeRoadTransfer (286) + BargeAirTransfer (2), ("barge","ice_road") prices
# BargeIceRoadTransfer (21), ("overland","ice_road") prices IceRoadRoadTransfer
# (12), ("plane","overland") prices AirRoadTransfer (2). infer_transfer_fees maps
# each transfer type straight to its pair via TRANSFER_TYPE_TO_MODES.
#
# RE-DERIVED 2026-11-17/18 (docs/cost_derivation/2026-11/addendum_transfer_fees.md):
# the old ("barge","overland") fee of 0.24 was one list price (Crowley Bethel truck
# rack) billed at BOTH the origin port and the destination landing on almost every
# barge route ($0.48/gal). It is replaced by LANDING_CLASS_FEES (below), keyed by
# the kind of place the barge lands at; the ("barge","overland") entry now holds
# only the single-key FALLBACK used when no landing class is available.
INTERMODAL_TRANSFER_FEES = {
    ("barge", "overland"): {
        # 288 transfer edges (BargeRoadTransfer 286 + BargeAirTransfer 2). SINGLE-KEY
        # FALLBACK ONLY: the model prices these edges by landing class
        # (LANDING_CLASS_FEES) whenever the classes are available. 0.04 per crossing
        # (about 0.08 per barge route, two crossings) is the verifier's single-key
        # value: hub-own gallons 17-25% x hub discharge ~0.12 + village gallons
        # 75-83% x village landing ~0.046 (ISER 2010 Table 4 terminal use $0.03 in
        # 2010$ x1.52). Range 0.01-0.10 (0.15 with a third-party terminal or a
        # missing header). PROVISIONAL (computed from the class values and an
        # assumed gallon mix). The truck rack (Crowley Bethel $0.25 in 2022 =
        # $0.284 in 2026$, a list price at one remote third-party terminal) is NOT
        # a base-case fee: it prices one event (loading a tank truck from a
        # tank farm), not a barge landing. Was 0.24 (range 0.15-0.30, "high
        # confidence" although the two methods behind it differed 11x).
        "counts": "single-key fallback: average landing handling, one crossing",
        "total": 0.04,
        "range": (0.01, 0.10),
    },
    ("barge", "ice_road"): {
        # 21 BargeIceRoadTransfer edges at North Slope hubs. Expected never to be
        # traversed: a same-month barge<->ice-road handoff is temporally
        # impossible there (ice roads Jan-Mar, barges only in the summer ice-free
        # window; zero month-overlap verified at the 8 sites of an earlier
        # network, recheck on rerunning workflow 03), so monthly Dijkstra should
        # never exercise this fee. Reasoned in 2026-07 as a thin facility-
        # interface residual (ice-road load/unload sits in the 0.010 rate's +20%
        # adder) -> ~0.011; UNCHANGED in the 2026-11 re-derivation: no source
        # prices this event (ASSUMED), and it is never traversed, so it stays a
        # completeness entry. Was 0.40. Range 0.00-0.02.
        "counts": "thin vessel<->land-tanker facility-interface residual",
        "total": 0.011,
        "range": (0.00, 0.02),
    },
    ("plane", "overland"): {
        # Latent modal boundary at air-served hubs (a future plane<->overland
        # connector). Bills the road/ground-side receiving only: tanker-
        # driver connect-monitor-disconnect (~0.83 hr) + fittings/grounding.
        # The aircraft onboard offload pump + flight/ground crew are EXCLUDED —
        # already in the all-in plane charter per-mile rate (0.016). UNCHANGED in
        # the 2026-11 re-derivation (ASSUMED: no source prices it). Was 0.157
        # (bundled aircraft handling + storage). Range 0.015-0.045. Conf. med.
        "counts": "road-side tarmac receiving labor + fittings",
        "total": 0.025,
        "range": (0.015, 0.045),
    },
    ("overland", "ice_road"): {
        # Keys IceRoadRoadTransfer (12 edges, Dalton/North Slope ice↔road hand-
        # offs). Bills the road-carriage
        # side of a single continuous truck->ice-road-truck pumped changeover
        # (metered PTO pump-out labor + transfer equipment). The ice-road-side
        # pump-in dwell is EXCLUDED — already in the 0.010 rate's +20% load/
        # unload adder. Was 0.25 (a storage/tank-rack analog, truck->tank->
        # truck two-leg chain). Range 0.014-0.032. Confidence medium.
        "counts": "road-side pumped-changeover labor + transfer equipment",
        "total": 0.022,
        "range": (0.014, 0.032),
    },
}


# ===========================================================================
# Barge landing fees by place type (USD per gallon per crossing, 2026$)
# ===========================================================================
# RE-DERIVED 2026-11 (docs/cost_derivation/2026-11/addendum_transfer_fees.md and
# the barge addenda). A barge<->land crossing is priced by WHAT KIND OF PLACE the
# barge lands at, not one value for every crossing. fuel_network.landings assigns
# each BargeRoadTransfer / BargeAirTransfer edge one of these classes. The fee is
# billed at either end of a route, so a route from a road-system port to a
# village pays "road_port" + the village class.
#
#   road_port        loading at a road-system port (Anchorage, Valdez, Whittier,
#                    Nenana ...): wharfage 20.49 c/bbl + valve-yard transfer 6.08
#                    c/bbl + modernization surcharge $0.14/bbl (Port of Alaska
#                    Tariff 10.2, 2026) = ~$0.01/gal. Range 0.00-0.03. PROVISIONAL
#                    (one tariff at one port).
#   hub              discharge of a line-haul barge at a remote hub OR a dock-served
#                    port, own terminal: Bethel $0.06 wharfage + $0.06 transfer
#                    (Tariff #005, 2026), Nome $0.05 inbound (Tariff 16.6, 2026),
#                    ISER 2010 shore labour $0.04-0.06 (2010$). 0.12, range
#                    0.05-0.20 (0.20-0.38 through a third-party terminal).
#                    PROVISIONAL (two methods, spread 1.4).
#   coastal_village  small-barge delivery from a hub or a vessel at anchor to a
#                    coastal village, discharge to the village header included:
#                    ASSEMBLED, not derived. The derived all-in is $0.45 per
#                    delivery (range 0.15-0.70) + 0.0010 per sailing mile
#                    (PROVISIONAL); the network has no edge for the sailing leg,
#                    so it is carried flat as $0.45 + 0.0010 x ~250 mi - the
#                    ~$0.05 of ocean line-haul the route already pays over the
#                    same miles = ~$0.65. Range 0.40-1.15. Village landing fee is
#                    ZERO on top of this (it already includes discharge).
#   river_village    river delivery, discharge included: the river fixed part
#                    $0.50 per delivery (range 0.20-0.80; PROVISIONAL; 0.0 on the
#                    contract reading, 0.82 on one ISER reading). The per-mile
#                    part is the "BargeRiver" rate on the river edges.
#
# Assembly rules (the assistant's proposals, applied with the owner's approval;
# see the chapter 00 addendum): (1) no separate village fee where a delivery
# charge is applied; (2) hub discharge is billed once, at the hub; (3) no fixed
# part on the ocean rate. The class of each landing comes from the reviewed table
# inputs/network_qc/landing_classes.csv plus a deterministic network rule.
LANDING_CLASS_FEES = {
    "road_port": {
        "counts": "loading at a road-system port: wharfage, valve-yard transfer, modernization surcharge",
        "total": 0.01, "range": (0.00, 0.03), "status": "provisional",
    },
    "hub": {
        "counts": "line-haul discharge at a remote hub or dock-served port: wharfage, transfer, shore labour",
        "total": 0.12, "range": (0.05, 0.20), "status": "provisional",
    },
    "coastal_village": {
        "counts": "small-barge delivery to a coastal village incl. discharge (assembled: 0.45 + mileage - ocean miles)",
        "total": 0.65, "range": (0.40, 1.15), "status": "provisional (assembled)",
    },
    "river_village": {
        "counts": "river delivery fixed part incl. discharge at the village header",
        "total": 0.50, "range": (0.20, 0.80), "status": "provisional",
    },
}

# ===========================================================================
# Transfer-fee inference (edge_class -> modal handoff -> fee)
# ===========================================================================
# Maps the routing graph's edge_class vocabulary onto the {overland, barge,
# ice_road, plane} modes that key INTERMODAL_TRANSFER_FEES, and prices each
# Transfer edge from the line-haul modes incident to its endpoints. Lives
# here (not in the routing layer) so the cost model owns every dollar and the
# derive-fuel-costs audit can import it without the graph-assembly module.

# edge_class -> vocabulary used by INTERMODAL_TRANSFER_FEES keys.
FEE_MODE = {
    "Waterway": "barge",
    "Road": "overland",
    "RoadConnector": "overland",
    "IceRoad": "ice_road",
    "IceRoadConnector": "ice_road",
    "Air": "plane",
    # legacy edge_class aliases (pre-rename DuckDBs)
    "Weld": "overland",
    "Join": "overland",
    "IceRoadWeld": "ice_road",
}

# Per-pair transfer type -> the two fee-modes it joins. A transfer's type NAMES
# the modes it bridges (classify_connectors), so its fee is a direct lookup — no
# incident-mode inference, no ambiguity. Keys are the edge_class/type values.
TRANSFER_TYPE_TO_MODES = {
    "BargeRoadTransfer":    ("barge", "overland"),
    "BargeIceRoadTransfer": ("barge", "ice_road"),
    "IceRoadRoadTransfer":  ("overland", "ice_road"),
    "AirRoadTransfer":      ("overland", "plane"),
    # A barge connector landing on a hub node that ALSO carries an air leg gets
    # named BargeAirTransfer (classify_connectors ranks Air over Road). Physically
    # it is still the barge->ground handoff — fuel lands at the hub's dock/road,
    # not nozzle-to-wing — so it is priced barge<->overland, same as BargeRoadTransfer.
    # Any onward air movement is the separate overland<->air step at that node.
    "BargeAirTransfer":     ("barge", "overland"),
}


def _lookup_fee(mode_a: str, mode_b: str) -> float:
    """Per-gallon transfer fee for a modal handoff, direction-insensitive.

    The fee dict is keyed directionally but a graph edge is traversed both
    ways; physical handling events are the same either direction, so the
    defined direction's total is used for both.
    """
    for key in ((mode_a, mode_b), (mode_b, mode_a)):
        if key in INTERMODAL_TRANSFER_FEES:
            return float(INTERMODAL_TRANSFER_FEES[key]["total"])
    raise KeyError(
        f"No INTERMODAL_TRANSFER_FEES entry for ({mode_a}, {mode_b}) in "
        "either direction — add one to friction_costs.py (edge-cost "
        "completeness rule: no edge is costless)."
    )


def landing_fee(landing_class: str) -> float:
    """Per-gallon fee for a barge landing class (see LANDING_CLASS_FEES)."""
    try:
        return float(LANDING_CLASS_FEES[landing_class]["total"])
    except KeyError:
        raise KeyError(
            f"Unknown landing class {landing_class!r}; expected one of "
            f"{sorted(LANDING_CLASS_FEES)}"
        ) from None


# Transfer types whose fee is set by landing class when classes are supplied.
LANDING_PRICED_TYPES = ("BargeRoadTransfer", "BargeAirTransfer")


def infer_transfer_fees(edges, landing_class=None):
    """Per-gallon fee for each transfer edge, from its per-pair type.

    A transfer's `edge_class` names the two modes it joins
    (``BargeRoadTransfer`` -> barge<->overland), so the fee is a direct
    `TRANSFER_TYPE_TO_MODES` -> `_lookup_fee` — no incident-mode inference and no
    ambiguity. A LEGACY export whose transfers are the generic `Transfer` type
    falls back to the incident-mode inference so old DuckDBs still price.

    Barge landings (BargeRoadTransfer, BargeAirTransfer) are priced by landing
    class when ``landing_class`` is given: a mapping or Series edge_id -> class in
    LANDING_CLASS_FEES. An edge missing from it takes the single-key fallback
    ("barge", "overland"). An unknown class is a hard error.

    Args:
        edges: DataFrame with columns edge_id, from_node, to_node, edge_class.
        landing_class: optional edge_id -> landing class.

    Returns:
        A pandas Series of fees indexed by edge_id for every transfer edge.
    """
    import pandas as pd

    fees = {}
    typed = edges[edges["edge_class"].isin(TRANSFER_TYPE_TO_MODES)]
    for edge_id, ec in typed[["edge_id", "edge_class"]].itertuples(index=False):
        cls = None
        if landing_class is not None and ec in LANDING_PRICED_TYPES:
            cls = landing_class.get(edge_id) if hasattr(landing_class, "get") else None
        if cls is not None and not (isinstance(cls, float) and cls != cls):
            fees[edge_id] = landing_fee(cls)
        else:
            fees[edge_id] = _lookup_fee(*TRANSFER_TYPE_TO_MODES[ec])

    legacy = edges[edges["edge_class"] == "Transfer"]
    if len(legacy):                       # old export: infer the pair from neighbours
        line_haul = edges[edges["edge_class"] != "Transfer"]
        incident = pd.concat([
            pd.DataFrame({"node": line_haul["from_node"],
                          "mode": line_haul["edge_class"].map(FEE_MODE)}),
            pd.DataFrame({"node": line_haul["to_node"],
                          "mode": line_haul["edge_class"].map(FEE_MODE)}),
        ])
        node_modes = incident.groupby("node")["mode"].agg(set)
        for edge_id, u, v in legacy[["edge_id", "from_node", "to_node"]].itertuples(index=False):
            side_u, side_v = node_modes.get(u, set()), node_modes.get(v, set())
            if len(side_u) != 1 or len(side_v) != 1:
                raise ValueError(
                    f"Transfer edge {edge_id}: ambiguous incident modes "
                    f"({sorted(side_u)} x {sorted(side_v)}) — review by hand."
                )
            fees[edge_id] = _lookup_fee(next(iter(side_u)), next(iter(side_v)))
    return pd.Series(fees, name="fee")


# ===========================================================================
# Physical constants
# ===========================================================================
FUEL_DENSITY_LB_PER_GAL = 7.1           # diesel/heating oil #1 and #2


# ===========================================================================
# State of Alaska FY25/FY26 contract adders (VALIDATION DATA - not input)
# ===========================================================================
# Per-gallon delivery premium over wholesale OPIS price at representative
# contract locations. These bundle ALL transport, handling, terminal, and
# overhead costs - use them to VALIDATE the modeled $/gallon cost from a
# routing run, NOT as an additive input.
#
# Format: location -> (vendor, HO_FY25, HO_FY26, ULSD_FY25, ULSD_FY26)
STATE_CONTRACT_ADDERS_PER_GALLON = {
    "Anchorage":     ("Shoreside/Crowley",     0.2816, 0.2872, 0.2065, 0.2106),
    "Fairbanks":     ("Inlet Energy/Crowley",  0.3969, 0.4048, 0.4974, 0.5074),
    "Kenai":         ("Petro Marine/Inlet",    0.2272, 0.2318, 0.2802, 0.2858),
    "Juneau":        ("Petro Marine/Delta W.", 0.2860, 0.2917, 0.1902, 0.1940),
    "Deadhorse":     ("Inlet Energy",          0.9188, 0.9371, 0.9976, 1.0175),
    "Eagle":         ("Inlet Energy",          1.4668, 1.4960, 1.5266, 1.5570),
    "Cordova":       ("Shoreside",             1.8088, 1.8143, 1.9633, 2.0019),
    "Klawock/Hollis":("Petro Marine Services", 1.1130, 1.1352, 1.1130, 1.1352),
}


# ===========================================================================
# Connector / plane edge cost parameters
# ===========================================================================
CONNECTOR_COST_PER_GALLON_MILE_USD = BASELINE_RATES_PER_GALLON_MILE["Road"]
PLANE_COST_PER_GALLON_MILE_USD = BASELINE_RATES_PER_GALLON_MILE["Plane"]
PLANE_HANDLING_COST_PER_GALLON_USD = INTERMODAL_TRANSFER_FEES[("plane", "overland")]["total"]


# ===========================================================================
# Per-mode pixel cost baselines (combined-raster work, currently deferred)
# ===========================================================================
OVERLAND_COST_PER_GALLON_PIXEL_USD = (BASELINE_RATES_PER_GALLON_MILE["Road"]  / METERS_PER_MILE) * TARGET_RESOLUTION
BARGE_COST_PER_GALLON_PIXEL_USD    = (BASELINE_RATES_PER_GALLON_MILE["Barge"] / METERS_PER_MILE) * TARGET_RESOLUTION


# ===========================================================================
# Mode metadata
# ===========================================================================
# Single source of truth for the canonical-mode <-> rate-key <-> facility-
# method-string relationships. The edge-weighting scripts read these mappings
# from here rather than defining their own.
MODE_METADATA = {
    "overland": {"rate_key": "Road",    "facility_method": "Road",     "repr_month": 6},
    "barge":    {"rate_key": "Barge",   "facility_method": "Barge",    "repr_month": 7},
    "ice_road": {"rate_key": "IceRoad", "facility_method": "Ice Road", "repr_month": 2},
    "plane":    {"rate_key": "Plane",   "facility_method": "Plane",    "repr_month": 0},
}

DEFAULT_REPR_MONTHS = {m: meta["repr_month"] for m, meta in MODE_METADATA.items() if m != "plane"}
METHOD_TO_MODE = {meta["facility_method"]: m for m, meta in MODE_METADATA.items()}
RATE_KEY_BY_MODE = {m: meta["rate_key"] for m, meta in MODE_METADATA.items()}


# ===========================================================================
# Authoritative ice-road-served communities
# ===========================================================================
# Reads Fuel_Delivery_Method.shp (ships in inputs/raw_facility_data/2022/bulk_fuel_data.zip; path in
# friction_paths.FUEL_DELIVERY_METHOD_SHP, extract with tools/extract_inputs.py),
# the authoritative per-community fuel-delivery-method source for the "which
# communities are ice-road served" question. The current authoritative set
# is {Atqasuk, Nuiqsut}. Anaktuvuk Pass is NOT ice-road-served despite a
# common assumption — Fuel_Delivery_Method.shp records it as "Plane".
#
# Delivery methods carry an AsOfDate, so the set is date-dependent: Atqasuk
# is "Plane" as of 2023-08-15 and "Ice Road" as of 2024-02-15 onward. Pass
# as_of=date(2023, ...) to reconstruct the set at a past date.


from datetime import date as _date
from functools import lru_cache as _lru_cache

def get_hub_facilities(con) -> dict[int, set[str]]:
    """Return facility_id -> set of modes for facilities serving > 1 mode.

    Implicit-hub model (Phase 4): any facility appearing in connects_to
    under more than one mode is a candidate intermodal handoff point.
    Sourced from connects_to (the reporting view) rather than
    mode_specific_edges so cross-mode pairs across edge-recompute cycles
    stay visible.
    """
    rows = con.execute("""
        SELECT facility_id, mode
        FROM (
            SELECT src AS facility_id, mode FROM connects_to WHERE mode IS NOT NULL
            UNION
            SELECT dst AS facility_id, mode FROM connects_to WHERE mode IS NOT NULL
        )
    """).fetchall()
    hubs: dict[int, set[str]] = {}
    for fid, mode in rows:
        hubs.setdefault(int(fid), set()).add(str(mode))
    return {fid: modes for fid, modes in hubs.items() if len(modes) > 1}


def chain_cost_with_transfer_fees(legs: list[tuple[str, float]]) -> float:
    """Sum a multi-leg route cost and apply INTERMODAL_TRANSFER_FEES at handoffs.

    Args:
        legs: ordered [(mode, cost_usd_per_gallon), ...] for each leg.

    Returns:
        Total $/gal including transfer fees at every mode change.

    Missing fee entries are treated as 0 and counted via the warning log
    so unhandled handoffs surface during analysis.

    NOTE: this helper is provided for a future multi-modal orchestrator
    layer above the per-(region, method) TSP. The current TSP iterates
    each (region, method) in isolation and produces a single-mode tour,
    so it does not call this helper — but downstream code that assembles
    Anchorage->Nome->village type routes from per-mode tour fragments
    should use it to charge the matching transfer fee at each hub.
    """
    import logging
    log = logging.getLogger(__name__)
    total = 0.0
    prev_mode: str | None = None
    def _norm(m: str) -> str:
        m = m.lower()
        return "overland" if m == "road" else m

    for mode, cost in legs:
        if prev_mode is not None and prev_mode != mode:
            n_prev = _norm(prev_mode)
            n_curr = _norm(mode)
            fee_entry = INTERMODAL_TRANSFER_FEES.get((n_prev, n_curr))
            if fee_entry is None:
                fee_entry = INTERMODAL_TRANSFER_FEES.get((n_curr, n_prev))
            if fee_entry is None:
                log.warning(
                    "no INTERMODAL_TRANSFER_FEES entry for (%s, %s); using 0",
                    prev_mode, mode,
                )
                fee = 0.0
            else:
                fee = float(fee_entry["total"])
            total += fee
        total += float(cost)
        prev_mode = mode
    return total


@_lru_cache(maxsize=4)
def load_ice_road_communities(
    as_of: _date | None = None, path: str | None = None
) -> frozenset[str]:
    """Return the set of community names served by ice road as of a given date.

    Reads Fuel_Delivery_Method.shp (attribute table only; ships in
    inputs/raw_facility_data/2022/bulk_fuel_data.zip — run tools/extract_inputs.py first), groups by
    CommunityName, takes the most recent AsOfDate <= as_of per community, and
    filters to rows where Fuel_Delivery_Method == 'Ice Road'.

    Args:
        as_of: Cutoff date. None uses today (no temporal filter).
        path: Override source path (.shp or .csv with the same columns).
              Defaults to friction_paths.FUEL_DELIVERY_METHOD_SHP.

    Returns:
        Frozen set of community names.
    """
    import pandas as pd

    from .friction_paths import FUEL_DELIVERY_METHOD_SHP

    src = path or FUEL_DELIVERY_METHOD_SHP
    if str(src).lower().endswith(".csv"):
        df = pd.read_csv(src)
    else:
        import geopandas as gpd

        if not os.path.exists(src):
            raise FileNotFoundError(
                f"{src} not found. It ships inside inputs/raw_facility_data/2022/bulk_fuel_data.zip — "
                "run `python tools/extract_inputs.py` first."
            )
        df = pd.DataFrame(gpd.read_file(src).drop(columns="geometry"))
        # DBF truncates field names to 10 chars — restore the canonical names.
        df = df.rename(columns={"CommunityN": "CommunityName",
                                "Fuel_Deliv": "Fuel_Delivery_Method"})
    if "AsOfDate" in df.columns:
        df["AsOfDate"] = pd.to_datetime(df["AsOfDate"], errors="coerce", utc=True).dt.tz_localize(None)
        if as_of is not None:
            df = df[df["AsOfDate"] <= pd.Timestamp(as_of)]
        df = df.sort_values("AsOfDate")
    # Most recent record per community wins.
    latest = df.drop_duplicates("CommunityName", keep="last")
    ice_road = latest[latest["Fuel_Delivery_Method"] == "Ice Road"]
    return frozenset(ice_road["CommunityName"].dropna().tolist())
