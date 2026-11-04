#!/usr/bin/env python3
"""Stage 03b — assign the stable facility_id from the append-only ledger.
The logic lives in source_scripts/inventory_qc/assign_facility_ids.py — this script only runs it.

    python workflows/00_inventory_qc/03b_assign_facility_ids.py [--release 2025] [--mint]
"""
import sys

from inventory_qc.assign_facility_ids import main

if __name__ == "__main__":
    sys.exit(main())
