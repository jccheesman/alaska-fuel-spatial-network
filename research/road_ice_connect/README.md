# research/road_ice_connect

A tracked **methodology study**: how to connect the road and seasonal ice-road networks where they
nearly meet, before porting the rule into the `mmnet` package. Unlike `explain/` (a disposable
walkthrough), the scripts here + [`METHOD.md`](METHOD.md) are committed; only the generated `out/`
(figures, CSVs, Markdown reports) is gitignored (`research/**/out/`).

## Prerequisite

Build the network once so `output/03_network__{nodes,edges}.gpkg` exist:

```bash
NETWEAVE_PROFILE=profile.yaml NETWEAVE_PROJECT=. \
  python3 -c "import mmnet; mmnet.run_pipeline('profile.yaml')"
```

## Run (in order)

```bash
cd research/road_ice_connect
python3 01_gaps.py            # measure & classify the ice→road gaps  -> out/ice_gap_table.csv + report
python3 02_candidates_map.py # per-candidate plausibility zoom maps   -> out/02_*.png
python3 03_sensitivity.py    # tolerance sweep + chart                -> out/sensitivity.csv + report
```

Each writes a dual stdout + Markdown transcript to `out/NN_*.md` (via the `_trace.Tracer`, copied
from `explain/`). `bridge_core.py` holds the connection rule — the single source of truth shared by all
three scripts and prototyped for the engine's `_proximity_bridges`.

## Output

- `out/01_gaps.md` — gap table, band classification, data guards.
- `out/02_candidates.md` — Alaska overview + one zoomed map per candidate (≤ 5 km) to judge plausibility.
- `out/03_sensitivity.md` — how many ice components attach to road per tolerance; the road-fragmentation note.

Read [`METHOD.md`](METHOD.md) for the conclusion and the recommended tolerance.
