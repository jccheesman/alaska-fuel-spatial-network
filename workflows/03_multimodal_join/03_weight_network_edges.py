#!/usr/bin/env python3
"""Stage 03 — sample friction along every edge, per month.
The logic lives in source_scripts/fuel_network/weights.py — this script only runs it.

    python workflows/03_multimodal_join/03_weight_network_edges.py
    python workflows/03_multimodal_join/03_weight_network_edges.py --months 2 7    # subset of months (smoke test)
"""
from fuel_network.weights import main

if __name__ == "__main__":
    main()
