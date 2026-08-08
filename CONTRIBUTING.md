# Contributing

To reproduce the build, start with the README Quickstart and then consult EXTERNAL_DATA.md, which documents the full inventory of what is committed to the repository, what must be regenerated, and what is absent by design. The working directories for data inputs, intermediate layers, and outputs are regenerable from the committed source material — see the pipeline table in README.md for stage dependencies and the per-stage driver scripts under `workflows/`.

Issues and pull requests are welcome. Please note that the frozen network-of-record (`final_network/*.zip`) and the cost and friction constants (`src/friction_surface/friction_costs.py`, `friction_config.py`) change only by decision of the repository owners; if you wish to propose changes to these components, please open an issue first to discuss your proposal.
