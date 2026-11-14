#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nhd_river_marine_check.py — classify NWN waterway segments against NHD.

Membership test, run on the machine holding the NHD download:

    a NWN segment is a RIVER iff enough of its length lies within
    --buffer-m of an NHD flowline of an accepted FType.

Everything else is salt water, and river ice must not migrate there. The
default is deny: a segment must affirmatively match NHD to be river-gated.

FType handling — this is the part that matters:
    460 StreamRiver     real watercourses
    558 ArtificialPath  centerline through waterbodies, which includes
                        estuaries and bays. Scored SEPARATELY, because on
                        its own it will match Wrangell Narrows and Cook
                        Inlet. The CSV carries both so 460-only and
                        460+558 can be compared before committing.
    566 Coastline       NEVER accepted. Traces the shoreline; would match
                        every channel in Southeast Alaska. Scored anyway,
                        purely so the report can show what it would have
                        done.

Outputs (both small — send both back):
    <out>.csv           one row per NWN segment, per-FType coverage
    <out>_nhd_near.gpkg the NHD flowlines within --prescreen-m of the NWN
                        network, with ftype/gnis_name. A few MB. This is
                        what lets the river domain be rebuilt downstream
                        without moving 4.6 GB.

Reads the extracted Shape/ directory, or straight out of the zip via
GDAL /vsizip/ if you point --nhd at the .zip instead.

Requires geopandas >= 0.13, pyogrio, shapely >= 2:

    python diagnostics/01_friction_build/nhd_river_marine_check.py

Defaults assume the NHD download extracted under inputs/river_ice_work/
and the NWN shapefile in place. Expect 10-40 minutes; it prints progress
and an ETA per chunk.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
from shapely import STRtree
from shapely.ops import unary_union

import repo_paths as rp
from friction_surface import friction_paths as fp

WORK_CRS = "EPSG:3338"
FT_STREAM, FT_ARTIFICIAL, FT_COASTLINE = 460, 558, 566
READ_FTYPES = (FT_STREAM, FT_ARTIFICIAL, FT_COASTLINE)
WANT_COLS = ("ftype", "gnis_name")


def find_flowlines(nhd: Path) -> list[tuple[str, str | None]]:
    """Return [(ogr_path, layer_or_None), ...] for every NHDFlowline part."""
    if nhd.is_dir():
        hits = sorted(nhd.rglob("NHDFlowline*.shp"))
        if not hits:
            sys.exit(f"No NHDFlowline*.shp under {nhd}")
        return [(str(h), None) for h in hits]
    if nhd.suffix.lower() == ".zip":
        layers = [str(r[0]) for r in pyogrio.list_layers(f"/vsizip/{nhd}")]
        flow = [n for n in layers if n.lower().startswith("nhdflowline")]
        if not flow:
            sys.exit(f"No NHDFlowline layer in {nhd}. Layers: {layers[:20]}")
        return [(f"/vsizip/{nhd}", n) for n in flow]
    sys.exit(f"--nhd must be a directory or .zip, got {nhd}")


def pick_columns(path: str, layer: str | None) -> list[str]:
    """Resolve WANT_COLS against the file's actual field casing."""
    info = pyogrio.read_info(path, layer=layer)
    actual = {str(f).lower(): str(f) for f in info["fields"]}
    missing = [c for c in WANT_COLS if c not in actual]
    if "ftype" in missing:
        sys.exit(f"{path}: no ftype field. Fields: {list(info['fields'])[:30]}")
    return [actual[c] for c in WANT_COLS if c in actual]


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nhd", default=str(rp.RIVER_ICE_WORK / "NHD_extracted" / "Shape"))
    ap.add_argument("--nwn", default=fp.NETWORK_FILES["waterways"])
    ap.add_argument("--out", default=str(rp.ANALYSIS / "nwn_nhd_classification.csv"))
    ap.add_argument("--buffer-m", type=float, default=200.0,
                    help="match distance; 200 matches the river-ice "
                         "pipeline's own FLOWLINE_BUFFER_M (default 200)")
    ap.add_argument("--prescreen-m", type=float, default=1000.0,
                    help="NHD lines this close to the network are exported")
    ap.add_argument("--chunk", type=int, default=100_000)
    args = ap.parse_args()

    t0 = time.time()
    nwn = gpd.read_file(args.nwn)
    if nwn.crs is None:
        sys.exit("NWN shapefile has no CRS")
    nwn = nwn.to_crs(WORK_CRS)
    n = len(nwn)
    seg_len = nwn.geometry.length.to_numpy()
    print(f"NWN: {n} segments, {seg_len.sum()/1000:,.0f} km")

    screen = unary_union(nwn.geometry.buffer(args.prescreen_m).values)
    seg_buf = list(nwn.geometry.buffer(args.buffer_m).values)
    tree = STRtree(seg_buf)

    hits = {f: [[] for _ in range(n)] for f in READ_FTYPES}
    keep_rows = []

    parts = find_flowlines(Path(args.nhd))
    print(f"{len(parts)} flowline part(s) to scan")
    use_where = True
    scanned = kept = 0

    for path, layer in parts:
        cols = pick_columns(path, layer)
        total = pyogrio.read_info(path, layer=layer)["features"]
        label = Path(path).name + (f":{layer}" if layer else "")
        print(f"\n{label}: {total:,} features")

        offset = 0
        while offset < total:
            kw = dict(layer=layer, columns=cols, skip_features=offset,
                      max_features=args.chunk)
            if use_where:
                kw["where"] = "ftype IN ({})".format(
                    ",".join(str(f) for f in READ_FTYPES))
            try:
                chunk = pyogrio.read_dataframe(path, **kw)
            except Exception as exc:                       # noqa: BLE001
                if use_where:
                    print(f"  note: attribute pushdown unavailable ({exc}); "
                          "filtering in pandas instead")
                    use_where = False
                    continue
                raise

            # NOTE: do NOT break on an empty chunk. With a pushdown filter an
            # interior chunk can legitimately come back empty while features
            # remain further in. Loop on offset vs total instead.
            offset += args.chunk
            scanned += args.chunk
            if len(chunk) == 0:
                continue

            low = {c.lower(): c for c in chunk.columns}
            ft = pd.to_numeric(chunk[low["ftype"]], errors="coerce")
            chunk = chunk[ft.isin(READ_FTYPES)]
            if len(chunk) == 0:
                continue
            if chunk.crs is None:
                sys.exit(f"{label}: flowlines have no CRS")
            chunk = chunk.to_crs(WORK_CRS)
            ft = pd.to_numeric(chunk[low["ftype"]], errors="coerce").to_numpy()

            near = chunk.geometry.intersects(screen).to_numpy()
            chunk, ft = chunk[near], ft[near]
            if len(chunk) == 0:
                pct = 100 * min(offset, total) / total
                print(f"  {min(offset,total):>9,}/{total:,} ({pct:4.1f}%) "
                      f"kept {kept:,}  {time.time()-t0:,.0f}s")
                continue

            kept += len(chunk)
            keep_rows.append(chunk.assign(**{"ftype_num": ft}))
            for geom, f in zip(chunk.geometry.values, ft):
                for j in tree.query(geom):
                    piece = seg_buf[j].intersection(geom)
                    if not piece.is_empty:
                        hits[int(f)][j].append(piece)

            pct = 100 * min(offset, total) / total
            rate = min(offset, total) / max(time.time() - t0, 1e-9)
            print(f"  {min(offset,total):>9,}/{total:,} ({pct:4.1f}%) "
                  f"kept {kept:,}  {time.time()-t0:,.0f}s  "
                  f"~{(total-min(offset,total))/max(rate,1):,.0f}s left in part")

    print("\nresolving per-segment coverage ...")
    frac = {f: np.zeros(n) for f in READ_FTYPES}
    for f, per_seg in hits.items():
        for j, pieces in enumerate(per_seg):
            if not pieces or seg_len[j] == 0:
                continue
            cover = unary_union(pieces).buffer(args.buffer_m)
            frac[f][j] = nwn.geometry.iloc[j].intersection(cover).length / seg_len[j]

    def field(name):
        return nwn[name] if name in nwn.columns else pd.Series([""] * n)

    out = pd.DataFrame({
        "key_id": field("KEY_ID"),
        "rivername": field("RIVERNAME"),
        "linkname": field("LINKNAME"),
        "geo_class": field("GEO_CLASS"),
        "state": field("STATE"),
        "wtwy_type": field("WTWY_TYPE"),
        "length_km": (seg_len / 1000).round(2),
        "frac_streamriver_460": frac[FT_STREAM].round(4),
        "frac_artificialpath_558": frac[FT_ARTIFICIAL].round(4),
        "frac_coastline_566": frac[FT_COASTLINE].round(4),
    })
    out["river_strict_460"] = out["frac_streamriver_460"] >= 0.30
    out["river_with_558"] = out[["frac_streamriver_460",
                                 "frac_artificialpath_558"]].max(axis=1) >= 0.30

    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest, index=False)

    gpkg = dest.with_name(dest.stem + "_nhd_near.gpkg")
    if keep_rows:
        near_gdf = gpd.GeoDataFrame(pd.concat(keep_rows, ignore_index=True),
                                    crs=WORK_CRS)
        near_gdf.to_file(gpkg, driver="GPKG", layer="nhd_near_nwn")
        gsize = gpkg.stat().st_size / 1e6
    else:
        gsize = 0.0

    print(f"\nscanned {scanned:,} features, kept {kept:,} near the network")
    print(f"river by 460 only : {int(out['river_strict_460'].sum())} of {n}")
    print(f"river by 460+558  : {int(out['river_with_558'].sum())} of {n}")
    print(f"would match on coastline 566 alone: "
          f"{int((out['frac_coastline_566'] >= 0.30).sum())} "
          "(why 566 is excluded)")
    print(f"\nwrote {dest} ({dest.stat().st_size/1024:.0f} KB)")
    print(f"wrote {gpkg} ({gsize:.1f} MB)")
    print(f"total {time.time()-t0:,.0f}s. Send back BOTH files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
