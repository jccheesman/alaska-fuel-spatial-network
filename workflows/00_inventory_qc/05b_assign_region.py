#!/usr/bin/env python3
"""Stage 05b — assign each located record to an AEA energy region.

Regions: Alaska_Energy_Authority_Library.zip (the 11 AEA energy regions, EPSG:3338), a member of
the tracked bundle inputs/region_and_census_data.zip. tools/extract_inputs.py extracts the bundle
to inputs/region_and_census_data/; this stage extracts that one member itself when the working
dir is absent (a fresh clone runs workflow 00 without the extraction step).

Per located record (owner decision 2026-10-31, docs/INVENTORY_QC_PLAN.md decision 15):
    inside    the point sits in a region polygon -> that region, distance 0
    nearest   inside no polygon, nearest region within thresholds aea_region_nearest_km ->
              that region, with the distance; reported, never reviewed (the one 2025 case is a
              road-served site 4 km over the Canadian border at Mile 42 Haines Highway)
    outside   inside no polygon and farther than the cap -> region blank
    untested  no coordinates
The assignment DESCRIBES where the point is; it never moves or relabels a record.

Writes outputs/00_inventory_qc/<release>/
    region_assignment.csv       every record: record_id, aea_region, aea_region_relation,
                                aea_region_distance_km — the publish step carries the three
                                into the clean table
    aea_regions.csv             region_name, num_facilities (located records assigned to it)
    aea_region_adjacency.csv    region_a, region_b, shared_border_m — both directions of every
                                pair of regions whose polygons touch, with the length of the
                                shared boundary (EPSG:3338 metres)
The last two are the region tables the harness loads (regions / adjacent_to); it computes no
geometry of its own.

Run:  python workflows/00_inventory_qc/05b_assign_region.py [--release 2025]
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from _qc import OUT, ROOT, latest_release, read_csv, thresholds, write_csv

BUNDLE = ROOT / "inputs" / "region_and_census_data.zip"
MEMBER = "region_and_census_data/Alaska_Energy_Authority_Library.zip"
REGIONS_ZIP = ROOT / "inputs" / MEMBER
REGION_COLUMN = "NAME"


def regions_path() -> Path:
    """The AEA region shapefile zip, extracted from the tracked bundle if the working dir is absent."""
    if REGIONS_ZIP.exists():
        return REGIONS_ZIP
    if not BUNDLE.exists():
        raise SystemExit(f"{BUNDLE.relative_to(ROOT)} is missing — clone incomplete? It is a plain git blob (no LFS); see DATA.md section 1.1.")
    with zipfile.ZipFile(BUNDLE) as zf:
        zf.extract(MEMBER, ROOT / "inputs")
    return REGIONS_ZIP


def load_regions(path: Path | None = None) -> gpd.GeoDataFrame:
    reg = gpd.read_file(f"zip://{path or regions_path()}")
    if reg.crs is None or reg.crs.to_epsg() != 3338:
        reg = reg.to_crs(3338)
    return reg[[REGION_COLUMN, "geometry"]].reset_index(drop=True)


def adjacency(reg: gpd.GeoDataFrame) -> pd.DataFrame:
    """Both directions of every pair whose polygons touch, with the shared boundary length (m)."""
    rows = []
    for i, a in reg.iterrows():
        for j, b in reg.iterrows():
            if i >= j or not (a.geometry.touches(b.geometry) or a.geometry.intersects(b.geometry)):
                continue
            shared = a.geometry.intersection(b.geometry)
            if shared.is_empty:
                continue
            rows.append((a[REGION_COLUMN], b[REGION_COLUMN], shared.length))
            rows.append((b[REGION_COLUMN], a[REGION_COLUMN], shared.length))
    return pd.DataFrame(rows, columns=["region_a", "region_b", "shared_border_m"]).sort_values(
        ["region_a", "region_b"]).reset_index(drop=True)


def assign(label: str, reg: gpd.GeoDataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(region_assignment for every record, aea_regions, aea_region_adjacency)."""
    reg = load_regions() if reg is None else reg
    cap_km = thresholds()["aea_region_nearest_km"]
    fac = read_csv(OUT / label / "facilities_normalised.csv")
    located = fac["latitude"].notna() & fac["longitude"].notna()
    pts = gpd.GeoDataFrame(fac.loc[located, ["record_id"]],
                           geometry=gpd.points_from_xy(fac.loc[located, "longitude"].astype(float),
                                                       fac.loc[located, "latitude"].astype(float)),
                           crs="EPSG:4326").to_crs(reg.crs)
    inside = gpd.sjoin(pts, reg, how="left", predicate="within")
    inside = inside[~inside.index.duplicated(keep="first")]          # a point on a shared edge: first polygon
    region = inside[REGION_COLUMN].copy()
    relation = pd.Series(np.where(region.notna(), "inside", "outside"), index=inside.index, dtype=object)
    dist = pd.Series(np.where(region.notna(), 0.0, np.nan), index=inside.index)
    for idx in inside.index[region.isna()]:
        d = reg.geometry.distance(pts.at[idx, "geometry"]) / 1000.0
        k = int(d.idxmin())
        dist.at[idx] = round(float(d.iloc[k]), 2)
        if d.iloc[k] <= cap_km:
            region.at[idx] = reg.at[k, REGION_COLUMN]
            relation.at[idx] = "nearest"
    A = pd.DataFrame({"record_id": fac["record_id"]})
    A["aea_region"] = A["record_id"].map(dict(zip(pts["record_id"], region)))
    A["aea_region_relation"] = A["record_id"].map(dict(zip(pts["record_id"], relation))).fillna("untested")
    A["aea_region_distance_km"] = A["record_id"].map(dict(zip(pts["record_id"], dist)))
    counts = A["aea_region"].value_counts()
    R = pd.DataFrame({"region_name": list(reg[REGION_COLUMN]),
                      "num_facilities": [int(counts.get(n, 0)) for n in reg[REGION_COLUMN]]})
    return A, R, adjacency(reg)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--release", default=None)
    a = ap.parse_args(argv)
    label = a.release or latest_release()
    A, R, J = assign(label)
    write_csv(A, OUT / label / "region_assignment.csv")
    write_csv(R, OUT / label / "aea_regions.csv")
    write_csv(J, OUT / label / "aea_region_adjacency.csv")
    rel = A["aea_region_relation"].value_counts().to_dict()
    print(f"release {label}: {len(R)} regions, {len(J) // 2} adjacent pairs; records "
          + ", ".join(f"{k} {v}" for k, v in sorted(rel.items())))
    for r in A[A["aea_region_relation"] == "nearest"].itertuples():
        print(f"  nearest: {r.record_id} -> {r.aea_region} ({r.aea_region_distance_km} km outside every region)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
