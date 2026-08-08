#!/usr/bin/env python3
"""Thin driver: build the friction stack (overland, road_base, barge_01..12).

Calls friction_surface.run_friction_pipeline.main — writes 14 TIFs backing 24
logical (mode, month) surfaces into outputs/01_friction_build/friction_stack/.

Requires: inputs/friction_rasters/ (regenerable — see EXTERNAL_DATA.md) and
the waterway corridor mask from 01_build_corridor_masks.py (the barge build
degrades with only a warning without it, severing ~18% of waterway edges —
run stage 01 first).

Run:  python workflows/01_friction_build/02_build_friction_stack.py [--input-dir D] [--output-dir D]
"""
from friction_surface.run_friction_pipeline import main

if __name__ == "__main__":
    main()
