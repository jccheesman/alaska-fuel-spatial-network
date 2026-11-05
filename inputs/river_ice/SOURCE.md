# River-ice intermediates: the Brown river masks

`river_ice_sources.zip` holds the **derived, hard-to-rebuild intermediates** of the
river-ice chain, so that anyone with ArcGIS Pro can regenerate the twelve monthly
river-ice rasters from this repository plus one small public download. It does
*not* hold raw data: the Brown et al. 2026 reach points are downloaded from their
DOI (below), and the 5 GB USGS hydrography the masks were cut from is needed only
to rebuild the masks themselves.

`python tools/extract_inputs.py` unpacks the zip into `inputs/river_ice_work/`
(gitignored), the working directory the river-ice scripts read. The repo's
blanket `*.zip` ignore is negated for this folder.

## What the river-ice chain needs, and where each piece comes from

| Piece | Where it comes from | Kind |
|---|---|---|
| Reach points, `waterFilledMedians2000_2023.geojson` | Brown et al. 2026, Arctic Data Center, [doi:10.18739/A2SB3X15X](https://doi.org/10.18739/A2SB3X15X) (9.6 MB, CC0). Download it into `inputs/river_ice_work/` under that name. | Download |
| River masks, `brown_river_polygons/` and `brown_river_flowlines/` | **This zip.** Derived from USGS NHD by `build_brown_polygon_mask.py` (description below). | In the repository |
| USGS National Hydrography Dataset for Alaska | USGS National Map, "NHD Alaska, state, shapefile" (~5 GB). **Only** to rebuild the masks. | Download (optional) |
| The twelve `river_ice_probability_MM_150m_EPSG3338.tif` | `river_ice_full_pipeline.py` in ArcGIS Pro, from the two rows above. | Built by the pipeline |

So the regeneration a user does is: unpack this zip, download the reach points,
run the ArcGIS script (`DATA.md` §3.1 Step B). The script takes the median of the
three observation periods per reach and month, rasterises the points at 150 m,
fills wide rivers with the per-polygon median of the points inside each polygon,
fills narrow rivers and gaps by inverse-distance weighting (12 neighbours, 50 km
cap), clamps to 0–1, and aligns the result to the friction grid. The masks decide
*where* a river cell exists and which cells share a polygon median; the points
decide *how much* ice.

## The masks

Both shapefiles are EPSG:3338 (NAD83 / Alaska Albers, metres). Both are cut to the
**thirty rivers Brown et al. observed** (the `BROWN_RIVER_NAMES` list in
`build_brown_polygon_mask.py`: Alsek, Buckland, Chena, Chitina, Colville, Copper,
Innoko, Kenai, Kobuk, Koyukuk, Kuparuk, Kuskokwim and its North and South Forks,
Kvichak, Nenana, Noatak, Nushagak, Porcupine, Sagavanirktok, Salcha, Skwentna,
Stikine, Stony, Susitna, Taku, Tanana, Teedriinjik, Yentna, Yukon).

### `brown_river_polygons/brown_river_polygons.shp` — the wide channels

The USGS NHD `NHDArea` polygons that carry a Brown river. A polygon enters the
mask if it is a `StreamRiver` (ftype 460) or `Lake/Pond` (ftype 364, for in-line
lakes such as Skilak on the Kenai) **and** either lies within 2 km of a reach
point (so we have data for it) **or** within 500 m of a Brown flowline (so braided
or parallel channels the points miss are still covered). Four salt-water polygons
that the union admitted at river mouths (Dry Strait at the Stikine, Cross Sound
at the Porcupine's mislabelled match, the Kenai mouth, the Kuparuk coast) are
removed by a marine clip against the waterway network, so the river-ice fill can
never freeze a marine barge route.

| Field | Meaning |
|---|---|
| `gnis_name` | The Brown river the polygon belongs to (reach-point match first, flowline match as fallback) |
| `ftype` | NHD feature type: 460 StreamRiver, 364 Lake/Pond |
| `areasqkm` | NHD area, km² |

In the pipeline each polygon gets one value per month: the median of the reach
points inside it (`ZonalStatisticsAsTable`, "polygon-median fill").

### `brown_river_flowlines/brown_river_flowlines.shp` — the centre lines

The USGS NHD `NHDFlowline` features whose `gnis_name` is one of the thirty rivers.
One field, `gnis_name`. In the pipeline they are buffered 200 m to form the
narrow-river mask: the union of that buffer and the polygons is the set of cells
that can hold river ice at all; cells in the buffer but outside a polygon are
filled by inverse-distance weighting from the reach points.

## Members of the zip

Fill this table when the zip is (re)built. Keep the members at the top level of
the zip, exactly as they sit in `inputs/river_ice_work/`.

| Member | Features | Size | Built on | Note |
|---|---|---|---|---|
| `brown_river_polygons/brown_river_polygons.{shp,shx,dbf,prj,cpg}` | *(owner to fill)* | | *(date)* | |
| `brown_river_flowlines/brown_river_flowlines.{shp,shx,dbf,prj,cpg}` | *(owner to fill)* | | *(date)* | |

| Field | Value |
|---|---|
| Zip added | *(pending: the zip has not been added yet)* |
| NHD vintage the masks were cut from | *(owner to fill)* |
| Zip sha256 | *(fill when the zip lands; also in `inputs/MANIFEST.md`)* |

## Adding an intermediate, rebuilding the masks

- **Adding a member** (another intermediate of the river-ice chain that is slow
  to rebuild): put it in `inputs/river_ice_work/` where the scripts expect it,
  re-zip the working directory *without* `waterFilledMedians2000_2023.geojson`
  and `NHD_extracted/` (both stay downloads), add a row to the members table
  with what it is and which script reads it, and update the sha256 here and in
  `inputs/MANIFEST.md`. Keep the zip under 50 MB (no Git LFS in this repository).
- **Rebuilding the masks** (only if NHD or the Brown reach set changes): download
  the NHD shapefile bundle into `inputs/river_ice_work/NHD_extracted/Shape/`, run
  `python -m friction_surface.friction_preprocessing.build_brown_polygon_mask`
  (it needs the waterway shapefile from `python tools/extract_inputs.py` for the
  marine clip), then re-zip and update the checksums as above.
