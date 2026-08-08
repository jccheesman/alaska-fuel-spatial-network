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
| `network_nodes` | 82,300 | node attributes + hub flags + coordinates |
| `network_edges` | 90,921 | topology + type + edge_class + derived length_m |
| `edge_month_weights` | 1,091,052 | environmental friction per (edge, month), strict passability |
| `edge_costs` | 1,091,052 | $/gallon per (edge, month) from friction × rates (+ transfer fees) |

## hub_facility_map — documented future work

The routing/TSP layer above this deliverable needs a
`hub_facility_map(hub_id, facility_id)` table (384 hubs ↔ 1,838 facilities).
**No writer or source data for it exists in this repository** — the
`backfill_facility_edges` stub in stage 03/04 and the probe in
`02_inspect_schema.py` are the extension points, kept deliberately so the
follow-on work has a named seam. Do not expect the table to exist.
