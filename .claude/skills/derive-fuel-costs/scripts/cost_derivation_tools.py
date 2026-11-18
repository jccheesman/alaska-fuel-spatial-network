# -*- coding: utf-8 -*-
"""cost_derivation_tools.py — reusable arithmetic for fuel-cost derivations.

The function library used by the derive-fuel-costs skill when deriving or
re-deriving a modality rate (BASELINE_RATES_PER_GALLON_MILE) or an
intermodal transfer fee (INTERMODAL_TRANSFER_FEES). Every conversion the
blind derivations performed by hand lives here so a future re-derivation
uses the same, tested arithmetic:

  - CPI adjustment to 2026$ (dollar-year discipline)
  - vehicle-mile tariff -> gallon-mile rate (capacity normalization)
  - per-pound air tariff -> per-gallon cost (density + fuel surcharge)
  - nautical -> statute miles (NOAA route distances)
  - OLS distance regression (state-contract adder vs. distance)
  - cross-method convergence statistics (the evidence standard)
  - traffic-weighted regime blending (ice-road two-regime rate)

`python cost_derivation_tools.py --selftest` re-derives every applied rate
and fee from its documented convergent-method inputs and checks the value
in friction_costs.py still falls inside the method spread and the
machine-readable ranges. Exit 0 = all reproduce; nonzero = drift between
the code and its documented derivation.

Sources: supplementary/cost-derivations/00_executive_summary.md (method
estimates), friction_costs.py comment blocks (provenance),
supplementary/cost-verification/ (Fuel Cost Blind Derivations.pdf, Fuel
Cost Derivation Verification.md).
"""
from __future__ import annotations

import math
import sys

# ===========================================================================
# CPI (dollar-year discipline)
# ===========================================================================
# CPI-U annual averages (U.S. city average, all items, BLS series
# CUUR0000SA0). Updated 2026-11-18 from a downloaded copy of the series
# (docs/cost_derivation/2026-11/index_basis_2026-11-17.md): 2025 is the
# 11-month average (October 2025 was not published); 2026 is the
# January-September 2026 average, 332.243, the index basis of the 2026-11
# re-derivation (it replaces the projected 330.0; 2010->2026 is x1.5237).
# The series used is a public mirror of the BLS table; when the BLS file is
# in hand, update here ONLY.
CPI_U_ANNUAL = {
    2003: 183.958, 2004: 188.883,
    2005: 195.3,   2006: 201.6,   2007: 207.342, 2008: 215.303,
    2009: 214.537, 2010: 218.056, 2011: 224.939, 2012: 229.594,
    2013: 232.957, 2014: 236.736, 2015: 237.017, 2016: 240.007,
    2017: 245.120, 2018: 251.107, 2019: 255.657, 2020: 258.811,
    2021: 270.970, 2022: 292.655, 2023: 304.702, 2024: 313.689,
    2025: 321.943, 2026: 332.243,
}


def cpi_factor(from_year: int, to_year: int = 2026) -> float:
    """Inflation multiplier taking `from_year` dollars to `to_year` dollars."""
    return CPI_U_ANNUAL[to_year] / CPI_U_ANNUAL[from_year]


def cpi_adjust(value: float, from_year: int, to_year: int = 2026) -> float:
    """Restate a dollar amount from `from_year` dollars into `to_year` dollars."""
    return value * cpi_factor(from_year, to_year)


# ===========================================================================
# Unit conversions
# ===========================================================================
FUEL_DENSITY_LB_PER_GAL = 7.1     # diesel/heating oil (friction_costs.py)
STATUTE_MILES_PER_NM = 1.15078


def gallon_mile_rate(vehicle_mile_rate: float, capacity_gal: float) -> float:
    """$/vehicle-mile tariff -> $/gallon-mile at a given payload.

    The core normalization of the whole cost model: makes a 3,000-gal
    ice-road truck comparable to a 3M-gal linehaul barge. E.g. the AK
    heavy-transport midpoint $4.75/mi over a 9,000-gal tanker -> 0.000528.
    """
    return vehicle_mile_rate / capacity_gal


def per_lb_to_per_gallon(rate_per_lb: float, surcharge: float = 0.0,
                         density: float = FUEL_DENSITY_LB_PER_GAL) -> float:
    """Air-cargo $/lb tariff -> $/gallon delivered, with fuel surcharge.

    E.g. Everts $0.80/lb x 1.26 surcharge x 7.05 lb/gal = $7.10/gal.
    Divide by stage length (per_gallon_over_distance) for a gal-mi rate.
    """
    return rate_per_lb * (1.0 + surcharge) * density


def per_gallon_over_distance(cost_per_gallon: float, miles: float) -> float:
    """Spread a per-delivery $/gal cost over a route length -> $/gal-mi.

    Only valid when the cost is genuinely distance-driven; a fixed
    per-delivery handling cost divided by miles is exactly the smearing
    error the transfer-fee re-derivation removed — use a transfer fee
    instead (see SKILL.md invariant 5).
    """
    return cost_per_gallon / miles


def nm_to_statute(nautical_miles: float) -> float:
    """Nautical -> statute miles (NOAA port-distance tables are in nm)."""
    return nautical_miles * STATUTE_MILES_PER_NM


# ===========================================================================
# Regression + convergence (the evidence standard)
# ===========================================================================

def ols(points, through_origin: bool = False):
    """Least-squares fit of (x, y) pairs -> dict(slope, intercept, r2, n).

    Used for the state-contract distance regression (adder $/gal vs. road
    miles): the slope IS a revealed $/gal-mi rate. through_origin=True
    forces intercept 0 (pure per-mile reading); the two-part cost
    structure finding says a free intercept usually fits better.
    """
    xs = [float(x) for x, _ in points]
    ys = [float(y) for _, y in points]
    n = len(xs)
    if n < 2:
        raise ValueError("need >= 2 points")
    if through_origin:
        slope = sum(x * y for x, y in zip(xs, ys)) / sum(x * x for x in xs)
        intercept = 0.0
    else:
        mx, my = sum(xs) / n, sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        slope = sxy / sxx
        intercept = my - slope * mx
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    my = sum(ys) / n
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"slope": slope, "intercept": intercept, "r2": r2, "n": n}


def convergence(estimates):
    """Spread statistics across independent method estimates.

    `estimates`: {method_name: value}. Returns min/max/spread ratio and
    the geometric mean (the natural center for rates spanning multiples).
    The blind-derivation evidence standard is convergence between >= 3
    genuinely independent methods, not any single source — a spread ratio
    beyond ~3x means the methods have NOT converged and the derivation is
    not ready to apply.
    """
    vals = {k: float(v) for k, v in estimates.items()}
    lo_k = min(vals, key=vals.get)
    hi_k = max(vals, key=vals.get)
    gm = math.exp(sum(math.log(v) for v in vals.values()) / len(vals))
    return {
        "n_methods": len(vals),
        "min": (lo_k, vals[lo_k]),
        "max": (hi_k, vals[hi_k]),
        "spread_ratio": vals[hi_k] / vals[lo_k],
        "geometric_mean": gm,
    }


def blend(rate_weight_pairs):
    """Traffic-weighted average of regime rates -> single blended rate.

    E.g. ice road: [(0.004, 0.5), (0.02, 0.5)] per the PCE FY2025 gallons
    split (Nuiqsut 279k vs Atqasuk 275k). Weights are normalized.
    """
    total_w = sum(w for _, w in rate_weight_pairs)
    return sum(r * w for r, w in rate_weight_pairs) / total_w


# ===========================================================================
# Self-test: reproduce every applied value from its documented derivation
# ===========================================================================

def _load_costs():
    from friction_surface import friction_costs as fc
    return fc


def selftest() -> int:
    """Re-derive each applied rate/fee from documented inputs; return #failures.

    Method inputs are cited from docs/cost_derivation/2026-11/ (the addenda of the
    2026-11 re-derivation) and the friction_costs.py comment blocks. A failure means the code
    value and its documented derivation have drifted apart — fix the
    documentation or re-derive, never silently retune the number.
    """
    fc = _load_costs()
    rates = fc.BASELINE_RATES_PER_GALLON_MILE
    ranges = fc.BASELINE_RATE_RANGES
    fees = fc.INTERMODAL_TRANSFER_FEES
    failures = []

    def check(name, ok, detail):
        print(("PASS  " if ok else "FAIL  ") + name + " — " + detail)
        if not ok:
            failures.append(name)

    status = fc.RATE_STATUS
    landing = fc.LANDING_CLASS_FEES

    # Inputs below are the documented figures of the 2026-11 re-derivation
    # (docs/cost_derivation/2026-11/addendum_*.md); source-year dollars are
    # restated with cpi_adjust so the index basis lives in one place.

    # --- Road: three methods of different kinds; applied 0.0007 confirmed ---
    road_methods = {
        "econ_one_valdez_fbx": cpi_adjust(0.20, 2016) / 364,            # 20 cpg, ~364 mi (Econ One 2016)
        "state_contract_gradient": 0.00068,                              # 11 points, FY27 fees (not re-opened 2026-11)
        "atri_tank_carrier_buildup": cpi_adjust(4.001, 2024) * 2 / 10_000,  # $4.001/mi revenue, empty return, 10,000 gal (payload assumed)
    }
    conv = convergence(road_methods)
    r = rates["Road"]
    check("road.methods_bracket_applied",
          conv["min"][1] * 0.95 <= r <= conv["max"][1] * 1.05,
          f"applied {r} vs methods [{conv['min'][1]:.6f}, {conv['max'][1]:.6f}]")
    check("road.spread_within_3x", conv["spread_ratio"] <= 3.0,
          f"spread {conv['spread_ratio']:.2f} across {conv['n_methods']} methods")
    check("road.in_documented_range", ranges["Road"][0] <= r <= ranges["Road"][1],
          f"{r} in {ranges['Road']}")

    # --- Barge (ocean line-haul): two clean published charges + a weak third --
    ocean_methods = {
        "iser_2010_charged_rate": cpi_adjust(0.205, 2010) / 1526.9,     # $0.19-0.22/gal midpoint, mean model miles to 5 hubs
        "econ_one_2016_long_leg": cpi_adjust(0.25, 2016) / 1669,         # 25 cpg, ~1,669 sm (distance assumed)
        "osro_tanker_midpoint": 0.00013,                                 # West Coast $0.15-0.29, route and year undocumented
    }
    conv = convergence(ocean_methods)
    b = rates["Barge"]
    clean = math.sqrt(ocean_methods["iser_2010_charged_rate"] * ocean_methods["econ_one_2016_long_leg"])
    check("barge_ocean.matches_clean_methods", abs(b - clean) / clean < 0.05,
          f"applied {b} vs geometric mean of the two clean methods {clean:.6f}")
    check("barge_ocean.spread_within_3x", conv["spread_ratio"] <= 3.0,
          f"spread {conv['spread_ratio']:.2f} across {conv['n_methods']} methods")
    check("barge_ocean.in_documented_range", ranges["Barge"][0] <= b <= ranges["Barge"][1],
          f"{b} in {ranges['Barge']}")
    check("barge_ocean.not_the_retired_blend", b < 0.0005,
          f"applied {b}; the blended 0.0010 is retired (any single barge rate above ~0.00052 routes Nome by river)")

    # --- BargeRiver: total at a short haul converges, per-mile part does not --
    river_slopes = {"state_contract_slope": 0.0044, "iser_2010_day_cost": 0.0011, "fy2025_price_slope": 0.0014}
    conv = convergence(river_slopes)
    br = rates["BargeRiver"]
    median = sorted(river_slopes.values())[1]
    check("barge_river.near_median_slope", abs(br - median) / median < 0.10,
          f"applied {br} vs median of three slopes {median}")
    check("barge_river.status_matches_spread",
          (conv["spread_ratio"] > 3.0) == (status["BargeRiver"] != "derived"),
          f"per-mile spread {conv['spread_ratio']:.2f} -> status {status['BargeRiver']!r}")
    tanana_methods = {"contract_net_of_truck": 0.61, "dec_2007_invoice_rate": 1.10, "iser_2010_build": 0.63}
    tanana = landing["river_village"]["total"] + br * 164          # 164 channel miles from Nenana
    conv = convergence(tanana_methods)
    check("barge_river.short_haul_total_inside_methods",
          conv["min"][1] <= tanana <= conv["max"][1] and conv["spread_ratio"] <= 3.0,
          f"fixed + per-mile at Tanana = {tanana:.2f} $/gal vs methods {sorted(tanana_methods.values())} (spread {conv['spread_ratio']:.2f})")
    check("barge_river.in_documented_range", ranges["BargeRiver"][0] <= br <= ranges["BargeRiver"][1],
          f"{br} in {ranges['BargeRiver']}")

    # --- Plane: two verified methods; price ceiling at Allakaket ------------
    plane_methods = {"published_statements": 0.0190, "nov_2007_allakaket_delivery": 0.0136}
    conv = convergence(plane_methods)
    p = rates["Plane"]
    check("plane.near_geometric_mean", abs(p - conv["geometric_mean"]) / conv["geometric_mean"] < 0.05,
          f"applied {p} vs geometric mean {conv['geometric_mean']:.4f} of {conv['n_methods']} methods")
    check("plane.status_matches_method_count",
          (conv["n_methods"] < 3) == (status["Plane"] != "derived"),
          f"{conv['n_methods']} verified methods -> status {status['Plane']!r}")
    check("plane.under_allakaket_ceiling", per_gallon_over_distance(3.70, 181.7) >= p,
          f"applied {p} <= FY2025 ceiling $3.70/gal over 181.7 mi = {per_gallon_over_distance(3.70, 181.7):.4f}")
    check("plane.in_documented_range", ranges["Plane"][0] <= p <= ranges["Plane"][1],
          f"{p} in {ranges['Plane']}")

    # --- Ice road: assumed; kept between the two regimes --------------------
    i = rates["IceRoad"]
    truck, sled = 0.0068, 0.0256
    check("iceroad.between_regimes", truck <= i <= sled,
          f"applied {i} between truck regime {truck} and sled regime {sled}")
    check("iceroad.status_assumed", status["IceRoad"] == "assumed",
          f"regimes differ {sled / truck:.1f}x and no tariff exists -> status {status['IceRoad']!r}")
    check("iceroad.in_documented_range", ranges["IceRoad"][0] <= i <= ranges["IceRoad"][1],
          f"{i} in {ranges['IceRoad']}")

    # --- Transfer fees and landing classes ---------------------------------
    for key, entry in fees.items():
        lo, hi = entry["range"]
        check(f"fee.{key}.in_range", lo <= entry["total"] <= hi,
              f"total {entry['total']} in ({lo}, {hi})")
    for key, entry in landing.items():
        lo, hi = entry["range"]
        check(f"landing.{key}.in_range", lo <= entry["total"] <= hi,
              f"total {entry['total']} in ({lo}, {hi})")
    port = (20.49 + 6.08 + 14.0) / 100 / 42          # Port of Alaska Tariff 10.2, cents per barrel -> $/gal
    check("landing.road_port.reproduces", abs(landing["road_port"]["total"] - port) < 0.005,
          f"wharfage + valve yard + surcharge = {port:.4f} $/gal vs applied {landing['road_port']['total']}")
    check("landing.hub.reproduces", abs(landing["hub"]["total"] - (0.06 + 0.06)) < 1e-9,
          f"Bethel wharfage 0.06 + fuel transfer 0.06 = 0.12 vs applied {landing['hub']['total']}")
    assembled = 0.45 + 0.0010 * 250 - rates["Barge"] * 250
    check("landing.coastal_village.assembly_reproduces",
          abs(landing["coastal_village"]["total"] - assembled) < 0.01,
          f"0.45 + 0.0010 x 250 mi - ocean rate x 250 mi = {assembled:.3f} vs applied {landing['coastal_village']['total']}")
    mix = (0.21 * (landing["road_port"]["total"] + landing["hub"]["total"]) + 0.79 * 0.055) / 2
    fee_bo = fees[("barge", "overland")]["total"]
    check("fee.barge_overland.fallback_reproduces", abs(fee_bo - mix) / mix < 0.20,
          f"single-key fallback {fee_bo} vs gallon-mix value {mix:.3f} per crossing")
    rack_2026 = cpi_adjust(0.25, 2022)       # Crowley Bethel truck rack, list price
    check("fee.truck_rack_not_base_case", fee_bo < rack_2026 and landing["hub"]["total"] < rack_2026,
          f"no landing fee equals the truck-rack list price {rack_2026:.3f} (it prices a different event)")

    print(f"\n{len(failures)} failure(s)" if failures else "\nAll derivations reproduce.")
    return len(failures)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(1 if selftest() else 0)
    print(__doc__)
