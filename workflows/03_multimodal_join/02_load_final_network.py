#!/usr/bin/env python3
"""Stage 02 — load the frozen handoff into DuckDB + the integrity tripwire.
The logic lives in source_scripts/fuel_network/load.py — this script only runs it.

    python workflows/03_multimodal_join/02_load_final_network.py
    python workflows/03_multimodal_join/02_load_final_network.py --dry-run  # validate only, no write
"""
from fuel_network.load import main

if __name__ == "__main__":
    main()
