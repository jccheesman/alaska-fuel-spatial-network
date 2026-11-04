# GLOSSARY — the words this repository assumes you know

Written for a researcher who has never worked on Alaska and never seen this
pipeline. Three lists: the agencies and datasets, the Alaskan geography, and the
pipeline's own vocabulary. `DATA.md` says where each dataset comes from; this
file only says what the words mean.

## Agencies, datasets and tools

| Term | Meaning |
|---|---|
| **ACCS** | Alaska Center for Conservation Science, at the University of Alaska Anchorage (UAA). Publishes North Slope anthropogenic datasets, one of the three ice-road sources. |
| **ACEP** | Alaska Center for Energy and Power, at the University of Alaska Fairbanks (UAF). Its public bulk-fuel file was used as evidence in the 2026-10 inventory audit, never merged. |
| **AEA** | Alaska Energy Authority, a state corporation. With DCRA it maintains the bulk-fuel facility inventory the network is built from, and it defines the **AEA energy regions** the facilities are tagged with. |
| **AKDOT&PF** | Alaska Department of Transportation and Public Facilities. Source of the road layer (the only road source since 2026-09) and of the airport registry. |
| **AOOS** | Alaska Ocean Observing System. Co-producer, with SNAP, of the Historical Sea Ice Atlas. |
| **Arctic Data Center** | The NSF repository that hosts the Brown et al. 2026 river-ice dataset (DOI 10.18739/A2SB3X15X). |
| **arcpy** | The Python library of ArcGIS Pro (Esri; Windows only, licensed). Only the river-ice interpolation uses it; everything else is open Python. |
| **Brown et al. 2026** | River-ice phenology dataset: for each of thirty Alaskan rivers, reach points with the median open-water fraction (`areaPropMedWater`) per month, 2000–2023. The pipeline turns it into a monthly ice probability. |
| **BTS / NTAD** | Bureau of Transportation Statistics / National Transportation Atlas Database. A second host of the waterway network lines. |
| **CDP** | Census Designated Place: an unincorporated community whose boundary the US Census draws for statistics. Most Alaskan villages are CDPs, not incorporated cities, so the inventory QC checks labels against both city and CDP boundaries. |
| **DCCED** | Alaska Department of Commerce, Community, and Economic Development. Parent of DCRA; its data portal hosts the facility inventory and the delivery-method layer. |
| **DCRA** | Division of Community and Regional Affairs, within DCCED. Publishes community boundaries and co-maintains the fuel inventory. |
| **DuckDB** | An embedded analytical database, one file (`outputs/fuel_network.duckdb`). The deliverable's four tables live in it. |
| **Dynamic World** | Google / World Resources Institute near-real-time land cover at 10 m, nine classes (water, trees, grass, flooded vegetation, crops, shrub and scrub, built, bare, snow and ice). The summer mode 2022–2024 is the land-cover input and the grid anchor. |
| **FABDEM** | "Forest And Buildings removed" Copernicus digital elevation model (Hawker et al. 2022), 30 m. Slope is derived from it. |
| **GEE** | Google Earth Engine, a cloud platform for geospatial computation. Four of the five friction inputs are exported from it; the finished stack is mirrored there as assets. |
| **GeoPackage (`.gpkg`)** | An open single-file geospatial container; the network build's intermediate format. |
| **GRIP4** | Global Roads Inventory Project, version 4. Used for the Canadian border roads until 2026-09-15; retired. |
| **Historical Sea Ice Atlas** | Monthly sea-ice concentration around Alaska from 1850 on, by SNAP and AOOS. The 1990–2022 monthly medians gate barge passability. |
| **LULC** | Land use / land cover. In this repository always the Dynamic World class raster. |
| **Natural Earth** | Public-domain basemap vectors. Figures only. |
| **NHD** | National Hydrography Dataset (USGS): rivers as lines (`NHDFlowline`) and wide channels and lakes as polygons (`NHDArea`). Defines where river ice can exist. |
| **NWN** | National Waterway Network (USACE / BTS): the lines of navigable waterways. The barge network and the waterway corridor mask come from it. |
| **Pastick et al. 2015** | USGS map of the probability of near-surface permafrost in Alaska. The permafrost input. |
| **R oracle** | The small R program (`source_scripts/mmnet/r_oracle/`, using `sf` and `sfnetworks`) that the network build calls for one job, noding (see below). "Oracle" because Python hands it the lines and takes back the answer. |
| **SIRA** | The third ice-road source, an ArcGIS Online item (link in `DATA.md` §1.2); its expansion is not recorded in this repository. |
| **SNAP** | Scenarios Network for Alaska and Arctic Planning, at UAF. Hosts the Historical Sea Ice Atlas. |
| **TIGER/Line** | The US Census Bureau's boundary files: places, county subdivisions, boroughs and census areas, states. |
| **USACE** | US Army Corps of Engineers. Publishes the National Waterway Network. |
| **USGS** | US Geological Survey. Publishes NHD and the permafrost map. |

## Alaskan geography

| Term | Meaning |
|---|---|
| **Alaska Albers, EPSG:3338** | The map projection every layer is in (NAD83 / Alaska Albers, units metres). It keeps the whole state, Aleutians included, on one continuous plane with no antimeridian split. |
| **Barge** | Fuel delivery by sea or river barge, only in the open-water season. The main delivery mode for coastal and river communities. |
| **Borough / census area** | Alaska's county equivalents. Much of the state is an "unorganized borough" that the Census splits into census areas. |
| **Bulk fuel** | Diesel and gasoline delivered in quantity and stored in a community's tank farm, usually once or twice a year. |
| **Community** | The named place a facility serves and the label on an inventory record. The QC never changes a label; it only records where the point physically sits. |
| **Delivery method** | DCRA's per-community record of how fuel arrives: barge, plane, road, or an ice road. Used for the ice-road community list and as a fallback in the build. |
| **Facility** | One bulk-fuel storage site in the inventory (a tank farm, a power plant's tanks, a school's tanks). Several facilities make one hub. |
| **Ice road** | A winter road built on frozen tundra, lakes and rivers, open roughly January to March. The North Slope oil-field ice roads are the seasonal **IceRoad** mode. |
| **North Slope** | The region north of the Brooks Range. Its communities are reachable only by sea in summer and by ice road in winter, which is why the build's connectivity proof is named after it. |
| **Permafrost** | Ground frozen year-round. Building and maintaining anything on it costs more, which is the permafrost friction. |
| **Remote site** | A facility far from any community: a mine, a repeater, a lodge. The QC keeps it and the hub builder gives it its own hub so it never drags a town's centroid. |
| **Utqiaġvik** | The northernmost town in the United States, formerly Barrow. The connectivity proof checks that its road and ice-road nodes are reachable. |

## The pipeline's own words

| Term | Meaning |
|---|---|
| **Act / step / stage / workflow** | Four words for the same thing in different documents: the five numbered folders under `workflows/`. Workflow 00 is the inventory QC; workflows 01–04 are acts (a)–(d) in the README. "Stage" is also used for the numbered scripts inside a workflow. |
| **Canonical grid, grid anchor** | The one raster grid every friction input must sit on: EPSG:3338, 150 m, 28,000 × 16,567 pixels, defined by the land-cover raster's transform and shape. |
| **Connector, transfer** | Synthetic edges the build adds. A *connector* welds two pieces of the same mode (`RoadConnector`); a *transfer* joins two modes and carries a dollar fee (`BargeRoadTransfer`). |
| **Corridor mask** | A 150 m raster of the waterway lines buffered 75 m. Without it, rivers narrower than a pixel disappear from the barge surface. |
| **Corrections, aliases, ledger** | The owner's recorded decisions about the facility inventory: value corrections with evidence, alternative community spellings, and the append-only table that gives every facility a permanent id. |
| **edge_id** | The row number of an edge in the exported shapefile. Every DuckDB table is keyed by it, which is why the exported zips must stay byte-identical. |
| **Edge class, mode** | Each edge belongs to one mode (Road, IceRoad, Barge, Plane) or is a connector or transfer; `edge_class` names which. |
| **Friction** | A unitless multiplier of how hard a pixel is to cross for a mode, baseline 1.0; `NoData` means impassable. Environmental only: no dollars. |
| **Friction stack** | The fourteen rasters workflow 01 writes: `overland.tif`, `road_base.tif` and `barge_01..12.tif`, read as 24 (mode, month) surfaces. |
| **Gate, exit code 3** | A run script's check for a documented input. When the input is absent the script prints what is missing and where `DATA.md` explains it, and exits 3: a skip, not a failure. |
| **Giant component** | The largest connected piece of the network. The build must put nearly every node in it. |
| **Handoff, network-of-record** | The frozen, checksummed export in `final_network/` that workflow 02 writes and workflow 03 reads. Re-exporting it creates a new network-of-record and invalidates every edge_id-keyed table. |
| **Harness** | The companion analysis repository that consumes the published facility table and the DuckDB deliverable. It derives nothing from raw data. |
| **Hub** | A community's fuel facilities grouped into one network node and snapped onto the nearest transport edge. 329 in the current network. |
| **mmnet, profile** | The region-agnostic network-building engine (`source_scripts/mmnet/`) and the one YAML file (`profile.yaml`) that holds every Alaska-specific choice. Improve the model by editing the profile, not the engine. |
| **NoData** | A raster's "no value" marker. In the friction stack it means impassable; one NoData sample along an edge makes that edge impassable for the month. |
| **Noding** | Splitting lines wherever they cross or touch so that every junction is a node. Done by the R oracle for road, ice road and air; in Python for the waterway. |
| **OD leg** | One origin–destination flight leg between two airports, drawn as a straight line. |
| **p_ice** | River-ice probability per cell and month, 1 minus the median open-water fraction, clamped to 0–1. |
| **Release** | One download of the AEA/DCRA inventory, kept as a tracked snapshot under `inputs/raw_facility_data/<year>/`. |
| **Snap** | Moving a hub onto the nearest network node or edge, within a distance cap. |
| **Strict NoData rule** | Any NoData sample on an edge in a month makes the edge impassable that month. A design decision, auditable through `nodata_frac`. |
| **Three kinds of file** | Every file is *in the repository*, *download and regenerate*, or *built by the pipeline*; `DATA.md` says which. |
