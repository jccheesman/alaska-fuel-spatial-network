---
name: align-to-ak-stack
description: Reproject, resample, and snap a raster onto the canonical
  AK_Stack_150m grid (reference layer: the land-cover raster
  inputs/friction_rasters/dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif)
  used by the friction layer. Use when ingesting any new raster (land cover,
  GEE export, sea-ice median, road raster) that must stack pixel-aligned with
  existing friction-input layers. Do NOT use for vector data — rasterize
  first, then align.
---

# Align raster to AK_Stack_150m grid

## When to use this skill

Trigger this skill when the user wants to add or refresh a raster layer in
`inputs/friction_rasters/` and the source raster has a different CRS, resolution,
extent, or pixel alignment than the canonical stack.

Do NOT trigger for:
- Vector inputs (shapefiles, GeoPackages) — those go through a rasterize step first
- Layers already produced by the GEE pipeline (they're aligned at export)

## Canonical grid specification

All layers in `inputs/friction_rasters/` MUST match:

- **CRS:** EPSG:3338 (Alaska Albers)
- **Resolution:** 150m × 150m
- **Pixel alignment:** snapped to the canonical reference layer
  `inputs/friction_rasters/dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif`
  — the Dynamic World export under its own (GEE) name, which is the name the
  pipeline reads (`friction_paths.RASTER_NAMES["lulc"]`). NEVER substitute a
  different raster as the grid reference, and never rename it.
- **Extent:** matches reference grid bounds (do not clip smaller; pad with nodata)
- **NoData:** -9999 for float, 255 for uint8

If a candidate doesn't match all four, run the alignment procedure below.

## Procedure

1. **Inspect the source.** Read CRS, resolution, extent, dtype, nodata. Report
   these to the user before transforming anything.

2. **Choose resampling method** (the script also supports `cubic`, `average`,
   `mode`):
   - Continuous, same or coarser source resolution (NDVI, elevation,
     sea-ice concentration) → `bilinear`
   - Continuous, downsampling from finer resolution (e.g. 30m → 150m) →
     `average` (bilinear samples only near the pixel center; average uses
     all contributing source pixels)
   - Categorical, same-resolution snapping (road class, ice-road mask) →
     `nearest`
   - Categorical, downsampling from finer resolution → `mode` (majority
     vote per output cell; the canonical LULC is itself a modal product)
   - Ask the user if ambiguous; do not guess.

3. **Run alignment** using `scripts/align_raster.py` (in this skill folder):
   ```
   python scripts/align_raster.py \
       --input <src.tif> \
       --reference inputs/friction_rasters/dynamic_world_LULC_2022_2024_summer_mode_150m_EPSG3338.tif \
       --resampling <method> \
       --output inputs/friction_rasters/<layer_name>.tif
   ```
   Output goes to `inputs/friction_rasters/` (the pipeline's
   `RASTER_DIR`). If the layer replaces one of the five pipeline inputs, write
   it under the pipeline's name for that input (`friction_paths.RASTER_NAMES`,
   `sea_ice_name`, `river_ice_name`); never invent a new name for a known input.

4. **Verify the output** before reporting success:
   - CRS == EPSG:3338
   - Shape matches reference
   - Affine transform matches reference exactly (not approximately)
   - NoData value set correctly

5. **Do NOT** modify or overwrite the LULC reference layer — it is the source of
   truth for grid alignment. If LULC itself needs to be regenerated, that is a
   separate, deliberate operation that requires re-aligning every other layer
   in the stack.

## Edge cases

- **Source extent larger than reference:** clip to reference bounds.
- **Source extent smaller than reference:** pad with nodata; the script warns
  with source vs. reference bounds — relay that warning to the user.
- **Source has no CRS metadata:** stop and ask the user — do not assume.

## Related

- Friction values are applied AFTER alignment — see `assign-friction-values`.
- After the aligned layer feeds a pipeline run, rebuild and validate via the
  `run-friction-pipeline` skill (grid conformance → preflight → output QA,
  with failure interpretation); it wraps
  `python -m friction_surface.qa.qa_friction_stack` (14-file contract,
  profile match against the reference grid, ice-gating direction, value
  floor; exit 0 = pass).
- Friction is environmental only; do not fold cost into aligned layers.
