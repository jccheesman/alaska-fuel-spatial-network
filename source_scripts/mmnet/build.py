"""Stage 03 — multimodal network assembly. **R nodes the sfnetwork; Python connects it.**

The build has one clear seam, with no work done twice:

* **R does the noding only** — the planar `clean/subdivide/smooth` per mode that is hard to
  reproduce exactly in Python. `node_layers_via_r` writes a LEAN file contract (just the line
  layers + a minimal registry/params) and runs `r_oracle/build_network.R --node-only`, returning
  the noded edges (geometry + `type`). R does NOT aggregate hubs, blend, build transfers, or join.
* **Python does the connection** — `build_network` reads R's noded edges and hands them to
  `mmnet.assemble.connect_multimodal`, which derives the node table from the edge endpoints
  (no re-noding), snaps the Stage-02 hubs to the ground, and links the modes at the profile's anchors
  (ports → barge↔road); airports SNAP onto the road (`_snap_airways_to_road`, a shared node, not a transfer).

The oracle is decoupled from any fixed R project — it reads only a self-contained WORKDIR
(see r_oracle/CONTRACT.md) plus its sibling lib.R.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import warnings
from pathlib import Path

import geopandas as gpd
import pandas as pd

from .config import LayerSpec, PipelineConfig, Params, load_config, load_params
from .io_readers import load_airways, load_boundary, load_roads, load_waterways
from .io_writers import out_path
from .network import NetworkTables

PROJECT_DIR = Path(__file__).resolve().parent          # the mmnet package dir (bundled R oracle)
R_ORACLE = PROJECT_DIR / "r_oracle" / "build_network.R"

CONTRACT_VERSION = "2"

# default_params() blend-tolerance knob per layer (the registry `blend_param`).
_BLEND_PARAM = {
    "roads": "road_blend_tolerance",
    "waterways": "barge_blend_tolerance",
    "airways": "air_blend_tolerance",
}


def _load_line_layer(spec: LayerSpec, cfg: PipelineConfig, params: Params,
                     facilities: gpd.GeoDataFrame) -> gpd.GeoDataFrame | None:
    """Load a single line layer via the profile-driven readers (mirrors the hubs step)."""
    paths = cfg.layer_paths(spec)
    if spec.name == "roads":
        bpath = cfg.boundary_path()
        boundary = load_boundary(bpath, cfg.crs.target) if bpath and bpath.exists() else None
        return load_roads(paths, cfg.crs.target, boundary=boundary,
                          border_stitch_m=cfg.border_stitch_m)
    if spec.name == "waterways":
        # Full Alaska marine network (the source is already AK-scoped via workflows/02_network_build/01_prep_waterway.py).
        # NO facility-bbox clip: the offshore marine spines must survive so road + ice can join the
        # giant by sea. Stage 03 nodes this in Python (50 m rounding), not R.
        return load_waterways(paths[0], cfg.crs.target)
    if spec.name == "airways":
        if paths[0].exists():
            return load_airways(paths[0], cfg.crs.target)
        return None
    # generic line layer
    from .io_readers import _read_lines
    return _read_lines(paths[0], cfg.crs.target)


# A non-base Barge (e.g. manual) route endpoint within this distance of the marine spine is treated as
# a LANDING and welded onto it; farther endpoints (on-land hub ends) are left as drawn. Must stay well
# below the gap between a landing and its hub end so the two are never confused.
MARINE_LANDING_TOL = 100.0
# Must match assemble.connect_multimodal's waterway vertex-rounding, so an inserted landing vertex and
# the snapped route endpoint round to the same node.
WATERWAY_NODE_TOL = 50.0


def _insert_vertices(line, pts):
    """Return `line` with each shapely Point in `pts` inserted at its projected position along it."""
    from shapely.geometry import LineString, Point

    coords = [(x, y) for x, y, *_ in line.coords]
    ordered = sorted(((line.project(pt), (pt.x, pt.y)) for pt in pts), key=lambda t: t[0])
    out, cum, pi = [coords[0]], 0.0, 0
    for i in range(1, len(coords)):
        seg_end = cum + Point(coords[i - 1]).distance(Point(coords[i]))
        while pi < len(ordered) and ordered[pi][0] <= seg_end + 1e-6:
            if ordered[pi][0] >= cum - 1e-6 and ordered[pi][1] not in (out[-1], coords[i]):
                out.append(ordered[pi][1])
            pi += 1
        out.append(coords[i])
        cum = seg_end
    return LineString(out)


def _weld_barge_landings(base: gpd.GeoDataFrame, extra: gpd.GeoDataFrame,
                         landing_tol: float, node_tol: float):
    """Weld manual/extra barge routes that LAND mid-edge on the base marine spine.

    For each `extra` line endpoint within `landing_tol` of a base waterway line, snap the endpoint onto
    that line and insert the projected point as a shared vertex on the base line (unless a base vertex is
    already within `node_tol`). After the assembler's vertex-rounding this yields a shared node, so the
    route welds into the marine network instead of forming an isolated segment. Endpoints beyond
    `landing_tol` (on-land hub ends) are left untouched. Returns (base, extra, n_welded)."""
    from shapely.geometry import LineString, Point

    base = base.reset_index(drop=True)
    base_geoms = list(base.geometry)
    sindex = base.sindex
    inserts: dict[int, list] = {}
    new_extra_geoms = []
    n_welded = 0

    for eg in extra.geometry:
        if eg is None or eg.is_empty or eg.geom_type != "LineString":
            new_extra_geoms.append(eg)
            continue
        cs = [(x, y) for x, y, *_ in eg.coords]
        for idx in (0, len(cs) - 1):
            p = Point(cs[idx])
            best = None
            for j in sindex.query(p.buffer(landing_tol)):
                d = base_geoms[j].distance(p)
                if best is None or d < best[0]:
                    best = (d, int(j))
            if best is None or best[0] > landing_tol:
                continue
            j = best[1]
            bg = base_geoms[j]
            proj = bg.interpolate(bg.project(p))
            cs[idx] = (proj.x, proj.y)                    # snap the route endpoint onto the spine
            if min(Point(v).distance(proj) for v in bg.coords) > node_tol:
                inserts.setdefault(j, []).append(proj)    # needs a new shared vertex on the spine
            n_welded += 1
        new_extra_geoms.append(LineString(cs))

    for j, pts in inserts.items():
        base_geoms[j] = _insert_vertices(base_geoms[j], pts)

    return base.assign(geometry=base_geoms), extra.assign(geometry=new_extra_geoms), n_welded


def _first_col(df, candidates: tuple[str, ...]) -> str | None:
    """First matching column name (case-insensitive) from a list of candidates."""
    low = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in low:
            return low[cand]
    return None


def _load_points_generic(path, cfg: PipelineConfig) -> gpd.GeoDataFrame:
    """Read an anchor point layer from a vector file (geojson/shp/gpkg) OR a CSV with
    lon/lat columns (inferred). Region-agnostic — no flight table or fixed column names."""
    path = Path(path)
    if path.suffix.lower() in (".csv", ".txt"):
        import pandas as pd

        df = pd.read_csv(path)
        lon = _first_col(df, ("lon", "longitude", "x", "x_lon", "long", "longitude_deg"))
        lat = _first_col(df, ("lat", "latitude", "y", "y_lat", "latitude_deg"))
        if lon is None or lat is None:
            raise RuntimeError(
                f"anchor CSV {path.name} needs lon/lat columns; got {list(df.columns)}"
            )
        g = gpd.GeoDataFrame(df.copy(), geometry=gpd.points_from_xy(df[lon], df[lat]),
                             crs=cfg.crs.input)
    else:
        g = gpd.read_file(path)
    g = g.to_crs(cfg.crs.target)
    g = g[g.geometry.notna() & ~g.geometry.is_empty]
    return g[g.geometry.geom_type == "Point"].reset_index(drop=True)


def _load_anchor(anchor: str, cfg: PipelineConfig) -> gpd.GeoDataFrame:
    """Load a transfer anchor point layer (ports / airports / ...) from its profile file."""
    return _load_points_generic(cfg.anchor_path(anchor), cfg)


# Anchors resolved from a pipeline OUTPUT rather than a file (no `anchors:` entry, no file check).
VIRTUAL_ANCHORS = {"barge_hubs"}


def _barge_hub_anchor(hubs: gpd.GeoDataFrame, cfg: PipelineConfig) -> gpd.GeoDataFrame:
    """The barge-demand anchor: Stage-02 hubs whose delivery_method contains "Barge", as points.

    Coastal communities served by barge anchor a Barge↔Road / Barge↔IceRoad transfer just like a
    port. Resolved from the `hubs` gdf (a pipeline output), so it is not a profile `anchors:` file.
    """
    if hubs is None or not len(hubs) or "delivery_method" not in hubs.columns:
        return hubs.iloc[:0] if hubs is not None else gpd.GeoDataFrame(geometry=[], crs=cfg.crs.target)
    barge = hubs[hubs["delivery_method"].astype(str).str.contains("Barge", na=False)]
    return barge.to_crs(cfg.crs.target).reset_index(drop=True)


def _resolve_anchor(anchor: str, cfg: PipelineConfig, hubs: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Resolve a transfer anchor to points — a virtual (hubs-derived) anchor or a profile file."""
    if anchor in VIRTUAL_ANCHORS:
        return _barge_hub_anchor(hubs, cfg)
    return _load_anchor(anchor, cfg)


def _tagged_for_contract() -> gpd.GeoDataFrame:
    """Read the native output/01b_tagged.gpkg as-is for the contract workdir.

    The engine writes its own region column name; the R oracle (build_network.R) maps it to the name
    its grouping logic expects. Keeping that bridge on the R side keeps source_scripts/ region-neutral. See CONTRACT.md.
    """
    return gpd.read_file(out_path("01b_tagged.gpkg"))


def _write_node_contract(workdir: Path, layers: list[str],
                         cfg: PipelineConfig, params: Params) -> None:
    """Assemble a LEAN node-only contract: just the line layers + a minimal registry/params.

    No facilities, no anchors, no transfers — the node-only oracle needs only the geometry to
    node, the target CRS, and the cleaning precision. Waterways are still clipped to the facility
    halo (mirrors the full contract) using the tagged facilities for the bbox only.
    """
    # Scope the suppression to this contract-writing block instead of calling
    # warnings.filterwarnings("ignore") (which leaks process-wide and would
    # hide legitimate warnings from the rest of the pipeline).
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        (workdir / "layers").mkdir(parents=True, exist_ok=True)
        facilities = _tagged_for_contract()                   # waterway clip bbox only (not written)
        spec_by_name = {s.name: s for s in cfg.layers}

        mode_rows = []
        for ln in layers:
            spec = spec_by_name.get(ln)
            if spec is None:
                continue
            mode_rows.append({"mode": spec.mode, "layer": spec.name,
                              "edge_label": spec.edge_label,
                              "blend_param": _BLEND_PARAM.get(ln, f"{ln}_blend_tolerance")})
            g = _load_line_layer(spec, cfg, params, facilities)
            if g is None or len(g) == 0:
                raise RuntimeError(f"layer {ln!r} produced no features (missing artifact?)")
            g[["geometry"]].to_file(workdir / "layers" / f"{ln}.gpkg", driver="GPKG")

        (workdir / "registry.json").write_text(
            json.dumps({"modes": mode_rows, "transfers": []}, indent=2))
        (workdir / "params.json").write_text(json.dumps({
            "contract_version": CONTRACT_VERSION,
            "target_crs": int(cfg.crs.target),
            "input_crs": int(cfg.crs.input),
            "precision": params.precision,
        }, indent=2))


def node_layers_via_r(layers: list[str], timeout_s: int = 1800) -> gpd.GeoDataFrame:
    """Run the R oracle in **node-only** mode and return the noded line edges (geometry + type).

    R's single job: build the per-mode sfnetwork (planar noding + subdivision + smoothing). It does
    NOT aggregate hubs, blend, build transfers, or join the modes — that is Python's job
    (:func:`mmnet.assemble.connect_multimodal`). Returns one GeoDataFrame of all modes' noded edges,
    each row carrying its `type` (edge_label).
    """
    cfg, params = load_config(), load_params()
    spec_by_name = {s.name: s for s in cfg.layers}
    modes = sorted({spec_by_name[l].mode for l in layers if l in spec_by_name})

    rscript = shutil.which("Rscript")
    if rscript is None:
        raise RuntimeError(
            "Rscript not found on PATH. The R noding oracle is a documented requirement of "
            "stage 02 on every OS: install R, then "
            'install.packages(c("sf", "sfnetworks", "tidygraph", "dplyr")). '
            "See README.md (Quickstart) and workflows/02_network_build/README.md."
        )

    with tempfile.TemporaryDirectory(prefix="mmnet_node_") as tmp:
        workdir = Path(tmp)
        _write_node_contract(workdir, layers, cfg, params)
        out_prefix = workdir / "noded"
        cmd = [rscript, str(R_ORACLE), "--workdir", str(workdir), "--out", str(out_prefix),
               "--modes", ",".join(modes), "--node-only"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        if proc.returncode != 0:
            raise RuntimeError(
                "R node-only oracle failed:\n"
                + "\n".join(l for l in proc.stderr.splitlines() if not l.startswith(("renv", "- Use"))))
        return gpd.read_file(str(out_prefix) + "__edges.gpkg")


def _snap_airways_to_road(r_edges: gpd.GeoDataFrame, from_label: str, to_label: str,
                          anchor_pts: gpd.GeoDataFrame, max_dist: float):
    """Snap each `from_label` (Air) leg endpoint that is an airport onto the nearest `to_label` (Road)
    node within `max_dist` — so the airport becomes a SHARED node on the road (no transfer edge).

    Operates on R's noded edges BEFORE the connect: it moves the air leg's airport vertex onto the nearest
    road edge-endpoint coordinate, so `connect_multimodal`'s node table merges them into one node. Only
    true airport endpoints snap (≤ 1 m from an `anchor_pts` point — air crossings are left alone); a leg
    whose airport has no road within `max_dist` is not moved (it stays air-only). Returns (r_edges, n_snapped).
    """
    import numpy as np
    from scipy.spatial import cKDTree
    from shapely.geometry import LineString

    to_pts = []
    for geom, t in zip(r_edges.geometry, r_edges["type"]):
        if t == to_label and geom is not None and not geom.is_empty:
            cs = list(geom.coords)
            to_pts.append(cs[0][:2]); to_pts.append(cs[-1][:2])
    if not to_pts or anchor_pts is None or not len(anchor_pts):
        return r_edges, 0
    to_arr = np.asarray(to_pts, dtype=float)
    to_tree = cKDTree(to_arr)
    ap_tree = cKDTree(np.c_[anchor_pts.geometry.x.values, anchor_pts.geometry.y.values])

    geoms = list(r_edges.geometry)
    n = 0
    for i, (geom, t) in enumerate(zip(geoms, r_edges["type"])):
        if t != from_label or geom is None or geom.is_empty:
            continue
        cs = [list(c[:2]) for c in geom.coords]
        if len(cs) < 2:
            continue
        changed = False
        for j in (0, len(cs) - 1):
            if float(ap_tree.query(cs[j])[0]) > 1.0:        # only real airport endpoints (not air crossings)
                continue
            d, k = to_tree.query(cs[j])
            if float(d) <= max_dist:
                cs[j] = list(to_arr[int(k)]); changed = True; n += 1
        if changed:
            geoms[i] = LineString(cs)
    out = r_edges.copy()
    out["geometry"] = geoms
    return out, n


def build_network(layers: list[str], out_prefix: str | Path, hubs: gpd.GeoDataFrame,
                  timeout_s: int = 1800) -> NetworkTables:
    """Build the connected multimodal network: **R nodes road/ice/air, Python connects it.**

    No redundancy: R nodes each land mode's lines ONCE (`node_layers_via_r`); the **waterway is noded
    in Python** (50 m rounding, not R — the marine spines are already a clean network). Python then
    connects everything ONCE (:func:`mmnet.assemble.connect_multimodal`) — derives the node table,
    snaps the Stage-02 hubs, and joins the modes: airports first SNAP onto the road (`_snap_airways_to_road`,
    a shared node — no transfer edge), then three passes — (1) anchor TRANSFERS (barge↔road and barge↔ice at
    ports + barge hubs); (2) proximity BRIDGES (road↔road / ice↔ice
    welds, ice↔road bridge); (3) a CONNECT_TO_GIANT shore-landing pass that pulls every still-isolated
    coastal piece into the giant — connecting the North Slope at its barge landing. All profile-driven.
    """
    from .assemble import connect_multimodal

    out_prefix = Path(out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    cfg = load_config()

    # 1. resolve the line layers; the waterway (Barge mode) is noded in Python, the rest by R.
    line_specs = [cfg.layer_by_name(l) for l in layers if cfg.layer_by_name(l).kind == "line"]
    ww_specs = [s for s in line_specs if s.mode == "Barge"]
    r_layers = [s.name for s in line_specs if s.mode != "Barge"]

    # 1a. R / sfnetworks noding (node-only) for the land modes — noded edges tagged by `type`.
    r_edges = node_layers_via_r(r_layers, timeout_s=timeout_s)

    # 1b. the full waterway, loaded un-clipped (Python nodes it in connect_multimodal). ALL Barge-mode
    #     layers are concatenated — the base marine spine plus any user-authored manual barge routes —
    #     so a second Barge layer is not silently dropped (symmetric with the R side, which already
    #     nodes N layers per land mode). A manual route often LANDS mid-edge on a long open-water spine
    #     segment; since the waterway is noded by vertex-rounding (not planar), that landing would not
    #     weld, so we insert it as a shared vertex on the spine first (_weld_barge_landings). On-land
    #     route ends (far from the spine) are left as drawn — they ride into the giant via the landing.
    waterway = None
    waterway_label = ww_specs[0].edge_label if ww_specs else "Waterway"
    if ww_specs:
        params = load_params()
        facilities = _tagged_for_contract()
        base_parts, extra_parts = [], []
        for s in ww_specs:
            g = _load_line_layer(s, cfg, params, facilities)
            if g is None or g.empty:
                continue
            (base_parts if s.name == "waterways" else extra_parts).append(g[["geometry"]])
        base = (gpd.GeoDataFrame(pd.concat(base_parts, ignore_index=True), geometry="geometry",
                                 crs=base_parts[0].crs) if base_parts else None)
        extra = (gpd.GeoDataFrame(pd.concat(extra_parts, ignore_index=True), geometry="geometry",
                                  crs=extra_parts[0].crs) if extra_parts else None)
        if base is not None and extra is not None and len(extra):
            base, extra, n_weld = _weld_barge_landings(
                base, extra, MARINE_LANDING_TOL, WATERWAY_NODE_TOL)
            print(f"[build] welded {n_weld} manual-barge endpoint(s) onto the marine spine "
                  f"(≤ {MARINE_LANDING_TOL:.0f} m; inserted a shared vertex at each landing)")
        combined = [df for df in (base, extra) if df is not None and len(df)]
        if combined:
            waterway = gpd.GeoDataFrame(pd.concat(combined, ignore_index=True),
                                        geometry="geometry", crs=combined[0].crs)
        if len(ww_specs) > 1:
            print(f"[build] waterway = {len(ww_specs)} Barge layer(s) "
                  f"({', '.join(s.name for s in ww_specs)}) -> "
                  f"{0 if waterway is None else len(waterway):,} lines")

    # 2. resolve the connection inputs from the profile (data-driven).
    label_by_mode = {s.mode: s.edge_label for s in line_specs}
    road_types = {s.edge_label for s in line_specs if s.mode == "Road"}
    # ground surface(s) hubs may snap onto (profile snap_target flag); default to road.
    snap_types = {s.edge_label for s in line_specs if getattr(s, "snap_target", False)} or road_types

    # 2a. airport snap-to-road: move each air-leg airport endpoint onto its nearest road node (a SHARED
    #     node, no transfer edge) before the connect.
    for s in cfg.snaps:
        if s.from_mode in label_by_mode and s.to_mode in label_by_mode:
            r_edges, n_snap = _snap_airways_to_road(
                r_edges, label_by_mode[s.from_mode], label_by_mode[s.to_mode],
                _resolve_anchor(s.anchor, cfg, hubs), float(s.max_dist))
            print(f"[build] snapped {n_snap} {s.from_mode} endpoints onto {s.to_mode} nodes "
                  f"(anchor={s.anchor}, ≤{s.max_dist:.0f} m)")

    transfers: list[dict] = []
    anchors: dict[str, gpd.GeoDataFrame] = {}
    for t in cfg.transfers:
        if t.from_mode in label_by_mode and t.to_mode in label_by_mode:
            if t.anchor not in anchors:
                anchors[t.anchor] = _resolve_anchor(t.anchor, cfg, hubs)
            transfers.append({"from_type": label_by_mode[t.from_mode],
                              "to_type": label_by_mode[t.to_mode],
                              "anchor": t.anchor, "max_dist": float(t.max_dist)})

    # proximity before-policies (road↔road / ice↔ice welds, ice↔road bridge), modes → edge labels.
    bridges = [{"from_type": label_by_mode[b.from_mode], "to_type": label_by_mode[b.to_mode],
                "max_dist": float(b.max_dist), "edge_type": getattr(b, "edge_type", "Bridge")}
               for b in cfg.bridges if b.from_mode in label_by_mode and b.to_mode in label_by_mode]
    connect_max_dist = float(cfg.connect_to_giant.max_dist)

    # 3. Python connect — fast, spatial-indexed, once.
    nodes, edges, _ = connect_multimodal(r_edges, hubs, road_types, transfers, anchors,
                                         snap_types=snap_types, waterway=waterway,
                                         waterway_label=waterway_label, bridges=bridges,
                                         connect_max_dist=connect_max_dist)

    net = NetworkTables.from_parts(nodes, edges)
    net.to_gpkg(out_prefix)
    return net
