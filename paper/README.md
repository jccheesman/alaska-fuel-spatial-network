# paper/

Generators of the publication figures and tables. Their output lands in
`outputs/figures/` and `outputs/tables/` (tracked), so `outputs/` holds only outputs and
every committed figure or table traces to one script here. Run from the repo root,
e.g. `python paper/figures/plot_weighted_network.py`.

| Script | Writes | Needs |
|---|---|---|
| `figures/plot_weighted_network.py` | `weighted_network_monthly*` | `outputs/fuel_network.duckdb` (full workflow 03), TIGER state outline |
| `figures/plot_hub_network.py` | `hubs_by_*` | same; imports its sibling `plot_weighted_network.py` |
| `figures/plot_data_connection_story.py` | `data_connection_story.{png,pptx}`, `panels/` | extracted `final_network/` + 2022 bulk-fuel bundle |
| `figures/plot_anchorage_wainwright_flight.py` | `anchorage_wainwright_flight.png` | `data/boundary.geojson` |
| `figures/plot_disconnected_hubs.py` | `disconnected_hubs.png` | `outputs/02_network_build/` (a stage-02 rebuild) |
| `figures/plot_paper_network.py` | `outputs/02_network_build/reports/figs/network_facets.{pdf,png}` (not yet in `outputs/figures/`) | a stage-02 build; fetches the Natural Earth basemap if absent |
| `figures/plot_combined_friction.py` | friction figures under the friction-stack output dir | the friction stack; imports its sibling `plot_friction_stack.py` |
| `figures/plot_friction_stack.py` | the per-mode friction grids, same place | the friction stack |
| `tables/build_input_datasets_xlsx.py` | `outputs/tables/input_datasets.xlsx` | — |
| `tables/build_combined_friction_tables.py` | `outputs/tables/combined_friction_tables.xlsx` | — (rates and fees read from `friction_costs.py`) |

Note: the tracked `outputs/tables/friction_config.xlsx` has no generator here;
`build_combined_friction_tables.py` writes `combined_friction_tables.xlsx`, which
its docstring says supersedes those sheets, but it is not committed.
