#!/usr/bin/env python3
"""Build the full Alaska waterway line layer for the mmnet build.

The build's old waterway input was only a facility-bbox CLIP of the National Waterway Network
(282 edges) — too sparse to connect the coastal/Arctic communities that reach the network only by
sea. This script extracts the REAL Alaska marine network from the raw NWN (Gulf of Alaska, Cook
Inlet, Bering Sea, Arctic Ocean spines) and writes it as the `waterways` layer the profile reads,
so the Stage-03 assembler can connect road + ice to the giant BY SEA (ports + barge hubs) and join
the North Slope at its coastal barge landing.

The AK-only filter (lat/lon bounds on the raw 4269 geometries) mirrors the validated research step
`research/waterway_network/01_ak_waterway.py`. Output is one connected marine network (~316 lines,
~31,903 km) in EPSG:3338.

Outputs (regenerable; data/interim is gitignored):
    data/interim/ak_waterway.gpkg   — full Alaska waterway lines (EPSG:3338)

Usage:
    python workflows/02_network_build/01_prep_waterway.py
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import networkx as nx

ROOT = Path(__file__).resolve().parents[2]  # repo root
RAW = ROOT / "data/raw/connectivity/barge/NWN_Waterway_Network_Lines/Waterway_Network.shp"
OUT = ROOT / "data" / "interim" / "ak_waterway.gpkg"

TARGET = 3338            # NAD83 / Alaska Albers (meters) — the profile's crs.target
NODE_TOL = 50.0          # vertex-rounding tolerance for the component check (matches the assembler)


def ak_only(raw: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """The Alaska marine network: lat > 50 N and west of -125 deg (or the antimeridian Aleutians).

    Ported verbatim from research/waterway_network/01_ak_waterway.py:31-39 — a bounds filter on the
    raw 4269 geometries, then reprojected to the target CRS.
    """
    b = raw.bounds                       # in 4269 (lon/lat)
    lat = (b.miny + b.maxy) / 2
    spans_am = (b.maxx - b.minx) > 300   # antimeridian-spanning (Aleutian / Bering) features
    west = b.maxx < -125                 # entirely west of -125 deg (AK mainland / SE)
    faraleut = b.minx > 168              # western Aleutians (far east of the antimeridian)
    keep = (lat > 50) & (west | faraleut | spans_am)
    return raw[keep].to_crs(TARGET).reset_index(drop=True)


def tag_components(gdf: gpd.GeoDataFrame, tol: float = NODE_TOL) -> gpd.GeoDataFrame:
    """Tag each line with its connected component (0 = giant) by rounding vertices to `tol` meters."""
    g = nx.Graph()
    first_key = []
    for geom in gdf.geometry:
        parts = [geom] if geom.geom_type == "LineString" else list(geom.geoms)
        first = None
        for ln in parts:
            cs = [(round(x / tol), round(y / tol)) for x, y, *_ in ln.coords]
            g.add_edges_from(zip(cs[:-1], cs[1:]))
            if first is None and cs:
                first = cs[0]
        first_key.append(first)
    comps = sorted(nx.connected_components(g), key=len, reverse=True)
    comp_of = {n: i for i, c in enumerate(comps) for n in c}
    out = gdf.copy()
    out["component"] = [comp_of.get(k, -1) for k in first_key]
    out["is_giant"] = out["component"] == 0
    out["length_m"] = out.geometry.length.round()
    return out, len(comps)


def main() -> None:
    if not RAW.exists():
        raise SystemExit(f"raw NWN not found: {RAW}")
    raw = gpd.read_file(RAW)
    ak = ak_only(raw)
    ak, n_comps = tag_components(ak)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    ak[["component", "is_giant", "length_m", "geometry"]].to_file(OUT, driver="GPKG")
    km = ak["length_m"].sum() / 1000.0
    giant_pct = 100.0 * int(ak["is_giant"].sum()) / max(len(ak), 1)
    print(f"AK waterway: {len(ak):,}/{len(raw):,} lines, {km:,.0f} km, {n_comps} component(s), "
          f"giant {giant_pct:.0f}% of lines -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
