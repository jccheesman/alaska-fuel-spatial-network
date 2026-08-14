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
    assert Path(r["lulc"]) == root / "inputs" / "friction_rasters" / "lulc.tif"


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
    assert Path(r["lulc"]) == tmp_path / "rr" / "lulc.tif"


def test_dead_constants_removed():
    """ROAD/ICE_ROAD mask + broken CSV constants were deleted in the merge."""
    import friction_surface.friction_paths as fp
    for gone in ("ROAD_MASK_TIF", "ICE_ROAD_MASK_TIF", "FUEL_DELIVERY_METHOD_CSV"):
        assert not hasattr(fp, gone), f"{gone} should have been removed"
