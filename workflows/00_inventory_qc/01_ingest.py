#!/usr/bin/env python3
"""Stage 01 — ingest a facility-inventory release onto the clean schema.
The logic lives in source_scripts/inventory_qc/ingest.py — this script only runs it.

    python workflows/00_inventory_qc/01_ingest.py RAW.csv --release 2025
    python workflows/00_inventory_qc/01_ingest.py --check      # verify committed releases
"""
import sys

from inventory_qc.ingest import main

if __name__ == "__main__":
    sys.exit(main())
