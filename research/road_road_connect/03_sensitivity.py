#!/usr/bin/env python3
"""STEP 03 — road↔road tolerance sweep + before/after.

Applies the closest-approach rule (one connector per non-backbone component, transitively merging) at a
sweep of tolerances and reports component-count reduction and backbone growth. Then renders a before/after
map at a chosen tolerance so the connectivity gain is visible. Run:
python3 research/road_road_connect/03_sensitivity.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _trace import OUT, ROOT, Tracer
from rr_core import apply_and_measure, closest_connectors, load_network, road_components

SWEEP = [10, 50, 150, 300, 500, 1000]      # metres
SHOW_TOL = 150                              # before/after map tolerance

T = Tracer("03_sensitivity", "STEP 03 — Road↔road tolerance sweep + before/after")
nodes, edges, xy = load_network()
road, ids, comps, comp_of = road_components(edges)
conns = closest_connectors(ids, xy, comps, comp_of)
nc0, big0, gf0, _ = apply_and_measure(ids, edges, comps, conns, tol=0)
T.kv("road nodes", f"{len(ids):,}")
T.kv("baseline components / backbone", f"{nc0:,} / {big0:,} ({gf0:.1%})")

rows = []
for tol in SWEEP:
    nc, big, gf, n_applied = apply_and_measure(ids, edges, comps, conns, tol)
    rows.append({"tol_m": tol, "connectors_applied": n_applied, "components_after": nc,
                 "backbone_after": big, "backbone_pct": round(gf * 100, 1),
                 "longest_connector_m": round(max((c["gap_m"] for c in conns if c["gap_m"] <= tol),
                                                  default=0))})
sweep = pd.DataFrame(rows)
T.show(sweep, "road↔road tolerance sweep", n=len(sweep),
       cols=["tol_m", "connectors_applied", "components_after", "backbone_after", "backbone_pct",
             "longest_connector_m"])
T.note(f"Backbone grows {gf0:.1%} → {sweep['backbone_pct'].iloc[2]:.1f}% at 150 m → "
       f"{sweep['backbone_pct'].iloc[-1]:.1f}% at 1 km. The count drops sharply (noding stubs merge), "
       "but the backbone fraction rises modestly because most stubs merge into each other, and the "
       "far regional systems (200–900 km out) never qualify — they ride the ferry/air anchors instead.")

fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5))
labels = [f"{t} m" for t in SWEEP]
a1.bar(labels, sweep["components_after"], color="#4a90c2")
for i, v in enumerate(sweep["components_after"]):
    a1.text(i, v, f"{int(v):,}", ha="center", va="bottom", fontsize=9)
a1.axhline(nc0, color="#d62728", ls="--", lw=1, label=f"baseline {nc0:,}")
a1.legend(loc="upper right", fontsize=8); a1.set_title("road components after merging noding gaps")
a2.bar(labels, sweep["backbone_pct"], color="#2ca02c")
a2.axhline(gf0 * 100, color="#d62728", ls="--", lw=1, label=f"baseline {gf0:.1%}")
for i, v in enumerate(sweep["backbone_pct"]):
    a2.text(i, v, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)
a2.set_ylim(0, 100); a2.legend(loc="lower right", fontsize=8)
a2.set_title("road backbone fraction")
fig.suptitle("Road↔road noding-gap closure — count drops, backbone grows modestly", fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.94])
p = OUT / "03_sensitivity.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, "Sensitivity — components and backbone fraction vs road-road tolerance")
sweep.to_csv(OUT / "sensitivity.csv", index=False)

# ---------------------------------------------------------------- before / after map
T.stage(f"Before / after at {SHOW_TOL} m — connectivity made visible")
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(nodes.crs)
back_before = set(comps[0])
# recompute components after adding ≤SHOW_TOL connectors to color the new backbone
import networkx as nx
g = nx.Graph(); g.add_nodes_from(ids)
g.add_edges_from(zip(road["from"], road["to"]))
g.add_edges_from((c["from_node"], c["to_node"]) for c in conns if c["gap_m"] <= SHOW_TOL)
back_after = max(nx.connected_components(g), key=len)

fig, axs = plt.subplots(1, 2, figsize=(16, 8))
for ax, title, back in [(axs[0], f"before — backbone {len(back_before):,} ({gf0:.0%})", back_before),
                        (axs[1], f"after ({SHOW_TOL} m) — backbone {len(back_after):,} "
                                 f"({len(back_after)/len(ids):.0%})", back_after)]:
    boundary.plot(ax=ax, color="#f1ead6", edgecolor="#b8a87a", linewidth=0.4, zorder=0)
    inb = road["from"].isin(back)
    road[~inb].plot(ax=ax, color="#d62728", linewidth=0.4, zorder=2)
    road[inb].plot(ax=ax, color="#444", linewidth=0.4, zorder=1)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal"); ax.set_title(title)
axs[1].legend(handles=[plt.Line2D([0], [0], color="#444", lw=2, label="backbone"),
                       plt.Line2D([0], [0], color="#d62728", lw=2, label="off-backbone")],
              loc="lower left", fontsize=8)
fig.suptitle(f"Road backbone (dark) before vs after closing ≤ {SHOW_TOL} m noding gaps", fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.95])
p = OUT / "03_before_after.png"; fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
T.image(p, f"Before/after at {SHOW_TOL} m — dark = backbone, red = still off-backbone")

T.note("Verdict in FINDINGS.md: close the ≤~150 m road gaps (clear noding artifacts, simple + logical); "
       "leave the far regional systems to the ferry/air anchors. Then this becomes ONE proximity rule "
       "for both road↔road (small tol) and ice↔road (500 m).")
T.done()
