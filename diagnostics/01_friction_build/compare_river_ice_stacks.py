"""Compare the rebuilt river-ice stack (no EucAllocation, marine clip) against
the pre-rebuild stack, preserved as river_ice.bak_pre_rebuild.

The fixed rebuild is now what feeds the friction build (it lives at
inputs/friction_rasters/river_ice), so --old-dir defaults to the
river_ice.bak_pre_rebuild backup rather than the live input dir.

Phase 0 of the new-vs-old verification plan (2026-08-25): raw rasters only,
nothing downstream is touched. Checks, per month:

  1. truncation gone   distinct values / exactly-0 share in the NEW raster
  2. coverage delta    valid cells new vs old; lost cells should be the old
                       NN-fallback footprint plus the 4 clipped polygons
  3. corridor flips    NWN river-corridor cells crossing RIVER_ICE_THRESHOLD,
                       split by direction (expected: navigable -> frozen only)

Outputs: a printed table, outputs/analysis/river_ice_new_vs_old.csv, and a
January change map outputs/analysis/river_ice_new_vs_old_jan.png.

Run:
    .venv/bin/python diagnostics/01_friction_build/compare_river_ice_stacks.py
"""

import argparse
import csv
import os

import numpy as np
import rasterio
from rasterio.windows import Window

import repo_paths as rp
from friction_surface import friction_paths as fp

THRESHOLD = 0.15
NODATA = -9999.0
MARGIN_M = 100_000.0  # window padding around the reference stack's data extent
WINDOW_DECIM = 10     # decimation factor for the cheap valid-bbox read


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--old-dir",
                   default=fp.RASTER_FILES["river_ice"] + ".bak_pre_rebuild")
    p.add_argument("--new-dir", default=fp.RASTER_FILES["river_ice"])
    p.add_argument("--river-mask", default=fp.WATERWAY_RIVER_MASK_TIF)
    p.add_argument("--out-dir", default=str(rp.ANALYSIS))
    return p.parse_args()


def data_window(ref_path, canon):
    """Window on the canonical grid covering ref_path's valid-data extent + margin.

    ref_path must already be on the canonical grid (every river_ice raster is),
    so its pixel indices map straight onto canon's. The valid bounding box is
    read decimated (WINDOW_DECIM) to keep this cheap; the MARGIN_M pad absorbs
    the decimation slop. Replaces the retired provenance_01.tif bounds lookup —
    pass the larger-extent (old) stack so lost cells stay inside the window."""
    with rasterio.open(ref_path) as s:
        if (s.width, s.height) != (canon.width, canon.height):
            raise SystemExit(f"{ref_path} is not on the canonical grid")
        oh = max(1, s.height // WINDOW_DECIM)
        ow = max(1, s.width // WINDOW_DECIM)
        small = s.read(1, out_shape=(oh, ow))
    valid = small != NODATA
    if not valid.any():
        raise SystemExit(f"{ref_path}: no valid (non-NoData) cells to window on")
    rr = np.where(np.any(valid, axis=1))[0]
    cc = np.where(np.any(valid, axis=0))[0]
    r0, r1 = rr[0] * WINDOW_DECIM, (rr[-1] + 1) * WINDOW_DECIM
    c0, c1 = cc[0] * WINDOW_DECIM, (cc[-1] + 1) * WINDOW_DECIM
    pad = int(MARGIN_M / abs(canon.transform.a))  # metres -> canonical pixels
    col = max(0, c0 - pad); row = max(0, r0 - pad)
    width = min(canon.width - col, (c1 - c0) + 2 * pad)
    height = min(canon.height - row, (r1 - r0) + 2 * pad)
    return Window(col, row, width, height)


def main():
    a = parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    canon = rasterio.open(os.path.join(a.old_dir, "river_ice_01.tif"))
    # window on the old (larger-extent) stack so cells lost by the fix stay in view
    win = data_window(os.path.join(a.old_dir, "river_ice_01.tif"), canon)
    print(f"analysis window: {win.width} x {win.height} at "
          f"({int(win.col_off)}, {int(win.row_off)}) on the canonical grid\n")

    with rasterio.open(a.river_mask) as s:
        if (s.width, s.height) != (canon.width, canon.height):
            raise SystemExit("river mask is not on the canonical grid")
        corridor = s.read(1, window=win) == 1
    print(f"NWN river-corridor cells in window: {corridor.sum():,}\n")

    hdr = (f"{'mo':>2} {'new valid':>11} {'old valid':>11} {'lost':>9} "
           f"{'gained':>7} {'distinct':>9} {'=0.0%':>6} "
           f"{'nav->frz':>8} {'frz->nav':>8}")
    print(hdr); print("-" * len(hdr))

    rows = []
    jan = {}
    for m in range(1, 13):
        with rasterio.open(os.path.join(a.new_dir, f"river_ice_{m:02d}.tif")) as s:
            if (s.width, s.height) != (canon.width, canon.height):
                raise SystemExit(
                    f"river_ice_{m:02d}.tif (new) is {s.width}x{s.height}, "
                    f"not the canonical {canon.width}x{canon.height} — "
                    "the ArcGIS alignment step did not run on it")
            new = s.read(1, window=win)
        with rasterio.open(os.path.join(a.old_dir, f"river_ice_{m:02d}.tif")) as s:
            old = s.read(1, window=win)

        nv, ov = new != NODATA, old != NODATA
        vals = new[nv]
        distinct = np.unique(np.round(vals, 4)).size
        frac0 = float((vals == 0).mean()) if vals.size else 0.0
        lost = int((ov & ~nv).sum())
        gained = int((nv & ~ov).sum())

        both = nv & ov & corridor
        o, n = old[both], new[both]
        n2f = int(((o < THRESHOLD) & (n >= THRESHOLD)).sum())
        f2n = int(((o >= THRESHOLD) & (n < THRESHOLD)).sum())
        # corridor cells that lost coverage entirely fall to the friction
        # build's tier 2/3 cascade; count them separately
        corr_lost = int((ov & ~nv & corridor).sum())

        print(f"{m:>2} {int(nv.sum()):>11,} {int(ov.sum()):>11,} {lost:>9,} "
              f"{gained:>7,} {distinct:>9,} {frac0*100:>5.1f}% "
              f"{n2f:>8,} {f2n:>8,}")
        rows.append(dict(month=m, new_valid=int(nv.sum()), old_valid=int(ov.sum()),
                         lost=lost, gained=gained, corridor_lost=corr_lost,
                         distinct=distinct, frac_exactly_zero=round(frac0, 4),
                         corridor_nav_to_frozen=n2f, corridor_frozen_to_nav=f2n))
        if m == 1:
            jan = dict(old=old.copy(), new=new.copy())
        del new, old, nv, ov

    csv_path = os.path.join(a.out_dir, "river_ice_new_vs_old.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"\nwrote {csv_path}")

    print("""
READ THE TABLE AGAINST THE PREDICTIONS (docs/TEST_LOG.md 2026-08-21):
  distinct    thousands per data month  (old NN-fallback: 85, 84% at 0.0)
  lost        ~73k per winter month = old NN-fallback + 4 clipped polygons;
              Jul/Aug lose only the clipped-polygon cells
  nav->frz    corridor cells the truncation was hiding (~4,900 in January)
  frz->nav    should be ~0; investigate anything large
""")

    # ---- January change map ------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    o, n = jan["old"], jan["new"]
    ov, nv = o != NODATA, n != NODATA
    both = ov & nv & corridor
    n2f = both & (o < THRESHOLD) & (n >= THRESHOLD)
    f2n = both & (o >= THRESHOLD) & (n < THRESHOLD)
    dropped = ov & ~nv & corridor
    same = corridor & ~n2f & ~f2n & ~dropped

    fig, ax = plt.subplots(figsize=(13, 9), dpi=150)
    fig.patch.set_facecolor("#fcfcfb"); ax.set_facecolor("#fcfcfb")

    def scatter(mask, color, size, label, z):
        r, c = np.nonzero(mask)
        if r.size:
            ax.scatter(c, r, s=size, c=color, marker="s", lw=0, label=None, zorder=z)
        return Line2D([], [], marker="s", ls="", color=color,
                      label=f"{label}  ({r.size:,})")

    handles = [
        scatter(same, "#b9c2cc", 0.4, "corridor, unchanged", 1),
        scatter(dropped, "#e0a83a", 1.6, "lost upstream coverage → refilled by 25 km cascade", 3),
        scatter(n2f, "#d03b3b", 1.6, "navigable → frozen (truncation corrected)", 4),
        scatter(f2n, "#7c3aed", 3.0, "frozen → navigable (UNEXPECTED)", 5),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=9, frameon=False)
    ax.set_title("River-ice rebuild, January: what changed on the NWN river corridor",
                 fontsize=13)
    ax.invert_yaxis(); ax.set_aspect("equal"); ax.axis("off")
    png = os.path.join(a.out_dir, "river_ice_new_vs_old_jan.png")
    fig.savefig(png, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {png}")


if __name__ == "__main__":
    main()
