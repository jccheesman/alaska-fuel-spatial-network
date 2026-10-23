#!/usr/bin/env python3
"""Stage 04 — $-rates x friction -> edge_costs + the weighted graph.
The logic lives in source_scripts/fuel_network/graph.py — this script only runs it.

    python workflows/03_multimodal_join/04_assemble_weighted_graph.py
    python workflows/03_multimodal_join/04_assemble_weighted_graph.py --dry-run  # compute + QA, no write
"""
from fuel_network.graph import main

if __name__ == "__main__":
    main()
