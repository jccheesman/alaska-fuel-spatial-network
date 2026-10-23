#!/usr/bin/env python3
"""Stage 02 — apply the owner-approved corrections.
The logic lives in source_scripts/inventory_qc/apply_corrections.py — this script only runs it.

    python workflows/00_inventory_qc/02_apply_corrections.py [--release 2025]
"""
import sys

from inventory_qc.apply_corrections import main

if __name__ == "__main__":
    sys.exit(main())
