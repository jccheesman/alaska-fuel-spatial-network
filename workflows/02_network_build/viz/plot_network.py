#!/usr/bin/env python3
"""Render a static PNG of the final multimodal network (no QGIS needed).

Reads the build output (`output/03_network__{nodes,edges}.gpkg`) and draws the connected graph
with `mmnet.viz.plot_network`: edges colored by mode, hubs sized by capacity, ports/airports as
anchors. The view is clipped to the Alaska bounding box so a handful of off-map outliers (a few
air OD endpoints whose codes geocoded to non-Alaska airports) don't squash the state into a dot.

Writes `outputs/02_network_build/reports/figs/03_alaska_network.png`.

Usage:
    python workflows/02_network_build/viz/plot_network.py
"""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
warnings.filterwarnings("ignore")

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[3]  # repo root
PROJ = ROOT / "outputs" / "02_network_build"  # mmnet project dir: engine writes PROJ/output + PROJ/reports
sys.path.insert(0, str(ROOT))                      # make the vendored mmnet importable
os.environ.setdefault("NETWEAVE_PROFILE", str(ROOT / "workflows" / "02_network_build" / "profile.yaml"))
os.environ.setdefault("NETWEAVE_PROJECT", str(ROOT))

from mmnet import viz as mv  # noqa: E402

T = 3338
MARGIN_M = 50_000           # halo around the Alaska boundary bbox


def main() -> None:
    n = gpd.read_file(PROJ / "output" / "03_network__nodes.gpkg").to_crs(T)
    e = gpd.read_file(PROJ / "output" / "03_network__edges.gpkg").to_crs(T)
    ak = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(T)
    ports = gpd.read_file(ROOT / "data" / "raw" / "anchor_points" / "Ports_and_Harbors.geojson").to_crs(T)
    air = gpd.read_file(ROOT / "data" / "processed" / "air_nodes.geojson").to_crs(T)

    minx, miny, maxx, maxy = ak.total_bounds
    minx, miny, maxx, maxy = minx - MARGIN_M, miny - MARGIN_M, maxx + MARGIN_M, maxy + MARGIN_M

    # Keep nodes inside the window, and edges fully inside it (drops the few off-map outliers).
    n_ak = n.cx[minx:maxx, miny:maxy]
    eb = e.bounds
    inside = (eb.minx >= minx) & (eb.miny >= miny) & (eb.maxx <= maxx) & (eb.maxy <= maxy)
    e_ak = e[inside]
    dropped = len(e) - len(e_ak)

    print(f"in-view: {len(n_ak)}/{len(n)} nodes, {len(e_ak)}/{len(e)} edges "
          f"({dropped} off-map edges dropped) | types={e_ak['type'].value_counts().to_dict()}")

    png = mv.plot_network(
        n_ak, e_ak,
        title="Alaska multimodal fuel network — final connected graph",
        slug="03_alaska_network",
        point_overlays={"ports": ports.cx[minx:maxx, miny:maxy],
                        "airports": air.cx[minx:maxx, miny:maxy]},
        dpi=240,
        out_dir=PROJ / "reports" / "figs",
    )
    print(f"WROTE: {Path(png).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
