# research/road_road_connect

A tracked **scoping study**: is the road network's 1,523-component fragmentation a fixable noding
problem or genuine geography, and how much should `mmnet` try to connect? Surfaced as a side-finding of
the [`road_ice_connect`](../road_ice_connect/) study. Scripts + [`FINDINGS.md`](FINDINGS.md) are tracked;
the generated `out/` (figures, CSV, report) is gitignored (`research/**/out/`).

## Prerequisite

`output/03_network__{nodes,edges}.gpkg` must exist (run the pipeline once).

## Run (in order)

```bash
cd research/road_road_connect
python3 01_fragmentation.py    # scope: size distribution, gap-to-backbone, anchor connectivity
python3 02_candidates_map.py   # show the close gaps are real noding artifacts (zoom maps)
python3 03_sensitivity.py      # tolerance sweep + before/after at 150 m
python3 04_optimize.py         # wide distance sweep → the component-minimizing knee (~450 m)
```

`rr_core.py` holds the road↔road rule (one connector per component to its nearest *other* component,
tolerance-gated) — the shared source of truth, analogous to the ice study's `bridge_core`.

## Conclusion

See [`FINDINGS.md`](FINDINGS.md). **Close the small road↔road gaps (≤ ~150 m)** — genuine cross-segment
noding artifacts; one tolerance-gated connector per component (the same proximity rule as the ice bridge,
emitted as a within-mode `Road` weld). That halves the component count (1,523 → 720) and grows the
backbone 69 % → 73 %. **Do not** fabricate the far regional links: Southeast Alaska, Canada GRIP4, and
Western village grids are 200–900 km separate roads, already tied into the multimodal giant via ports
(ferries) and airports (85 % of road nodes already reach the giant). One proximity rule, two tolerances:
road↔road at 150 m, ice↔road at 500 m.
