#!/usr/bin/env python3
"""Stage 00 — normalize the heterogeneous raw data into a uniform `data/interim/` layer.

Each raw file (3 CRS, mixed geometry, dozens of junk columns) becomes a clean canonical file:
**EPSG:3338**, canonical column names, GeoPackage for vectors / CSV for tables. The pipeline then
reads these uniform inputs (the profile points at `data/interim/`); the loaders' own cleaning stays
as an idempotent safety net.

Scope = file-local standardization only (reproject + clean geometry + select/rename + write).
Pipeline-coupled transforms stay where they belong: waterways bbox-clip and the GRIP4 border-stitch
(the loaders), and the airways geocoding + boundary dissolve (`workflows/02_network_build/02_prep_airways.py`).

Writes `data/interim/<name>.{gpkg,csv}` + `data/interim/MANIFEST.md`.

Usage:
    python workflows/02_network_build/00_normalize_raw.py
"""

from __future__ import annotations

import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]  # repo root

import geopandas as gpd
import pandas as pd
import pyogrio

from mmnet.io_readers import _read_lines  # reuse the pipeline's line cleaning

TARGET_CRS = 3338
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"

# One entry per raw file. kind: line | point | polygon | table. rename: raw -> canonical.
# `keep` (tables) limits/order columns; `filter` (tables) is an optional (col, value) row filter.
SPEC = [
    # --- facilities inventory (table) ---
    {"name": "facilities", "kind": "table", "status": "used (inventory)",
     "src": RAW / "facilities" / "Utilities_Bulk_Fuel_Inventory.csv",
     "rename": {"ASTFacilityID": "id", "CommunityName": "community",
                "Delivery_method": "delivery_method", "Total_Capacity": "total_capacity",
                "Gasoline_Capacity": "gasoline_capacity", "Diesel_Capacity": "diesel_capacity",
                "AV_Gas_Capacity": "av_gas_capacity", "Jet_Fuel_Capacity": "jet_fuel_capacity",
                "Other_Fuel_Capacity": "other_fuel_capacity", "EntityName": "entity",
                "ASTFacilityLongitude": "longitude", "ASTFacilityLatitude": "latitude"}},
    # --- transport lines ---
    {"name": "roads_akdot", "kind": "line", "status": "used (roads)",
     "src": RAW / "connectivity" / "road" / "Roads_AKDOT" / "Roads_AKDOT.shp",
     "rename": {"Route_ID": "route_id", "Route_Name": "route_name"}},
    {"name": "roads_grip4", "kind": "line", "status": "used (roads extra / border-stitch)",
     "src": RAW / "connectivity" / "road" / "GRIP4_canada" / "Export_Alaska_Roads_grip4.shp",
     "rename": {}},
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
     "src": ROOT / "inputs" / "air" / "airports_ak_dotpf.csv",
     "rename": {"NAME": "name", "LAT_DD": "latitude_deg", "LONG_DD": "longitude_deg",
                "FAA_ID": "iata_code", "ICAO": "ident", "REGION": "region", "OWNER": "owner"},
     "keep": ["name", "latitude_deg", "longitude_deg", "iata_code", "ident", "region", "owner"]},
    {"name": "air_flight_paths_od", "kind": "table", "status": "used (air OD) — official Flights data",
     "src": ROOT / "inputs" / "air" / "flight_paths_combined.csv",
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

    out = INTERIM / f"{name}.gpkg"
    g.to_file(out, driver="GPKG")
    return {**e, "rows": len(g), "out": out, "src_crs": src_crs, "columns": list(g.columns)}


def main() -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)
    rows = []
    for e in SPEC:
        r = normalize_entry(e)
        flag = "·" if r["out"] else "MISSING"
        print(f"  {flag} {r['name']:<28} {r['rows']:>6} rows  {r['src_crs']:<14} -> "
              f"{(r['out'].name if r['out'] else '—')}")
        rows.append(r)

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
