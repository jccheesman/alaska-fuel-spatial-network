#!/usr/bin/env python3
"""PROOF — the engine reproduces the connected waterway network (the North Slope joins the giant).

A short, plain check that the mmnet pipeline's `output/03_network` is the connected multimodal network
the research produced: the full Alaska waterway, barge transfers to BOTH road and ice at ports + barge
hubs, the road↔road / ice↔ice / ice↔road before-policies, and the connect-to-giant shore-landing pass.
Prints a before -> after summary, the headline giant fractions, and the one line that matters:

    North Slope (Barrow): CONNECTED

Run (from this folder, after a build):
    python -c "import mmnet; mmnet.run_pipeline('profile.yaml')"   # writes ./output/03_network
    python verify_north_slope.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent          # examples/alaska — where the build writes output/
sys.path.insert(0, str(HERE.parents[1]))        # mmnet-toolkit root, so `import mmnet` works uninstalled
from mmnet.network import NetworkTables  # noqa: E402

BARROW = (-100728.0, 2368953.0)          # a North-Slope (Barrow/Utqiaġvik) coordinate, EPSG:3338


def giant(e, mask) -> tuple[set, int]:
    g = nx.Graph()
    sub = e[mask]
    g.add_edges_from(zip(sub["from"], sub["to"]))
    comps = sorted(nx.connected_components(g), key=len, reverse=True)
    return (comps[0] if comps else set()), len(comps)


def main() -> None:
    stem = HERE / "output" / "03_network"
    if not (stem.parent / "03_network__edges.gpkg").exists():
        raise SystemExit("no output/03_network — run: python -c \"import mmnet; mmnet.run_pipeline('profile.yaml')\"")
    nt = NetworkTables.from_gpkg(stem)
    nd = nt.nodes.sort_values("node_id").reset_index(drop=True)
    xy = np.c_[nd.geometry.x.values, nd.geometry.y.values]
    e = nt.edges.copy()
    e["from"] = e["from"].astype(int); e["to"] = e["to"].astype(int)
    et, sr = e["type"], e["source"].astype(str)

    rid = np.array(sorted(set(e[et == "Road"]["from"]) | set(e[et == "Road"]["to"])), dtype=int)
    iid = np.array(sorted(set(e[et == "IceRoad"]["from"]) | set(e[et == "IceRoad"]["to"])), dtype=int)
    wid = np.array(sorted(set(e[et == "Waterway"]["from"]) | set(e[et == "Waterway"]["to"])), dtype=int)

    def cnt(pred):
        return int(pred.sum())

    print("=" * 78)
    print(" PROOF — mmnet reproduces the connected waterway network (North Slope joins giant)")
    print("=" * 78)

    print("\n what changed in the engine  (before  ->  after)")
    print(f"   waterway              clipped 282 edges        ->  full AK marine {cnt(et=='Waterway'):>6,} edges")
    print(f"   barge transfers       Road only, ports only    ->  Road+Ice, ports+hubs   "
          f"{cnt((et=='Transfer') & sr.isin(['ports','barge_hubs'])):>4}")
    print(f"   before-policies       (none)                   ->  weld+bridge            "
          f"{cnt((et=='Bridge') & ~sr.eq('weld:to-giant')):>4}")
    print(f"   connect-to-giant      (none)                   ->  shore landings + welds "
          f"{cnt(sr.str.startswith('shore') | sr.eq('weld:to-giant')):>4}")

    print("\n connectors by source")
    for k, v in sr[sr.str.contains('weld|bridge|shore', regex=True) | sr.isin(['ports', 'barge_hubs', 'airports'])
                   ].value_counts().items():
        print(f"   {k:<22} {v:>6,}")

    # headline: the full multimodal network (this is the real output)
    Gfull, ncF = giant(e, np.ones(len(e), bool))
    pct = lambda ids, G: 100.0 * sum(n in G for n in ids) / max(len(ids), 1)
    print("\n FULL multimodal network (road + ice + waterway + air)")
    print(f"   giant {len(Gfull):,}/{len(nd):,} nodes = {100*len(Gfull)/len(nd):.1f}%   components {ncF}")
    print(f"   road {pct(rid,Gfull):.1f}%   ice {pct(iid,Gfull):.1f}%   waterway {pct(wid,Gfull):.1f}%   in giant")

    # research view: road + ice + waterway BY SEA (no air) — reproduces 02_connect_via_ports.py
    by_sea = (et.isin(["Road", "IceRoad", "Waterway", "Bridge"])
              | ((et == "Transfer") & sr.isin(["ports", "barge_hubs"])) | sr.str.startswith("shore")) \
        & ~(et == "Air") & ~(sr == "airports")
    Gsea, ncS = giant(e, by_sea)
    print("\n by-sea view (road + ice + waterway only — the research metric)")
    print(f"   road {pct(rid,Gsea):.1f}%   ice {pct(iid,Gsea):.1f}%   waterway {pct(wid,Gsea):.1f}%   "
          f"components {ncS}   (research: road 95.6  ice 95.4  waterway 100  comps 101)")

    # the one line that matters
    br = int(rid[int(cKDTree(xy[rid]).query(BARROW)[1])])
    bi = int(iid[int(cKDTree(xy[iid]).query(BARROW)[1])])
    road_ok, ice_ok = br in Gfull, bi in Gfull
    print("\n" + "-" * 78)
    mark = "CONNECTED" if (road_ok and ice_ok) else "DISCONNECTED"
    print(f"   North Slope (Barrow):  {mark}   (road in giant: {road_ok} · ice in giant: {ice_ok})")
    print("-" * 78)

    checks = {
        "North Slope road in giant": road_ok,
        "North Slope ice in giant": ice_ok,
        "waterway 100% connected": abs(pct(wid, Gfull) - 100.0) < 0.05,
        "road >= 95% in giant": pct(rid, Gfull) >= 95.0,
        "ice  >= 95% in giant": pct(iid, Gfull) >= 95.0,
        "barge transfers ~201 (ports+hubs)": 180 <= cnt((et == "Transfer") & sr.isin(["ports", "barge_hubs"])) <= 220,
    }
    print("\n checks")
    for label, ok in checks.items():
        print(f"   [{'PASS' if ok else 'FAIL'}] {label}")
    overall = all(checks.values())
    print("\n RESULT:", "PASS — the expected connected network is reproduced." if overall
          else "FAIL — see the checks above.")
    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()
