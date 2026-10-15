# raw_facility_data — tracked facility-inventory releases

One folder per release of the bulk-fuel facility inventory, labelled by release year
(a second release in one year gets a suffix, e.g. `2025-12`). Each folder holds the
**safe-column snapshot** of the release (the clean-schema columns only), its manifest,
a `SOURCE.md` with the full raw file's SHA-256, and a generated diff against the previous
release. From 2025 on the full raw CSV is **not committed** (it carries personal contact fields);
verify a local copy against the SHA-256 in `SOURCE.md`. The 2022 bundle `bulk_fuel_data.zip`
remains tracked in `2022/` for now (it also carries the processed files and the
Fuel_Delivery_Method layer that `tools/extract_inputs.py` unpacks).

Why track releases: differences between releases are evidence. The 2025 release deleted
71 duplicate rows and moved three records (Hooper Bay, Noorvik, Point Lay) into their
labelled communities, confirming corrections we had proposed from the 2022 data.

| Release | Rows | Located | Raw SHA-256 (prefix) | Notes |
|---|---|---|---|---|
| 2022 | 1901 | 1838 | `132338fe0722…` | AEA/DCRA Bulk Fuel Inventory, last AEA edit 2022-12-29. The release both repositories were built from. |
| 2025 | 1830 | 1767 | `3fbee569c63d…` | AEA/DCRA Bulk Fuel Inventory, last AEA edit 2025-12-16. 71 duplicate records removed; 5 records edited (3 map-point corrections). |

## Adding a release

1. Download the AEA CSV; do not open it in anything that re-saves it. Do NOT add the CSV to git (the .gitignore blocks it).
2. `python workflows/00_inventory_qc/01_ingest.py RAW.csv --release <label>` — writes this
   folder, the manifest and the diff; refuses if a kept column is missing.
3. Fill in `SOURCE.md` download date / note, and add the raw SHA-256 to `inputs/MANIFEST.md`.
4. Run `validate-facility-inventory`; review the diff and any corrections it reports as resolved.

Schema and adapters: `inputs/inventory_qc/facility_schema.csv`, `inputs/inventory_qc/sources/`.
