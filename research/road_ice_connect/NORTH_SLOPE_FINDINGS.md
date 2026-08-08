# North Slope road↔ice findings (road + ice only)

Follow-up to a question: an ice road looked close to a grey road in the south of the North Slope view —
why wasn't it connected there, while a 55 km gap was highlighted in the north? Investigated with
`04_deadhorse_gap.py`, `05_northern_ice.py`, `06_reachability.py` (road + ice only — no barge/air).

## Two different northern ice systems (I had conflated them)

| ice system | size | nearest road | distance to the **Dalton backbone** |
|---|---|---|---|
| **Barrow / North Slope giant** | 728 nodes | Barrow grid, 18 m (a disconnected local grid) | **55 km** |
| **Deadhorse piece** ← the southern point | 10 nodes | **the Dalton Highway, 2.4 km** | **2.4 km** |

The southern ice-near-road point is the **Deadhorse piece**: a 10-node ice road sitting **2.4 km from the
Dalton Highway backbone** (`out/04_deadhorse_gap.png`, with a 1 km scale bar). The road↔ice rule skipped
it only because the tolerance was **500 m** (2.4 km > 500 m). A ≥ 2.5 km tolerance would connect it — but
it is a small ~10-node win.

## Connecting it does NOT connect the ice network

The Barrow giant and the Deadhorse piece are **separate systems, 57 km apart**, and the giant is 55 km
from the Dalton. So connecting the Deadhorse 2.4 km gap attaches only those ~10–14 nodes. Applying **both**
ice↔ice and road↔ice at a common tolerance (`out/06_reachability.png`):

| tolerance | ice nodes reaching the road backbone |
|---|---|
| 0.25–2 km | 4 / 931 (0.4%) |
| 3–10 km | **14 / 931 (1.5%)** |

The reachability is **capped at ~2% even at 10 km**. The 728-node Barrow system never chains in — it is
genuinely 55 km from the Dalton with no road or ice across that gap. `05_northern_ice.png` shows the
fragmentation: the northern ice splits into ~41 components scattered across the Slope, each at a different
distance from the backbone.

## Conclusion (road + ice only)

- The ice **is** connected to its local roads where they physically meet (e.g. Barrow grid, 18 m).
- It **cannot** be connected to the road backbone by short proximity links — the ice network is genuinely
  fragmented and the big system is 55 km out. Raising the tolerance buys almost nothing (~2% ceiling).
- The southern point you spotted is real and connectable (Deadhorse, 2.4 km to the Dalton) but minor.
- The only lever to connect the big Barrow system would be a **missing winter-route segment** in
  `Ice_Roads.shp` (a data question), not a larger tolerance.

These are research findings only — no engine/profile changes were made.
