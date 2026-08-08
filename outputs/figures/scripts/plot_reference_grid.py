"""Paper figure of the canonical AK_Stack_150m reference grid.

Reads all grid parameters directly from the canonical reference raster
(inputs/friction_rasters/lulc.tif) so the figure can never drift
from the actual grid definition. Draws:
  - the full grid extent with a schematic cell lattice (every N cells),
  - a light Alaska boundary (TIGER cb_2023_us_state_500k, reprojected),
  - a lat/lon graticule with edge labels,
  - an inset showing the true 150 m cell lattice,
  - a parameter box (CRS, origin, dimensions, resolution, extent).

Outputs: outputs/figures/ak_stack_150m_reference_grid.{png,pdf}
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.patches import Rectangle
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[3]  # repo root (outputs/figures/scripts/ is 3 deep)
REF_RASTER = ROOT / "inputs" / "friction_rasters" / "lulc.tif"
STATES_SHP = ROOT / "inputs" / "region_and_census_data" / "tiger" / "cb_2023_us_state_500k.shp"
OUT_STEM = str(ROOT / "outputs" / "figures" / "ak_stack_150m_reference_grid")

LATTICE_EVERY = 2000          # schematic gridline spacing, in cells (2000 * 150 m = 300 km)
PARALLELS = range(50, 76, 5)  # degrees N
MERIDIANS = range(-210, -119, 10)  # degrees E (west of -180 = eastern Aleutians)

# ---------------------------------------------------------------- grid params
with rasterio.open(REF_RASTER) as src:
    crs = src.crs
    ncols, nrows = src.width, src.height
    dx, dy = src.res
    left, bottom, right, top = src.bounds

to_lonlat = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
from_lonlat = Transformer.from_crs("EPSG:4326", crs, always_xy=True)

# ---------------------------------------------------------------- figure
fig, ax = plt.subplots(figsize=(9, 6.2))
km = 1e-3

# Alaska boundary, light fill
states = gpd.read_file(STATES_SHP)
ak = states[states["STUSPS"] == "AK"].to_crs(crs)
ak.geometry = ak.geometry.scale(km, km, origin=(0, 0))
ak.plot(ax=ax, facecolor="#e9e9e9", edgecolor="#9a9a9a", linewidth=0.5, zorder=2)

# schematic cell lattice, aligned to true pixel edges
step = LATTICE_EVERY * dx
xs = np.arange(left, right + 1, step)
ys = np.arange(top, bottom - 1, -LATTICE_EVERY * dy)
for x in xs:
    ax.plot([x * km, x * km], [bottom * km, top * km],
            color="#b5b5b5", lw=0.5, zorder=1)
for y in ys:
    ax.plot([left * km, right * km], [y * km, y * km],
            color="#b5b5b5", lw=0.5, zorder=1)

# grid extent
ax.add_patch(Rectangle((left * km, bottom * km),
                       (right - left) * km, (top - bottom) * km,
                       fill=False, edgecolor="black", lw=1.3, zorder=5))

# grid origin (upper-left corner of pixel (0, 0))
ax.plot(left * km, top * km, marker="s", ms=6, mfc="none", mec="crimson",
        mew=1.4, zorder=6)
ax.annotate(f"grid origin\n({left:,.0f}, {top:,.0f}) m",
            xy=(left * km, top * km), xytext=(8, 10),
            textcoords="offset points", fontsize=7.5, color="crimson")

# ---------------------------------------------------------------- graticule
pad = 120e3  # sample slightly beyond the extent so edge labels interpolate cleanly
lat_line_lons = np.linspace(-215, -115, 400)
lon_line_lats = np.linspace(45, 75, 300)

def label_at_edge(px, py, axis, edge, text, flip=False):
    """Interpolate where a projected graticule line crosses a box edge; label it.

    Returns True if the crossing fell inside the box (label placed)."""
    px, py = np.asarray(px), np.asarray(py)
    if axis == "x":  # crossing a vertical edge at x=edge -> find y
        ok = np.argsort(px)
        y = np.interp(edge, px[ok], py[ok], left=np.nan, right=np.nan)
        if bottom < y < top:
            off, ha = (4, "left") if flip else (-4, "right")
            ax.annotate(text, xy=(edge * km, y * km), xytext=(off, 0),
                        textcoords="offset points", ha=ha, va="center",
                        fontsize=7.5, color="#4477aa")
            return True
    else:            # crossing a horizontal edge at y=edge -> find x
        ok = np.argsort(py)
        x = np.interp(edge, py[ok], px[ok], left=np.nan, right=np.nan)
        if left < x < right:
            off, va = (4, "bottom") if flip else (-4, "top")
            ax.annotate(text, xy=(x * km, edge * km), xytext=(0, off),
                        textcoords="offset points", ha="center", va=va,
                        fontsize=7.5, color="#4477aa")
            return True
    return False

for lat in PARALLELS:
    px, py = from_lonlat.transform(lat_line_lons, np.full_like(lat_line_lons, lat))
    inside = (px > left - pad) & (px < right + pad) & (py > bottom - pad) & (py < top + pad)
    if inside.any():
        ax.plot(px[inside] * km, py[inside] * km, color="#4477aa", lw=0.5,
                ls=(0, (4, 3)), alpha=0.65, zorder=3)
        lab = f"{lat}\N{DEGREE SIGN}N"
        label_at_edge(px, py, "x", left, lab) or \
            label_at_edge(px, py, "y", top, lab, flip=True)

for lon in MERIDIANS:
    disp = lon if lon >= -180 else lon + 360  # display label in [-180, 180]
    lab = f"{abs(disp)}\N{DEGREE SIGN}{'W' if disp < 0 else 'E'}"
    px, py = from_lonlat.transform(np.full_like(lon_line_lats, disp), lon_line_lats)
    inside = (px > left - pad) & (px < right + pad) & (py > bottom - pad) & (py < top + pad)
    if inside.any():
        ax.plot(px[inside] * km, py[inside] * km, color="#4477aa", lw=0.5,
                ls=(0, (4, 3)), alpha=0.65, zorder=3)
        label_at_edge(px, py, "y", bottom, lab) or \
            label_at_edge(px, py, "x", left, lab)

# note: the west edge wraps past the antimeridian, so meridians exiting it
# carry East-longitude labels (Bering Sea / far-western Aleutians)
ax.text(left * km + 35, (bottom + top) / 2 * km,
        "west edge crosses 180\N{DEGREE SIGN} \N{RIGHTWARDS ARROW} \N{DEGREE SIGN}E labels\n"
        "(Bering Sea / far-western Aleutians)",
        rotation=90, ha="left", va="center", fontsize=6.5, style="italic",
        color="#4477aa", zorder=4)

# ---------------------------------------------------------------- inset: true 150 m cells
# window near Fairbanks, snapped to pixel edges
fx, fy = from_lonlat.transform(-147.72, 64.84)
ix = left + np.floor((fx - left) / dx) * dx
iy = top - np.floor((top - fy) / dy) * dy
n = 10  # 10 x 10 cells = 1.5 km
axins = ax.inset_axes([0.75, 0.615, 0.185, 0.185])
for i in range(n + 1):
    axins.plot([ix, ix + n * dx], [iy - i * dy] * 2, color="#888", lw=0.5)
    axins.plot([ix + i * dx] * 2, [iy - n * dy, iy], color="#888", lw=0.5)
axins.set_xlim(ix - dx, ix + (n + 1) * dx)
axins.set_ylim(iy - (n + 1) * dy, iy + dy)
axins.set_aspect("equal")
axins.set_xticks([]); axins.set_yticks([])
axins.set_title(f"cell lattice\n{n} \N{MULTIPLICATION SIGN} {n} cells ({dx:.0f} m)",
                fontsize=7, pad=3)
ax.plot(ix * km, iy * km, marker="o", ms=3, color="#555", zorder=6)
ax.annotate("", xy=(0.75, 0.70), xycoords="axes fraction",
            xytext=((ix * km - left * km) / ((right - left) * km),
                    (iy * km - bottom * km) / ((top - bottom) * km)),
            textcoords="axes fraction",
            arrowprops=dict(arrowstyle="-", color="#555", lw=0.6))

# ---------------------------------------------------------------- parameter box
info = "\n".join([
    "AK_Stack_150m reference grid",
    f"CRS: {crs.to_string()}",
    "  (NAD83 / Alaska Albers)",
    f"Cell size: {dx:.0f} m \N{MULTIPLICATION SIGN} {dy:.0f} m",
    "Dimensions:",
    f"  {ncols:,} \N{MULTIPLICATION SIGN} {nrows:,} cells",
    f"  ({ncols * nrows / 1e6:,.0f} M cells)",
    "Extent (m):",
    f"  x [{left:,.0f}, {right:,.0f}]",
    f"  y [{bottom:,.0f}, {top:,.0f}]",
    f"Span: {(right - left) * km:,.0f} \N{MULTIPLICATION SIGN} "
    f"{(top - bottom) * km:,.0f} km",
    f"Gridlines every {LATTICE_EVERY:,} cells",
    f"  ({step * km:.0f} km)",
])
ax.text(0.095, 0.88, info, transform=ax.transAxes, fontsize=7.5,
        va="top", ha="left", family="DejaVu Sans",
        bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="#aaaaaa", lw=0.6),
        zorder=7)

# ---------------------------------------------------------------- axes cosmetics
mx, my = 260, 200  # km margins
ax.set_xlim(left * km - mx, right * km + mx)
ax.set_ylim(bottom * km - my, top * km + my)
ax.set_aspect("equal")
ax.set_xlabel("Easting (km, EPSG:3338)", fontsize=9)
ax.set_ylabel("Northing (km, EPSG:3338)", fontsize=9)
ax.tick_params(labelsize=8)
for s in ax.spines.values():
    s.set_color("#bbbbbb")

fig.tight_layout()
fig.savefig(f"{OUT_STEM}.png", dpi=300)
fig.savefig(f"{OUT_STEM}.pdf")
print(f"wrote {OUT_STEM}.png / .pdf")
