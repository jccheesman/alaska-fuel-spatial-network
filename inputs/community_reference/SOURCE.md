# Alaska community reference (State of Alaska DCRA)

Two public sources from the Division of Community and Regional Affairs (DCRA),
Alaska Department of Commerce, Community, and Economic Development, committed as
dated snapshots so every consumer (the inventory review, the harness's community
list) reads the same communities. Built and checked by
`tools/input_prep/build_community_reference.py`.

| File | What | Rows | sha256 |
|---|---|---|---|
| `dcra_community_locations.csv` | "Alaska Communities" point layer: every community DCRA tracks, its type, area type, active flag, start/end dates, the layer's own lon/lat attributes (`x`, `y`), the point in EPSG:3338 (`x_3338`, `y_3338`), state-plane zone and DCRA regional-office district. Fetched 2026-11-16 | 489 | `87163f3577a65ade014a4e4185d98779a1cb316508f4e7d52f15be20dbe15d59` |
| `dcra_community_overview.csv` | DCRA Community Overview export (incorporation, borough or census area, population and year, federally recognised tribe, incorporation year; X/Y in EPSG:3338). Downloaded by the owner 2026-10-10; byte-identical to the harness's `okf/catalogs/sources/dcra_Community_Overview.csv` | 482 | `9a045c2b2710b35d48d4c46d87d38d277328c031971964c86b2e6f47de19a81b` |
| `dcra_community_reference.csv` | **Derived**: one row per location-layer community, joined to the Overview by the DCRA community GUID | 489 | `aaddb20cb53df7aab22638851ad7f6933322ea6d432f4bd0ad83fb46a2b37d2c` |

## Where they come from

- Locations: `https://maps.commerce.alaska.gov/server/rest/services/Community_Related/Community_Locations_and_Boundaries/MapServer/0`
  (layer "Alaska Communities", point, native EPSG:3338), queried
  `where=1=1`, `outSR=3338`, ordered by `OBJECTID`, paged by `resultOffset`.
- Overview: DCRA Community Data Online, `dcra-cdo-dcced.opendata.arcgis.com`,
  dataset `a97cb794ab054cd9a4fa7f07b8149b68_0`.

**Not written**, on purpose: `created_user` / `last_edited_user` (names of state
staff), `Comments` (editors' notes signed with staff initials), the edit dates,
the database row ids (`OBJECTID`, `GlobalID`) and the Web Mercator copy of the
point.

## What the reference holds

`community_id` (the DCRA GUID, the same `community_id` the AEA inventory
carries), `community_name`, `community_type` (2nd Class City, CDP, Locality,
Census Area, …), `area_type` (Community 318 / Place of Interest 169 / State 2),
`is_active` (5 inactive: Valdez-Cordova and Petersburg Census Areas, North
Lakes, South Lakes, Adak Station), `start_date`, `end_date`, `lon`, `lat`,
`x_3338`, `y_3338`, `in_overview`, and from the Overview `overview_name`,
`incorporation`, `borough_census_area`, `population`, `population_year`,
`tribe`, `incorporation_year`.

Facts found while building it (2026-11-16):

- Every one of the Overview's 482 communities joins by GUID and has the same
  name in both sources. The 7 layer-only rows are the 5 inactive entries and the
  two State-type rows (`N/A` and `Alaska`), which are not communities.
- **Position = the geometry.** The layer's `x`/`y` attributes are not recomputed
  when an editor moves a point: for 11 points they disagree with the geometry
  by 1.9 to 6.9 km, and for Aleutians West Census Area by 800 km. The
  Overview's X/Y equal the geometry exactly. The reference's `lon`/`lat` are
  therefore computed from `x_3338`/`y_3338`; the snapshot keeps the attributes
  as published.
- All 269 community codes of the 2025 inventory are DCRA GUIDs in this reference.

## Refreshing

```bash
SSL_CERT_FILE=<CA bundle, only behind a TLS-inspecting proxy> python tools/input_prep/build_community_reference.py --fetch
```

then update the fetch date, row count and the sha256 here and in
`inputs/MANIFEST.md`, and review the diff of `dcra_community_reference.csv`. A
new Overview export replaces `dcra_community_overview.csv` (same file name) and
needs the same updates. `--check` (and `tests/test_community_reference.py`)
re-derives the reference from the two snapshots without the network.
