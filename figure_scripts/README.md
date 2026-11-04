# figure_scripts/

Generators of the publication figures and tables. Their output lands in
`outputs/figures/` and `outputs/tables/` (tracked), so `outputs/` holds only outputs and
every committed figure or table traces to one script here. Run from the repo root,
e.g. `python figure_scripts/plot_weighted_network.py`.

Two of them need packages the pipeline doesn't: `openpyxl` (the `tables/` workbooks) and
`python-pptx` (the data-connection story deck). Install them once with the `figures` extra:

```bash
uv sync --extra figures        # or: uv pip install -e ".[figures]"
```

| Script | Writes | Needs |
|---|---|---|
| `plot_weighted_network.py` | `weighted_network_monthly*` | `outputs/fuel_network.duckdb` (full workflow 03), TIGER state outline |
| `plot_hub_network.py` | `hubs_by_*` | same; imports its sibling `plot_weighted_network.py` |
| `plot_data_connection_story.py` | `data_connection_story.{png,pptx}`, `panels/` | extracted `final_network/` + 2022 bulk-fuel bundle |
| `plot_anchorage_wainwright_flight.py` | `anchorage_wainwright_flight.png` | `data/boundary.geojson` |
| `plot_disconnected_hubs.py` | `disconnected_hubs.png` | `outputs/02_network_build/` (a stage-02 rebuild) |
| `plot_paper_network.py` | `outputs/02_network_build/reports/figs/network_facets.{pdf,png}` (not yet in `outputs/figures/`) | a stage-02 build; fetches the Natural Earth basemap if absent |
| `plot_combined_friction.py` | friction figures under the friction-stack output dir | the friction stack; imports its sibling `plot_friction_stack.py` |
| `plot_friction_stack.py` | the per-mode friction grids, same place | the friction stack |
| `tables/build_input_datasets_xlsx.py` | `outputs/tables/input_datasets.xlsx` | — |
| `tables/build_combined_friction_tables.py` | `outputs/tables/combined_friction_tables.xlsx` | — (every value read from `friction_config.py` and `friction_costs.py`) |

`combined_friction_tables.xlsx` replaced the hand-exported `friction_config.xlsx`
(retired 2026-10; it survives in git history). Rebuild it whenever
`friction_config.py` or `friction_costs.py` changes.
