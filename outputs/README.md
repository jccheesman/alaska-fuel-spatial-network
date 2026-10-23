# outputs/

Outputs of the workflows are managed in this folder. Gitignored paths are
regenerable working trees — never hand-edit them; rerun their producer.

| Path | Tracked? | Producer | Contents |
|---|---|---|---|
| `00_inventory_qc/<release>/` | partly | workflow 00 (`validate_inventory.py --publish`) | `facilities_clean.csv` (the published clean facility table workflow 02 reads) + `qc_report.md`, the flags, boundary checks, exclusions and corrections log. Regenerated only by workflow 00 — fix data in `inputs/inventory_qc/corrections.csv`, never in the table. `facilities_corrected.csv`, `facilities_normalised.csv` and `review_queue.xlsx` are gitignored |
| `figures/` | yes | `paper/figures/` (`plot_weighted_network.py`, `plot_hub_network.py`, `plot_data_connection_story.py`, `plot_anchorage_wainwright_flight.py`, `plot_disconnected_hubs.py`) | Publication figures: weighted-network monthly grids, hub maps by type / capacity / season (each in light + dark, PNG + PDF), the data-connection story (+ `panels/`, `.pptx`), disconnected hubs |
| `tables/` | yes | `paper/tables/build_*.py` | Publication workbooks (`*.xlsx`) |
| `final_network_plots/` | no (not present until run) | `diagnostics/03_multimodal_join/` (`make_network_plots.py`, `plot_edge_types.py`, `plot_connector_*.py`) | Statewide / connector / hub / edge-type network views |
| `diagnostics/` | **no** | `diagnostics/<stage>/*.py` | Build-time check and investigation plots, by stage |
| `01_friction_build/` | **no** | workflow 01 | Waterway corridor mask + the 14-file friction stack (~288 MB, regenerable) |
| `02_network_build/` | **no** | workflow 02 | The mmnet project dir: `output/` gpkg stages + trail CSVs + QGIS projects, `reports/` (connectivity reports) |
| `fuel_network.duckdb` | **no** | workflows 03–04 | The weighted-network database: `network_nodes`, `network_edges`, `edge_month_weights`, `edge_costs` (+ `hub_members`, `hub_snaps` from a 2026-10 or later export); ~30 MB, regenerable |
| `pipeline_*.log` | **no** | `friction_paths.setup_logging` | Timestamped run logs |

The driver-run plots of `workflows/02_network_build/viz/` write into
`02_network_build/output/`; the friction figures (`paper/figures/plot_friction_stack.py`,
`plot_combined_friction.py`) into the friction-output dir. Everything else that makes a
figure lives in `paper/` (committed figures and tables) or `diagnostics/` (build checks) —
see their READMEs.

## Related docs

- `../README.md` — the pipeline overview
- `../docs/DATA_CONTRACTS.md` — inter-stage contracts (incl. the DuckDB schema)
- `../docs/DATA_DICTIONARY.md` — what every column in these tables means, with units
