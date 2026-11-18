---
name: check-route-against-surface
description: Test any vector route against any friction surface with the pipeline's own
  sampler, and diagnose WHY failing samples fail (land-cover class, sea ice, river-ice
  domain, off-grid). Use when drafting or auditing a line (barge, ice road, any mode),
  when an edge is unexpectedly impassable, or before adopting a new line source. Do NOT
  use to decide whether a hub SHOULD have a route (that is connect-nearshore-barge-hubs)
  or to alter the surface so a route passes.
---

# Check a route against a surface

A line in the network is only as good as the pixels under it: workflow 03 closes an edge
for a month when ONE 75 m sample lands on NoData. This skill is how to test any line
against any surface the way the pipeline will, and read the result correctly.

## Core invariants

1. **Use the pipeline's sampler, never an approximation.** `fuel_network.weights`
   samples segmentize-at-75 m MIDPOINTS; endpoint-based sampling disagrees at the pixel
   level. The primitives live in `fuel_network.geo_checks`; the runnable check is
   `diagnostics/01_friction_build/check_route_against_surface.py`.
2. **Test the segments the build will create**: vertices rounded to the 50 m grid
   (the default; `--whole-features` only for non-network geometry).
3. **Pick the test month by region**: July for most of the state; August or September on
   the Arctic coast. Sea-ice failures in the required month with an open shoulder month
   are SEASON, not error.
4. **Read min-over-months before diagnosing**: NoData that never clears in any tested
   month is land or missing coverage; NoData that clears in late summer is ice. The
   `--causes` output then names the input: `land_cover:<class>` (off the corridor burn),
   `sea_ice`, `river_ice_domain`, `off_grid`.
5. **Never bend the data to pass.** A failing route is moved or reported. A cause that
   implicates an input (a surface hole, a corridor gap, an ice product under-read) is a
   finding for the owner + the friction skills, not a license to edit thresholds.

## Procedure

1. Run the check:
   ```
   python diagnostics/01_friction_build/check_route_against_surface.py \
       --lines <vector> [--mode Barge] --months 6,7,8,9,10 --require 7 \
       [--require-class marine] --causes
   ```
   Monthly barge surface is the default; `--surface overland|road_base|<path>` for others.
   `--require-class marine` adds the nearshore rule (every sample on marine pixels of the
   water label) — mandatory for barge lines.
2. Read the table: `min_nodata_frac > 0` rows are land/coverage problems; rows failing
   only the required month with other months open are seasonal.
3. For failures, open the causes table and the failure-points GeoPackage
   (`outputs/diagnostics/01_friction_build/route_check_failures.gpkg`) over the surface
   in QGIS — WHERE the bad samples sit (village end? mid-line? harbour?) decides whether
   to move a vertex, reroute a leg, or report an input defect.
4. Fix and re-run until PASS, or write up why the route cannot pass.

## What NOT to do

- No threshold, mask, or surface edits to make a route pass (principle 5).
- No exception-list edits from here — the stage checks (`qa/00_check_manual_barge`) own
  the reviewed exceptions; this diagnostic always reports the raw truth.
- Not a drafting tool: it verifies geometry you already have.

## Related

- `connect-nearshore-barge-hubs` — the end-to-end procedure this check serves.
- `assign-friction-values` / `run-friction-pipeline` — where implicated input defects go.
- `fuel_network/geo_checks.py` — the shared primitives (sampling, cause classification,
  nearest-class distance, grid identity, weld distances).
