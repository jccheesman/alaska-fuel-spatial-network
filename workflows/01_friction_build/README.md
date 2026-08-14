# Workflow 01 — friction-layer build (act a)

Builds the monthly environmental friction surfaces for Alaska on the
canonical 150 m EPSG:3338 grid (contract: `docs/DATA_CONTRACTS.md` §1–2).

## Run order (the corridor-mask step is NOT optional)

```bash
python 00_preflight_inputs.py       # grid + range gates on inputs/friction_rasters
python 01_build_corridor_masks.py   # -> outputs/01_friction_build/waterway_mask_150m.tif
python 02_build_friction_stack.py   # -> outputs/01_friction_build/friction_stack/ (14 TIFs)
python 03_qa_friction_stack.py      # 14-file contract, ice gating, value floor
# or: bash run_all.sh
```

Skipping step 01 now FAILS the build: `write_friction_stack` raises a
hard error when the waterway mask is absent, because a maskless build
severs ~18% of waterway edges — quietly wrong output a public pipeline
must catch. (The old behavior was a warning, and the old README omitted
the step entirely; both were documented bugs.) The escape hatch for
synthetic/research runs is `--allow-missing-waterway-mask` on stage 02
or `FRICTION_ALLOW_MISSING_WATERWAY_MASK=1`.

## Inputs

`inputs/friction_rasters/` (~7 GB, regenerable-only — see `EXTERNAL_DATA.md`):
slope, lulc, permafrost, sea_ice/{01..12}, river_ice/{01..12}, all snapped to
`lulc.tif`. Plus the waterways shapefile from
`inputs/data_for_network_build.zip` (run `python tools/extract_inputs.py`).

External preprocessing (before this workflow can run at all): the GEE export
script + arcpy river-ice pipeline + `align_permafrost` under
`source_scripts/friction_surface/friction_preprocessing/`.

## Outputs

`outputs/01_friction_build/`: `waterway_mask_150m.tif` +
`friction_stack/{overland.tif, road_base.tif, barge_01..12.tif}` — consumed by
workflow 03's weighting stage. Knobs: `source_scripts/friction_surface/friction_config.py`
(single source of truth). Figure generators: `viz/`.
