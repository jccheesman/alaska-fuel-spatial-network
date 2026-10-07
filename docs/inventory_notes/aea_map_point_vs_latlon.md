# aea_map_point_vs_latlon

**Looks like:** the publisher's map geometry (`X`/`Y`, EPSG:3338 → `map_x`/`map_y`) disagrees with the
`ASTFacilityLatitude`/`Longitude` columns by kilometres (Kodiak 328 km, Coldfoot 803 km in 2022;
Hooper Bay, Noorvik, Point Lay after AEA's Dec-2025 edits).

**Why:** AEA corrects records by moving the map point; the lat/lon attribute columns — the ones both
pipelines read — are not updated. So an upstream "fix" is invisible to the build unless the map point
is consulted. The map point is usually the corrected one.

**Handled by:** `04_detect.py::map_point_disagrees` (suggests the map point as the fix); the ingest
diff reports map-point moves beyond the ~1 m re-projection jitter. Ask AEA to update lat/lon when
they move a map point.
