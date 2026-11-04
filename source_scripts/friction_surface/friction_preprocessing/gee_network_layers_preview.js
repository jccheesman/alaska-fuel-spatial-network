// ============================================================================
// NETWORK INPUT LAYERS — Earth Engine preview (visual check only)
//
// Overlays the transport layers the spatial network is built from (workflow 02)
// on Alaska, so they can be eyeballed against the friction rasters made by
// gee_friction_layer_multi_data_processing.js. It is kept for that check and
// as a record of which layers were uploaded; NOTHING downstream reads its
// output. The network build reads the ORIGINAL downloads from data/raw/
// (the file-by-file layout is in DATA.md section 4.1), never a GEE export.
//
// The layers are uploads of those same downloads. To use this script, upload
// them to your own project and set the asset ids in CONFIG; any layer you have
// not uploaded can simply be commented out.
// ============================================================================

// ----------------------------------------------------------------------------
// CONFIG — your project's uploaded copies of the network inputs
// ----------------------------------------------------------------------------
var ASSET_ROOT = 'projects/gee-friction-layer-processing/assets';   // <- your project
var ASSETS = {
  roads:     ASSET_ROOT + '/AKDOT_roads',                      // AKDOT&PF roads (the sole road source)
  waterways: ASSET_ROOT + '/NWN_Waterway_Network_Lines',       // USACE National Waterway Network
  ports:     ASSET_ROOT + '/AK_Ports_and_Harbors',             // ports and harbors (barge anchors)
  iceRoads:  ASSET_ROOT + '/ice_roads_merged_and_processed'    // North Slope ice roads, merged
};
var EXPORT_VECTORS = false;        // true: also queue SHP exports of the layers to Drive
var EXPORT_FOLDER  = 'AK_Stack_150m';

// ----------------------------------------------------------------------------
// Study area
// ----------------------------------------------------------------------------
var alaska = ee.FeatureCollection('TIGER/2018/States')
               .filter(ee.Filter.eq('STATEFP', '02'));
Map.addLayer(alaska, {color: 'red'}, 'Alaska boundary');
Map.setCenter(-152.0, 64.0, 4);

// ----------------------------------------------------------------------------
// Layers used by the network build (uploaded copies of the data/raw downloads)
// ----------------------------------------------------------------------------
var akRoads      = ee.FeatureCollection(ASSETS.roads);
var nwnWaterways = ee.FeatureCollection(ASSETS.waterways);
var ports        = ee.FeatureCollection(ASSETS.ports);
var iceRoads     = ee.FeatureCollection(ASSETS.iceRoads);

// GRIP4 global roads: NO LONGER USED by the network (removed 2026-09-15; the
// AKDOT&PF layer is the sole road source). Shown off by default, for comparison.
var grip4 = ee.FeatureCollection('projects/sat-io/open-datasets/GRIP4/North-America')
              .filterBounds(alaska);

Map.addLayer(grip4.style({color: 'FF4500', width: 1}),        {}, 'GRIP4 roads (legacy, unused)', false);
Map.addLayer(akRoads.style({color: '252525', width: 1.5}),    {}, 'AKDOT&PF roads');
Map.addLayer(nwnWaterways.style({color: '1F78B4', width: 1.5}), {}, 'USACE waterways (NWN)');
Map.addLayer(ports.style({color: 'D95F02', pointSize: 6, pointShape: 'circle',
                          fillColor: 'FDAE6B80'}),              {}, 'Ports and harbors');
Map.addLayer(iceRoads.style({color: 'FF00FF', width: 1}),     {}, 'Ice roads');

// ----------------------------------------------------------------------------
// Optional: export the layers as shapefiles to Drive (not consumed by the build)
// ----------------------------------------------------------------------------
var exportVector = function(fc, name) {
  Export.table.toDrive({collection: fc, description: 'Export_' + name,
                        folder: EXPORT_FOLDER, fileNamePrefix: name, fileFormat: 'SHP'});
};
if (EXPORT_VECTORS) {
  exportVector(akRoads,      'AKDOT_roads');
  exportVector(nwnWaterways, 'NWN_waterways_AK');
  exportVector(ports,        'AK_ports_and_harbors');
  exportVector(iceRoads,     'Ice_Roads');
  print('Vector export tasks queued — open the Tasks tab and click Run on each.');
}
