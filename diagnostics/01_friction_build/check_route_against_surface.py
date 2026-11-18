#!/usr/bin/env python3
"""Check ANY line layer against ANY friction surface, with cause diagnosis.

The general form of workflows/02_network_build/qa/00_check_manual_barge.py:
sample a vector route with the pipeline's own 75 m midpoint sampler
(fuel_network.geo_checks / fuel_network.weights) against a monthly or static
surface, report per-feature passability per month, and — with --causes —
explain every failing sample (land-cover class, sea ice, river-ice domain,
off-grid), separating land from ice by the minimum NoData over the months
tested. Optionally require every sample on a class of the water label
(--require-class marine: the nearshore barge rule).

Examples (from the repo root, in its environment):
    python diagnostics/01_friction_build/check_route_against_surface.py \
        --lines scratch/draft.shp --months 6,7,8,9,10 --require 7 --causes
    python diagnostics/01_friction_build/check_route_against_surface.py \
        --lines inputs/mannual_connections/mannual_connections.shp \
        --mode Barge --months all --require-class marine
    python diagnostics/01_friction_build/check_route_against_surface.py \
        --lines some_overland_route.gpkg --surface overland

Exit codes: 0 all pass; 1 failures; 3 surface absent (gate).
Output: table + failing-sample gpkg under outputs/diagnostics/01_friction_build/.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString

import repo_paths as rp
from fuel_network import geo_checks as gc
from friction_surface.friction_config import (
    FRICTION_NODATA, WATER_CLASS_MARINE, WATER_CLASS_RIVER)
from friction_surface.friction_paths import FRICTION_OUTPUT_DIR, WATER_CLASS_TIF

GATE_EXIT = 3
NODE_TOL = 50.0  # assembler vertex rounding: tested segments = built edges
CLASS_VALUE = {"marine": WATER_CLASS_MARINE, "river": WATER_CLASS_RIVER}


def split_segments(lines: gpd.GeoDataFrame, as_built: bool) -> gpd.GeoDataFrame:
    rows = []
    for i, r in lines.iterrows():
        g = r.geometry
        parts = [g] if g.geom_type == "LineString" else list(g.geoms)
        for part in parts:
            if as_built:
                cs = [(round(x / NODE_TOL) * NODE_TOL, round(y / NODE_TOL) * NODE_TOL)
                      for x, y, *_ in part.coords]
                for k, (a, b) in enumerate(zip(cs[:-1], cs[1:])):
                    if a != b:
                        rows.append({"feature": i, "segment": k, "geometry": LineString([a, b])})
            else:
                rows.append({"feature": i, "segment": 0, "geometry": part})
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=lines.crs)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lines", required=True)
    ap.add_argument("--mode", default=None,
                    help="keep only features whose mode-ish column equals this (e.g. Barge)")
    ap.add_argument("--surface", default="barge",
                    help="'barge' (monthly barge_MM.tif), 'overland', 'road_base', or a path; "
                         "a path containing {MM} is treated as monthly")
    ap.add_argument("--months", default="7", help="7 | 6,7,8 | all (monthly surfaces only)")
    ap.add_argument("--require", type=int, default=7,
                    help="the month every segment must pass (monthly surfaces)")
    ap.add_argument("--require-class", choices=["marine", "river"], default=None,
                    help="additionally require every sample on this water-label class")
    ap.add_argument("--whole-features", action="store_true",
                    help="test whole features instead of 50 m-rounded built segments")
    ap.add_argument("--causes", action="store_true", help="diagnose every failing sample")
    a = ap.parse_args()

    stack = Path(FRICTION_OUTPUT_DIR)
    if a.surface == "barge":
        tif_of = lambda m: stack / f"barge_{m:02d}.tif"
        monthly = True
    elif a.surface in ("overland", "road_base"):
        tif_of = lambda m: stack / f"{a.surface}.tif"
        monthly = False
    else:
        monthly = "{MM}" in a.surface
        tif_of = (lambda m: Path(a.surface.replace("{MM}", f"{m:02d}"))) if monthly \
            else (lambda m: Path(a.surface))
    months = ([int(m) for m in a.months.split(",")] if a.months != "all"
              else list(range(1, 13))) if monthly else [0]
    if monthly and a.require not in months:
        months.append(a.require)
    probe = tif_of(a.require if monthly else 0)
    if not probe.exists():
        print(f"GATE: {probe} absent — fetch or build the friction stack first")
        return GATE_EXIT

    lines = gpd.read_file(a.lines)
    if a.mode:
        col = next((c for c in lines.columns
                    if c.lower() in ("mode", "transport_mode", "transport", "modality", "type")), None)
        if col is None:
            print(f"FAIL: --mode given but no mode-ish column in {a.lines}")
            return 1
        lines = lines[lines[col].astype(str).str.strip().str.lower() == a.mode.lower()]
    if lines.crs is None or lines.crs.to_epsg() != 3338:
        print(f"FAIL: lines must be EPSG:3338, got {lines.crs}")
        return 1
    seg = split_segments(lines, as_built=not a.whole_features).reset_index(drop=True)
    print(f"{len(lines)} feature(s), {len(seg)} tested segment(s)")

    out_dir = rp.DIAGNOSTICS_OUT / "01_friction_build"
    out_dir.mkdir(parents=True, exist_ok=True)
    table = seg[["feature", "segment"]].copy()
    table["length_km"] = (seg.geometry.length / 1000).round(2)
    ndf_by_month = {}
    xy = seg_len = owner = None
    for m in sorted(set(months)):
        xy, seg_len, owner, vals = gc.sample_along(seg.geometry, seg.index, tif_of(m))
        _, ndf = gc.per_feature_nodata(owner, seg_len, vals, len(seg), FRICTION_NODATA)
        ndf_by_month[m] = ndf
        tag = f"{m:02d}" if monthly else "static"
        table[f"nodata_frac_{tag}"] = np.round(ndf, 4)
        table[f"passable_{tag}"] = ndf == 0
    min_ndf = np.minimum.reduce(list(ndf_by_month.values()))
    table["min_nodata_frac"] = np.round(min_ndf, 4)  # >0 in every tested month = land/coverage, not ice

    req_tag = f"{a.require:02d}" if monthly else "static"
    fails = ~table[f"passable_{req_tag}"].values

    if a.require_class:
        wc = Path(WATER_CLASS_TIF)
        if not wc.exists():
            print(f"GATE: {wc} absent — run workflows/01_friction_build/04_build_water_class.py")
            return GATE_EXIT
        import rasterio
        with rasterio.open(wc) as src:
            rows_, cols_ = rasterio.transform.rowcol(src.transform, xy[:, 0], xy[:, 1])
            rows_ = np.clip(np.asarray(rows_), 0, src.height - 1)
            cols_ = np.clip(np.asarray(cols_), 0, src.width - 1)
            cls = src.read(1)[rows_, cols_]
        bad = cls != CLASS_VALUE[a.require_class]
        frac = np.bincount(owner, weights=bad.astype(float), minlength=len(seg)) \
            / np.maximum(np.bincount(owner, minlength=len(seg)), 1)
        table[f"off_{a.require_class}_frac"] = np.round(frac, 4)
        fails |= frac > 0

    with pd.option_context("display.width", 220, "display.max_columns", 40):
        cols_show = ["feature", "segment", "length_km", "min_nodata_frac"] + \
            [c for c in table.columns if c.endswith(req_tag) or c.startswith("off_")]
        print(table.loc[fails | (table.min_nodata_frac > 0), cols_show].to_string(index=False)
              if (fails.any() or (table.min_nodata_frac > 0).any())
              else "(no segment touches NoData in any tested month)")
    table.to_csv(out_dir / "route_check.csv", index=False)

    if a.causes and fails.any():
        vals = gc.sample_raster(tif_of(a.require if monthly else 0), xy)
        nd = vals == FRICTION_NODATA
        if nd.any():
            causes = gc.classify_nodata_cause(xy[nd])
            cdf = pd.DataFrame({"feature": seg.feature.values[owner[nd]], "cause": causes})
            print("\nfailing-sample causes (required month):")
            print(cdf.groupby(["feature", "cause"]).size().unstack(fill_value=0).to_string())
            pts = gpd.GeoDataFrame({"cause": causes},
                                   geometry=gpd.points_from_xy(xy[nd, 0], xy[nd, 1]), crs=3338)
            pts.to_file(out_dir / "route_check_failures.gpkg", driver="GPKG")
            print(f"failure points -> {out_dir / 'route_check_failures.gpkg'}")

    n_fail = int(pd.Series(fails).groupby(seg.feature).any().sum())
    if fails.any():
        print(f"\nFAIL: {int(fails.sum())} segment(s) across {n_fail} feature(s)")
        return 1
    print(f"\nPASS: all {len(seg)} segments"
          + (f" (and 100% {a.require_class})" if a.require_class else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
