"""inventory_qc — the facility-inventory QC chain (workflow 00).

One module per stage, run in order by workflows/00_inventory_qc/ (each numbered script there
is a thin wrapper around a module's main()):

    ingest -> apply_corrections -> normalise -> assign_facility_ids -> detect -> boundary_check
    -> assign_region -> review_queue -> publish -> ledger

`core` holds the shared paths, config loaders and name canonicalisation, so the files under
inputs/inventory_qc/ stay the single source of truth.
"""
