#!/usr/bin/env python3
"""Stage 04 — structural detectors.
The logic lives in source_scripts/inventory_qc/detect.py — this script only runs it.

    python workflows/00_inventory_qc/04_detect.py [--release 2025]
"""
import sys

from inventory_qc.detect import main

if __name__ == "__main__":
    sys.exit(main())
