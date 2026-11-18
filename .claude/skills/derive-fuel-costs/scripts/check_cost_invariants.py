# -*- coding: utf-8 -*-
"""check_cost_invariants.py — mechanical audit of the fuel-cost model.

Run after ANY change to source_scripts/friction_surface/friction_costs.py rates, fees, or
mode metadata:

    python .claude/skills/derive-fuel-costs/scripts/check_cost_invariants.py

Checks (FAIL = exit 1; WARN/SKIP never fail the run):

  1. Every baseline rate lies inside its BASELINE_RATE_RANGES band, and
     the two dicts cover exactly the same rate keys.
  2. Fee-table schema: every INTERMODAL_TRANSFER_FEES entry keys a 2-tuple
     of canonical modes {overland, barge, ice_road, plane}, carries
     total/counts/range, total > 0 (no costless edge) and inside range,
     and no pair appears in both key orders (direction-insensitive lookup
     would silently shadow one).
  3. Mode metadata coherence: MODE_METADATA rate keys == baseline rate
     keys; METHOD_TO_MODE / RATE_KEY_BY_MODE round-trip; DEFAULT_REPR_MONTHS
     is exactly all modes minus plane; VEHICLE_MILE_RATES_REFERENCE covers
     the same rate keys.
  4. Derived constants (connector/plane/pixel) still equal their sources —
     catches a rate edit that skipped a downstream alias.
  5. chain_cost_with_transfer_fees smoke test charges the right fee.
  6. Graph fee coverage: every live Transfer edge in outputs/fuel_network.duckdb
     resolves to a fee via the production infer_transfer_fees() — the
     no-unpriced-modal-boundary rule, checked against the real network
     rather than the latent-key comment. SKIPs if the db is absent.
  7. Published workbook freshness: WARN if modality_cost_rates.xlsx is
     older than friction_costs.py (regenerate via make_modality_cost_table).
  8. Evidence status and landing classes (2026-11): every rate has a
     RATE_STATUS in {derived, provisional, assumed}; every rate key is a mode's
     rate key or a declared variant (RATE_VARIANTS); LANDING_CLASS_FEES has
     total/counts/range/status with total inside range; every class named in
     inputs/network_qc/landing_classes.csv is a LANDING_CLASS_FEES key.
"""
from __future__ import annotations

import sys

import repo_paths as rp
REPO_ROOT = rp.ROOT

from friction_surface import friction_costs as fc  # noqa: E402

CANONICAL_MODES = {"overland", "barge", "ice_road", "plane"}
RESULTS = []


def record(status, name, detail):
    RESULTS.append((status, name, detail))
    print(f"{status:5s} {name} — {detail}")


def check(name, ok, detail):
    record("PASS" if ok else "FAIL", name, detail)


# --- 1. rates in ranges ----------------------------------------------------

def check_rate_ranges():
    rates, ranges = fc.BASELINE_RATES_PER_GALLON_MILE, fc.BASELINE_RATE_RANGES
    check("rates.keys_match_ranges", set(rates) == set(ranges),
          f"rates {sorted(rates)} vs ranges {sorted(ranges)}")
    for key, rate in rates.items():
        lo, hi = ranges.get(key, (float("nan"),) * 2)
        check(f"rates.{key}.in_range", lo <= rate <= hi,
              f"{rate} in ({lo}, {hi})")


# --- 2. fee schema ---------------------------------------------------------

def check_fee_schema():
    fees = fc.INTERMODAL_TRANSFER_FEES
    seen = set()
    for key, entry in fees.items():
        ok_key = (isinstance(key, tuple) and len(key) == 2
                  and set(key) <= CANONICAL_MODES and key[0] != key[1])
        check(f"fees.{key}.key_canonical", ok_key,
              f"2-tuple of {sorted(CANONICAL_MODES)}")
        check(f"fees.{key}.schema", {"total", "counts", "range"} <= set(entry),
              "has total/counts/range")
        total = entry.get("total", -1)
        check(f"fees.{key}.no_costless_edge", total > 0, f"total {total} > 0")
        if "range" in entry:
            lo, hi = entry["range"]
            check(f"fees.{key}.in_range", lo <= total <= hi,
                  f"{total} in ({lo}, {hi})")
        pair = frozenset(key)
        check(f"fees.{key}.no_reversed_duplicate", pair not in seen,
              "one key order per modal boundary")
        seen.add(pair)


# --- 3. mode metadata ------------------------------------------------------

def check_mode_metadata():
    meta = fc.MODE_METADATA
    rate_keys = {m["rate_key"] for m in meta.values()}
    variants = {k for keys in fc.RATE_VARIANTS.values() for k in keys}
    check("meta.rate_keys_cover_rates",
          rate_keys | variants == set(fc.BASELINE_RATES_PER_GALLON_MILE)
          and rate_keys <= set(fc.BASELINE_RATES_PER_GALLON_MILE),
          f"mode keys {sorted(rate_keys)} + variants {sorted(variants - rate_keys)}")
    check("meta.rate_variants_name_modes",
          set(fc.RATE_VARIANTS) <= set(meta)
          and all(meta[m]["rate_key"] in keys for m, keys in fc.RATE_VARIANTS.items()),
          f"{fc.RATE_VARIANTS}")
    check("meta.modes_canonical", set(meta) == CANONICAL_MODES, f"{sorted(meta)}")
    check("meta.method_to_mode_roundtrip",
          all(fc.METHOD_TO_MODE[m["facility_method"]] == mode
              for mode, m in meta.items()),
          "facility_method inverts cleanly")
    check("meta.rate_key_by_mode",
          all(fc.RATE_KEY_BY_MODE[mode] == m["rate_key"]
              for mode, m in meta.items()),
          "consistent with MODE_METADATA")
    check("meta.repr_months_exclude_plane",
          set(fc.DEFAULT_REPR_MONTHS) == CANONICAL_MODES - {"plane"},
          f"{sorted(fc.DEFAULT_REPR_MONTHS)}")
    check("meta.vehicle_mile_reference_keys",
          set(fc.VEHICLE_MILE_RATES_REFERENCE)
          == set(fc.BASELINE_RATES_PER_GALLON_MILE),
          "reference table covers every rate key")


# --- 4. derived constants --------------------------------------------------

def check_derived_constants():
    rates = fc.BASELINE_RATES_PER_GALLON_MILE
    check("derived.connector_rate",
          fc.CONNECTOR_COST_PER_GALLON_MILE_USD == rates["Road"],
          "connector == Road rate")
    check("derived.plane_rate",
          fc.PLANE_COST_PER_GALLON_MILE_USD == rates["Plane"],
          "plane alias == Plane rate")
    check("derived.plane_handling",
          fc.PLANE_HANDLING_COST_PER_GALLON_USD
          == fc.INTERMODAL_TRANSFER_FEES[("plane", "overland")]["total"],
          "handling alias == (plane, overland) fee")
    from friction_surface.friction_config import METERS_PER_MILE, TARGET_RESOLUTION
    for name, key in (("overland", "Road"), ("barge", "Barge")):
        expected = rates[key] / METERS_PER_MILE * TARGET_RESOLUTION
        actual = getattr(fc, f"{name.upper()}_COST_PER_GALLON_PIXEL_USD")
        check(f"derived.{name}_pixel", abs(actual - expected) < 1e-12,
              f"{actual} == rate/mile*{TARGET_RESOLUTION}m")


# --- 5. chain-cost smoke ---------------------------------------------------

def check_chain_cost():
    fee = fc.INTERMODAL_TRANSFER_FEES[("barge", "overland")]["total"]
    got = fc.chain_cost_with_transfer_fees([("Barge", 1.0), ("Road", 0.5)])
    check("chain.barge_to_road", abs(got - (1.5 + fee)) < 1e-12,
          f"{got} == 1.5 + fee {fee} (Road normalizes to overland)")


# --- 6. graph coverage -----------------------------------------------------

def check_graph_coverage():
    db = rp.DUCKDB
    if not db.exists():
        record("SKIP", "graph.fee_coverage", "outputs/fuel_network.duckdb not found")
        return
    try:
        import duckdb
        from friction_surface.friction_costs import FEE_MODE, infer_transfer_fees
    except ImportError as exc:
        record("SKIP", "graph.fee_coverage", f"import failed: {exc}")
        return
    con = duckdb.connect(str(db), read_only=True)
    try:
        edges = con.execute(
            "SELECT edge_id, from_node, to_node, edge_class FROM network_edges"
        ).df()
    finally:
        con.close()
    line_classes = set(edges.loc[edges["edge_class"] != "Transfer", "edge_class"])
    unmapped = line_classes - set(FEE_MODE)
    check("graph.edge_classes_mapped", not unmapped,
          f"unmapped line-haul edge_class values: {sorted(unmapped) or 'none'}")
    try:
        fees = infer_transfer_fees(edges)
        n = int((edges["edge_class"] == "Transfer").sum())
        check("graph.fee_coverage", len(fees) == n,
              f"all {n} Transfer edges priced by INTERMODAL_TRANSFER_FEES")
    except (KeyError, ValueError) as exc:
        check("graph.fee_coverage", False, str(exc))


# --- 7. workbook freshness -------------------------------------------------

def check_workbook_freshness():
    wb = rp.TABLES / "modality_cost_rates.xlsx"
    src = REPO_ROOT / "friction_surface" / "friction_costs.py"
    if not wb.exists():
        record("SKIP", "workbook.freshness", f"{wb.name} not built yet")
        return
    if wb.stat().st_mtime < src.stat().st_mtime:
        record("WARN", "workbook.freshness",
               "modality_cost_rates.xlsx older than friction_costs.py — "
               "rerun outputs/tables/make_modality_cost_table.py")
    else:
        record("PASS", "workbook.freshness", "workbook newer than source")


# --- 8. evidence status and landing classes ---------------------------------

def check_status_and_landings():
    statuses = {"derived", "provisional", "assumed"}
    check("status.covers_rates", set(fc.RATE_STATUS) == set(fc.BASELINE_RATES_PER_GALLON_MILE),
          f"{sorted(fc.RATE_STATUS)}")
    check("status.vocabulary", set(fc.RATE_STATUS.values()) <= statuses,
          f"{sorted(set(fc.RATE_STATUS.values()))} within {sorted(statuses)}")
    for key, entry in fc.LANDING_CLASS_FEES.items():
        check(f"landing.{key}.schema", {"total", "counts", "range", "status"} <= set(entry),
              "has total/counts/range/status")
        lo, hi = entry["range"]
        check(f"landing.{key}.in_range", lo <= entry["total"] <= hi and entry["total"] > 0,
              f"{entry['total']} in ({lo}, {hi}) and > 0")
    try:
        from fuel_network.landings import TABLE_PATH, load_landing_table
        table = load_landing_table()
        check("landing.table_classes_known", set(table.values()) <= set(fc.LANDING_CLASS_FEES),
              f"{len(table)} place(s) in {TABLE_PATH.name}: {sorted(set(table.values()))}")
    except ValueError as exc:
        check("landing.table_classes_known", False, str(exc))
    fee = fc.infer_transfer_fees
    import pandas as pd
    e = pd.DataFrame({"edge_id": [1, 2], "from_node": [0, 0], "to_node": [1, 1],
                      "edge_class": ["BargeRoadTransfer", "BargeAirTransfer"]})
    got = fee(e, {1: "hub"}).to_dict()
    check("landing.fee_inference", got == {1: fc.LANDING_CLASS_FEES["hub"]["total"],
                                           2: fc.INTERMODAL_TRANSFER_FEES[("barge", "overland")]["total"]},
          f"classed landing -> class fee, unclassed -> fallback: {got}")


def main() -> int:
    for fn in (check_rate_ranges, check_fee_schema, check_mode_metadata,
               check_derived_constants, check_chain_cost,
               check_graph_coverage, check_workbook_freshness,
               check_status_and_landings):
        fn()
    fails = [r for r in RESULTS if r[0] == "FAIL"]
    warns = [r for r in RESULTS if r[0] == "WARN"]
    print(f"\n{len(RESULTS)} checks: {len(fails)} FAIL, {len(warns)} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
