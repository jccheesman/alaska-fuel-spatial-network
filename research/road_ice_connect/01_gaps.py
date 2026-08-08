#!/usr/bin/env python3
"""STEP 01 — measure & classify the road↔ice-road gaps.

Extracts the IceRoad subgraph from the built network, finds each ice component's CLOSEST APPROACH to
the road network (both: any ice node → nearest road node, and the canonical dangle-endpoint rule the
engine will use), classifies by gap band, and writes a table. Run: python3 research/road_ice_connect/01_gaps.py
"""

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from _trace import OUT, Tracer
from bridge_core import candidate_connectors, load_network, mode_node_ids, mode_subgraph

T = Tracer("01_gaps", "STEP 01 — Road ↔ Ice-Road gap analysis")

T.stage("Inputs — the built network (output/03_network__*.gpkg)")
nodes, edges, xy = load_network()
N = len(nodes)
ice_g, ice_comps, ice_sub = mode_subgraph(edges, "IceRoad")
road_ids = mode_node_ids(edges, "Road")
ice_ids = mode_node_ids(edges, "IceRoad")
T.kv("network nodes / edges", f"{N:,} / {len(edges):,}")
T.kv("IceRoad edges / nodes", f"{len(ice_sub):,} / {len(ice_ids):,}")
T.kv("IceRoad components", len(ice_comps))
T.kv("Road nodes", f"{len(road_ids):,}")
T.note("R nodes each mode SEPARATELY, so an ice endpoint meters from a road is never joined across "
       "modes — that is the gap this study measures and the bridge step will close.")

T.stage("Per-component closest approach to the road network")
tree = cKDTree(xy[road_ids])
deg = dict(ice_g.degree())
rows = []
for ci, comp in enumerate(ice_comps):
    d_all, _ = tree.query(xy[comp])                       # any ice node → nearest road node
    dangles = [n for n in comp if deg.get(n, 0) == 1]
    d_dangle = tree.query(xy[dangles])[0] if dangles else np.array([np.inf])
    cx, cy = xy[comp].mean(0)
    rows.append({"comp": ci, "size": len(comp), "n_dangles": len(dangles),
                 "min_node_gap_m": float(np.min(d_all)),
                 "min_dangle_gap_m": float(np.min(d_dangle)),
                 "cx": cx, "cy": cy})
gaps = pd.DataFrame(rows).sort_values("min_node_gap_m").reset_index(drop=True)

# canonical connector rule (dangle-preferred), the exact rule the engine ships
conns = candidate_connectors(edges, xy, "IceRoad", "Road", prefer_dangle=True)
conn_gap = {c["comp"]: c["gap_m"] for c in conns}
gaps["connector_gap_m"] = gaps["comp"].map(conn_gap)

T.show(gaps.head(14), "closest 14 ice-road components (by min node→road gap)",
       cols=["comp", "size", "n_dangles", "min_node_gap_m", "min_dangle_gap_m", "connector_gap_m"])

T.stage("Gap-band classification (canonical connector gap)")
bands = [("≤ 100 m", 0, 100), ("100–500 m", 100, 500), ("500 m–1 km", 500, 1000),
         ("1–2 km", 1000, 2000), ("2–5 km", 2000, 5000), ("5–10 km", 5000, 10000),
         ("> 10 km", 10000, np.inf)]
cg = gaps["connector_gap_m"].to_numpy()
band_counts = {}
for lab, lo, hi in bands:
    k = int(((cg >= lo) & (cg < hi)).sum())
    band_counts[lab] = k
    T.kv(f"components with connector gap {lab}", k)

giant = gaps.loc[gaps["size"].idxmax()]
T.note(f"The GIANT ice system — {int(giant['size'])} nodes — sits {giant['min_node_gap_m']:.0f} m from a "
       f"road (its centroid is ~73 km away; centroid distance is misleading for large systems).")
n_close = int((cg <= 100).sum())
n_remote = int((cg > 10000).sum())
T.kv("near-touches (≤ 100 m)", n_close)
T.kv("genuinely remote (> 10 km)", n_remote)

# data regression guards (loose — protect against silent data drift)
assert len(ice_comps) == 47, f"expected 47 ice components, got {len(ice_comps)}"
assert len(ice_ids) == 931, f"expected 931 ice nodes, got {len(ice_ids)}"
assert len(ice_sub) == 1248, f"expected 1248 IceRoad edges, got {len(ice_sub)}"
assert n_close >= 5, f"expected >=5 near-touches (≤100 m), got {n_close}"
assert n_remote >= 30, f"expected >=30 remote (>10 km) components, got {n_remote}"
T.note("Data guards passed (47 comps / 931 ice nodes / 1248 ice edges; near-touch & remote bands).")

csv = OUT / "ice_gap_table.csv"
gaps.to_csv(csv, index=False)
T.kv("wrote", csv.relative_to(OUT.parent))
T.note("Next: 02_candidates_map.py renders a zoomed plausibility map per candidate; 03_sensitivity.py "
       "sweeps tolerances. Pick the tolerance from those, then set bridges[].max_dist in profile.yaml.")
T.done()
