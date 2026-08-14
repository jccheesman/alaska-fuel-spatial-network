# Friction-surface pipeline 

Deterministic, reproducible construction of mode-specific monthly friction
surfaces and cost-distance edges for the Alaska bulk-fuel logistics graph.

## Inputs

All inputs are assumed preprocessed to a common CRS (EPSG:3338 — NAD83 Alaska Albers), resolution (150 m), and extent. Paths are resolved under `$RASTER_DIR` (default
`inputs/friction_rasters`, anchored to the repo root).

| Path | Description | Units |
|---|---|---|
| `slope.tif` | Per-pixel slope from FabDEM | degrees, float32 |
| `lulc.tif`  | Dynamic World modal class | int (0–8) |
| `permafrost.tif` | Near-surface permafrost extent (Pastick et al., 2015) | 0–1 or 0–100; auto-normalized |
| `sea_ice/sea_ice_{01..12}.tif` | AOOS Historical Sea Ice Atlas monthly climatology | 0–1 or 0–100; auto-normalized |
| `river_ice/river_ice_{01..12}.tif` | Brown et al. (2026) river ice phenology monthly probability | 0–1 or 0–100; auto-normalized |

Dynamic World class codes used:
`0 water, 1 trees, 2 grass, 3 flooded_vegetation, 4 crops, 5 shrub_scrub, 6 built_area, 7 bare_ground, 8 snow_ice`.

The scripts and source data that produce these inputs live in
`friction_preprocessing/`. GEE Code Editor scripts handle the
slope/LULC/permafrost/sea-ice exports; the ArcGIS Pro pipeline
`friction_preprocessing/river_ice_full_pipeline.py` produces the 12 monthly
`river_ice/*.tif`. See `friction_preprocessing/README.md` for the pipeline
details.

## Outputs

- **Friction rasters** written to
  `outputs/01_friction_build/friction_stack/`: 12 monthly
  `barge_{MM}.tif` plus a single `overland.tif`. Overland carries no
  seasonal signal (pure terrain), so it is written once and the pipeline
  samples it for all 12 months — the `(mode, month)` stack still resolves 24
  logical entries. float32, NoData = -9999, LZW-compressed.
- **`road_base.tif`** (same directory) — static land-edge friction
  `max(ROAD_FRICTION, slope_friction) × permafrost_mod` (no LULC, no water
  mask, **NoData-free by construction**). This is what the network-overlay
  sampler (`weight_network_edges.py`) reads along Road / IceRoad / Join
  edges; the mode-month rasters are kept for viz and the off-network
  WBT validation tool. Regenerate alone (seconds) with
  `python -m friction_surface.friction_surface`.
This stage produces **only the friction rasters**. Per-edge weighting of the
delivered network is a separate, downstream step (not part of
`run_friction_pipeline`): `weight_network_edges.py` samples these surfaces along
every `final_network` edge into the `edge_month_weights` table, and
`assemble_weighted_graph.py` combines those weights with the
`friction_costs.py` rates into the `edge_costs` table and the weighted graph.

## Design decisions

### LULC and permafrost are independent factors

LULC and permafrost are kept as independent factors rather than baked
together into a single matrix. LULC affects trafficability via land
cover (forest, tundra, built area, bare ground). Permafrost affects
trafficability via the engineering cost of building and maintaining
overland transport across frozen ground (frost heave, thaw settlement,
ice-rich subgrade maintenance) — a cost that is persistent year-round
at the routing scale, not strongly seasonal.

- **LULC** enters the year-round **static base**.
- **Permafrost** is a **year-round zonal modifier** looked up by IPA
  permafrost zone classification (Brown et al. 1997), with the
  Alaska-specific implementation following Jorgenson et al. (2008). The
  extent raster is the Pastick et al. (2015) 30 m near-surface permafrost
  probability (USGS ScienceBase 10.5066/F7C53HX6), resampled to 150 m:

  | Zone | Extent (p) | Multiplier |
  |---|---|---|
  | None / isolated | p < 0.10 | 1.00 |
  | Sporadic | 0.10 ≤ p < 0.50 | 1.15 |
  | Discontinuous | 0.50 ≤ p < 0.90 | 1.30 |
  | Continuous | p ≥ 0.90 | 1.50 |

  This replaces an earlier seasonal interpolation (1.0 winter → 1.40
  summer). The seasonal signal it carried was both gentle (max 1.4×) and
  geographically narrow (only activates where p > 0), and was double-
  counting the seasonal gating already done by the ice-road burn-in
  (Jan–Mar; see **Ice-road semantics**) and barge sea-ice gating.

This also reflects mode-specific reality: permafrost is irrelevant to
barge travel, so the barge mode ignores the modifier.

### NoData is the sole impassability mechanism

Impassable pixels are stored as `-9999` (the raster's nodata value), not as
a sentinel high number (`999`/`9999`). WhiteboxTools `CostDistance` treats
NoData as non-traversible and routes around it.

Applied uniformly:

- Overland over water → NoData. (The old road-bridge burn-in is retired:
  land edges are priced by sampling the separate, NoData-free
  `road_base.tif`, so river crossings on the network can never be
  accidentally severed by the overland water mask.)
- Off-season ice-road-only pixels (Apr–Dec, away from the regular road
  network) → effectively NoData via the underlying off-road tundra cost.
- Barge over land **not on the waterway network** → NoData. Barge
  navigability is `(lulc_water | waterway_mask) & ~ice` (2026-07-23):
  the rasterized waterway network (`outputs/01_friction_build/waterway_mask_150m.tif`)
  recovers rivers narrower than a 150 m pixel, which the nearest-sampled
  Dynamic World class misses — without it, 18% of final_network waterway
  edges were severed year-round. The overland water mask is unchanged.
- Barge over ice-covered water (sea-ice or river-ice probability above
  `SEA_ICE_THRESHOLD = 0.15` / `RIVER_ICE_THRESHOLD = 0.15` — the NSIDC
  ice-edge convention; see the rationale block in `friction_config.py`)
  → NoData.
  River ice is **nearest-filled** onto waterway-network cells the IDW
  product does not cover (~87% of the corridor): uncovered cells borrow
  the p_ice of the nearest covered river cell (`extend_ice_nearest`), so
  recovered tributaries freeze with their trunk stream instead of
  reading as open water year-round. Interim until the ArcGIS IDW is
  re-run over the full waterway network.

A raster represents only what the mode can actually traverse. Numeric
friction values are reserved for traversible pixels.

### Monthly barge surfaces + one static overland

Sea ice and river ice climatologies are seasonal, not binary winter/summer
events, so barge navigability is written per month (`barge_{MM}.tif`) and any
representative month can be selected downstream without rebuilding. Overland,
by contrast, is pure terrain with no seasonal signal (roads and ice roads are
priced by the network layer, not burned into the raster), so it is written
once as `overland.tif` and sampled for all 12 months. The representative
months used by the downstream edge-weighting step default to overland=June,
barge=July.

### Ice-road semantics (seasonal extension of overland)

AK ice roads are **overland packed-snow tundra routes** (North Slope /
NPR-A style), not frozen river corridors. They are modeled as a
**seasonal extension of the overland mode**, not as a separate transport
mode — and, under the network-overlay design, they are handled at the
EDGE level, not burned into any raster: `IceRoad` edges of the delivered
network sample the NoData-free `road_base.tif` with the
`ICEROAD_TIME_PENALTY = 2.0` multiplier and are hard-gated to
`ICE_ROAD_SEASON_MONTHS = {1, 2, 3}` by workflow 03's weighting stage
(`03_weight_network_edges.py`). LULC is intentionally absent from
road_base because an ice road is an engineered packed-snow surface (the
underlying wet-tundra / shrub class shouldn't add a substrate penalty on
top of the 2× seasonal slowdown). Out of season the edges are simply
impassable — the routing graph drops the seasonal connectivity without
special-casing.

Treating ice roads as an overland extension rather than a separate mode
matches their physical reality (one driver, one vehicle, drives onto the
ice-road segment from a regular road) and gives the overland surface
its meaningful monthly variation — the network topology itself shrinks
from January (full network including ice-road extensions) to July
(roads only).

Two authoritative inputs:

- `inputs/data_for_network_build/ice_roads_150m_3338/Ice_Roads.shp` —
  merged ice-road LineString network (NOS + SIRA + Alaska Trails). Enters
  the delivered network as `IceRoad` edges (workflow 02); no raster mask
  is built from it anymore.
- `inputs/bulk_fuel_data/raw/Fuel_Delivery_Method.shp` — per-community
  fuel-delivery-method dataset. Authoritative for which communities are
  ice-road served. As of 2026-06-10 only **Atqasuk** and **Nuiqsut** have
  `Fuel_Delivery_Method == "Ice Road"`. The `AsOfDate` column lets the
  loader (`friction_costs.load_ice_road_communities`) reconstruct the
  set at any historical date. (Community-level metadata is unchanged by
  the mode merge — `Delivery_Methods = "Ice Road"` remains the
  authoritative facility attribute; only the *transport graph mode* is
  now `overland`.)

See **Seasonal windows** below for the literature backing the Jan–Mar
window.

### Ice-road friction value (travel-time semantic)

For an in-season `IceRoad` edge, per-sample friction is
`max(1.0, slope_friction) * permafrost_mod` (that is road_base.tif),
scaled by `ICEROAD_TIME_PENALTY = 2.0` at the edge level. Under
travel-time semantics this means a flat, non-permafrost ice-road
segment takes ~2× as long to traverse as a highway segment. LULC is
absent because the engineered packed-snow surface, not the underlying
tundra class, is what the truck contacts; slope rides through via
`max()` so any grade is still penalized; permafrost is retained for
engineering-persistent operating cost.

Derivation: loaded ice-road max speed of 25 mph (35 km/h) at 2× minimum
ice thickness per UAF/INE 2023 [*Design and Operation of Ice Roads*][uaf-ine]
(Table 8.1, p. 8.3, sponsored by FHWA), divided by an Alaska heavy-truck
highway baseline of ~50 mph. We use the 25 mph point rather than the
strict 15 mph floating-ice limit because the AK ice roads serving Atqasuk
and Nuiqsut are overland packed-snow tundra routes, not floating ice over
deep water. The Tibbitt-to-Contwoyto Winter Road (NWT) corroborates with
a loaded limit of 25 km/h. The 15 mph floating-ice number is itself a
physics constraint — above ~70% of the critical wave speed in the ice
cover, deflection becomes asymmetric and the ice cracks.

The friction surface intentionally stays **environmental-only**. The
operational cost premium of ice-road delivery (driver wage premium, narrow
Jan–Mar window) is applied separately via
`friction_costs.BASELINE_RATES_PER_GALLON_MILE` (`IceRoad` =
$0.010/gal-mi vs `Road` = $0.0007/gal-mi; verified 2026-07-17). Under the
network-overlay design the per-mode rate is applied per **edge**, not per
pixel: final_network edges carry a `type` (Road / IceRoad / …), so
`weight_network_edges.py` samples the friction and Phase 3 applies the
matching rate — the per-pixel `surface_type` lookup that was previously
planned here is superseded. Keeping the time/cost layers separate avoids
bundling uncertain economic weights into the per-pixel friction scalar
and lets each be updated independently.

[uaf-ine]: https://aidc.uaf.edu/media/1580/ice-road-manual_final.pdf

### Seasonal windows

Two hard seasonal masks gate the routable months per mode, layered on
top of the per-pixel environmental rasters:

- **Ice road (`ICE_ROAD_SEASON_MONTHS = {1, 2, 3}`).** Based on the
  general BLM Community Winter Access Trail (CWAT) operating window for
  North Slope villages (Atqasuk, Nuiqsut, Wainwright, Utqiagvik) and
  ConocoPhillips's Alpine/NPR-A ice-road practice (nominally Jan–Apr).
  April is **excluded** because both endpoints are partial months in
  practice (CWAT opens "early January," often mid-month; closures cluster
  mid-April), and the North Slope tundra travel season has shortened from
  ~200 to ~130 days/year since the 1970s per Alaska DNR records. Revisit
  periodically. The authoritative real-time source is the [BLM NPR-A
  Weekly Weather and Tundra Travel Report][blm-npra]. Tighter regional
  analogue: Tibbitt-to-Contwoyto runs ~8–10 weeks (Feb–Mar), consistent
  with a three-month Alaska window.
- **Marine linehaul (`MARINE_LINEHAUL_SEASON_MONTHS = {6, 7, 8, 9, 10}`).**
  This is the outer **operator-activity envelope**, not the physical
  ice-free window. The regional difference between Bering/Kuskokwim
  (Jun–Oct, ~180-day window per Crowley/Vitus schedules) and Beaufort
  (~6–8 weeks, ~Jul to mid-Sep, per Foss/Lynden Arctic schedules) is
  handled per-pixel by the monthly sea-ice climatology raster against
  `SEA_ICE_THRESHOLD`. May was previously included but no operator runs
  in May — the 2026 Bethel first-arrival was early June (KYUK,
  4 Jun 2026). Communities on the Beaufort coast (Utqiagvik, Wainwright,
  Kaktovik) rely entirely on the sea-ice raster for their narrower window.

[blm-npra]: https://www.blm.gov/programs/energy-and-minerals/oil-and-gas/about/alaska/NPR-A/NPR-A-weekly-weather-and-tundra-travel-report

### Multi-modal composition (implicit-hub model)

Routes are composed as chains of single-mode edges between facilities.
Where two consecutive edges in a chain use different modes, the matching
`INTERMODAL_TRANSFER_FEES[(from, to)]` entry (in `friction_costs.py`) is
paid at the shared facility. Any facility in `connects_to` under more
than one mode acts as a hub implicitly; `friction_costs.get_hub_facilities`
returns the current hub set. Ice-road delivery to Atqasuk and Nuiqsut
now travels end-to-end on the `overland` mode (regular road from
Anchorage or Fairbanks through Deadhorse, then the in-season ice-road
extension), so no overland↔ice_road handoff is required. The
`(overland, ice_road)` transfer-fee entry in `friction_costs.py` remains
defined as a latent boundary (fee inference can still key it if a future
export produces such a handoff); no current Transfer edge uses it.

**Scope note.** Route composition / TSP optimization over the weighted graph is
**not** part of this release (it is the subject of separate work). The cost model
here provides the pieces such a router would consume: per-edge weights
(`edge_month_weights`), per-mode rates (`BASELINE_RATES_PER_GALLON_MILE`), and the
intermodal handoff fees (`INTERMODAL_TRANSFER_FEES`), with
`friction_costs.chain_cost_with_transfer_fees(legs)` as the helper for charging a
handoff at a shared hub facility.

## How to run

The friction code lives in the `friction_surface/` package and uses
relative imports, so invoke the runner as a module from the project root:

```bash
# Build the friction surface stack:
python -m friction_surface.run_friction_pipeline

# Post-build QA on the friction stack:
python -m friction_surface.qa.qa_friction_stack

# Build just the surface stack directly (numpy/rasterio only):
python -m friction_surface.friction_surface
```

The friction stage reads only the preprocessed input rasters and writes the
friction TIFs — no DuckDB database is required. Sampling those surfaces onto the
network happens later via `weight_network_edges.py` (see the repo-root
`README.md`).

## Configuration

All input/output locations resolve through `friction_paths.py`. Defaults are
anchored to the repo root (the parent of the `friction_surface/` package) as
**absolute** paths, so resolution does not depend on the process working
directory. Any of these environment variables overrides its default; a
relative override is resolved against the current CWD.

| Env var | Overrides | Default (relative to repo root) |
|---|---|---|
| `RASTER_DIR` | Preprocessed input rasters (`slope.tif`, `lulc.tif`, `permafrost.tif`, `sea_ice/`, `river_ice/`) | `inputs/friction_rasters` |
| `FRICTION_DIR` | Friction-stack output dir | `outputs/01_friction_build/friction_stack` |
| `NETWORK_DIR` | Network vector shapefiles | `inputs/data_for_network_build` |
| `INPUTS_DIR` | Ice-road / fuel-delivery datasets | `inputs` |
| `OUTPUTS_DIR` | Outputs root (waterway mask lives under `outputs/01_friction_build/`) | `outputs` |
| `VECTOR_DIR` | Misc vector data | `vectors` |


`friction_paths` has **no import-time side effects**: the old chdir into
the repo root is gone (every consumer anchors its paths absolutely), so
scripts run correctly from any working directory.

Dependencies are declared once, in the repo-root `pyproject.toml`
(`uv venv && uv sync && uv pip install -e .`).

## Runtime expectations

Building the surface stack (14 rasters on disk backing 24 logical
`(mode, month)` entries @ 150 m) takes a few minutes on commodity hardware.

If memory becomes a bottleneck, `build_mode_friction` accepts a `window`
argument for tile-based processing; this is off by default.

## Module map

`friction_surface/` is the repo's **config + surface-builder core**, not a
standalone distributable: root-level modules (`build_corridor_masks.py`,
`weight_network_edges.py`, `assemble_weighted_graph.py`, `pipeline.py`) import
*from* this package. The friction-build entry point
`run_friction_pipeline.py` uses `pipeline.py` (logging + path resolution) from
the repo root, so it is invoked as a module from there.

**Library** (imported by other code — the public surface is re-exported from
`friction_surface/__init__.py`):

| File | Purpose |
|---|---|
| `friction_surface.py` | Raster reclassifications and the friction-stack writer (`write_friction_stack`, `build_mode_friction`). Pure numpy / rasterio. Builds 14 files on disk (1 `overland.tif` + 12 `barge_MM.tif` + `road_base.tif`) backing 24 logical `(mode, month)` entries. |
| `friction_config.py` | Single source of truth for friction constants (CRS, resolution, thresholds, multipliers, seasonal windows, delivery-method → mode maps). |
| `friction_costs.py` | Cost-per-gallon-mile rates, intermodal transfer fees, hub/community helpers. Kept **separate** from friction — cost is never folded into the environmental surface. |
| `friction_paths.py` | Env-overridable path construction, anchored to the repo root (no dependence on the process CWD). |
| `friction_io.py` | Raster/vector I/O helpers used by the surface builder. |
| `friction_preflight.py` | Input-raster validation (grid alignment, value ranges) used before a build. |

**Scripts / entry points** (run, not imported):

| File | Purpose |
|---|---|
| `run_friction_pipeline.py` | Friction-build entry point. Input validation, surface build, summary printout. (Thin driver: `workflows/01_friction_build/02_build_friction_stack.py`.) |
| `check_grid_exports.py` | One-off gate: verify re-exported inputs sit on the canonical full-Alaska grid. |
| `qa/*`, `friction_preprocessing/*` | Post-build QA and upstream data prep (see **Subdirectories**). Figure generators live in `workflows/01_friction_build/viz/`. |

## Subdirectories

| Path | Purpose |
|---|---|
| `friction_preprocessing/` | Upstream pipelines that produce the inputs: GEE Code Editor scripts (slope, LULC, permafrost, sea ice) and the ArcGIS Pro river-ice pipeline. Source hydrography lives in `friction_preprocessing/data/`. |
| `../../inputs/friction_rasters/` | Inputs consumed by this stage: `lulc.tif`, `slope.tif`, `permafrost.tif`, and the monthly `sea_ice/` and `river_ice/` stacks (regenerable-only — see `EXTERNAL_DATA.md`). |
| `../../outputs/01_friction_build/` | Generated friction stack in `friction_stack/` — 14 files (`overland.tif`, `barge_{MM}.tif`, `road_base.tif`) backing 24 logical `(mode, month)` entries — plus the waterway mask. |
| `../../workflows/01_friction_build/viz/` | Visualization generators — `plot_friction_stack.py` (3×4 monthly raster grid PNG), `generate_grid_schema.py` (cell-by-cell schematic PNG), `generate_pipeline_diagram.py` (two-page PDF, committed at `outputs/figures/`). |
| `qa/` | Post-build QA scripts — `qa_friction_stack.py` (hard checks on the friction stack) and `qa_river_ice_thresholds.py` (river-ice threshold histogram diagnostic). |
| `../../tests/` | Pytest suite — `test_friction_surface.py`, `test_friction_paths.py`. Run with `pytest` from the project root. |
