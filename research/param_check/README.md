# research/param_check — plausibility of the profile.yaml parameters

A diagnostic sandbox: are the `profile.yaml` tolerances plausible for the Alaska bulk-fuel network? It
measures each LIVE cap against the actual connectors in `output/03_network`, the hub-snap distance
distribution, and traces which `topology:` params the gold (Python-connect) pipeline still uses.

## Run
```
python3 research/param_check/01_param_plausibility.py
```
Prints the connection-cap distributions + the hub-snap distances and writes two figures.

## Result
**Live connection caps are plausible and mostly slack** — barge transfers 5 km (median 893 m), bridges 3 km
(welds median 60–450 m), connect-to-giant 2 km (median 212 m), airport snap 2 km (80/84 airports ≤ 2 km).
**Two issues:** the **hub-snap is uncapped** (roadless hubs snap up to **153 km**; 39 hubs > 20 km — the
100 km `max_snap_dist_m` is never enforced), and **much of `topology:` is dead** in the gold pipeline
(`topo_gap_m`, `transfer_max_dist`, `air_transfer_max_dist`, `noding_tol`, `manual_snap_tol`, `access_max_m`,
the `*_blend_tolerance` knobs — all legacy R-build only). Full per-parameter verdict + recommendations in
**`PARAM_EVALUATION.md`**. Evaluation only — no engine/profile change.

> **UPDATE (applied).** The dead `topology:`/`hubs:`/per-layer knobs this study flagged were later
> **removed** from `profile.yaml` + `mmnet/config.py` (dead-code cleanup, commit `6c93f1b`). The prose
> above describes params that no longer exist; kept as the historical rationale. The uncapped hub-snap
> is unchanged.
