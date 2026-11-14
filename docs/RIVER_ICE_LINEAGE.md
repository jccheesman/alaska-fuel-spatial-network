# River ice: raw data to visualization

End-to-end lineage of the river-ice signal, as it stands after the marine-leak
fix (2026-08-20) and the removal of the arcpy nearest-neighbour fill
(2026-08-21). Each stage covers what it does, why it is built that way, every
tunable value, and what it hands to the next stage.

Three things to hold onto before reading.

**The source product measures open water, not ice.** Ice is its complement,
which is why NoData and zero must never be conflated — they are opposite
claims, and conflating them is what caused both of this month's defects.

**Measurement and inference are now separated by stage.** Stage [2] (arcpy)
writes a value only where it has one — a polygon median or an IDW estimate
within 50 km of a reach point — and leaves everything else NoData. All
extrapolation happens in stage [5] (numpy), under a distance cap. Until
2026-08-21 stage [2] had a third, unbounded fill of its own; it filled
73,526 cells per winter month with a truncated p_ice of 0 or 1, and those
cells then entered stage [5] disguised as measurements. There is now **one
fill policy in the chain, and it is the capped one.**

**Two domains, nested but not neatly.** Stage [2] produces values across the
Brown river mask; stage [5] consumes them across the NWN waterway corridor.
The corridor is roughly a tenth the size — but 8,817 of its cells fall
*outside* the Brown mask entirely and can never carry a measured value. See
"The two domains" before stage [5].

Rows marked **NEW** did not exist before the fix. Diagnosis is in
`docs/TEST_LOG.md` (2026-08-20 and 2026-08-21); the truncation defect has its
own write-up in `docs/FINDING_eucallocation_truncation.md`; the operational
runbook is `docs/RERUN_river_ice_fix.md`.

```
Brown reach points ─┐
                    ├─► [1] mask geometry ─► [2] IDW ─► [3] pad ─► [5] three-tier gate ─► barge_MM.tif
NHD (NHDArea,       ┘        geopandas       arcpy      rasterio        numpy/scipy            │
     NHDFlowline)                                                            ▲                 │
                                                                             │                 ▼
NWN waterway network ──────────────────────► [4] corridor masks ─────────────┘          [6] QA gate
                                                geopandas + rasterio                           │
                                                                                               ▼
                                                                            [7] edge weights ─► [8] figures
```

---

## [0] Source data

| dataset | source | size | contents |
|---|---|---|---|
| `waterFilledMedians2000_2023.geojson` | Brown et al. 2026, [10.18739/A2SB3X15X](https://doi.org/10.18739/A2SB3X15X), CC0 | 9.6 MB | ~31,745 reach-point observations; fields `ReachID`, `month`, `areaPropMedWater`; 30 named rivers |
| `NHD_H_Alaska_State_Shape.zip` | USGS National Map | 5.2 GB | `NHDArea.shp` (polygons) + `NHDFlowline_{0..6}.shp` |
| `waterways_network_ak_albers.shp` | USACE National Waterway Network extract | 1.4 MB | 320 line features, EPSG:3338 |

Only the third is committed (inside `inputs/data_for_network_build.zip`). The
first two are regenerable-only — see `EXTERNAL_DATA.md`.

**What the Brown product actually measures.** Not ice. It reports
`areaPropMedWater` — the median proportion of a river reach's area that was
*open water* in satellite imagery, per reach per month, over 2000–2023.
Ice probability is inferred as its complement in stage [2]. That inversion is
the reason a NoData cell must never be written as 0: zero open water and no
observation are opposite claims.

The 30 rivers Brown sampled are the ceiling on how much of Alaska can ever have
measured river ice. Everything outside them is inference, which is what makes
stage [5]'s tier accounting necessary.

---

## [1] Mask geometry

**Tool:** `source_scripts/friction_surface/friction_preprocessing/build_brown_polygon_mask.py`
— local Python, `geopandas`. Needs `PYTHONPATH` reaching `source_scripts`.

**Flowlines.** `NHDFlowline_{0..6}` filtered by `GNIS_Name ∈ BROWN_RIVER_NAMES`
(30 rivers, hardcoded). → **17,864 lines, 14,123 km**, reprojected to EPSG:3338,
written with `gnis_name` + geometry only.

**Polygons.** `NHDArea` filtered to `NHDAREA_KEEP_FTYPES = [460, 364]`
(StreamRiver, Lake/Pond), then selected by the **union** of two criteria:

| knob | value | effect |
|---|---|---|
| `--point-buffer-m` | **2,000 m** | polygon intersects a buffered Brown reach point |
| `--flowline-buffer-m` | **500 m** | polygon intersects a buffered Brown flowline |

Why a union and not an intersection: the two criteria fail in different
places. Reach points sit wherever the satellite record had a usable
observation, so criterion (a) finds polygons the centerline misses — including
off-centerline channels in a braided floodplain. Criterion (b) finds polygons
the centerline passes through but where no reach point happens to land. Either
alone leaves holes; the docstring is explicit that the union is what gives
usable coverage.

Each polygon carries exactly one `gnis_name` label. Where both criteria fire,
the reach-point name wins — it is the one tied to actual data — and the
flowline name is the fallback. The label is provenance only; nothing
downstream routes on it, which is how a polygon in Chatham Strait ended up
labelled "Porcupine River" without anything complaining.

**NEW — marine clip.** `drop_marine_polygons()` removes any polygon
intersecting an NWN segment whose `KEY_ID` is **not** in
`friction_config.RIVER_SEGMENT_KEY_IDS`. `ftype 364` is not always a lake, and
a polygon enters the mask *whole* if any part of it reaches the buffer:

| labelled | ftype | km² | actually |
|---|---|---|---|
| Stikine River | 364 | 225.1 | Dry Strait / Stikine delta front |
| Porcupine River | 364 | 141.0 | Chatham/Peril Strait, ~1,100 km away |
| Kenai River | 364 | 4.8 | Kenai mouth into Cook Inlet |
| Kuparuk River | 364 | 0.5 | — |

The clip is deliberately narrow. Dropping `ftype 364` wholesale would lose
1,130 km² including legitimate in-line lakes (Skilak on the Kenai is why 364
was admitted at all). Dropping the flowline-derived half instead — provably
free of marine cells — would cost 9,661 river cells of coverage, concentrated
on the Kuskokwim, Koyukuk and Kobuk, whose nearest surviving coverage is
21–35 km away and therefore past stage [5]'s fill cap. Removing four polygons
costs 315 river cells and takes the marine contamination from 396 to 2.

**Output:** `brown_river_polygons.shp` — **963 polygons, 9,577 km²** (was 967 /
9,948); `brown_river_flowlines.shp` — 17,864 lines, unchanged by the clip.
Escape hatch: `--no-marine-clip` reproduces the pre-fix mask for comparison.

---

## [2] Interpolation to a raster

**Tool:** `river_ice_full_pipeline.py` — **ArcGIS Pro `arcpy`**, Windows only,
Spatial Analyst extension. `PROJECT_ROOT` is overridable via the
`FRICTION_LAYER_ROOT` env var rather than editing the file.

### Environment

`setup_environment()` pins EPSG:3338, `cellSize = 150`,
`parallelProcessingFactor = "75%"`, Z/M disabled, pyramids off, and routes all
intermediates through ArcGIS's auto-managed scratch GDB. That last one is not
cosmetic — writing intermediates next to a Pro project on OneDrive produces
file locks that fail the run halfway.

### Reach values

```
p_ice = clamp(1 − areaPropMedWater, 0, 1)
```

taken as the **median across the three Brown periods** (early / middle / late),
then aggregated to a **median per `(ReachID, month)`**. Median rather than mean
throughout: reach observations are sparse and skewed, and one anomalous
period should not move a reach's freeze signal. Points are then deduplicated to
**one representative feature per `ReachID`**, with the per-month value joined
back — so each reach contributes one location, not one per observation.

### The river mask

Built once, before any interpolation:

```
river_mask = NHDArea polygons  ∪  Buffer(NHDFlowline, FLOWLINE_BUFFER_M = 200 m)
```

combined with `Con(IsNull(buffer), polygons, buffer)`, rasterized at 150 m, and
then wired into **`arcpy.env.snapRaster` and `arcpy.env.mask`**. From that point
every raster operation in the pipeline is both aligned to and clipped by the
river network. This is the single most consequential line in the file: whatever
is inside this mask gets a real interpolated value, salt water included, which
is exactly what the marine clip in [1] exists to prevent.

### Per-month fill — two stages, with provenance

**Data months** (`DATA_MONTHS = [1,2,3,4,5,6,9,10,11,12]`) get a two-stage
spatial fill. Cells neither stage can reach are **left NoData on purpose**:

| stage | operator | covers | knobs |
|---|---|---|---|
| 1 | `ZonalStatisticsAsTable` — per-polygon median | wide rivers, where a polygon holds several reach points | — |
| 2 | `Idw` | narrow rivers and gaps between polygons | `IDW_POWER = 2`, `IDW_NUM_POINTS = 12`, `RadiusVariable(12, 50 km)` |
| — | *nothing* | everything else inside the mask stays NoData, for [5] to fill under its cap | — |

Values are clamped to [0,1] after stage 2:
`final = Con(~IsNull(river_mask), clamped)`.

**CHANGED 2026-08-21 — the third stage was removed.** It read
`nn_fill = EucAllocation(clamped)`. `EucAllocation` is a *zone* tool: a float
input is truncated to integer before allocation, so every cell it filled
inherited **0** (any neighbour below 1.0) or **1** (a neighbour at exactly
1.0), never the neighbour's actual p_ice. Measured on the January output:

| | |
|---|---|
| cells the stage filled | 73,526 |
| distinct values among them | **85** |
| exactly 0.0 | 61,753 (84.0%) |
| exactly 1.0 | 10,988 (14.9%) |
| for contrast — tier 1 distinct values (200k sample) | 9,921 |
| for contrast — tier 2 distinct values | 46,016 |

Of those, **4,894 sat on the NWN corridor and read as open water in January**,
arriving in [5] as tier-1 *measured* values where nothing flags them. Nothing
replaced the stage, because [5] already fills those cells under a 25 km cap the
arcpy one never had. Re-adding any upstream fill puts two fill policies back on
nested domains, which is the shape of both defects found this month.

Each month also writes **`provenance_MM.tif`**: **1 = polygon-median,
2 = IDW, 3 = no source here — left NoData for [5]**. Class 3 has changed
meaning: it used to mark cells arcpy had filled, and now marks cells arcpy
deliberately did not. It remains a per-pixel audit trail of measured versus
inferred, upstream of and separate from the tier accounting in [5]. This one
records coverage *within the Brown mask*; [5] fills *within the waterway river
corridor*, using this raster's footprint as its ground truth.

**Summer months** (`SUMMER_MONTHS = [7, 8]`) are **not interpolated at all**.
They are written as a constant **0.0** everywhere inside the river mask —
Alaskan rivers are ice-free in July and August, and asserting that directly is
more honest than interpolating a field that is uniformly zero.

### Alignment

`align_to_canonical_grid()` snaps the twelve outputs to `lulc.tif`
(`snapRaster`, `extent`, `cellSize` all set from it, `mask` cleared so
alignment is not clipped). `_load_ice` in [5] requires inputs already on the
canonical grid — there is no WarpedVRT fallback — so a missing `lulc.tif` here
means a warning now and a preflight failure later. `provenance_*.tif` is
**intentionally not aligned**: it is a diagnostic, not a pipeline input.

**Output:** `<PROJECT_ROOT>/AK_Stack_150m/river_ice_{01..12}.tif` +
`provenance_{01..12}.tif`, 150 m, EPSG:3338.

---

## [3] Pad to the canonical grid

**Tool:** `pad_river_ice_to_grid.py` — `rasterio`. Lossless window insert, not
a resample: the ArcGIS window is an exact sub-window of the canonical lattice.

| property | value |
|---|---|
| canonical grid | **28,001 × 16,567**, 150 m, EPSG:3338 |
| origin (top-left) | −2,130,150 , 2,595,450 |
| fill outside the window | **−9999**, not 0 |

The ArcGIS window is narrower than the canonical grid because Brown's rivers
are interior — there are no freezing rivers in the western Aleutians or the
Southeast panhandle, so the IDW never needed to cover them. Because the window
shares the canonical origin and 150 m lattice exactly, bringing it to full
extent is an integer offset insert, not a resample: no resampling error, no
interpolation across the seam.

The fill value is load-bearing and easy to get wrong. `0` means "river present,
ice-free this month"; `−9999` means "no product here". `_load_ice` in [5] maps
NoData to 0.0 at read time anyway, so the two look identical downstream — but
writing literal 0 would bake the claim into the raster itself, asserting
ice-free rivers across regions that have no rivers. The archive copies stay in
`small_grid/`; nothing is moved or deleted.

**Output:** `inputs/friction_rasters/river_ice/river_ice_{01..12}.tif`

---

## [4] Corridor masks

**Tool:** `workflows/01_friction_build/01_build_corridor_masks.py` —
`geopandas` + `rasterio.features.rasterize`, `all_touched=True`, buffer
`CORRIDOR_BUFFER_M = 75 m`, snapped to `lulc.tif`.

| output | cells | what |
|---|---|---|
| `waterway_mask_150m.tif` | 501,684 | all 320 NWN segments |
| **NEW** `waterway_river_mask_150m.tif` | **86,789 (17.3%)** | 24 reviewed freshwater segments |

The river subset comes from `select_river_segments()`, which selects by the
frozen allowlist `RIVER_SEGMENT_KEY_IDS` — **not** a live predicate. No single
NWN attribute survives contact with the table: `GEO_CLASS == "I"` admits Cook
Inlet and the Inside Passage; `WTWY_TYPE == 6` admits Norton Sound; `RIVERNAME`
misses 451 km of the lower Yukon (filed as "NORTON SOUND"); `LINKNAME` admits
Drift River Platforms, an oil terminal.

The 75 m buffer is half a pixel — enough to guarantee the rasterized line is
connected at 150 m without widening the corridor into surrounding land.
`all_touched=True` means any pixel the buffered line clips is included, which
is what recovers rivers narrower than a single 150 m cell. Without the waterway
mask entirely, roughly 18% of `final_network` waterway edges are severed
year-round, which is why stage 02 hard-errors when it is absent.

A name heuristic still runs as a **drift detector** — `STATE == "AK"` and
`RIVER|CREEK` as a whole word in either `RIVERNAME` or `LINKNAME`. It selects
nothing; it only has to agree. If its candidate set stops matching
`allowlist ∪ RIVER_SEGMENT_REJECTED`, the build raises and names the
difference, so a re-extracted NWN forces a re-audit rather than silently
shifting the split. `RIVER_SEGMENT_REJECTED` keeps the four reviewed
exclusions as data with their reasons, so a known rejection reappearing is
distinguishable from a genuinely new segment.

Both masks come from one pass over one shapefile with one buffer, so the river
mask is guaranteed a strict subset — `friction_surface` asserts this at load
time and raises if the two ever drift apart.

---

## The two domains

Stage [2] and stage [5] work on different footprints, and the relationship is
the thing to have straight before reading the tier table.

| | cells | built from |
|---|---|---|
| Brown river mask — where [2] can produce values | 1,004,288 | NHDArea polygons ∪ 200 m flowline buffer |
| NWN river corridor — where [5] applies the gate | 86,789 | 24 reviewed NWN segments, 75 m buffer |
| in both | 77,972 | |
| Brown only — measured, but no barge route through it | 926,316 | |
| **corridor only — outside the Brown mask entirely** | **8,817** | |

The corridor is about a tenth of the Brown mask, not larger. But the last row
is why [5] needs tiers at all: 8,817 corridor cells have no river-ice product
underneath them at any resolution and can never be tier 1, no matter how well
[2] runs.

**The fill pool and the fill target are different sets.** A corridor cell with
no value of its own looks outward into the *whole* Brown mask for a covered
neighbour — not just into the corridor. That is why the 25 km cap is the
load-bearing constant: without it the search is over a 1-million-cell surface
spanning the state, and it will always find something.

One consequence of the 2026-08-21 change: removing the arcpy fill shrinks the
**pool** as well as reclassifying the target. About 73k cells per winter month
that used to hold a value now hold nothing, so some corridor cells that
previously found a covered neighbour within 25 km will now fall through to
tier 3. That is expected, and it is the mechanism behind the predicted tier
shift below.

---

## [5] The three-tier gate

**Tool:** `source_scripts/friction_surface/friction_surface.py` — `numpy`,
`scipy.spatial.cKDTree`, `rasterio`.

`_load_ice()` normalizes: source NoData → 0.0, auto-divide by 100 if max > 1,
clip to [0,1]. It also returns `river_ice_cov`, the footprint of real values,
read **before** NoData collapses to 0.

Every tier is confined to `river_domain` = the river mask from [4].

| tier | rule | cells | share |
|---|---|---|---|
| 1 | IDW value where `river_ice_cov` is true | 77,657 | 89.5% |
| 2 | `extend_ice_nearest` — nearest covered cell, bounded | 4,734 | 5.5% |
| 3 | **NEW** `fill_by_nearest_median` — median of the k nearest | 4,398 | 5.1% |

**These counts are pre-2026-08-21** — measured against a river-ice raster that
still carried the arcpy fill. They will move once [2] is re-run: tier 1 should
shed roughly 4,900 corridor cells (the ones the arcpy stage used to invent),
with tiers 2 and 3 absorbing them — about five points out of tier 1. Those
cells go from p_ice near 0 to near 0.78, so **more** river cells block in
winter, not fewer. Marine sites are untouched; [6] must still pass 12/12 on all
eight Gulf/SE ports. Check the rebuilt numbers against this prediction rather
than accepting whatever comes out.

| constant | value | why |
|---|---|---|
| `RIVER_ICE_FILL_MAX_KM` | **25.0** | = 166.67 px at 150 m, passed as `distance_upper_bound`. Unbounded, the fill reached 227 km across watersheds |
| `RIVER_ICE_FALLBACK_K` | **200** | ~4.5 km² of river surface — robust to one anomalous reach, stays inside one drainage |
| `RIVER_ICE_THRESHOLD` | **0.15** | NSIDC ice-edge convention, shared with sea ice |
| `SEA_ICE_THRESHOLD` | 0.15 | same |
| `WATER_FRICTION_BARGE` | 1.0 | ice-free open-water baseline |
| `FRICTION_NODATA` | −9999.0 | the sole impassability mechanism |

**Tier 2** is `scipy.spatial.cKDTree.query(..., distance_upper_bound=166.67)`.
The bound is what separates two behaviours that shared one name: a Yukon cell
borrowing from 1.5 km downstream is interpolation; Ugashik borrowing from
149.6 km and "Dahl Creek" from 227.5 km is fabrication across watersheds.
Misses return `inf` and index `len(src)`, which is how the function knows which
cells to hand to tier 3. The index map is memoized on
`(coverage.sum(), target.sum(), bound)` — the river-ice footprint is nearly
month-invariant (months 1 and 4–11 share one, 2/3/12 differ slightly), so the
KD-tree is rebuilt about five times per twelve-month run rather than twelve.
Observed tier-2 median borrow: **1.17 km**.

**Tier 3** takes the median of the `k` nearest covered cells. Geography bounds
it on both axes, with no band to fall out of. It must stay k-nearest: a
latitude band was tried first and shipped Egegik navigable in January, because
its ±0.75° band held only Taku, Stikine and a mislabelled "Porcupine" polygon —
Southeast rainforest rivers 1,200–1,400 km east — while Kvichak (58.88N) and
Nushagak (59.0N) sat just above its ceiling. Alaska's freeze gradient is not
north-south enough for a band to be safe. Verified source selection after the
change: Egegik draws 100% from Nushagak/Kvichak at 89 km, Ugashik 100% at
149 km, "Dahl Creek" 85% from Buckland at 228 km.

Tier 3 is not a smaller version of tier 2. Tier 2 copies one cell; tier 3 takes
a median of many, because at that range no single cell is credible and the
question shifts from "what is this reach doing" to "what does this region do".

**The gate**, in `build_mode_friction`:

```python
nav_water    = water_mask | (waterway_mask == 1)      # LULC water OR the corridor
river_blocked = river_ice_present & river_domain       # NEW: clipped to rivers
navigable    = nav_water & ~(sea_ice_present | river_blocked)
out[navigable] = WATER_FRICTION_BARGE                  # else FRICTION_NODATA
```

`nav_water` is the union of LULC water and the rasterized corridor, so a river
too narrow for a 150 m LULC pixel is still navigable. `FRICTION_NODATA` is the
sole impassability mechanism — there is no sentinel value, and WhiteboxTools
cost-distance routes around NoData — so "blocked" and "no data" are the same
thing to everything downstream. That is why the NoData discipline in [3]
matters so much.

The `& river_domain` clip is **not** redundant with the tier restriction, and
the distinction is worth holding onto. The tier restriction stops river ice
being *copied* onto salt water. The gate clip stops river ice that is *already
there* — the 396 marine cells carrying genuine IDW values out of [2] — from
being read. Remove the first and 288,954 cells close in February; remove the
second and 396 do, including Dry Strait and the Petersburg approach. Different
failures, different mechanisms, both live.

**Output:** `outputs/01_friction_build/friction_stack/barge_{01..12}.tif`

---

## [6] QA gate

**Tool:** `source_scripts/friction_surface/qa/qa_friction_stack.py`

`check_year_round_ports()` — `PORT_PROBE_HALF_M = 2,000 m`, counts **waterway
cells**, not any water pixel. Three tripwire groups, each guarding a different
way to break the gate:

| group | sites | rule |
|---|---|---|
| `ICE_FREE_PORTS` | Ketchikan, Sitka, Juneau, Petersburg, Kodiak, Seward, Valdez, Whittier | navigable **12/12 months** |
| `SEASONAL_PORTS` | Nome, Utqiagvik | open in August, closed in February |
| `FREEZING_RIVERS` | Yukon @ Galena, Kuskokwim @ Aniak, Yukon @ Holy Cross, Egegik River | open in August, closed in February |

The first catches river ice leaking onto salt water. The second and third stop
anyone "fixing" such a failure by disabling ice gating altogether.

`FREEZING_RIVERS` is chosen to exercise **one site per tier**, so a regression
in any single tier is caught:

| site | coverage | exercises |
|---|---|---|
| Yukon @ Galena | 59/59 cells IDW-covered | tier 1, the raw product |
| Kuskokwim @ Aniak | 64/64 covered | tier 1 |
| Yukon @ Holy Cross | 78 river cells, 0 covered | tier 2, nearest-fill |
| **Egegik River** | 10 river cells, 0 covered | **tier 3**, k-nearest median |

Egegik is the important one — no coverage and nothing within 25 km, so it can
only be reached by tier 3. It has already caught one regression (the latitude-
band fallback). Against the pre-fix stack the whole check reports 8 failures.

---

## [7] Edge weighting

**Tool:** `workflows/03_multimodal_join/03_weight_network_edges.py`

Waterway edges are densified and sampled point-by-point against
`barge_MM.tif`. **Strict rule: any NoData sample ⇒ the edge is impassable that
month.** An edge with a single frozen pixel anywhere along it is severed
entirely — no partial-cost path. `nodata_frac` is nonetheless recorded per
edge-month, so a 2%-blocked edge and a 100%-blocked edge remain
distinguishable after the fact even though both are impassable.

The strict rule cuts both ways. It means the friction stack cannot quietly
route a barge through a frozen reach, and it means an edge spanning both
covered and uncovered river stretches still dies on the covered part — which
is why cell-level improvements do not translate one-for-one into edge-level
ones. Land edges are immune by construction: `road_base.tif` is NoData-free,
so a DEM hole can never sever a road.

34,099 Waterway edges × 12 months → `edge_month_weights` (1,091,052 rows total
across all classes), then `edge_costs`, in `outputs/fuel_network.duckdb`.

**Read passability by length, not by count.** The two metrics disagree by a
factor of seventeen in February and the count version is the misleading one:

| | edges | total km | mean centroid |
|---|---|---|---|
| passable, Feb | 1,024 | **16,362** | 57.73N 138.15W (Gulf of Alaska) |
| blocked, Feb | 33,075 | 15,634 | 64.46N 154.58W (interior) |

The interior river network is chopped into tens of thousands of short edges
while the Gulf marine routes are a few hundred long ones, so edge *count* is
really a measure of where the graph is dense, not where barges can go. The
passable set carries more total kilometres than the blocked set. By count
February reads 0.030; by length, 0.511 — which matches the 57.6% of waterway
*cells* open that month, as it should.

---

## [8] Visualization

**Tool:** `diagnostics/01_friction_build/plot_river_ice_marine_leak.py` —
`matplotlib` (Agg), `rasterio`, `scipy.ndimage.binary_dilation`, `pyproj`.

Classifies every waterway cell for a target month into navigable / blocked-real
/ blocked-leak. The leak test: a cell is spurious if it is blocked, on salt
water, and off-network open water within `PROBE_RADIUS_PX` is navigable that
month — sea ice cannot explain it. **On a correct stack the leak class is
empty**; pre-fix it held 288,954 cells in February.

| knob | value |
|---|---|
| `PROBE_RADIUS_PX` | 7 (≈1 km at 150 m) |
| `DECIMATE` | 6 (backdrop downsample) |
| `ROW_CHUNK` | 3,000 rows — keeps peak memory in the hundreds of MB, not ~25 GB |
| palette | `#2a78d6` navigable · `#4a3aa7` blocked-real · `#d03b3b` blocked-leak |

The palette is validated, not chosen by eye: worst all-pairs CVD ΔE 13.0,
normal-vision ΔE 16.3, all ≥ 3:1 on the `#fcfcfb` surface.

```bash
python diagnostics/01_friction_build/plot_river_ice_marine_leak.py --month 2
```

### The other diagnostic: fill provenance

`friction_preprocessing/plot_river_ice_provenance.py` — **runs inside ArcGIS
Pro's `arcgispro-py3`**, not the project venv, because it reads the
`provenance_MM.tif` rasters from [2] with `arcpy`. Three panels (Jan / Apr /
Oct) coloured 1 = polygon-median green, 2 = IDW blue, 3 = orange.

**The orange class now means the opposite of what it did.** Before 2026-08-21
it marked cells arcpy had filled by nearest-neighbour allocation; it now marks
cells arcpy deliberately left NoData for [5]. The legend text in that script
still says "NN-fallback" and should be re-read as "no source — deferred to the
friction build". Any figure generated before 2026-08-21 carries the old
meaning.

This answers a different question from the leak figure. The leak figure asks
*is the gate wrong*; the provenance figure asks *how much of the river-ice
product is measured rather than inferred*, at the arcpy stage — before the
waterway corridor is even involved. Read them together and you can tell a
tier-3 cell that had no upstream source at all from one fed by a stage-1
polygon median.

**Figures in `outputs/analysis/`:**

| file | shows |
|---|---|
| `river_ice_marine_leak.png` | February classification map + 12-month curve |
| `river_ice_coverage_gap.png` | the cells outside the IDW, by river |
| `waterway_river_mask.png` | the river/marine split, with SE Alaska and Bristol Bay insets |
| `brown_flowlines_and_polygons.png` | the [1] geometry, with the 4 marine polygons flagged |

**Tables:** `waterway_river_marine_classification.csv` (all 320 NWN segments),
`nwn_vs_brown_flowlines.csv` (NHD cross-check).

---

## Where a value lives

Everything tunable is in `source_scripts/friction_surface/friction_config.py`
except:

| value | lives in |
|---|---|
| 2,000 m / 500 m polygon-join buffers | `build_brown_polygon_mask.py` argparse defaults |
| `FLOWLINE_BUFFER_M = 200` | `river_ice_full_pipeline.py` |
| `IDW_POWER = 2`, `IDW_NUM_POINTS = 12`, `IDW_MAX_DIST_M = 50000` | `river_ice_full_pipeline.py` |
| `DATA_MONTHS` / `SUMMER_MONTHS` | `river_ice_full_pipeline.py` |
| `PROJECT_ROOT` | `FRICTION_LAYER_ROOT` env var, or the literal fallback |
| `BROWN_RIVER_NAMES` (30 rivers) | `build_brown_polygon_mask.py` |
| canonical grid | `lulc.tif`, read as the reference profile |
| `PROBE_RADIUS_PX`, `DECIMATE`, palette | `plot_river_ice_marine_leak.py` |

---

## Change log

| date | change | effect |
|---|---|---|
| 2026-08-20 | river-mask clip on the fill target and on the gate; 25 km cap; k-nearest tier 3 | 288,954 cells stop blocking in February; Gulf and Inside Passage open year-round |
| 2026-08-20 | marine clip in `build_brown_polygon_mask` | 4 polygons, 371.3 km², removed from the IDW mask |
| 2026-08-21 | `EucAllocation` removed from `river_ice_full_pipeline` | ~4,900 corridor cells stop reading as open water in January; one fill policy instead of two |

The 2026-08-21 change is **applied to source but not yet run** — it needs the
ArcGIS machine. Until then the shipped `river_ice_MM.tif` rasters still carry
the truncated values, and stage [5]'s river-mask clip is what keeps them from
doing damage.
