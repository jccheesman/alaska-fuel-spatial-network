#!/usr/bin/env python3
"""Stage 05b — assign the AEA energy region per located record.
The logic lives in source_scripts/inventory_qc/assign_region.py — this script only runs it.

    python workflows/00_inventory_qc/05b_assign_region.py [--release 2025]
"""
import sys

from inventory_qc.assign_region import main

if __name__ == "__main__":
    sys.exit(main())
