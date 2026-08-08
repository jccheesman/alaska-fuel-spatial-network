# TEST LOG — end-to-end verification runs

## 2026-08-06 — mode-A end-to-end (Julia's machine, conda `akful`, macOS)

First full run of the merged repo on real data. Mode A = everything rebuilt
fresh EXCEPT the frozen network-of-record stays the ingest source.

### Data staging

- Canonical wide-grid rasters located on Julia's machine (the audit's
  "exists nowhere" concern is resolved): wide `lulc`/`slope`, aligned
  `permafrost`, padded `sea_ice` + `river_ice` → `inputs/friction_rasters/`.
  The June narrow-grid GEE export is archived (`gee_exports/` zip +
  `small_grid/`); grid history documented below.
- Raw network tree supplied as `inputs/network_raw.zip` (exact SPEC layout;
  redistribution decision still pending — LOCAL ONLY until §6.2 clears).

### Gates and results

| Gate | Result |
|---|---|
| `00_preflight_inputs` | ALL PASS on the 28,001×16,567 wide grid, incl. Adak/Atka far-west coverage |
| Workflow 01 (mask → stack → QA) | PASS — 14-file contract, ice gating, value floor |
| 03/02 ingest tripwire | PASS — exact frozen inventory (82,300 / 90,921 / 384 / 21 / 99.65%) |
| edge_class | 1,331 Weld + 36 IceRoadConnector, consumed from DB by stage 03 |
| 03/03 weighting QA | Road avg_friction ∈ [1.000, 2.625], 0 impassable; IceRoad in-season 3,852/3,852 passable, out-of-season 0; barge passability seasonal curve (Feb–Mar ≈ 0.000, Jul–Sep ≈ 0.999–1.000) |
| 03/04 costing QA | Transfer fee inventory exactly 205×$0.24 + 8×$0.011; zero cost-free passable edge-months |
| Tables | `edge_month_weights` + `edge_costs` = 1,091,052 rows each; 4-table schema confirmed; giant = 82,012 nodes |
| Workflow 04 validation queries | Sensible passability by mode/month (IceRoad Jan–Mar only) |

### Waterway passability by month (reference values, this build)

Jan 0.130 · Feb 0.000 · Mar 0.000 · Apr 0.042 · May 0.878 · Jun 0.971 ·
Jul 0.999 · Aug 1.000 · Sep 0.999 · Oct 0.584 · Nov 0.126 · Dec 0.014

### Outstanding

- **Workflow 02 (mmnet build): NOT yet verified.** Stage-04 gpkg absent at
  export time — suspected missing R oracle deps (Rscript + sf/sfnetworks/
  tidygraph/dplyr). The export step correctly refused, so the frozen
  network-of-record was never touched.
- Bugs found BY this test run and fixed in-branch: stale
  `check_grid_exports.DEFAULT_INPUTS` path; preflight driver gating on
  rc=1; SPEC air paths; `extract_inputs` network_raw rooting;
  (`pad_river_ice_to_grid` still carries pre-merge paths — unused this run
  because the padded set already existed; repoint before the next GEE
  re-export).

### Grid history (for future readers)

Three nested footprints: (1) river ice is produced on its own interior
ArcGIS window (no freezing rivers in the Aleutians/panhandle) and PADDED
onto the statewide grid; (2) the original statewide grid (18,531 cols,
X₀=−1,120,050) missed the far-western Aleutians; (3) the canonical extended
grid (28,001 cols, X₀=−2,130,150) fixed that — the Adak/Atka coverage check
in preflight exists to catch generation-2 data masquerading as canonical.
