# Plausibility of `profile.yaml` parameters — evaluation

Grounded in `output/03_network` + the data (`01_param_plausibility.py`) and a code trace of where each
parameter is consumed. **Diagnostic only — nothing changed in the engine/profile.**

> **UPDATE (applied).** Recommendation #2 below was implemented: the dead `topology:`/`hubs:`/per-layer
> knobs (`transfer_max_dist`, `air_transfer_max_dist`, `noding_tol`, `manual_snap_tol`, `topo_gap_m`,
> `access_max_m`, the `*_blend_tolerance` set, `snap_radius_m`, `max_snap_dist_m`, plus `multimodal_join`,
> `score_weights`, `major_places`) were **removed from `profile.yaml` and `mmnet/config.py`** in the
> dead-code cleanup (commit `6c93f1b`). The airport snap made `air_transfer_max_dist` doubly-dead. This
> document stays as the historical rationale; the tables below describe params that no longer exist in the
> profile. The one behavioural item — the uncapped hub-snap — is unchanged.

## Verdict in one line
The **live connection caps are well-sized and plausible**; the two issues are (1) the **hub-snap is
uncapped** — roadless hubs snap up to **153 km** to a road — and (2) **much of `topology:` is dead** in the
current (Python-connect) pipeline, a leftover of the legacy full-R build.

## (A) Connection caps — LIVE, plausible (mostly slack)
Measured connector lengths vs the profile cap:

| connector | param | cap | n | median | p90 | max | near-cap (>0.8·cap) | verdict |
|---|---|---|---|---|---|---|---|---|
| barge transfers | `transfers.max_dist` | 5000 | 201 | 893 | 3285 | 5072 | 9 | ✅ plausible; ~4 % near cap |
| road↔road weld | `bridges` | 3000 | 1262 | 106 | 400 | 2965 | 3 | ✅ plausible (noding gaps), generous cap |
| ice↔ice weld | `bridges` | 3000 | 26 | 443 | 2465 | 2710 | 3 | ✅ plausible |
| ice↔road bridge | `bridges` | 3000 | 10 | 61 | 2033 | 2449 | 1 | ✅ plausible |
| connect-to-giant | `connect_to_giant.max_dist` | 2000 | 81 | 212 | 804 | 1730 | 2 | ✅ well-sized (North Slope = 210 m) |
| airport snap | `snaps.max_dist` | 2000 | — | 80/84 ≤ 2 km (median 435 m) | | | 4 bush air-only | ✅ plausible |

Every connector sits comfortably under its cap (medians 60–900 m; a handful approach it). The caps are
realistic for Alaska logistics — a barge port within 5 km of a road, a village runway within 2 km of a road,
noding gaps ≤ 3 km. If anything they are slightly **generous** (could tighten `bridges`/`transfers` a bit),
but nothing is implausible or badly binding.

## (B) Stage 01 / 02 — LIVE, plausible
| param | value | role | verdict |
|---|---|---|---|
| `inventory…max_dist_m` (delivery fallback) | 5000 | fill blank delivery mode from nearest community marker | ✅ reasonable |
| `hubs.dedup_tol_m` | 50 | merge co-located tanks (Stage 01) | ✅ tanks at one facility |
| `hubs.buffer_dist` | 5000 | facility buffering for grouping | ✅ reasonable |
| `hubs.percentile` / `abs_threshold` | 0.90 / 500000 | hub threshold | ✅ reasonable default (data-dependent) |
| `hubs.group_by` | community, city, region | one hub per place | ✅ sound |
| `crs` 3338 / `precision` 1 | — | Alaska Albers, 1 m noding | ✅ correct |

## (C) `topology:` — mostly DEAD in the gold pipeline
The Python `connect_multimodal` uses the **per-rule** caps in `transfers`/`bridges`/`snaps`/`connect_to_giant`,
not these `topology:` scalars. A code trace shows most only fed the **legacy full-R build** / the graft / weld
oracles, which the Alaska gold path never runs:

| param | value | consumed by | live in gold? |
|---|---|---|---|
| `transfer_max_dist` | 5000 | legacy R contract only (gold uses `transfers[].max_dist`) | ❌ dead |
| `air_transfer_max_dist` | 10000 | legacy R contract; **air now SNAPS** (no transfer) | ❌ dead (doubly) |
| `noding_tol` | 150 | `weld_via_r` oracle only | ❌ dead |
| `manual_snap_tol` | 5 | `weld_via_r` oracle only | ❌ dead |
| `topo_gap_m` | 2000 | **0 code references** | ❌ dead |
| `access_max_m` | 5000 | `graft_via_r` (corridor layers) only | ❌ dead in Alaska build |
| `*_blend_tolerance` (road 500 / barge 2000 / air 10000) | — | full-R build; the **node-only** contract writes only `precision` | ❌ dead in gold |
| `snap_radius_m` / `max_snap_dist_m` | 75000 / 100000 | contract; **not enforced** in the gold hub-snap | ❌ not enforced (see below) |

These values are harmless (they don't affect the build) but **misleading** — e.g. `air_blend_tolerance: 10000`
and `air_transfer_max_dist: 10000` suggest air behaviour that no longer exists.

## The one real behavioural concern — uncapped hub-snap
`assemble.connect_multimodal` phase 2 snaps every Stage-02 hub to its nearest **ground** node
(`sjoin_nearest`, ground = Road ∪ Ice Road) with **no distance limit** — `max_snap_dist_m` is never applied.

- 02_hubs → snapped node: median **160 m** (fine for road communities) but **p90 ≈ 20 km** and **max ≈ 153 km**;
  **66 hubs snap > 5 km, 39 > 20 km, 2 > 100 km**.
- These are roadless barge/air villages: their hub is dragged tens–hundreds of km to a distant road, so the
  hub's *network position* is wrong (its barge link, via the `barge_hubs` anchor, is still at the village —
  an internal inconsistency).
- **Waterway is not a `snap_target`**, so a barge-only village hub can't snap to the water it actually uses.

## Recommendations (follow-up, not applied here)
1. **Cap the hub-snap.** Enforce `max_snap_dist_m` in `connect_multimodal` phase 2 (leave a hub at the
   community, or drop/flag it, when no ground node is within the cap), and lower the cap from 100 km to a
   plausible value (≈ 5–10 km). Optionally let barge/air hubs snap to the **waterway** (add it as a
   `snap_target` for barge hubs) instead of a far road.
2. **Prune or clearly mark the dead `topology:` knobs** (`topo_gap_m`, `transfer_max_dist`,
   `air_transfer_max_dist`, `noding_tol`, `manual_snap_tol`, `access_max_m`, `*_blend_tolerance`) as
   "legacy R-build only", so the profile reflects the gold Python pipeline.
3. The live caps (`transfers` 5 km, `bridges` 3 km, `connect_to_giant` 2 km, `snaps` 2 km) are fine; tighten
   only if you want stricter connectors.

## Figures (`out/`, regenerable)
`01_caps_vs_lengths.png` (connector lengths vs their caps), `01_hub_snap_cdf.png` (hub-snap distance CDF with
the 100 km line).
