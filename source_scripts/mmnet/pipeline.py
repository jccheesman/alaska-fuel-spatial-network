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

from .assemble import classify_connectors
from .build import build_network
from .config import load_config, load_params

# Synthetic-connector naming vocabulary (mirrored in friction_costs.py). The
# carrier word per line layer defaults to its transport MODE; the air layer uses
# "Air" (its edge_label) rather than the mode word "Plane". `_TOKEN_ORDER` fixes a
# deterministic order for a two-mode pair so it yields ONE canonical name
# (BargeRoadTransfer, not RoadBargeTransfer).
_CARRIER_ALIAS = {"Plane": "Air"}
_TOKEN_ORDER = {"Barge": 0, "IceRoad": 1, "Air": 2, "Road": 3}


def _connector_tokens(cfg) -> dict:
    """edge_label -> carrier word used in synthetic-connector type names."""
    line_specs = [s for s in cfg.layers if s.kind == "line"]
    return {s.edge_label: _CARRIER_ALIAS.get(s.mode, s.mode) for s in line_specs}
from .io_writers import output_dir, write_gdf
from .network import NetworkTables
from .steps.consolidate import consolidate_facilities
from .steps.hubs import aggregate_hubs, hub_members
from .steps.tag import assign_community_region, passthrough_tag


def write_site_members(fac) -> Path:
    """Long-form trail of the consolidation merge: one row per (site, raw record).

    Written beside 01_facilities.gpkg as 01_site_members.csv so a hub can be traced back to the
    inventory records it aggregates (site -> hub membership is then recoverable from 02_hubs).
    """
    import pandas as pd
    rows = [(sid, rid) for sid, ids in zip(fac["ast_facility_id"], fac["member_record_ids"].fillna(""))
            for rid in ids.split(";") if rid]
    out = output_dir() / "01_site_members.csv"
    pd.DataFrame(rows, columns=["ast_facility_id", "record_id"]).to_csv(out, index=False, lineterminator="\n")
    return out


def write_conflicts(tagged) -> Path:
    """Labelled facilities whose label's borough differs from their coordinates' borough
    (tag step name_match='conflict'). Kept in the build; listed here for the inventory corrections."""
    cols = [c for c in ("ast_facility_id", "member_record_ids", "community_name", "place_name",
                        "region_name", "label_borough", "delivery_method", "total_capacity")
            if c in tagged.columns]
    c = tagged.loc[tagged["name_match"] == "conflict", cols].copy()
    c["x"], c["y"] = tagged.loc[c.index].geometry.x.round(1), tagged.loc[c.index].geometry.y.round(1)
    out = output_dir() / "01b_conflicts.csv"
    c.to_csv(out, index=False, lineterminator="\n")
    return out


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
    if "member_record_ids" in fac.columns:
        write_site_members(fac)
    wh = fac.attrs.get("withheld")
    if wh is not None:
        wh.to_csv(output_dir() / "01_withheld.csv", index=False, lineterminator="\n")

    # 01b — tag (community/region; passthrough when tagging is off)
    if not cfg.tagging_enabled or cfg.place_tagging is None:
        tagged = passthrough_tag(fac)
    else:
        from .io_readers import load_places, load_regions
        places = load_places(cfg.place_path(), cfg.crs.target, cfg.places_cols)
        regions = load_regions(cfg.region_path(), cfg.crs.target, cfg.regions_cols)
        tagged = assign_community_region(fac, places, regions)
    write_gdf(tagged, "01b_tagged.gpkg")          # the R build reads this
    if "name_match" in tagged.columns:
        write_conflicts(tagged)

    # 02 — hubs (aggregate centroids; the Python assembler snaps them to the road)
    hubs = aggregate_hubs(tagged, params)
    write_gdf(hubs, "02_hubs.gpkg")
    hub_members(hubs).to_csv(output_dir() / "02_hub_members.csv", index=False, lineterminator="\n")

    # 03 — build the multimodal network: R nodes, Python connects (gold procedure)
    layer_list = [s.name for s in cfg.layers if s.kind == "line"]
    net = build_network(layer_list, output_dir() / "03_network", hubs,
                        max_snap_dist=float(params.max_snap_dist_m))

    # 03b — re-type synthetic connectors by the modes they join (same-mode ->
    # {Mode}Connector, two modes -> per-pair Transfer). Rewrites 03_network so the
    # report + stage 04 + export all speak one mode-based vocabulary.
    tokens = _connector_tokens(cfg)
    net = NetworkTables.from_parts(net.nodes, classify_connectors(net.edges, tokens, _TOKEN_ORDER))
    net.to_gpkg(output_dir() / "03_network")

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
        # the stage-04 join edges are raw "Join" — classify them (and re-confirm
        # the rest) so cross-mode joins become the right per-pair Transfer.
        je = classify_connectors(je, tokens, _TOKEN_ORDER)
        joined = NetworkTables.from_parts(jn, je)
        joined.to_gpkg(output_dir() / "04_network_joined")
        print(f"[04] joined {jsum['n_joined']} components (≤ {jc:.0f} m) in {jsum['rounds']} round(s); "
              f"components {net.nodes['component'].nunique()} -> {jsum['n_components']}, "
              f"giant {jsum['giant_frac']:.1%}")
        jrep = _inspect.connectivity_report(joined.nodes, joined.edges)
        _inspect.write_network_report(jrep, out_name="04_network_joined.md",
                                      title="Stage 04 — components joined to the giant")

    return net    # 03 stays the canonical return; 04 is the new on-disk deliverable
