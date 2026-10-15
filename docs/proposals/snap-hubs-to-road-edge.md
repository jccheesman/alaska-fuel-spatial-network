# Proposal — snap hubs to the nearest road EDGE, not just the nearest node

Status: **IMPLEMENTED** · 2026-10-15 · rescue-only, 2 km, default off (Alaska profile = 2000) ·
shipped in `assemble.py` + `config.py` + profile + `tests/test_hub_builder.py`; in the 2026-10-15
network-of-record

## Problem

In the corrected 2026-10-15 rebuild, **7 of 46 unplaced hubs sit ≤5 km from a road line
the network already contains, yet their nearest road *node* is 25–40 km away**, so hub
snapping drops them as `unplaced:beyond_cap`:

| hub | community | mode | dist to road **line** | dist to nearest **node** | nearest edge len |
|---|---|---|---|---|---|
| Hub_234 | blob:48 | Road | 0.08 km | 29.9 km | 86 km |
| Hub_335 | Glennallen | Plane | 0.30 km | 26.4 km | 86 km |
| Hub_298 | **Chistochina** | Road | 0.35 km | 38.3 km | 95 km |
| Hub_327 | Fairbanks | Road | 1.39 km | 32.5 km | 104 km |
| Hub_344 | Valdez | Plane | 1.82 km | 30.6 km | 86 km |
| Hub_342 | blob:37 | Plane | 3.63 km | 39.0 km | 175 km |
| Hub_328 | Bettles Field | Plane | 4.06 km | 27.3 km | 85 km |

Several are plainly road-connected towns (Glennallen, Fairbanks, Valdez). They are not
missing roads and not mis-located — they sit *mid-edge* on a very long road segment.

## Root cause

`connect_multimodal` builds its global node table **only from edge endpoints**
(`assemble.py:92–110`, "global node table from edge endpoints (rounded) — no re-noding"),
and the AK-DOT road layer is noded as **84–175 km single edges**. Hub snapping then does a
nearest-**node** join (`assemble.py:183–185`, `gpd.sjoin_nearest(h, snap_nodes)`). A hub in
the middle of a 95 km edge is 0.35 km from the *line* but 38 km from either *endpoint*, so it
exceeds `max_snap_dist_m` (25 km) and is left unplaced — a false negative.

Verified: Chistochina's nearest road edge is 94.9 km long, passing 0.35 km away, with endpoint
nodes 38.3 km and 47.2 km off.

## Why not just raise `max_snap_dist_m`

Raising the cap to 40 km would "place" Chistochina by snapping it to a node **38 km down the
highway** — pinning the hub 38 km from the real town. That is worse than unplaced. (Placed
community hubs today snap within 19.7 km max / 12.5 km at the 99th percentile — see the
threshold analysis; 25 km is already well-chosen.) The gap is a *noding-granularity* problem,
not a distance problem, so the fix must be geometric, not a bigger radius.

## Proposed change — an edge-projection snap tier

Add a third snapping tier to `connect_multimodal`, run **only for hubs still unplaced** after
the existing node-snap + own-mode fallback (minimal blast radius):

1. For each still-unplaced hub, find the nearest **snap-type edge** (Road ∪ IceRoad) via an
   STRtree / `edges.sindex.nearest` over edge geometries.
2. Project the hub onto that edge → landing point `p`.
3. If `dist(hub, p) ≤ snap_to_edge_tol_m` (a new, conservative knob — "this close means the
   hub is on the road"), **split the edge at `p`**: replace edge `(a, b)` with `(a, n)` and
   `(n, b)`, where `n` is a new shared node registered in the node table at `p`; both halves
   inherit the original `type` / `source` / `edge_label`, with geometries sliced at `p`.
4. Attach the hub to node `n` using the existing placed / merge / `02_hub_snaps.csv` logic
   (`snap_surface` = the edge's mode; `snap_dist_m` = `dist(hub, p)`).

This **generalizes the existing `_weld_barge_landings`** pattern (`build.py:97–141`), which
already projects a manual-barge endpoint onto a waterway edge and inserts a shared vertex. We
reuse the same idea for a hub landing on a road/ice edge.

### Design details
- **Scope to ground edges first** (Road ∪ IceRoad — the `snap_types`). The waterway is already
  finely noded (vertex-rounded), and air is a separate snap mechanism; leave both out initially.
- **New knob `hubs.snap_to_edge_tol_m`** (config `HubParams`, surfaced in `profile.yaml`),
  default conservative (~2000 m). Distinct from `max_snap_dist_m`: this is "on-road" proximity,
  not a search radius. All 7 cases are ≤4.1 km; a 2–5 km tol captures them. Keep it small so a
  hub near a road it isn't served by does not wrongly attach.
- **Determinism**: nearest-edge ties broken by edge index; the split node id is appended in
  stable order and registered in `coord_id` so later welds dedupe against it.
- **Rescue-only vs all-hubs**: rescue-only (above) changes the least. A stronger variant would
  project *every* hub to its nearest edge (fixing placed-but-mis-pinned hubs too — see Caveats);
  propose rescue-only first, revisit all-hubs after reviewing the cost-accuracy check.

## Scope of impact
- Rescues ~7 currently-unplaced hubs (incl. Chistochina + the Glennallen/Fairbanks/Valdez
  `remote_site`s beside long edges). **Does not touch the 39 genuinely-far hubs** (where the road
  *line* itself is 25–118 km away) — this is a precision fix, not a cure-all.
- Each split turns 1 edge into 2 and adds 1 node → **node/edge/hub counts change ⇒ a NEW
  network-of-record.** The `EXPECTED` tripwire (`03_multimodal_join/02_load_final_network.py`),
  the checksums (`inputs/MANIFEST.md`, `final_network/README.md`, CI) and every edge_id-keyed
  table must regenerate together, owner-gated — the `edge_id = shapefile row order` contract
  means any edge-set change is by definition a deliberate re-export.

## Caveats / risks
- **Cost accuracy (good)**: splitting a 95 km edge at the landing yields two halves that keep
  the same per-mile rate, so total line-haul cost is unchanged; the hub simply attaches at the
  right place. No cost distortion.
- **Over-attachment (watch)**: a hub near a road it isn't actually served by could wrongly weld.
  Mitigated by a small `snap_to_edge_tol_m` and by the model's premise that the last delivery
  mile is a truck. Log every edge-snap with its distance; flag any > ~1 km for a look.
- **Placed-but-mis-pinned hubs**: the same long edges likely pin some *already-placed* hubs to a
  distant endpoint (placed, but attached kilometres from their real position). Rescue-only leaves
  those as-is; the all-hubs variant would fix them but is a larger change — gate on the separate
  cost-accuracy check.
- **Interaction**: the new node must enter `coord_id`/`node_tol` rounding so downstream
  `connect_to_giant` and transfer passes see it like any other node.

## Alternative considered — global node densification
Add every edge vertex as a node before snapping. Simpler to state, but explodes the node table
(long highways carry many vertices), changes the whole topology, and inflates every downstream
table. Edge-projection splits **only where a hub actually lands** — surgical, far smaller delta.

## Verification
- After implementing + rebuild (EXPORT off): the 7 mid-long-edge hubs become `status=placed`
  and reachable; Chistochina attaches at ≤0.35 km. The 39 far hubs are unchanged.
- Each split edge's two halves sum to the original length and keep `edge_label`/`type`/`source`.
- Re-run `05_verify_north_slope.py`; confirm no connectivity regression.
- New fixture in `tests/test_hub_builder.py`: a hub placed mid-edge on a long synthetic road
  snaps to a freshly split node at the projection point, not to a far endpoint.

## Files to touch (when approved)
- `source_scripts/mmnet/assemble.py` — `connect_multimodal`: edge-projection tier after the
  node-snap/fallback block (~L203); helper `_split_edge_at(point, edge)` mirroring
  `build.py::_weld_barge_landings`.
- `source_scripts/mmnet/config.py` — `HubParams`: add `snap_to_edge_tol_m`.
- `workflows/02_network_build/profile.yaml` — `hubs.snap_to_edge_tol_m`.
- `tests/test_hub_builder.py` — the mid-long-edge fixture.
