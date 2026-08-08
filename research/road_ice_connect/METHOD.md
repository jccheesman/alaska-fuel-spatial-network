# Method — connecting the road ↔ ice-road networks

**Problem.** R nodes each mode's lines *separately* into an sfnetwork, so an ice-road endpoint that
lies meters from a road is never joined across modes. After the weld-leftover step was removed, all 47
ice-road components are isolated — correct for genuinely remote winter routes, but it over-isolates the
ice systems that physically touch the road network.

**Goal.** A robust, profile-driven rule that connects an ice-road component to the road network at its
single closest approach — one connector per component — **only when the real gap is within a tolerance**.
The principled replacement for the deleted weld: tolerance-gated, geometry-real, evaluated.

## What the data shows (step 01)

47 ice components · 931 ice nodes · 1,248 IceRoad edges · 47,278 road nodes. Closest approach per ice
component (the canonical dangle-endpoint → nearest-road-node rule):

| band | # ice comps | reading |
|---|---|---|
| ≤ 100 m | **6** | gaps 1–87 m — cross-mode near-touches never noded. Incl. the **728-node / 4,052 km** NW-Alaska (Kotzebue-area) winter-trail system at **18 m**. |
| 442 m | 1 | a clean ramp onto a road junction (visually plausible) |
| 1.07 / 1.99 / 2.45 km | 3 | plausible winter ramps — judgment calls |
| 5–10 km | 1 | borderline |
| **> 10 km** | **36** | genuinely remote routes to roadless villages — must stay isolated |

Component **centroid** distance is misleading (the 728-node system's centroid is ~73 km from roads, yet
the system itself touches a road at 18 m). Use **node-level closest approach**, preferring degree-1
**dangle** endpoints — the natural ramp ends.

## The rule (shipped in `bridge_core.candidate_connectors`, ported to the engine)

For each disconnected component of `from_mode` (Ice Road):
1. candidate attach points = the component's degree-1 **dangles** (fallback: all its nodes);
2. find the single **closest** `to_mode` (Road) node via a `cKDTree` arg-min (deterministic: sort
   components and nodes by id);
3. emit **one** connector (ice dangle → nearest road node) **iff** gap ≤ `max_dist`.

Properties: tolerance-gated (no connector longer than `max_dist`), one per component (no over-connecting),
idempotent/deterministic, leaves the 36 remote components isolated, and mode-pair-parameterized (not
ice-specific). Geometry: **snap to nearest road node** (chosen) — simple, reuses the anchor-transfer
pattern, negligible accuracy loss at these gaps.

## Tolerance sensitivity (step 03)

| tol | ice comps bridged | onto main backbone | ice nodes folded in | longest connector |
|---|---|---|---|---|
| 100 m | 6 | 4 | 765 | 87 m |
| 500 m | 7 | 5 | 812 | 442 m |
| 1 km | 7 | 5 | 812 | 442 m |
| 2 km | 9 | 6 | 816 | 1,987 m |
| 5 km | 10 | 6 | 818 | 2,449 m |

**Recommended default: `max_dist = 500 m`** — captures all six near-touches (incl. the 728-node system)
plus the one clean 442 m ramp; every connector is visually plausible (step 02 maps); excludes the 1–2.5 km
judgment-call ramps and all 36 remote systems. Raise to **2,000 m** to include the plausible ramps after
eyeballing `out/02_cand_08/09/10_*.png`.

## Separate finding — the road network is itself fragmented (out of scope here)

The whole-network "giant fraction" barely moves (83.8% → 83.9%) even when ice is correctly bridged,
because **the road network is fragmented into 1,523 components** (largest holds 40,683 of 48,563 nodes).
The 728-node ice system attaches at 18 m to a **157-node village road stub**, not the highway backbone —
which is real winter geography (ice trails link villages; each village has a small local road grid not
tied to the Dalton/Parks highway system). Connecting those village road grids to the backbone is a
**separate** road↔road connectivity problem; this study scopes only the ice→road attachment.

## Port to `mmnet` (after the tolerance is locked)

Add a declarative `bridges:` section + `BridgeSpec` (config), a `_proximity_bridges` helper + phase 3.5
in `connect_multimodal` (after anchor transfers, before component labeling), wiring in `build_network`,
and a `Bridge` edge type in `viz.py`. The engine reuses this exact rule; this sandbox then imports the
shipped helper to stay a single source of truth.
