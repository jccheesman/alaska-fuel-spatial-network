# research/ice_ice_connect

A tracked study (figures in `out/` gitignored): does the ice-road network need connecting **to itself**,
the way the road network did? Second step in the connection sequence (road↔road ✓ → **ice↔ice** →
road↔ice). Scripts + [`FINDINGS.md`](FINDINGS.md) are tracked.

## Prerequisite

`output/03_network__{nodes,edges}.gpkg` must exist (run the pipeline once).

## Run

```bash
cd research/ice_ice_connect
python3 01_ice_ice.py   # closest ice-component pairs, candidate maps, distance sweep + knee test
```

`ii_core.py` is the mode-generic within-mode core (shared design with the road study's `rr_core`).

## Conclusion

See [`FINDINGS.md`](FINDINGS.md). The ice network is already well-noded internally (closest gap 65 m, no
swarm) and the component count declines gradually with **no sharp knee** — the 47 components are mostly
separate winter-trail systems, not noding gaps. Only ~10 sub-300 m pairs are genuine branch gaps worth a
small within-mode weld (~150–300 m). The ice systems reach the wider network through **road** (the
road↔ice bridge, next study), not through each other.
