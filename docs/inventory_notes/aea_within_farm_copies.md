# aea_within_farm_copies

**Looks like:** 2–4 rows on one farm id with the same community, the same `Total_Capacity` and the
same fuel breakdown (Birch Creek farm 139: four identical 7,800 gal diesel rows).

**Why:** the farm total is repeated on every row of the farm. Summing rows over-counts capacity;
the farm's own `Total_Capacity` counted once is correct. AEA deleted 66 such copies in its 2025
release (plus 5 copies on shared-id farms).

**Handled by:** `04_detect.py::within_farm_copies` (low severity, information for capacity sums);
the data repo's 50 m consolidation already takes max() per site so hub capacities are right when
the copies share an exact point.
