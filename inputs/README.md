# inputs/

Source data for the workflows. **What each dataset is, where it comes from,
whether it is in the repository or must be downloaded and regenerated, and
which script converts it, is documented once, in [`../DATA.md`](../DATA.md).**
This file only says what is in this folder. Checksums of the committed files
are in [`MANIFEST.md`](MANIFEST.md).

**Data terms.** The committed bundles repackage open/public datasets (AEA /
DCRA, AKDOT&PF, USACE, US Census TIGER). `DATA.md` §1 names the original
license holder of each; cite the originals when reusing the data outside this
project.

After cloning: `python tools/extract_inputs.py` unzips the bundles into their
gitignored working directories.

## Layout

| Path | Contents | DATA.md |
|---|---|---|
| `raw_facility_data/<release>/` | One folder per AEA/DCRA bulk-fuel inventory release: the safe-column snapshot, its manifest, a `SOURCE.md` (retrieval date, raw sha256, citation) and the diff against the previous release. The 2022 folder also holds `bulk_fuel_data.zip` (the 2022 raw CSV, the Fuel Delivery Method shapefile). See `raw_facility_data/README.md` for adding a release | §1.1, §2 |
| `inventory_qc/` | The inventory-QC configuration tables (schema, source column maps, corrections, aliases, remote sites, thresholds, derived columns, the facility-id ledger) and the DCRA city / CDP boundary zips (`boundaries/SOURCE.md`) | §1.1, §2 |
| `data_for_network_build.zip` | Curated EPSG:3338 shapefiles: the USACE waterway lines the corridor mask is built from, plus legacy road, ice-road and flight layers kept for provenance | §1.2, §3.2 |
| `region_and_census_data.zip` | The AEA energy-region library (read by the inventory QC) and the 2023 Census state boundary (figures) | §1.1, §1.3 |
| `air/` | The AK DOT&PF airport registry and the matched flight legs (tracked CSVs; `flight_paths.xlsx` is the hand-digitised source) | §1.2, §4.2 |
| `mannual_connections/` | The user-authored manual-connections shapefile, split by `Mode` at build time | §1.2, §4.2 |
| `river_ice/` | `river_ice_sources.zip`: the Brown et al. 2026 reach points and the two NHD-derived river masks, i.e. the river-ice working directory without the 5 GB NHD download (`SOURCE.md` has provenance and checksums) | §1.4, §3.1 |
| `friction_rasters/` | **Not in the repository.** The environmental rasters on the canonical grid; download and regenerate | §1.4, §3.1 |
| `network_raw.zip` | **Not in the repository.** The raw transport and boundary files that populate `data/raw/`; download and regenerate | §4.1 |
| `bulk_fuel_data/`, `data_for_network_build/`, `region_and_census_data/`, `river_ice_work/` | Unzipped working copies written by `tools/extract_inputs.py` (gitignored) | §6 |
