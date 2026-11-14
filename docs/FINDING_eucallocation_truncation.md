# The arcpy NN fallback truncates p_ice to 0 or 1

Found while prototyping a Python port of `river_ice_full_pipeline.py`, 2026-08-21.
The port is not the point — this is a defect in the arcpy stage itself, and the
evidence below is read straight off arcpy's own two output rasters.

## The observation

`process_data_month` ends with:

```python
nn_fill = EucAllocation(clamped)
final   = Con(~IsNull(mask_r), Con(IsNull(clamped), nn_fill, clamped))
```

`clamped` is float p_ice in [0, 1]. `EucAllocation` is a *zone* tool — it
allocates zone identifiers, so a float input is truncated to integer before
allocation. Every gap cell therefore inherits **0** (any neighbour < 1.0) or
**1** (a neighbour at exactly 1.0), never the neighbour's actual value.

## The evidence

Read `provenance_01.tif` (arcpy's own tier map, native grid) and sample
`river_ice_01.tif` at the cells it marks tier 3:

```
arcpy values at its own tier-3 (EucAllocation) cells, month 01:  73,526 cells
  distinct values:        85
  exactly 0.0:        61,753   (84.0%)
  exactly 1.0:        10,988   (14.9%)
```

For contrast, on the same raster:

```
  tier 1 (polygon median):  9,921 distinct values in a 200k sample
  tier 2 (IDW):            46,016 distinct values
```

A continuous field does not produce 85 distinct values over 73,526 cells. The
handful of non-0/1 values are bilinear bleed from the Step 7 alignment.

## What it costs

Restricted to the 86,789-cell NWN river corridor — the only cells the friction
gate reads — with the Python port supplying the true nearest-neighbour value
for comparison:

| | arcpy | true nearest |
|---|---|---|
| tier-3 corridor cells | 4,898 | 4,898 |
| exactly 0.0 | 4,880 (99.6%) | — |
| mean p_ice | **0.0005** | **0.7780** |
| below `RIVER_ICE_THRESHOLD` (0.15) | 4,894 | 4 |

**4,894 corridor cells read as open water in January that should read as
frozen.** They enter the friction build as tier-1 "measured" values, so nothing
downstream flags them — this is the ~7% of tier 1 that provenance showed coming
from the arcpy fallback.

## What validates the comparison

The same port reproduces the two stages that are not broken, on arcpy's native
grid, cell for cell:

| stage | agreement |
|---|---|
| river mask membership | 99.98% (18,802 python-only cells of 585k, boundary rasterisation) |
| tier assignment 1/2/3 | 99.58% of shared cells |
| tier 1 values (polygon median) | mean abs diff **0.0032** |
| tier 2 values (IDW, power 2 / 12 pts / 50 km) | mean abs diff **0.00065** |
| tier 3 values (EucAllocation) | mean abs diff **0.66**, 80% differ by >0.05 |

The IDW agreement is the control: a 40-line `cKDTree` reproduces arcpy's `Idw`
to 6.5e-4. The divergence is confined to the one stage.

## The fix

`arcpy-eucallocation-fix.patch` deletes the `EucAllocation` call and leaves
those cells NoData:

```python
mask_r = Raster(river_mask_ras)
final  = Con(~IsNull(mask_r), clamped)
```

Nothing replaces it, because the friction build already has a gap-filler that
is better than the one being removed: `extend_ice_nearest` (capped at
`RIVER_ICE_FILL_MAX_KM = 25 km`, clipped to the river mask) falling back to
`fill_by_nearest_median` (K = 200). This collapses two fill policies into one
and retires the unbounded one.

Expect after re-running: `river_ice_MM.tif` loses ~73k cells per winter month
to NoData, and the friction build's per-month log line shifts a corresponding
number of cells from tier 1 into tiers 2 and 3. The three-tier split
(89.5 / 5.5 / 5.1) will move — that is the fix working, not a regression.

## Caveats

- Verified on month 01 only, against the June/July 2026 arcpy output and the
  pre-marine-clip 967-polygon mask (the same inputs that run consumed).
- The port's mask carries ~3% more cells than arcpy's, from cell-centre
  rasterisation differing at polygon boundaries. This does not affect the
  tier-3 finding, which is measured inside arcpy's own mask.
- The corridor figures use the port as the source of truth for "what the
  nearest neighbour actually holds". The 85-distinct-values result does not —
  it stands on arcpy's output alone.
