# research/waterway_network

Defines the **Alaska waterway network** from the raw National Waterway Network (NWN) — the input for a
later waterway↔road connection study. The built network's waterway is only a facility-bbox clip (282
edges); this extracts the real Alaska marine network. Tracked scripts + `FINDINGS.md`; `out/` gitignored.

Uses the **mmnet package as-is**: ports via `mmnet.build._load_anchor("ports", cfg)`, barge hubs from
`output/02_hubs.gpkg` (delivery_method contains "Barge"). No new data abstractions.

## Prerequisite

`output/02_hubs.gpkg` exists (run the pipeline once); `data/raw/connectivity/barge/NWN_Waterway_Network_Lines/`.

## Run

```bash
cd research/waterway_network
python3 01_ak_waterway.py
```

Prints the two-extent comparison + port/barge-hub coverage; writes `ak_waterway_{akonly,akspine}__edges.gpkg`,
the side-by-side map, and the transcript.

## Conclusion

See [`FINDINGS.md`](FINDINGS.md). The Alaska waterway is one fully-connected marine network:
**AK-only = 316 lines / 31,903 km / 1 component**; **AK+spine** adds the Pacific deep-water spine to the
lower-48 (39,433 km). Coverage: 94/147 ports and 107/202 barge hubs within 5 km. Pick AK-only for the
Alaska network proper, or AK+spine to model the lower-48 barge supply line. The chosen `.gpkg` feeds the
follow-up waterway↔road connection (ports = mmnet anchor, barge hubs = demand).
