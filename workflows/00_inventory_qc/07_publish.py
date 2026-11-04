#!/usr/bin/env python3
"""Stage 07 — publish the clean facility table.
The logic lives in source_scripts/inventory_qc/publish.py — this script only runs it.

    python workflows/00_inventory_qc/07_publish.py [--release 2025]
"""
import sys

from inventory_qc.publish import main

if __name__ == "__main__":
    sys.exit(main())
