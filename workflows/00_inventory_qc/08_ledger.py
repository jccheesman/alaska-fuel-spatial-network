#!/usr/bin/env python3
"""Stage 08 — write the per-release inventory ledger workbook.
The logic lives in source_scripts/inventory_qc/ledger.py — this script only runs it.

    python workflows/00_inventory_qc/08_ledger.py [--release 2025]
"""
import sys

from inventory_qc.ledger import main

if __name__ == "__main__":
    sys.exit(main())
