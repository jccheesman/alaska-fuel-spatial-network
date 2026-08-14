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
# Baseline delivery cost rates (USD per gallon-mile, 2026$)
# ===========================================================================
# Derived and verified in supplementary/cost-verification/"Fuel Cost Blind
# Derivations.pdf"; sources in supplementary/cost-derivations/*.md. Each
# rate survived three rounds:
# blind multi-method derivation (2026-07-15), web primary-source
# verification (2026-07-15), and local-document verification against
# ATRI/Econ One/PCE FY2025/NSB/Noatak documents (2026-07-17).
#
#   Road (highway tanker): carriage cost incl. empty backhaul. Econ One
#       transport map (Valdez->Fairbanks $0.20/gal / 364 mi, CPI 2015->26)
#       + ATRI-based build-up + 11-point state-contract distance regression
#       (slope 0.00067, R^2~0.75) converge at 0.0007. Range 0.00045-0.0011;
#       Dalton corridor runs ~0.0012-0.0015 (state contract rows).
#   Barge: blended all-in rate at Bethel-type distance for the current
#       one-rate design. Decomposition (use if linehaul/river edges ever
#       split): ocean linehaul 0.00023 (NOAA route Anchorage->Bethel
#       1,109 nm = 1,276 sm; ISER market rate $0.19-0.22/gal), river
#       distribution 0.011 (DEC 2007 invoice rate $0.007/gal per map mile),
#       lightering/terminal ~$0.8-1.2/gal as a fixed transfer component
#       currently smeared into this blended rate. May-Oct only.
#   Plane: charter-equivalent transport cost, DC-6/C-46 mix at typical
#       130-350 mi stage lengths. Revealed premiums (DCRA Jan 2026 vs
#       empirical $3.60 FAI wholesale anchor) + DC-6 build-up + ISER 2010
#       benchmark + federal charter award converge at 0.025 (range
#       0.015-0.042). Underprices <75-mi shuttles (~0.1-0.2 real).
#   Ice road: single rate spanning two verified regimes per user decision
#       (no regime split): engineered ice road/tanker ~0.004 (Nuiqsut,
#       Kuskokwim) vs tundra snow-trail/cat-train ~0.02 (Atqasuk, AKP).
#       Traffic split data-backed ~50/50 (PCE FY2025 gallons). Jan-Apr.
#       Known bias: ~2x high for Nuiqsut-type edges, ~2x low for
#       Atqasuk-type edges. Last unverified input: ~$900/hr convoy rate.
BASELINE_RATES_PER_GALLON_MILE = {
    "Road":     0.0007,
    "Barge":    0.0010,
    "Plane":    0.025,
    "IceRoad":  0.010,
}

# Documented uncertainty ranges for the baseline rates — same units and
# provenance as the comment block above, restated as data so the
# derive-fuel-costs skill checker can enforce point-in-range mechanically.
# Barge bounds are the decomposition endpoints (ocean linehaul 0.00023,
# river distribution 0.011): the blended one-rate value must lie between
# them. IceRoad bounds are the two verified regimes (engineered ice road
# ~0.004, tundra cat-train ~0.02) widened to the blind-derivation range.
# Update these together with the rate whenever a re-derivation shifts a
# point estimate.
BASELINE_RATE_RANGES = {
    "Road":    (0.00045, 0.0011),
    "Barge":   (0.00023, 0.011),
    "Plane":   (0.015,   0.042),
    "IceRoad": (0.004,   0.025),
}

# Raw vehicle-mile rates from carrier tariffs - reference only, not consumed
# by routing. Kept here so future updates can trace back to source data.
VEHICLE_MILE_RATES_REFERENCE = {
    "Road":    {"low": 3.50, "high": 6.00, "point": 4.75, "capacity_gal": 9000,
                "note": "AK heavy-transport range (heavyequipmenttransport.com); "
                        "tanker payloads 9,000-13,000 gal (Dalton semis/A-trains)"},
    "Barge":   {"low": None, "high": None, "point": 0.29, "capacity_gal": 3_000_000,
                "note": "$0.29/gal linehaul Anchorage->Bethel over 1,276 sm "
                        "(NOAA 1,109 nm); ISER 2010 $0.19-0.22/gal x1.51 CPI"},
    "Plane":   {"low_per_lb": 0.80, "high_per_lb": 2.12, "fuel_surcharge": 0.26,
                "fuel_density_lb_per_gal": 7.05, "capacity_gal": 4000,
                "note": "Everts tariff verified 2026-07-15 (26% surcharge); "
                        "Wright Air within 0-6%; DC-6 diesel payload ~4,000 gal "
                        "(28,000 lb); bulk fuel actually flies charter-only"},
    "IceRoad": {"low": 10.00, "high": 30.00, "point": 20.00, "capacity_gal": 3000,
                "note": "engineering estimate, no published source exists; "
                        "Noatak proposal confirms 3,000-5,000 gal loads at "
                        "10-12 mph but publishes no rate"},
}


# ===========================================================================
# Intermodal transfer fees (USD per gallon)
# ===========================================================================
# Structured to mirror the routing graph. Every Transfer edge joins exactly
# two line-haul modes, so every key here is one (mode_a, mode_b) modal
# boundary in the FEE_MODE vocabulary that infer_transfer_fees (below) derives
# from edge_class — {overland, barge, ice_road, plane}. One entry == one kind
# of modal handoff, the same way the graph has one Transfer edge per handoff.
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
# Live in the current network: ("barge","overland") keys 205 Transfer edges,
# ("barge","ice_road") keys 8. The other pairs are latent modal boundaries
# kept so a future edge (or a plane connector) is priced
# rather than hard-erroring in _lookup_fee (below).
INTERMODAL_TRANSFER_FEES = {
    ("barge", "overland"): {
        # 205 graph Transfer edges (Waterway <-> Road). Bills the road-side
        # truck-rack out-loading only (Crowley Bethel rack $0.25 -> $0.276
        # CPI-2026, shaded to 0.24 for sole-provider margin). The barge marine-
        # header / tank-farm intake is EXCLUDED — already in the all-in barge
        # per-mile rate (0.0010). Was 0.40 (marine_header 0.15 + rack 0.25);
        # the 0.15 was a double-count. Range 0.15-0.30. Confidence high.
        "counts": "road-side truck-rack out-loading",
        "total": 0.24,
        "range": (0.15, 0.30),
    },
    ("barge", "ice_road"): {
        # 8 graph Transfer edges (Waterway <-> IceRoad) at North Slope hubs.
        # NEVER traversed: a same-month barge<->ice-road handoff is temporally
        # impossible (ice roads Jan-Mar, barges May-Oct; zero month-overlap at
        # all 8 sites), so monthly Dijkstra never exercises this fee. Both
        # incident modes are all-in (barge intake in 0.0010; ice-road load/
        # unload in the 0.010 rate's +20% adder), so only a thin facility-
        # interface residual remains -> ~0.011. Was 0.40 (double-counted both
        # all-in legs). Range 0.00-0.02. Completeness/no-costless-edge only.
        "counts": "thin vessel<->land-tanker facility-interface residual",
        "total": 0.011,
        "range": (0.00, 0.02),
    },
    ("plane", "overland"): {
        # Latent modal boundary at air-served hubs (a future plane<->overland
        # connector). Bills the road/ground-side receiving only: tanker-
        # driver connect-monitor-disconnect (~0.83 hr) + fittings/grounding.
        # The aircraft onboard offload pump + flight/ground crew are EXCLUDED —
        # already in the all-in plane charter per-mile rate (0.025). Was 0.157
        # (bundled aircraft handling + storage). Range 0.015-0.045. Conf. med.
        "counts": "road-side tarmac receiving labor + fittings",
        "total": 0.025,
        "range": (0.015, 0.045),
    },
    ("overland", "ice_road"): {
        # Latent modal boundary (Dalton/North Slope). Bills the road-carriage
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
    "Weld": "overland",
    "Join": "overland",
    "IceRoad": "ice_road",
    "IceRoadConnector": "ice_road",
    "IceRoadWeld": "ice_road",   # legacy alias (pre-rename DuckDBs)
    "Air": "plane",
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


def infer_transfer_fees(edges):
    """Per-gallon fee for each Transfer edge, keyed by incident modes.

    For each endpoint of a Transfer edge, collect the fee-modes of its
    incident line-haul edges; the handoff pair is (mode at from-side,
    mode at to-side). Endpoints with several incident modes or with no
    line-haul edge at all are hard errors — with 213 Transfer edges these
    are hand-reviewable, and guessing would misprice the mode switch.

    Args:
        edges: DataFrame with columns edge_id, from_node, to_node, edge_class.

    Returns:
        A pandas Series of fees indexed like the Transfer subset of `edges`.
    """
    import pandas as pd

    line_haul = edges[edges["edge_class"] != "Transfer"]
    incident = pd.concat([
        pd.DataFrame({"node": line_haul["from_node"],
                      "mode": line_haul["edge_class"].map(FEE_MODE)}),
        pd.DataFrame({"node": line_haul["to_node"],
                      "mode": line_haul["edge_class"].map(FEE_MODE)}),
    ])
    node_modes = incident.groupby("node")["mode"].agg(set)

    transfers = edges[edges["edge_class"] == "Transfer"]
    fees = {}
    for edge_id, u, v in transfers[["edge_id", "from_node", "to_node"]].itertuples(
        index=False
    ):
        side_u = node_modes.get(u, set())
        side_v = node_modes.get(v, set())
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
# Reads Fuel_Delivery_Method.shp (ships in inputs/bulk_fuel_data.zip; path in
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
    inputs/bulk_fuel_data.zip — run tools/extract_inputs.py first), groups by
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
                f"{src} not found. It ships inside inputs/bulk_fuel_data.zip — "
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
