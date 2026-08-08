#!/usr/bin/env python3
"""Explore the network's COMPONENTS in QGIS + measure each one's distance to the giant.

Reads the build output (`output/03_network__{nodes,edges}.gpkg`) and, for every connected
component that is NOT the giant, computes the straight-line distance from the component to the
giant network (nearest node → nearest giant node). Produces:

  1. `output/alaska_components_qgis.gpkg` — layers to explore the components:
       boundary, giant_edges, component_edges (the disconnected pieces),
       component_nodes, components (one labeled point per non-giant component),
       gap_lines (the shortest link from each component to the giant, length = the distance).
  2. `output/alaska_components.qgz` — a QGIS project pre-styled: the giant in grey, the
       disconnected components graduated by distance-to-giant (green = near … red = far),
       gap lines dashed and labeled with the distance in km.
  3. `output/component_distances.csv` — the per-component table (id, nodes, modes, distance).

Usage:  python3 workflows/02_network_build/viz/export_qgis_components.py
"""
from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point

ROOT = Path(__file__).resolve().parents[3]  # repo root
PROJ = ROOT / "outputs" / "02_network_build"  # mmnet project dir: engine writes PROJ/output + PROJ/reports
OUT = PROJ / "output"
BOUNDARY = ROOT / "data" / "boundary.geojson"
GPKG_OUT = OUT / "alaska_components_qgis.gpkg"
QGZ_OUT = OUT / "alaska_components.qgz"
CSV_OUT = OUT / "component_distances.csv"
TARGET_CRS = 3338

# distance-to-giant class breaks (meters) + a green→red ramp (near = green, far = red)
DIST_BREAKS = [0, 500, 1000, 2000, 5000, 20000, 1e12]
DIST_COLORS = ["#1a9850", "#91cf60", "#fee08b", "#fc8d59", "#d73027", "#7a0177"]
DIST_LABELS = ["≤ 0.5 km", "0.5–1 km", "1–2 km", "2–5 km", "5–20 km", "> 20 km"]


# --------------------------------------------------------------------------- compute
def compute() -> dict:
    """Build the component GeoDataFrames + the per-component distance-to-giant table."""
    nt_nodes = gpd.read_file(OUT / "03_network__nodes.gpkg").to_crs(TARGET_CRS)
    nt_edges = gpd.read_file(OUT / "03_network__edges.gpkg").to_crs(TARGET_CRS)
    nt_nodes["node_id"] = nt_nodes["node_id"].astype(int)
    nt_nodes["component"] = nt_nodes["component"].astype(int)
    is_giant = nt_nodes["is_giant"].fillna(False).astype(bool)
    giant_id = int(nt_nodes.loc[is_giant, "component"].mode().iloc[0])

    xy = np.c_[nt_nodes.geometry.x.values, nt_nodes.geometry.y.values]
    id_to_row = {nid: i for i, nid in enumerate(nt_nodes["node_id"].values)}

    giant_mask = nt_nodes["component"].eq(giant_id).values
    giant_xy = xy[giant_mask]
    giant_tree = cKDTree(giant_xy)

    # edge → component (endpoints of a real edge share a component)
    nt_edges["from"] = nt_edges["from"].astype(int)
    nt_edges["comp"] = nt_edges["from"].map(
        dict(zip(nt_nodes["node_id"], nt_nodes["component"]))).fillna(-1).astype(int)
    nt_edges["in_giant"] = nt_edges["comp"].eq(giant_id)

    # per-component: size, modes, nearest-to-giant pair, distance
    rows, gap_geoms = [], []
    modes_by_comp = (nt_edges.groupby("comp")["type"]
                     .agg(lambda s: "+".join(sorted(set(s)))).to_dict())
    for comp, grp in nt_nodes.groupby("component"):
        if comp == giant_id:
            continue
        c_xy = np.c_[grp.geometry.x.values, grp.geometry.y.values]
        d, idx = giant_tree.query(c_xy)
        j = int(np.argmin(d))
        dist = float(d[j])
        c_pt = c_xy[j]
        g_pt = giant_xy[int(idx[j])]
        rows.append({
            "component": int(comp),
            "n_nodes": int(len(grp)),
            "n_edges": int((nt_edges["comp"] == comp).sum()),
            "modes": modes_by_comp.get(comp, ""),
            "n_hubs": int(grp["is_hub"].fillna(False).astype(bool).sum())
                       if "is_hub" in grp else 0,
            "dist_to_giant_m": round(dist, 1),
            "dist_to_giant_km": round(dist / 1000, 3),
            "geometry": Point(c_pt),          # the component's nearest node (representative pt)
        })
        gap_geoms.append(LineString([c_pt, g_pt]))

    comp_pts = gpd.GeoDataFrame(rows, geometry="geometry", crs=TARGET_CRS)
    comp_pts = comp_pts.sort_values("dist_to_giant_m").reset_index(drop=True)

    gaps = gpd.GeoDataFrame(
        {"component": [r["component"] for r in rows],
         "dist_to_giant_m": [r["dist_to_giant_m"] for r in rows],
         "modes": [r["modes"] for r in rows]},
        geometry=gap_geoms, crs=TARGET_CRS)

    comp_node_ids = set(comp_pts["component"])
    comp_nodes = nt_nodes[~nt_nodes["component"].eq(giant_id)].copy()
    comp_nodes["dist_to_giant_m"] = comp_nodes["component"].map(
        dict(zip(comp_pts["component"], comp_pts["dist_to_giant_m"])))

    return {
        "giant_id": giant_id,
        "boundary": gpd.read_file(BOUNDARY).to_crs(TARGET_CRS) if BOUNDARY.exists() else None,
        "giant_edges": nt_edges.loc[nt_edges["in_giant"], ["type", "source", "geometry"]].reset_index(drop=True),
        "component_edges": nt_edges.loc[~nt_edges["in_giant"],
                                        ["type", "source", "comp", "geometry"]]
            .rename(columns={"comp": "component"}).reset_index(drop=True),
        "component_nodes": comp_nodes[["node_id", "component", "dist_to_giant_m", "geometry"]],
        "components": comp_pts,
        "gap_lines": gaps,
    }


# --------------------------------------------------------------------------- GeoPackage
def build_gpkg(layers: dict) -> None:
    if GPKG_OUT.exists():
        GPKG_OUT.unlink()
    order = ["boundary", "giant_edges", "component_edges", "gap_lines",
             "component_nodes", "components"]
    first, counts = True, {}
    for name in order:
        gdf = layers.get(name)
        if gdf is None or not len(gdf):
            continue
        gdf.to_file(GPKG_OUT, layer=name, driver="GPKG", mode="w" if first else "a")
        counts[name] = len(gdf); first = False
    print(f"GeoPackage -> {GPKG_OUT.relative_to(ROOT)}  layers={counts}")


# --------------------------------------------------------------------------- QGIS project
def _hexrgb(h: str) -> str:
    h = h.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


def build_qgz() -> bool:
    try:
        from qgis.core import (
            QgsApplication, QgsCoordinateReferenceSystem, QgsFillSymbol,
            QgsGraduatedSymbolRenderer, QgsLineSymbol, QgsMarkerSymbol,
            QgsPalLayerSettings, QgsProject, QgsRendererRange, QgsTextFormat,
            QgsVectorLayer, QgsVectorLayerSimpleLabeling,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"PyQGIS not available ({exc}); skipping .qgz (the GeoPackage + CSV are ready).")
        return False

    QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
    qgs = QgsApplication([], False)
    qgs.initQgis()
    try:
        project = QgsProject.instance()
        project.clear()
        project.setCrs(QgsCoordinateReferenceSystem(f"EPSG:{TARGET_CRS}"))
        project.writeEntryBool("Paths", "/Absolute", False)

        def load(layer_name, title):
            lyr = QgsVectorLayer(f"{GPKG_OUT}|layername={layer_name}", title, "ogr")
            return lyr if lyr.isValid() else None

        def line_sym(hexc, width=0.4, dashed=False):
            s = QgsLineSymbol.createSimple({"color": _hexrgb(hexc), "width": str(width)})
            if dashed:
                sl = s.symbolLayer(0); sl.setUseCustomDashPattern(True); sl.setCustomDashVector([3.0, 2.0])
            return s

        def marker_sym(hexc, size=2.6, outline="0,0,0", ow=0.3):
            return QgsMarkerSymbol.createSimple(
                {"color": _hexrgb(hexc), "size": str(size),
                 "outline_color": outline, "outline_width": str(ow)})

        def graduated(field, sym_factory):
            ranges = []
            for i in range(len(DIST_BREAKS) - 1):
                lo, hi = DIST_BREAKS[i], DIST_BREAKS[i + 1]
                ranges.append(QgsRendererRange(lo, hi, sym_factory(DIST_COLORS[i]), DIST_LABELS[i]))
            return QgsGraduatedSymbolRenderer(field, ranges)

        def label_by(layer, expr, size=8):
            s = QgsPalLayerSettings(); s.fieldName = expr; s.isExpression = True
            fmt = QgsTextFormat(); fmt.setSize(size)
            s.setFormat(fmt)
            layer.setLabeling(QgsVectorLayerSimpleLabeling(s)); layer.setLabelsEnabled(True)

        added = []

        boundary = load("boundary", "Alaska boundary")
        if boundary:
            boundary.renderer().setSymbol(QgsFillSymbol.createSimple(
                {"color": "241,234,214,80", "outline_color": "52,105,154", "outline_width": "0.3"}))
            added.append(boundary)

        giant = load("giant_edges", "Giant component (connected core)")
        if giant:
            giant.renderer().setSymbol(line_sym("#b8b8b8", width=0.3))
            giant.setOpacity(0.9)
            added.append(giant)

        cedges = load("component_edges", "Disconnected component edges")
        if cedges:
            cedges.renderer().setSymbol(line_sym("#d73027", width=0.9))
            added.append(cedges)

        gaps = load("gap_lines", "Distance to giant (shortest link)")
        if gaps:
            gaps.setRenderer(graduated("dist_to_giant_m", lambda c: line_sym(c, width=0.8, dashed=True)))
            label_by(gaps, "round(\"dist_to_giant_m\"/1000, 2) || ' km'", size=7)
            added.append(gaps)

        cnodes = load("component_nodes", "Disconnected nodes")
        if cnodes:
            cnodes.renderer().setSymbol(marker_sym("#d73027", size=1.2, outline="255,255,255", ow=0.2))
            cnodes.setOpacity(0.7)
            added.append(cnodes)

        comps = load("components", "Components (by distance to giant)")
        if comps:
            comps.setRenderer(graduated("dist_to_giant_m", lambda c: marker_sym(c, size=3.4)))
            label_by(comps, "'C' || \"component\" || ' · ' || round(\"dist_to_giant_m\"/1000,1) || ' km'", size=8)
            added.append(comps)

        for lyr in added:
            project.addMapLayer(lyr)
        project.write(str(QGZ_OUT))
        print(f"QGIS project -> {QGZ_OUT.relative_to(ROOT)}  ({len(added)} styled layers)")
        return True
    finally:
        qgs.exitQgis()


def main() -> None:
    if not (OUT / "03_network__nodes.gpkg").exists():
        raise SystemExit("build output missing — run the pipeline first.")
    layers = compute()
    comps = layers["components"]

    # CSV + console table
    tbl = comps.drop(columns="geometry").copy()
    tbl.to_csv(CSV_OUT, index=False)
    print(f"\n{len(comps)} disconnected components; distance to the giant "
          f"(giant component id = {layers['giant_id']}):")
    print(f"  nearest : C{tbl.iloc[0]['component']}  {tbl.iloc[0]['dist_to_giant_km']} km  "
          f"({tbl.iloc[0]['modes']}, {tbl.iloc[0]['n_nodes']} nodes)")
    print(f"  farthest: C{tbl.iloc[-1]['component']}  {tbl.iloc[-1]['dist_to_giant_km']} km  "
          f"({tbl.iloc[-1]['modes']}, {tbl.iloc[-1]['n_nodes']} nodes)")
    d = tbl["dist_to_giant_m"]
    for lo, hi, lab in zip(DIST_BREAKS[:-1], DIST_BREAKS[1:], DIST_LABELS):
        print(f"    {lab:>9}: {int(((d >= lo) & (d < hi)).sum())} components")
    print(f"  median gap {d.median()/1000:.2f} km · CSV -> {CSV_OUT.relative_to(ROOT)}")

    build_gpkg(layers)
    ok = build_qgz()
    print("\nOpen in QGIS:")
    if ok:
        print(f"  • {QGZ_OUT.relative_to(ROOT)}   (styled — components colored by distance to giant)")
    print(f"  • {GPKG_OUT.relative_to(ROOT)}   (drag layers in; the `gap_lines`/`components` carry dist_to_giant_m)")


if __name__ == "__main__":
    main()
