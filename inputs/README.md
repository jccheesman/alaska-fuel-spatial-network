# inputs/

Source data for the fuel-network and friction-surface pipelines. 
Data that was too large to commit to the **git** can be regenerated in Google Earth Engine
(see `../README.md` → "Preprocessing friction inputs" and
`../EXTERNAL_DATA.md`).

Every dataset below is derived from an open/public source; the "Source" columns
point at the originals so the inputs can be reconstructed independently.

## Committed zips

### `bulk_fuel_data.zip` (0.4 MB)
AEA bulk-fuel facilities and per-community delivery mode.

| File | Source | Purpose |
|---|---|---|
| `raw/Utilities_Bulk_Fuel_Inventory.csv` | Alaska Energy Authority — [State of Alaska Geoportal](https://gis.data.alaska.gov/maps/DCCED::utilities-bulk-fuel-inventory/about) | AEA bulk fuel tank-farm inventory (facility metadata + lat/lon). |
| `raw/Fuel_Delivery_Method.zip` | AEA / DCRA — [Alaska Fuel Delivery Method (Fuel Survey)](https://gis.data.alaska.gov/datasets/DCCED::fuel-delivery-method/about) | Per-community delivery-mode shapefile (`Delivery_Methods` field: barge / road / ice road). Canonical source for how each community is served. |
| `processed/bulk_fuel_sites.geojson`, `processed/bulk_fuel_sites_clean.csv` | derived from the inventory CSV | Cleaned facility set used by the graph build. |
| `processed/sites_with_regions.csv` | derived | Per-site AEA region assignment. |

### `data_for_network_build.zip` (33 MB)
Multi-modal network shapefiles in EPSG:3338 (NAD83 Alaska Albers), curated in ArcGIS Pro.

| Layer | Source |
|---|---|
| `roads_networks/ak_albers_roads_merge.shp` | [AKDOT&PF Roads](https://gis.data.alaska.gov/datasets/AKDOT::roads-akdot) + [GRIP4 global roads](https://www.globio.info/download-grip-dataset) statewide merge |
| `water_networks/…` | [National Waterway Network Lines](https://geospatial-usace.opendata.arcgis.com/maps/ace7645d305647448a84492a3b909d48) (USACE) |
| `ice_roads_150m_3338/Ice_Roads.shp` | Overland packed-snow tundra routes; manually edited in ArcGIS Pro. North Slope ice roads: [UAA](https://accscatalog.uaa.alaska.edu/dataset/anthropogenic-datasets-north-slope/resource/5d898316-507e-4535-8bf0-b0608d3ca83a), [AK DOT](https://www.arcgis.com/home/item.html?id=820ebeed349b484eab23ffaa685b64ef#overview), [SIRA](https://www.arcgis.com/home/item.html?id=ef4056f5fb0545698b5c4318821c8237#overview) |
| `Flights/Airports.csv` | [OurAirports](https://ourairports.com/data/), filtered to Alaska |
| `Flights/flight_paths_combined.csv`, `Flights/Flight Paths.xlsx` | Derived from multiple flight service websites in Alaska and manually digitized in ArcGIS Pro |

### `region_and_census_data.zip` (6.7 MB)
Administrative / boundary polygons.

| File | Source | Purpose |
|---|---|---|
| `Alaska_Energy_Authority_Library.zip` | AEA — [Alaska Energy Authority ArcGIS Hub](https://hub.arcgis.com/datasets/DCCED::alaska-energy-authority-regions/explore?location=61.308100%2C0.314300%2C0) | AEA regional boundary polygons. |
| `tiger/cb_2023_us_state_500k.*` | US Census Bureau — [TIGER/Line Shapefiles](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) | State boundary (Alaska clip). |

## Not committed (regenerated in GEE)

### `gee_exports/AK_Stack_150m.zip` (4.7 GB)
GEE export bundle — mirror of the friction-input rasters at 150 m / EPSG:3338, built from these open source datasets:

| Layer | Source dataset |
|---|---|
| slope / DEM | [FABDEM V1 — GEE community catalog](https://gee-community-catalog.org/projects/fabdem/) |
| permafrost | [Pastick et al. 2015](https://www.sciencedirect.com/science/article/pii/S0034425715300778?via%3Dihub) ([USGS publication](https://www.usgs.gov/publications/distribution-near-surface-permafrost-alaska-estimates-present-and-future-conditions)) |
| land cover | [Dynamic World V1](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1) (GEE) |
| sea ice (12 monthly medians) | [UAF SNAP Historical Sea Ice Atlas](https://catalog.snap.uaf.edu/geonetwork/srv/eng/catalog.search#/metadata/047e91c7-35c6-410a-a1ef-95539c1ee328) |

It exceeds GitHub's 100 MB/file limit, so it is **kept out of git**
(`.gitignore`). Regenerate with
`friction_surface/friction_preprocessing/gee_friction_layer_mutli_data_processing.js`
in the Earth Engine Code Editor, then unzip into
`friction_surface/friction_inputs/` to populate that folder. Full source-dataset
table and step-by-step instructions are in `../README.md` and `../EXTERNAL_DATA.md`. Some datasets were manually downloaded from links above and uploaded to GEE for further processing. 

## Regeneration / refresh

- `bulk_fuel_sites_clean.csv` / `bulk_fuel_sites.geojson` are regenerated from `Utilities_Bulk_Fuel_Inventory.csv` during the fuel-network build.
- `Fuel_Delivery_Method` is downloaded from the AEA ArcGIS service when it changes (rare).
- Network shapefiles are curated by hand in ArcGIS Pro and have no automated regeneration path.
- `AK_Stack_150m.zip` — regenerate in GEE as above.

## Related docs

- `../README.md` — project overview + full preprocessing → pipeline walkthrough
- `../EXTERNAL_DATA.md` — large/external datasets and how to obtain/regenerate them
