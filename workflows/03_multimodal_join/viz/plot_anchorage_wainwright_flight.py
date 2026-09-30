#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_anchorage_wainwright_flight.py

Simple illustrative figure: a straight "flight path" line from Anchorage to
Wainwright, Alaska, drawn over the Alaska state border and annotated with the
great-circle mileage of the segment.

Uses the committed Alaska boundary (data/boundary.geojson, WGS84) and projects
everything to Alaska Albers (EPSG:3338) so the map reads with correct shape.
The plotted line is straight in projected space (a map straight line); the
labelled distance is the true geodesic (great-circle) distance in statute miles.

No CLI args. Writes into outputs/figures/.

Usage:
    python plot_anchorage_wainwright_flight.py
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pyproj import Geod
from shapely.geometry import LineString, Point

ROOT = Path(__file__).resolve().parents[3]
BOUNDARY = ROOT / "data" / "boundary.geojson"
OUT_DIR = ROOT / "outputs" / "figures"

# (lon, lat) in WGS84
ANCHORAGE = (-149.9003, 61.2181)
WAINWRIGHT = (-160.0369, 70.6376)

MAP_CRS = "EPSG:3338"  # Alaska Albers


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Great-circle distance on the WGS84 ellipsoid -> statute miles.
    geod = Geod(ellps="WGS84")
    _, _, dist_m = geod.inv(
        ANCHORAGE[0], ANCHORAGE[1], WAINWRIGHT[0], WAINWRIGHT[1]
    )
    miles = dist_m / 1609.344

    # Alaska border.
    ak = gpd.read_file(BOUNDARY).to_crs(MAP_CRS)

    # Cities + flight line, projected to the map CRS.
    pts = gpd.GeoSeries(
        [Point(*ANCHORAGE), Point(*WAINWRIGHT)], crs="EPSG:4326"
    ).to_crs(MAP_CRS)
    anc_xy, wai_xy = (pts.iloc[0].x, pts.iloc[0].y), (pts.iloc[1].x, pts.iloc[1].y)
    line = gpd.GeoSeries(
        [LineString([Point(*ANCHORAGE), Point(*WAINWRIGHT)])], crs="EPSG:4326"
    ).to_crs(MAP_CRS)

    fig, ax = plt.subplots(figsize=(9, 8))
    ak.plot(ax=ax, facecolor="#eef2f4", edgecolor="#607d8b", linewidth=0.8)
    line.plot(ax=ax, color="#d62728", linewidth=2.0, linestyle="--", zorder=3)

    ax.scatter(*anc_xy, s=55, color="#1f3b57", zorder=4)
    ax.scatter(*wai_xy, s=55, color="#1f3b57", zorder=4)
    ax.annotate("Anchorage", anc_xy, textcoords="offset points",
                xytext=(8, -12), fontsize=10, fontweight="bold")
    ax.annotate("Wainwright", wai_xy, textcoords="offset points",
                xytext=(8, 6), fontsize=10, fontweight="bold")

    # Mileage label at the midpoint of the projected line.
    mid = line.iloc[0].interpolate(0.5, normalized=True)
    ax.annotate(
        f"{miles:,.0f} mi",
        (mid.x, mid.y),
        textcoords="offset points",
        xytext=(12, 0),
        fontsize=11,
        color="#d62728",
        fontweight="bold",
    )

    ax.set_title("Anchorage → Wainwright flight path", fontsize=13)
    ax.set_axis_off()
    ax.set_aspect("equal")
    fig.tight_layout()

    out = OUT_DIR / "anchorage_wainwright_flight.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"great-circle distance: {miles:,.1f} statute miles")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
