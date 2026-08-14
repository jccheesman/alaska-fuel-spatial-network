# inputs/ 

Source data for all four workflows. Anything too large for git is
regenerable; the "Source" columns point at the originals so every input can
be reconstructed independently. Checksums of the committed files live in
[`MANIFEST.md`](MANIFEST.md).

**Data terms.** The committed bundles repackage open/public datasets (AEA /
DCRA, AKDOT&PF, USACE, US Census TIGER, GRIP4 CC-BY, OurAirports). Each table
below names the original license holder; cite the originals when reusing the
data outside this project.

After cloning: `python tools/extract_inputs.py` unzips the
bundles into their gitignored working directories.

## Committed zips

### `data_for_network_build.zip` (~33 MB)
Multi-modal network shapefiles in EPSG:3338 (NAD83 Alaska Albers), curated in
ArcGIS Pro. Feeds the corridor mask (workflow 01) and provenance.

| Layer | Source |
|---|---|
| `roads_networks/ak_albers_roads_merge.shp` | [AKDOT&PF Roads](https://gis.data.alaska.gov/datasets/AKDOT::roads-akdot) + [GRIP4 global roads](https://www.globio.info/download-grip-dataset) statewide merge |
| `water_networks/…` | [National Waterway Network Lines](https://geospatial-usace.opendata.arcgis.com/maps/ace7645d305647448a84492a3b909d48) (USACE) |
| `ice_roads_150m_3338/Ice_Roads.shp` | Overland packed-snow tundra routes; manually edited in ArcGIS Pro. North Slope ice roads: [UAA](https://accscatalog.uaa.alaska.edu/dataset/anthropogenic-datasets-north-slope/resource/5d898316-507e-4535-8bf0-b0608d3ca83a), [AK DOT](https://www.arcgis.com/home/item.html?id=820ebeed349b484eab23ffaa685b64ef#overview), [SIRA](https://www.arcgis.com/home/item.html?id=ef4056f5fb0545698b5c4318821c8237#overview) |
| `Flights/Airports.csv` | [OurAirports](https://ourairports.com/data/), filtered to Alaska |
| `Flights/flight_paths_combined.csv`, `Flights/Flight Paths.xlsx` | Derived from multiple flight service websites in Alaska, manually digitized |

## Pending: `network_raw.zip` (workflow 02's raw sources, ~60 MB)

The network build's raw GIS data (AKDOT roads + GRIP4 Canada, USACE NWN
waterways, Ice_Roads, TIGER places / county subdivisions / boroughs,
Ports_and_Harbors, AEA facilities CSV, Fuel_Delivery_Method.geojson)
is **kept local-only** (the assembled zip exists on this build machine but
is gitignored and was purged from git history on 2026-08-08): committing it
is gated on the data-redistribution decision.

Until it lands, populate `data/raw/` by either:
1. copying `data/raw/**` from the original `alaska_network_mmnet` working
   tree into this repo's `data/raw/`, or
2. re-downloading from the sources in the tables above (AKDOT&PF, GRIP4,
   USACE NWN, TIGER 2022 place/cousub/boroughs, AEA Geoportal) and running
   `workflows/02_network_build/00_normalize_raw.py`, whose SPEC table
   documents the expected file-by-file layout.

Once the license check clears: build the zip from `data/raw/**` (junk
excluded, `Flight Paths.xlsx` renamed `flight_paths.xlsx`), un-ignore and commit it,
and record its sha256 in `MANIFEST.md` — `tools/extract_inputs.py` already
knows how to unpack it.

## Not committed (regenerable only)

### `gee_exports/AK_Stack_150m.zip` (4.7 GB)
GEE export bundle — mirror of the friction-input rasters at 150 m /
EPSG:3338. Exceeds GitHub's file limit; regenerate with
`source_scripts/friction_surface/friction_preprocessing/gee_friction_layer_multi_data_processing.js`
in the Earth Engine Code Editor.

| Layer | Source dataset |
|---|---|
| slope / DEM | [FABDEM V1 — GEE community catalog](https://gee-community-catalog.org/projects/fabdem/) |
| permafrost | [Pastick et al. 2015](https://www.sciencedirect.com/science/article/pii/S0034425715300778) ([USGS](https://www.usgs.gov/publications/distribution-near-surface-permafrost-alaska-estimates-present-and-future-conditions)) |
| land cover | [Dynamic World V1](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1) (GEE) |
| sea ice (12 monthly medians) | [UAF SNAP Historical Sea Ice Atlas](https://catalog.snap.uaf.edu/geonetwork/srv/eng/catalog.search#/metadata/047e91c7-35c6-410a-a1ef-95539c1ee328) |

**The final layers are alos hosted on GEE. Final friction stack TIF files are hosted on Google Earth Engine at:**

Barge_monthly Image Collection: https://code.earthengine.google.com/?asset=projects/gee-friction-layer-processing/assets/friction_stack_final/barge_monthly

Overland Friction: https://code.earthengine.google.com/?asset=projects/gee-friction-layer-processing/assets/friction_stack_final/overland_base

Road_base Friction: https://code.earthengine.google.com/?asset=projects/gee-friction-layer-processing/assets/friction_stack_final/road_base

### `friction_rasters/` (~7 GB)
`slope.tif`, `lulc.tif`, `permafrost.tif`, `sea_ice/sea_ice_{01..12}.tif`,
`river_ice/river_ice_{01..12}.tif` — unzip the GEE stack here, then run the
arcpy river-ice pipeline + `align_permafrost`
(`source_scripts/friction_surface/friction_preprocessing/`). See `../EXTERNAL_DATA.md`
for the honest inventory of what exists where.

## Regeneration / refresh

- `bulk_fuel_sites_clean.csv` / `bulk_fuel_sites.geojson` — regenerated from
  `Utilities_Bulk_Fuel_Inventory.csv` during the network build.
- `Fuel_Delivery_Method` — re-download from the AEA ArcGIS service when it
  changes (rare).
- Network shapefiles — curated by hand in ArcGIS Pro; no automated
  regeneration path.
- `AK_Stack_150m.zip` / `friction_rasters/` — regenerate in GEE + arcpy as
  above.

## Related docs

- `../README.md` — project overview + the four-act pipeline walkthrough
- `../EXTERNAL_DATA.md` — large/external datasets: what exists where, and how to regenerate
- `../docs/DATA_CONTRACTS.md` — every inter-stage data contract on one page
