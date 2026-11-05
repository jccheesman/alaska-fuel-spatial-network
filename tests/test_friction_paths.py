"""Path-resolution tests for friction_surface.friction_paths.

The merge moved the package to source_scripts/ and removed the import-time os.chdir;
these tests pin the contract: defaults are absolute, anchored to the repo
root, independent of the caller's CWD — and importing the module never
changes the CWD.

Each case runs in a subprocess so a fresh import happens from a controlled
fake CWD with a controlled environment (the module captures env at import).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

_PROBE = r"""
import json, os, sys
cwd_before = os.getcwd()
import friction_surface.friction_paths as fp
print(json.dumps({
    "cwd_before": cwd_before,
    "cwd_after": os.getcwd(),
    "PROJECT_ROOT": fp.PROJECT_ROOT,
    "RASTER_DIR": fp.RASTER_DIR,
    "FRICTION_OUTPUT_DIR": fp.FRICTION_OUTPUT_DIR,
    "WATERWAY_MASK_TIF": fp.WATERWAY_MASK_TIF,
    "NETWORK_DIR": fp.NETWORK_DIR,
    "lulc": fp.get_raster_path("lulc"),
}))
"""


def _probe_from(cwd: Path, extra_env: dict[str, str] | None = None) -> dict:
    env = {k: v for k, v in os.environ.items()
           if k not in ("RASTER_DIR", "FRICTION_DIR", "NETWORK_DIR",
                        "INPUTS_DIR", "OUTPUTS_DIR")}
    if extra_env:
        env.update(extra_env)
    out = subprocess.run(
        [sys.executable, "-c", _PROBE],
        cwd=cwd, env=env, capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def test_defaults_resolve_to_repo_root_from_fake_cwd(tmp_path):
    """Run from an unrelated CWD: every default must anchor to the repo root."""
    r = _probe_from(tmp_path)
    root = Path(r["PROJECT_ROOT"])
    assert root == REPO_ROOT
    assert Path(r["RASTER_DIR"]) == root / "inputs" / "friction_rasters"
    assert Path(r["FRICTION_OUTPUT_DIR"]) == (
        root / "outputs" / "01_friction_build" / "friction_stack"
    )
    assert Path(r["WATERWAY_MASK_TIF"]) == (
        root / "outputs" / "01_friction_build" / "waterway_mask_150m.tif"
    )
    assert Path(r["NETWORK_DIR"]) == root / "inputs" / "data_for_network_build"
    assert Path(r["lulc"]) == (
        root / "inputs" / "friction_rasters"
        / "dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif"
    )


def test_import_does_not_chdir(tmp_path):
    """The old import-time os.chdir side effect must stay gone."""
    r = _probe_from(tmp_path)
    assert r["cwd_before"] == r["cwd_after"] == str(tmp_path.resolve())


def test_env_overrides_used_verbatim(tmp_path):
    """RASTER_DIR/FRICTION_DIR env overrides take precedence over defaults."""
    r = _probe_from(tmp_path, {"RASTER_DIR": str(tmp_path / "rr"),
                               "FRICTION_DIR": str(tmp_path / "ff")})
    assert Path(r["RASTER_DIR"]) == tmp_path / "rr"
    assert Path(r["FRICTION_OUTPUT_DIR"]) == tmp_path / "ff"
    assert Path(r["lulc"]) == (
        tmp_path / "rr" / "dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif"
    )


def test_dead_constants_removed():
    """ROAD/ICE_ROAD mask + broken CSV constants were deleted in the merge."""
    import friction_surface.friction_paths as fp
    for gone in ("ROAD_MASK_TIF", "ICE_ROAD_MASK_TIF", "FUEL_DELIVERY_METHOD_CSV"):
        assert not hasattr(fp, gone), f"{gone} should have been removed"


# ---------------------------------------------------------------------------
# The one-name rule: every input raster keeps its producer's name all the way
# through the pipeline (owner, 2026-11-04). friction_paths is the only place
# the names live; the two producers that cannot import it (the Earth Engine
# script and the arcpy river-ice pipeline) repeat them verbatim, so pin that
# the copies agree.
# ---------------------------------------------------------------------------
PREPROCESSING = REPO_ROOT / "source_scripts" / "friction_surface" / "friction_preprocessing"


def test_raster_names_are_the_producers_names():
    import friction_surface.friction_paths as fp
    assert fp.RASTER_NAMES == {
        "slope": "FABDEM_slope_150m_EPSG3338.tif",
        "lulc": "dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif",
        "permafrost": "permafrost_probability_150m_EPSG3338.tif",
    }
    assert fp.sea_ice_name(1) == "sea_ice_median_01_Jan_150m_EPSG3338.tif"
    assert fp.sea_ice_name(12) == "sea_ice_median_12_Dec_150m_EPSG3338.tif"
    assert fp.river_ice_name(7) == "river_ice_probability_07_150m_EPSG3338.tif"
    assert fp.sea_ice_relpath(3).replace(os.sep, "/") == (
        "sea_ice/sea_ice_median_03_Mar_150m_EPSG3338.tif"
    )
    assert fp.river_ice_relpath(3).replace(os.sep, "/") == (
        "river_ice/river_ice_probability_03_150m_EPSG3338.tif"
    )


def test_gee_script_exports_the_pipeline_names():
    """The Earth Engine script writes <prefix>_150m_EPSG3338.tif; the prefixes it
    queues must produce exactly the names friction_paths expects."""
    import friction_surface.friction_paths as fp
    js = (PREPROCESSING / "gee_friction_layer_multi_data_processing.js").read_text(encoding="utf-8")
    for key in ("slope", "permafrost"):
        prefix = fp.RASTER_NAMES[key].removesuffix("_150m_EPSG3338.tif")
        assert f"'{prefix}'" in js, f"GEE script no longer exports {prefix}"
    assert f"fileNamePrefix: '{fp.RASTER_NAMES['lulc'].removesuffix('.tif')}'" in js
    assert "'sea_ice_median_' + mm + '_' + name" in js
    assert "'Jan','Feb','Mar','Apr','May','Jun'" in js
    assert fp.MONTH_ABBR == ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def test_arcpy_river_ice_pipeline_repeats_the_names_verbatim():
    """river_ice_full_pipeline.py runs in ArcGIS Pro's Python and cannot import
    friction_paths, so it carries copies of two names; they must not drift."""
    import friction_surface.friction_paths as fp
    src = (PREPROCESSING / "river_ice_full_pipeline.py").read_text(encoding="utf-8")
    assert f'RIVER_ICE_NAME_FMT = "{fp.RIVER_ICE_NAME_FMT}"' in src
    assert f'LULC_NAME          = "{fp.RASTER_NAMES["lulc"]}"' in src
    # and no machine-specific default sneaks back in
    assert "E:\\" not in src and "C:\\Users" not in src


def test_run_drivers_gate_on_the_land_cover_name():
    """Both run_all drivers gate workflow 01 on the grid anchor by its literal name
    (bash cannot import friction_paths); keep the literal in step with the module."""
    import friction_surface.friction_paths as fp
    rel = "inputs/friction_rasters/" + fp.RASTER_NAMES["lulc"]
    assert rel in (REPO_ROOT / "run_all.py").read_text(encoding="utf-8")
    assert rel in (REPO_ROOT / "workflows" / "01_friction_build" / "run_all.sh").read_text(
        encoding="utf-8")
