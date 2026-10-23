"""paper/, diagnostics/ and tools/ hold standalone scripts nobody runs on every build, so they
rot silently: the 2026-10 sort found four that could not run (package-relative imports outside
a package, paths to folders that no longer exist, paths on one machine). Pin the cheap part:
each one parses, imports nothing relatively, and names no machine-specific path.
"""
import ast
import re

import pytest

import repo_paths as rp

SCRIPTS = sorted(p for d in ("paper", "diagnostics", "tools") for p in (rp.ROOT / d).rglob("*.py"))
MACHINE_PATH = re.compile(r"""['"](/mnt/|/tmp/|/Users/|[A-Za-z]:\\)""")

# Allowed exceptions, each with its reason (keep this list short).
KNOWN_MACHINE_PATHS = {
    # reads /tmp intermediates of the 2026 river-ice marine-leak investigation (never committed);
    # kept as the record of that figure, documented in diagnostics/README.md
    "diagnostics/01_friction_build/plot_marine_clip.py",
}


def _rel(p):
    return p.relative_to(rp.ROOT).as_posix()


@pytest.mark.parametrize("path", SCRIPTS, ids=_rel)
def test_script_parses_and_imports_absolutely(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    relative = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.level]
    assert not relative, f"{_rel(path)}: relative import at line(s) {relative} — a script is not a package"


@pytest.mark.parametrize("path", SCRIPTS, ids=_rel)
def test_script_names_no_machine_specific_path(path):
    if _rel(path) in KNOWN_MACHINE_PATHS:
        pytest.skip("documented exception")
    hits = [i for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
            if MACHINE_PATH.search(line)]
    assert not hits, f"{_rel(path)}: machine-specific path at line(s) {hits} — use repo_paths"
