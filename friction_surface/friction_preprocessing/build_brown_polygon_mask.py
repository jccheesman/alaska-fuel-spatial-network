#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_brown_polygon_mask.py

This script filters river polygons from the NHD for the river ice processing. 

Inputs:
- National Hydrology Dataset (NHD) for Alaska (Polygons)

Outputs:
- brown_river_polygons.shp: NHDArea polygons (ftype in {460=StreamRiver,
  364=Lake/Pond}) selected by the UNION of two criteria:
    a) polygon is within --point-buffer-m of a Brown reach point
       (selects polygons we have data for, including off-centerline
       polygons that the centerline misses)
    b) polygon is within --flowline-buffer-m of a Brown flowline
       (selects polygons that the named-river centerline passes through
       or close to — catches narrow or braided floodplain channels, 
       where reach points sit in one channel and the polygon is in a parallel 
  Together (a) and (b) cover both data-driven and geometry-driven
  polygon selection. Either alone leaves gaps, due to discrepencies betweent the two. 
  Together they enable the most extensive selection of all rivers in Alaska 

- brown_river_flowlines.shp: NHDFlowline filtered to the 30 Brown rivers
  by GNIS_Name. 

Usage:
    python build_brown_polygon_mask.py
    python build_brown_polygon_mask.py --nhd-dir path/to/NHD/Shape \\
                                       --reach-points path/to/reach.geojson
"""

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

BROWN_RIVER_NAMES = [
    "Alsek River", "Buckland River", "Chena River", "Chitina River",
    "Colville River", "Copper River", "Innoko River", "Kenai River",
    "Kobuk River", "Koyukuk River", "Kuparuk River", "Kuskokwim River",
    "Kvichak River", "Nenana River", "Noatak River",
    "North Fork Kuskokwim River", "Nushagak River", "Porcupine River",
    "Sagavanirktok River", "Salcha River", "Skwentna River",
    "South Fork Kuskokwim River", "Stikine River", "Stony River",
    "Susitna River", "Taku River", "Tanana River", "Teedriinjik River",
    "Yentna River", "Yukon River",
]

# NHDArea ftypes that can carry surface water for a river. 460 is
# StreamRiver (the wide-channel polygons); 364 is Lake/Pond (covers
# in-line lakes like Skilak on the Kenai, where reach points may sit
# inside a lake polygon rather than a stream polygon).
NHDAREA_KEEP_FTYPES = [460, 364]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--nhd-dir", default="data/NHD_extracted/Shape",
        help="Directory containing NHDArea.shp and NHDFlowline_*.shp",
    )
    parser.add_argument(
        "--reach-points", default="data/waterFilledMedians2000_2023.geojson",
        help="Brown reach points (drives polygon selection)",
    )
    parser.add_argument(
        "--output", default="data/brown_river_polygons.shp",
        help="Polygon output shapefile path",
    )
    parser.add_argument(
        "--flowlines-output", default="data/brown_river_flowlines.shp",
        help="Flowline output shapefile path",
    )
    parser.add_argument(
        "--point-buffer-m", type=float, default=2000.0,
        help=(
            "Buffer (m) applied to reach points before the polygon-containment "
            "join. 0 = strict point-in-polygon; 2000 m is the empirically-tuned "
            "default that balances reach-point precision against picking up "
            "off-centerline polygons. Higher values (e.g. 5000) start pulling "
            "in tributary polygons that happen to sit near reach points."
        ),
    )
    parser.add_argument(
        "--flowline-buffer-m", type=float, default=500.0,
        help=(
            "Buffer (m) applied to Brown flowlines for the geometry-driven "
            "selection criterion. Polygons that intersect any Brown flowline "
            "within this buffer are kept (in addition to those caught by "
            "--point-buffer-m). 500 m catches braided floodplain polygons the "
            "centerline runs through; higher (1000-2000 m) catches off-channel "
            "polygons too and increases overall coverage substantially."
        ),
    )
    args = parser.parse_args()

    nhd_dir = Path(args.nhd_dir)
    if not nhd_dir.exists():
        sys.exit(f"ERROR: {nhd_dir} not found. Use --nhd-dir to point at it.")

    reach_path = Path(args.reach_points)
    if not reach_path.exists():
        sys.exit(
            f"ERROR: {reach_path} not found. Use --reach-points to point at the"
            f" waterFilledMedians2000_2023.geojson."
        )

    # 1. Brown reach points — drive polygon selection.
    reach = gpd.read_file(reach_path).to_crs(3338)
    print(f"Reach points:                  {len(reach):,}")
    print(f"  Unique rivers:               {reach['GNIS_Name'].nunique()}")
    # Duplicate to unique locations — many points repeat across months.
    reach_unique = reach.drop_duplicates(subset="geometry").copy()
    print(f"  Unique reach locations:      {len(reach_unique):,}")

    # 2. Candidate NHDArea polygons - statewide. No name filter — the
    #    spatial join below selects only those that contain reach data.
    area = gpd.read_file(nhd_dir / "NHDArea.shp").to_crs(3338)
    candidates = area[area["ftype"].isin(NHDAREA_KEEP_FTYPES)].copy()
    print(
        f"NHDArea candidates (ftype in {NHDAREA_KEEP_FTYPES}): "
        f"{len(candidates):,} / {len(area):,}"
    )

    # 3. Brown-filtered flowlines — used both as the geometry-driven
    #    polygon selector below AND written out as brown_river_flowlines
    parts = []
    i = 0
    while (nhd_dir / f"NHDFlowline_{i}.shp").exists():
        fl = gpd.read_file(nhd_dir / f"NHDFlowline_{i}.shp")
        parts.append(fl[fl["gnis_name"].isin(BROWN_RIVER_NAMES)])
        i += 1
    if not parts:
        sys.exit(f"ERROR: no NHDFlowline_*.shp under {nhd_dir}")
    fl_brown = gpd.GeoDataFrame(
        pd.concat(parts, ignore_index=True), crs=parts[0].crs
    ).to_crs(3338)
    print(
        f"Brown flowline features:        {len(fl_brown):,}  "
        f"({fl_brown['gnis_name'].nunique()} of {len(BROWN_RIVER_NAMES)} rivers)"
    )

    # 4. Two-criteria polygon join, unioned. (a) reach-point containment
    #    with --point-buffer-m, (b) flowline intersection with
    #    --flowline-buffer-m. A polygon enters the output if it satisfies
    #    EITHER criterion. Each polygon gets a single gnis_name label;
    #    reach-point match wins (it's the data source), flowline label is
    #    fallback.
    candidates = candidates.reset_index(drop=True)
    candidates["_poly_idx"] = candidates.index
    # Drop the NHDArea-side gnis_name to avoid suffix collision with the
    # flowline join below.
    candidates_geom = candidates[["_poly_idx", "geometry"]].copy()

    # (a) reach-point join
    if args.point_buffer_m > 0:
        reach_buf = reach_unique[["GNIS_Name", "geometry"]].copy()
        reach_buf["geometry"] = reach_buf.geometry.buffer(args.point_buffer_m)
        rp_predicate = "intersects"
    else:
        reach_buf = reach_unique[["GNIS_Name", "geometry"]]
        rp_predicate = "contains"
    print(f"  Reach-point buffer:          {args.point_buffer_m:.0f} m")
    rp_joined = gpd.sjoin(candidates_geom, reach_buf,
                          predicate=rp_predicate, how="inner")
    rp_label = (rp_joined.sort_values("_poly_idx")
                         .drop_duplicates("_poly_idx", keep="first")
                         .set_index("_poly_idx")["GNIS_Name"])

    # (b) flowline join
    print(f"  Flowline buffer:             {args.flowline_buffer_m:.0f} m")
    fl_buf = fl_brown[["gnis_name", "geometry"]].copy()
    fl_buf["geometry"] = fl_brown.geometry.buffer(args.flowline_buffer_m)
    fl_joined = gpd.sjoin(candidates_geom, fl_buf,
                          predicate="intersects", how="inner")
    fl_label = (fl_joined.sort_values("_poly_idx")
                         .drop_duplicates("_poly_idx", keep="first")
                         .set_index("_poly_idx")["gnis_name"])

    # Union: reach-point label wins; flowline fills the gaps.
    poly_label = rp_label.combine_first(fl_label)
    print(f"  Reach-point matches:         {len(rp_label):,}")
    print(f"  Flowline matches:            {len(fl_label):,}")
    print(f"  Union (output polygons):     {len(poly_label):,}")

    out = candidates.set_index("_poly_idx").loc[poly_label.index].copy()
    out["gnis_name"] = poly_label
    out = out[["gnis_name", "ftype", "areasqkm", "geometry"]].reset_index(drop=True)

    # 5. Sanity-check coverage.
    print(f"Output polygons:               {len(out):,}")
    print("  By ftype:")
    for ft, c in out["ftype"].value_counts().items():
        print(f"    ftype {ft}: {c}")
    covered = out["gnis_name"].nunique()
    print(f"  Rivers with polygons:        {covered} / {len(BROWN_RIVER_NAMES)}")
    print(f"  Total mask area:             {out['areasqkm'].sum():.1f} km²")
    print("  Polygon count by river:")
    counts = out["gnis_name"].value_counts().sort_index()
    for name, n in counts.items():
        print(f"    {name:<35s} {n:>4d}")
    missing = sorted(set(BROWN_RIVER_NAMES) - set(out["gnis_name"]))
    if missing:
        print(f"  Rivers without any polygon matching either criterion:")
        for name in missing:
            print(f"    {name}")
        print("  (these rely entirely on the buffered NHDFlowline + kernel fallback)")

    out.to_file(args.output)
    print(f"\nWrote {args.output}  ({len(out):,} polygons)")

    # 6. Write Brown-filtered flowlines (loaded in step 3).
    fl_out = fl_brown[["gnis_name", "geometry"]].reset_index(drop=True)
    fl_out.to_file(args.flowlines_output)
    print(f"Wrote {args.flowlines_output}  ({len(fl_out):,} flowlines)")

    print("\nNext steps:")
    print(f"  1. Zip {args.output.rsplit('.', 1)[0]}.{{shp,shx,dbf,prj}}")
    print(f"  2. Zip {args.flowlines_output.rsplit('.', 1)[0]}.{{shp,shx,dbf,prj}}")
    print("  3. In river_ice_from_waterFilledMedians.js, set:")
    print("       NHD_BROWN_POLYGONS_ASSET    = '<polygon asset id>'")
    print("       NHD_FEATURECOLLECTION_ASSET = '<flowline asset id>'")
    print("       RIVER_MASK_ASSET            = null")
    print("       RIVER_MASK_SOURCE           = 'nhd_named'")


if __name__ == "__main__":
    main()
