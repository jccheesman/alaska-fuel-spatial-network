#!/usr/bin/env python3
"""Split the user-authored manual-connections shapefile into per-mode line layers.

Some fuel hubs land disconnected in the automated build. The fix is a hand-drawn
`manual_connections` shapefile of line segments that tie each disconnected hub's local
network to the hub, snapped to nodes/edges of the existing network. It is the ONE
user-editable file for growing the network by hand: add a line, tag its `mode`, rebuild.

The mmnet engine assigns ONE mode per layer (per-feature attributes are dropped), so a
mixed-mode shapefile cannot enter as a single layer. This prep step reprojects the file to
the target CRS, validates each line's `mode` against the profile's declared modes, and
splits it into one interim GeoPackage per mode. The profile then reads each split file as a
generic line layer that reuses the mode's existing edge_label (Plane->Air, Barge->Waterway,
...), so nothing downstream (costing, edge types) needs to change. Lines snapped to existing
nodes weld automatically (1 m node tolerance) — no connection rule is required.

Source (committed, authored — NOT regenerable, so it lives under inputs/, not data/; opted in
via .gitignore like inputs/air/, NOT inside the zip-extracted data_for_network_build/ tree):
    inputs/mannual_connections/mannual_connections.shp

Outputs (regenerable; gitignored under data/interim):
    data/interim/manual_<mode-slug>.gpkg   one per mode present (e.g. manual_plane.gpkg)

If the source shapefile is absent this exits with the gate code (3) so a fresh clone that
has no manual connections still builds cleanly (run_all.sh treats 3 as "documented input
absent, skip").

Usage:
    python workflows/02_network_build/03_prep_manual_connections.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import yaml

ROOT = Path(__file__).resolve().parents[2]  # repo root
SRC = ROOT / "inputs" / "mannual_connections" / "mannual_connections.shp"
PROFILE = Path(__file__).resolve().parent / "profile.yaml"
OUT_DIR = ROOT / "data" / "interim"

GATE_EXIT = 3  # matches workflows/_lib.sh `gate`: documented input absent -> skip
MODE_COL_CANDIDATES = ("mode", "transport_mode", "transport", "modality", "type")


def _mode_slug(mode: str) -> str:
    """Filename slug for a mode name: 'Ice Road' -> 'ice_road', 'Plane' -> 'plane'."""
    return "_".join(mode.strip().lower().split())


def _target_crs() -> int:
    prof = yaml.safe_load(PROFILE.read_text())
    return int(prof["crs"]["target"])


def _profile_modes() -> list[str]:
    """Mode names declared in the profile (the allowed set for the `mode` tag)."""
    prof = yaml.safe_load(PROFILE.read_text())
    return [m["name"] for m in prof.get("modes", [])]


def _find_mode_col(cols) -> str:
    low = {c.lower(): c for c in cols}
    for cand in MODE_COL_CANDIDATES:
        if cand in low:
            return low[cand]
    raise SystemExit(
        f"manual_connections has no mode column (looked for {MODE_COL_CANDIDATES}); "
        f"got columns {list(cols)}. Tag each line with its transport mode."
    )


def prep_manual_connections() -> None:
    if not SRC.exists():
        print(f"[gate] no manual connections at {SRC.relative_to(ROOT)} — skipping "
              f"(add the shapefile there to grow the network by hand).")
        sys.exit(GATE_EXIT)

    target_crs = _target_crs()
    valid_modes = _profile_modes()
    # case-insensitive lookup from the shapefile's tag to the canonical profile mode name
    canon = {m.lower(): m for m in valid_modes}

    gdf = gpd.read_file(SRC).to_crs(target_crs)
    n_raw = len(gdf)
    mode_col = _find_mode_col(gdf.columns)

    # geometry hygiene: keep only real lines (mirrors io_readers._read_lines)
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
    gdf = gdf[gdf.geometry.geom_type.isin(["LineString", "MultiLineString"])]
    gdf = gdf.explode(index_parts=False, ignore_index=True)
    gdf = gdf[gdf.geometry.geom_type == "LineString"]
    gdf = gdf[gdf.geometry.length > 0].copy()

    # normalize + validate the mode tag against the profile's declared modes
    raw_mode = gdf[mode_col].astype(str).str.strip()
    gdf["mode"] = raw_mode.str.lower().map(canon)
    unknown = sorted(set(raw_mode[gdf["mode"].isna()]))
    if unknown:
        raise SystemExit(
            f"manual_connections column '{mode_col}' has values not in the profile modes "
            f"{valid_modes}: {unknown}. Fix the tags or add the mode to profile.yaml."
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"manual_connections: {len(gdf)}/{n_raw} lines kept from "
          f"{SRC.relative_to(ROOT)} (EPSG:{target_crs}); mode column '{mode_col}'.")
    for mode, sub in gdf.groupby("mode"):
        out = OUT_DIR / f"manual_{_mode_slug(mode)}.gpkg"
        sub[["mode", "geometry"]].reset_index(drop=True).to_file(out, driver="GPKG")
        print(f"  {mode:<10} {len(sub):>4} lines -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    prep_manual_connections()
