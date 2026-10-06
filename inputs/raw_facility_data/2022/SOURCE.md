# AEA bulk-fuel inventory — release 2022

- **Source:** Alaska Energy Authority / DCRA "Utilities Bulk Fuel Inventory" (map service CDO_Utilities, layer 48).
- **Raw file:** `Utilities_Bulk_Fuel_Inventory.csv` — inside `bulk_fuel_data.zip` in this folder (tracked; full file incl. contact fields — see plan decision 1b).
- **Raw SHA-256:** `132338fe0722bb9338e8c96e53531be2761a1a0497a0dae734d009ba7e1fb5e1`
- **Raw rows:** 1901 (1838 with coordinates)
- **Downloaded:** 2026-06-01 (copy carried in inputs/bulk_fuel_data.zip)
- **Note:** AEA/DCRA Bulk Fuel Inventory, last AEA edit 2022-12-29. The release both repositories were built from.

## What is committed here

- `aea_inventory_2022.csv` — the 29 clean-schema columns only (see `inputs/inventory_qc/sources/aea/column_map.csv`; written by `workflows/00_inventory_qc/01_ingest.py`), raw row order preserved via `source_row`. SHA-256 `898848c8ff3aaa1e1ba7a656b5cc4c31001fd6b662a61069ecc8ebc8ab695ed4`.
- `snapshot_manifest.json` — checksums, columns kept / dropped / never read, folded fills, unknown columns.
