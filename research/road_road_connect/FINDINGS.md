# Scoping — road-network fragmentation

**Question.** The road layer alone splits into **1,523 connected components** (backbone = 32,760 of
47,278 road nodes, 69%). Is that a fixable noding-quality problem, or genuine geography? How much
should `mmnet` try to connect?

## What the road network actually looks like (step 01)

**The count is dominated by tiny stubs.** 1,315 of 1,523 components have < 10 nodes; 917 lie within
**150 m** (the profile `noding_tol`) of another component — cross-segment gaps where adjacent AKDOT
segments don't share an exact endpoint. But closing **all** ≤ 150 m gaps (transitive) only moves the
count 1,523 → 756 and the backbone 32,760 → 34,742 (**69% → 73.5%**). Noding-snap tidies the *count*; it
does **not** unify Alaska's roads.

**The big secondary systems are separate regional networks, not noding gaps.** Gap from each large
(≥ 200-node) component to the *backbone* specifically:

| comp | nodes | gap to backbone | region |
|---|---|---|---|
| 1 | 1,153 | 539 km | interior / western village grid |
| 2 | 633 | 926 km | far SE / Canada (GRIP4) |
| 3 | 532 | 204 km | Kenai / Southcentral |
| 4 | 474 | 784 km | far SE / Canada (GRIP4) |
| **5** | **416** | **102 m** | interior — the lone large **noding gap** that belongs to the backbone |
| 6–10 | 200–388 | 290–770 km | interior / Canada / south |

Southeast Alaska, the Canada GRIP4 roads, and Western-Alaska village grids genuinely have **no road**
to the Interior. Fabricating a 200–900 km "road" to merge them would be wrong.

## The key result — they're already connected, the right way

**9 of the 10 largest regional road systems are already in the full multimodal giant**, joined through
**ports** (Alaska Marine Highway ferries ≈ barge) and **airports** — the physically-correct connectors.
Counting all modes, **85.3 % of road nodes (40,333 / 47,278) already reach the giant**. The road
"fragmentation" is largely an artifact of looking at the road layer in isolation; the multimodal network
resolves it through anchors. Only **comp 9 (213) and comp 12 (174)** — Canada GRIP4 pieces — sit outside
the giant because they have no AK port/airport anchor, plus the ~29 tiny grids > 5 km from anything.

## The connection experiment (steps 02–03)

Apply the **same proximity rule as the ice study, within the road mode**: connect each non-backbone road
component to its closest *other* road component, one connector per component, gated by a tolerance (the
chain transitively merges the stub swarm). The candidate maps (`out/02_*.png`) show the close gaps are
genuine **noding artifacts** — e.g. comp 1 (1,153 nodes, a city grid) sits **15.8 m** from comp 160 with
the road ends aligned; the break disappears when the connector is drawn. Plausibility holds to ~150 m;
by ~300 m the two ends merely "point at each other" across open ground (judgment calls).

Tolerance sweep (`out/03_sensitivity.png`, before/after at 150 m in `out/03_before_after.png`):

| tol | connectors | components after | backbone | longest |
|---|---|---|---|---|
| 10 m | 29 | 1,502 | 69.4% | 9 m |
| 50 m | 277 | 1,299 | 70.0% | 50 m |
| **150 m** | **917** | **720** | **72.6%** | 149 m |
| 300 m | 1,208 | 457 | 73.9% | 298 m |
| 500 m | 1,332 | 344 | 74.3% | 496 m |
| 1 km | 1,389 | 291 | 74.6% | 957 m |

Closing **≤ 150 m** gaps halves the component count (1,523 → 720) and grows the backbone 69 % → 73 %.

## Optimization — the distance that minimizes components (step 04)

Merging any two road components within distance `d` (true minimum-components model), components fall:
1,523 → 696 (150 m) → 410 (300 m) → **299 at the knee ≈ 450 m** → 285 (500 m) → 223 (1 km) → 120 (50 km).
The curve **knees at ~450 m**: 50–150 m removes 600 components, 150–300 m removes 286, 300–500 m removes
125, then it flattens (−62 over 500 m–1 km, −28 over 1–2 km). Components keep falling only by fabricating
ever-longer non-road links toward the 120-component floor (the genuinely-separate regional systems).
Backbone fraction tracks it: 69 % → 76 % by ~500 m, then plateau. See `out/04_optimize.png`.

So the **component-minimizing distance is ~450 m** (the knee). The tension: the step-02 maps show
connectors beyond ~150–300 m become road ends merely pointing at each other across open ground (judgment
calls), while ≤ 150 m are unambiguous noding gaps. **150 m = conservative/clearly-noding; ~450 m =
maximal component reduction before diminishing returns.**

## Recommendation

1. **Close the small road↔road gaps (≤ ~150 m) — simple and logical.** These are cross-segment noding
   artifacts (road ends that should share a node but sit meters apart). One tolerance-gated connector per
   component, the same rule as the ice bridge. Recommended tolerance **150 m** (the profile `noding_tol`):
   every connector in that band reads as a road-end mismatch on the maps; by 300 m+ they become judgment
   calls, so stop at ~150 m. Semantically these are road continuations, not intermodal transfers — emit
   them as `Road` (a within-mode weld), not as a `Bridge`/`Transfer`.
2. **Do NOT fabricate the far regional links.** Southeast Alaska, Canada GRIP4, and Western village grids
   are 200–900 km from the backbone — real separate road networks. They are already tied into the
   multimodal giant via **ports (ferries) and airports**; 85 % of road nodes already reach the giant.
   No road link to invent there.
3. **Anchor coverage is the remaining lever.** comp 9 / comp 12 (Canada GRIP4) sit outside the giant for
   lack of a port/airport anchor — a short follow-up can check each unanchored regional grid against real
   Marine-Highway / air service.

**Bottom line — one proximity rule, two tolerances:** road↔road at **150 m** (within-mode noding weld) and
ice↔road at **500 m** (cross-mode bridge). The close gaps get connected the simple, logical way; the far
regional systems correctly ride the ferry/air anchors. This is the unified mechanism to port into `mmnet`.
