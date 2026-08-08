# Workflow 03 — multimodal join (act c)

Joins the frozen network (act b) with the friction surfaces (act a) into
per-(edge, month) weights and dollar costs, writing
`outputs/fuel_network.duckdb` incrementally (this is where the code already
wrote it; act d certifies it).

## Stage contracts (full text: docs/DATA_CONTRACTS.md)

- **edge_id = 0-based shapefile row order** of the edges shapefile. Derived
  at stage 02, shared by every table. The committed zips are checksummed —
  never mix tables from different exports.
- **EXPECTED inventory tripwire** (stage 02): 82,300 nodes / 90,921 edges /
  384 hubs / 21 components / 99.65% giant + the exact edge-type counts. A
  changed export fails loudly here, not silently downstream.
- **Strict NoData rule** (stage 03): any NoData sample ⇒ the edge is
  impassable that month. nodata_frac makes partial blockage auditable.
- **edge_class is derived once** (stage 02) and consumed from the DB by
  stage 03 — the Bridge/IceRoad weld disambiguation lives in one place.
  Ice-involved connectors are named `IceRoadConnector` end-to-end: rebuilt
  networks emit that type directly (profile `edge_type`), and the frozen
  network's legacy `Bridge` edges are mapped to it at ingest.

## Run order

```bash
python 01_extract_network_handoff.py   # unzip the frozen handoff (fresh-clone fix)
python 02_load_final_network.py        # ingest + tripwire -> network_nodes/network_edges
python 03_weight_network_edges.py      # 75 m sampling -> edge_month_weights (needs act a's rasters)
python 04_assemble_weighted_graph.py   # $-rates + fees -> edge_costs (+ --smoke-dijkstra)
# or: bash run_all.sh                  # stops gracefully after 02 if the friction stack is absent
```

Stages 01–02 run from committed data alone — that pair is the CI smoke test.
Dollars enter ONLY at stage 04, from `src/friction_surface/friction_costs.py`.
Figures: `viz/make_network_plots.py`.
