# The new Flights data vs. the existing raw air data — a comparison

This study builds on a **new, self-contained Alaska air-cargo dataset** in `data/raw/connectivity/air/`. It supersedes
the air inputs the mmnet pipeline currently uses. The two differ in source, completeness, and quality.

## The new data — `data/raw/connectivity/air/`
A provenance-tracked, GIS-validated air-cargo network keyed to the authoritative Alaska airport registry.

- **`flight_paths_combined.csv`** — **98 OD cargo legs**, **86 airports**. Each leg carries **embedded
  coordinates** (`Origin/Destination_Lat/Lon`), **FAA_ID + ICAO + airport name**, and **STATUS / REGION /
  OWNER**, plus a **`Source` citation per leg** (carrier schedules, Flightsfrom.com). Carriers:
  **Lynden Air Cargo 66 · Everts Air Cargo 28 · Bering Air 4**.
- **`Airports.csv`** — **285 Alaska airports** from the **AK DOT&PF GIS registry** (NAME, FAA_ID, ICAO,
  LAT_DD/LONG_DD, REGION, OWNER, STATUS, GlobalID).
- **`build_map.py`** — matches a hand-curated `Flight Paths.xlsx` to that registry by FAA code → fuzzy
  base-name → manual typo overrides → hard-coded military fields, then writes the combined CSV, an
  interactive **`flight_map.html`**, and an **`unmatched_locations.csv`**. Only **1 location was unmatched**
  (Newtok — the village relocated to Mertarvik; its FAA field is EWU).

## The existing raw data — `data/raw/connectivity/air/`
- **`air_flight_paths_od.csv`** — **78 OD legs** (`origin_code`/`destination_code`/`primary_carrier`/
  `service_type`/`notes`), including **Ryan Air** Kuskokwim-delta spokes — but **no coordinates**.
- **`airports.csv`** — the **85,130-row global OurAirports DB (12.5 MB)**, used only to *geocode* the bare
  codes. This mis-geocodes some Alaska codes to **lower-48 airports** (the documented README bug) and the
  codes themselves are inconsistent (e.g. EMK↔ENM, AET↔6A8, HSL↔HLA).
- Feeds the build via **`scripts/prep_airways.py`** → `data/processed/airways.geojson` (LineStrings) +
  `air_nodes.geojson` (the profile's `airways` layer + `airports` anchor).

## Side by side
| | OLD raw (`data/raw/.../air`) | NEW (`data/raw/connectivity/air/`) |
|---|---|---|
| OD legs | 78 | **98** |
| airport master | 85,130 global (mis-geocodes to lower-48) | **285 curated AK (DOT&PF)** |
| coordinates | none — external geocode | **embedded per endpoint** |
| identifiers | code only (several wrong) | **FAA_ID + ICAO + name (validated)** |
| attributes | carrier, service_type | + **status, region, owner** |
| provenance | `notes` only | **`Source` citation per leg** |
| unmatched report | silent | **explicit (1: Newtok)** |
| geocoding errors | yes (lower-48) | **none (matched to AK registry)** |
| extras | — | **build script + interactive map** |

## What the new data gives this network (see 01/02)
- A connected hub-and-spoke graph: **2 components**, giant **84 / 86 airports (98 %)**; the off-giant pair
  is **Kenai ↔ Nondalton** (a leg not linked to the trunk).
- Hierarchy: **trunk** ANC/FAI → **regional hubs** Bethel (deg 32), Nome (19), Kotzebue (13) → 72 spokes.
- Coverage: **85 of the 285 registry airports (30 %)** carry a cargo leg — Northern 43 %, Central 39 %, but
  **Southcoast/Southeast just 3 %** (the panhandle + Aleutians, served mostly by ferry/barge).

## Caveats (why this is research, not a drop-in swap)
- **Different source compilations.** The new file is built from `Flight Paths.xlsx` (Lynden-heavy); the old
  list is a separately curated OD set with **Ryan Air** delta spokes. The route sets and carrier attribution
  differ — reconciling them into one authoritative OD set is a separate task (not done here).
- **Now the official source.** The new data has since been promoted to the official air input at
  `data/raw/connectivity/air/` and wired into the pipeline (`normalize_raw.py` → interim →
  `prep_airways.py` → processed); the old global-geocode inputs were removed. Geocoding the OD codes against
  the AK registry drops 2 legs whose codes aren't in it (Tin City `TNC`, one blank `NAN`) → 96/98 legs.
