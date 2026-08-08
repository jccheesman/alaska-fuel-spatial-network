# research/airport_connection — how airports connect (transfer edge vs snap-to-road)

A verification/analysis sandbox: how are the airports connected to the multimodal network, and would
**snapping them to the road** (the requirement) differ from the current **transfer-edge** approach?

## Run
```
python3 research/airport_connection/01_airport_connection.py
```
Reads `output/03_network`, characterizes the current air↔road transfers, measures each airport's distance to
the nearest road node, builds a SNAPPED variant (merge air→road, drop the transfer) and compares connectivity,
and draws the current-vs-snapped maps.

## Result
Airports today connect via **78 air↔road `Transfer` edges** (`profile.yaml:156` → `connect_multimodal`
phase 3) — **0 are snapped** onto the road. But **78/84 airports are within 1 km of a road** (median 0.4 km),
and a snapped variant keeps the **same connectivity** (67 components, giant 98.6 %) with 78 fewer nodes/edges.
**Recommendation: snap airports onto the nearest road node instead of a transfer edge** (the 6 bush fields
> 1 km stay air-only). Full writeup + the exact code change in **`FINDINGS.md`**. Research only — no engine edit.
