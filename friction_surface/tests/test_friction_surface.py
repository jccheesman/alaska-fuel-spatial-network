"""Tests for friction_surface.

Run from the project root:
    pytest friction_surface/tests/test_friction_surface.py -v
"""

from __future__ import annotations
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from ..friction_surface import _load_ice, build_mode_friction, load_permafrost_base


CRS = "EPSG:3338"
RES = 150.0  # meters per pixel


def _make_ref_profile(width: int, height: int) -> dict:
    """Reference profile anchored at projection origin (0, 0)."""
    transform = from_origin(0.0, 0.0, RES, RES)
    return {
        "crs": rasterio.crs.CRS.from_string(CRS),
        "transform": transform,
        "width": width,
        "height": height,
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
    }


def _write_raster(path, data: np.ndarray, transform, nodata=None) -> None:
    profile = {
        "driver": "GTiff",
        "height": data.shape[0],
        "width": data.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": CRS,
        "transform": transform,
    }
    if nodata is not None:
        profile["nodata"] = nodata
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data.astype(np.float32), 1)


def test_load_permafrost_base_same_grid(tmp_path):
    """Source grid matches reference: returns data normalized to [0, 1]."""
    ref = _make_ref_profile(20, 20)
    data = np.full((20, 20), 50.0, dtype=np.float32)
    path = tmp_path / "permafrost.tif"
    _write_raster(path, data, ref["transform"])

    out = load_permafrost_base(path, reference_profile=ref)

    assert out.shape == (20, 20)
    assert out.dtype == np.float32
    np.testing.assert_allclose(out, 0.5)


def test_load_permafrost_base_raises_on_grid_mismatch(tmp_path):
    """Source on a different grid: hard error.

    Alignment is an upstream prerequisite
    (friction_preprocessing/align_permafrost.py). The loader does not
    resample; any mismatch must raise with a message that points at the fix.
    """
    ref = _make_ref_profile(20, 20)
    src_transform = from_origin(5 * RES, -5 * RES, RES, RES)
    data = np.full((10, 10), 50.0, dtype=np.float32)
    path = tmp_path / "permafrost_offset.tif"
    _write_raster(path, data, src_transform)

    with pytest.raises(ValueError, match="align_permafrost"):
        load_permafrost_base(path, reference_profile=ref)


def test_load_permafrost_base_auto_detects_fractional_source(tmp_path):
    """Auto-detect: max <= 1.0 -> already a 0-1 fraction, don't divide.

    This is the river_ice-style case where the source is already 0-1
    (max=0.7 here). The /100 step would have wrongly produced 0-0.007.
    """
    ref = _make_ref_profile(10, 10)
    data = np.full((10, 10), 0.7, dtype=np.float32)
    path = tmp_path / "permafrost_fraction.tif"
    _write_raster(path, data, ref["transform"])

    out = load_permafrost_base(path, reference_profile=ref)
    np.testing.assert_allclose(out, 0.7)


def test_load_ice_auto_detects_fractional_source(tmp_path):
    """Auto-detect on _load_ice: max <= 1.0 -> no divide (river_ice case)."""
    ref = _make_ref_profile(10, 10)
    data = np.full((10, 10), 0.8, dtype=np.float32)
    path = tmp_path / "river_ice_fraction.tif"
    _write_raster(path, data, ref["transform"])

    out = _load_ice(path, reference_profile=ref)
    np.testing.assert_allclose(out, 0.8)


def test_load_ice_same_grid(tmp_path):
    """Source matches reference: returns data normalized to [0, 1]."""
    ref = _make_ref_profile(20, 20)
    data = np.full((20, 20), 60.0, dtype=np.float32)
    path = tmp_path / "sea_ice.tif"
    _write_raster(path, data, ref["transform"])

    out = _load_ice(path, reference_profile=ref)

    assert out.shape == (20, 20)
    assert out.dtype == np.float32
    np.testing.assert_allclose(out, 0.6)


def test_load_ice_raises_on_grid_mismatch(tmp_path):
    """Source on a different grid: hard error.

    Alignment is an upstream prerequisite (sea_ice via the GEE crsTransform;
    river_ice via the arcpy pipeline's Step 7 alignment). The loader does not
    resample.
    """
    ref = _make_ref_profile(20, 20)
    src_transform = from_origin(5 * RES, -5 * RES, RES, RES)
    data = np.full((10, 10), 80.0, dtype=np.float32)
    path = tmp_path / "river_ice_offset.tif"
    _write_raster(path, data, src_transform)

    with pytest.raises(ValueError, match="reference grid"):
        _load_ice(path, reference_profile=ref)


def test_ice_split_invariant_at_equal_thresholds():
    """Per-source ice gating collapses to a combined-max gate at equal thresholds.

    The barge branch gates on `sea_present | river_present`, where each source
    uses its own threshold. When SEA_ICE_THRESHOLD == RIVER_ICE_THRESHOLD, that
    per-source OR is pointwise identical to a single `max(sea, river) > T` gate.
    The two thresholds can be set independently (e.g. a distinct river-ice limit
    for a future frozen-river mode); this test only asserts the equal-threshold
    equivalence and skips when they differ.
    """
    import pytest
    from ..friction_config import SEA_ICE_THRESHOLD, RIVER_ICE_THRESHOLD
    if SEA_ICE_THRESHOLD != RIVER_ICE_THRESHOLD:
        pytest.skip(
            "Thresholds differ (sea vs river), so the per-source gate does not "
            "reduce to a combined-max gate — barge output differs in shoulder "
            "months by design."
        )

    rng = np.random.default_rng(0)
    sea = rng.random(1000).astype(np.float32)
    river = rng.random(1000).astype(np.float32)

    combined_max = np.maximum(sea, river) > SEA_ICE_THRESHOLD
    per_source = (sea > SEA_ICE_THRESHOLD) | (river > RIVER_ICE_THRESHOLD)
    np.testing.assert_array_equal(combined_max, per_source)


def _bridge_test_inputs():
    """Synthetic 5x5 grid: vertical 1-pixel river in col 2, land elsewhere.

    The river column is water (NoData in the overland surface). The trailing
    road_mask / slope_friction elements are retained for signature
    compatibility but are unused now that overland carries no road burn-in.
    """
    shape = (5, 5)
    static_base = np.full(shape, 1.5, dtype=np.float32)
    static_base[:, 2] = -9999.0  # mirror FRICTION_NODATA inside the water column
    water_mask = np.zeros(shape, dtype=bool)
    water_mask[:, 2] = True       # vertical river
    permafrost_mod = np.ones(shape, dtype=np.float32)
    no_ice = np.zeros(shape, dtype=bool)
    road_mask = np.zeros(shape, dtype=np.uint8)
    road_mask[2, :] = 1           # horizontal road
    # Flat slope everywhere — keeps the bridge/road tests deterministic;
    # the road-on-land burn-in becomes max(ROAD_FRICTION, 1.0) = 1.0.
    slope_friction = np.full(shape, 1.0, dtype=np.float32)
    return (static_base, water_mask, permafrost_mod, no_ice, road_mask,
            slope_friction)


def test_overland_is_pure_terrain_static_base_times_permafrost():
    """Overland land pixels = static_base × permafrost; no road/ice burn-in.

    Roads and ice roads are priced by the network layer (road_base.tif),
    not burned into the overland raster, so a land cell that happens to sit
    on the (now ignored) road row gets plain terrain cost.
    """
    sb, wm, pm, ni, _, _ = _bridge_test_inputs()
    pm[:] = 1.15  # sporadic permafrost zone → uniform 1.15 modifier

    out = build_mode_friction(
        static_base=sb, water_mask=wm, permafrost_mod=pm,
        sea_ice_present=ni, river_ice_present=ni,
        mode="overland",
    )

    # Land cells: static_base (1.5) × permafrost (1.15) — no road override.
    for c in (0, 1, 3, 4):
        assert out[2, c] == pytest.approx(1.5 * 1.15)


def test_overland_water_pixels_are_nodata():
    """Water column stays NoData — no bridge burn-in reconnects it now."""
    from ..friction_config import FRICTION_NODATA
    sb, wm, pm, ni, _, _ = _bridge_test_inputs()

    out = build_mode_friction(
        static_base=sb, water_mask=wm, permafrost_mod=pm,
        sea_ice_present=ni, river_ice_present=ni,
        mode="overland",
    )

    # The entire river column (including the former road-river crossing at
    # (2, 2)) is NoData: on-network crossings are priced in the network
    # layer, not bridged into the overland raster.
    np.testing.assert_array_equal(out[:, 2], FRICTION_NODATA)


def _make_stack_inputs(input_dir, iced_month: int = 1) -> None:
    """Write a tiny but complete input tree for write_friction_stack.

    8x8 grid on the projection origin, all layers on one grid so the build
    never hits an alignment error:
      - slope: flat 1.0 deg (slope friction 1.0)
      - lulc:  shrub_scrub (class 5) everywhere except a 1-pixel water
               column (class 0) at col 3
      - permafrost: 0.0 -> "none" zone (modifier 1.0)
      - sea_ice: fully iced (1.0) in `iced_month`, ice-free (0.0) otherwise
      - river_ice: ice-free (0.0) every month
    """
    from ..friction_config import LULC_WATER_CLASS

    transform = from_origin(0.0, 0.0, RES, RES)
    shape = (8, 8)

    slope = np.ones(shape, dtype=np.float32)
    _write_raster(input_dir / "slope.tif", slope, transform)

    lulc = np.full(shape, 5, dtype=np.uint8)  # LULC is an integer class raster
    lulc[:, 3] = int(LULC_WATER_CLASS)        # vertical river column
    lulc_profile = {
        "driver": "GTiff", "height": shape[0], "width": shape[1], "count": 1,
        "dtype": "uint8", "crs": CRS, "transform": transform,
    }
    with rasterio.open(input_dir / "lulc.tif", "w", **lulc_profile) as dst:
        dst.write(lulc, 1)

    permafrost = np.zeros(shape, dtype=np.float32)
    _write_raster(input_dir / "permafrost.tif", permafrost, transform)

    (input_dir / "sea_ice").mkdir()
    (input_dir / "river_ice").mkdir()
    for m in range(1, 13):
        sea = np.full(shape, 1.0 if m == iced_month else 0.0, dtype=np.float32)
        _write_raster(input_dir / "sea_ice" / f"sea_ice_{m:02d}.tif", sea, transform)
        river = np.zeros(shape, dtype=np.float32)
        _write_raster(input_dir / "river_ice" / f"river_ice_{m:02d}.tif", river, transform)


def test_write_friction_stack_end_to_end(tmp_path, monkeypatch):
    """Smoke test the full build/write contract on synthetic inputs.

    This is the handoff check: a clean checkout can build the stack and get
    the documented 14-file / 24-entry output with the right NoData semantics,
    without any real data. Preflight is skipped (its grid checks are covered
    by the loader tests above) and the waterway mask is pointed at a missing
    path so barge uses the documented LULC-water fallback rather than the
    full-Alaska mask on disk.
    """
    from ..friction_surface import write_friction_stack
    from ..friction_config import FRICTION_NODATA

    monkeypatch.setattr(
        "friction_surface.friction_surface.WATERWAY_MASK_TIF",
        str(tmp_path / "no_such_waterway_mask.tif"),
    )

    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    output_dir = tmp_path / "stack"
    _make_stack_inputs(input_dir, iced_month=1)

    written = write_friction_stack(input_dir, output_dir, preflight=False)

    # --- 24 logical (mode, month) entries; overland dedups to one file ---
    assert len(written) == 24
    overland_paths = {written[("overland", m)] for m in range(1, 13)}
    assert len(overland_paths) == 1, "all 12 overland months must map to one file"

    # --- 14 files on disk: overland + road_base + 12 barge ---
    tifs = {p.name for p in output_dir.glob("*.tif")}
    expected = {"overland.tif", "road_base.tif"} | {f"barge_{m:02d}.tif" for m in range(1, 13)}
    assert tifs == expected
    assert not any(name.startswith("overland_") for name in tifs), "no per-month overland files"

    water_col = 3
    land_cols = [c for c in range(8) if c != water_col]

    # --- overland: water column is NoData; land is finite terrain cost ---
    with rasterio.open(output_dir / "overland.tif") as ds:
        ov = ds.read(1)
        assert ds.nodata == FRICTION_NODATA
    np.testing.assert_array_equal(ov[:, water_col], FRICTION_NODATA)
    assert np.all(ov[:, land_cols] > 0)
    assert not np.any(ov[:, land_cols] == FRICTION_NODATA)

    # --- barge ice-free month: water navigable, land NoData ---
    with rasterio.open(output_dir / "barge_02.tif") as ds:
        barge_open = ds.read(1)
    assert np.all(barge_open[:, water_col] > 0), "open-water barge cells must be navigable"
    np.testing.assert_array_equal(barge_open[:, land_cols], FRICTION_NODATA)

    # --- barge fully-iced month (01): even the water column gates to NoData ---
    with rasterio.open(output_dir / "barge_01.tif") as ds:
        barge_iced = ds.read(1)
    np.testing.assert_array_equal(barge_iced[:, water_col], FRICTION_NODATA)

    # --- road_base is NoData-free by construction ---
    with rasterio.open(output_dir / "road_base.tif") as ds:
        rb = ds.read(1)
    assert np.all(np.isfinite(rb))
    assert not np.any(rb == FRICTION_NODATA)


def test_load_permafrost_base_error_points_at_align_script(tmp_path):
    """Grid-mismatch ValueError names the upstream fix.

    The error must mention `align_permafrost` so callers know which
    preprocessing script to run rather than guessing at a manual reproject.
    """
    ref = _make_ref_profile(20, 20)
    src_transform = from_origin(5 * RES, -5 * RES, RES, RES)
    data = np.full((10, 10), 50.0, dtype=np.float32)
    path = tmp_path / "permafrost_offgrid.tif"
    _write_raster(path, data, src_transform)

    with pytest.raises(ValueError) as exc_info:
        load_permafrost_base(path, reference_profile=ref)
    msg = str(exc_info.value)
    assert "align_permafrost" in msg
    assert "reference grid" in msg
