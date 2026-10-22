#!/usr/bin/env python3
"""Stage 05 — verify each record's community label against the community's boundary.

Boundaries: inputs/inventory_qc/boundaries/City_Boundaries.zip (DCRA incorporated cities,
matched by community_id GUID, else name) and Census_Designated_Place_Boundaries.zip (CDPs,
matched by canonical name). Both EPSG:3338.

The check VERIFIES ONLY. It never relabels, moves or drops a record. A community with no
boundary in these files (unified city-boroughs such as Anchorage, unincorporated places
without a CDP) is not tested: its records are kept as labelled and produce no flag.

Outcome per labelled record with coordinates:
    match         inside, or within boundary_buffer_m of, its own community's boundary -> no flag
    mismatch      inside a DIFFERENT community's boundary
    outside       inside no boundary at all, but its own boundary exists elsewhere
Priority: review  if mismatch AND > boundary_review_km from its own boundary
          info    mismatch nearer than that (owner 2026-10-08): a neighbouring Census place that
                  is part of the same town (Badger/North Pole, Nikiski/Kenai, Fritz Creek/Homer);
                  the label and coordinates are both right — reported, never reviewed
          info    outside — NEVER reviewed (owner 2026-10-08): a labelled site outside every
                  boundary is the normal shape of a remote Alaskan facility (repeater, mine, camp,
                  hatchery) carrying its home-town label. It is reported here and its distance is
                  published as `community_distance_km` so the hub builder can keep a far site out of
                  the town's hub centroid (profile `hubs.remote_site_km`). The copied-coordinate
                  error that can hide in this class is caught by the shared_point detector.
Records listed in inputs/inventory_qc/remote_sites.csv (owner-accepted remote sites) and
records with a pending/approved correction are reported as covered, not re-raised.

Writes outputs/00_inventory_qc/<release>/flags_boundary.csv (flagged records only),
boundary_distance.csv (EVERY located record: outcome, km to its own boundary, the city/CDP polygon
the point physically sits in, and the derived relation — the publish step carries the last three
into the clean table as `community_distance_km`, `located_in_place`, `community_relation`) and
boundary_summary.csv (counts per outcome, incl. untested).

The published pair `community_name` (the labelled = service community, what the hub builder groups
on) vs `located_in_place` (where the point physically is) records the difference instead of
resolving it. `community_relation` summarises it per record:
    inside     in, or within boundary_buffer_m of, its own community's boundary
    adjacent   inside a neighbouring place <= boundary_review_km away (same town; Badger/North Pole)
    remote     inside no boundary at all (a remote site with its home-town label)
    elsewhere  inside another community's boundary > boundary_review_km away (one of the two is wrong)
    untested   no label, or the labelled community has no boundary in the files

Run:  python workflows/00_inventory_qc/05_boundary_check.py [--release 2025]
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

from _qc import OUT, QC, canon, corrections, latest_release, read_csv, thresholds, write_csv

BND = QC / "boundaries"
CITY_ZIP, CDP_ZIP = BND / "City_Boundaries.zip", BND / "Census_Designated_Place_Boundaries.zip"


def load_boundaries() -> gpd.GeoDataFrame:
    def read(zpath: Path) -> gpd.GeoDataFrame:
        with zipfile.ZipFile(zpath) as zf:
            shp = next(n for n in zf.namelist() if n.lower().endswith(".shp"))
        return gpd.read_file(f"zip://{zpath}!{shp}").to_crs(3338)
    city, cdp = read(CITY_ZIP), read(CDP_ZIP)
    b = pd.concat([
        gpd.GeoDataFrame({"bname": city["CommunityN"], "guid": city["CommunityI"], "btype": "city"}, geometry=city.geometry),
        gpd.GeoDataFrame({"bname": cdp["Name"].str.replace(r"\s+CDP$", "", regex=True), "guid": None, "btype": "CDP"}, geometry=cdp.geometry),
    ], ignore_index=True)
    b = gpd.GeoDataFrame(b, crs=3338)
    b["bkey"] = b["bname"].map(canon)
    b["geometry"] = b.geometry.buffer(0)
    return b


def check(label: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Returns (flags, summary, distance) — see the module docstring."""
    th = thresholds()
    buf_m, review_km = th["boundary_buffer_m"], th["boundary_review_km"]
    fac = read_csv(OUT / label / "facilities_normalised.csv")
    B = load_boundaries()
    # aliases are already folded into community_key; map boundary keys through the same alias table
    from _qc import aliases
    amap = {canon(r.variant): canon(r.canonical) for r in aliases().itertuples()}
    B["bkey"] = B["bkey"].map(lambda k: amap.get(k, k))
    by_key = {k: g.geometry.union_all() for k, g in B.groupby("bkey")}
    by_guid = {k: g.geometry.union_all() for k, g in B.dropna(subset=["guid"]).groupby("guid")}

    loc = fac.dropna(subset=["latitude", "longitude"]).copy()
    G = gpd.GeoDataFrame(loc, geometry=gpd.points_from_xy(loc["longitude"].astype(float), loc["latitude"].astype(float)), crs=4326).to_crs(3338)
    inside = gpd.sjoin(G[["record_id", "geometry"]], B[["bname", "bkey", "guid", "geometry"]], how="left", predicate="within")
    inside_names = inside.groupby("record_id")["bname"].agg(lambda s: sorted(set(s.dropna())))

    corr = corrections()
    cstat = corr.groupby("record_id")["status"].agg(lambda s: "approved" if "approved" in set(s) else ("pending" if "pending" in set(s) else "rejected"))
    exc = pd.read_csv(QC / "remote_sites.csv", dtype=str, keep_default_na=False) if (QC / "remote_sites.csv").exists() else pd.DataFrame(columns=["record_id"])
    exc_ids = set(exc["record_id"])

    rows, dist = [], []
    counts = {"untested: no label": 0, "untested: no boundary for this community": 0, "match": 0, "mismatch": 0, "outside": 0}
    for r in G.itertuples():
        key = r.community_key
        ins = inside_names.get(r.record_id, [])
        located = ", ".join(ins)                    # the city/CDP polygon(s) the point physically sits in
        if not isinstance(key, str):
            counts["untested: no label"] += 1
            dist.append(dict(record_id=r.record_id, outcome="untested", own_boundary_km="", located_in_place=located, community_relation="untested"))
            continue
        own = by_guid.get(r.community_id) if isinstance(r.community_id, str) and r.community_id in by_guid else by_key.get(key)
        if own is None:
            counts["untested: no boundary for this community"] += 1
            dist.append(dict(record_id=r.record_id, outcome="untested", own_boundary_km="", located_in_place=located, community_relation="untested"))
            continue
        d = own.distance(r.geometry)
        km = d / 1000
        if d <= buf_m:
            counts["match"] += 1
            dist.append(dict(record_id=r.record_id, outcome="match", own_boundary_km=round(km, 2), located_in_place=located, community_relation="inside"))
            continue
        outcome = "mismatch" if ins else "outside"
        counts[outcome] += 1
        relation = "remote" if outcome == "outside" else ("adjacent" if km <= review_km else "elsewhere")
        dist.append(dict(record_id=r.record_id, outcome=outcome, own_boundary_km=round(km, 2), located_in_place=located, community_relation=relation))
        priority = "review" if (outcome == "mismatch" and km > review_km) else "info"
        covered = (f"correction:{cstat[r.record_id]}" if r.record_id in cstat.index
                   else ("exception:remote_site" if r.record_id in exc_ids else ""))
        rows.append(dict(record_id=r.record_id, community_name=r.community_name, outcome=outcome, priority=priority,
                         inside_boundary_of=", ".join(ins), own_boundary_km=round(km, 2),
                         latitude=r.latitude, longitude=r.longitude, covered_by=covered,
                         note=("inside a neighbouring place (same town)" if outcome == "mismatch" and km <= review_km
                               else ("remote site, outside every boundary" if outcome == "outside" else ""))))
    F = pd.DataFrame(rows, columns=["record_id", "community_name", "outcome", "priority", "inside_boundary_of", "own_boundary_km",
                                    "latitude", "longitude", "covered_by", "note"])
    F = F.sort_values(["priority", "own_boundary_km"], ascending=[True, False]).reset_index(drop=True)
    S = pd.DataFrame([{"outcome": k, "records": v} for k, v in counts.items()] +
                     [{"outcome": "flagged: review", "records": int((F["priority"] == "review").sum())},
                      {"outcome": "flagged: review, not yet covered by a decision", "records": int(((F["priority"] == "review") & (F["covered_by"] == "")).sum())},
                      {"outcome": "info: inside a neighbouring place <= review km (same town, not reviewed)",
                       "records": int(((F["priority"] == "info") & (F["outcome"] == "mismatch")).sum())},
                      {"outcome": "info: outside every boundary (remote site, not reviewed)",
                       "records": int(((F["priority"] == "info") & (F["outcome"] == "outside")).sum())}])
    D = pd.DataFrame(dist, columns=["record_id", "outcome", "own_boundary_km", "located_in_place", "community_relation"]).sort_values("record_id").reset_index(drop=True)
    return F, S, D


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--release", default=None)
    a = ap.parse_args(argv)
    label = a.release or latest_release()
    F, S, D = check(label)
    write_csv(F, OUT / label / "flags_boundary.csv")
    write_csv(S, OUT / label / "boundary_summary.csv")
    write_csv(D, OUT / label / "boundary_distance.csv")
    for r in S.itertuples():
        print(f"  {r.outcome:52s} {r.records:5d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
