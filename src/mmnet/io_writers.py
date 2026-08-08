"""Artifact writers. GeoPackage for vectors (QGIS-openable), CSV for tables."""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from .config import project_root


def output_dir() -> Path:
    """The current project's `output/` dir (resolved at call time; see config.project_root)."""
    return project_root() / "output"


def out_path(name: str, out_dir: str | Path | None = None) -> Path:
    """Absolute path for `name` under `out_dir` (or the project output dir), creating the dir."""
    base = Path(out_dir) if out_dir else output_dir()
    base.mkdir(parents=True, exist_ok=True)
    return base / name


def write_gdf(gdf: gpd.GeoDataFrame, name: str, out_dir: str | Path | None = None) -> Path:
    """Write `gdf` to `<out_dir>/name` as a GeoPackage; return the path."""
    p = out_path(name, out_dir)
    gdf.to_file(p, driver="GPKG")
    return p
