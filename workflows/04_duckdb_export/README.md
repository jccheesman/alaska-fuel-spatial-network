# Workflow 04 — the DuckDB deliverable (act d)

Certifies and documents `outputs/fuel_network.duckdb` — the deliverable the
paper's analyses read. Workflow 03 writes the tables; this stage validates
and inspects them.

```bash
python 01_run_validation_queries.py    # monthly passability by mode
python 02_inspect_schema.py            # schema + row counts
```

## Schema (4 tables; full contract in docs/DATA_CONTRACTS.md §8)

| Table | Rows | Purpose |
|---|---|---|
| `network_nodes` | 84,089 | node attributes + hub flags + coordinates |
| `network_edges` | 92,978 | topology + type + edge_class + derived length_m |
| `edge_month_weights` | 1,115,736 | environmental friction per (edge, month), strict passability |
| `edge_costs` | 1,115,736 | $/gallon per (edge, month) from friction × rates (+ transfer fees) |

## hub_members / hub_snaps — the hub handoff (replaces the hub_facility_map seam)

Since the 2026-10 export the deliverable also carries `hub_members` (one row
per hub and raw inventory `record_id`, with the hub's `hub_key`,
`hub_community`, `hub_kind`, modes, type, landing `node_id` and
`snap_status`) and `hub_snaps` (stage 03's placement trail), loaded by
`02_load_final_network.py` from `final_network/hub_members.csv` and
`hub_snaps.csv` (written by `06_export_final_network.py` through
`mmnet.handoff`). This is the writer the old "hub_facility_map — documented
future work" note waited for: membership comes from the build, not from a
consumer's distance rule. The `backfill_facility_edges` stub in stage 03/04
and the probe in `02_inspect_schema.py` can be built on it. An export older
than 2026-10 has neither table.
