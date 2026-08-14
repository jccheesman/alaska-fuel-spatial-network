"""Stage 01b — community (city) + region tagging (R: assign_community_region, :167-209).

Two-tier spatial join: a facility relates to a COMMUNITY if it falls inside a city polygon
(`places`); otherwise it falls back to the REGION it sits in (`regions`, which tile the area).
The inventory's own community_name is authoritative and only cross-checked against the polygon name.
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd


def _norm(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().str.upper()


def _canon(s: pd.Series) -> pd.Series:
    """Canonical place/community name for matching: upper, strip punctuation, SAINT->ST, MOUNT->MT.

    Absorbs spelling/punctuation variants so 'Saint Marys' / "St. Mary's" / 'Clark's Point' compare
    equal, while keeping genuinely different names distinct. Region-agnostic.
    """
    out = s.astype("string").str.upper().str.replace(r"[.'`,]", "", regex=True)
    out = out.str.replace(r"\bSAINT\b", "ST", regex=True).str.replace(r"\bMOUNT\b", "MT", regex=True)
    return out.str.replace(r"\s+", " ", regex=True).str.strip()


def passthrough_tag(facilities: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Tagging disabled: no spatial join. assigned_community = the inventory community only.

    Keeps the downstream schema (assigned_community/level/geo_label/region_name) so s02 hub
    grouping still works for regions that supply no place/region polygons.
    """
    out = facilities.copy()
    comm = out["community_name"] if "community_name" in out.columns else pd.Series(None, index=out.index)
    out["place_name"] = None
    out["place_geoid"] = None
    out["region_name"] = None
    out["economic_region"] = None
    out["assigned_community"] = comm
    out["assigned_level"] = np.where(comm.notna(), "inventory_only", "untagged")
    out["geo_label"] = comm
    out["name_agrees"] = False
    out["name_match"] = "n/a"
    if "ast_facility_id" in out.columns:
        out = out.sort_values("ast_facility_id", kind="stable")
    return out.reset_index(drop=True)


def assign_community_region(
    facilities: gpd.GeoDataFrame, places: gpd.GeoDataFrame, regions: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """Tag each facility with a community (TIGER place, else inventory, else borough) + region.

    Two-tier point-in-polygon (place, then borough; nearest-region fallback so region is never NA).
    The inventory community is authoritative, then reconciled against the place polygon via a
    canonical name match into `name_match`: `agree` (same canonical name, absorbing spelling
    variants), `neighbor` (differs but same borough — kept as the inventory community), or `conflict`
    (the labelled community belongs to a different borough than the coordinates → a genuine data
    error, **dropped** from the output). Adds assigned_community/level, geo_label, name_match,
    name_agrees.
    """
    fac = facilities.copy()

    # Two-tier point-in-polygon (within). drop join index cols after each.
    out = fac.sjoin(places[["place_name", "place_geoid", "geometry"]], how="left", predicate="within")
    out = out.drop(columns=[c for c in out.columns if c.startswith("index_right")])
    # A point on a shared edge can match >1 polygon: keep one row per facility (stable first).
    out = out.sort_values("ast_facility_id", kind="stable").drop_duplicates("cluster_id", keep="first")

    out = out.sjoin(regions[["region_name", "economic_region", "geometry"]], how="left", predicate="within")
    out = out.drop(columns=[c for c in out.columns if c.startswith("index_right")])
    out = out.sort_values("ast_facility_id", kind="stable").drop_duplicates("cluster_id", keep="first")

    # Offshore/edge points may miss every region: snap to the nearest so the fallback is never NA.
    na = out["region_name"].isna()
    if na.any():
        nearest = out.loc[na, ["geometry"]].sjoin_nearest(
            regions[["region_name", "economic_region", "geometry"]], how="left"
        )
        nearest = nearest[~nearest.index.duplicated(keep="first")]
        out.loc[na, "region_name"] = nearest["region_name"]
        out.loc[na, "economic_region"] = nearest["economic_region"]

    has_place = out["place_name"].notna()
    has_comm = out["community_name"].notna()
    # Inventory community_name is authoritative; polygon place_name only fills gaps.
    out["assigned_community"] = out["community_name"].where(has_comm, out["place_name"])
    out["assigned_level"] = np.select(
        [has_place, has_comm], ["inside_place", "inventory_only"], default="region_only"
    )
    out["geo_label"] = out["place_name"].where(
        out["place_name"].notna(),
        out["community_name"].where(has_comm, out["region_name"]),
    )

    # --- Name reconciliation (canonical) → name_match ∈ {agree, neighbor, conflict, n/a} ----------
    # Which borough each TIGER place sits in (built from the supplied layers; region-agnostic).
    pc = places[["place_name", "geometry"]].copy()
    pc["geometry"] = pc.geometry.representative_point()
    pc = gpd.sjoin(pc, regions[["region_name", "geometry"]], how="left", predicate="within")
    place_borough: dict = {}
    for k, v in zip(_canon(pc["place_name"]), pc["region_name"]):
        if pd.notna(k):
            place_borough.setdefault(k, v)

    cp, cc = _canon(out["place_name"]), _canon(out["community_name"])
    comm_borough = cc.map(place_borough)                 # borough the LABELLED community belongs to
    comparable = has_place & has_comm
    agree = (comparable & (cp == cc)).fillna(False)
    conflict = (comparable & ~agree & comm_borough.notna()
                & (comm_borough != out["region_name"])).fillna(False)
    neighbor = (comparable & ~agree & ~conflict).fillna(False)
    out["name_match"] = np.select([agree, neighbor, conflict],
                                  ["agree", "neighbor", "conflict"], default="n/a")
    out["name_agrees"] = agree                            # back-compat (now includes spelling variants)

    # Conflict = the labelled community is in a different borough than the coordinates: a genuine
    # data error (wrong coordinate or label). DROP these facilities from the tagged set.
    n_conflict = int(conflict.sum())
    if n_conflict:
        print(f"[tag] dropped {n_conflict} cross-borough conflict facilities (name_match='conflict')")
        out = out[~conflict.values].copy()

    return out.sort_values("ast_facility_id", kind="stable").reset_index(drop=True)
