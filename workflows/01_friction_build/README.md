# Workflow 01 — friction-layer build (act a)

Builds the monthly environmental friction surfaces for Alaska on the
canonical 150 m EPSG:3338 grid (contract: `docs/DATA_CONTRACTS.md` §1–2).

## Run order (the corridor-mask step is NOT optional)

```bash
python 00_preflight_inputs.py       # grid + range gates on inputs/friction_rasters
python 01_build_corridor_masks.py   # -> waterway_mask_150m.tif + waterway_river_mask_150m.tif
python 02_build_friction_stack.py   # -> outputs/01_friction_build/friction_stack/ (14 TIFs)
python 03_qa_friction_stack.py      # 14-file contract, ice gating, value floor
# or: bash run_all.sh
```

Step 01 emits TWO masks. `waterway_river_mask_150m.tif` is the freshwater-river
subset (24 reviewed NWN segments, 86,789 cells, 17.3% of the corridor) and is
the ONLY domain in which river ice may gate a barge pixel; everything else on
the network is salt water, gated by the sea-ice climatology alone. Both masks
come out of one pass over one shapefile with one buffer, so they cannot drift
apart, and stage 02 hard-errors if the river mask is absent. Without it the
nearest-neighbour fill smears interior river ice onto the marine network and
closes the Gulf of Alaska, the Inside Passage and Kodiak every winter — see
`docs/TEST_LOG.md` (2026-08-20) and the regression gate
`qa_friction_stack.check_year_round_ports`.

Skipping step 01 now FAILS the build: `write_friction_stack` raises a
hard error when the waterway mask is absent, because a maskless build
severs ~18% of waterway edges — quietly wrong output a public pipeline
must catch. (The old behavior was a warning, and the old README omitted
the step entirely; both were documented bugs.) The escape hatch for
synthetic/research runs is `--allow-missing-waterway-mask` on stage 02
or `FRICTION_ALLOW_MISSING_WATERWAY_MASK=1`.

## Inputs

`inputs/friction_rasters/` (not in the repository; download and regenerate)
and the waterways shapefile unzipped from `inputs/data_for_network_build.zip`.
What the rasters are, where they come from, and the Earth Engine, padding,
alignment and river-ice steps that produce them: `DATA.md` §1.4 and §3.1.

## Outputs

`outputs/01_friction_build/`: `waterway_mask_150m.tif` +
`waterway_river_mask_150m.tif` +
`friction_stack/{overland.tif, road_base.tif, barge_01..12.tif}` — consumed by
workflow 03's weighting stage. Knobs: `source_scripts/friction_surface/friction_config.py`
(single source of truth). Figure generators: `viz/`.
