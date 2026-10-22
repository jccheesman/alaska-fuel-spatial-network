#!/usr/bin/env python3
"""Stage 05 — verify community labels against boundaries.
The logic lives in source_scripts/inventory_qc/boundary_check.py — this script only runs it.

    python workflows/00_inventory_qc/05_boundary_check.py [--release 2025]
"""
import sys

from inventory_qc.boundary_check import main

if __name__ == "__main__":
    sys.exit(main())
