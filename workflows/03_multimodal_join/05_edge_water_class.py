#!/usr/bin/env python3
"""Marine / river water class per Waterway edge -> edge_water_class table.

Samples the water-class label (workflow 01's water_class_150m.tif) along every
Waterway edge with the SAME 75 m midpoint sampler workflow 03 uses for the
friction weights, and writes a NEW DuckDB table:

    edge_water_class(edge_id, marine_frac, river_frac, notwater_frac, water_class)

water_class: marine (>= 90% of water samples marine), river (>= 90% river),
mixed (an edge crossing a river mouth), no_water_samples. The fractions are
length-weighted over WATER samples; corridor pixels whose centre misses the
burned cell are excluded from that denominator and reported in notwater_frac.

edge_month_weights and edge_class are untouched — this is a sibling table the
barge cost split (line-haul vs lightering vs river barge) reads. Exits GATE (3)
when the label raster is absent. Requires stage 02 (network_edges in DuckDB)
and the extracted final_network shapefile (stage 01).

Usage:  python workflows/03_multimodal_join/05_edge_water_class.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

import repo_paths as rp
from fuel_network.weights import build_sample_arrays
from friction_surface.friction_config import WATER_CLASS_MARINE, WATER_CLASS_RIVER
from friction_surface.friction_paths import WATER_CLASS_TIF

GATE_EXIT = 3
PURE = 0.9  # >= this fraction of water samples -> a pure marine / river class


def main() -> int:
    wc = Path(WATER_CLASS_TIF)
    if not wc.exists():
        print(f"GATE: {wc} absent — run workflows/01_friction_build/04_build_water_class.py")
        return GATE_EXIT
    if not rp.FINAL_EDGES_SHP.exists():
        print(f"GATE: {rp.FINAL_EDGES_SHP} absent — run 01_extract_network_handoff.py")
        return GATE_EXIT

    con = duckdb.connect(str(rp.DUCKDB))
    ww_ids = set(con.execute(
        "SELECT edge_id FROM network_edges WHERE edge_class = 'Waterway'").df().edge_id)
    if not ww_ids:
        print("FAIL: no Waterway edges in network_edges — run 02_load_final_network.py first")
        return 1
    edges = gpd.read_file(rp.FINAL_EDGES_SHP)
    edges["edge_id"] = range(len(edges))  # fuel_network.load: edge_id = row order
    ww = edges[edges.edge_id.isin(ww_ids)]
    xy, seg_len, owner = build_sample_arrays(ww.geometry, ww.edge_id)
    print(f"{len(ww)} Waterway edges, {len(xy):,} samples")

    with rasterio.open(wc) as src:
        rows, cols = rasterio.transform.rowcol(src.transform, xy[:, 0], xy[:, 1])
        rows = np.clip(np.asarray(rows), 0, src.height - 1)
        cols = np.clip(np.asarray(cols), 0, src.width - 1)
        vals = src.read(1)[rows, cols]

    owner = np.asarray(owner)
    n_max = int(owner.max()) + 1
    mar = np.bincount(owner, weights=seg_len * (vals == WATER_CLASS_MARINE), minlength=n_max)
    riv = np.bincount(owner, weights=seg_len * (vals == WATER_CLASS_RIVER), minlength=n_max)
    nww = np.bincount(owner, weights=seg_len * (vals == 0), minlength=n_max)
    ids = np.unique(owner)
    mar, riv, nww = mar[ids], riv[ids], nww[ids]
    water = mar + riv
    with np.errstate(invalid="ignore", divide="ignore"):
        ewc = pd.DataFrame({
            "edge_id": ids,
            "marine_frac": np.where(water > 0, mar / water, np.nan),
            "river_frac": np.where(water > 0, riv / water, np.nan),
            "notwater_frac": nww / (water + nww),
        })
    ewc["water_class"] = np.select(
        [water <= 0, ewc.marine_frac >= PURE, ewc.river_frac >= PURE],
        ["no_water_samples", "marine", "river"], default="mixed")

    con.execute("DROP TABLE IF EXISTS edge_water_class")
    con.execute("CREATE TABLE edge_water_class AS SELECT * FROM ewc")
    con.close()
    print(ewc.water_class.value_counts().to_string())
    mixed = ewc[ewc.water_class == "mixed"]
    if len(mixed):
        print(f"mixed (river-mouth) edges: {mixed.edge_id.tolist()}")
    print(f"wrote edge_water_class ({len(ewc)} rows) to {rp.DUCKDB}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
