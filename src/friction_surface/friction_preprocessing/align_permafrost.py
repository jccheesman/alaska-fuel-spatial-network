# -*- coding: utf-8 -*-
"""align_permafrost.py

One-shot prep: snap a continuous-coverage permafrost raster to the friction
canonical grid defined by lulc.tif.

The Pastick et al. 2015 near-surface permafrost probability raster is the
data source; IPA-convention thresholds (Brown et al. 1997) are applied
downstream. Wherever the upstream rasterized permafrost.tif comes from
(GEE Pastick export, or an already-continuous vendor product), this
script reprojects + snaps it onto the lulc.tif grid. This alignment step
is load-bearing: the friction-pipeline loaders require inputs already on
the canonical grid (no WarpedVRT fallback) and raise on grid mismatch.

Resampling: BILINEAR — the input is continuous fractional permafrost
coverage in [0, 1] (or [0, 100], auto-detected by load_permafrost_base).
Do NOT switch to nearest: the upstream zone-code → coverage conversion has
already been done; treating it as categorical here would just create stair-
step artifacts at zone boundaries.

Run from the project root with the friction-surface Python env active:
    python -m friction_surface.friction_preprocessing.align_permafrost

Or pass explicit paths:
    python -m friction_surface.friction_preprocessing.align_permafrost \\
        --src /path/to/raw_permafrost.tif --out friction_inputs/permafrost.tif
"""

from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

from ..friction_paths import RASTER_DIR, RASTER_FILES

logger = logging.getLogger(__name__)

# Default I/O. SRC_DEFAULT points at the same path the friction pipeline
# already reads — running with defaults aligns the file in place. Pass --src
# if your unaligned source lives elsewhere (e.g., a vendor delivery folder
# outside friction_inputs).
SRC_DEFAULT = Path(RASTER_FILES["permafrost"])
OUT_DEFAULT = Path(RASTER_FILES["permafrost"])
TEMPLATE_DEFAULT = Path(RASTER_DIR) / "lulc.tif"

# Float-NoData sentinel matching the rest of the friction stack
# (friction_config.FRICTION_NODATA).
OUT_NODATA = -9999.0


def align_permafrost(
    src_path: Path,
    out_path: Path,
    template_path: Path,
) -> None:
    """Reproject + snap src_path to template_path's grid, write to out_path."""
    if not template_path.exists():
        raise FileNotFoundError(
            f"Canonical grid template not found: {template_path}"
        )
    if not src_path.exists():
        raise FileNotFoundError(f"Source permafrost raster not found: {src_path}")

    with rasterio.open(template_path) as ref:
        dst_crs = ref.crs
        dst_transform = ref.transform
        dst_height = ref.height
        dst_width = ref.width

    # Aligning in place needs a temp file — can't open the same TIFF for
    # read and write simultaneously.
    same_path = out_path.resolve() == src_path.resolve()
    write_path = out_path.with_suffix(".aligned.tif") if same_path else out_path
    write_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(src_path) as src:
        logger.info(
            "source: %s  crs=%s  shape=(%d, %d)  res=%s",
            src_path, src.crs, src.height, src.width, src.res,
        )
        logger.info(
            "target: %s  crs=%s  shape=(%d, %d)",
            template_path, dst_crs, dst_height, dst_width,
        )

        src_data = src.read(1).astype(np.float32)
        dst_data = np.full(
            (dst_height, dst_width), OUT_NODATA, dtype=np.float32
        )

        reproject(
            source=src_data,
            destination=dst_data,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            dst_nodata=OUT_NODATA,
            resampling=Resampling.bilinear,
        )

        profile = src.profile

    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        height=dst_height,
        width=dst_width,
        crs=dst_crs,
        transform=dst_transform,
        nodata=OUT_NODATA,
        compress="deflate",
        tiled=True,
    )

    with rasterio.open(write_path, "w", **profile) as dst:
        dst.write(dst_data, 1)

    if same_path:
        write_path.replace(out_path)

    valid = dst_data[dst_data != OUT_NODATA]
    if valid.size:
        logger.info(
            "wrote %s  valid_px=%d  min=%.4f  max=%.4f",
            out_path, valid.size, float(valid.min()), float(valid.max()),
        )
    else:
        logger.warning("wrote %s but no valid pixels in target extent", out_path)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--src", type=Path, default=SRC_DEFAULT,
                   help=f"source permafrost raster (default: {SRC_DEFAULT})")
    p.add_argument("--out", type=Path, default=OUT_DEFAULT,
                   help=f"aligned output path (default: {OUT_DEFAULT})")
    p.add_argument("--template", type=Path, default=TEMPLATE_DEFAULT,
                   help=f"canonical grid template (default: {TEMPLATE_DEFAULT})")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    align_permafrost(args.src, args.out, args.template)
    return 0


if __name__ == "__main__":
    sys.exit(main())
