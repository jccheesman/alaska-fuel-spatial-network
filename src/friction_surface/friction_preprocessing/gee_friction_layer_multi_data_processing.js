
// ============================================================
// Multi-dataset Alaska visualization (merged & cleaned)
//   Layers: FABDEM elevation + slope, permafrost,
//           monthly sea ice climatologies (land-masked medians),
//           Dynamic World LULC, roads, waterways, ports
//   Includes: export of Alaska roads to Drive
// ============================================================


// Load the TIGER states collection and filter for Alaska (FIPS code '02')
var alaska = ee.FeatureCollection('TIGER/2018/States')
               .filter(ee.Filter.eq('STATEFP', '02'));

// Add the boundary to the map with a red outline and transparent fill
Map.addLayer(alaska, {color: 'red'}, 'Alaska Boundary');

// Center the map view over Alaska (longitude, latitude, zoom level)
Map.setCenter(-152.0, 64.0, 4);

// ------------------------------------------------------------
// User-uploaded vector assets
// ------------------------------------------------------------
var akRoads      = ee.FeatureCollection('projects/gee-friction-layer-processing/assets/AKDOT_roads');
var nwnWaterways = ee.FeatureCollection('projects/gee-friction-layer-processing/assets/NWN_Waterway_Network_Lines');

// ------------------------------------------------------------
// Dataset 1: GRIP4 Global Roads (filtered to Alaska)
// ------------------------------------------------------------
var grip4 = ee.FeatureCollection('projects/sat-io/open-datasets/GRIP4/North-America')
              .filterBounds(alaska);


// ------------------------------------------------------------
// Dataset 2: FABDEM elevation + derived slope
// ------------------------------------------------------------
var fabdem = ee.ImageCollection('projects/sat-io/open-datasets/FABDEM')
                .mosaic()
                .setDefaultProjection('EPSG:4326', null, 30);

var elevation = fabdem.clip(alaska);
var elevVis = {
  min: 0, max: 3000,
  palette: ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']
};
Map.addLayer(elevation, elevVis, 'FABDEM Elevation', true, 0.8);

var slopeImg = ee.Terrain.slope(elevation);
var slopeVis = {
  min: 0, max: 45,
  palette: ['ffffff', 'ffeda0', 'feb24c', 'fc4e2a', 'b10026']
};
Map.addLayer(slopeImg, slopeVis, 'FABDEM Slope (degrees)', false, 0.7);

// ------------------------------------------------------------
// Dataset 3: Probability of Near-Surface Permafrost (Pastick 2015)
// ------------------------------------------------------------
var permafrostRaw  = ee.Image('projects/gee-friction-layer-processing/assets/AK_ProbofPF_1m_clipped');
var permafrostProb = permafrostRaw.updateMask(permafrostRaw.lte(100));
var permafrostVis = {
  min: 0, max: 100,
  palette: ['ffffcc', 'a1dab4', '41b6c4', '2c7fb8', '253494']
};
Map.addLayer(permafrostProb, permafrostVis,
             'Probability of Near-Surface Permafrost (%)', true, 0.75);

// ============================================================
// Dataset 4: SNAP Historical Sea Ice Atlas
//   Monthly climatological MEDIANS, 1990–2022
//   Land masked via band 2 source flag (128 = land)
// ============================================================
var seaIceRaw = ee.ImageCollection(
  'projects/gee-friction-layer-processing/assets/sea_ice_atlas_monthly'
);

// Filter 1990–2022, mask land using band 2 flag, keep concentration band
var seaIceMasked = seaIceRaw
  .filterDate('1990-01-01', '2023-01-01')
  .map(function(img) {
    var landMask = img.select(1).neq(128);   // 1=ocean, 0=land
    return img.select(0).updateMask(landMask);
  });

// Helper: monthly climatological median for a given month-of-year
var monthlyMedian = function(m) {
  return seaIceMasked
    .filter(ee.Filter.calendarRange(m, m, 'month'))
    .median()
    .rename('sic_median')
    .set('month', m);
};

// Visualization (Sea Ice Atlas-style blue → white ramp)
var sicPalette = ['#0a1172', '#2e5cb8', '#87CEEB', '#e0f3f8', '#ffffff'];
var sicVis     = {min: 0, max: 100, palette: sicPalette};

// Optional: mask out open-water-ish pixels (<15%) so the basemap shows through
var maskOpenWater = function(img) { return img.updateMask(img.gt(15)); };

// Per-month layers. March (winter peak) shown by default; rest off.
var monthNames = ['Jan','Feb','Mar','Apr','May','Jun',
                  'Jul','Aug','Sep','Oct','Nov','Dec'];
monthNames.forEach(function(name, i) {
  var monthNum = i + 1;
  var shown    = (monthNum === 3);  // default-on: March
  Map.addLayer(maskOpenWater(monthlyMedian(monthNum)), sicVis,
               'Sea Ice — ' + name + ' median (1990–2022)', shown, 0.85);
});


// ------------------------------------------------------------
// Dataset 5: Dynamic World V1 — LULC (summer mode composite)
// ------------------------------------------------------------
var dwClasses = [
  {value: 0, name: 'Water',        color: '419BDF'},
  {value: 1, name: 'Trees',        color: '397D49'},
  {value: 2, name: 'Grass',        color: '88B053'},
  {value: 3, name: 'Flooded veg.', color: '7A87C6'},
  {value: 4, name: 'Crops',        color: 'E49635'},
  {value: 5, name: 'Shrub & scrub', color: 'DFC35A'},
  {value: 6, name: 'Built',        color: 'C4281B'},
  {value: 7, name: 'Bare',         color: 'A59B8F'},
  {value: 8, name: 'Snow & ice',   color: 'B39FE1'}
];
var dwPalette = dwClasses.map(function(c) { return c.color; });
var dwVis = {min: 0, max: 8, palette: dwPalette};

// Load collection and create standard composite
var dwColl = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
               .filterBounds(alaska)
               .filterDate('2022-06-01', '2024-10-01')
               .filter(ee.Filter.calendarRange(6, 9, 'month'))
               .select('label');
               
// No .clip(alaska): the TIGER Alaska geometry wraps the antimeridian, and the export
// region already bounds the output — clipping only adds antimeridian-geometry overhead.
var dwModeRaw = dwColl.mode();

// Map layers (Using standard GEE scaling for quick dynamic browsing)
Map.addLayer(dwModeRaw, dwVis, 'Dynamic World LULC (Interactive Map View)', true, 0.85);

// Give the mode composite a real 10 m projection so the export can resample it onto the
// 150 m grid. FAST PATH: we deliberately do NOT reduceResolution() to an exact 15x15
// majority — that evaluates mode() ~225x per output cell and is what made the full-AK
// export run for hours. Instead the export nearest-samples the 10 m mode to 150 m
// (~225x less work): each 150 m class is the land-cover mode at the cell's representative
// 10 m pixel, not the exact spatial majority. Nearest (not bilinear) keeps class codes intact.
var lulc10m = dwModeRaw.setDefaultProjection('EPSG:3338', null, 10);

// ------------------------------------------------------------
// Dataset 6: Ports & Harbors
// ------------------------------------------------------------
var ports = ee.FeatureCollection('projects/gee-friction-layer-processing/assets/AK_Ports_and_Harbors');


// ------------------------------------------------------------
// Dataset 7:  Ice Roads
// ------------------------------------------------------------
var ice_roads = ee.FeatureCollection('projects/gee-friction-layer-processing/assets/ice_roads_merged_and_processed');

// ------------------------------------------------------------
// Vector overlays — added LAST so they render on top of rasters
// ------------------------------------------------------------
var grip4Style        = grip4.style({color: 'FF4500', width: 1});
var akRoadsStyle      = akRoads.style({color: '252525', width: 1.5});
var nwnWaterwaysStyle = nwnWaterways.style({color: '1F78B4', width: 1.5});
var portsStyle        = ports.style({
                          color: 'D95F02',
                          pointSize: 6,
                          pointShape: 'circle',
                          fillColor: 'FDAE6B80'
                        });
var iceRoadStyle = ice_roads.style({color: 'FF00FF', width: 1});

Map.addLayer(grip4Style,        {}, 'GRIP4 Roads (Alaska)', false);
Map.addLayer(akRoadsStyle,      {}, 'AK DOT Roads');
Map.addLayer(nwnWaterwaysStyle, {}, 'NWN Waterways');
Map.addLayer(portsStyle,        {}, 'AK Ports & Harbors');
Map.addLayer(iceRoadStyle,        {}, 'Ice Roads');

// ============================================================
// Legends
// ============================================================

var makeLegendRow = function(color, name) {
  var colorBox = ui.Label('', {
    backgroundColor: '#' + color,
    padding: '8px',
    margin: '0 6px 4px 0'
  });
  var description = ui.Label(name, {margin: '0 0 4px 0', fontSize: '11px'});
  return ui.Panel({
    widgets: [colorBox, description],
    layout: ui.Panel.Layout.Flow('horizontal')
  });
};

// Helper: build a continuous-ramp legend panel
var makeContinuousLegend = function(title, visParams, ticks, footnote) {
  var panel = ui.Panel({
    style: {padding: '8px 12px', backgroundColor: 'rgba(255, 255, 255, 0.9)'}
  });
  panel.add(ui.Label(title,
    {fontWeight: 'bold', fontSize: '12px', margin: '0 0 6px 0'}));

  // 0–100 lon ramp scaled into the visParams range
  var gradient = ee.Image.pixelLonLat().select('longitude')
    .multiply((visParams.max - visParams.min) / 100.0)
    .add(visParams.min);
  panel.add(ui.Thumbnail({
    image: gradient.visualize(visParams),
    params: {bbox: [0, 0, 100, 8], dimensions: '200x12'},
    style: {stretch: 'horizontal', margin: '0', maxHeight: '14px'}
  }));

  // Tick labels — distribute evenly across the bar width
  var tickWidgets = ticks.map(function(t, i) {
    var align = (i === 0) ? 'left'
              : (i === ticks.length - 1) ? 'right'
              : 'center';
    return ui.Label(String(t), {
      margin: '2px 0',
      fontSize: '11px',
      textAlign: align,
      stretch: 'horizontal'    // each tick gets equal share of the row
    });
  });
  panel.add(ui.Panel({
    widgets: tickWidgets,
    layout: ui.Panel.Layout.flow('horizontal'),
    style: {width: '200px', margin: '0', padding: '0'}
  }));

  if (footnote) {
    panel.add(ui.Label(footnote,
      {fontSize: '11px', margin: '6px 0 0 0', color: '#555'}));
  }
  return panel;
};

// ------------------------------------------------------------
// Legend 1 — Permafrost probability
// ------------------------------------------------------------
var permafrostLegend = makeContinuousLegend(
  'Permafrost Probability (%)',
  permafrostVis,
  [0, 25, 50, 75, 100]
);
permafrostLegend.style().set('position', 'bottom-right');
Map.add(permafrostLegend);

// ------------------------------------------------------------
// Legend 2 — Sea Ice Concentration
// ------------------------------------------------------------
var sicLegend = makeContinuousLegend(
  'Sea Ice Concentration (%)',
  sicVis,
  [0, 25, 50, 75, 100],
  'Land: masked (transparent)'
);
sicLegend.style().set('position', 'bottom-right');
Map.add(sicLegend);

// ------------------------------------------------------------
// Legend 3 — Slope
// ------------------------------------------------------------
var slopeLegend = makeContinuousLegend(
  'Slope (degrees)',
  slopeVis,
  [0, 15, 30, 45]
);
slopeLegend.style().set('position', 'bottom-right');
Map.add(slopeLegend);

// ------------------------------------------------------------
// Legend 4 — Dynamic World LULC
// ------------------------------------------------------------
var dwLegend = ui.Panel({style: {position: 'bottom-left', padding: '8px'}});
dwLegend.add(ui.Label('Dynamic World LULC',
                      {fontWeight: 'bold', fontSize: '12px', margin: '0 0 4px 0'}));
dwClasses.forEach(function(c) {
  dwLegend.add(makeLegendRow(c.color, c.name));
});
Map.add(dwLegend);


// ============================================================
// EXPORTS — all rasters aligned to a common 150 m grid in EPSG:3338
//   - Same CRS, same crsTransform, same region for every raster
//   - Continuous rasters: bilinear resampling
//   - Categorical raster (DW): mode resampling
//   - Vectors exported as SHP (region-filtered already)
// ============================================================

// ---- Common export grid ----
var EXPORT_CRS    = 'EPSG:3338';   // NAD83 / Alaska Albers
var EXPORT_SCALE  = 150;            // metres
var EXPORT_FOLDER = 'AK_Stack_150m';

// Full-Alaska AOI defined in EPSG:3338 METRES (not lon/lat) so it spans the entire
// Aleutian chain continuously — Alaska Albers is conic, so the western Aleutians land at
// large-negative easting with no antimeridian split. Corners are multiples of 150 m and
// anchored to the same grid as EXPORT_TRANSFORM, so the grid lines match the prior stack;
// this only widens the footprint E/W to cover the whole transport network.
//   [xmin, ymin, xmax, ymax] = [-2130000, 110400, 2070000, 2595450]  ->  28,000 x 16,567 px
var EXPORT_REGION = ee.Geometry.Rectangle([-2130000, 110400, 2070000, 2595450], 'EPSG:3338', false);

// Anchor crsTransform to a clean origin so all rasters share grid lines.
// Format: [scaleX, shearX, translateX, shearY, scaleY, translateY]
// We pick translateX/Y at 0 in EPSG:3338 metres — arbitrary but consistent.
var EXPORT_TRANSFORM = [EXPORT_SCALE, 0, 0, 0, -EXPORT_SCALE, 0];

// ---- Raster export helper ----
// resampleMethod: 'bilinear' (continuous) or 'mode' (categorical)
var exportRaster = function(image, name, resampleMethod) {
  var prepared;
  if (resampleMethod === 'mode') {
    // For categorical data: aggregate native pixels into the 150 m cell
    // using majority class.
    prepared = image
      .reduceResolution({reducer: ee.Reducer.mode(), maxPixels: 1024})
      .reproject({crs: EXPORT_CRS, crsTransform: EXPORT_TRANSFORM});
  } else {
    prepared = image.resample('bilinear');
  }

  Export.image.toDrive({
    image:         prepared,
    description:   'Export_' + name,
    folder:        EXPORT_FOLDER,
    fileNamePrefix: name + '_150m_EPSG3338',
    region:        EXPORT_REGION,
    crs:           EXPORT_CRS,
    crsTransform:  EXPORT_TRANSFORM,
    maxPixels:     1e13
  });
};

// ---- Vector export helper ----
var exportVector = function(fc, name) {
  Export.table.toDrive({
    collection:     fc,
    description:    'Export_' + name,
    folder:         EXPORT_FOLDER,
    fileNamePrefix: name,
    fileFormat:     'SHP'
  });
};

// ============================================================
// Raster export tasks
// ============================================================

// FABDEM elevation + slope (continuous)
exportRaster(elevation, 'FABDEM_elevation', 'bilinear');
exportRaster(slopeImg,  'FABDEM_slope',     'bilinear');

// Permafrost probability (continuous)
exportRaster(permafrostProb, 'permafrost_probability', 'bilinear');

// Sea ice — 12 monthly medians (continuous)
monthNames.forEach(function(name, i) {
  var monthNum = i + 1;
  var mm       = (monthNum < 10 ? '0' : '') + monthNum;
  exportRaster(
    monthlyMedian(monthNum),
    'sea_ice_median_' + mm + '_' + name,
    'bilinear'
  );
});

// Dynamic World LULC mode composite (categorical) — FAST scale-150 export.
// Direct toDrive (NOT via exportRaster, whose 'mode' branch does the slow exact
// reduceResolution and whose 'bilinear' branch would wrongly average class codes).
// Nearest-samples the 10 m mode onto the exact 150 m grid via crsTransform. If a
// class-exact 15x15 spatial majority is ever required, revert to reduceResolution('mode')
// or use the tiled path.
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

// ------------------------------------------------------------
// LULC — ROBUST TWO-STAGE path (asset bake, then trivial resample)
// ------------------------------------------------------------
// The single-task export above computes the per-scene mode() AND the 10m->150m
// aggregation in one shot over 464M cells — near GEE's batch ceiling, so it can run
// for hours or time out. Splitting it bounds each task:
//   Stage A: bake the 10 m summer mode to an ASSET (robust batch, reusable intermediate).
//   Stage B: resample that static asset to the 150 m grid (fast, trivial) via exportRaster.
// Hedge: run Stage A in PARALLEL with the single-task export; whichever lands first wins.
var LULC_ASSET_ID =
  'projects/gee-friction-layer-processing/assets/DW_summer_mode_10m';

// --- Stage A: click Run on this task ('Bake_DW_summer_mode_10m'). ---
// (If re-baking, delete the existing asset first — toAsset won't overwrite.)
Export.image.toAsset({
  image:        lulc10m,                       // 10 m summer mode, EPSG:3338 base
  description:  'Bake_DW_summer_mode_10m',
  assetId:      LULC_ASSET_ID,
  region:       EXPORT_REGION,
  crs:          EXPORT_CRS,
  crsTransform: [10, 0, 0, 0, -10, 0],         // 10 m lattice nested in the 150 m grid
  maxPixels:    1e13
});

// --- Stage B: uncomment and run ONLY after 'Bake_DW_summer_mode_10m' finishes. ---
// Reuses the exportRaster 'mode' helper (reduceResolution -> reproject) on the static
// asset, so it lands on the exact 150 m grid with no per-scene mode() recompute.
// var lulcAsset = ee.Image(LULC_ASSET_ID);
// exportRaster(lulcAsset, 'dynamic_world_LULC_2022_2024_summer_mode_150m', 'mode');

// ============================================================
// Vector export tasks
// ============================================================
exportVector(grip4,        'GRIP4_roads_AK');
exportVector(akRoads,      'AKDOT_roads');
exportVector(nwnWaterways, 'NWN_waterways_AK');
exportVector(ports,        'AK_ports_and_harbors');
exportVector(ice_roads,        'Ice_Roads');

print('All export tasks queued — open the Tasks tab and click Run on each.');