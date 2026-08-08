#!/usr/bin/env python3
"""Extract the frozen network-of-record zips for workflow 03's readers.

final_network/network_joined_{nodes,edges}.zip -> final_network/
network_joined_{nodes,edges}/ shapefile dirs (gitignored, regenerable by
re-running this script). Fixes the fresh-clone FileNotFoundError the old
README papered over ("load_final_network.py extracts the zips" — it never
did).

__MACOSX resource-fork entries are skipped. Extraction is idempotent.

Run:  python workflows/03_multimodal_join/01_extract_network_handoff.py
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root
FINAL = ROOT / "final_network"


def main() -> None:
    for stem in ("network_joined_nodes", "network_joined_edges"):
        zpath = FINAL / f"{stem}.zip"
        if not zpath.exists():
            raise SystemExit(f"{zpath} missing — clone incomplete? (Git LFS: run `git lfs pull`)")
        with zipfile.ZipFile(zpath) as zf:
            members = [m for m in zf.namelist()
                       if not m.startswith("__MACOSX/") and not m.endswith(".DS_Store")]
            zf.extractall(FINAL, members=members)
        shp = FINAL / stem / f"{stem}.shp"
        if not shp.exists():
            raise SystemExit(f"extraction of {zpath.name} did not produce {shp}")
        print(f"extracted {zpath.name} -> {shp.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
