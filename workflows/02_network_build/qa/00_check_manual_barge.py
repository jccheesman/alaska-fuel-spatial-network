#!/usr/bin/env python3
"""Check the authored manual Barge lines against the barge surface BEFORE the build.

Workflow 03 marks a Waterway edge impassable for a month if ONE 75 m sample
falls on a NoData pixel of barge_MM.tif. This check applies the same test, with
the pipeline's own sampler (fuel_network.weights), to the manual-connections
Barge features before they enter the network, and additionally requires every
sample to sit on MARINE pixels of the water-class label (nearshore rule: lines
never follow a river).

A failing feature fails the stage, unless its shapefile row is listed in
inputs/network_qc/accepted_barge_exceptions.csv (kind=line) — the one tracked
exception today is the Skwentna river line, which predates the nearshore rule.

Exits GATE (3) when the friction stack is absent (fresh clone without rasters);
the water-class check degrades to a warning when only that raster is absent.

Usage:
    python workflows/02_network_build/qa/00_check_manual_barge.py
    python workflows/02_network_build/qa/00_check_manual_barge.py --lines <draft.shp> --months 6,7,8,9,10
Options: --months 7 | 6,7 | all (default 7) --require 7
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from shapely.geometry import LineString

import repo_paths as rp
from fuel_network.weights import SAMPLE_SPACING_M, build_sample_arrays, edge_weighted_stats, sample_raster
from friction_surface.friction_config import WATER_CLASS_MARINE
from friction_surface.friction_paths import FRICTION_OUTPUT_DIR, WATER_CLASS_TIF

GATE_EXIT = 3
NODE_TOL = 50.0  # mmnet.build waterway vertex rounding — tested segments = built edges
EXCEPTIONS = rp.INPUTS / "network_qc" / "accepted_barge_exceptions.csv"


def line_exceptions() -> set[int]:
    if not EXCEPTIONS.exists():
        return set()
    with open(EXCEPTIONS, newline="") as fh:
        return {int(r["key"]) for r in csv.DictReader(fh) if r["kind"] == "line"}


def segments(lines: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    rows = []
    for i, r in lines.iterrows():
        g = r.geometry
        for part in ([g] if g.geom_type == "LineString" else list(g.geoms)):
            cs = [(round(x / NODE_TOL) * NODE_TOL, round(y / NODE_TOL) * NODE_TOL)
                  for x, y, *_ in part.coords]
            for k, (a, b) in enumerate(zip(cs[:-1], cs[1:])):
                if a != b:
                    rows.append({"line": i, "segment": k, "geometry": LineString([a, b])})
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=lines.crs)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lines", default=str(rp.MANUAL_CONNECTIONS))
    ap.add_argument("--months", default="7")
    ap.add_argument("--require", type=int, default=7)
    a = ap.parse_args()

    lines_path = Path(a.lines)
    if not lines_path.exists():
        print(f"GATE: {lines_path} absent (optional user layer) — nothing to check")
        return GATE_EXIT
    stack = Path(FRICTION_OUTPUT_DIR)
    months = list(range(1, 13)) if a.months == "all" else [int(m) for m in a.months.split(",")]
    if a.require not in months:
        months.append(a.require)
    if not (stack / f"barge_{a.require:02d}.tif").exists():
        print(f"GATE: friction stack absent ({stack}) — fetch or build workflow 01 first")
        return GATE_EXIT

    lines = gpd.read_file(lines_path)
    col = next((c for c in lines.columns if c.lower() == "mode"), None)
    if col:
        lines = lines[lines[col].astype(str).str.strip().str.lower() == "barge"]
    if lines.crs is None or lines.crs.to_epsg() != 3338:
        print(f"FAIL: lines must be EPSG:3338, got {lines.crs}")
        return 1
    seg = segments(lines).reset_index(drop=True)
    xy, seg_len, owner = build_sample_arrays(seg.geometry, seg.index)
    print(f"{len(lines)} Barge line(s), {len(seg)} segments, {len(xy):,} samples "
          f"at {SAMPLE_SPACING_M:.0f} m")

    fail_rows = np.zeros(len(seg), dtype=bool)
    for m in sorted(set(months)):
        tif = stack / f"barge_{m:02d}.tif"
        if not tif.exists():
            print(f"FAIL: {tif} missing")
            return 1
        vals = sample_raster(tif, xy)
        _, ndf = edge_weighted_stats(owner, seg_len, vals, len(seg))
        if m == a.require:
            fail_rows = ndf > 0
        n_bad = int((ndf > 0).sum())
        if n_bad:
            print(f"  month {m:2d}: {n_bad} segment(s) touch NoData")

    # marine-only rule
    wc = Path(WATER_CLASS_TIF)
    if wc.exists():
        with rasterio.open(wc) as src:
            rows_, cols_ = rasterio.transform.rowcol(src.transform, xy[:, 0], xy[:, 1])
            rows_ = np.clip(np.asarray(rows_), 0, src.height - 1)
            cols_ = np.clip(np.asarray(cols_), 0, src.width - 1)
            cls = src.read(1)[rows_, cols_]
        nonmar = cls != WATER_CLASS_MARINE
        if nonmar.any():
            bad_seg = np.unique(owner[nonmar])
            print(f"  water-class: {int(nonmar.sum())} sample(s) on non-marine pixels "
                  f"(segments {bad_seg[:10].tolist()}{'...' if len(bad_seg) > 10 else ''})")
            fail_rows[bad_seg] = True
    else:
        print(f"  WARNING: {wc} absent — marine-only rule not checked "
              "(run workflows/01_friction_build/04_build_water_class.py)")

    excused = line_exceptions()
    bad_lines = sorted(set(seg.loc[fail_rows, "line"]))
    real = [ln for ln in bad_lines if ln not in excused]
    for ln in bad_lines:
        tag = "accepted exception" if ln in excused else "FAILS"
        print(f"  line (shp row) {ln}: {int((fail_rows & (seg.line == ln)).sum())} "
              f"failing segment(s) in month {a.require} — {tag}")
    if real:
        print(f"FAIL: {len(real)} manual Barge line(s) not passable/marine in month "
              f"{a.require} and not excused: rows {real}")
        return 1
    print(f"PASS: every manual Barge line is on valid marine barge pixels in month {a.require}"
          + (f" ({len(bad_lines)} accepted exception(s))" if bad_lines else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
