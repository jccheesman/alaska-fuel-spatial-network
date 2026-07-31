# outputs/

Publication figures, tables, and light analysis artifacts, plus a few
generated rasters the friction stack consumes. Most files are regeneratable by
the friction pipeline or the one-off analysis/table/figure scripts.

## Layout

| Path | Contents |
|---|---|
| `tables/` | Publication workbooks (`*.xlsx`) **and** their generator scripts. Each generator writes next to itself, so the pair stays together. |
| `figures/` | Standalone diagnostic plots (e.g. IDW river-ice overviews). |
| `analysis/` | Sensitivity / distribution study results: `_*.json` data + companion `*.md` writeups (LULC sensitivity, road-grade distribution). |
| `final_network_plots/` | Statewide / connector / hub plots from `../make_network_plots.py`. |

## Pipeline **inputs** that live here (do NOT reorganize)

These corridor masks are written by `../build_corridor_masks.py` and consumed by
the friction stack via `../friction_surface/friction_paths.py`; they must stay at
the `outputs/` top level:

| File | Read by |
|---|---|
| `road_mask_150m.tif` | friction stack (`ROAD_MASK_TIF`) — overland road/bridge burn-in |
| `waterway_mask_150m.tif` | friction stack (`WATERWAY_MASK_TIF`) — **barge navigability**: `(lulc_water \| waterway_mask) & ~ice` recovers rivers narrower than a 150 m LULC pixel |
| `ice_road_mask_150m.tif` | friction stack (`ICE_ROAD_MASK_TIF`) — overland Jan–Mar ice-road burn-in |

## Notes

- The friction pipeline writes its rasters to
  `../friction_surface/friction_outputs/`, not here, and logs to
  `outputs/pipeline_YYYYMMDD_HHMMSS.log`.
- The weighted network DuckDB (`../fuel_network.duckdb`) is built at the repo
  root by `load_final_network.py` → `weight_network_edges.py` →
  `assemble_weighted_graph.py`.

## Related docs

- `../README.md` — project overview + how to run the three stages
