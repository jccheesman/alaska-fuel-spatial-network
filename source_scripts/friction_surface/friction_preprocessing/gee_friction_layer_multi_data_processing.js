// ============================================================================
// FRICTION-SURFACE INPUT RASTERS — Google Earth Engine export script
//
// Produces the four raster inputs of the friction build (workflow 01), all on
// ONE grid: EPSG:3338 (NAD83 / Alaska Albers), 150 m, 28,000 x 16,567 pixels,
// origin (-2,130,000, 2,595,450). The friction pipeline reads the files under
// EXACTLY the names this script gives them (the "one name" rule, defined once
// in source_scripts/friction_surface/friction_paths.py): never rename a file.
//
//   Drive file                                                     pipeline role
//   FABDEM_slope_150m_EPSG3338.tif                                 slope (degrees)
//   dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif     land cover (0..8) — THE GRID ANCHOR
//   permafrost_probability_150m_EPSG3338.tif                       permafrost probability (0..100)
//   sea_ice_median_{MM}_{Mon}_150m_EPSG3338.tif  (x12)             sea-ice concentration (0..100)
//
// River ice is NOT made here: it comes from the ArcGIS pipeline
// (river_ice_full_pipeline.py). The network's transport layers are NOT needed
// here either; a separate script, gee_network_layers_preview.js, overlays them
// on these rasters for a visual check.
//
// HOW TO USE
//   1. Upload two datasets as assets in YOUR Earth Engine project and put their
//      ids in the CONFIG block below:
//        - Pastick et al. 2015 near-surface permafrost probability (GeoTIFF, USGS)
//        - the Historical Sea Ice Atlas monthly rasters (UAF SNAP / AOOS) as an
//          ImageCollection; band 1 = concentration, band 2 = source flag
//          (128 = land)
//      FABDEM and Dynamic World are public catalog datasets; nothing to upload.
//   2. Paste this file into the Code Editor and Run. Open the Tasks tab and
//      start every "Export_*" task (the two-stage land-cover path is explained
//      at the bottom; start "Bake_DW_summer_mode_10m" as well).
//   3. When the tasks finish, download the GeoTIFFs from the Drive folder
//      EXPORT_FOLDER into the repository:
//        inputs/friction_rasters/<name>.tif                  (slope, land cover, permafrost)
//        inputs/friction_rasters/sea_ice/<name>.tif          (the twelve monthly medians)
//      If Drive delivers a raster as several tiles (…-0000000000-0000000000.tif),
//      merge them into one file of the plain name (e.g. `rio merge`); the tile
//      suffix is the only thing that may be removed from a name.
//   4. Then, from the repo root (DATA.md section 3.1):
//        python -m friction_surface.friction_preprocessing.pad_sea_ice_to_grid
//        python -m friction_surface.friction_preprocessing.align_permafrost
//      (the sea-ice exports come back cropped to the atlas footprint and the
//      permafrost export to its own area; both are fixed in place).
// ============================================================================

// ----------------------------------------------------------------------------
// CONFIG — the only lines a new user edits
// ----------------------------------------------------------------------------
var ASSET_ROOT         = 'projects/gee-friction-layer-processing/assets';  // <- your project
var PERMAFROST_ASSET   = ASSET_ROOT + '/AK_ProbofPF_1m_clipped';           // Pastick et al. 2015, uploaded
var SEA_ICE_ATLAS      = ASSET_ROOT + '/sea_ice_atlas_monthly';            // Historical Sea Ice Atlas, uploaded
var LULC_BAKE_ASSET    = ASSET_ROOT + '/DW_summer_mode_10m';               // written by this script (stage A)
var EXPORT_FOLDER      = 'AK_Stack_150m';                                   // Drive folder the tasks write to

var SEA_ICE_START      = '1990-01-01';   // climatology window for the monthly medians
var SEA_ICE_END        = '2023-01-01';
var DW_START           = '2022-06-01';   // Dynamic World scenes used for the summer mode
var DW_END             = '2024-10-01';
var DW_MONTHS          = [6, 9];         // June..September

// ----------------------------------------------------------------------------
// Study area: Alaska (TIGER states, FIPS 02)
// ----------------------------------------------------------------------------
var alaska = ee.FeatureCollection('TIGER/2018/States')
               .filter(ee.Filter.eq('STATEFP', '02'));
Map.addLayer(alaska, {color: 'red'}, 'Alaska boundary');
Map.setCenter(-152.0, 64.0, 4);

// ----------------------------------------------------------------------------
// Dataset 1: FABDEM elevation -> slope (degrees)
// ----------------------------------------------------------------------------
var fabdem = ee.ImageCollection('projects/sat-io/open-datasets/FABDEM')
                .mosaic()
                .setDefaultProjection('EPSG:4326', null, 30);
var elevation = fabdem.clip(alaska);
var elevVis = {min: 0, max: 3000,
               palette: ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']};
Map.addLayer(elevation, elevVis, 'FABDEM elevation', true, 0.8);

var slopeImg = ee.Terrain.slope(elevation);
var slopeVis = {min: 0, max: 45,
                palette: ['ffffff', 'ffeda0', 'feb24c', 'fc4e2a', 'b10026']};
Map.addLayer(slopeImg, slopeVis, 'FABDEM slope (degrees)', false, 0.7);

// ----------------------------------------------------------------------------
// Dataset 2: probability of near-surface permafrost (Pastick et al. 2015)
// ----------------------------------------------------------------------------
var permafrostRaw  = ee.Image(PERMAFROST_ASSET);
var permafrostProb = permafrostRaw.updateMask(permafrostRaw.lte(100));
var permafrostVis = {min: 0, max: 100,
                     palette: ['ffffcc', 'a1dab4', '41b6c4', '2c7fb8', '253494']};
Map.addLayer(permafrostProb, permafrostVis,
             'Probability of near-surface permafrost (%)', true, 0.75);

// ----------------------------------------------------------------------------
// Dataset 3: Historical Sea Ice Atlas — monthly climatological medians
//   Land masked via band 2 source flag (128 = land)
// ----------------------------------------------------------------------------
var seaIceRaw = ee.ImageCollection(SEA_ICE_ATLAS);
var seaIceMasked = seaIceRaw
  .filterDate(SEA_ICE_START, SEA_ICE_END)
  .map(function(img) {
    var landMask = img.select(1).neq(128);   // 1=ocean, 0=land
    return img.select(0).updateMask(landMask);
  });

// monthly climatological median for a given month-of-year
var monthlyMedian = function(m) {
  return seaIceMasked
    .filter(ee.Filter.calendarRange(m, m, 'month'))
    .median()
    .rename('sic_median')
    .set('month', m);
};

var sicPalette = ['#0a1172', '#2e5cb8', '#87CEEB', '#e0f3f8', '#ffffff'];
var sicVis     = {min: 0, max: 100, palette: sicPalette};
var maskOpenWater = function(img) { return img.updateMask(img.gt(15)); };

var monthNames = ['Jan','Feb','Mar','Apr','May','Jun',
                  'Jul','Aug','Sep','Oct','Nov','Dec'];
monthNames.forEach(function(name, i) {
  var monthNum = i + 1;
  var shown    = (monthNum === 3);  // March (winter peak) shown by default
  Map.addLayer(maskOpenWater(monthlyMedian(monthNum)), sicVis,
               'Sea ice — ' + name + ' median', shown, 0.85);
});

// ----------------------------------------------------------------------------
// Dataset 4: Dynamic World V1 — land cover, summer mode composite
// ----------------------------------------------------------------------------
var dwClasses = [
  {value: 0, name: 'Water',         color: '419BDF'},
  {value: 1, name: 'Trees',         color: '397D49'},
  {value: 2, name: 'Grass',         color: '88B053'},
  {value: 3, name: 'Flooded veg.',  color: '7A87C6'},
  {value: 4, name: 'Crops',         color: 'E49635'},
  {value: 5, name: 'Shrub & scrub', color: 'DFC35A'},
  {value: 6, name: 'Built',         color: 'C4281B'},
  {value: 7, name: 'Bare',          color: 'A59B8F'},
  {value: 8, name: 'Snow & ice',    color: 'B39FE1'}
];
var dwPalette = dwClasses.map(function(c) { return c.color; });
var dwVis = {min: 0, max: 8, palette: dwPalette};

var dwColl = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
               .filterBounds(alaska)
               .filterDate(DW_START, DW_END)
               .filter(ee.Filter.calendarRange(DW_MONTHS[0], DW_MONTHS[1], 'month'))
               .select('label');
// No .clip(alaska): the TIGER Alaska geometry wraps the antimeridian, and the
// export region already bounds the output.
var dwModeRaw = dwColl.mode();
Map.addLayer(dwModeRaw, dwVis, 'Dynamic World land cover (summer mode)', true, 0.85);

// Give the mode composite a real 10 m projection so the export can resample it
// onto the 150 m grid. FAST PATH: we deliberately do NOT reduceResolution() to
// an exact 15x15 majority — that evaluates mode() ~225x per output cell and is
// what made the full-AK export run for hours. The export nearest-samples the
// 10 m mode to 150 m; nearest (not bilinear) keeps class codes intact.
var lulc10m = dwModeRaw.setDefaultProjection('EPSG:3338', null, 10);

// ----------------------------------------------------------------------------
// Legends (map preview only)
// ----------------------------------------------------------------------------
var makeLegendRow = function(color, name) {
  var colorBox = ui.Label('', {backgroundColor: '#' + color, padding: '8px',
                               margin: '0 6px 4px 0'});
  var description = ui.Label(name, {margin: '0 0 4px 0', fontSize: '11px'});
  return ui.Panel({widgets: [colorBox, description],
                   layout: ui.Panel.Layout.Flow('horizontal')});
};

var makeContinuousLegend = function(title, visParams, ticks, footnote) {
  var panel = ui.Panel({style: {padding: '8px 12px',
                                backgroundColor: 'rgba(255, 255, 255, 0.9)'}});
  panel.add(ui.Label(title, {fontWeight: 'bold', fontSize: '12px', margin: '0 0 6px 0'}));
  var gradient = ee.Image.pixelLonLat().select('longitude')
    .multiply((visParams.max - visParams.min) / 100.0)
    .add(visParams.min);
  panel.add(ui.Thumbnail({
    image: gradient.visualize(visParams),
    params: {bbox: [0, 0, 100, 8], dimensions: '200x12'},
    style: {stretch: 'horizontal', margin: '0', maxHeight: '14px'}
  }));
  var tickWidgets = ticks.map(function(t, i) {
    var align = (i === 0) ? 'left' : (i === ticks.length - 1) ? 'right' : 'center';
    return ui.Label(String(t), {margin: '2px 0', fontSize: '11px',
                                textAlign: align, stretch: 'horizontal'});
  });
  panel.add(ui.Panel({widgets: tickWidgets, layout: ui.Panel.Layout.flow('horizontal'),
                      style: {width: '200px', margin: '0', padding: '0'}}));
  if (footnote) {
    panel.add(ui.Label(footnote, {fontSize: '11px', margin: '6px 0 0 0', color: '#555'}));
  }
  return panel;
};

var permafrostLegend = makeContinuousLegend('Permafrost probability (%)', permafrostVis,
                                            [0, 25, 50, 75, 100]);
permafrostLegend.style().set('position', 'bottom-right');
Map.add(permafrostLegend);

var sicLegend = makeContinuousLegend('Sea ice concentration (%)', sicVis,
                                     [0, 25, 50, 75, 100], 'Land: masked (transparent)');
sicLegend.style().set('position', 'bottom-right');
Map.add(sicLegend);

var slopeLegend = makeContinuousLegend('Slope (degrees)', slopeVis, [0, 15, 30, 45]);
slopeLegend.style().set('position', 'bottom-right');
Map.add(slopeLegend);

var dwLegend = ui.Panel({style: {position: 'bottom-left', padding: '8px'}});
dwLegend.add(ui.Label('Dynamic World land cover',
                      {fontWeight: 'bold', fontSize: '12px', margin: '0 0 4px 0'}));
dwClasses.forEach(function(c) { dwLegend.add(makeLegendRow(c.color, c.name)); });
Map.add(dwLegend);

// ============================================================================
// EXPORTS — every raster on the same 150 m EPSG:3338 grid
//   Continuous rasters: bilinear resampling. Categorical (land cover): nearest.
// ============================================================================
var EXPORT_CRS   = 'EPSG:3338';   // NAD83 / Alaska Albers
var EXPORT_SCALE = 150;           // metres

// Full-Alaska footprint in EPSG:3338 METRES (not lon/lat) so it spans the whole
// Aleutian chain continuously — Alaska Albers is conic, so the western
// Aleutians land at large-negative easting with no antimeridian split. Corners
// are multiples of 150 m, anchored to EXPORT_TRANSFORM, so every raster shares
// grid lines.  [xmin, ymin, xmax, ymax] -> 28,000 x 16,567 px
var EXPORT_REGION = ee.Geometry.Rectangle([-2130000, 110400, 2070000, 2595450],
                                          'EPSG:3338', false);
// [scaleX, shearX, translateX, shearY, scaleY, translateY], origin at (0, 0)
var EXPORT_TRANSFORM = [EXPORT_SCALE, 0, 0, 0, -EXPORT_SCALE, 0];

// Export helper. The Drive file is <name>_150m_EPSG3338.tif — the exact name the
// pipeline reads (friction_paths.RASTER_NAMES / sea_ice_name).
var exportRaster = function(image, name, resampleMethod) {
  var prepared;
  if (resampleMethod === 'mode') {
    prepared = image
      .reduceResolution({reducer: ee.Reducer.mode(), maxPixels: 1024})
      .reproject({crs: EXPORT_CRS, crsTransform: EXPORT_TRANSFORM});
  } else {
    prepared = image.resample('bilinear');
  }
  Export.image.toDrive({
    image:          prepared,
    description:    'Export_' + name,
    folder:         EXPORT_FOLDER,
    fileNamePrefix: name + '_150m_EPSG3338',
    region:         EXPORT_REGION,
    crs:            EXPORT_CRS,
    crsTransform:   EXPORT_TRANSFORM,
    maxPixels:      1e13
  });
};

// ---- slope (continuous) -> FABDEM_slope_150m_EPSG3338.tif
exportRaster(slopeImg, 'FABDEM_slope', 'bilinear');

// ---- permafrost (continuous) -> permafrost_probability_150m_EPSG3338.tif
exportRaster(permafrostProb, 'permafrost_probability', 'bilinear');

// ---- sea ice, 12 monthly medians -> sea_ice_median_MM_Mon_150m_EPSG3338.tif
monthNames.forEach(function(name, i) {
  var monthNum = i + 1;
  var mm       = (monthNum < 10 ? '0' : '') + monthNum;
  exportRaster(monthlyMedian(monthNum), 'sea_ice_median_' + mm + '_' + name, 'bilinear');
});

// ---- land cover (categorical) -> dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif
// FAST single-task export: nearest-samples the 10 m mode onto the exact 150 m
// grid via crsTransform. Not via exportRaster: its 'mode' branch does the slow
// exact reduceResolution and its 'bilinear' branch would average class codes.
Export.image.toDrive({
  image:          lulc10m,
  description:    'Export_dynamic_world_LULC_2022_2024_summer_mode_150m',
  folder:         EXPORT_FOLDER,
  fileNamePrefix: 'dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338',
  region:         EXPORT_REGION,
  crs:            EXPORT_CRS,
  crsTransform:   EXPORT_TRANSFORM,
  maxPixels:      1e13
});

// ---- land cover, ROBUST TWO-STAGE path (asset bake, then trivial resample) ----
// The single-task export above computes the per-scene mode() AND the 10 m ->
// 150 m aggregation in one shot over 464M cells — near GEE's batch ceiling, so
// it can run for hours or time out. Splitting it bounds each task:
//   Stage A: bake the 10 m summer mode to an ASSET (robust batch, reusable).
//   Stage B: resample that static asset to the 150 m grid (fast) via exportRaster.
// Hedge: run Stage A in PARALLEL with the single-task export; whichever lands
// first wins. Either way the Drive file has the same name.
//
// Stage A: start the task 'Bake_DW_summer_mode_10m'. (If re-baking, delete the
// existing asset first — toAsset won't overwrite.)
Export.image.toAsset({
  image:        lulc10m,
  description:  'Bake_DW_summer_mode_10m',
  assetId:      LULC_BAKE_ASSET,
  region:       EXPORT_REGION,
  crs:          EXPORT_CRS,
  crsTransform: [10, 0, 0, 0, -10, 0],         // 10 m lattice nested in the 150 m grid
  maxPixels:    1e13
});
// Stage B: uncomment and run ONLY after 'Bake_DW_summer_mode_10m' finishes.
// var lulcAsset = ee.Image(LULC_BAKE_ASSET);
// exportRaster(lulcAsset, 'dynamic_world_LULC_2022_2024_summer_mode_150m', 'mode');

print('Export tasks queued — open the Tasks tab and click Run on each.');
print('Drive folder: ' + EXPORT_FOLDER + '. Download into inputs/friction_rasters/ ' +
      '(sea ice into inputs/friction_rasters/sea_ice/) WITHOUT renaming, then run ' +
      'pad_sea_ice_to_grid and align_permafrost (DATA.md section 3.1).');
