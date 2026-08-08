# research/multimodal_network — the full multimodal network with the new flight data

A research sandbox that **shows the complete Alaska multimodal fuel network** — road + ice + waterway +
the **new official air-cargo data** — and isolates what the air mode contributes. Mirrors
`research/waterway_network/` + `research/flights_network/`.

## Data
- **Source:** `output/03_network__{nodes,edges}.gpkg` — the engine's built multimodal network, produced by
  the pipeline **with the new official flight data** now wired into the air mode.
- Rebuild it first if stale: `python -c "import mmnet; mmnet.run_pipeline('profile.yaml')"`.

## Scripts (run from this folder)
```
python3 01_multimodal_network.py   # per-mode size, network-by-mode map, connectivity (giant +
                                   # per-mode % reachable), connected-vs-disconnected, hub reachability
python3 02_air_role.py             # the new air mode's marginal contribution: air↔road transfers,
                                   # WITH-vs-WITHOUT-air giant, air-only-reachable hubs/communities
```
Reuses the project: `mmnet.network.NetworkTables`, `mmnet.viz._EDGE_TYPE_COLORS`, the research `_trace.py`,
and `data/boundary.geojson`. Outputs land in `out/` (gitignored via `research/**/out/`).

## Result
98.6 % of nodes in one giant (67 components); per-mode in giant — Road 97.7 % · Waterway 100 % · IceRoad
95.4 % · Air 100 %; 331/384 fuel hubs reachable. **Air alone connects 44 fuel hubs + ~1,000 road nodes**
that road + barge + ice cannot reach (without it: 214 components). Full writeup in **`FINDINGS.md`**.
