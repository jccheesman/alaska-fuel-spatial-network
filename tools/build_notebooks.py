#!/usr/bin/env python3
"""Generate one notebook per pipeline step (consolidate -> tag -> hubs -> build -> join, + a run_pipeline capstone).

The notebooks are GENERATED, not hand-edited (same pattern as the toy project's
_build_notebook.py): edit the cell text here and re-run to rebuild them. Each notebook is
self-contained — a shared SETUP cell loads the profile, the mmnet package, the transport
overlays, and a PASS/FAIL harness; the step cells then read the previous step's artifact
from output/ and write their own. This keeps the steps modular and independently runnable,
and keeps mmnet importable by a future agent (every step is one function call).

Usage:
    python tools/build_notebooks.py          # writes notebooks/*.ipynb
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent
NB_DIR = ROOT / "notebooks"

# --------------------------------------------------------------------------- shared setup
SETUP = f'''\
import os, sys, warnings
from pathlib import Path

import geopandas as gpd
import pandas as pd
import networkx as nx

PROJECT = "{ROOT}"
os.environ["NETWEAVE_PROFILE"] = f"{{PROJECT}}/profile.yaml"   # selects the Alaska region profile
os.environ["NETWEAVE_PROJECT"] = PROJECT                       # output/ lands HERE
os.chdir(PROJECT); sys.path.insert(0, PROJECT)
warnings.filterwarnings("ignore")

import mmnet
from mmnet import inspect as mi, viz as mv
from mmnet.config import load_config, load_params
from mmnet.io_writers import out_path, output_dir, write_gdf
cfg, params = load_config(), load_params()
print("mmnet:", Path(mmnet.__file__).parent)
print("modes:", [s.mode for s in cfg.layers], "| target CRS:", cfg.crs.target)

# visible test harness: each significant result gets a PASS/FAIL check.
_PASSED = []
def check(name, cond):
    _PASSED.append(bool(cond))
    print(("\\u2713 PASS" if cond else "\\u2717 FAIL"), "-", name)
    assert cond, f"FAILED: {{name}}"

# Transport line layers (drawn under every map) + anchor overlays (ports, airports).
# Waterways are the national network — clip to the Alaska bbox so maps stay local + fast.
T = cfg.crs.target
_ak = gpd.read_file("data/boundary.geojson").to_crs(T)
_b = _ak.total_bounds

def _lines(p, clip=False):
    g = gpd.read_file(p).to_crs(T)
    g = g[g.geometry.geom_type.isin(["LineString", "MultiLineString"])]
    return g.cx[_b[0]:_b[2], _b[1]:_b[3]] if clip else g

NET = {{
    "roads":     _lines("data/raw/connectivity/road/Roads_AKDOT/Roads_AKDOT.shp"),
    "waterways": _lines("data/raw/connectivity/barge/NWN_Waterway_Network_Lines/Waterway_Network.shp", clip=True),
    "airways":   gpd.read_file("data/processed/airways.geojson").to_crs(T),
    "ice_roads": _lines("data/raw/connectivity/ice_roads/ice_roads_150m_3338/Ice_Roads.shp"),
}}
ports = gpd.read_file("data/raw/anchor_points/Ports_and_Harbors.geojson").to_crs(T)
_ap = pd.read_csv("data/interim/airports.csv", low_memory=False)   # AK DOT&PF registry (official Flights data)
_ap = _ap[_ap["longitude_deg"].notna() & _ap["latitude_deg"].notna()]
airports = gpd.GeoDataFrame(_ap.copy(), geometry=gpd.points_from_xy(_ap["longitude_deg"], _ap["latitude_deg"]),
                            crs=4326).to_crs(T)
print("overlays |", {{k: len(v) for k, v in NET.items()}}, "| ports:", len(ports), "| airports:", len(airports))
'''

INTRO = '''\
# Alaska multimodal network — Step {nn}: {title}

This notebook runs **one step** of the `mmnet` pipeline on Alaska bulk-fuel logistics.
The full chain is `consolidate → tag → hubs → build → join`; the methodology is identical to
the toy gold-standard project, only the region profile (`profile.yaml`) and data differ.

Each step reads the previous step's artifact from `output/` and writes its own, so the
notebooks are modular — run them in order, or re-run one after changing a parameter in
`profile.yaml`. The `check(...)` calls are a visible PASS/FAIL harness on each result.

**Run setup first**, then the step below.
'''

# --------------------------------------------------------------------------- per-step cells
CONSOLIDATE = '''\
from mmnet.steps.consolidate import consolidate_facilities

raw_path = cfg.raw_path("facilities")
raw_df = pd.read_csv(raw_path, low_memory=False)

# Reads the raw inventory, scopes to routable modes, reprojects, and dedups co-located
# tanks (complete-linkage at hubs.dedup_tol_m), unioning delivery methods + max() capacity.
fac = consolidate_facilities(raw_path, params, input_crs=cfg.crs.input,
                             target_crs=cfg.crs.target, config=cfg)
write_gdf(fac, "01_facilities.gpkg")
mi.describe_output(fac, "01_facilities")

check("output carries geometry + delivery_method + total_capacity",
      {"geometry", "delivery_method", "total_capacity"} <= set(fac.columns))
check("reprojected to the target CRS (Alaska Albers 3338)", fac.crs.to_epsg() == int(cfg.crs.target))
check("dedup did not grow the inventory", len(fac) <= len(raw_df))
check("every facility has a positive capacity", (fac["total_capacity"] > 0).all())

mv.plot_before_after(None, fac, "Step 01 — consolidate (facilities by delivery method)",
                     slug="01_consolidate", after_label="deduped facilities",
                     overlays={"ports": ports, "airports": airports}, lines=NET)
'''

TAG = '''\
from mmnet.steps.tag import assign_community_region, passthrough_tag
from mmnet.io_readers import load_places, load_regions

fac_in = gpd.read_file(out_path("01_facilities.gpkg"))

# Two-tier spatial tag: facility -> TIGER place, else borough/census area. The inventory's
# own community name is authoritative; polygons fill gaps + supply the region.
if not cfg.tagging_enabled or cfg.place_tagging is None:
    tagged = passthrough_tag(fac_in)
else:
    places = load_places(cfg.place_path(), cfg.crs.target, cfg.places_cols)
    regions = load_regions(cfg.region_path(), cfg.crs.target, cfg.regions_cols)
    tagged = assign_community_region(fac_in, places, regions)
write_gdf(tagged, "01b_tagged.gpkg")          # the R build reads this
mi.describe_output(tagged, "01b_tagged")
added = mi.diff_columns(fac_in, tagged)["added"]

check("tag preserves every facility row", len(tagged) == len(fac_in))
check("tag adds the assignment columns", "assigned_level" in tagged.columns and len(added) > 0)
check("every facility resolved a community/region (no untagged)",
      (tagged["assigned_level"] != "untagged").all())

mv.plot_before_after(None, tagged, "Step 01b — tag (facilities, region-resolved)",
                     slug="01b_tag", after_label="tagged facilities",
                     overlays={"ports": ports, "airports": airports}, lines=NET)
'''

HUBS = '''\
from mmnet.steps.hubs import aggregate_hubs
from mmnet.assemble import snap_to_roads

tagged = gpd.read_file(out_path("01b_tagged.gpkg"))

# Group facilities into one hub per (community, delivery_method) at the member centroid,
# sum capacity, classify Supplier/Receiver within each mode. snap_to_roads then places every
# hub on the nearest road, so a Barge hub lands on land.
hubs = aggregate_hubs(tagged, params)
write_gdf(hubs, "02_hubs.gpkg")
mi.describe_output(hubs, "02_hubs")

hubs_onroad = snap_to_roads(hubs, NET["roads"])

check("hubs aggregate below the facility count", 0 < len(hubs) < len(tagged))
check("hub types classified Supplier / Receiver", set(hubs["hub_type"]) <= {"Supplier", "Receiver"})
check("every hub carries a positive aggregated capacity", (hubs["total_hub_capacity"] > 0).all())
check("snap_to_roads puts every hub on the road (finite snap distance)",
      hubs_onroad["road_snap_dist_m"].notna().all())

mv.plot_hubs(tagged, hubs, hubs_onroad, title="Step 02 — hubs on the road (centroid vs on-road)",
             slug="02_hubs", lines=NET,
             point_overlays={"ports": ports, "airports": airports})
'''

BUILD = '''\
from mmnet.build import build_network

hubs = gpd.read_file(out_path("02_hubs.gpkg"))
layer_list = [s.name for s in cfg.layers if s.kind == "line"]   # roads, waterways, airways, ice_roads
print("building modes/layers:", layer_list)

# No redundancy: R nodes the sfnetwork ONCE (the hard planar noding/subdivision), then Python
# connects ONCE — derive nodes from R's edges (no re-noding), snap the Stage-02 hubs to the road,
# SNAP airports onto the road (a shared node, NOT a transfer edge), add barge<->road/ice Transfer
# edges at ports + coastal hubs, proximity bridges (road/ice welds + ice<->road) and a connect-to-giant
# shore pass. R noding ~1 min; Python connect ~seconds (spatial index).
# Requires Rscript + sf/sfnetworks/tidygraph on the PATH.
net = build_network(layer_list, output_dir() / "03_network", hubs, timeout_s=1800)
n, e = net.nodes, net.edges
mi.describe_output(n, "03_network nodes"); mi.describe_output(e, "03_network edges")
s = net.summary()
print("summary:", s, "| edge types:", e["type"].value_counts().to_dict())

check("R noded every mode present in the data (Road/Waterway/Air/IceRoad edges)",
      {"Road", "Waterway", "Air", "IceRoad"} <= set(e["type"]))
check("Python built intermodal Transfer edges (barge<->road/ice at ports + hubs)", (e["type"] == "Transfer").any())
check("hubs are present on the network", int(n["is_hub"].fillna(False).astype(bool).sum()) > 0)
# Alaska is NOT one component (many isolated bush communities) — report, do not assert ==1.
print(f"connectivity: {s['n_components']} components, giant covers {s['giant_frac']:.1%} of nodes")

mv.plot_network(n, e, title="Step 03 — Alaska multimodal network (edges by type + hubs)",
                slug="03_build", point_overlays={"ports": ports, "airports": airports})

# Connectivity report — per-mode + fuel-hub reachability, and the air mode's marginal contribution
# (the official flight data). Prints a headline and writes reports/03_network.md.
rep = mi.connectivity_report(n, e)
contrib = mi.mode_contribution(n, e, "Air")
mi.write_network_report(rep, contrib)
check("the network forms one dominant giant (>= 95% of nodes)", rep["giant_frac"] >= 0.95)
check("most fuel hubs are reachable (>= 80%)", rep["hubs_pct"] >= 80)
check("air connects fuel hubs that road/barge/ice cannot", contrib["only_via_hubs"] > 0)
'''

JOIN = '''\
from mmnet.assemble import join_components_to_giant
from mmnet.network import NetworkTables

# Pipeline Stage 04. The Stage-03 build leaves some components disconnected; this step joins every
# non-giant component to the giant when its nearest node is within join_components.max_dist (m) of a
# giant node — a straight `Join` connector per component, iterated until stable. It reads 03 and writes
# a SEPARATE 04_network_joined; 03_network stays canonical (run_pipeline returns 03).
nt = NetworkTables.from_gpkg(output_dir() / "03_network")
nd = nt.nodes.sort_values("node_id").reset_index(drop=True)   # row index == node_id (the join engine assumes it)
e = nt.edges.copy(); e["from"] = e["from"].astype(int); e["to"] = e["to"].astype(int)
cap = float(cfg.join_components.max_dist)
print("join_components.max_dist:", cap, "m  (0 disables; a large cap collapses to one component)")

rep0 = mi.connectivity_report(nd, e)                          # before
nd2, e2, js = join_components_to_giant(nd, e, cap)
NetworkTables.from_parts(nd2, e2).to_gpkg(output_dir() / "04_network_joined")
rep1 = mi.connectivity_report(nd2, e2)                        # after
mi.write_network_report(rep1, out_name="04_network_joined.md",
                        title="Stage 04 — components joined to the giant")
print(f"joined {js['n_joined']} components (<= {cap:.0f} m) in {js['rounds']} round(s): "
      f"{rep0['n_components']} -> {rep1['n_components']} components, "
      f"giant {rep0['giant_frac']:.1%} -> {rep1['giant_frac']:.1%}, "
      f"hubs {rep0['hubs_reachable']} -> {rep1['hubs_reachable']}")

check("Stage 04 wrote the separate joined network", (output_dir() / "04_network_joined__nodes.gpkg").exists())
check("03_network is untouched (still on disk)", (output_dir() / "03_network__nodes.gpkg").exists())
if cap > 0 and js["n_joined"] > 0:
    check("the join reduced the component count", rep1["n_components"] < rep0["n_components"])
    check("Join connectors were added", (e2["type"] == "Join").any())
    check("the giant did not shrink", rep1["giant_frac"] >= rep0["giant_frac"])
else:
    check("no join requested (max_dist=0) -> unchanged", rep1["n_components"] == rep0["n_components"])

mv.plot_network(nd2, e2, title=f"Step 04 — components joined to the giant (max_dist = {cap/1000:g} km)",
                slug="04_join", point_overlays={"ports": ports, "airports": airports})
'''

RUN_ALL = '''\
# The top-level entry point: one call runs consolidate -> tag -> hubs -> build -> join and returns
# the canonical 03 network. This is the function a future agent would call. It reproduces the same
# result the step notebooks build (output/03_network__{nodes,edges}.gpkg), and — when the profile's
# join_components.max_dist > 0 — also writes the Stage-04 output/04_network_joined__{nodes,edges}.gpkg.
net = mmnet.run_pipeline("profile.yaml")
s = net.summary()
print("run_pipeline summary:", s, "| edge types:", net.edges["type"].value_counts().to_dict())

check("run_pipeline produced nodes and edges", s["n_nodes"] > 0 and s["n_edges"] > 0)
check("run_pipeline carries all mode edge types",
      {"Road", "Waterway", "Air", "IceRoad", "Transfer"} <= set(net.edges["type"]))
check("run_pipeline placed the hubs", s["n_hubs"] > 0)

# Connectivity result — per-mode + fuel-hub reachability + the air mode's contribution (reports/03_network.md).
rep = mi.connectivity_report(net.nodes, net.edges)
mi.write_network_report(rep, mi.mode_contribution(net.nodes, net.edges, "Air"))
check("giant connects >= 95% of nodes", rep["giant_frac"] >= 0.95)
check("fuel hubs mostly reachable (>= 80%)", rep["hubs_pct"] >= 80)

# Stage 04 runs inside run_pipeline when join_components.max_dist > 0 (a separate 04_network_joined;
# 03 is the canonical return above).
from mmnet.network import NetworkTables
rows = [
    ("01 consolidate", "raw inventory", "deduped multimodal facilities"),
    ("01b tag",        "facilities",    "+ community/region assignment"),
    ("02 hubs",        "tagged",        "facilities -> classified hubs"),
    ("03 build",       "hubs + layers", f"network: {s['n_nodes']} nodes / {s['n_edges']} edges / {s['n_components']} comp"),
]
if cfg.join_components.max_dist > 0:
    check("Stage 04 wrote output/04_network_joined", (output_dir() / "04_network_joined__nodes.gpkg").exists())
    j = NetworkTables.from_gpkg(output_dir() / "04_network_joined")
    rows.append(("04 join", "03 network",
                 f"joined: {j.nodes['component'].nunique()} components ({100*j.nodes['is_giant'].mean():.1f}% giant)"))
print(pd.DataFrame(rows, columns=["step", "in", "out"]).to_string(index=False))
print(f"\\nALL {len(_PASSED)} CHECKS PASSED \\u2713" if all(_PASSED) else f"\\n{sum(_PASSED)}/{len(_PASSED)} passed")
'''

STEPS = [
    ("01", "consolidate", "Consolidate the facility inventory", CONSOLIDATE),
    ("01b", "tag", "Tag facilities by community and region", TAG),
    ("02", "hubs", "Aggregate and classify hubs", HUBS),
    ("03", "build", "Build the multimodal network", BUILD),
    ("04", "join", "Join disconnected components to the giant by distance", JOIN),
    ("05", "run_pipeline", "Run the whole pipeline end-to-end", RUN_ALL),
]


def make_notebook(nn: str, title: str, body: str) -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell(INTRO.format(nn=nn, title=title)),
        nbf.v4.new_markdown_cell("## Setup"),
        nbf.v4.new_code_cell(SETUP),
        nbf.v4.new_markdown_cell(f"## Step {nn} — {title}"),
        nbf.v4.new_code_cell(body),
    ]
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.metadata["language_info"] = {"name": "python"}
    return nb


def main() -> None:
    NB_DIR.mkdir(parents=True, exist_ok=True)
    for nn, slug, title, body in STEPS:
        nb = make_notebook(nn, title, body)
        path = NB_DIR / f"{nn}_{slug}.ipynb"
        nbf.write(nb, path)
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
