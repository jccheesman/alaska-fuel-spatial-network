#!/usr/bin/env python3
"""Stage 00 — normalize the heterogeneous raw data into a uniform `data/interim/` layer.

Each raw file (3 CRS, mixed geometry, dozens of junk columns) becomes a clean canonical file:
**EPSG:3338**, canonical column names, GeoPackage for vectors / CSV for tables. The pipeline then
reads these uniform inputs (the profile points at `data/interim/`); the loaders' own cleaning stays
as an idempotent safety net.

Scope = file-local standardization only (reproject + clean geometry + select/rename + write).
Pipeline-coupled transforms stay where they belong: the waterways bbox-clip (the loaders), and the
airways geocoding + boundary dissolve (`workflows/02_network_build/02_prep_airways.py`).

Writes `data/interim/<name>.{gpkg,csv}` + `data/interim/MANIFEST.md`.

Usage:
    python workflows/02_network_build/00_normalize_raw.py
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import repo_paths as rp
ROOT = rp.ROOT

import geopandas as gpd
import pandas as pd
import pyogrio

from mmnet.io_readers import _read_lines  # reuse the pipeline's line cleaning

TARGET_CRS = 3338
RAW = rp.RAW
INTERIM = rp.INTERIM
QC_OUT = rp.INVENTORY_QC_OUT
QC_DERIVED = rp.INVENTORY_QC / "derived_columns.csv"
# Owner-reviewed anchor points that take no part in the build (layer, column, value, reason, ...).
# The landing rules are universal (every port and barge hub gets a transfer to the nearest
# waterway node within reach); where one anchor makes a link that is not real, the fix is a
# reviewed row here, not a change to the rule.
EXCLUDED_ANCHORS = rp.INPUTS / "network_qc" / "excluded_anchors.csv"
EXCLUSION_STATUSES = ("approved", "retired")


def _derived_columns() -> list[str]:
    """Every derived column workflow 00 declares (inputs/inventory_qc/derived_columns.csv) rides into
    the interim facilities table, so a new QC variable reaches the build without an edit here."""
    return list(pd.read_csv(QC_DERIVED, dtype=str)["name"]) if QC_DERIVED.exists() else []


FACILITIES_HINT = ("no published facility table under outputs/00_inventory_qc/<release>/ — "
                   "run workflows/00_inventory_qc/run_all.sh (skill: validate-facility-inventory)")


def _published_facilities() -> Path:
    """Latest published clean facility table (workflow 00): the highest release label that has one.
    When none exists the returned path does not exist, so the entry reports MISSING + FACILITIES_HINT."""
    rels = sorted(p.name for p in QC_OUT.glob("*") if (p / "facilities_clean.csv").exists()) if QC_OUT.exists() else []
    return QC_OUT / (rels[-1] if rels else "latest") / "facilities_clean.csv"

# One entry per raw file. kind: line | point | polygon | table. rename: raw -> canonical.
# `keep` (tables) limits/order columns; `filter` (tables) is an optional (col, value) row filter.
SPEC = [
    # --- facilities inventory (table) ---
    # The facility inventory comes from workflow 00 (inventory QC): the owner-corrected,
    # normalised, published table for the latest release — never the raw AEA CSV directly.
    # Column names are already the clean schema; only the profile's logical names are renamed.
    {"name": "facilities", "kind": "table", "status": "used (inventory) — from workflow 00",
     "src": _published_facilities(),
     "rename": {"ast_facility_id": "id", "community_name": "community", "entity_name": "entity"},
     "keep": ["id", "record_id", "community", "entity", "delivery_method",
              "total_capacity", "gasoline_capacity", "diesel_capacity", "jet_fuel_capacity",
              "other_fuel_capacity", "latitude", "longitude", *_derived_columns()]},
    # --- transport lines ---
    # The ONLY road source (2026-09-07 AK DOT&PF download, 26,650 features).
    # The GRIP4 Canada extra/border-stitch layer was removed 2026-09-15:
    # transnational roads are not fuel-delivery routes.
    {"name": "roads_akdot", "kind": "line", "status": "used (roads)",
     "src": RAW / "connectivity" / "road" / "Roads_AKDOT" / "Roads_AKDOT.shp",
     "rename": {"Route_ID": "route_id", "Route_Name": "route_name"}},
    {"name": "waterways", "kind": "line", "status": "used (barge)",
     "src": RAW / "connectivity" / "barge" / "NWN_Waterway_Network_Lines" / "Waterway_Network.shp",
     "rename": {"WATERWAY": "waterway_id", "LINKNAME": "name"}},
    {"name": "ice_roads", "kind": "line", "status": "used (ice road)",
     "src": RAW / "connectivity" / "ice_roads" / "ice_roads_150m_3338" / "Ice_Roads.shp",
     "rename": {"Name": "name", "STATUS": "status", "Length_mi": "length_mi"}},
    # --- anchor points ---
    {"name": "ports", "kind": "point", "status": "used (barge anchor)",
     "src": RAW / "anchor_points" / "Ports_and_Harbors.geojson",
     "rename": {"Location": "location", "Region": "region", "Facility": "facility"}},
    # --- tagging polygons ---
    {"name": "tiger_places", "kind": "polygon", "status": "used (place tagging)",
     "src": RAW / "boundaries" / "tiger_places" / "tl_2022_02_place.shp",
     "rename": {"NAME": "place_name", "GEOID": "place_geoid"}},
    {"name": "boroughs", "kind": "polygon", "status": "used (region tagging + boundary)",
     "src": RAW / "boundaries" / "borough_census_area" / "Alaska_Borough_and_Census_Area_Boundaries.shp",
     "rename": {"CommunityN": "region_name", "EconomicRe": "economic_region"}},
    # --- air tables (OFFICIAL Flights data: the AK DOT&PF airport registry + the matched OD legs).
    #     These two CSVs are TRACKED at inputs/air/ (small, diffable) rather than
    #     living in the gitignored data/raw tree — the merge moved them there. ---
    {"name": "airports", "kind": "table", "status": "used (air geocoding) — AK DOT&PF registry",
     "src": rp.AIR_INPUTS / "airports_ak_dotpf.csv",
     "rename": {"NAME": "name", "LAT_DD": "latitude_deg", "LONG_DD": "longitude_deg",
                "FAA_ID": "iata_code", "ICAO": "ident", "REGION": "region", "OWNER": "owner"},
     "keep": ["name", "latitude_deg", "longitude_deg", "iata_code", "ident", "region", "owner"]},
    {"name": "air_flight_paths_od", "kind": "table", "status": "used (air OD) — official Flights data",
     "src": rp.AIR_INPUTS / "flight_paths_combined.csv",
     "rename": {"Origin_Airport_Name": "origin_node", "Origin_FAA_ID": "origin_code",
                "Destination_Airport_Name": "destination_node", "Destination_FAA_ID": "destination_code",
                "Carrier": "primary_carrier", "Notes": "service_type"},
     "keep": ["origin_node", "origin_code", "destination_node", "destination_code",
              "primary_carrier", "service_type"]},
    # --- present but NOT consumed by the current build (normalized for completeness) ---
    {"name": "tiger_county_subdivisions", "kind": "polygon", "status": "unused",
     "src": RAW / "boundaries" / "tiger_county_subdivisions" / "tl_2022_02_cousub.shp",
     "rename": {"NAME": "name", "GEOID": "geoid"}},
    {"name": "fuel_delivery_method", "kind": "point", "status": "used (delivery-method fallback)",
     "src": RAW / "boundaries" / "Fuel_Delivery_Method.geojson",
     "rename": {"CommunityName": "community", "Fuel_Delivery_Method": "delivery_method"}},
]


def _src_crs(src: Path) -> str:
    try:
        return str(pyogrio.read_info(src).get("crs"))
    except Exception:  # noqa: BLE001
        return "n/a"


def _select_rename_vec(g: gpd.GeoDataFrame, rename: dict) -> gpd.GeoDataFrame:
    cols = [c for c in rename if c in g.columns]
    out = g[cols + ["geometry"]].rename(columns=rename) if cols else g[["geometry"]].copy()
    return gpd.GeoDataFrame(out, geometry="geometry", crs=g.crs)


def load_anchor_exclusions(path: Path | None = None) -> dict[str, list[tuple[str, str]]]:
    """layer -> [(column, value)] of the APPROVED rows. Absent file = no exclusions.
    A row needs a reason, a reviewer and a date; `retired` rows are kept as history and ignored."""
    import csv
    path = EXCLUDED_ANCHORS if path is None else path
    out: dict[str, list[tuple[str, str]]] = {}
    if not path.exists():
        return out
    with open(path, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            status = (row.get("status") or "").strip().lower()
            if status not in EXCLUSION_STATUSES:
                raise SystemExit(f"{path.name} line {i}: status {status!r} is not one of {EXCLUSION_STATUSES}")
            if not all((row.get(k) or "").strip() for k in ("layer", "column", "value", "reason", "reviewer", "date")):
                raise SystemExit(f"{path.name} line {i}: layer, column, value, reason, reviewer and date are all required")
            if status == "approved":
                out.setdefault(row["layer"].strip(), []).append((row["column"].strip(), row["value"].strip()))
    return out


def apply_anchor_exclusions(g: gpd.GeoDataFrame, layer: str, exclusions: dict | None = None) -> tuple[gpd.GeoDataFrame, list[str]]:
    """Drop the reviewed anchors of `layer`. A row that matches nothing stops the stage: the
    publisher renamed or removed the anchor, so the row is stale and must be retired, not ignored."""
    exclusions = load_anchor_exclusions() if exclusions is None else exclusions
    dropped: list[str] = []
    for col, val in exclusions.get(layer, []):
        if col not in g.columns:
            raise SystemExit(f"excluded_anchors.csv: layer {layer!r} has no column {col!r} (columns: {list(g.columns)})")
        hit = g[col].astype(str).str.strip() == val
        if not hit.any():
            raise SystemExit(f"excluded_anchors.csv: no {layer} anchor has {col} = {val!r}; "
                             "retire the row (status=retired) if the publisher changed it")
        dropped.append(f"{col}={val} ({int(hit.sum())})")
        g = g[~hit]
    return g.reset_index(drop=True), dropped


def normalize_entry(e: dict) -> dict:
    src, name, kind = e["src"], e["name"], e["kind"]
    if not src.exists():
        return {**e, "rows": 0, "out": None, "src_crs": "MISSING", "columns": []}

    if kind == "table":
        df = pd.read_csv(src, low_memory=False, encoding="utf-8-sig")
        if "filter" in e:
            col, val = e["filter"]
            df = df[df[col] == val]
        if e.get("rename"):
            df = df.rename(columns=e["rename"])
        if e.get("keep"):
            df = df[[c for c in e["keep"] if c in df.columns]]
        out = INTERIM / f"{name}.csv"
        df.to_csv(out, index=False)
        return {**e, "rows": len(df), "out": out, "src_crs": "n/a (table)", "columns": list(df.columns)}

    src_crs = _src_crs(src)
    if kind == "line":
        g = _read_lines(src, TARGET_CRS)                       # reproject + force_2d + explode + clean
        g = _select_rename_vec(g, e["rename"])
    else:  # point / polygon
        g = gpd.read_file(src).to_crs(TARGET_CRS)
        g = g[g.geometry.notna() & ~g.geometry.is_empty]
        if kind == "point":
            g = g[g.geometry.geom_type.isin(["Point", "MultiPoint"])]
        g = _select_rename_vec(g, e["rename"]).reset_index(drop=True)

    excluded: list[str] = []
    if kind == "point":
        g, excluded = apply_anchor_exclusions(g, name)
        if excluded:
            print(f"   {name}: excluded by inputs/network_qc/excluded_anchors.csv: {', '.join(excluded)}")
    out = INTERIM / f"{name}.gpkg"
    g.to_file(out, driver="GPKG")
    return {**e, "rows": len(g), "out": out, "src_crs": src_crs, "columns": list(g.columns), "excluded": excluded}


def _refresh_manifest_rows(rows: list[dict]) -> None:
    """--only: rewrite just these layers' rows in an existing MANIFEST.md, leaving the rest."""
    man = INTERIM / "MANIFEST.md"
    if not man.exists():
        return
    text = man.read_text()
    for r in rows:
        outname = r["out"].name if r["out"] else "—"
        cols = ", ".join(c for c in r["columns"] if c != "geometry") or "(geometry only)"
        line = (f"| `{r['name']}` | {r['status']} | {r['src_crs']} | {r['rows']} | "
                f"`{outname}` | {cols} |")
        text = re.sub(rf"^\| `{re.escape(r['name'])}` \|.*$", lambda _m: line, text, count=1, flags=re.M)
    man.write_text(text)


def main(argv: list[str] | None = None) -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--only", nargs="+", metavar="NAME",
                    help="normalize only these SPEC entries (e.g. facilities) and update their "
                         "MANIFEST rows; the other interim layers are left as they are")
    args = ap.parse_args(argv)
    INTERIM.mkdir(parents=True, exist_ok=True)
    spec = SPEC
    if args.only:
        names = {e["name"] for e in SPEC}
        unknown = sorted(set(args.only) - names)
        if unknown:
            raise SystemExit(f"--only: no SPEC entry named {unknown}; known: {sorted(names)}")
        spec = [e for e in SPEC if e["name"] in args.only]
    rows = []
    for e in spec:
        r = normalize_entry(e)
        flag = "·" if r["out"] else "MISSING"
        print(f"  {flag} {r['name']:<28} {r['rows']:>6} rows  {r['src_crs']:<14} -> "
              f"{(r['out'].name if r['out'] else '—')}")
        if r["name"] == "facilities" and not r["out"]:
            print(f"    ! {FACILITIES_HINT}")
        rows.append(r)
    if args.only:
        # A layer asked for by name is one whose owner-edited inputs must reach this build. If its raw
        # source is gone while an earlier data/interim copy is still there, the build would quietly use
        # that copy, without the reviewed exclusions. Stop instead.
        stale = [r["name"] for r in rows if not r["out"] and r["name"] != "facilities"
                 and load_anchor_exclusions().get(r["name"])]
        if stale:
            raise SystemExit(f"--only {' '.join(stale)}: the raw source is missing, so the reviewed exclusions in "
                             f"{EXCLUDED_ANCHORS.relative_to(ROOT)} cannot be applied; restore data/raw "
                             "(tools/extract_inputs.py) before building")
        _refresh_manifest_rows(rows)
        print(f"\nrefreshed {', '.join(args.only)} in {INTERIM.relative_to(ROOT)}/")
        return

    lines = ["# data/interim — normalized inputs (MANIFEST)", "",
             f"Generated by `workflows/02_network_build/00_normalize_raw.py`. All vectors are **EPSG:{TARGET_CRS}**.", "",
             "| layer | status | src CRS | rows | output | columns |",
             "| --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        src_rel = Path(r["src"]).relative_to(ROOT)
        outname = r["out"].name if r["out"] else "—"
        cols = ", ".join(c for c in r["columns"] if c != "geometry") or "(geometry only)"
        lines.append(f"| `{r['name']}` | {r['status']} | {r['src_crs']} | {r['rows']} | "
                     f"`{outname}` | {cols} |")
        lines.append(f"|  | _src:_ `{src_rel}` |  |  |  |  |")
    (INTERIM / "MANIFEST.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {len(rows)} layers + MANIFEST.md -> {INTERIM.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
