# final_network — the Alaska multimodal network (final, joined)

The **final network**: the Stage-04 *joined* multimodal transport graph — road + barge (waterway) + air
+ seasonal ice road, with every remaining component joined to the giant within 20 km. Exported here as
**Esri Shapefiles** (ArcGIS-ready).

- **Nodes:** `network_joined_nodes.shp` — 82,300 points
- **Edges:** `network_joined_edges.shp` — 90,921 lines (incl. 45 `Join` distance-connectors)
- **Components:** 21 · **giant:** 99.65% of nodes · **fuel hubs:** 384
- **CRS:** EPSG:3338 — NAD83 / Alaska Albers (meters). The `.prj` reads as `NAD_1983_Alaska_Albers`.

Each shapefile is the usual multi-file set (`.shp/.shx/.dbf/.prj/.cpg`) — copy all of them together.

## Field names (Shapefile 10-character limit)

Shapefile/DBF truncates field names to 10 characters, so three long names were shortened on export.
Full mapping:

**Nodes**

| shapefile field | meaning |
|---|---|
| `node_id`    | 0-based node id (matches edge `from`/`to`) |
| `is_hub`     | 1 if a fuel hub snapped to this node |
| `hub_id`     | hub identifier (when `is_hub`) |
| `deliv_meth` | **delivery_method** — the hub's mode(s): Road / Barge / Plane / "… or …" combos |
| `hub_type`   | Supplier / Receiver |
| `hub_cap`    | **total_hub_capacity** — summed fuel capacity at the hub |
| `snap_surf`  | **snap_surface** — surface the hub snapped to (Road / IceRoad) |
| `component`  | connected-component id (1 = the giant) |
| `is_giant`   | 1 if the node is in the giant component |

**Edges**

| shapefile field | meaning |
|---|---|
| `from`, `to` | endpoint `node_id`s |
| `type`       | Road · Waterway · Air · IceRoad · Transfer · Bridge · **Join** |
| `source`     | provenance (e.g. `Road`, `ports`, `barge_hubs`, `weld:*`, `bridge:*`, `shore:*`, `join:to-giant`) |
| `join_gap_m` | for `Join` edges, the straight-line gap (m) that was closed; NULL/0 otherwise |

## Provenance

Built by the `mmnet` pipeline from `profile.yaml` (this repo): `consolidate → tag → hubs → build (Stage 03)
→ join (Stage 04)`. R nodes each land mode; Python nodes the waterway and connects everything; Stage 04
joins leftover components to the giant within `join_components.max_dist: 20000` (20 km). The canonical
pre-join network (66 components, 98.65% giant) is `output/03_network`; this folder is the **joined**
variant (`output/04_network_joined`).

## Regenerate

```bash
bash scripts/run_all.sh                        # rebuild 03 + 04 from profile.yaml
python scripts/export_final_shapefile.py       # re-export the joined network into this folder
```

This folder holds only the network **data** (the shapefiles) + this README. The shapefiles are
gitignored (regenerable, ~90 MB total); the exporter lives in `scripts/export_final_shapefile.py`. If
you prefer a single-file format, ArcGIS Pro also opens the original GeoPackage
`output/04_network_joined__{nodes,edges}.gpkg`.
