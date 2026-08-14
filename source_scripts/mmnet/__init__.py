"""mmnet — a self-contained multimodal spatial-network builder.

Python orchestration (consolidate / tag / hubs / viz / inspect) + a **bundled R / sfnetworks
build** (the `r_oracle/` scripts run via Rscript). It reads a `profile.yaml` (the region-agnostic
single source of truth) and reproduces the connected multimodal network the profile defines
(hubs snap to the road, airports snap onto the road as shared nodes, barge transfers at ports,
then an optional Stage-04 join of leftover components to the giant by distance).

Quick start::

    import mmnet
    net = mmnet.run_pipeline("profile.yaml")   # -> output/03_network__{nodes,edges}.gpkg

Requires R + the sfnetworks/sf/tidygraph stack on the PATH (for the build step).
"""
from __future__ import annotations

from . import inspect, viz
from .assemble import connect_multimodal, join_components_to_giant, snap_to_roads
from .build import build_network, node_layers_via_r
from .config import load_config, load_params, load_profile
from .network import NetworkTables
from .pipeline import run_pipeline

__all__ = [
    "run_pipeline",
    "build_network",
    "node_layers_via_r",
    "connect_multimodal",
    "join_components_to_giant",
    "snap_to_roads",
    "load_profile",
    "load_config",
    "load_params",
    "NetworkTables",
    "viz",
    "inspect",
]
