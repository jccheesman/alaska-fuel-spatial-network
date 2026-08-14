# outputs/

| Path | Tracked? | Producer | Contents |
|---|---|---|---|
| `figures/` | yes | `figures/scripts/*` + `workflows/01_friction_build/viz/*` | Publication figures (weighted-network monthly grids, reference grid, IDW overviews, regions, pipeline diagram, sea-ice padding) |
| `figures/scripts/` | yes | — | Their generators (`plot_weighted_network.py`, `plot_hub_network.py`, `plot_reference_grid.py`) — kept beside the outputs deliberately |
| `tables/` | yes | `tables/build_*.py` | Publication workbooks (`*.xlsx`) and their generators; each writes next to itself |
| `analysis/` | yes | one-off studies | Sensitivity / distribution results: `_*.json` data + `*.md` writeups (LULC sensitivity, road grade), `lulc_fast_vs_exact_disagreement.png` |
| `final_network_plots/` | yes | `workflows/03_multimodal_join/viz/make_network_plots.py` | Statewide / connector / hub network plots |
| `01_friction_build/` | **no** | workflow 01 | Waterway corridor mask + the 14-file friction stack (~288 MB, regenerable) |
| `02_network_build/` | **no** | workflow 02 | The mmnet project dir: `output/` gpkg stages + QGIS projects, `reports/` |
| `fuel_network.duckdb` | **no** | workflows 03–04 | The 4-table weighted-network database (~30 MB, regenerable) |
| `pipeline_*.log` | **no** | `pipeline_utils.setup_logging` | Timestamped run logs |

(The old top-level corridor-mask story is gone: `road_mask_150m.tif` and
`ice_road_mask_150m.tif` are retired — only the waterway mask is live, and it
lives under `01_friction_build/` with its consumer.)

## Related docs

- `../README.md` — the four-act pipeline
- `../docs/DATA_CONTRACTS.md` — inter-stage contracts (incl. the DuckDB schema)
