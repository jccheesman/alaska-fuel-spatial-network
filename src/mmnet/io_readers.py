"""Input loaders. Phase 1 covers the raw facility inventory; layer loaders arrive in Phase 1–2.

Column mappings + tagging column names come from the RegionProfile (no region-specific constants here).
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

# Internal names that must always be coerced to numeric (R `as.numeric` path). Capacity columns are
# added per-profile; lon/lat are mapped to these fixed internal names.
_ALWAYS_NUMERIC = ["total_capacity", "longitude", "latitude"]


def read_facilities_raw(
    csv_path: str | Path, input_crs: int, target_crs: int,
    column_map: dict[str, str] | None = None, numeric_cols: list[str] | None = None,
) -> gpd.GeoDataFrame:
    """Read the point inventory CSV into points (EPSG:target_crs).

    `column_map` (raw header -> internal snake_case) and `numeric_cols` (internal names to coerce)
    come from the RegionProfile. Drops rows missing lon/lat, builds points in `input_crs`, and
    reprojects to `target_crs`.
    """
    if not column_map:
        raise ValueError(
            "read_facilities_raw needs a column_map (raw header -> internal name) from the "
            "RegionProfile/PipelineConfig; none was supplied."
        )
    cmap = column_map
    numeric = list(dict.fromkeys((numeric_cols or []) + _ALWAYS_NUMERIC))
    df = pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False)
    present = {src: dst for src, dst in cmap.items() if src in df.columns}
    df = df[list(present)].rename(columns=present)
    for col in numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["longitude", "latitude"]).reset_index(drop=True)
    gdf = gpd.GeoDataFrame(
        df.drop(columns=["longitude", "latitude"]),
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs=input_crs,
    )
    return gdf.to_crs(target_crs)


def _read_lines(path: str | Path, target_crs: int, bbox=None) -> gpd.GeoDataFrame:
    import shapely

    g = gpd.read_file(path, bbox=bbox) if bbox is not None else gpd.read_file(path)
    g = g.to_crs(target_crs)
    g = g[g.geometry.notna() & ~g.geometry.is_empty]
    g = g[g.geometry.geom_type.isin(["LineString", "MultiLineString"])].copy()
    # Drop Z/M (R read_sources drop_zm=TRUE) so coordinates are 2D throughout.
    g["geometry"] = shapely.force_2d(g.geometry.values)
    # Explode MultiLineStrings to LineStrings so the noder/snapper see simple lines.
    g = g.explode(index_parts=False, ignore_index=True)
    g = g[g.geometry.geom_type == "LineString"]
    return g[g.geometry.length > 0]


def load_boundary(path: str | Path, target_crs: int) -> gpd.GeoDataFrame:
    """Region boundary (e.g. TIGER county subdivisions), projected to target CRS (R: load_boundary)."""
    return gpd.read_file(path).to_crs(target_crs)


def load_roads(
    paths: list[str | Path], target_crs: int, boundary: gpd.GeoDataFrame | None = None,
    border_stitch_m: float = 5000.0,
) -> gpd.GeoDataFrame:
    """Road lines (R: load_roads). The PRIMARY source is the in-region roadmap (paths[0]); any extra
    source (paths[1:], e.g. GRIP4 Canada) is a continental dataset whose cross-border segments are
    kept only where they LEAVE the region, then short connector edges stitch each cross-border
    endpoint to the nearest primary-road vertex within `border_stitch_m`.

    Without a `boundary` (or a single source) this is a plain concat of the primary roads — matching
    the degenerate single-source case of R's load_roads.
    """
    import shapely

    primary = _read_lines(paths[0], target_crs)[["geometry"]].reset_index(drop=True)
    primary = primary.assign(road_source="akdot")
    if boundary is None or len(paths) < 2:
        return gpd.GeoDataFrame(primary, geometry="geometry", crs=target_crs)

    # --- extra (continental) segments that extend BEYOND the region boundary ---
    extra = _read_lines(paths[1], target_crs)[["geometry"]].reset_index(drop=True)
    region = boundary.to_crs(target_crs).geometry.union_all()
    leaves = ~extra.geometry.within(region)
    cross = extra[leaves][["geometry"]].reset_index(drop=True).assign(road_source="grip4_ca")

    # --- border stitch: connect each cross-border endpoint to nearby primary roads ---
    pgeom = primary.geometry
    stitch_lines = []
    for geom in cross.geometry:
        coords = list(geom.coords)
        for pt in (shapely.Point(coords[0]), shapely.Point(coords[-1])):
            ni = pgeom.sindex.nearest(pt)[1][0] if len(pgeom) else None
            if ni is None:
                continue
            nearest = pgeom.iloc[int(ni)]
            conn = shapely.shortest_line(pt, nearest)
            ln = conn.length
            if 0 < ln <= border_stitch_m:
                stitch_lines.append(conn)
    stitch = gpd.GeoDataFrame(
        {"road_source": ["stitch"] * len(stitch_lines)},
        geometry=stitch_lines, crs=target_crs,
    )

    out = pd.concat([primary, cross, stitch], ignore_index=True)
    out = gpd.GeoDataFrame(out, geometry="geometry", crs=target_crs)
    return out[~out.geometry.is_empty].reset_index(drop=True)


def load_waterways(path: str | Path, target_crs: int, clip_bbox=None) -> gpd.GeoDataFrame:
    """Water lines. Read fully, reproject, then optionally clip to a target-CRS bbox
    (minx, miny, maxx, maxy) — the region halo."""
    g = _read_lines(path, target_crs)
    if clip_bbox is not None:
        minx, miny, maxx, maxy = clip_bbox
        g = g.cx[minx:maxx, miny:maxy]
    return g[["geometry"]].reset_index(drop=True)


def load_airways(path: str | Path, target_crs: int) -> gpd.GeoDataFrame:
    """Airways lines — the static artifact from workflows/02_network_build/02_prep_airways.py."""
    return _read_lines(path, target_crs)


def load_places(
    path: str | Path, target_crs: int, cols: dict[str, str] | None = None
) -> gpd.GeoDataFrame:
    """Place polygons -> place_name, place_geoid (R: load_places).

    `cols` maps logical fields to source columns ({'name': ..., 'id': ...}) from the profile;
    falls back to TIGER conventions when omitted.
    """
    cols = cols or {}
    p = gpd.read_file(path).to_crs(target_crs)
    name = cols.get("name") or next((c for c in ("NAME", "NAMELSAD") if c in p.columns), None)
    gid = cols.get("id") or next((c for c in ("GEOID", "PLCIDFP", "PLACEFP") if c in p.columns), None)
    out = gpd.GeoDataFrame(
        {
            "place_name": p[name] if name and name in p.columns else None,
            # astype("string") (nullable) keeps NA as <NA>; plain astype(str)
            # would turn nulls into the literal "nan"/"None" strings.
            "place_geoid": p[gid].astype("string") if gid and gid in p.columns else None,
        },
        geometry=p.geometry, crs=p.crs,
    )
    return out


def load_regions(
    path: str | Path, target_crs: int, cols: dict[str, str] | None = None
) -> gpd.GeoDataFrame:
    """Region polygons -> region_name, economic_region (R: load region tiles).

    `cols` maps {'name': ..., 'region': ...} from the profile (raw source headers -> logical fields).
    """
    cols = cols or {}
    b = gpd.read_file(path).to_crs(target_crs)
    name = cols.get("name")
    region = cols.get("region")
    out = gpd.GeoDataFrame(
        {
            # astype("string") (nullable) preserves NA so the nearest-region
            # fallback in tag.py (region_name.isna()) still fires; plain
            # astype(str) would turn a null name into the literal "nan".
            "region_name": b[name].astype("string") if name and name in b.columns else None,
            "economic_region": b[region].astype("string") if region and region in b.columns else None,
        },
        geometry=b.geometry, crs=b.crs,
    )
    return out


def load_delivery_fallback(
    path: str | Path, target_crs: int, community_col: str, method_col: str
) -> gpd.GeoDataFrame:
    """Community->mode fallback points -> community, method, geometry (Points, target CRS).

    Used by Stage 01 to fill facilities whose inventory delivery_method is blank. `community_col` /
    `method_col` name the source's community + delivery-mode columns (profile DATA, region-agnostic).
    """
    g = gpd.read_file(path).to_crs(target_crs)
    g = g[g.geometry.notna() & ~g.geometry.is_empty & g.geometry.geom_type.isin(["Point", "MultiPoint"])]
    out = gpd.GeoDataFrame(
        {
            "community": g[community_col].astype("string") if community_col in g.columns else None,
            "method": g[method_col].astype("string") if method_col in g.columns else None,
        },
        geometry=g.geometry, crs=g.crs,
    )
    return out[out["community"].notna() & out["method"].notna()].reset_index(drop=True)
