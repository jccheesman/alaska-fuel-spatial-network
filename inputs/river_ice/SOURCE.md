# River-ice sources: the Brown et al. 2026 reach points and the two river masks

`river_ice_sources.zip` is the river-ice working directory, zipped, so that the
ArcGIS step (`river_ice_full_pipeline.py`) can run from a fresh clone without
the 5 GB NHD download. `python tools/extract_inputs.py` unpacks it into
`inputs/river_ice_work/` (gitignored). The repo's blanket `*.zip` ignore is
negated for this folder.

| Member | What it is | Source | Licence |
|---|---|---|---|
| `waterFilledMedians2000_2023.geojson` | ~31,745 reach-point observations for thirty Alaskan rivers: `ReachID`, `month`, `areaPropMedWater` (median open-water fraction, 2000–2023) | Brown et al. 2026, Arctic Data Center, [doi:10.18739/A2SB3X15X](https://doi.org/10.18739/A2SB3X15X) | CC0 |
| `brown_river_polygons/brown_river_polygons.shp` | NHDArea polygons (StreamRiver + Lake/Pond) within 2 km of a reach point or 500 m of a Brown flowline, salt-water polygons removed | Derived from USGS NHD Alaska by `build_brown_polygon_mask.py` | Public domain (USGS) |
| `brown_river_flowlines/brown_river_flowlines.shp` | NHDFlowline features whose `gnis_name` is one of the thirty Brown rivers | Derived from USGS NHD Alaska by `build_brown_polygon_mask.py` | Public domain (USGS) |

| Field | Value |
|---|---|
| Added | *(pending: the zip has not been added yet)* |
| Retrieved (Brown et al.) | *(owner to fill)* |
| NHD vintage | *(owner to fill; USGS National Map, "NHD Alaska, state, shapefile")* |
| Zip sha256 | *(fill when the zip lands; also in `inputs/MANIFEST.md`)* |

Rebuilding the masks (only if NHD or the Brown reach set changes): download the
NHD shapefile bundle into `inputs/river_ice_work/NHD_extracted/Shape/`, run
`python -m friction_surface.friction_preprocessing.build_brown_polygon_mask`,
then re-zip the working directory without `NHD_extracted/` and update the sha256
here and in `inputs/MANIFEST.md`.
