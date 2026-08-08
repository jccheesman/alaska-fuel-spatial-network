#!/usr/bin/env python3
"""Build the air-mode line layer (and an Alaska basemap boundary) for the mmnet build.

The Alaska air mode arrives as an origin-destination CODE list plus an airport
coordinate table. The raw sources are the official AK DOT&PF data at
inputs/air/ (flight_paths_combined.csv + airports_ak_dotpf.csv);
00_normalize_raw.py copies them into the interim layer under their legacy
interim names (data/interim/air_flight_paths_od.csv + airports.csv), which is
what this script reads — there is no airways geometry on disk. This script geocodes
each OD leg's endpoints and writes the straight-line flight paths as a LineString
layer the profile's `airways` layer reads, mirroring the toy project's prepped
`airways.geojson`.

It also dissolves the borough/census-area polygons into one Alaska outline
(`boundary.geojson`) used for the road border-stitch and the map basemap.

Outputs (regenerable; gitignored under data/processed and data/):
    data/processed/airways.geojson   — air OD legs as LineStrings (EPSG:4326)
    data/boundary.geojson            — Alaska land outline for viz (EPSG:4326)

Usage:
    python workflows/02_network_build/02_prep_airways.py
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point

# Inputs are the NORMALIZED interim files (00_normalize_raw.py): airports filtered to
# Alaska, so OD codes can no longer geocode to lower-48 airports.
ROOT = Path(__file__).resolve().parents[2]  # repo root
OD_CSV = ROOT / "data" / "interim" / "air_flight_paths_od.csv"
AIRPORTS_CSV = ROOT / "data" / "interim" / "airports.csv"
BOROUGHS = ROOT / "data" / "interim" / "boroughs.gpkg"

AIRWAYS_OUT = ROOT / "data" / "processed" / "airways.geojson"
AIR_NODES_OUT = ROOT / "data" / "processed" / "air_nodes.geojson"
BOUNDARY_OUT = ROOT / "data" / "boundary.geojson"


def build_code_lookup(airports: pd.DataFrame) -> dict[str, tuple[float, float]]:
    """Map an airport code -> (lon, lat), preferring IATA, then GPS/local/ident codes.

    Later sources fill only codes the earlier, more authoritative source missed, so an
    IATA hit is never overwritten by a weaker code match.
    """
    ap = airports[airports["longitude_deg"].notna() & airports["latitude_deg"].notna()].copy()
    lookup: dict[str, tuple[float, float]] = {}
    for col in ("iata_code", "gps_code", "local_code", "ident"):
        if col not in ap.columns:
            continue
        sub = ap[ap[col].notna()]
        for code, lon, lat in zip(sub[col].astype(str).str.strip().str.upper(),
                                  sub["longitude_deg"], sub["latitude_deg"]):
            lookup.setdefault(code, (float(lon), float(lat)))
    return lookup


def prep_airways() -> None:
    od = pd.read_csv(OD_CSV)
    airports = pd.read_csv(AIRPORTS_CSV, low_memory=False)
    lookup = build_code_lookup(airports)

    rows, geoms, missing = [], [], set()
    for r in od.itertuples(index=False):
        o, d = str(r.origin_code).strip().upper(), str(r.destination_code).strip().upper()
        if o not in lookup:
            missing.add(o)
        if d not in lookup:
            missing.add(d)
        if o in lookup and d in lookup:
            geoms.append(LineString([lookup[o], lookup[d]]))
            rows.append({
                "from_code": o, "to_code": d,
                "origin_node": r.origin_node, "destination_node": r.destination_node,
                "carrier": r.primary_carrier, "service_type": r.service_type,
            })

    gdf = gpd.GeoDataFrame(rows, geometry=geoms, crs=4326)
    AIRWAYS_OUT.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(AIRWAYS_OUT, driver="GeoJSON")
    print(f"airways: {len(gdf)}/{len(od)} OD legs geocoded -> {AIRWAYS_OUT.relative_to(ROOT)}")
    if missing:
        print(f"  unmatched codes ({len(missing)}): {sorted(missing)}")

    # Airport anchor points: the unique geocoded airports actually in the air graph.
    # These (not the 85k-row global airports.csv) are the air<->road transfer anchors.
    seen, node_rows, node_geoms = set(), [], []
    for r in od.itertuples(index=False):
        for code, name in ((str(r.origin_code).strip().upper(), r.origin_node),
                           (str(r.destination_code).strip().upper(), r.destination_node)):
            if code in lookup and code not in seen:
                seen.add(code)
                node_rows.append({"code": code, "name": name})
                node_geoms.append(Point(lookup[code]))
    nodes = gpd.GeoDataFrame(node_rows, geometry=node_geoms, crs=4326)
    nodes.to_file(AIR_NODES_OUT, driver="GeoJSON")
    print(f"air nodes: {len(nodes)} airports -> {AIR_NODES_OUT.relative_to(ROOT)}")


def prep_boundary() -> None:
    boroughs = gpd.read_file(BOROUGHS).to_crs(4326)
    outline = gpd.GeoDataFrame(geometry=[boroughs.geometry.union_all()], crs=4326)
    BOUNDARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    outline.to_file(BOUNDARY_OUT, driver="GeoJSON")
    print(f"boundary: Alaska outline -> {BOUNDARY_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    prep_airways()
    prep_boundary()