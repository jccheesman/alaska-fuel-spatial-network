"""Pure-Python port of river_ice_full_pipeline.py's interpolation stages.

Reproduces, without arcpy:

    Step 5   river mask   = NHDArea polygons  UNION  200 m flowline buffer
    Step 6a  polygon fill = per-polygon median of the point raster
    Step 6b  IDW          = power 2, 12 nearest, 50 km cap
    Step 6c  NN fallback  = nearest valid cell (arcpy EucAllocation)
    provenance             1 = polygon median, 2 = IDW, 3 = NN fallback

Everything is computed on an explicit grid passed in by the caller, so the
same code can run on arcpy's native (unaligned) grid for validation and on
the canonical 150 m friction grid for production.
"""

from __future__ import annotations

import numpy as np
import geopandas as gpd
from rasterio.features import rasterize
from scipy.spatial import cKDTree
from scipy.ndimage import distance_transform_edt  # noqa: F401  (parity notes)

# --- knobs, mirroring river_ice_full_pipeline.py --------------------------
FLOWLINE_BUFFER_M = 200
IDW_POWER = 2
IDW_NUM_POINTS = 12
IDW_MAX_DIST_M = 50_000
FIELD_REACH = "ReachID"
FIELD_MONTH = "month"
FIELD_VALUE = "areaPropMedWater"
NODATA = -9999.0


# --------------------------------------------------------------------------
# Step 1-4: points -> one representative point per reach, with a month median
# --------------------------------------------------------------------------
def load_reach_points(geojson_path):
    """Return (reach_gdf, median_table).

    reach_gdf    one row per ReachID, geometry = first observation's point
                 (arcpy: DeleteIdentical keeps the lowest OBJECTID)
    median_table dict[(reach, month)] -> median p_ice
    """
    pts = gpd.read_file(geojson_path)
    if pts.crs is None or pts.crs.to_epsg() != 3338:
        pts = pts.to_crs(3338)

    # Step 2: p_ice = clamp(1 - areaPropMedWater, 0, 1)
    pts["p_ice"] = (1.0 - pts[FIELD_VALUE].astype(float)).clip(0.0, 1.0)

    # Step 3: median across the three periods, per (reach, month)
    med = (pts.groupby([FIELD_REACH, FIELD_MONTH])["p_ice"]
              .median()
              .rename("median_p_ice")
              .reset_index())

    # Step 4: one point per reach
    reaches = pts.drop_duplicates(subset=[FIELD_REACH], keep="first")
    reaches = reaches[[FIELD_REACH, "geometry"]].reset_index(drop=True)
    return reaches, med


def month_points(reaches, med, month):
    """Reach points carrying a value for `month` (arcpy's pts_layer)."""
    sub = med[med[FIELD_MONTH] == month][[FIELD_REACH, "median_p_ice"]]
    j = reaches.merge(sub, on=FIELD_REACH, how="inner")
    xy = np.column_stack([j.geometry.x.values, j.geometry.y.values])
    return xy, j["median_p_ice"].to_numpy(float)


# --------------------------------------------------------------------------
# Step 5: the river mask, and the zone raster used for the polygon median
# --------------------------------------------------------------------------
def build_masks(polygons_path, flowlines_path, transform, shape):
    """Return (mask, zone).

    mask  bool   polygons UNION 200 m flowline buffer, cell-centre rule
    zone  int32  1-based polygon id per cell, 0 outside every polygon
    """
    polys = gpd.read_file(polygons_path)
    if polys.crs.to_epsg() != 3338:
        polys = polys.to_crs(3338)
    polys = polys.reset_index(drop=True)
    polys["zone_id"] = np.arange(1, len(polys) + 1, dtype=np.int64)

    # arcpy rasterises with the higher OBJECTID winning an overlap; burning in
    # ascending order gives the same result (later burns overwrite earlier).
    zone = rasterize(
        ((g, z) for g, z in zip(polys.geometry, polys.zone_id) if g is not None),
        out_shape=shape, transform=transform, fill=0,
        dtype=np.int32, all_touched=False,
    )

    lines = gpd.read_file(flowlines_path)
    if lines.crs.to_epsg() != 3338:
        lines = lines.to_crs(3338)
    buf = lines.geometry.buffer(FLOWLINE_BUFFER_M)  # round caps/joins, as arcpy
    line_mask = rasterize(
        ((g, 1) for g in buf if g is not None and not g.is_empty),
        out_shape=shape, transform=transform, fill=0,
        dtype=np.uint8, all_touched=False,
    ).astype(bool)

    mask = (zone > 0) | line_mask
    return mask, zone, polys


# --------------------------------------------------------------------------
# Step 6a: PointToRaster(MEAN) -> ZonalStatistics(MEDIAN) -> PolygonToRaster
# --------------------------------------------------------------------------
def polygon_medians(xy, vals, zone, transform, n_zones, even="mean"):
    """Median of the point raster inside each polygon.

    arcpy path: PointToRaster(MEAN) collapses co-located reaches to one cell
    value first, then ZonalStatisticsAsTable(MEDIAN) takes the median of
    those *cell* values -- not of the raw points. Reproduced exactly.
    """
    inv = ~transform
    cols, rows = inv * (xy[:, 0], xy[:, 1])
    rows = np.floor(rows).astype(np.int64)
    cols = np.floor(cols).astype(np.int64)
    h, w = zone.shape
    ok = (rows >= 0) & (rows < h) & (cols >= 0) & (cols < w)
    rows, cols, v = rows[ok], cols[ok], vals[ok]

    # PointToRaster cell_assignment="MEAN"
    flat = rows.astype(np.int64) * w + cols
    order = np.argsort(flat, kind="stable")
    flat, v = flat[order], v[order]
    uniq, start = np.unique(flat, return_index=True)
    sums = np.add.reduceat(v, start)
    counts = np.diff(np.append(start, len(v)))
    cell_val = sums / counts

    cell_zone = zone.ravel()[uniq]
    keep = cell_zone > 0
    cz, cv = cell_zone[keep], cell_val[keep]

    med = np.full(n_zones + 1, np.nan)
    if cz.size:
        o = np.argsort(cz, kind="stable")
        cz, cv = cz[o], cv[o]
        bounds = np.searchsorted(cz, np.arange(cz[0], cz[-1] + 2))
        for i, z in enumerate(range(cz[0], cz[-1] + 1)):
            a, b = bounds[i], bounds[i + 1]
            if b > a:
                seg = np.sort(cv[a:b])
                n = b - a
                if n % 2:
                    med[z] = seg[n // 2]
                else:
                    med[z] = (seg[n // 2 - 1] + seg[n // 2]) / 2.0 \
                        if even == "mean" else seg[n // 2 - 1]
    return med, uniq, cell_val


# --------------------------------------------------------------------------
# Step 6b: IDW, power 2, 12 nearest, 50 km cap  (arcpy RadiusVariable)
# --------------------------------------------------------------------------
def idw(xy, vals, tx, ty, k=IDW_NUM_POINTS, power=IDW_POWER,
        max_dist=IDW_MAX_DIST_M, chunk=200_000):
    """Return interpolated values, NaN where no point lies within max_dist."""
    tree = cKDTree(xy)
    out = np.full(tx.size, np.nan)
    for s in range(0, tx.size, chunk):
        e = min(s + chunk, tx.size)
        q = np.column_stack([tx[s:e], ty[s:e]])
        d, i = tree.query(q, k=k, distance_upper_bound=max_dist, workers=-1)
        if k == 1:
            d, i = d[:, None], i[:, None]
        good = np.isfinite(d)
        i = np.where(good, i, 0)
        vv = vals[i]

        exact = d == 0.0
        has_exact = exact.any(axis=1)

        with np.errstate(divide="ignore", invalid="ignore"):
            wgt = np.where(good, 1.0 / np.power(d, power), 0.0)
        wgt[~good] = 0.0
        wsum = wgt.sum(axis=1)
        res = np.where(wsum > 0, (wgt * vv).sum(axis=1) / np.where(wsum > 0, wsum, 1), np.nan)

        if has_exact.any():
            first = np.argmax(exact, axis=1)
            res[has_exact] = vv[has_exact, first[has_exact]]
        res[~good.any(axis=1)] = np.nan
        out[s:e] = res
    return out


# --------------------------------------------------------------------------
# Step 6c: EucAllocation -- nearest valid cell, unbounded
# --------------------------------------------------------------------------
def nearest_fill(src_xy, src_vals, tgt_xy, max_dist=np.inf):
    if src_xy.shape[0] == 0 or tgt_xy.shape[0] == 0:
        return np.full(tgt_xy.shape[0], np.nan), np.full(tgt_xy.shape[0], np.inf)
    d, i = cKDTree(src_xy).query(tgt_xy, k=1,
                                 distance_upper_bound=max_dist, workers=-1)
    out = np.full(tgt_xy.shape[0], np.nan)
    ok = np.isfinite(d)
    out[ok] = src_vals[i[ok]]
    return out, d


# --------------------------------------------------------------------------
# Driver for one month
# --------------------------------------------------------------------------
def build_month(month, reaches, med, mask, zone, polys, transform, shape,
                nn_max_dist=np.inf, even="mean"):
    """Return (values, provenance) full-grid arrays for one data month."""
    h, w = shape
    xy, vals = month_points(reaches, med, month)

    zmed, _, _ = polygon_medians(xy, vals, zone, transform,
                                 n_zones=len(polys), even=even)

    idx = np.flatnonzero(mask.ravel())
    rr, cc = np.divmod(idx, w)
    # cell centres
    cx = transform.c + (cc + 0.5) * transform.a
    cy = transform.f + (rr + 0.5) * transform.e

    zcell = zone.ravel()[idx]
    poly_val = np.where(zcell > 0, zmed[zcell], np.nan)

    need = np.isnan(poly_val)
    out = poly_val.copy()
    prov = np.where(need, 0, 1).astype(np.uint8)

    if need.any():
        iv = idw(xy, vals, cx[need], cy[need])
        out[need] = iv
        got = np.isfinite(iv)
        pn = prov[need]
        pn[got] = 2
        prov[need] = pn

    out = np.clip(out, 0.0, 1.0)

    still = np.isnan(out)
    if still.any():
        src = ~still
        filled, _ = nearest_fill(np.column_stack([cx[src], cy[src]]), out[src],
                                 np.column_stack([cx[still], cy[still]]),
                                 max_dist=nn_max_dist)
        out[still] = filled
        pn = prov[still]
        pn[:] = 3
        prov[still] = pn

    vfull = np.full(h * w, NODATA, dtype=np.float32)
    vfull[idx] = np.where(np.isnan(out), NODATA, out)
    pfull = np.zeros(h * w, dtype=np.uint8)
    pfull[idx] = prov
    return vfull.reshape(shape), pfull.reshape(shape)
