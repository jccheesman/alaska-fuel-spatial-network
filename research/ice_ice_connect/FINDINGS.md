# Ice ↔ ice connection study

**Question (step in the user's sequence: road↔road ✓ → ice↔ice → road↔ice).** The ice-road network
splits into **47 components** (one 728-node giant + 46 small). Are these noding gaps to weld, like the
road stubs, or genuinely separate winter-trail systems?

## What the data shows

The ice network is **already well-noded internally** — the closest gap between any two ice components is
**65.5 m** (roads, by contrast, had sub-metre near-touches in a swarm of 917). The pairwise gaps spread
across a continuum:

| gap band | # component pairs |
|---|---|
| ≤ 100 m | 2 |
| 100–300 m | 8 |
| 300–500 m | 6 |
| 500 m–1 km | 6 |
| 1–5 km | 24 |
| > 5 km | 78 |

Merging components within distance `d` declines the count **gradually, with no sharp knee** (knee
strength 0.10 vs the road curve's clear bend): 47 → 45 (100 m) → 37 (300 m) → 33 (500 m) → 27 (1 km) →
16 (5 km) → 6 (50 km). See `out/01_ice_optimize.png`. There is **no natural minimizing distance** — the
components are separate trail systems at every scale, not a noding-gap swarm.

## Candidate inspection (the few close pairs)

The ~10 sub-300 m pairs are genuine branch gaps worth closing — the maps show it:
- **comp 29 ↔ 34 (65 m):** one trail digitized in two pieces, meeting at a junction (`out/01_cand_01.png`).
- **comp 0 ↔ 21 (168 m):** a 2-node trail branches off the giant's junction but wasn't noded in
  (`out/01_cand_05.png`).

Beyond ~300 m the pairs are distinct trails running to different places.

## Recommendation

1. **Close only the few genuine branch gaps — a small tolerance (~150–300 m).** ~8–10 ice-component
   pairs at 65–300 m are trails that branch from a shared junction but weren't noded together; weld them
   within the IceRoad mode (same proximity rule as road↔road, smaller tolerance). Unlike roads there is
   **no knee** to optimize — the cut is driven by plausibility (the candidate maps), not a curve bend.
2. **Do NOT bulk-merge ice components.** The other ~37 components are real separate winter-trail systems
   (65 m to 50 km apart at a continuum); merging them would fabricate trails that don't exist.
3. **The ice systems join the wider network through ROAD, not each other.** The giant ice system + the
   close components attach to village roads via the **road↔ice bridge** (the next study, 500 m). Ice↔ice
   is a minor cleanup; the real connectivity for ice comes from the cross-mode step.

**Bottom line:** ice↔ice is a light touch — weld ~10 short branch gaps (≤ ~300 m), leave the separate
trail systems alone. Contrast with road↔road (a real noding swarm with a 450 m knee). Next: road↔ice.
