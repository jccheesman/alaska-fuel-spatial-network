# outputs/

Outputs of the workflow are managed in this folder. Which products are in the
repository, which are built by the pipeline, and the command that regenerates
each: `../DATA.md` §6.

| Path | Tracked? | Producer | Contents |
|---|---|---|---|
| `figures/` | yes | `workflows/03_multimodal_join/viz/*` + `workflows/01_friction_build/viz/*` | Publication figures (weighted-network monthly grids, reference grid, IDW overviews, regions, pipeline diagram, sea-ice padding) |
| `tables/` | yes | `tables/build_*.py` | Publication workbooks (`*.xlsx`) and their generators; each writes next to itself |
| `final_network_plots/` | **no** (written on demand) | `workflows/03_multimodal_join/viz/make_network_plots.py` | Statewide / connector / hub network plots |
| `01_friction_build/` | **no** | workflow 01 | Waterway corridor mask + the 14-file friction stack (~288 MB, regenerable) |
| `02_network_build/` | **no** | workflow 02 | The mmnet project dir: `output/` gpkg stages + QGIS projects, `reports/` |
| `fuel_network.duckdb` | **no** | workflows 03–04 | The 4-table weighted-network database (~30 MB, regenerable) |
| `pipeline_*.log` | **no** | `friction_paths.setup_logging` | Timestamped run logs |


## Related docs

- `../README.md` — the four-act pipeline
- `../docs/DATA_CONTRACTS.md` — inter-stage contracts (incl. the DuckDB schema)
