# -*- coding: utf-8 -*-
"""friction_preflight.py

Fail-fast input validation for the friction-surface pipeline.

Checks every raster write_friction_stack will touch BEFORE any work starts:
existence, CRS, resolution, grid alignment (transform + shape), dtype
sanity, and value-range spot checks. One canonical grid is established
from lulc.tif and everything else is compared against it.

Two outcomes per layer:
  OK     — matches the canonical grid exactly.
  FATAL  — missing file, CRS mismatch, resolution mismatch, transform
           misalignment (sub-pixel or extent), or out-of-range values.
           Pipeline must not run.

Grid alignment is an upstream prerequisite of this stage: permafrost is
snapped by `friction_preprocessing/align_permafrost.py`, river_ice by the
arcpy pipeline's Step 7 alignment in `river_ice_full_pipeline.py`, and
slope / lulc / sea_ice come from the GEE export pinned to the canonical
crsTransform. The loaders in `friction_surface.py` require inputs already
on the canonical grid (no WarpedVRT fallback), so any drift surfaced here
must be fixed at the source.

Usage:
    from friction_surface.friction_preflight import run_preflight
    run_preflight(input_dir, modes=MODES, months=range(1, 13))  # raises

    # or from the shell (from the project root):
    python -m friction_surface.friction_preflight [input_dir]
"""

from __future__ import annotations
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
import numpy as np
import rasterio
from .friction_config import MODES
from .friction_paths import get_raster_dir

logger = logging.getLogger(__name__)

# Tolerance (in CRS units, meters for EPSG:3338) when comparing transform
# origins. Catches half-pixel shifts without tripping on float noise.
ORIGIN_TOL_M = 0.01
RES_TOL_M = 1e-6


@dataclass
class LayerReport:
    key: str
    path: Path
    status: str = "OK"            # OK | FATAL
    issues: list[str] = field(default_factory=list)
    crs: str | None = None
    shape: tuple[int, int] | None = None
    res: tuple[float, float] | None = None
    dtype: str | None = None
    nodata: float | None = None

    def flag(self, status: str, msg: str) -> None:
        order = {"OK": 0, "FATAL": 1}
        if order[status] > order[self.status]:
            self.status = status
        self.issues.append(msg)


class PreflightError(RuntimeError):
    """Raised when one or more input layers fail preflight."""

    def __init__(self, reports: list[LayerReport]):
        self.reports = reports
        fatal = [r for r in reports if r.status == "FATAL"]
        super().__init__(
            f"{len(fatal)} input layer(s) failed preflight:\n"
            + format_report(reports, only_problems=True)
        )


def _expected_layers(
    input_dir: Path,
    modes: Iterable[str],
    months: Iterable[int],
) -> dict[str, Path]:
    """Enumerate every raster the pipeline will open, keyed by logical name.

    All inputs are mode-independent (the overland raster is pure terrain and
    reads no road/ice-road corridor mask), so `modes` is accepted for
    signature symmetry with the pipeline but does not change the layer set.
    """
    layers: dict[str, Path] = {
        "slope": input_dir / "slope.tif",
        "lulc": input_dir / "lulc.tif",
        "permafrost": input_dir / "permafrost.tif",
    }
    for m in months:
        layers[f"sea_ice_{m:02d}"] = input_dir / "sea_ice" / f"sea_ice_{m:02d}.tif"
        layers[f"river_ice_{m:02d}"] = input_dir / "river_ice" / f"river_ice_{m:02d}.tif"
    return layers


def _value_spot_check(report: LayerReport, src: rasterio.DatasetReader) -> None:
    """Cheap decimated read to catch obviously-wrong value ranges."""
    try:
        sample = src.read(
            1, out_shape=(min(256, src.height), min(256, src.width))
        ).astype(np.float64)
    except Exception as exc:  # pragma: no cover - driver-level failures
        report.flag("FATAL", f"unreadable: {exc}")
        return
    if src.nodata is not None:
        sample = sample[sample != src.nodata]
    if sample.size == 0:
        report.flag("FATAL", "no valid data in decimated sample")
        return
    lo, hi = float(sample.min()), float(sample.max())
    key = report.key
    if key == "lulc" and (lo < 0 or hi > 8):
        report.flag("FATAL", f"LULC classes outside 0..8 (got {lo:g}..{hi:g})")
    if key == "slope" and (lo < 0 or hi > 90):
        report.flag("FATAL", f"slope outside 0..90 deg (got {lo:g}..{hi:g})")
    if key == "permafrost" or key.startswith(("sea_ice", "river_ice")):
        if hi > 100 or lo < 0:
            report.flag("FATAL", f"expected 0..100 (or 0..1), got {lo:g}..{hi:g}")
        # No flag for max<=1.0: load_permafrost_base / _load_ice auto-detect
        # the source scale (divide by 100 only when max > 1.0), so a
        # 0..1-normalized source loads correctly.


def check_inputs(
    input_dir: str | Path,
    modes: Iterable[str] = MODES,
    months: Iterable[int] = range(1, 13),
    reference_key: str = "lulc",
    spot_check_values: bool = True,
) -> list[LayerReport]:
    """Validate all pipeline inputs against a canonical grid. Returns reports."""
    input_dir = Path(input_dir)
    layers = _expected_layers(input_dir, modes, months)

    # --- establish the canonical grid ---
    ref_path = layers[reference_key]
    if not ref_path.exists():
        report = LayerReport(reference_key, ref_path)
        report.flag("FATAL", "reference raster missing; cannot establish canonical grid")
        return [report]
    with rasterio.open(ref_path) as ref:
        ref_crs, ref_transform = ref.crs, ref.transform
        ref_shape, ref_res = (ref.height, ref.width), ref.res

    reports: list[LayerReport] = []
    for key, path in layers.items():
        rep = LayerReport(key, path)
        reports.append(rep)
        if not path.exists():
            rep.flag("FATAL", "file not found")
            continue
        with rasterio.open(path) as src:
            rep.crs = str(src.crs)
            rep.shape = (src.height, src.width)
            rep.res = src.res
            rep.dtype = src.dtypes[0]
            rep.nodata = src.nodata

            if src.crs != ref_crs:
                rep.flag("FATAL", f"CRS {src.crs} != canonical {ref_crs}")
            if any(abs(a - b) > RES_TOL_M for a, b in zip(src.res, ref_res)):
                rep.flag("FATAL", f"resolution {src.res} != canonical {ref_res}")

            same_shape = rep.shape == ref_shape
            same_origin = (
                abs(src.transform.c - ref_transform.c) <= ORIGIN_TOL_M
                and abs(src.transform.f - ref_transform.f) <= ORIGIN_TOL_M
            )
            if rep.status != "FATAL" and not same_origin:
                dx = (src.transform.c - ref_transform.c) / ref_res[0]
                dy = (src.transform.f - ref_transform.f) / ref_res[1]
                rep.flag(
                    "FATAL",
                    f"origin off canonical by ({dx:.4f}, {dy:.4f}) pixels; "
                    "snap to lulc grid upstream (align_permafrost / arcpy "
                    "river_ice_full_pipeline / GEE crsTransform).",
                )
            if rep.status != "FATAL" and not same_shape:
                rep.flag(
                    "FATAL",
                    f"shape {rep.shape} != canonical {ref_shape}; "
                    "extent differs from lulc — align upstream.",
                )
            if spot_check_values and rep.status != "FATAL":
                _value_spot_check(rep, src)
    return reports


def format_report(reports: list[LayerReport], only_problems: bool = False) -> str:
    rows = []
    for r in reports:
        if only_problems and r.status == "OK":
            continue
        meta = (
            f"{r.crs or '-'} {r.shape or '-'} {r.dtype or '-'}"
            if r.crs else "-"
        )
        issue = "; ".join(r.issues) if r.issues else ""
        rows.append(f"  [{r.status:8s}] {r.key:16s} {meta}  {issue}")
    return "\n".join(rows) if rows else "  (all layers OK)"


def run_preflight(
    input_dir: str | Path,
    modes: Iterable[str] = MODES,
    months: Iterable[int] = range(1, 13),
    **kwargs,
) -> list[LayerReport]:
    """Check inputs and raise PreflightError if any layer is FATAL."""
    reports = check_inputs(input_dir, modes=modes, months=months, **kwargs)
    if any(r.status == "FATAL" for r in reports):
        raise PreflightError(reports)
    logger.info("preflight passed: %d layers checked", len(reports))
    return reports


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    target = sys.argv[1] if len(sys.argv) > 1 else get_raster_dir()
    reps = check_inputs(target)
    print(f"Preflight report for {target}:")
    print(format_report(reps))
    sys.exit(1 if any(r.status == "FATAL" for r in reps) else 0)
