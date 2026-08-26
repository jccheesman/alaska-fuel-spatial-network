"""River Ice Probability — Full ArcGIS Pro Pipeline (standalone version).

- End-to-end pipeline from waterFilledMedians2000_2023.geojson (Brown et al. 2026)
to 12 monthly river-ice probability rasters at 150 m EPSG:3338. 

- Per-month value: p_ice = clamp(1 - areaPropMedWater, 0, 1), median across the
3 periods (early/middle/late) per reach.

- Spatial fill: per-polygon median (wide rivers) + IDW (narrow rivers / gaps),
masked to NHDArea polygons union 200 m buffered NHDFlowline. Cells with no
source at all are left NoData for the friction build to fill under its own
distance cap -- see the note in process_data_month.

Run with Pro's Python environment:
    "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\scripts\\propy.bat" river_ice_full_pipeline.py
or, after `conda activate arcgispro-py3`:
    python river_ice_full_pipeline.py

Edit the Configuration block before running.
"""

import os
import arcpy
from arcpy.sa import (
    Idw, ZonalStatisticsAsTable, Con, IsNull, Raster, RadiusVariable,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Windows / ArcGIS Pro only (needs arcpy). Override the project root without
# editing this file via the FRICTION_LAYER_ROOT env var; the literal below is
# the fallback for the original authoring box.
PROJECT_ROOT = os.getenv("FRICTION_LAYER_ROOT", r"E:\DOE\Friction_layer\FRICTION_LAYER")

# Inputs
GEOJSON_PATH = os.path.join(PROJECT_ROOT, "waterFilledMedians2000_2023.geojson")
POLYGON_SHP  = os.path.join(PROJECT_ROOT, "brown_river_polygon",
                            "brown_river_polygons.shp")
FLOWLINE_SHP = os.path.join(PROJECT_ROOT, "flowlines",
                            "brown_river_flowlines.shp")

# Output: 12 filled 150 m TIFs
OUT_DIR = os.path.join(PROJECT_ROOT, "AK_Stack_150m")

# Canonical grid reference. The friction pipeline (friction_surface) expects
# every input raster to share the same origin / shape / extent as lulc.tif.
# Pre-aligning here means friction_preflight reports OK and _load_ice takes
# its same-grid path; the loader requires inputs already on the canonical
# grid (no WarpedVRT fallback), so alignment is required. If this file is
# missing, the alignment step is skipped with a warning and the output will
# fail preflight downstream.
CANONICAL_GRID_TIF = os.path.join(OUT_DIR, "lulc.tif")

# Grid / spatial reference
TARGET_CELL_SIZE  = 150
EPSG              = 3338
FLOWLINE_BUFFER_M = 200

# IDW knobs
IDW_POWER      = 2
IDW_NUM_POINTS = 12
IDW_MAX_DIST_M = 50000

# GeoJSON field names
FIELD_REACH = "ReachID"
FIELD_MONTH = "month"
FIELD_VALUE = "areaPropMedWater"

DATA_MONTHS   = [1, 2, 3, 4, 5, 6, 9, 10, 11, 12]
SUMMER_MONTHS = [7, 8]


# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------
# Configures arcpy globals (Spatial license, EPSG:3338, 150 m cell size,
# parallel factor, no Z/M) and routes intermediate I/O through ArcGIS's
# auto-managed scratch GDB/folder to avoid OneDrive / project-file locks.
# Returns the scratch GDB path used by every downstream step.
def setup_environment():
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput          = True
    arcpy.env.outputCoordinateSystem   = arcpy.SpatialReference(EPSG)
    arcpy.env.cellSize                 = TARGET_CELL_SIZE
    arcpy.env.pyramid                  = "NONE"
    arcpy.env.parallelProcessingFactor = "75%"
    arcpy.env.outputZFlag              = "Disabled"
    arcpy.env.outputMFlag              = "Disabled"

    # Auto-managed scratch — avoids OneDrive / Pro-project locks
    arcpy.env.scratchWorkspace = arcpy.env.scratchFolder
    arcpy.env.workspace        = arcpy.env.scratchGDB

    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    print("Scratch GDB:    ", arcpy.env.scratchGDB)
    print("Scratch folder: ", arcpy.env.scratchFolder)
    print("Output dir:     ", OUT_DIR)
    return arcpy.env.scratchGDB


# ---------------------------------------------------------------------------
# Step 0 — Clean start - Deletes all layer from geodatabase and the map
# ---------------------------------------------------------------------------
# Idempotent reset so reruns don't collide with prior intermediates: removes
# matching layers/tables from the active Pro map (no-op when standalone),
# deletes known feature classes / per-month tables / rasters from the scratch
# GDB, wipes the river-mask scratch folder (skipping ArcGIS .sr.lock files),
# and clears the previous mosaic GDB and river_ice_*/provenance_* TIFFs in
# OUT_DIR.
def clean_start(SCRATCH_GDB):
    GDB_BASE_NAMES = [
        "reach_points_all", "reach_points_proj", "reach_month_median",
        "reach_points", "flowline_buf", "polygons_repaired",
        "reach_points_p_ice", "polygons_validation",
    ]
    MONTH_PREFIXES = ["stats_", "pts_", "ptsras_", "zonal_", "zonalall_",
                      "poly_", "polyras_", "final_", "prov_"]
    ALL_MONTHS = list(range(1, 13))

    # 1. Remove matching layers/tables from every map (no-op in standalone)
    NB_PREFIXES = (
        "reach_points", "reach_month_median", "flowline_buf",
        "polygons_repaired", "stats_", "pts_", "ptsras_", "zonal_", "poly_",
        "polyras_", "buf_ras", "poly_ras_mask", "river_mask", "river_ice_",
        "reach_points_p_ice", "polygons_validation", "zonalall_", "idw_",
        "provenance_", "prov_",
    )
    try:
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        for m in aprx.listMaps():
            for lyr in list(m.listLayers()):
                if lyr.name.startswith(NB_PREFIXES):
                    print("  map layer:", lyr.name)
                    m.removeLayer(lyr)
            for tbl in list(m.listTables()):
                if tbl.name.startswith(NB_PREFIXES):
                    print("  map table:", tbl.name)
                    m.removeTable(tbl)
    except Exception as e:
        print("Map cleanup skipped:", e)

    # 2. Delete from scratch GDB
    arcpy.env.workspace = SCRATCH_GDB
    existing = set((arcpy.ListFeatureClasses() or [])
                 + (arcpy.ListTables() or [])
                 + (arcpy.ListRasters() or []))

    to_delete = list(GDB_BASE_NAMES)
    for m in ALL_MONTHS:
        mm = "{:02d}".format(m)
        to_delete.extend("{}{}".format(p, mm) for p in MONTH_PREFIXES)

    for name in to_delete:
        if name in existing:
            arcpy.management.Delete(os.path.join(SCRATCH_GDB, name))
            print("  GDB delete:", name)

    # 3. Wipe the mask scratch folder; skip ArcGIS-managed .sr.lock files
    MASK_DIR = os.path.join(arcpy.env.scratchFolder, "river_mask_scratch")
    if os.path.isdir(MASK_DIR):
        for f in os.listdir(MASK_DIR):
            if f.endswith(".lock") or ".sr.lock" in f:
                continue
            try:
                arcpy.management.Delete(os.path.join(MASK_DIR, f))
                print("  mask delete:", f)
            except Exception as e:
                print("  mask skip:  ", f, "-", e)

    # 4. Delete previous mosaic and TIFs in OUT_DIR
    mosaic_gdb_path = os.path.join(OUT_DIR, "river_ice_mosaic.gdb")
    if arcpy.Exists(mosaic_gdb_path):
        try:
            arcpy.management.Delete(mosaic_gdb_path)
            print("  mosaic delete:", os.path.basename(mosaic_gdb_path))
        except Exception as e:
            print("  mosaic skip:  ", mosaic_gdb_path, "-", e)

    if os.path.isdir(OUT_DIR):
        for f in os.listdir(OUT_DIR):
            if (f.startswith("river_ice_") or f.startswith("provenance_")) \
                    and f.lower().endswith(".tif"):
                try:
                    arcpy.management.Delete(os.path.join(OUT_DIR, f))
                    print("  out delete:", f)
                except Exception as e:
                    print("  out skip:  ", f, "-", e)

    print("Clean start complete.")


# ---------------------------------------------------------------------------
# Step 1 — Load GeoJSON as points * reproject to ESPG 3338
# ---------------------------------------------------------------------------
# Converts the Brown et al. 2026 waterFilledMedians2000_2023 GeoJSON into a
# point feature class in the scratch GDB and reprojects to EPSG:3338 if the
# source CRS differs. Returns the path to the projected points.
def load_points(SCRATCH_GDB):
    points_all = os.path.join(SCRATCH_GDB, "reach_points_all") #waterFilledMedians2000_2023.geojson - Brown et al., 2026
    arcpy.conversion.JSONToFeatures(GEOJSON_PATH, points_all, "POINT")

    desc = arcpy.Describe(points_all)
    if desc.spatialReference.factoryCode != EPSG:
        proj = os.path.join(SCRATCH_GDB, "reach_points_proj")
        arcpy.management.Project(points_all, proj,
                                  arcpy.SpatialReference(EPSG))
        points_all = proj

    print("{} observations loaded".format(
        arcpy.management.GetCount(points_all)[0]))
    return points_all


# ---------------------------------------------------------------------------
# Step 2 — Per-point percentage_ice (p_ice)
# ---------------------------------------------------------------------------
# Adds a `p_ice` field to each observation as clamp(1 - areaPropMedWater, 0, 1).
# Inverts the source's open-water proportion into an ice probability bounded
# to [0, 1] so downstream aggregations stay on a clean 0..1 scale.
def add_p_ice(points_all):
    arcpy.management.AddField(points_all, "p_ice", "DOUBLE")
    arcpy.management.CalculateField(
        points_all, "p_ice",
        "max(0.0, min(1.0, 1.0 - !{}!))".format(FIELD_VALUE),
        "PYTHON3",
    )
    print("p_ice computed")


# ---------------------------------------------------------------------------
# Step 3 — Aggregate to median per (ReachID, month)
# ---------------------------------------------------------------------------
# Collapses the three per-period observations (early/middle/late) into one
# representative p_ice per (ReachID, month) by taking the median — robust to
# the occasional outlier period and yields a single value to drive each
# monthly raster.
def aggregate_reach_month(points_all, SCRATCH_GDB):
    stats_tbl = os.path.join(SCRATCH_GDB, "reach_month_median")
    arcpy.analysis.Statistics(
        in_table=points_all,
        out_table=stats_tbl,
        statistics_fields=[["p_ice", "MEDIAN"]],
        case_field=[FIELD_REACH, FIELD_MONTH],
    )
    print("{} (reach, month) groups".format(
        arcpy.management.GetCount(stats_tbl)[0]))
    return stats_tbl


# ---------------------------------------------------------------------------
# Step 4 — One representative point per reach
# ---------------------------------------------------------------------------
# Deduplicates the observation points down to one feature per ReachID so each
# reach contributes a single location to the monthly point→raster step. The
# per-month value is joined back from Step 3's reach-month median table.
def dedup_reaches(points_all, SCRATCH_GDB):
    reach_points = os.path.join(SCRATCH_GDB, "reach_points")
    arcpy.management.CopyFeatures(points_all, reach_points)
    arcpy.management.DeleteIdentical(reach_points, [FIELD_REACH])
    print("{} unique reaches".format(
        arcpy.management.GetCount(reach_points)[0]))
    return reach_points


# ---------------------------------------------------------------------------
# Step 5 — River mask raster (150 m)
# ---------------------------------------------------------------------------
# Builds the 150 m raster that defines "river" cells: union of NHDArea
# polygons (wide rivers) with a 200 m buffer around NHDFlowlines (narrow
# rivers). Repairs input geometry, sets env.extent to cover both layers,
# rasterizes each, and combines them via Con/IsNull. The saved mask is
# wired into arcpy.env.snapRaster and arcpy.env.mask so all subsequent
# raster ops align to and are clipped by the river network.
def build_river_mask(SCRATCH_GDB):
    flowline_buf_fc = os.path.join(SCRATCH_GDB, "flowline_buf")
    arcpy.analysis.Buffer(FLOWLINE_SHP, flowline_buf_fc,
                          "{} Meters".format(FLOWLINE_BUFFER_M),
                          dissolve_option="ALL")
    arcpy.management.RepairGeometry(flowline_buf_fc, delete_null="DELETE_NULL")

    poly_repaired = os.path.join(SCRATCH_GDB, "polygons_repaired")
    arcpy.management.CopyFeatures(POLYGON_SHP, poly_repaired)
    arcpy.management.RepairGeometry(poly_repaired, delete_null="DELETE_NULL")

    ext_buf  = arcpy.Describe(flowline_buf_fc).extent
    ext_poly = arcpy.Describe(poly_repaired).extent
    arcpy.env.extent = arcpy.Extent(
        min(ext_buf.XMin, ext_poly.XMin),
        min(ext_buf.YMin, ext_poly.YMin),
        max(ext_buf.XMax, ext_poly.XMax),
        max(ext_buf.YMax, ext_poly.YMax),
    )
    arcpy.env.snapRaster = None
    arcpy.env.mask       = None  # build mask before constraining ops to it

    MASK_DIR = os.path.join(arcpy.env.scratchFolder, "river_mask_scratch")
    if not os.path.isdir(MASK_DIR):
        os.makedirs(MASK_DIR)

    buf_ras = os.path.join(MASK_DIR, "buf_ras.tif")
    arcpy.conversion.PolygonToRaster(flowline_buf_fc, "OBJECTID", buf_ras,
                                      cellsize=TARGET_CELL_SIZE)

    poly_ras_mask = os.path.join(MASK_DIR, "poly_ras_mask.tif")
    arcpy.conversion.PolygonToRaster(poly_repaired, "OBJECTID", poly_ras_mask,
                                      cellsize=TARGET_CELL_SIZE)

    river_mask_obj = Con(IsNull(Raster(buf_ras)),
                          Raster(poly_ras_mask),
                          Raster(buf_ras))
    river_mask_ras = os.path.join(MASK_DIR, "river_mask.tif")
    river_mask_obj.save(river_mask_ras)
    arcpy.env.snapRaster = river_mask_ras
    arcpy.env.mask       = river_mask_ras  # confines IDW & friends

    arcpy.management.AddField(poly_repaired, "join_id", "LONG")
    arcpy.management.CalculateField(poly_repaired, "join_id",
                                     "!OBJECTID!", "PYTHON3")

    print("River mask:", river_mask_ras)
    return poly_repaired, river_mask_ras, MASK_DIR


# ---------------------------------------------------------------------------
# Step 6 — Per-month processing
# ---------------------------------------------------------------------------
# Produces one 150 m river_ice_MM.tif and one provenance_MM.tif per month.
# For data months (Jan–Jun, Sep–Dec): select that month's reach medians,
# rasterize the points, fill wide rivers with per-polygon zonal median,
# fill narrow rivers / gaps with IDW (power=2, 12 nearest, 50 km cap),
# clamp to [0, 1], then nearest-neighbor allocate to fill any remaining
# NoData inside the river mask. Provenance raster encodes which stage
# produced each cell: 1=polygon-median, 2=IDW, 3=NN-fallback.
# Summer months (Jul, Aug) are handled separately as a constant 0.0
# everywhere inside the river mask.
MEDIAN_FIELD = "MEDIAN_p_ice"


def process_data_month(m, SCRATCH_GDB, MASK_DIR,
                       stats_tbl, reach_points, poly_repaired,
                       river_mask_ras):
    mm = "{:02d}".format(m)
    print("Month {} — processing".format(mm))

    month_tbl = os.path.join(SCRATCH_GDB, "stats_{}".format(mm))
    arcpy.analysis.TableSelect(stats_tbl, month_tbl,
                                '"{}" = {}'.format(FIELD_MONTH, m))
    n_rows = int(arcpy.management.GetCount(month_tbl)[0])
    if n_rows == 0:
        print("  no rows for month {} — skipping".format(mm))
        return
    print("  {} reaches with data".format(n_rows))

    pts_m = os.path.join(SCRATCH_GDB, "pts_{}".format(mm))
    arcpy.management.CopyFeatures(reach_points, pts_m)
    arcpy.management.JoinField(pts_m, FIELD_REACH,
                                month_tbl, FIELD_REACH, [MEDIAN_FIELD])
    pts_layer = "pts_layer_{}".format(mm)
    arcpy.management.MakeFeatureLayer(
        pts_m, pts_layer,
        '"{}" IS NOT NULL'.format(MEDIAN_FIELD),
    )

    pts_ras = os.path.join(SCRATCH_GDB, "ptsras_{}".format(mm))
    arcpy.conversion.PointToRaster(pts_layer, MEDIAN_FIELD, pts_ras,
                                    cell_assignment="MEAN",
                                    cellsize=TARGET_CELL_SIZE)
    zonal_tbl = os.path.join(SCRATCH_GDB, "zonal_{}".format(mm))
    ZonalStatisticsAsTable(poly_repaired, "join_id", pts_ras, zonal_tbl,
                            ignore_nodata="DATA",
                            statistics_type="MEDIAN")
    poly_join = os.path.join(SCRATCH_GDB, "poly_{}".format(mm))
    arcpy.management.CopyFeatures(poly_repaired, poly_join)
    arcpy.management.JoinField(poly_join, "join_id",
                                zonal_tbl, "join_id", ["MEDIAN"])
    poly_ras = os.path.join(SCRATCH_GDB, "polyras_{}".format(mm))
    arcpy.conversion.PolygonToRaster(poly_join, "MEDIAN", poly_ras,
                                      cell_assignment="CELL_CENTER",
                                      cellsize=TARGET_CELL_SIZE)

    # IDW -> TIFF in MASK_DIR. arcpy.env.mask already clips to river cells.
    idw_tif = os.path.join(MASK_DIR, "idw_{}.tif".format(mm))
    if arcpy.Exists(idw_tif):
        arcpy.management.Delete(idw_tif)
    idw_ras = Idw(pts_layer, MEDIAN_FIELD,
                  cell_size=TARGET_CELL_SIZE,
                  power=IDW_POWER,
                  search_radius=RadiusVariable(IDW_NUM_POINTS,
                                                IDW_MAX_DIST_M))
    idw_ras.save(idw_tif)
    idw_masked = Raster(idw_tif)

    # Mosaic + clamp. Materialize to scratch GDB first, then CopyRaster to
    # TIFF — saving a chained Con expression directly to TIFF on a different
    # drive can hit ERROR 010240.
    poly_r   = Raster(poly_ras)
    combined = Con(IsNull(poly_r), idw_masked, poly_r)
    clamped  = Con(combined < 0, 0, Con(combined > 1, 1, combined))

    # Gaps inside the river mask are deliberately left as NoData.
    #
    # This used to be EucAllocation(clamped). That was wrong: EucAllocation
    # treats its input as a ZONE raster, so a float p_ice in [0, 1] is
    # truncated to an integer before allocation. Every gap cell inherited 0
    # (or 1, for a source cell at exactly 1.0) rather than its neighbour's
    # actual value. Measured on the Jan 2026 output: 73,526 gap cells held
    # only 85 distinct values, 84% of them exactly 0.0 -- i.e. "open water"
    # -- of which 4,894 sit on the NWN river corridor and were read
    # downstream as navigable in January. See docs/TEST_LOG.md.
    #
    # Leaving them NoData hands the gap-filling to the friction build's own
    # cascade (friction_surface.extend_ice_nearest -> fill_by_nearest_median),
    # which is distance-capped at RIVER_ICE_FILL_MAX_KM and clipped to the
    # river mask. One fill policy instead of two, and the capped one.
    mask_r = Raster(river_mask_ras)
    final  = Con(~IsNull(mask_r), clamped)

    final_gdb = os.path.join(SCRATCH_GDB, "final_{}".format(mm))
    final.save(final_gdb)

    out_tif = os.path.join(OUT_DIR, "river_ice_{}.tif".format(mm))
    if arcpy.Exists(out_tif):
        arcpy.management.Delete(out_tif)
    arcpy.management.CopyRaster(
        in_raster=final_gdb,
        out_rasterdataset=out_tif,
        pixel_type="32_BIT_FLOAT",
        format="TIFF",
        nodata_value=-9999,
    )
    print("  -> {}".format(out_tif))

    # Per-pixel provenance: 1=polygon-median, 2=IDW, 3=no source here, left
    # NoData for the friction build's capped cascade to fill. NoData outside
    # the river mask. Lets downstream code distinguish which stage produced
    # each cell (the value raster alone does not carry this).
    prov = Con(~IsNull(mask_r),
               Con(~IsNull(poly_r), 1,
                   Con(~IsNull(idw_masked), 2, 3)))
    prov_gdb = os.path.join(SCRATCH_GDB, "prov_{}".format(mm))
    prov.save(prov_gdb)

    prov_tif = os.path.join(OUT_DIR, "provenance_{}.tif".format(mm))
    if arcpy.Exists(prov_tif):
        arcpy.management.Delete(prov_tif)
    arcpy.management.CopyRaster(
        in_raster=prov_gdb,
        out_rasterdataset=prov_tif,
        pixel_type="8_BIT_UNSIGNED",
        format="TIFF",
        nodata_value=0,
    )
    print("  -> {}".format(prov_tif))
    arcpy.management.Delete(pts_layer)


def process_summer_month(m, SCRATCH_GDB, river_mask_ras):
    mm = "{:02d}".format(m)
    print("Month {} — summer (constant 0)".format(mm))
    final = Con(Raster(river_mask_ras) >= 0, 0.0)

    final_gdb = os.path.join(SCRATCH_GDB, "final_{}".format(mm))
    final.save(final_gdb)

    out_tif = os.path.join(OUT_DIR, "river_ice_{}.tif".format(mm))
    if arcpy.Exists(out_tif):
        arcpy.management.Delete(out_tif)
    arcpy.management.CopyRaster(
        in_raster=final_gdb,
        out_rasterdataset=out_tif,
        pixel_type="32_BIT_FLOAT",
        format="TIFF",
        nodata_value=-9999,
    )
    print("  -> {}".format(out_tif))


# ---------------------------------------------------------------------------
# Step 7 — Align outputs to friction canonical grid
# ---------------------------------------------------------------------------
# Snaps every river_ice_MM.tif to the canonical lulc.tif grid (origin, cell
# size, shape, extent). Without this, friction_preflight raises FATAL on
# river_ice (the friction loader requires inputs already on the canonical
# grid, with no WarpedVRT fallback) and the pipeline will not run. Two-step
# per file: ProjectRaster snaps origin + cell size via
# env.snapRaster; Clip with maintain_clipping_extent forces an exact match
# to lulc's shape, padding NoData outside the river mask.
# Resampling: BILINEAR — river_ice is continuous fractional cover in [0, 1].
# Cells outside the canonical extent are dropped; cells outside the river
# mask stay NoData. provenance_*.tif is intentionally NOT aligned: the
# friction pipeline doesn't consume it (it's QA-only), and the values are
# categorical (1/2/3) so bilinear would corrupt them.
def align_to_canonical_grid():
    if not arcpy.Exists(CANONICAL_GRID_TIF):
        print("WARN: canonical grid {} not found — skipping alignment"
              .format(CANONICAL_GRID_TIF))
        return

    print("Aligning river_ice rasters to canonical grid:", CANONICAL_GRID_TIF)

    # Stash and override env so the alignment step is self-contained.
    saved_snap   = arcpy.env.snapRaster
    saved_extent = arcpy.env.extent
    saved_cell   = arcpy.env.cellSize
    saved_mask   = arcpy.env.mask

    arcpy.env.snapRaster = CANONICAL_GRID_TIF
    arcpy.env.extent     = CANONICAL_GRID_TIF
    arcpy.env.cellSize   = CANONICAL_GRID_TIF
    arcpy.env.mask       = None  # alignment must not be clipped by river mask

    out_sr = arcpy.SpatialReference(EPSG)

    try:
        for m in range(1, 13):
            mm = "{:02d}".format(m)
            src_tif = os.path.join(OUT_DIR, "river_ice_{}.tif".format(mm))
            if not arcpy.Exists(src_tif):
                print("  month {}: source missing — skipping".format(mm))
                continue

            proj_tif = os.path.join(OUT_DIR, "river_ice_{}_proj.tif".format(mm))
            clip_tif = os.path.join(OUT_DIR, "river_ice_{}_aligned.tif".format(mm))
            for tmp in (proj_tif, clip_tif):
                if arcpy.Exists(tmp):
                    arcpy.management.Delete(tmp)

            # 1. Snap origin + cell size to the canonical grid (CRS no-op,
            # both already EPSG:3338).
            arcpy.management.ProjectRaster(
                in_raster=src_tif,
                out_raster=proj_tif,
                out_coor_system=out_sr,
                resampling_type="BILINEAR",
                cell_size=TARGET_CELL_SIZE,
            )

            # 2. Force exact shape/extent match to lulc.tif. MAINTAIN_EXTENT
            # pads with NoData where the river-mask raster is smaller than
            # the canonical extent.
            arcpy.management.Clip(
                in_raster=proj_tif,
                rectangle="",
                out_raster=clip_tif,
                in_template_dataset=CANONICAL_GRID_TIF,
                nodata_value=-9999,
                clipping_geometry="NONE",
                maintain_clipping_extent="MAINTAIN_EXTENT",
            )

            arcpy.management.Delete(src_tif)
            arcpy.management.Rename(clip_tif, src_tif)
            arcpy.management.Delete(proj_tif)
            print("  aligned: river_ice_{}.tif".format(mm))
    finally:
        arcpy.env.snapRaster = saved_snap
        arcpy.env.extent     = saved_extent
        arcpy.env.cellSize   = saved_cell
        arcpy.env.mask       = saved_mask


# ---------------------------------------------------------------------------
# Step 8 — Validation layers
# ---------------------------------------------------------------------------
# Diagnostic feature classes for QA against source observations:
#   - reach_points_p_ice: one point per reach with monthly p_ice columns (p01..p12)
#   - polygons_validation: per-polygon zonal stats per month (count/min/max/range/median),
#     plus worst_range / worst_month / worst_max roll-ups to flag polygons where
#     within-polygon disagreement is largest.
def build_validation_layers(SCRATCH_GDB, reach_points, poly_repaired):
    STATS_TO_KEEP = ["COUNT", "MIN", "MAX", "RANGE", "MEDIAN"]

    val_pts = os.path.join(SCRATCH_GDB, "reach_points_p_ice")
    arcpy.management.CopyFeatures(reach_points, val_pts)

    for m in DATA_MONTHS:
        mm = "{:02d}".format(m)
        month_tbl = os.path.join(SCRATCH_GDB, "stats_{}".format(mm))
        if not arcpy.Exists(month_tbl):
            continue
        arcpy.management.JoinField(val_pts, FIELD_REACH,
                                    month_tbl, FIELD_REACH, [MEDIAN_FIELD])
        new_name = "p{}".format(mm)
        arcpy.management.AlterField(val_pts, MEDIAN_FIELD, new_name, new_name)

    print("Built", val_pts)

    val_poly = os.path.join(SCRATCH_GDB, "polygons_validation")
    arcpy.management.CopyFeatures(poly_repaired, val_poly)

    for m in DATA_MONTHS:
        mm = "{:02d}".format(m)
        pts_ras = os.path.join(SCRATCH_GDB, "ptsras_{}".format(mm))
        if not arcpy.Exists(pts_ras):
            continue
        zall = os.path.join(SCRATCH_GDB, "zonalall_{}".format(mm))
        ZonalStatisticsAsTable(poly_repaired, "join_id", pts_ras, zall,
                                ignore_nodata="DATA",
                                statistics_type="ALL")
        arcpy.management.JoinField(val_poly, "join_id",
                                    zall, "join_id", STATS_TO_KEEP)
        for f in STATS_TO_KEEP:
            new_name = "m{}_{}".format(mm, f.lower())
            arcpy.management.AlterField(val_poly, f, new_name, new_name)

    for fname in ("worst_range", "worst_max"):
        arcpy.management.AddField(val_poly, fname, "DOUBLE")
    arcpy.management.AddField(val_poly, "worst_month", "TEXT", field_length=2)

    existing = {f.name for f in arcpy.ListFields(val_poly)}
    range_fields = [("m{:02d}_range".format(m), "{:02d}".format(m))
                    for m in DATA_MONTHS
                    if "m{:02d}_range".format(m) in existing]
    max_fields   = ["m{:02d}_max".format(m)
                    for m in DATA_MONTHS
                    if "m{:02d}_max".format(m) in existing]

    cursor_fields = (["worst_range", "worst_month", "worst_max"]
                     + [f for f, _ in range_fields]
                     + max_fields)
    nr = len(range_fields)
    with arcpy.da.UpdateCursor(val_poly, cursor_fields) as cur:
        for row in cur:
            rng_vals = row[3:3 + nr]
            max_vals = row[3 + nr:]
            best_v, best_i = None, -1
            for i, v in enumerate(rng_vals):
                if v is None:
                    continue
                if best_v is None or v > best_v:
                    best_v, best_i = v, i
            row[0] = best_v
            row[1] = range_fields[best_i][1] if best_i >= 0 else None
            ms = [v for v in max_vals if v is not None]
            row[2] = max(ms) if ms else None
            cur.updateRow(row)

    print("Built", val_poly)


# ---------------------------------------------------------------------------
# Step 9 — Bundle into a mosaic dataset
# ---------------------------------------------------------------------------
# Wraps the 12 monthly river_ice_*.tif rasters into a single ArcGIS mosaic
# dataset so they browse as one time-aware layer. Provenance TIFFs are
# excluded by the filename filter. Display stats are pinned to 0–1 so all
# months render on the same stretch.
def build_mosaic():
    mosaic_gdb  = os.path.join(OUT_DIR, "river_ice_mosaic.gdb")
    mosaic_name = "river_ice_monthly"
    mosaic_path = os.path.join(mosaic_gdb, mosaic_name)

    if not arcpy.Exists(mosaic_gdb):
        arcpy.management.CreateFileGDB(os.path.dirname(mosaic_gdb),
                                        os.path.basename(mosaic_gdb))

    if arcpy.Exists(mosaic_path):
        arcpy.management.Delete(mosaic_path)
    arcpy.management.CreateMosaicDataset(
        in_workspace=mosaic_gdb,
        in_mosaicdataset_name=mosaic_name,
        coordinate_system=arcpy.SpatialReference(EPSG),
        pixel_type="32_BIT_FLOAT",
    )

    arcpy.management.AddRastersToMosaicDataset(
        in_mosaic_dataset=mosaic_path,
        raster_type="Raster Dataset",
        input_path=[OUT_DIR],
        filter="river_ice_*.tif",
        update_cellsize_ranges="UPDATE_CELL_SIZES",
        update_boundary="UPDATE_BOUNDARY",
        update_overviews="NO_OVERVIEWS",
        build_pyramids="NO_PYRAMIDS",
        calculate_statistics="CALCULATE_STATISTICS",
    )

    arcpy.management.SetRasterProperties(
        mosaic_path,
        data_type="GENERIC",
        statistics=[[1, 0.0, 1.0, 0.5, 0.25]],
    )

    print("Mosaic dataset:", mosaic_path)
    print("Items added:   ", arcpy.management.GetCount(mosaic_path)[0])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    SCRATCH_GDB = setup_environment()

    clean_start(SCRATCH_GDB)

    points_all   = load_points(SCRATCH_GDB)
    add_p_ice(points_all)
    stats_tbl    = aggregate_reach_month(points_all, SCRATCH_GDB)
    reach_points = dedup_reaches(points_all, SCRATCH_GDB)

    poly_repaired, river_mask_ras, MASK_DIR = build_river_mask(SCRATCH_GDB)

    for m in DATA_MONTHS:
        process_data_month(m, SCRATCH_GDB, MASK_DIR,
                           stats_tbl, reach_points, poly_repaired,
                           river_mask_ras)
    for m in SUMMER_MONTHS:
        process_summer_month(m, SCRATCH_GDB, river_mask_ras)

    align_to_canonical_grid()

    build_validation_layers(SCRATCH_GDB, reach_points, poly_repaired)
    build_mosaic()

    arcpy.CheckInExtension("Spatial")
    print("\nDone. 12 rasters in", OUT_DIR)


if __name__ == "__main__":
    main()
