#!/usr/bin/env python3
"""Fetch the Natural Earth basemap vectors used by the publication map (workflows/02_network_build/viz/plot_paper_network.py).

Downloads two 10 m Natural Earth layers from the `nvkelso/natural-earth-vector` GitHub mirror into
`data/basemap/` (gitignored) — run once; it skips files already present:

  * ne_10m_land.geojson                        — land polygons (Alaska + Canada landmass; the sea is
                                                  drawn as the axes background, so no ocean file is needed).
  * ne_10m_admin_0_boundary_lines_land.geojson — country borders (the AK <-> Canada line = context).

Natural Earth is public domain. Run: python3 workflows/02_network_build/03_fetch_basemap.py
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root
DEST = ROOT / "data" / "basemap"
BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson"
FILES = [
    "ne_10m_land.geojson",
    "ne_10m_admin_0_boundary_lines_land.geojson",
]


def fetch(name: str) -> Path:
    out = DEST / name
    if out.exists() and out.stat().st_size > 0:
        print(f"  have  {out.relative_to(ROOT)}  ({out.stat().st_size/1e6:.1f} MB)")
        return out
    url = f"{BASE}/{name}"
    print(f"  get   {name} <- {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "alaska-network-mmnet/basemap"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 (trusted public URL)
        data = r.read()
    out.write_bytes(data)
    print(f"  wrote {out.relative_to(ROOT)}  ({len(data)/1e6:.1f} MB)")
    return out


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    try:
        for f in FILES:
            fetch(f)
    except Exception as exc:  # noqa: BLE001
        print(f"\nbasemap download failed ({exc}).\n"
              f"The plot falls back to data/boundary.geojson (Alaska outline, no Canada landmass).",
              file=sys.stderr)
        return 1
    print(f"basemap ready in {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
