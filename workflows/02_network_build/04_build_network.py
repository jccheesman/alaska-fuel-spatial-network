#!/usr/bin/env python3
"""Thin driver: validate the profile, then run the mmnet engine (stages 01->04).

Artifacts land under outputs/02_network_build/ (the mmnet project dir):
  output/01_facilities.gpkg -> 01b_tagged -> 02_hubs -> 03_network__{nodes,edges}
  -> 04_network_joined__{nodes,edges}   plus reports/03_network.md etc.

Requires the prep stages first (00_normalize_raw -> 01_prep_waterway ->
02_prep_airways), which populate data/interim + data/processed from
inputs/network_raw.zip (extract via tools/extract_inputs.py). Rscript with
sf/sfnetworks/tidygraph/dplyr must be on PATH for the R noding oracle.

Run:  python workflows/02_network_build/04_build_network.py [profile.yaml]
"""
import sys
from pathlib import Path

import mmnet
from mmnet.config import validate_profile

ROOT = Path(__file__).resolve().parents[2]  # repo root
PROJ = ROOT / "outputs" / "02_network_build"  # mmnet project dir
PROFILE = Path(__file__).resolve().parent / "profile.yaml"


def main() -> None:
    profile = Path(sys.argv[1]) if len(sys.argv) > 1 else PROFILE
    prof, warnings = validate_profile(profile)
    for w in warnings:
        print(f"[profile warning] {w}")
    PROJ.mkdir(parents=True, exist_ok=True)
    net = mmnet.run_pipeline(profile, project_dir=PROJ)
    print(f"built network: {len(net.nodes):,} nodes / {len(net.edges):,} edges "
          f"-> {PROJ / 'output'}")


if __name__ == "__main__":
    main()
