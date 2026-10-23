#!/usr/bin/env python3
"""Stage 03 — normalise community names and delivery methods.
The logic lives in source_scripts/inventory_qc/normalise.py — this script only runs it.

    python workflows/00_inventory_qc/03_normalise.py [--release 2025]
"""
import sys

from inventory_qc.normalise import main

if __name__ == "__main__":
    sys.exit(main())
