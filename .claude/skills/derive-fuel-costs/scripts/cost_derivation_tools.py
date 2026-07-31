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
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]

# ===========================================================================
# CPI (dollar-year discipline)
# ===========================================================================
# CPI-U annual averages (U.S. city average, all items, BLS series
# CUUR0000SA0). 2025 is a preliminary annual average; 2026 is a projection
# (~2.5% over 2025) — the project's canonical 2010->2026 factor is x1.51
# (see friction_costs.py barge comment), which this table reproduces
# (330.0 / 218.056 = 1.514). When BLS publishes finals, update here ONLY.
CPI_U_ANNUAL = {
    2005: 195.3,   2006: 201.6,   2007: 207.342, 2008: 215.303,
    2009: 214.537, 2010: 218.056, 2011: 224.939, 2012: 229.594,
    2013: 232.957, 2014: 236.736, 2015: 237.017, 2016: 240.007,
    2017: 245.120, 2018: 251.107, 2019: 255.657, 2020: 258.811,
    2021: 270.970, 2022: 292.655, 2023: 304.702, 2024: 313.689,
    2025: 322.6,   2026: 330.0,
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
    sys.path.insert(0, str(REPO_ROOT))
    from friction_surface import friction_costs as fc
    return fc


def selftest() -> int:
    """Re-derive each applied rate/fee from documented inputs; return #failures.

    Method inputs are cited from
    supplementary/cost-derivations/00_executive_summary.md and the
    friction_costs.py comment blocks. A failure means the code
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

    # --- Road: three convergent methods bracket the applied 0.0007 ---------
    road_methods = {
        "econ_one_valdez_fbx": cpi_adjust(0.20, 2015) / 364,       # $0.20/gal, 364 mi
        "contract_regression_slope": 0.00067,                       # 11 pts, R2~0.75
        "tariff_midpoint": gallon_mile_rate(4.75, 9000),            # AK heavy transport
    }
    conv = convergence(road_methods)
    r = rates["Road"]
    check("road.methods_bracket_applied",
          conv["min"][1] <= r <= conv["max"][1] * 1.05,
          f"applied {r} vs methods [{conv['min'][1]:.6f}, {conv['max'][1]:.6f}]")
    check("road.in_documented_range", ranges["Road"][0] <= r <= ranges["Road"][1],
          f"{r} in {ranges['Road']}")

    # --- Barge: decomposition endpoints reproduce; blend sits between ------
    linehaul = per_gallon_over_distance(0.29, nm_to_statute(1109))  # ANC->Bethel
    river = cpi_adjust(0.007, 2007)                                 # DEC 2007 invoice
    b = rates["Barge"]
    check("barge.linehaul_reproduces", abs(linehaul - 0.00023) / 0.00023 < 0.05,
          f"0.29/gal over {nm_to_statute(1109):.0f} sm = {linehaul:.6f} (doc 0.00023)")
    check("barge.river_reproduces", abs(river - 0.011) / 0.011 < 0.05,
          f"$0.007/gal-mi (2007$) x CPI = {river:.4f} (doc 0.011)")
    check("barge.blend_between_endpoints", linehaul < b < river,
          f"blended {b} between linehaul {linehaul:.6f} and river {river:.4f}")
    check("barge.in_documented_range", ranges["Barge"][0] <= b <= ranges["Barge"][1],
          f"{b} in {ranges['Barge']}")

    # --- Plane: charter award reproduces the applied rate at stage length --
    charter_per_gal = 11792.50 / 1400          # exact federal charter award
    p = rates["Plane"]
    lo = per_gallon_over_distance(charter_per_gal, 350)   # long stage
    hi = per_gallon_over_distance(charter_per_gal, 130)   # short stage
    check("plane.charter_award_brackets",
          lo * 0.95 <= p <= hi,
          f"${charter_per_gal:.2f}/gal over 130-350 mi -> [{lo:.4f}, {hi:.4f}], applied {p}")
    check("plane.in_documented_range", ranges["Plane"][0] <= p <= ranges["Plane"][1],
          f"{p} in {ranges['Plane']}")

    # --- Ice road: 50/50 regime blend per PCE FY2025 gallons ---------------
    i = rates["IceRoad"]
    regime_blend = blend([(0.004, 279_232), (0.02, 274_877)])  # Nuiqsut / Atqasuk
    check("iceroad.between_regimes", 0.004 <= i <= 0.02,
          f"applied {i} between engineered 0.004 and cat-train 0.02")
    check("iceroad.near_traffic_blend", abs(i - regime_blend) / regime_blend < 0.25,
          f"applied {i} vs PCE-weighted blend {regime_blend:.4f} (known ~2x per-regime bias)")
    check("iceroad.in_documented_range", ranges["IceRoad"][0] <= i <= ranges["IceRoad"][1],
          f"{i} in {ranges['IceRoad']}")

    # --- Transfer fees: totals inside documented ranges; rack fee <= CPI'd -
    for key, entry in fees.items():
        lo, hi = entry["range"]
        check(f"fee.{key}.in_range", lo <= entry["total"] <= hi,
              f"total {entry['total']} in ({lo}, {hi})")
    rack_2026 = 0.276  # Crowley Bethel rack $0.25 CPI-adjusted (doc value)
    fee_bo = fees[("barge", "overland")]["total"]
    check("fee.barge_overland.shaded_below_rack", fee_bo <= rack_2026,
          f"{fee_bo} <= CPI-adjusted rack {rack_2026} (sole-provider shading)")

    print(f"\n{len(failures)} failure(s)" if failures else "\nAll derivations reproduce.")
    return len(failures)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(1 if selftest() else 0)
    print(__doc__)
