#!/usr/bin/env python3
"""Stage 06 — build the owner's review queue.
The logic lives in source_scripts/inventory_qc/review_queue.py — this script only runs it.

    python workflows/00_inventory_qc/06_review_queue.py [--release 2025]
"""
import sys

from inventory_qc.review_queue import main

if __name__ == "__main__":
    sys.exit(main())
