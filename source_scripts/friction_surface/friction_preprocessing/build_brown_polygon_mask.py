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

# ---------------------------------------------------------------------------
# Marine exclusion
# ---------------------------------------------------------------------------
# A polygon is admitted WHOLE if any part of it comes within --point-buffer-m
# of a reach point or --flowline-buffer-m of a flowline. One graze at a river
# mouth therefore drags an entire adjoining waterbody into the mask, and four
# of them are salt water:
#
#   Stikine River    ftype 364  225.1 km2  Dry Strait / Stikine delta front,
#                                          on the Petersburg approach
#   Porcupine River  ftype 364  141.0 km2  Cross Sound / Chatham Strait,
#                                          ~1,100 km from the Porcupine. The
#                                          label is a first-match artifact,
#                                          not a location.
#   Kenai River      ftype 364    4.8 km2  Kenai River mouth, Cook Inlet
#   Kuparuk River    ftype 364    0.5 km2  Beaufort coast
#
# Between them they place 396 cells of the MARINE waterway network inside the
# river-ice mask, so the IDW writes p_ice over Dry Strait and Cross Sound and
# barges freeze out of Southeast Alaska in winter. All four are ftype 364; no
# ftype 460 polygon touches salt water.
#
# Dropping them costs 371 km2 (3.7% of the polygon mask) and 315 cells of
# river-network coverage: 89.8% -> 89.5%. Two alternatives were measured and
# are worse:
#
#   drop ftype 364 entirely     loses 1,130 km2 and the in-line lakes that
#                               364 was included for (Skilak on the Kenai)
#   clip polygons by the        removes only 11 of the 396 cells — at 150 m
#   marine network              with all_touched rasterization the clipped
#                               edge still shares pixels with the network line
#
# Pass --no-marine-clip to reproduce the pre-fix mask.
MARINE_CLIP_DEFAULT_WATERWAY = (
    "../../../inputs/data_for_network_build/water_networks/"
    "waterways_network_ak_albers.shp"
)


def drop_marine_polygons(polys, waterway_shp, verbose=True):
    """Remove NHDArea polygons that intersect a MARINE waterway segment.

    "Marine" means an NWN segment whose KEY_ID is not in
    friction_config.RIVER_SEGMENT_KEY_IDS — the same reviewed river/marine
    split the friction surface uses, so the two cannot disagree about which
    segments are salt water.

    Returns (kept, dropped). The friction_config import is deferred and
    optional so this script still runs standalone from its own directory;
    when it is unavailable the clip is skipped LOUDLY rather than silently.
    """
    try:
        from friction_surface.friction_config import RIVER_SEGMENT_KEY_IDS
    except ImportError:
        print(
            "  WARNING: friction_surface.friction_config is not importable, "
            "so the marine clip cannot run and the mask will include salt "
            "water (Dry Strait, Cross Sound). Run from the repo root, or with "
            "PYTHONPATH=source_scripts, or pass --no-marine-clip to accept "
            "the unclipped mask deliberately."
        )
        return polys, polys.iloc[0:0]

    way = gpd.read_file(waterway_shp).to_crs(polys.crs)
    key = (way["KEY_ID"].fillna("").astype(str)
           .str.strip().str.strip("'").str.strip())
    marine = way[~key.isin(RIVER_SEGMENT_KEY_IDS)]
    if marine.empty:
        raise RuntimeError(
            f"{waterway_shp}: 0 of {len(way)} segments classified marine. The "
            "KEY_ID join failed; refusing to skip the marine clip silently."
        )
    geom = marine.geometry
    merged = geom.union_all() if hasattr(geom, "union_all") else geom.unary_union

    # NHDArea contains topologically invalid polygons (self-intersections);
    # older GEOS raises "TopologyException: side location conflict" on
    # intersects() instead of tolerating them. Repair ONLY for the test --
    # kept/dropped rows still carry the original geometry, and the arcpy
    # pipeline runs its own RepairGeometry downstream.
    test_geom = polys.geometry
    invalid = ~test_geom.is_valid
    if invalid.any():
        print(f"  Marine clip: repairing {int(invalid.sum())} invalid "
              "polygon(s) for the intersects test only")
        try:
            from shapely.validation import make_valid as _make_valid
            repaired = test_geom[invalid].apply(_make_valid)
        except ImportError:                      # very old shapely
            repaired = test_geom[invalid].buffer(0)
        test_geom = test_geom.copy()
        test_geom[invalid] = repaired
    hits = test_geom.intersects(merged)
    kept, dropped = polys[~hits], polys[hits]
    if verbose:
        print(f"  Marine clip: {len(marine):,} marine NWN segments")
        print(f"    dropped {len(dropped)} polygon(s), "
              f"{dropped['areasqkm'].sum():.1f} km2")
        for _, r in dropped.sort_values("areasqkm", ascending=False).iterrows():
            print(f"      {r['gnis_name']:<26} ftype {int(r['ftype'])} "
                  f"{r['areasqkm']:>8.1f} km2")
    return kept, dropped


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
    parser.add_argument(
        "--waterway", default=MARINE_CLIP_DEFAULT_WATERWAY,
        help=(
            "NWN waterway shapefile used to identify marine segments for the "
            "post-join marine clip (default resolves to "
            "inputs/data_for_network_build/water_networks/ from this "
            "script's directory)."
        ),
    )
    parser.add_argument(
        "--no-marine-clip", dest="marine_clip", action="store_false",
        help=(
            "Skip the marine clip and reproduce the pre-fix mask, which puts "
            "396 marine waterway cells inside the river-ice domain."
        ),
    )
    parser.set_defaults(marine_clip=True)
    args = parser.parse_args()

    if args.marine_clip and not Path(args.waterway).exists():
        alt = Path(__file__).resolve().parent / MARINE_CLIP_DEFAULT_WATERWAY
        if alt.exists():
            args.waterway = str(alt)
        else:
            sys.exit(
                f"ERROR: waterway shapefile not found at {args.waterway}. "
                "Pass --waterway, or --no-marine-clip to build without it "
                "(which reinstates the salt-water leak)."
            )

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

    # 4b. Marine clip. Must run AFTER the union join, because the whole point
    #     is that the join admits polygons wholesale — see the comment block
    #     on drop_marine_polygons.
    if args.marine_clip:
        before = len(out)
        out, dropped = drop_marine_polygons(out, args.waterway, verbose=True)
        out = out.reset_index(drop=True)
        print(f"  Polygons after marine clip:  {len(out):,} (was {before:,})")
    else:
        print("  Marine clip DISABLED (--no-marine-clip): the mask will "
              "include salt water at Dry Strait and Cross Sound.")

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
        print("  Rivers without any polygon matching either criterion:")
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
