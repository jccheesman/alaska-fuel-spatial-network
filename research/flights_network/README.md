# research/flights_network — the Alaska air-cargo network from the new Flights data

A research sandbox (read-only w.r.t. the engine) that **characterizes the new `data/raw/connectivity/air/` air-cargo
dataset** and **builds + studies the Alaska air network** from it: hubs, spokes, components, and how much of
the airport registry it serves. Mirrors `research/waterway_network/`.

## Data
- **Official air source:** `data/raw/connectivity/air/flight_paths_combined.csv` — 98 OD cargo legs with
  embedded coords + FAA/ICAO + region/owner/status + source provenance, built by `build_map.py` from the AK
  DOT&PF registry `airports_ak_dotpf.csv` (285 airports). This is now the **official** flight data and feeds
  the pipeline via `scripts/normalize_raw.py` → interim → `scripts/prep_airways.py` → processed.
- See **`DATA_COMPARISON.md`** for the new-vs-old report (the old global-geocode inputs it replaced).

## Scripts (run from this folder)
```
python3 01_air_network.py   # build nodes (airports→EPSG:3338) + edges (legs); components/hubs/spokes;
                            # writes out/air_network__{nodes,edges}.gpkg + the network map + degree chart
python3 02_structure.py     # hierarchy, degree distribution, region/owner/status, coverage vs the 285
                            # registry airports; writes out/02_* figures
```
Reuses the project: `_trace.py` (the sandbox Tracer), `mmnet.config.load_config` (target CRS 3338),
`data/boundary.geojson` (basemap). Outputs land in `out/` (gitignored via `research/**/out/`).

## Result
86 airports, 98 legs, 2 components (giant 98 %); trunk ANC/FAI → regional hubs **Bethel (32)**/Nome/Kotzebue
→ 72 spokes; **30 %** of the 285 registry airports are cargo-served (Northern/Western; Southeast ~3 %).
Full writeup in **`FINDINGS.md`**.
