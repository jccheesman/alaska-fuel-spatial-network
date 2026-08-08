#!/usr/bin/env python3
"""Export the final multimodal network for viewing in QGIS — styled and ready to open.

Reads the build output (`output/03_network__{nodes,edges}.gpkg`) plus context layers (Alaska
boundary, ports, airport nodes) and produces:

  1. `output/alaska_network_qgis.gpkg` — one GeoPackage with clean, separated layers:
       boundary, edges, transfers, nodes, hubs, ports, airports.
  2. `output/alaska_network.qgz` — a QGIS project with every layer pre-styled (edges colored
     by mode, intermodal transfers highlighted, hubs by delivery method, ports/airports as
     anchors). Just open this file in QGIS.

The .qgz needs PyQGIS (`qgis.core`); if it is unavailable the GeoPackage is still written and
you can drag its layers into QGIS and style them by the `type` / `delivery_method` fields.

Usage:
    python workflows/02_network_build/viz/export_qgis.py
"""

from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[3]  # repo root
PROJ = ROOT / "outputs" / "02_network_build"  # mmnet project dir: engine writes PROJ/output + PROJ/reports
OUT = PROJ / "output"
EDGES_IN = OUT / "03_network__edges.gpkg"
NODES_IN = OUT / "03_network__nodes.gpkg"
BOUNDARY = ROOT / "data" / "boundary.geojson"
PORTS = ROOT / "data" / "raw" / "anchor_points" / "Ports_and_Harbors.geojson"
AIR_NODES = ROOT / "data" / "processed" / "air_nodes.geojson"

GPKG_OUT = OUT / "alaska_network_qgis.gpkg"
QGZ_OUT = OUT / "alaska_network.qgz"
TARGET_CRS = 3338

# Mode colors (match mmnet.viz); IceRoad = cyan, Bridge = orange (welds / cross-mode bridges).
EDGE_COLORS = {
    "Road": "#6b6b6b", "Waterway": "#1f77b4", "Air": "#9467bd",
    "IceRoad": "#17becf", "Transfer": "#d62728", "Bridge": "#ff7f0e",
    "Join": "#000000",   # Stage-04 component→giant joins (04_network_joined)
}
HUB_COLORS = {  # by delivery_method (incl. multimodal mixes)
    "Road": "#2ca02c", "Barge": "#1f77b4", "Plane": "#9467bd",
    "Barge or Road": "#8c564b", "Barge or Plane": "#e377c2",
    "Plane or Road": "#ff7f0e", "Barge or Plane or Road": "#bcbd22",
}


def _to_crs(g: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return g.to_crs(TARGET_CRS) if g.crs is not None else g.set_crs(TARGET_CRS)


def build_gpkg() -> dict:
    """Write the consolidated, layer-separated GeoPackage. Returns the layer rowcounts."""
    if not EDGES_IN.exists() or not NODES_IN.exists():
        raise SystemExit(f"build output missing — run the pipeline first ({EDGES_IN.name}).")

    edges = _to_crs(gpd.read_file(EDGES_IN))
    nodes = _to_crs(gpd.read_file(NODES_IN))
    edges["length_m"] = edges.geometry.length.round(1)

    is_hub = nodes["is_hub"].fillna(False).astype(bool)
    layers = {
        "boundary": _to_crs(gpd.read_file(BOUNDARY)) if BOUNDARY.exists() else None,
        "edges": edges[["type", "source", "length_m", "from", "to", "geometry"]],
        "transfers": edges.loc[edges["type"] == "Transfer",
                               ["type", "source", "length_m", "geometry"]].reset_index(drop=True),
        # every intermodal connection — transfers (port/hub/airport + shore landings) AND the bridges
        # (road↔road / ice↔ice welds, ice↔road bridge, weld-to-giant), distinguishable by `source`.
        "connectors": edges.loc[edges["type"].isin(["Transfer", "Bridge"]),
                                ["type", "source", "length_m", "geometry"]].reset_index(drop=True),
        "nodes": nodes[["node_id", "is_hub", "component", "is_giant", "geometry"]],
        "hubs": nodes.loc[is_hub, [c for c in ("hub_id", "delivery_method", "hub_type",
                                              "total_hub_capacity", "snap_surface",
                                              "component", "is_giant", "geometry")
                                   if c in nodes.columns]].reset_index(drop=True),
        "ports": _to_crs(gpd.read_file(PORTS)) if PORTS.exists() else None,
        "airports": _to_crs(gpd.read_file(AIR_NODES)) if AIR_NODES.exists() else None,
    }

    if GPKG_OUT.exists():
        GPKG_OUT.unlink()
    counts = {}
    first = True
    for name, gdf in layers.items():
        if gdf is None or not len(gdf):
            continue
        gdf.to_file(GPKG_OUT, layer=name, driver="GPKG", mode="w" if first else "a")
        counts[name] = len(gdf)
        first = False
    print(f"GeoPackage -> {GPKG_OUT.relative_to(ROOT)}  layers={counts}")
    return counts


# --------------------------------------------------------------------------- QGIS project
def _hexrgb(h: str) -> str:
    if "," in h:               # already an "r,g,b" string
        return h
    h = h.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


def build_qgz() -> bool:
    """Build a styled QGIS project (.qgz). Returns False if PyQGIS is unavailable."""
    try:
        from qgis.core import (
            QgsApplication, QgsCategorizedSymbolRenderer, QgsCoordinateReferenceSystem,
            QgsLineSymbol, QgsMarkerSymbol, QgsFillSymbol, QgsProject, QgsRendererCategory,
            QgsSimpleMarkerSymbolLayerBase, QgsVectorLayer,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"PyQGIS not available ({exc}); skipping .qgz (the GeoPackage is ready).")
        return False

    QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
    qgs = QgsApplication([], False)
    qgs.initQgis()
    try:
        project = QgsProject.instance()
        project.clear()
        project.setCrs(QgsCoordinateReferenceSystem(f"EPSG:{TARGET_CRS}"))
        project.writeEntryBool("Paths", "/Absolute", False)  # relative paths -> portable .qgz

        def load(layer_name: str, title: str):
            uri = f"{GPKG_OUT}|layername={layer_name}"
            lyr = QgsVectorLayer(uri, title, "ogr")
            return lyr if lyr.isValid() else None

        def line_sym(hex_color, width=0.26, dashed=False):
            s = QgsLineSymbol.createSimple({"color": _hexrgb(hex_color), "width": str(width)})
            if dashed:
                sl = s.symbolLayer(0)
                sl.setUseCustomDashPattern(True)
                sl.setCustomDashVector([3.0, 2.0])
            return s

        def marker_sym(hex_color, size=2.0, shape=None, outline="255,255,255", ow=0.2):
            s = QgsMarkerSymbol.createSimple(
                {"color": _hexrgb(hex_color), "size": str(size),
                 "outline_color": outline, "outline_width": str(ow)})
            if shape is not None:
                s.symbolLayer(0).setShape(shape)
            return s

        def categorized(field, mapping, sym_factory):
            cats = [QgsRendererCategory(k, sym_factory(v), k) for k, v in mapping.items()]
            return QgsCategorizedSymbolRenderer(field, cats)

        added = []

        # bottom -> top draw order
        boundary = load("boundary", "Alaska boundary")
        if boundary:
            boundary.setRenderer(boundary.renderer())
            fill = QgsFillSymbol.createSimple(
                {"color": "241,234,214,80", "outline_color": "52,105,154", "outline_width": "0.3"})
            boundary.renderer().setSymbol(fill)
            added.append(boundary)

        edges = load("edges", "Network edges (by mode)")
        if edges:
            order = ["Road", "Waterway", "IceRoad", "Air", "Bridge", "Transfer"]
            edges.setRenderer(categorized(
                "type", {k: EDGE_COLORS[k] for k in order},
                lambda c: line_sym(c, width=0.5 if c == EDGE_COLORS["Transfer"] else 0.26,
                                   dashed=(c == EDGE_COLORS["Transfer"]))))
            added.append(edges)

        nodes = load("nodes", "Network nodes")
        if nodes:
            nodes.setRenderer(nodes.renderer())
            nodes.renderer().setSymbol(marker_sym("120,120,120", size=0.7, ow=0.0))
            nodes.setOpacity(0.5)
            added.append(nodes)

        transfers = load("transfers", "Intermodal transfers")
        if transfers:
            transfers.setRenderer(transfers.renderer())
            transfers.renderer().setSymbol(line_sym(EDGE_COLORS["Transfer"], width=0.8, dashed=True))
            added.append(transfers)

        connectors = load("connectors", "Connectors (transfer · weld · bridge · shore) by source")
        if connectors:
            srcs = sorted(set(gpd.read_file(GPKG_OUT, layer="connectors")["source"].astype(str)))

            def conn_color(s: str) -> str:
                if s.startswith("shore"):
                    return "#000000"              # coastal barge landings (ground ↔ waterway)
                if s.startswith("weld"):
                    return "#ff7f0e"              # noding welds (road↔road / ice↔ice / to-giant)
                if s.startswith("bridge"):
                    return "#9467bd"              # cross-mode bridge (ice↔road)
                return "#d62728"                  # anchor transfers (ports / barge_hubs / airports)

            connectors.setRenderer(categorized(
                "source", {s: conn_color(s) for s in srcs},
                lambda c: line_sym(c, width=0.7, dashed=True)))
            added.append(connectors)

        ports = load("ports", "Ports / harbors (barge anchors)")
        if ports:
            ports.setRenderer(ports.renderer())
            ports.renderer().setSymbol(
                marker_sym("#1565c0", size=2.4, shape=QgsSimpleMarkerSymbolLayerBase.Square))
            added.append(ports)

        airports = load("airports", "Airports (air anchors)")
        if airports:
            airports.setRenderer(airports.renderer())
            airports.renderer().setSymbol(
                marker_sym("#2e7d32", size=2.8, shape=QgsSimpleMarkerSymbolLayerBase.Triangle))
            added.append(airports)

        hubs = load("hubs", "Fuel hubs (by delivery method)")
        if hubs:
            hubs.setRenderer(categorized(
                "delivery_method", HUB_COLORS,
                lambda c: marker_sym(c, size=3.4, shape=QgsSimpleMarkerSymbolLayerBase.Star,
                                     outline="0,0,0", ow=0.3)))
            added.append(hubs)

        # add bottom-first so 'added' order becomes draw order (addMapLayer puts new on top)
        for lyr in added:
            project.addMapLayer(lyr)

        project.write(str(QGZ_OUT))
        print(f"QGIS project -> {QGZ_OUT.relative_to(ROOT)}  ({len(added)} styled layers)")
        return True
    finally:
        qgs.exitQgis()


def _use_stem(stem: str) -> None:
    """Point the exporter at a different built network (e.g. `04_network_joined`)."""
    global EDGES_IN, NODES_IN, GPKG_OUT, QGZ_OUT
    EDGES_IN = OUT / f"{stem}__edges.gpkg"
    NODES_IN = OUT / f"{stem}__nodes.gpkg"
    GPKG_OUT = OUT / f"alaska_{stem}_qgis.gpkg"
    QGZ_OUT = OUT / f"alaska_{stem}.qgz"


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Export a built network for QGIS.")
    ap.add_argument("--stem", default="03_network",
                    help="output/<stem>__{nodes,edges}.gpkg to export (e.g. 04_network_joined)")
    args = ap.parse_args()
    if args.stem != "03_network":
        _use_stem(args.stem)

    build_gpkg()
    ok = build_qgz()
    print("\nOpen in QGIS:")
    if ok:
        print(f"  • {QGZ_OUT.relative_to(ROOT)}   (fully styled — double-click or File > Open Project)")
    print(f"  • {GPKG_OUT.relative_to(ROOT)}   (drag layers in; style by 'type' / 'delivery_method')")


if __name__ == "__main__":
    main()
