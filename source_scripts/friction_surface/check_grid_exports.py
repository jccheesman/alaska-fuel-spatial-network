#!/usr/bin/env python3
"""
Verify re-exported friction inputs align to the intended full-Alaska grid.

Pass/fail gate for the grid-fix step: after the GEE re-export (EXPORT_REGION widened
to the Albers-metres full-Alaska footprint), every raster dropped into inputs/friction_rasters/
must sit on ONE identical grid that covers the whole transport network.

Target grid (must match the GEE EXPORT_REGION / EXPORT_TRANSFORM):
    CRS   = EPSG:3338
    transform = Affine(150, 0, -2130000, 0, -150, 2595450)
    size  = 28,000 cols x 16,567 rows   (150 m pixels)

Cheap by design: reads raster METADATA only for the grid check, a tiny window for the
per-hub NoData check, and a decimated read for value sanity — never the full 464 M-pixel array.

Usage:
    python3 friction_surface/check_grid_exports.py                 # check inputs/friction_rasters/
    python3 friction_surface/check_grid_exports.py --inputs-dir X  # check another dir
    python3 friction_surface/check_grid_exports.py --plot          # + western-edge PNG
"""
from __future__ import annotations
import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine
from rasterio.windows import Window
import geopandas as gpd

# ---- intended grid ------------------------------------------------------
EXP_CRS = "EPSG:3338"


@dataclass(frozen=True)
class TargetGrid:
    """The grid every re-exported raster must sit on.

    Derived either from lulc.tif (canonical) or from fallback constants.
    Bounds are computed from the transform + size so they can never drift
    from it. Passed explicitly to the checks — no module-level mutation.
    """
    transform: Affine
    width: int
    height: int
    source: str
    crs: str = EXP_CRS

    @property
    def xmin(self) -> float:
        return self.transform.c

    @property
    def ymax(self) -> float:
        return self.transform.f

    @property
    def xmax(self) -> float:
        return self.xmin + self.width * self.transform.a

    @property
    def ymin(self) -> float:
        return self.ymax + self.height * self.transform.e


# Fallback target when lulc.tif is not yet present. NOTE: GEE snaps the export one
# column WEST of the requested -2130000, so it delivers origin -2130150 / width 28001.
# When lulc.tif exists it is the canonical grid and overrides these (see resolve_target).
FALLBACK_GRID = TargetGrid(
    transform=Affine(150.0, 0.0, -2130150.0, 0.0, -150.0, 2595450.0),
    width=28001,
    height=16567,
    source="target = fallback constants (lulc.tif not present yet)",
)


def resolve_target(inputs_dir: Path) -> TargetGrid:
    """If lulc.tif (the canonical reference) is present, adopt ITS grid as the target."""
    lulc = inputs_dir / "lulc.tif"
    if not lulc.exists():
        return FALLBACK_GRID
    with rasterio.open(lulc) as ds:
        return TargetGrid(
            transform=ds.transform,
            width=ds.width,
            height=ds.height,
            source="target = lulc.tif (canonical reference grid)",
        )

# Repo root is two levels above source_scripts/friction_surface/ (source_scripts layout).
REPO = Path(__file__).resolve().parents[2]
# Default to the pipeline's raster home (env-overridable via RASTER_DIR).
from .friction_paths import RASTER_DIR as _RASTER_DIR  # noqa: E402
DEFAULT_INPUTS = Path(_RASTER_DIR)
NODES_SHP = REPO / "final_network" / "network_joined_nodes" / "network_joined_nodes.shp"
KEY_HUBS = {"Hub_21": "Adak", "Hub_275": "Atka"}   # the two western hubs the fix must cover

OK, BAD, WARN = "  OK ", "FAIL ", "WARN "


def transforms_match(a: Affine, b: Affine, tol=1e-6) -> bool:
    return all(abs(x - y) <= tol for x, y in zip(a[:6], b[:6]))


def check_raster(path: Path, target: TargetGrid) -> tuple[bool, str]:
    """Metadata-only grid check for one raster."""
    with rasterio.open(path) as ds:
        crs_ok = ds.crs is not None and ds.crs.to_string() == target.crs
        dim_ok = (ds.width, ds.height) == (target.width, target.height)
        tf_ok = transforms_match(ds.transform, target.transform)
        ok = crs_ok and dim_ok and tf_ok
        bits = []
        if not crs_ok:
            bits.append(f"CRS={ds.crs}")
        if not dim_ok:
            bits.append(f"dims={ds.width}x{ds.height}")
        if not tf_ok:
            bits.append(f"origin=({ds.transform.c:.0f},{ds.transform.f:.0f}) px={ds.transform.a:g}")
        detail = "grid OK" if ok else "MISMATCH: " + ", ".join(bits)
    return ok, detail


def decimated_stats(path: Path, max_dim=1000) -> str:
    """Cheap value sanity via a downsampled read."""
    with rasterio.open(path) as ds:
        scale = max(1, int(max(ds.width, ds.height) / max_dim))
        out_h, out_w = ds.height // scale, ds.width // scale
        arr = ds.read(1, out_shape=(out_h, out_w)).astype("float64")
        nod = ds.nodata
        mask = np.isfinite(arr)
        if nod is not None:
            mask &= (arr != nod)
        valid = arr[mask]
        if valid.size == 0:
            return "all-NoData!"
        return f"valid≈{100*valid.size/arr.size:4.1f}%  min={valid.min():.3g} max={valid.max():.3g}"


def point_valid(path: Path, x: float, y: float) -> bool | None:
    """Is the pixel at (x,y) inside the grid and non-NoData? None if out of bounds."""
    with rasterio.open(path) as ds:
        col, row = ~ds.transform * (x, y)
        row, col = int(row), int(col)
        if not (0 <= col < ds.width and 0 <= row < ds.height):
            return None
        v = ds.read(1, window=Window(col, row, 1, 1))
        if v.size == 0:
            return None
        return ds.nodata is None or v.flat[0] != ds.nodata


def find_reference(tifs: list[Path]) -> Path | None:
    for p in tifs:
        n = p.name.lower()
        if "lulc" in n or "dynamic_world" in n or "land" in n:
            return p
    return tifs[0] if tifs else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs-dir", type=Path, default=DEFAULT_INPUTS)
    ap.add_argument("--plot", action="store_true", help="save a western-edge overview PNG")
    args = ap.parse_args()

    target = resolve_target(args.inputs_dir)
    all_tifs = sorted(args.inputs_dir.rglob("*.tif"))
    # Ignore archived small-grid, backup/provenance side-copies, and raw GEE
    # sea-ice exports: the live inputs are the padded full-grid sea_ice_MM.tif.
    tifs = [p for p in all_tifs
            if not any(part in ("small_grid", "_v1_backup", "provenance", "gee_export")
                       for part in p.parts)]
    # river_ice is on a separate (ArcGIS) track re-aligned in the rebuild step, NOT this
    # GEE re-export — report it informationally, don't let it gate the grid fix.
    gate = [p for p in tifs if "river_ice" not in p.parts]
    river = [p for p in tifs if "river_ice" in p.parts]

    print(f"\nGrid check — {args.inputs_dir}")
    print(f"{target.source}")
    print(f"Target: {target.crs}  {target.width}x{target.height}  origin({target.transform.c:.0f}, {target.transform.f:.0f})  150 m")
    print(f"        X[{target.xmin:,.0f} → {target.xmax:,.0f}]  Y[{target.ymin:,.0f} → {target.ymax:,.0f}]")
    print(f"Found {len(gate)} GEE-layer raster(s) to gate on"
          f" (+{len(river)} river_ice on the deferred track).\n")
    if not gate:
        print("No GEE-layer .tif files found — nothing to gate on yet.")
        return 1

    all_ok = True
    for p in gate:
        ok, detail = check_raster(p, target)
        all_ok &= ok
        stats = decimated_stats(p) if ok else "—"
        print(f"[{OK if ok else BAD}] {p.relative_to(args.inputs_dir)!s:<52} {detail}   {stats}")

    if river:
        print("\nriver_ice (informational — realigned separately in the rebuild step):")
        for p in river:
            ok, detail = check_raster(p, target)
            print(f"[{'  ok ' if ok else 'note '}] {p.relative_to(args.inputs_dir)!s:<52} {detail}")

    # ---- coverage vs network + the two western hubs ----
    print("\nNetwork coverage:")
    grid_ok = True
    if NODES_SHP.exists():
        nodes = gpd.read_file(NODES_SHP)
        bx0, by0, bx1, by1 = nodes.total_bounds
        inside = (bx0 >= target.xmin and bx1 <= target.xmax and by0 >= target.ymin and by1 <= target.ymax)
        grid_ok &= inside
        print(f"[{OK if inside else BAD}] network bounds "
              f"X[{bx0:,.0f} → {bx1:,.0f}] Y[{by0:,.0f} → {by1:,.0f}] "
              f"{'⊆ grid' if inside else 'NOT fully inside grid'}")
        x, y = nodes.geometry.x, nodes.geometry.y
        oob = int(((x < target.xmin) | (x > target.xmax) | (y < target.ymin) | (y > target.ymax)).sum())
        print(f"[{OK if oob == 0 else BAD}] residual out-of-grid nodes: {oob} (expect 0)")
        grid_ok &= (oob == 0)

        ref = find_reference(tifs)
        hubs = nodes[nodes["is_hub"]].set_index("hub_id")
        for hid, name in KEY_HUBS.items():
            if hid not in hubs.index:
                print(f"[{WARN}] {name} ({hid}) not found in nodes")
                continue
            g = hubs.loc[hid].geometry
            inb = target.xmin <= g.x <= target.xmax and target.ymin <= g.y <= target.ymax
            pv = point_valid(ref, g.x, g.y) if (ref and inb) else None
            note = "inside grid" if inb else "OUTSIDE grid"
            if inb and pv is not None:
                note += f", {ref.name} pixel {'valid' if pv else 'NoData'}"
            print(f"[{OK if inb else BAD}] {name:<5} ({hid}) X={g.x:,.0f} Y={g.y:,.0f}  {note}")
            grid_ok &= inb
    else:
        print(f"[{WARN}] {NODES_SHP} not found — skipped coverage check")

    if args.plot:
        _plot_western_edge(tifs, find_reference(tifs), target)

    passed = all_ok and grid_ok
    print("\n" + ("PASS — all rasters on the target grid, network fully covered."
                  if passed else
                  "NOT YET — see FAIL rows above. (Expected before the re-export lands.)"))
    return 0 if passed else 2


def _plot_western_edge(tifs, ref, target: TargetGrid):
    if ref is None:
        return
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    outdir = REPO / "outputs" / "final_network_plots"
    outdir.mkdir(parents=True, exist_ok=True)
    with rasterio.open(ref) as ds:
        scale = max(1, int(max(ds.width, ds.height) / 1200))
        arr = ds.read(1, out_shape=(ds.height // scale, ds.width // scale))
        extent = [ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top]
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.imshow(arr, extent=extent, cmap="terrain", origin="upper")
    for gx in (target.xmin, target.xmax):
        ax.axvline(gx, color="red", lw=1, ls="--")
    ax.set_title(f"{ref.name} — extent vs target grid (red = intended E/W bounds)")
    out = outdir / "grid_export_check.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    sys.exit(main())
