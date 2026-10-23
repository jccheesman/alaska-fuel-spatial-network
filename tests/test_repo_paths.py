"""repo_paths is the one place repository locations are defined.

Two contracts: every tracked location it names exists (a folder move that forgets
repo_paths fails here, not mid-pipeline), and no script recomputes the repo root
from its own file location (that pattern is what made moves cost dozens of edits).
"""
import re
import subprocess
import sys

import repo_paths as rp

# Locations that are committed, so they exist on a fresh clone.
TRACKED = [
    rp.INPUTS, rp.OUTPUTS, rp.WORKFLOWS, rp.FINAL_NETWORK,
    rp.FACILITY_RELEASES, rp.INVENTORY_QC, rp.AIR_INPUTS, rp.MANUAL_CONNECTIONS,
    rp.INVENTORY_QC_OUT, rp.FIGURES, rp.TABLES,
    rp.INVENTORY_QC_WORKFLOW, rp.NETWORK_PROFILE,
    rp.HUB_MEMBERS_CSV, rp.HUB_SNAPS_CSV,
    rp.FINAL_NODES_SHP.parent.with_suffix(".zip"),
    rp.FINAL_EDGES_SHP.parent.with_suffix(".zip"),
]

# May locate themselves: they run before (or without) the project environment.
SELF_LOCATING = {"run_all.py", "tools/extract_inputs.py", "source_scripts/repo_paths.py",
                 "tests/test_friction_paths.py",   # an independent oracle for friction_paths
                 "source_scripts/mmnet/config.py"}  # region-agnostic engine's own default dir

ROOT_FROM_FILE = re.compile(r"Path\(__file__\)\.resolve\(\)\.parents\[\d\]"
                            r"|dirname\(os\.path\.dirname\(os\.path\.(abs|real)path\(__file__\)")


def test_root_is_the_repository():
    assert (rp.ROOT / "pyproject.toml").is_file()
    assert (rp.ROOT / "CLAUDE.md").is_file()


def test_tracked_locations_exist():
    missing = [str(p.relative_to(rp.ROOT)) for p in TRACKED if not p.exists()]
    assert not missing, f"repo_paths names locations that are not in the tree: {missing}"


def test_no_script_recomputes_the_repo_root():
    files = subprocess.run(["git", "ls-files", "*.py"], cwd=rp.ROOT, capture_output=True,
                           text=True, check=True).stdout.split()
    offenders = [f for f in files
                 if f not in SELF_LOCATING and not f.startswith("docs/data_audit/")
                 and ROOT_FROM_FILE.search((rp.ROOT / f).read_text(encoding="utf-8"))]
    assert not offenders, f"locate the repo via `import repo_paths as rp` instead: {offenders}"


def test_a_script_resolves_to_its_own_checkout(tmp_path):
    """Another clone's script, run with this environment, must see that clone — not this one."""
    clone = tmp_path / "clone"
    (clone / "source_scripts").mkdir(parents=True)
    (clone / "source_scripts" / "repo_paths.py").write_text("# marker\n")
    script = clone / "workflows" / "probe.py"
    script.parent.mkdir()
    script.write_text("import repo_paths as rp; print(rp.ROOT)\n")
    out = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True,
                         text=True, check=True).stdout.strip()
    assert out == str(clone.resolve())
