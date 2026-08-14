"""Stage 02 — hub aggregation + Supplier/Receiver classification (+ snapping).

R: aggregate_hubs_logic / classify_hub_type, network_preprocessing.R:266-419. Facilities are grouped
by (community, delivery_method) into one hub per community-mode pair; the hub point is the plain
centroid of its members; capacity sums; each hub is classified Supplier/Receiver within its mode,
then snapped onto the relevant network layer(s), dropping hubs displaced beyond max_snap_dist_m.

Buffer-union path (mirrors R lib.R:142-167): when community tags are absent or "community" is not
in params.group_by, buffer facilities by params.buffer_dist, dissolve overlapping buffers per
delivery_method into blobs, assign blob_id by spatial join, then group by (blob_id, *extra_keys).
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

from ..config import Params

# Modes are NOT hardcoded here: hub grouping derives every mode from the delivery_method tags on the
# facilities, which the RegionProfile supplies. The step is region-agnostic.


def classify_hub_type(
    capacity, method: str = "percentile", percentile: float = 0.90, abs_threshold: float = 5e5
) -> np.ndarray:
    """Supplier/Receiver within one delivery-method group (R: classify_hub_type)."""
    cap = np.asarray(capacity, dtype=float)
    if method == "absolute":
        return np.where(cap >= abs_threshold, "Supplier", "Receiver")
    if method == "jenks":
        valid = cap[~np.isnan(cap)]
        if len(np.unique(valid)) >= 3:
            import mapclassify
            brk = mapclassify.NaturalBreaks(valid, k=2).bins[0]
            return np.where(cap >= brk, "Supplier", "Receiver")
        # fall through to percentile for tiny groups
    thr = np.nanquantile(cap, percentile)  # numpy 'linear' == R type-7 quantile
    return np.where(cap >= thr, "Supplier", "Receiver")


def _dominant(label: pd.Series, weight: pd.Series):
    """Capacity-weighted mode of `label` (R: dominant)."""
    keep = label.notna()
    if not keep.any():
        return None
    sums = weight[keep].groupby(label[keep]).sum()
    return sums.idxmax()


# Logical group_by key -> the tagged-facility column it maps to.
_GROUP_KEY_COL = {"community": "_community", "city": "place_name",
                  "region": "region_name", "delivery_method": "delivery_method"}


def _union_methods(methods) -> str:
    """Union delivery-method strings into sorted ' or '-joined atoms ('Barge'+'Road' -> 'Barge or Road')."""
    atoms: set[str] = set()
    for v in pd.Series(methods).dropna():
        atoms.update(a.strip() for a in str(v).replace(" and ", " or ").split(" or ") if a.strip())
    return " or ".join(sorted(atoms))


def _dedup_colocated(hubs: gpd.GeoDataFrame, tol: float) -> gpd.GeoDataFrame:
    """Merge hubs that share the same centroid (rounded to `tol`): sum capacity + facilities, union modes.

    Co-located per-mode hubs collapse into one multimodal hub. Idempotent; first-wins for the
    community/city/region labels (a coincident centroid implies the same place).
    """
    if hubs.empty:
        return hubs
    rx = (hubs.geometry.x / tol).round().astype("int64")
    ry = (hubs.geometry.y / tol).round().astype("int64")
    work = hubs.assign(_rx=rx, _ry=ry)
    if not work.duplicated(["_rx", "_ry"]).any():
        return hubs                                   # nothing co-located
    rows, geoms = [], []
    for _, g in work.groupby(["_rx", "_ry"], sort=False):
        rows.append({
            "num_facilities": int(g["num_facilities"].sum()),
            "total_hub_capacity": float(g["total_hub_capacity"].sum(skipna=True)),
            "hub_community": g["hub_community"].iloc[0],
            "hub_city": g["hub_city"].iloc[0] if "hub_city" in g else None,
            "hub_region": g["hub_region"].iloc[0],
            "delivery_method": _union_methods(g["delivery_method"]),
        })
        geoms.append((g.geometry.x.mean(), g.geometry.y.mean()))
    return gpd.GeoDataFrame(
        pd.DataFrame(rows),
        geometry=gpd.points_from_xy([x for x, _ in geoms], [y for _, y in geoms]),
        crs=hubs.crs,
    )


def _use_buffer_union(group_by: list[str], tagging_enabled: bool) -> bool:
    """True when the buffer-union spatial path should replace community-key grouping.

    Two conditions trigger the buffer-union path, mirroring R's aggregate_hubs_logic
    decision (lib.R:125):

    1. "community" is not in the configured group_by keys — the caller explicitly
       requests pure-radius aggregation (e.g. group_by: ["delivery_method"]).
    2. Spatial community tagging was disabled in the profile (tagging_enabled=False).
       R's equivalent: it checks for a region-specific column that real tagging
       populates; here we use the explicit config flag so the engine stays
       region-agnostic and the detection is transparent.

    Either condition is sufficient; delivery_method is always a split key.
    """
    if "community" not in group_by:
        return True
    return not tagging_enabled


def _buffer_union_hubs(fac: gpd.GeoDataFrame, params: Params) -> gpd.GeoDataFrame:
    """Buffer-union aggregation (mirrors R lib.R:142-167).

    Buffer each facility by params.buffer_dist, dissolve overlapping buffers per
    delivery_method into blobs (unary_union -> explode), assign blob_id via spatial
    join, group by (blob_id, delivery_method, *extra_group_by_keys), then set hub
    geometry = centroid of the member facility point cloud (matching R's st_centroid
    applied to the blob, which equals the centroid of member points for convex blobs).
    """
    group_by: list[str] = list(params.group_by)
    # delivery_method is always a split key; the extra keys are everything else
    # except "community" (which has no data in the untagged path).
    extra_keys = [k for k in group_by if k not in ("community", "delivery_method")]

    recs: list[dict] = []
    geoms: list[tuple[float, float]] = []

    for dm, g in fac.groupby("delivery_method", sort=False):
        # Buffer + dissolve overlapping circles -> one polygon per spatial blob.
        merged = unary_union(g.geometry.buffer(float(params.buffer_dist)))
        # Explode to individual polygons (handles MULTIPOLYGON from unary_union).
        blobs_geoms = list(getattr(merged, "geoms", [merged]))
        blobs = gpd.GeoDataFrame(
            {"blob_id": [f"{dm}_{i}" for i in range(len(blobs_geoms))]},
            geometry=blobs_geoms,
            crs=fac.crs,
        )

        # Assign each facility to the blob it intersects (guaranteed: facility was buffered to form it).
        joined = gpd.sjoin(
            g[["geometry", "total_capacity"] + extra_keys].copy(),
            blobs[["blob_id", "geometry"]],
            how="left",
            predicate="intersects",
        )
        # A facility on a blob boundary may match two blobs; keep the first match (stable).
        joined = joined[~joined.index.duplicated(keep="first")]

        for (blob_id, *extra_vals), grp in joined.groupby(
            ["blob_id"] + extra_keys, sort=False
        ):
            rec: dict = {
                "num_facilities": len(grp),
                "total_hub_capacity": float(grp["total_capacity"].sum(skipna=True)),
                "hub_community": None,
                "hub_region": None,
                "delivery_method": dm,
            }
            # Restore extra group_by columns (e.g. a custom city key).
            for key, val in zip(extra_keys, extra_vals):
                rec[key] = val
            recs.append(rec)
            # Hub geometry = centroid of the member facility point cloud (matches R).
            pts = g.loc[grp.index.intersection(g.index), "geometry"]
            if len(pts) == 0:
                pts = g["geometry"]
            geoms.append((float(pts.x.mean()), float(pts.y.mean())))

    hubs = gpd.GeoDataFrame(
        pd.DataFrame(recs),
        geometry=gpd.points_from_xy([x for x, _ in geoms], [y for _, y in geoms]),
        crs=fac.crs,
    )
    hubs.insert(0, "hub_id", [f"Hub_{i + 1}" for i in range(len(hubs))])
    return hubs


def aggregate_hubs(facilities: gpd.GeoDataFrame, params: Params) -> gpd.GeoDataFrame:
    """Form + classify hubs (no snapping).

    Two paths, mirroring R aggregate_hubs_logic (lib.R:119-167):

    Tagged path  — "community" in params.group_by AND assigned_community is non-NA:
        group by exactly the profile's keys (community/city/region [+ delivery_method]); hub geometry
        = centroid of members. When `delivery_method` is NOT a key, each place is ONE hub whose
        delivery_method is the union of its facilities' modes. Hubs that still share a centroid are
        merged (`_dedup_colocated`): capacity + facilities summed, delivery methods unioned.

    Buffer-union path — community absent or not requested:
        buffer facilities by params.buffer_dist, dissolve overlapping buffers per
        delivery_method into blobs, group by (blob_id, *extra_group_by_keys).

    In both cases: classify_hub_type runs after grouping, before snap.
    """
    fac = facilities.copy()
    group_by: list[str] = list(params.group_by)

    if _use_buffer_union(group_by, params.tagging_enabled):
        hubs = _buffer_union_hubs(fac, params)
    else:
        # Tagged path: coalesce community tiers (mirrors R lib.R:127-141).
        grp = fac.get("assigned_community").where(
            fac.get("assigned_community").notna(), fac.get("geo_label")
        )
        grp = grp.where(grp.notna(), fac.get("region_name"))
        fac["_community"] = grp

        # Group by exactly the profile's keys, mapped to columns. When `delivery_method` is a key,
        # hubs are per-mode; when it is NOT (e.g. group_by = [community, city, region]), each place
        # is ONE hub whose delivery_method is the UNION of its facilities' modes. dropna=False so a
        # missing place_name/region is still a valid group key.
        keys = [_GROUP_KEY_COL[k] for k in group_by
                if k in _GROUP_KEY_COL and _GROUP_KEY_COL[k] in fac.columns]
        keys = list(dict.fromkeys(keys))               # de-dup, preserve order
        region_is_key = "region_name" in keys
        split_by_mode = "delivery_method" in keys

        recs, geoms = [], []
        for _, g in fac.groupby(keys, sort=False, dropna=False):
            recs.append({
                "num_facilities": len(g),
                "total_hub_capacity": float(g["total_capacity"].sum(skipna=True)),
                "hub_community": g["_community"].iloc[0],
                "hub_city": g["place_name"].iloc[0] if "place_name" in g else None,
                "hub_region": (g["region_name"].iloc[0] if region_is_key
                               else (_dominant(g["region_name"], g["total_capacity"])
                                     if "region_name" in g else None)),
                "delivery_method": (g["delivery_method"].iloc[0] if split_by_mode
                                    else _union_methods(g["delivery_method"])),
            })
            geoms.append((g.geometry.x.mean(), g.geometry.y.mean()))

        hubs = gpd.GeoDataFrame(
            pd.DataFrame(recs),
            geometry=gpd.points_from_xy([x for x, _ in geoms], [y for _, y in geoms]),
            crs=fac.crs,
        )
        # Merge hubs that share the same centroid position (sum capacity, union delivery methods).
        n_before = len(hubs)
        hubs = _dedup_colocated(hubs, max(float(params.precision), 1.0))
        if len(hubs) < n_before:
            print(f"[hubs] merged {n_before - len(hubs)} co-located hub(s) sharing a centroid")
        hubs.insert(0, "hub_id", [f"Hub_{i + 1}" for i in range(len(hubs))])

    # Classify Supplier/Receiver within each delivery-method group.
    # classify_hub_type runs AFTER grouping, BEFORE snap (spec requirement).
    hubs["hub_type"] = ""
    for dm, idx in hubs.groupby("delivery_method").groups.items():
        hubs.loc[idx, "hub_type"] = classify_hub_type(
            hubs.loc[idx, "total_hub_capacity"].to_numpy(),
            method=params.hub_threshold_method,
            percentile=params.hub_percentile,
            abs_threshold=params.hub_abs_threshold,
        )
    hubs["is_hub"] = True
    return hubs
