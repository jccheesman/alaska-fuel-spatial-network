"""run_all.py is the Windows twin of the bash drivers. CI proves the two report the
same summary, but only for the stages that run in CI; workflow 02 is always gated off
there (no raw data), so its step list could drift unseen — and did (2026-11: the
Python twin skipped the manual-connections split and used a weaker prep gate). Pin
the cheap part statically: every stage runs the same run_step labels, in the same
order, in both drivers, and the inputs each stage gates on are spelled the same.
"""
import re

import repo_paths as rp

STAGES = ["01_friction_build", "02_network_build", "03_multimodal_join", "04_duckdb_export"]
BASH_STEP = re.compile(r'^\s*run_step\s+"([^"]+)"', re.M)
PY_STEP = re.compile(r'run_step\(\s*"([^"]+)"')


def _py_stage_bodies() -> dict[str, str]:
    src = (rp.ROOT / "run_all.py").read_text(encoding="utf-8")
    bodies = {}
    for stage in STAGES:
        m = re.search(rf"^def stage_{stage}\(.*?(?=^def |^STAGES =)", src, re.M | re.S)
        assert m, f"run_all.py has no stage_{stage}"
        bodies[stage] = m.group(0)
    return bodies


def _bash_steps(stage: str) -> list[str]:
    return BASH_STEP.findall((rp.ROOT / "workflows" / stage / "run_all.sh").read_text(encoding="utf-8"))


def test_every_stage_runs_the_same_steps_in_both_drivers():
    bodies = _py_stage_bodies()
    for stage in STAGES:
        assert PY_STEP.findall(bodies[stage]) == _bash_steps(stage), f"{stage}: step lists differ"


def test_stage_02_gates_are_spelled_the_same():
    """The prep gate (MANIFEST.md, not non-emptiness), the manual-connections layer and
    the six public downloads must be the same literals in both drivers."""
    bash = (rp.ROOT / "workflows" / "02_network_build" / "run_all.sh").read_text(encoding="utf-8")
    py = _py_stage_bodies()["02_network_build"]
    for literal in ("data/interim/MANIFEST.md", "inputs/mannual_connections/mannual_connections.shp"):
        assert literal in bash and literal in py, literal
    bash_raw = re.search(r"RAW_DOWNLOADS=\((.*?)\)", bash, re.S).group(1).split()
    py_raw = re.findall(r'"(data/raw/[^"]+)"', py)
    assert bash_raw == py_raw
