"""friction_surface.py

Deterministic, agent-free friction-surface construction.

Builds the mode-specific friction stack from preprocessed inputs
(slope, LULC, permafrost, monthly sea ice, monthly river ice) for two
transport modes: overland and barge. The stack resolves 24 logical
(mode, month) entries but is deduplicated on disk to 14 files — one
static ``overland.tif`` (no seasonal signal, sampled for all 12 months),
12 monthly ``barge_MM.tif``, and ``road_base.tif`` — see point 4 below.

Design principles
-----------------
1. LULC and permafrost - LULC enters a year-round
   static base; permafrost is a year-round zonal modifier binned from
   Pastick et al. 2015 per-pixel near-surface probability using
   IPA-convention thresholds (Brown et al. 1997) — see
   PERMAFROST_ZONE_BREAKS and PERMAFROST_ZONE_MULTIPLIERS in
   friction_config.
2. The overland mode is a pure environmental terrain surface
   (slope x LULC x permafrost). Roads and ice roads are NOT burned into
   it — on-network land traversal is priced by the network layer, which
   samples road_base.tif along Road / IceRoad / Join edges (IceRoad
   additionally x ICEROAD_TIME_PENALTY, gated to Jan-Mar in
   weight_network_edges). Keeping the overland raster road-free makes it
   the correct bare surface for off-network (terrain) cost-distance.
3. NoData is the sole impassability mechanism. There is no sentinel value.
   WhiteboxTools CostDistance routes around NoData pixels.
4. 24 logical (mode, month) entries, deduplicated on disk. Sea ice and
   river ice are applied per-month to barge, written as barge_{MM}.tif.
   Overland carries no seasonal signal, so instead of 12 identical copies
   it is written once as overland.tif and mapped to all 12 months by the
   runner. With road_base.tif that is 14 files on disk backing the 24
   logical entries. Barge navigability is (LULC water | rasterized waterway
   network) & ~ice — the waterway mask recovers rivers narrower than a
   150 m pixel, and river ice is nearest-filled onto network cells the
   IDW product does not cover so they stay seasonally gated.

"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import numpy as np
import rasterio

from .friction_config import (
    FRICTION_NODATA,
    LULC_FRICTION,
    LULC_WATER_CLASS,
    MODES,
    PERMAFROST_ZONE_BREAKS,
    PERMAFROST_ZONE_MULTIPLIERS,
    RIVER_ICE_THRESHOLD,
    ROAD_FRICTION,
    SEA_ICE_THRESHOLD,
    SLOPE_FRICTION,
    SLOPE_THRESHOLDS,
    WATER_FRICTION_BARGE,
)
from .friction_paths import WATERWAY_MASK_TIF

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Single-factor reclassifications
# ---------------------------------------------------------------------------

def compute_slope_friction(slope_path: str | Path) -> tuple[np.ndarray, dict]:
    """Reclassify a slope raster (degrees) into a friction array.

    NoData pixels (src.nodata sentinel or NaN) are propagated as
    FRICTION_NODATA so downstream stacking does not silently classify
    them as flat (the default initializer would otherwise leak a 1.0
    friction wherever the DEM had a hole).

    Returns (friction, profile). Profile is from the source raster and is
    the canonical grid for downstream stacking.
    """
    with rasterio.open(slope_path) as src:
        slope = src.read(1).astype(np.float32)
        src_nodata = src.nodata
        profile = src.profile.copy()

    lo, hi = SLOPE_THRESHOLDS
    f_flat, f_roll, f_mtn = SLOPE_FRICTION

    friction = np.full(slope.shape, f_flat, dtype=np.float32)
    friction[(slope >= lo) & (slope < hi)] = f_roll
    friction[slope >= hi] = f_mtn

    invalid = np.isnan(slope)
    if src_nodata is not None:
        invalid |= (slope == np.float32(src_nodata))
    friction[invalid] = FRICTION_NODATA
    return friction, profile


def compute_lulc_friction(
    lulc_path: str | Path,
    lulc_lookup: dict[int, float | None] = LULC_FRICTION,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Reclassify a LULC raster into friction values.

    Returns (friction, water_mask, profile). Water pixels (class
    LULC_WATER_CLASS or any class mapped to None) get FRICTION_NODATA in
    the friction array; water_mask is True at those pixels.
    """
    with rasterio.open(lulc_path) as src:
        lulc = src.read(1)
        profile = src.profile.copy()

    max_cls = max(max(lulc_lookup.keys()), int(LULC_WATER_CLASS))
    lookup_arr = np.full(max_cls + 1, np.nan, dtype=np.float32)
    for cls, value in lulc_lookup.items():
        if value is not None:
            lookup_arr[cls] = value

    valid_pixels = (lulc >= 0) & (lulc <= max_cls)
    friction = np.full(lulc.shape, FRICTION_NODATA, dtype=np.float32)
    water_mask = np.ones(lulc.shape, dtype=bool)

    if np.any(valid_pixels):
        vals = np.full(lulc.shape, np.nan, dtype=np.float32)
        vals[valid_pixels] = lookup_arr[lulc[valid_pixels]]
        water_mask = np.isnan(vals) | (lulc == LULC_WATER_CLASS)
        friction[~water_mask] = vals[~water_mask]
    return friction, water_mask, profile


def build_static_base(
    slope_path: str | Path,
    lulc_path: str | Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Year-round terrain base = slope_friction * lulc_friction.

    Multiplicative composition: friction values are travel-time slowdown
    factors, so grade and surface penalties compound.
    Water pixels are FRICTION_NODATA; mode-specific surfaces handle them.
    slope_friction is also returned separately so the road burn-in in
    build_mode_friction can override LULC while preserving grade penalty.

    Returns (static_base, slope_friction, water_mask, profile).
    """
    slope_fric, profile = compute_slope_friction(slope_path)
    lulc_fric, water_mask, _ = compute_lulc_friction(lulc_path)

    if slope_fric.shape != lulc_fric.shape:
        raise ValueError(
            f"Slope shape {slope_fric.shape} != LULC shape {lulc_fric.shape}; "
            "inputs must be on a common grid."
        )

    base = (slope_fric * lulc_fric).astype(np.float32)
    # Propagate slope-NoData as NoData (sentinel × LULC would otherwise
    # be a large negative). Water pixels already get NoData via water_mask.
    slope_invalid = slope_fric == FRICTION_NODATA
    base[water_mask | slope_invalid] = FRICTION_NODATA
    return base, slope_fric, water_mask, profile


def load_permafrost_base(
    permafrost_path: str | Path,
    reference_profile: dict,
) -> np.ndarray:
    """Load permafrost normalized to 0-1.

    Requires the source to already be on the reference grid — alignment is
    an upstream prerequisite (run `friction_preprocessing/align_permafrost.py`
    after each GEE re-export). Preflight enforces this; mismatch here is a
    hard error rather than silent resampling.

    Scale auto-detection: if the source's max > 1.0, treat it as a 0-100
    percentage and divide by 100; otherwise treat it as a 0-1 fraction
    already. Avoids the bug where a 0-1 source got divided to 0-0.01.

    Source NoData pixels are mapped to 0, which `compute_permafrost_modifier`
    bins into the "none" zone (modifier 1.0 — no permafrost penalty).
    """
    ref_crs = reference_profile["crs"]
    ref_transform = reference_profile["transform"]
    ref_width = reference_profile["width"]
    ref_height = reference_profile["height"]

    with rasterio.open(permafrost_path) as src:
        if not (
            src.crs == ref_crs
            and src.transform == ref_transform
            and src.width == ref_width
            and src.height == ref_height
        ):
            raise ValueError(
                f"Permafrost source {permafrost_path} is not on the reference "
                f"grid (src crs={src.crs} shape=({src.height},{src.width}) "
                f"transform={src.transform}; "
                f"ref crs={ref_crs} shape=({ref_height},{ref_width}) "
                f"transform={ref_transform}). Run "
                "`python -m friction_surface.friction_preprocessing.align_permafrost` "
                "to snap it before invoking the pipeline."
            )
        permafrost = src.read(1).astype(np.float32)
        src_nodata = src.nodata
        if src_nodata is not None:
            permafrost = np.where(permafrost == src_nodata, 0.0, permafrost)

    finite_max = float(np.nanmax(permafrost)) if permafrost.size else 0.0
    if finite_max > 1.0:
        permafrost = permafrost / 100.0
    return np.clip(permafrost, 0.0, 1.0)


def compute_permafrost_modifier(permafrost: np.ndarray) -> np.ndarray:
    """Per-pixel multiplicative modifier (>=1.0) by permafrost zone.

    Bins the Pastick et al. 2015 per-pixel near-surface permafrost
    probability p in [0, 1] using IPA-convention thresholds (Brown et al.
    1997) and returns the per-zone multiplier. Applied year-round —
    permafrost transport cost is engineering-persistent (frost heave, thaw
    settlement, ice-rich subgrade maintenance), not seasonal at the
    routing scale.

    Binning (np.digitize, right=False):
        p in [0.00, 0.10) -> none / isolated   -> 1.00
        p in [0.10, 0.50) -> sporadic          -> 1.15
        p in [0.50, 0.90) -> discontinuous     -> 1.30
        p in [0.90, 1.00] -> continuous        -> 1.50
    """
    # Subtract a small epsilon from each break so that pixels at the
    # nominal boundary (e.g. p == 0.90 exactly) bin into the higher zone.
    # float32(0.9) ~ 0.89999998 is strictly less than float64(0.9), and
    # input rasters travel through both dtypes; without the nudge,
    # nominal-90% pixels land in discontinuous instead of continuous.
    # Permafrost extent is noisy at the third decimal so 1e-4 is well
    # within data precision.
    breaks = np.asarray(PERMAFROST_ZONE_BREAKS, dtype=np.float64) - 1e-4
    zone_idx = np.digitize(permafrost, breaks, right=False)
    multipliers = np.asarray(PERMAFROST_ZONE_MULTIPLIERS, dtype=np.float32)
    return multipliers[zone_idx]


def compute_road_base(
    slope_friction: np.ndarray, permafrost_mod: np.ndarray
) -> np.ndarray:
    """Static land-edge friction: max(ROAD_FRICTION, slope_friction) * permafrost_modifier.

    Purely environmental — slope (grades -> trucks) and permafrost (roadbed
    stability) only, NO LULC and NO water mask. This is the friction the
    network-overlay sampler reads along Road / IceRoad / Join edges: Dynamic
    World labels a road-through-forest pixel as "Trees" (impassable), so land
    cover must not enter a road edge's friction. It matches the on-road burn-in
    build_mode_friction already applies (max(ROAD_FRICTION, slope) * permafrost),
    lifted out as a standalone grid so no corridor rasterization is needed.

    NoData-free by construction: max(ROAD_FRICTION, -9999) heals slope-NoData
    (DEM holes) to the flat-road baseline, and permafrost-NoData was already
    mapped to modifier 1.0 upstream. So the downstream strict "any NoData =>
    impassable" edge rule can never sever a land edge on this surface, while
    barge_MM keeps its NoData so ice still blocks water edges. Values in
    [ROAD_FRICTION, max(SLOPE_FRICTION) * max(PERMAFROST_ZONE_MULTIPLIERS)].
    """
    return (
        np.maximum(np.float32(ROAD_FRICTION), slope_friction) * permafrost_mod
    ).astype(np.float32)


# ---------------------------------------------------------------------------
# Mode-specific friction
# ---------------------------------------------------------------------------

def _load_ice(
    path: str | Path,
    reference_profile: dict,
    return_coverage: bool = False,
) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
    """Load an ice-probability raster normalized to 0-1.

    With return_coverage=True, also returns the boolean footprint of source
    data (True where the raster had a real value, False at source NoData).
    The driver uses this to nearest-fill river ice onto waterway-network
    cells the IDW product does not cover — the footprint must be read here,
    before NoData is mapped to 0 and becomes indistinguishable from
    "genuinely ice-free".

    Requires the source to already be on the reference grid — alignment is
    an upstream prerequisite (sea_ice via the GEE export pinned to the
    lulc crsTransform; river_ice via the arcpy pipeline's Step 7 alignment
    in `friction_preprocessing/river_ice_full_pipeline.py`). Preflight
    enforces this; mismatch here is a hard error rather than silent
    resampling.

    Scale auto-detection: if the source's max > 1.0, treat as a 0-100
    percentage and divide by 100; otherwise treat as a 0-1 fraction
    already. Handles the mixed-source case where sea_ice TIFs come out
    of GEE as 0-100 but river_ice TIFs from the arcpy pipeline are
    already 0-1.

    Source NoData pixels (off-river for river_ice; land for sea_ice) map
    to 0, which is the right default for barge gating: "no ice product
    coverage at this cell" reads as "not ice-gated."
    """
    ref_crs = reference_profile["crs"]
    ref_transform = reference_profile["transform"]
    ref_width = reference_profile["width"]
    ref_height = reference_profile["height"]

    with rasterio.open(path) as src:
        if not (
            src.crs == ref_crs
            and src.transform == ref_transform
            and src.width == ref_width
            and src.height == ref_height
        ):
            raise ValueError(
                f"Ice raster {path} is not on the reference grid "
                f"(src crs={src.crs} shape=({src.height},{src.width}) "
                f"transform={src.transform}; "
                f"ref crs={ref_crs} shape=({ref_height},{ref_width}) "
                f"transform={ref_transform}). Re-export onto the lulc grid "
                "(sea_ice: GEE script's crsTransform; river_ice: arcpy "
                "pipeline's Step 7 alignment in river_ice_full_pipeline.py)."
            )
        arr = src.read(1).astype(np.float32)
        src_nodata = src.nodata
        coverage = ~np.isnan(arr)
        if src_nodata is not None:
            coverage &= arr != np.float32(src_nodata)
            arr = np.where(arr == src_nodata, 0.0, arr)

    finite_max = float(np.nanmax(arr)) if arr.size else 0.0
    if finite_max > 1.0:
        arr = arr / 100.0
    arr = np.clip(arr, 0.0, 1.0)
    if return_coverage:
        return arr, coverage
    return arr


def extend_ice_nearest(
    ice: np.ndarray,
    coverage: np.ndarray,
    target_mask: np.ndarray,
    cache: dict,
) -> np.ndarray:
    """Fill ice values onto uncovered target cells from the nearest covered cell.

    The river-ice IDW product covers the main-stem rivers only (~13% of the
    waterway-network corridor). Cells under target_mask (the rasterized
    waterway network) that lack coverage borrow the p_ice of the nearest
    covered cell — tributaries freeze with their trunk stream — preserving
    the north-south freeze gradient that a blanket seasonal window would
    lose. This is an interim measure: the proper fix (re-running the ArcGIS
    IDW over the full waterway network) supersedes it when that pipeline is
    next touched.

    The nearest-source index map depends only on (coverage, target_mask).
    The river-ice footprint is MOSTLY month-invariant (months 1, 4-11
    share one footprint; 2, 3 and 12 differ slightly), so the map is
    memoized in `cache` keyed on the coverage/target sums and recomputed
    only when the footprint actually changes (5 computes per 12-month
    run, ~seconds each).

    Returns a copy of `ice` with the target cells filled.
    """
    from scipy.spatial import cKDTree  # local import; scipy only needed here

    key = (int(coverage.sum()), int(target_mask.sum()))
    if cache.get("key") != key:
        src_rc = np.argwhere(coverage)
        tgt_rc = np.argwhere(target_mask & ~coverage)
        _, nearest = cKDTree(src_rc).query(tgt_rc, k=1, workers=-1)
        cache.update(
            key=key,
            tgt_rows=tgt_rc[:, 0], tgt_cols=tgt_rc[:, 1],
            src_rows=src_rc[nearest, 0], src_cols=src_rc[nearest, 1],
        )
        logger.info(
            "river-ice nearest-fill map: %d covered cells -> %d target cells",
            len(src_rc), len(tgt_rc),
        )

    out = ice.copy()
    out[cache["tgt_rows"], cache["tgt_cols"]] = ice[
        cache["src_rows"], cache["src_cols"]
    ]
    return out


def build_mode_friction(
    static_base: np.ndarray,
    water_mask: np.ndarray,
    permafrost_mod: np.ndarray,
    sea_ice_present: np.ndarray,
    river_ice_present: np.ndarray,
    mode: str,
    waterway_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Produce a mode-specific monthly friction surface.

    Impassable pixels are FRICTION_NODATA. The signature is uniform across
    modes so the driver can loop cleanly. Sea-ice and river-ice masks are
    thresholded by the driver against their own constants
    (SEA_ICE_THRESHOLD / RIVER_ICE_THRESHOLD); barge mode treats either
    type of ice as blocking.

    Overland is a pure terrain surface: static_base (slope x LULC) x
    permafrost on valid land pixels, FRICTION_NODATA on water and DEM
    holes. Roads and ice roads are NOT burned in — on-network land
    traversal is priced separately by the network layer, which samples
    road_base.tif along Road / IceRoad / Join edges (see compute_road_base
    and weight_network_edges). This keeps overland the bare off-network
    terrain surface and makes it month-invariant (no seasonal signal).

    Barge inputs:
        waterway_mask: optional. When provided, barge navigability is
            (lulc_water | waterway_mask) & ~ice: cells on the rasterized
            waterway network count as navigable water even where LULC
            missed them (rivers narrower than a 150 m pixel lose the
            nearest-sample vote to the surrounding land class). The
            network asserts navigability, so burned cells get
            WATER_FRICTION_BARGE like any water pixel. Callers should
            pair this with the nearest-filled river ice (see
            extend_ice_nearest) so recovered tributaries stay seasonally
            gated. Overland is unaffected — its water_mask is unchanged.
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
    if static_base.shape != water_mask.shape:
        raise ValueError("static_base and water_mask shape mismatch")

    out = np.full(static_base.shape, FRICTION_NODATA, dtype=np.float32)
    land_mask = ~water_mask
    valid_base = land_mask & (static_base != FRICTION_NODATA)

    if mode == "overland":
        # Pure terrain: static_base (slope x LULC) x permafrost. Roads and
        # ice roads are priced by the network layer (road_base.tif), not
        # burned in here, so this stays the bare off-network surface.
        out[valid_base] = static_base[valid_base] * permafrost_mod[valid_base]
        return out

    if mode == "barge":
        nav_water = water_mask
        if waterway_mask is not None:
            nav_water = water_mask | (waterway_mask == 1)
        navigable = nav_water & ~(sea_ice_present | river_ice_present)
        out[navigable] = WATER_FRICTION_BARGE
        return out

    raise AssertionError(f"unhandled mode {mode!r}")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _resolve_path(input_dir: Path, name: str) -> Path:
    p = input_dir / name
    if not p.exists():
        raise FileNotFoundError(f"Required input missing: {p}")
    return p


def _load_corridor_mask(
    mask_path: str | Path,
    expected_shape: tuple[int, int],
    build_hint: str,
) -> np.ndarray:
    """Load a binary corridor mask, verifying it matches the friction grid.

    Args:
        mask_path: Path to the corridor TIF (uint8, 1 = corridor, 0 = else).
        expected_shape: (height, width) the mask must match.
        build_hint: Human-readable hint surfaced in the FileNotFoundError so
            the caller knows how to regenerate the file (e.g. "Run
            build_corridor_masks.py to rasterize <shp>").

    Raises FileNotFoundError if the mask is missing (callers can catch this
    when the mask is optional) and ValueError on shape mismatch.
    """
    mask_path = Path(mask_path)
    if not mask_path.exists():
        raise FileNotFoundError(
            f"Corridor mask not found at {mask_path}. {build_hint}"
        )
    with rasterio.open(mask_path) as src:
        arr = src.read(1)
    if arr.shape != expected_shape:
        raise ValueError(
            f"Corridor mask {mask_path} shape {arr.shape} does not match "
            f"friction grid {expected_shape}. Rebuild aligned to the same "
            "reference raster."
        )
    return arr


def write_friction_stack(
    input_dir: str | Path,
    output_dir: str | Path,
    modes: Iterable[str] = MODES,
    months: Iterable[int] = range(1, 13),
    preflight: bool = True,
) -> dict[tuple[str, int], Path]:
    """Build and write all mode-month friction surfaces.

    Inputs expected under input_dir:
      slope.tif, lulc.tif, permafrost.tif,
      sea_ice/sea_ice_{01..12}.tif,
      river_ice/river_ice_{01..12}.tif

    Outputs under output_dir:
      barge_{MM}.tif for each month, plus a single overland.tif and
      road_base.tif. The overland surface is a pure terrain surface
      (slope x LULC x permafrost) with no road or ice-road burn-in and no
      seasonal signal, so it is written once as overland.tif; the returned
      dict still maps all 12 (\"overland\", month) keys to that one file to
      preserve the MODES x 12 contract. Roads and ice roads are priced by
      the network layer, which samples road_base.tif (also written here)
      along Road / IceRoad / Join edges.

    If preflight is True (default), runs friction_preflight.run_preflight
    before any raster is read; raises PreflightError on any FATAL layer
    (missing, wrong CRS/resolution, sub-pixel misalignment, etc.).

    Returns a dict mapping (mode, month) -> output Path.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if preflight:
        # Local import to keep friction_preflight optional for embedders.
        from .friction_preflight import run_preflight
        run_preflight(
            input_dir,
            modes=modes,
            months=months,
        )

    slope_path = _resolve_path(input_dir, "slope.tif")
    lulc_path = _resolve_path(input_dir, "lulc.tif")
    permafrost_path = _resolve_path(input_dir, "permafrost.tif")

    static_base, slope_friction, water_mask, profile = build_static_base(
        slope_path, lulc_path
    )

    out_profile = profile.copy()
    out_profile.update(
        dtype="float32",
        count=1,
        nodata=FRICTION_NODATA,
        compress="lzw",
    )

    written: dict[tuple[str, int], Path] = {}
    modes = tuple(modes)
    months = tuple(months)

    # Roads and ice roads are not burned into the overland raster — the
    # network layer prices on-network land traversal by sampling
    # road_base.tif (written below) along Road / IceRoad / Join edges. The
    # road / ice-road corridor masks are therefore not loaded here.

    # Waterway-network mask widens barge navigability to rivers narrower
    # than a 150 m LULC pixel (the network asserts navigability). Missing
    # file => warn and fall back to LULC-water-only barge surfaces.
    waterway_mask: np.ndarray | None = None
    if "barge" in modes:
        try:
            waterway_mask = _load_corridor_mask(
                WATERWAY_MASK_TIF,
                static_base.shape,
                build_hint=(
                    "Run `python build_corridor_masks.py` to rasterize "
                    "inputs/data_for_network_build/water_networks/"
                    "waterways_network_ak_albers.shp."
                ),
            )
        except FileNotFoundError as e:
            logger.warning(
                "Waterway mask not found (%s) — barge surfaces will sever "
                "rivers narrower than one 150 m LULC pixel (~18%% of "
                "final_network waterway edges).",
                e,
            )

    permafrost_base = load_permafrost_base(
        permafrost_path,
        reference_profile=profile,
    )
    # Zonal permafrost modifier is year-round, so it's computed once and
    # reused across all 12 months.
    permafrost_mod = compute_permafrost_modifier(permafrost_base)

    # Static land-edge friction for the network-overlay sampler (Road / IceRoad
    # / Join edges sample this; IceRoad additionally x ICEROAD_TIME_PENALTY and
    # gated to ICE_ROAD_SEASON_MONTHS). Environmental only, NoData-free — see
    # compute_road_base and PLAN_network_friction_integration.md. Not a mode-month
    # surface, so it is written here but not added to `written` (which the driver
    # length-checks against MODES x 12).
    road_base = compute_road_base(slope_friction, permafrost_mod)
    road_base_path = output_dir / "road_base.tif"
    with rasterio.open(road_base_path, "w", **out_profile) as dst:
        dst.write(road_base, 1)
    logger.info(
        "wrote %s (static land-edge friction; no LULC, NoData-free; min=%.3f max=%.3f)",
        road_base_path, float(road_base.min()), float(road_base.max()),
    )

    # Overland carries no seasonal signal (pure terrain: static_base x
    # permafrost_mod), so it is written once and all 12 ("overland", month)
    # keys point at the single file. Writing it once rather than as 12
    # identical copies avoids ~485 MB of duplicate output per run. Ice inputs
    # are not needed here.
    if "overland" in modes:
        overland = build_mode_friction(
            static_base=static_base,
            water_mask=water_mask,
            permafrost_mod=permafrost_mod,
            sea_ice_present=None,
            river_ice_present=None,
            mode="overland",
            waterway_mask=None,
        )
        overland_path = output_dir / "overland.tif"
        with rasterio.open(overland_path, "w", **out_profile) as dst:
            dst.write(overland, 1)
        for m in range(1, 13):
            written[("overland", m)] = overland_path
        logger.info("wrote %s (static overland surface; sampled for all 12 months)", overland_path)

    # Genuinely seasonal modes are still built per month below.
    monthly_modes = tuple(mode for mode in modes if mode != "overland")

    # Memoizes the nearest-covered-cell index map across the monthly loop
    # (the river-ice footprint is month-invariant).
    ice_fill_cache: dict = {}

    for month in months if monthly_modes else ():
        sea_ice_path = _resolve_path(input_dir, f"sea_ice/sea_ice_{month:02d}.tif")
        river_ice_path = _resolve_path(input_dir, f"river_ice/river_ice_{month:02d}.tif")
        sea_ice = _load_ice(sea_ice_path, reference_profile=profile)
        river_ice, river_ice_cov = _load_ice(
            river_ice_path, reference_profile=profile, return_coverage=True
        )
        if waterway_mask is not None:
            # Tributaries recovered by the waterway mask need an ice gate:
            # borrow p_ice from the nearest IDW-covered river cell so they
            # freeze with their trunk stream instead of reading as open
            # water year-round ("no coverage" would otherwise map to 0).
            river_ice = extend_ice_nearest(
                river_ice, river_ice_cov, waterway_mask == 1, ice_fill_cache
            )

        sea_ice_present = sea_ice > SEA_ICE_THRESHOLD
        river_ice_present = river_ice > RIVER_ICE_THRESHOLD

        for mode in monthly_modes:
            arr = build_mode_friction(
                static_base=static_base,
                water_mask=water_mask,
                permafrost_mod=permafrost_mod,
                sea_ice_present=sea_ice_present,
                river_ice_present=river_ice_present,
                mode=mode,
                waterway_mask=waterway_mask if mode == "barge" else None,
            )
            out_path = output_dir / f"{mode}_{month:02d}.tif"
            with rasterio.open(out_path, "w", **out_profile) as dst:
                dst.write(arr, 1)
            written[(mode, month)] = out_path
            logger.info("wrote %s", out_path)

    return written


def write_road_base(
    input_dir: str | Path,
    output_dir: str | Path,
    filename: str = "road_base.tif",
) -> Path:
    """Emit only the static road_base.tif (slope x permafrost, no LULC).

    Standalone regenerator so road_base can be rebuilt in seconds without
    recomputing the 24 mode-month surfaces. Reads slope.tif + permafrost.tif
    from input_dir, writes output_dir/road_base.tif. Same result as the
    road_base emitted inside write_friction_stack.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    slope_path = _resolve_path(input_dir, "slope.tif")
    permafrost_path = _resolve_path(input_dir, "permafrost.tif")

    slope_friction, profile = compute_slope_friction(slope_path)
    permafrost_mod = compute_permafrost_modifier(
        load_permafrost_base(permafrost_path, reference_profile=profile)
    )
    road_base = compute_road_base(slope_friction, permafrost_mod)

    out_profile = profile.copy()
    out_profile.update(
        dtype="float32", count=1, nodata=FRICTION_NODATA, compress="lzw"
    )
    out_path = output_dir / filename
    with rasterio.open(out_path, "w", **out_profile) as dst:
        dst.write(road_base, 1)
    logger.info(
        "wrote %s  min=%.3f max=%.3f (no NoData)",
        out_path, float(road_base.min()), float(road_base.max()),
    )
    return out_path


if __name__ == "__main__":
    import argparse

    from .friction_paths import RASTER_DIR, get_friction_output_dir

    ap = argparse.ArgumentParser(
        description="Emit road_base.tif (static land-edge friction) only."
    )
    ap.add_argument("--input-dir", default=RASTER_DIR)
    ap.add_argument("--output-dir", default=None)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    out_dir = args.output_dir or get_friction_output_dir()
    write_road_base(args.input_dir, out_dir)
