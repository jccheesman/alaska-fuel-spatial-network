"""Extract per-month barge navigability at the waterway-mask cells only.

The full barge_MM.tif rasters are 464M cells; the friction comparison only
needs the 501,684 waterway cells. This writes a compact .npz (<1 MB) holding,
for each month, a boolean navigability vector over those cells, plus the
cells' row/col so any analysis can put them back on the map.

Run:
    python diagnostics/01_friction_build/extract_barge_waterway.py [stack_dir] [out_npz]

Defaults: the friction stack -> outputs/analysis/barge_waterway_new.npz
"""
import sys
import numpy as np
import rasterio

import repo_paths as rp
from friction_surface import friction_paths as fp

stack = sys.argv[1] if len(sys.argv) > 1 else fp.FRICTION_OUTPUT_DIR
out = sys.argv[2] if len(sys.argv) > 2 else str(rp.ANALYSIS / "barge_waterway_new.npz")

with rasterio.open(fp.WATERWAY_MASK_TIF) as s:
    ww = s.read(1) == 1
rows, cols = np.nonzero(ww)
print(f"waterway cells: {rows.size:,}")

nav = np.zeros((12, rows.size), dtype=bool)
for m in range(1, 13):
    with rasterio.open(f"{stack}/barge_{m:02d}.tif") as s:
        a = s.read(1)
    nav[m - 1] = a[rows, cols] != -9999.0
    print(f"  month {m:02d}: {int(nav[m-1].sum()):,} navigable")

np.savez_compressed(out, rows=rows.astype(np.int32), cols=cols.astype(np.int32),
                    nav=np.packbits(nav, axis=1), n_cells=rows.size)
print(f"wrote {out}")
