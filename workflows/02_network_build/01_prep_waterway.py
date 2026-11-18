#!/usr/bin/env python3
"""Build the full Alaska waterway line layer for the mmnet build.

SOURCE (owner 2026-11-17): the OWNER-CURATED NWN derivative
`inputs/data_for_network_build/water_networks/waterways_network_ak_albers.shp`
— converted and edited by the owner in ArcGIS Pro so that every route avoids
land pixels and flows on water (harbour approaches round the headlands instead
of clipping docks/islands: Kodiak channel, the Akutan line that the published
NWN runs straight across Akutan Island, the Bering Sea Access family, Point
Hope, Kaktovik). This is also the file the barge corridor masks are rasterised
from (`friction_paths.py` "waterways"), so the network and the friction
surface share ONE waterway geometry by construction.

History: the build's first waterway input was a facility-bbox CLIP of the NWN
(282 edges, too sparse); 2026-09 replaced it with a full-Alaska extraction of
the RAW NWN download; 2026-11-17 the extraction was repointed at the owner's
curated layer after a measured comparison (land-crossing 0-0.8% vs 1.5-2.3% of
samples at the eight closed harbour approaches; all 14 all-year-closed NWN
edges clean on the existing barge surface; full rebuild PASS). The raw NWN
download stays under data/raw as the upstream reference and is no longer read
by the build.

The AK-only filter (lat/lon bounds, mirrored from the validated waterway
research step) runs on 4269 geometries, so the curated 3338 layer round-trips
through 4269 for the filter. Output ~315 lines, ~30,617 km in EPSG:3338.

Outputs (regenerable; data/interim is gitignored):
    data/interim/ak_waterway.gpkg   — full Alaska waterway lines (EPSG:3338)

Usage:
    python workflows/02_network_build/01_prep_waterway.py
"""

from __future__ import annotations


import geopandas as gpd
import networkx as nx

import repo_paths as rp
ROOT = rp.ROOT
# The owner-curated waterway (see module docstring). NOT the raw NWN download.
CURATED = rp.NETWORK_DATA / "water_networks" / "waterways_network_ak_albers.shp"
OUT = rp.INTERIM / "ak_waterway.gpkg"

TARGET = 3338            # NAD83 / Alaska Albers (meters) — the profile's crs.target
NODE_TOL = 50.0          # vertex-rounding tolerance for the component check (matches the assembler)


def ak_only(raw: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """The Alaska marine network: lat > 50 N and west of -125 deg (or the antimeridian Aleutians).

    Ported verbatim from the waterway research prototype — a bounds filter on the raw 4269
    geometries, then reprojected to the target CRS.
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
    if not CURATED.exists():
        raise SystemExit(
            f"curated waterway not found: {CURATED} "
            "(extract inputs/data_for_network_build.zip: python tools/extract_inputs.py)")
    cur = gpd.read_file(CURATED)
    # the AK filter works on lon/lat bounds; the curated layer is 3338 already
    raw = cur.to_crs(4269)
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
