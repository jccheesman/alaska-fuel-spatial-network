#!/usr/bin/env python3
"""STEP 04 — export the connected-vs-disconnected network as a styled QGIS project.

Turns `out/connected_via_ports__edges.gpkg` (road+ice+waterway + port/weld/bridge connectors, tagged
`source` + `is_giant`) into a clean multi-layer GeoPackage + a pre-styled `.qgz` so the connected (giant)
vs disconnected features can be explored interactively in QGIS — the interactive version of
`03_connected_vs_disconnected.png`. Run: python3 research/waterway_network/04_qgis_connected.py
"""

import os

import geopandas as gpd
import numpy as np

from _trace import OUT, ROOT, Tracer

T = Tracer("04_qgis_connected", "STEP 04 — QGIS export of the connected vs disconnected network")
TARGET = 3338
GPKG = OUT / "connected_vs_disconnected_qgis.gpkg"
QGZ = OUT / "connected_vs_disconnected.qgz"
SRC = OUT / "connected_via_ports__edges.gpkg"

# ── build the layered GeoPackage ──
e = gpd.read_file(SRC).to_crs(TARGET)
e["status"] = np.where(e["is_giant"].astype(bool), "connected", "disconnected")
boundary = gpd.read_file(ROOT / "data" / "boundary.geojson").to_crs(TARGET)
ports = gpd.read_file(ROOT / "data" / "raw" / "anchor_points" / "Ports_and_Harbors.geojson").to_crs(TARGET)

conn_sources = [s for s in e["source"].unique() if (":" in str(s)) or str(s).startswith(("port", "hub",
                "weld", "bridge"))]

# hubs — SNAPPED to the ground network + tagged connected/disconnected by step 02 (single source of truth)
hubs_all = gpd.read_file(OUT / "connected_hubs__snapped.gpkg").to_crs(TARGET)

layers = {
    "boundary": boundary,
    "waterway": e[e["source"] == "Waterway"][["source", "status", "geometry"]],
    "land_network": e[e["source"].isin(["Road", "IceRoad"])][["source", "status", "geometry"]],
    "connectors": e[e["source"].isin(conn_sources)][["source", "status", "geometry"]],
    "hubs": hubs_all,
    "ports": ports,
}
for name, gdf in layers.items():
    gdf.to_file(GPKG, layer=name, driver="GPKG")
    T.kv(f"layer '{name}'", f"{len(gdf)} features")
T.note(f"land_network categorized by `status`: connected (giant) vs disconnected; "
       f"{int((e['source'].isin(['Road','IceRoad']) & (e['status']=='connected')).sum()):,} connected / "
       f"{int((e['source'].isin(['Road','IceRoad']) & (e['status']=='disconnected')).sum()):,} disconnected.")

# ── build the styled .qgz with PyQGIS ──
try:
    from qgis.core import (QgsApplication, QgsCategorizedSymbolRenderer, QgsCoordinateReferenceSystem,
                           QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol, QgsProject,
                           QgsRendererCategory, QgsSimpleMarkerSymbolLayerBase, QgsVectorLayer)
except Exception as exc:  # noqa: BLE001
    T.note(f"PyQGIS unavailable ({exc}); the GeoPackage is ready — drag layers into QGIS, style "
           "'land_network' by `status`.")
    T.done(); raise SystemExit


def rgb(h):
    h = h.lstrip("#"); return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
app = QgsApplication([], False); app.initQgis()
try:
    project = QgsProject.instance(); project.clear()
    project.setCrs(QgsCoordinateReferenceSystem(f"EPSG:{TARGET}"))
    project.writeEntryBool("Paths", "/Absolute", False)

    def load(layer, title):
        lyr = QgsVectorLayer(f"{GPKG}|layername={layer}", title, "ogr")
        return lyr if lyr.isValid() else None

    def line(hexc, w=0.3, dashed=False):
        s = QgsLineSymbol.createSimple({"color": rgb(hexc), "width": str(w)})
        if dashed:
            sl = s.symbolLayer(0); sl.setUseCustomDashPattern(True); sl.setCustomDashVector([3.0, 2.0])
        return s

    def marker(hexc, size=2.4, shape=None):
        s = QgsMarkerSymbol.createSimple({"color": rgb(hexc), "size": str(size),
                                          "outline_color": "255,255,255", "outline_width": "0.2"})
        if shape is not None:
            s.symbolLayer(0).setShape(shape)
        return s

    def cat(field, mapping, factory):
        return QgsCategorizedSymbolRenderer(field, [QgsRendererCategory(k, factory(v), str(k))
                                                    for k, v in mapping.items()])

    added = []
    b = load("boundary", "Alaska boundary")
    if b:
        b.renderer().setSymbol(QgsFillSymbol.createSimple(
            {"color": "241,234,214,70", "outline_color": "184,168,122", "outline_width": "0.3"}))
        added.append(b)
    w = load("waterway", "Waterway — connected vs disconnected")
    if w:
        w.setRenderer(cat("status", {"connected": "#2ca02c", "disconnected": "#d62728"},
                          lambda c: line(c, w=0.45)))
        added.append(w)
    land = load("land_network", "Road + ice — connected vs disconnected")
    if land:
        land.setRenderer(cat("status", {"connected": "#2ca02c", "disconnected": "#d62728"},
                             lambda c: line(c, w=0.35 if c == rgb("#2ca02c") else 0.5)))
        added.append(land)
    c = load("connectors", "Connectors (Barge transfer · weld · bridge)")
    if c:
        def conn_color(src):
            if "Barge" in src:
                return "#000000"                 # port/hub Barge transfers
            return "#ff7f0e" if src.startswith("weld") else "#9467bd"   # weld / bridge
        c.setRenderer(cat("source", {s: conn_color(s) for s in conn_sources},
                          lambda col: line(col, w=0.7, dashed=True)))
        added.append(c)
    hb = load("hubs", "Fuel hubs (snapped) — connected vs disconnected")
    if hb:
        hb.setRenderer(cat("status", {"connected": "#2ca02c", "disconnected": "#d62728"},
                           lambda col: marker(col, size=3.0, shape=QgsSimpleMarkerSymbolLayerBase.Star)))
        added.append(hb)
    pt = load("ports", "Ports / harbors")
    if pt:
        pt.renderer().setSymbol(marker("#1565c0", size=2.4, shape=QgsSimpleMarkerSymbolLayerBase.Square))
        added.append(pt)
    for lyr in added:
        project.addMapLayer(lyr)
    project.write(str(QGZ))
    T.kv("wrote QGIS project", f"{QGZ.relative_to(ROOT)}  ({len(added)} styled layers)")
finally:
    app.exitQgis()

T.note("Open out/connected_vs_disconnected.qgz in QGIS (fully styled): land_network AND waterway both "
       "green=connected / red=disconnected, connectors dashed (port/hub/weld/bridge), ports as squares. "
       "Or drag the gpkg layers in and style by `status`.")
T.done()
