"""Compare the new full-AK LULC export against the old-grid reference.

The new LULC was exported with the FAST path (nearest-sample of the 10 m Dynamic World
mode to 150 m) instead of an exact 15x15 spatial majority (reduceResolution mode). This
script quantifies how much that resampling choice changed the classes, using the old
`small_grid/lulc.tif` (the previous exact-ish reference) as ground truth over their
overlapping extent.

Both rasters are uint8 Dynamic World labels (0-8) on the identical 150 m EPSG:3338
lattice; the old grid is a strict column subset of the new one, so the overlay is exact
(integer pixel offset, no resampling). Reports overall agreement, agreement excluding
water/nodata (class 0), per-class recall, and the largest class confusions. Optionally
writes a decimated disagreement map.

Usage:
    python friction_surface/qa/compare_lulc_grids.py [--plot]
    python friction_surface/qa/compare_lulc_grids.py --new <path> --old <path>
"""
from __future__ import annotations
import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window

HERE = Path(__file__).resolve().parent
INPUTS = HERE.parent / "friction_inputs"
NEW_DEFAULT = INPUTS / "dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif"
OLD_DEFAULT = INPUTS / "small_grid" / "lulc.tif"

DW_NAMES = ["Water", "Trees", "Grass", "Flooded veg", "Crops",
            "Shrub/scrub", "Built", "Bare", "Snow/ice"]
NC = 9
ROW_BLOCK = 2048


def overlap_offset(new: rasterio.DatasetReader, old: rasterio.DatasetReader) -> tuple[int, int]:
    """Integer (col, row) offset of the OLD raster inside the NEW raster. Asserts alignment."""
    tn, to = new.transform, old.transform
    assert (tn.a, tn.e) == (to.a, to.e), "pixel sizes differ — not the same lattice"
    off_col = (to.c - tn.c) / tn.a
    off_row = (to.f - tn.f) / tn.e
    assert float(off_col).is_integer() and float(off_row).is_integer(), \
        f"non-integer offset (col={off_col}, row={off_row}) — grids not aligned"
    off_col, off_row = int(round(off_col)), int(round(off_row))
    assert off_col >= 0 and off_row >= 0, "old raster starts outside new raster"
    assert off_col + old.width <= new.width and off_row + old.height <= new.height, \
        "old raster extends beyond new raster"
    return off_col, off_row


def build_confusion(new_path: Path, old_path: Path) -> np.ndarray:
    """9x9 confusion matrix conf[old_class, new_class] over the overlap, block-streamed."""
    conf = np.zeros((NC, NC), dtype=np.int64)
    with rasterio.open(new_path) as new, rasterio.open(old_path) as old:
        off_col, off_row = overlap_offset(new, old)
        for r0 in range(0, old.height, ROW_BLOCK):
            h = min(ROW_BLOCK, old.height - r0)
            old_blk = old.read(1, window=Window(0, r0, old.width, h))
            new_blk = new.read(1, window=Window(off_col, off_row + r0, old.width, h))
            valid = (old_blk < NC) & (new_blk < NC)          # guard any stray >8 fill
            o = old_blk[valid].astype(np.int64)
            n = new_blk[valid].astype(np.int64)
            idx = o * NC + n
            conf += np.bincount(idx, minlength=NC * NC).reshape(NC, NC)
    return conf


def report(conf: np.ndarray) -> None:
    total = conf.sum()
    diag = np.diag(conf).sum()
    print(f"\nCompared {total:,} overlapping cells\n")

    print(f"Overall agreement (incl. water/0):   {100 * diag / total:6.3f}%")
    # exclude cells that are 0 in BOTH (ocean/water/nodata dominates and inflates)
    both_zero = conf[0, 0]
    denom_nz = total - both_zero
    diag_nz = diag - both_zero
    print(f"Agreement excl. cells 0-in-both:     {100 * diag_nz / denom_nz:6.3f}%  "
          f"({denom_nz:,} cells)")
    # land only: reference (old) is a real land class 1..8
    land = conf[1:, :]
    land_total = land.sum()
    land_match = np.diag(conf)[1:].sum()
    if land_total:
        print(f"Agreement on reference land (old 1-8): {100 * land_match / land_total:6.3f}%  "
              f"({land_total:,} cells)")

    print("\nPer-class (reference = old grid):")
    print(f"  {'class':<13} {'ref cells':>12} {'matched':>12} {'recall':>8}")
    for c in range(NC):
        ref = conf[c, :].sum()
        m = conf[c, c]
        rec = (100 * m / ref) if ref else float("nan")
        print(f"  {DW_NAMES[c]:<13} {ref:>12,} {m:>12,} {rec:>7.2f}%")

    # largest off-diagonal confusions
    off = conf.copy()
    np.fill_diagonal(off, 0)
    flat = np.argsort(off.ravel())[::-1][:8]
    print("\nLargest class disagreements (old -> new):")
    for f in flat:
        oc, nn = divmod(int(f), NC)
        cnt = off[oc, nn]
        if cnt == 0:
            break
        print(f"  {DW_NAMES[oc]:<13} -> {DW_NAMES[nn]:<13} {cnt:>12,}  "
              f"({100 * cnt / total:.3f}% of overlap)")


def save_plot(new_path: Path, old_path: Path, out_png: Path, width_px: int = 1400) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap

    with rasterio.open(old_path) as old, rasterio.open(new_path) as new:
        off_col, off_row = overlap_offset(new, old)
        scale = max(1, round(old.width / width_px))
        oh, ow = old.height // scale, old.width // scale
        old_d = old.read(1, out_shape=(oh, ow))
        new_d = new.read(1, out_shape=(oh, ow),
                         window=Window(off_col, off_row, old.width, old.height))
        b = old.bounds
    ext = [b.left / 1000, b.right / 1000, b.bottom / 1000, b.top / 1000]
    mism = ((old_d != new_d) & (old_d < NC) & (new_d < NC)).astype(float)
    # grey where both 0 (ocean/water agree), else white=agree, red=disagree
    fig, ax = plt.subplots(figsize=(12, 8), constrained_layout=True)
    ax.imshow(np.where((old_d == 0) & (new_d == 0), 0.9, np.nan), extent=ext,
              origin="upper", cmap=ListedColormap(["0.85"]), vmin=0, vmax=1)
    ax.imshow(np.where(mism > 0, 1.0, np.nan), extent=ext, origin="upper",
              cmap=ListedColormap(["crimson"]), vmin=0, vmax=1)
    ax.set_title("LULC fast-nearest vs exact reference — disagreeing 150 m cells (red)\n"
                 "grey = water/nodata agree", fontsize=11)
    ax.set_xlabel("Albers easting (km)"); ax.set_ylabel("Albers northing (km)")
    fig.savefig(out_png, dpi=130)
    print(f"\nwrote {out_png}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", type=Path, default=NEW_DEFAULT)
    ap.add_argument("--old", type=Path, default=OLD_DEFAULT)
    ap.add_argument("--plot", action="store_true", help="also write a decimated disagreement map")
    args = ap.parse_args()

    for f in (args.new, args.old):
        if not f.exists():
            raise FileNotFoundError(f)
    print(f"NEW: {args.new}\nOLD: {args.old}")

    conf = build_confusion(args.new, args.old)
    report(conf)
    if args.plot:
        save_plot(args.new, args.old, HERE / "lulc_fast_vs_exact_disagreement.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
