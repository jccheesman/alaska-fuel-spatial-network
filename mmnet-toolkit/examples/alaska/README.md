# Example — Alaska bulk-fuel multimodal network

A complete, real `profile.yaml`: Alaska's road + barge (waterway) + air + seasonal ice-road network,
built from the state bulk-fuel facility inventory and the connectivity layers. Use it as the template
to model your own region on (see the `define-network-profile` skill).

## What's shipped vs what you provide

This folder ships the **worked configuration** (`profile.yaml`) and the **proof gate**
(`verify_north_slope.py`) — **not the data** (the GIS inputs are large and are gitignored in the source
project). The profile's relative paths show exactly where each input goes; drop your copies there:

```
examples/alaska/
├── profile.yaml               # the config (shipped)
├── verify_north_slope.py      # the proof gate (shipped)
├── data/
│   ├── interim/               # facilities.csv, tiger_places.gpkg, boroughs.gpkg,
│   │                          #   roads_akdot.gpkg, roads_grip4.gpkg, ak_waterway.gpkg,
│   │                          #   ice_roads.gpkg, ports.gpkg, fuel_delivery_method.gpkg
│   ├── processed/             # airways.geojson, air_nodes.geojson
│   └── boundary.geojson
└── output/                    # created by the build (gitignored)
```

The `data/interim/` and `data/processed/` layers are **derived** — in the source project they're built
from `data/raw/` by `scripts/normalize_raw.py` (raw → uniform EPSG:3338 interim), `scripts/prep_airways.py`
(air OD legs → `airways.geojson` + `air_nodes.geojson` + `boundary.geojson`), and
`scripts/prep_waterway.py` (the AK marine network). Bring those prepared layers (or your own equivalents)
to the paths above.

## Run

```bash
# from this folder, with mmnet installed (pip install -e ../.. at the toolkit root) and R + sf/sfnetworks on PATH:
python -c "import mmnet; net = mmnet.run_pipeline('profile.yaml'); print(net.summary())"
python verify_north_slope.py
```

`run_pipeline` writes `output/03_network__{nodes,edges}.gpkg` + `reports/03_network.md` here; with the
profile's `join_components` enabled it also writes `output/04_network_joined__*`.

## Expected result (the proof)

The Alaska build produces one dominant connected network: **≈ 82,300 nodes / 90,876 edges**, giant
**≈ 98.6 %**, with the North Slope reachable by sea (barge landings). `verify_north_slope.py` prints
`North Slope (Barrow): CONNECTED` and a `RESULT: PASS` line — that proof is the definition of a correct
build (see the `build-and-verify-network` skill).
