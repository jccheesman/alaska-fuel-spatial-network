#!/usr/bin/env python3
"""STEP 03 — tolerance sensitivity sweep.

For a sweep of tolerances, apply the canonical one-connector-per-component rule and report how many ice
components connect, how many ice nodes fold into the road giant, the network giant-fraction before/after,
and (a hard check) that the 36 genuinely-remote components NEVER connect. Output: a table + a bar chart
to justify the tolerance you set in profile.yaml. Run: python3 research/road_ice_connect/03_sensitivity.py
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from _trace import OUT, Tracer
from bridge_core import candidate_connectors, giant_fraction, load_network, mode_subgraph

SWEEP = [100, 500, 1000, 2000, 5000]      # metres

T = Tracer("03_sensitivity", "STEP 03 — Tolerance sensitivity sweep")
nodes, edges, xy = load_network()
N = len(nodes)
ice_g, ice_comps, _ = mode_subgraph(edges, "IceRoad")
conns = candidate_connectors(edges, xy, "IceRoad", "Road", prefer_dangle=True)
nc0, gf0 = giant_fraction(edges, N)        # baseline (no bridges)
T.kv("baseline components / giant", f"{nc0:,} / {gf0:.1%}")

# --- the bridge's JOB is ice→road (mode-level). The whole-network giant fraction is confounded by
#     the road network's OWN fragmentation, so we also measure ice-centric success directly. ---
G0 = nx.Graph(); G0.add_nodes_from(range(N)); G0.add_edges_from(zip(edges["from"], edges["to"]))
base_comp = {n: i for i, c in enumerate(sorted(nx.connected_components(G0), key=len, reverse=True))
             for n in c}
road = edges[edges["type"] == "Road"]
road_comp_count = nx.number_connected_components(nx.Graph(list(zip(road["from"], road["to"]))))
T.note(f"NOTE — the road network is itself fragmented into {road_comp_count:,} components (largest holds "
       f"{int(gf0*N):,} of {N:,} nodes). So 'whole-network giant fraction' barely moves even when an ice "
       "system is correctly bridged onto a small road stub. Road↔road connectivity is a SEPARATE problem; "
       "here we measure the bridge's real job: attaching ice components to the road network.")
T.note("Rule per tolerance: bridge every ice component whose closest approach ≤ tol, one connector each "
       "(the exact rule the engine ships). Remote components (> 10 km) must never connect at any tol.")

remote_comps = {c["comp"] for c in conns if c["gap_m"] > 10000}
rows = []
for tol in SWEEP:
    chosen = [c for c in conns if c["gap_m"] <= tol]
    pairs = [(c["from_node"], c["to_node"]) for c in chosen]
    ncc, gfc = giant_fraction(edges, N, extra_pairs=pairs)
    ice_nodes_added = sum(len(ice_comps[c["comp"]]) for c in chosen)
    # how many of the bridged ice components attach to the MAIN road backbone (the giant)?
    to_giant = sum(1 for c in chosen if base_comp[c["to_node"]] == 0)
    max_len = max((c["gap_m"] for c in chosen), default=0.0)
    assert not (remote_comps & {c["comp"] for c in chosen}), f"remote comp connected at tol={tol}!"
    rows.append({"tol_m": tol, "ice_comps_bridged": len(chosen), "to_main_backbone": to_giant,
                 "ice_nodes_attached": ice_nodes_added, "longest_connector_m": round(max_len),
                 "components_after": ncc, "giant_after": gfc})
sweep = pd.DataFrame(rows)
sweep["giant_after_pct"] = (sweep["giant_after"] * 100).round(1)
T.show(sweep, "tolerance sweep — ice components attached to the road network",
       cols=["tol_m", "ice_comps_bridged", "to_main_backbone", "ice_nodes_attached",
             "longest_connector_m", "components_after", "giant_after_pct"])
T.note(f"At 100 m: {int(sweep['ice_comps_bridged'].iloc[0])} ice components attach to road "
       f"({int(sweep['to_main_backbone'].iloc[0])} onto the main backbone), folding in "
       f"{int(sweep['ice_nodes_attached'].iloc[0])} ice nodes. The 728-node system attaches at ≤ 100 m but "
       "to a 157-node road stub, so the whole-network giant fraction barely changes — that is the road "
       "fragmentation, not a bridge failure.")

fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5))
labels = [f"{t} m" for t in SWEEP]
a1.bar(labels, sweep["ice_comps_bridged"], color="#17becf", label="bridged to road")
a1.bar(labels, sweep["to_main_backbone"], color="#1f77b4", label="onto main backbone")
for i, v in enumerate(sweep["ice_comps_bridged"]):
    a1.text(i, v, str(int(v)), ha="center", va="bottom")
a1.axhline(len(ice_comps), color="#999", ls=":", lw=1)
a1.text(0, len(ice_comps), f"  all {len(ice_comps)} ice comps", va="bottom", fontsize=8, color="#666")
a1.legend(loc="center right", fontsize=8); a1.set_title("ice components attached to the road network")
a2.bar(labels, sweep["ice_nodes_attached"], color="#2ca02c")
for i, v in enumerate(sweep["ice_nodes_attached"]):
    a2.text(i, v, f"{int(v)}", ha="center", va="bottom", fontsize=9)
a2.set_title("ice nodes folded into the road network")
fig.suptitle("Tolerance sensitivity — ice→road attachment per tolerance "
             f"(road net itself fragmented: giant ≈ {gf0:.0%})", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.94])
p = OUT / "03_sensitivity.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Sensitivity — components connected and giant-fraction vs tolerance")

sweep.to_csv(OUT / "sensitivity.csv", index=False)
T.kv("wrote", "out/sensitivity.csv")
T.note("Pick the tolerance where the candidate maps (step 02) stop being plausible. Set it as "
       "bridges[].max_dist in profile.yaml; the engine applies this exact rule during the build.")
T.done()
