"""End-to-end multimodal-network pipeline: consolidate -> tag -> hubs -> build -> join.

`run_pipeline(profile_path)` reproduces this project's result from a `profile.yaml` and its
`data/`: it deduplicates the inventory, tags it, aggregates hubs, then builds the connected
multimodal network. The build is a **hybrid** — the bundled **R / sfnetworks** oracle nodes the
layers and builds the per-mode topology (the hard part), then the Python assembler connects them:
hubs snap to the road, airports snap onto the road (a shared node, no transfer edge), barge
transfers at ports + coastal hubs. Outputs land in `<project>/output/` as `01_facilities`,
`01b_tagged`, `02_hubs`, and the canonical `03_network__{nodes,edges}.gpkg`. Stage 04
(`join_components.max_dist > 0`) then joins any leftover components to the giant by distance,
writing a separate `04_network_joined__{nodes,edges}.gpkg`; `run_pipeline` returns the 03 network.
"""
from __future__ import annotations

import os
from pathlib import Path

from .build import build_network
from .config import load_config, load_params
from .io_writers import output_dir, write_gdf
from .network import NetworkTables
from .steps.consolidate import consolidate_facilities
from .steps.hubs import aggregate_hubs
from .steps.tag import assign_community_region, passthrough_tag


def run_pipeline(profile_path: str | Path, project_dir: str | Path | None = None) -> NetworkTables:
    """Run the full pipeline and return the final network (also written to <project>/output/).

    `profile_path` — the region's `profile.yaml`. `project_dir` — where `output/` is written
    (defaults to the profile's own directory).
    """
    profile_path = Path(profile_path).resolve()
    os.environ["MMNET_PROFILE"] = str(profile_path)
    os.environ["MMNET_PROJECT"] = str(Path(project_dir).resolve() if project_dir else profile_path.parent)

    cfg, params = load_config(), load_params()

    # 01 — consolidate (dedup the raw inventory)
    fac = consolidate_facilities(cfg.raw_path("facilities"), params,
                                 input_crs=cfg.crs.input, target_crs=cfg.crs.target, config=cfg)
    write_gdf(fac, "01_facilities.gpkg")

    # 01b — tag (community/region; passthrough when tagging is off)
    if not cfg.tagging_enabled or cfg.place_tagging is None:
        tagged = passthrough_tag(fac)
    else:
        from .io_readers import load_places, load_regions
        places = load_places(cfg.place_path(), cfg.crs.target, cfg.places_cols)
        regions = load_regions(cfg.region_path(), cfg.crs.target, cfg.regions_cols)
        tagged = assign_community_region(fac, places, regions)
    write_gdf(tagged, "01b_tagged.gpkg")          # the R build reads this

    # 02 — hubs (aggregate centroids; the Python assembler snaps them to the road)
    hubs = aggregate_hubs(tagged, params)
    write_gdf(hubs, "02_hubs.gpkg")

    # 03 — build the multimodal network: R nodes, Python connects (gold procedure)
    layer_list = [s.name for s in cfg.layers if s.kind == "line"]
    net = build_network(layer_list, output_dir() / "03_network", hubs)

    # connectivity report — per-mode + fuel-hub reachability (and, where an Air mode exists, its marginal
    # contribution). Prints a headline and writes reports/03_network.md.
    from . import inspect as _inspect
    rep = _inspect.connectivity_report(net.nodes, net.edges)
    contrib = (_inspect.mode_contribution(net.nodes, net.edges, "Air")
               if "Air" in set(net.edges["type"]) else None)
    _inspect.write_network_report(rep, contrib)

    # 04 — join every still-disconnected component to the giant within cfg.join_components.max_dist
    # (0 disables). This does NOT touch 03_network; it writes a separate 04_network_joined + report.
    jc = float(cfg.join_components.max_dist)
    if jc > 0:
        from .assemble import join_components_to_giant
        jn, je, jsum = join_components_to_giant(net.nodes, net.edges, jc)
        joined = NetworkTables.from_parts(jn, je)
        joined.to_gpkg(output_dir() / "04_network_joined")
        print(f"[04] joined {jsum['n_joined']} components (≤ {jc:.0f} m) in {jsum['rounds']} round(s); "
              f"components {net.nodes['component'].nunique()} -> {jsum['n_components']}, "
              f"giant {jsum['giant_frac']:.1%}")
        jrep = _inspect.connectivity_report(joined.nodes, joined.edges)
        _inspect.write_network_report(jrep, out_name="04_network_joined.md",
                                      title="Stage 04 — components joined to the giant")

    return net    # 03 stays the canonical return; 04 is the new on-disk deliverable
