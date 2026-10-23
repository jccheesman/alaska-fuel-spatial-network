"""fuel_network — the weighted multimodal network (workflow 03).

    load     stage 02: frozen final_network handoff -> network_nodes / network_edges (+ hub
             handoff) in DuckDB; derives edge_id (= edges row order) and edge_class, ONLY here
    weights  stage 03: friction sampled along every edge, per month -> edge_month_weights
    graph    stage 04: $-rates x friction -> edge_costs, and the weighted MultiGraph

Analysis code starts from the graph API re-exported here:

    from fuel_network import load_weighted_multigraph, month_view, hub_to_hub_costs
"""
from .graph import hub_to_hub_costs, load_weighted_multigraph, month_view

__all__ = ["hub_to_hub_costs", "load_weighted_multigraph", "month_view"]
