#!/usr/bin/env python3
"""Build the marine / river water-class label on the project grid.

water_class_150m.tif (uint8): 0 = not water, 1 = marine, 2 = river/inland.
Method and constants: friction_config WATER_CLASS_* (owner 2026-11-17). The
domain is nav_water = LULC water | waterway corridor mask — exactly the pixels
the barge surface can mark navigable — so every valid barge pixel gets a class.

QA gates (run inline; any failure exits non-zero):
  - the output grid matches the land-cover raster exactly (shape + transform);
  - every pixel of the reviewed RIVER corridor classes river (hard, 0 allowed);
  - at most 0.1% of the reviewed MARINE corridor classes non-marine (the
    reviewed corridors are the truth; a handful of mixed shore pixels are
    tolerated and reported).

The label is a new product: it does not touch the friction stack, any friction
value, the corridor masks or the ice gating. Exits GATE (3) when the inputs
(land cover or corridor masks) are absent.

Usage:  python workflows/01_friction_build/04_build_water_class.py
"""
from __future__ import annotations

import sys

import numpy as np
import rasterio
from scipy import ndimage

import repo_paths as rp  # noqa: F401  (locates the repo; parity with the stage)
from friction_surface.friction_config import (
    WATER_CLASS_FRINGE_GROW_PX,
    WATER_CLASS_MARINE,
    WATER_CLASS_MIN_CHANNEL_PX,
    WATER_CLASS_NOT_WATER,
    WATER_CLASS_RIVER,
    WATER_CLASS_RIVER_ZONE_M,
    LULC_WATER_CLASS,
)
from friction_surface.friction_paths import (
    RASTER_FILES,
    WATER_CLASS_TIF,
    WATERWAY_MASK_TIF,
    WATERWAY_RIVER_MASK_TIF,
)

GATE_EXIT = 3
S8 = np.ones((3, 3), bool)


def main() -> int:
    from pathlib import Path

    lulc_path = Path(RASTER_FILES["lulc"])
    for p, what in [(lulc_path, "land-cover raster (fetch/regenerate, DATA.md 3.1)"),
                    (Path(WATERWAY_MASK_TIF), "waterway corridor mask (run 01_build_corridor_masks.py)"),
                    (Path(WATERWAY_RIVER_MASK_TIF), "river corridor mask (run 01_build_corridor_masks.py)")]:
        if not p.exists():
            print(f"GATE: {p} missing — {what}")
            return GATE_EXIT

    with rasterio.open(lulc_path) as src:
        profile = src.profile.copy()
        ref = (src.height, src.width, src.transform, src.crs)
        water = src.read(1) == LULC_WATER_CLASS

    def load_mask(path):
        with rasterio.open(path) as src:
            if (src.height, src.width) != ref[:2] or src.transform != ref[2]:
                raise SystemExit(f"FAIL: {path} grid does not match the land-cover raster")
            return src.read(1) != 0

    ww = load_mask(WATERWAY_MASK_TIF)
    river_cor = load_mask(WATERWAY_RIVER_MASK_TIF)
    marine_cor = ww & ~river_cor
    nav = water | ww
    del water, ww
    H, W = nav.shape
    px_m = abs(ref[2].a)
    print(f"nav_water {int(nav.sum()):,} px; river corridor {int(river_cor.sum()):,}; "
          f"marine corridor {int(marine_cor.sum()):,} (grid {W}x{H} @ {px_m:g} m)")

    # river zone: everything within WATER_CLASS_RIVER_ZONE_M of the reviewed
    # river corridor, built by dilation at 2x coarse for memory
    H2, W2 = H // 2, W // 2

    def pool2(a):
        return a[:H2 * 2, :W2 * 2].reshape(H2, 2, W2, 2).any(axis=(1, 3))

    steps = int(round(WATER_CLASS_RIVER_ZONE_M / (2 * px_m)))
    rz2 = ndimage.binary_dilation(pool2(river_cor), structure=S8, iterations=steps)
    river_zone = np.zeros((H, W), dtype=bool)
    river_zone[:H2 * 2, :W2 * 2] = np.repeat(np.repeat(rz2, 2, axis=0), 2, axis=1)
    if W % 2:
        river_zone[:, -1] = river_zone[:, -2]
    if H % 2:
        river_zone[-1, :] = river_zone[-2, :]
    del rz2
    river_zone[marine_cor] = False     # the reviewed marine corridor is never river
    river_zone[river_cor] = True

    # ocean flood fill: wide, non-river water from the grid border, with the
    # reviewed marine corridor as a width-exempt conduit
    wide = ndimage.binary_erosion(nav, structure=S8,
                                  iterations=WATER_CLASS_MIN_CHANNEL_PX, border_value=1)
    permitted = (nav & ~river_zone & wide) | marine_cor
    del wide
    seeds = np.zeros((H, W), dtype=bool)
    for sl in [np.s_[0, :], np.s_[-1, :], np.s_[:, 0], np.s_[:, -1]]:
        seeds[sl] = permitted[sl]
    if not seeds.any():
        raise SystemExit("FAIL: no ocean seed pixels on the grid border")
    core = ndimage.binary_propagation(seeds, structure=S8, mask=permitted)
    del permitted, seeds
    marine = ndimage.binary_dilation(core, structure=S8,
                                     iterations=WATER_CLASS_FRINGE_GROW_PX,
                                     mask=(nav & ~river_zone))
    del core, river_zone
    marine &= nav

    out = np.full((H, W), WATER_CLASS_NOT_WATER, dtype=np.uint8)
    out[marine] = WATER_CLASS_MARINE
    out[nav & ~marine] = WATER_CLASS_RIVER
    print(f"marine {int(marine.sum()):,} px; river/inland {int((nav & ~marine).sum()):,} px")

    # QA: reviewed-corridor agreement
    riv_bad = int((river_cor & marine).sum())
    mar_bad = int((marine_cor & ~marine).sum())
    mar_tol = 0.001 * marine_cor.sum()
    print(f"QA: river-corridor px classed marine: {riv_bad} (allowed 0); "
          f"marine-corridor px classed non-marine: {mar_bad} (allowed {int(mar_tol)})")
    if riv_bad > 0 or mar_bad > mar_tol:
        raise SystemExit("FAIL: water-class label disagrees with the reviewed corridors")

    profile.update(dtype="uint8", nodata=None, compress="deflate", predictor=2, tiled=True)
    with rasterio.open(WATER_CLASS_TIF, "w", **profile) as dst:
        dst.write(out, 1)
    with rasterio.open(WATER_CLASS_TIF) as src:
        assert (src.height, src.width) == ref[:2] and src.transform == ref[2], \
            "output grid drifted from the land-cover raster"
    print(f"wrote {WATER_CLASS_TIF}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
