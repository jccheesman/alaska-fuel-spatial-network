# Repository Structure

Public-facing companion code and data for the Data-in-Brief (DIB) spatial-network paper.
This is a curated copy of the working repository, organized for reproducibility and release.
See `EXTERNAL_DATA.md` for large/external datasets.

## Layout

```
.
├── README.md                     # project overview
├── requirements.txt              # Python dependencies
├── STRUCTURE.md                  # this file
├── EXTERNAL_DATA.md              # large/external data & regeneration notes
├── .gitignore
│
│   ── executable code (flat layout; run from repo root so imports resolve) ──
├── load_final_network.py         # network ingest (shapefiles → DuckDB)
├── weight_network_edges.py       # sample friction rasters onto edges
├── assemble_weighted_graph.py    # per-month edge costs + weighted graph
├── build_corridor_masks.py       # rasterize transport corridors
├── pipeline.py                   # shared infra helpers (logging + input-raster paths)
├── query_duckdb.py  run_validation_query.py   # ad-hoc DB queries
├── make_network_plots.py         # network / weighted-edge figures
│
├── .claude/skills/              # Claude Code skills (friction-surface + cost playbooks)
│
├── friction_surface/            # environmental friction package (code only)
│   ├── run_friction_pipeline.py  # entry point
│   ├── friction_config.py        # single source of truth (CRS, thresholds, seasons)
│   ├── friction_costs.py         # per-mode operational cost rates (separate from friction)
│   ├── friction_*.py             # surface builder, I/O, preflight, paths
│   ├── friction_preprocessing/   # GEE + ArcGIS preprocessing scripts
│   ├── tests/  qa/  viz/
│   ├── README_friction.md
│   └── requirements-friction.txt
│
├── mmnet-toolkit/               # reusable multimodal-network builder (installable package)
│
│   ── data (kept at root to preserve code paths) ──
├── inputs/                      # ALL input datasets (4.9 GB; see EXTERNAL_DATA.md re: the zip)
├── final_network/               # final joined network (shapefile zips + README)
├── outputs/                     # publication figures, tables, analysis (light artifacts only)
│
├── supplementary/
│   ├── cost-derivations/         # blind cost derivations (write-ups + built PDFs)
│   └── cost-verification/        # cost-rate verification & audit
│
└── setup/                        # environment provisioning (Jetstream, installs)
```

## Notes

- **Scope.** This release covers the friction stack, ingest of the delivered network
  (`final_network/` → `load_final_network.py`), and per-edge weighting
  (`weight_network_edges.py` → `assemble_weighted_graph.py`). The multi-agent routing /
  TSP-optimization layer is the subject of separate work and is **not** shipped here.
- **Flat code layout is intentional.** Scripts import each other by module name
  (`import pipeline`, `from friction_surface import …`); run them from the repository root.
- **`.claude/skills/`** holds four Claude Code skills: `align-to-ak-stack`,
  `assign-friction-values`, `derive-fuel-costs`, and `run-friction-pipeline`.
  Each ships a runnable script and/or invariant checker; they document and
  enforce the friction-surface and cost-model procedures.
- **`pipeline.py`** provides shared infrastructure helpers only — logging and
  input-raster path resolution — used by the friction build.
- **Surface-only friction build.** `run_friction_pipeline.py` produces the friction
  rasters only; per-edge weighting is the separate `weight_network_edges.py` →
  `assemble_weighted_graph.py` step. The legacy per-facility cost-distance edge builder
  (`routing_wbt.py`, WhiteboxTools) has been retired along with it.
- **Superseded / out-of-scope modules** (`build_connectors.py`, `build_river_mask_nhd.py`,
  `routing_wbt.py`, and the agent/routing modules `run_graph.py`, `build_fuel_network.py`,
  `tools.py`, `multimodal_router.py`, `market_cost_analysis.py`) are **not** shipped in
  this public copy.
- **`setup/`** holds environment provisioning helpers (`JETSTREAM_SETUP_GUIDE.md`,
  `installations.txt`).
- Internal working notes, the DIB paper draft, and third-party source PDFs are
  **not** included in this public copy.
