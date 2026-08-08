# Python <-> R NODE-ONLY ORACLE — FILE CONTRACT (contract_version "2")

The Stage-03 oracle (`build_network.R` + `lib.R`) does R's **one** job in the gold pipeline: build
the per-mode sfnetwork — the planar noding + subdivision + smoothing that is hard to reproduce
exactly in Python. It aggregates NO hubs, blends nothing, builds NO transfers, and joins NO modes;
Python owns hub aggregation (Stage 02) and the intermodal connection
(`mmnet.assemble.connect_multimodal`).

The oracle is **decoupled**: it never `setwd()`s into an Alaska R project, sources its modules, or
reads a `{targets}` cache. The **Python side** (`mmnet/build.py::_write_node_contract`) assembles a
self-contained temp **WORKDIR**, and the oracle reads ONLY that workdir plus its sibling `lib.R`.

## Invocation

```
Rscript build_network.R --workdir <WORKDIR> --out <PREFIX> --modes Road,Plane --node-only
```

`--node-only` is required (the oracle runs no other mode). `--modes` is the comma-separated list of
mode atoms (registry `mode` values) to node. Writes ONLY `<PREFIX>__edges.gpkg` (one row per noded
edge, carrying `type` = the mode's `edge_label`). Python derives the global node table from the edge
endpoints, so no nodes file is written.

`contract_version` is `"2"` (a string), defined in both `build_network.R` (`CONTRACT_VERSION`) and
written into `params.json` by the Python side. The oracle errors on a mismatch.

## WORKDIR layout

```
<WORKDIR>/
  layers/<layername>.gpkg       one per transport LINE layer to node (key = registry `layer`)
  params.json                   { contract_version, target_crs, input_crs, precision }
  registry.json                 { "modes": [...], "transfers": [] }
```

No facilities, no anchors — the noder needs only the line geometry, the target CRS, and the cleaning
precision. Only the layers for the **selected** modes are read: `layers/<layer>.gpkg` for each kept
registry mode.

### `params.json` — flat object

```json
{
  "contract_version": "2",
  "target_crs": 3338,
  "input_crs": 4326,
  "precision": 1
}
```

`precision` is the coordinate-rounding precision (meters) `clean_subnetwork()` uses; `target_crs`
labels the noded geometry.

### `registry.json` — modes

```json
{
  "modes": [
    {"mode": "Road",  "layer": "roads",     "edge_label": "Road",    "blend_param": "road_blend_tolerance"},
    {"mode": "Plane", "layer": "airways",   "edge_label": "Air",     "blend_param": "air_blend_tolerance"},
    {"mode": "Ice Road", "layer": "ice_roads", "edge_label": "IceRoad", "blend_param": "ice_roads_blend_tolerance"}
  ],
  "transfers": []
}
```

- `modes[].layer` is the key for `layers/<layer>.gpkg`.
- `modes[].edge_label` becomes the noded edge `type`.
- `blend_param` is carried for compatibility but is unused by the node-only oracle.
- `transfers` is always empty (Python builds every intermodal connection).

## Guarantees

- The oracle sources only `lib.R` (same dir). No `setwd` to any Alaska project, no `tar_read`.
- `lib.R` holds `clean_subnetwork()` copied VERBATIM from
  `network_preprocess/R/network_preprocessing.R`; its logic is unchanged. The mode registry
  (formerly `config.R`) is supplied as DATA via `registry.json`.
