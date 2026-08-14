#!/usr/bin/env python3
"""Thin driver: gate the friction build on its input rasters.

Runs the cheap metadata-only grid check (check_grid_exports) followed by the
full preflight (friction_preflight) against RASTER_DIR
(default inputs/friction_rasters — see source_scripts/friction_surface/friction_paths.py).

Run:  python workflows/01_friction_build/00_preflight_inputs.py [input_dir]
"""
import logging
import sys

from friction_surface.check_grid_exports import main as check_grids
from friction_surface.friction_preflight import check_inputs, format_report
from friction_surface.friction_paths import get_raster_dir


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    rc = check_grids()
    if rc == 2:
        # Actual grid misalignment among GEE-named exports — hard stop.
        return rc
    if rc == 1:
        # No GEE-named rasters found: normal once exports are renamed to the
        # pipeline names (slope.tif etc.) — the full preflight below is the
        # gate that matters. Informational only.
        print("(no raw GEE-named exports to gate — continuing to the full preflight)\n")
    target = sys.argv[1] if len(sys.argv) > 1 else get_raster_dir()
    reports = check_inputs(target)
    print(f"Preflight report for {target}:")
    print(format_report(reports))
    return 1 if any(r.status == "FATAL" for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
