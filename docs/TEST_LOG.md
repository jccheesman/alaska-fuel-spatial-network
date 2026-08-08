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

## 2026-08-07 — full four-stage run on Diego's machine (Linux, Python 3.13)

First end-to-end verification of **all four** workflows on one machine, and
the first verification of workflow 02 (the 2026-08-06 run could not: the R
oracle deps were missing there).

Environment: `uv venv && uv sync && uv pip install -e .` — CPython 3.13.3,
rasterio 1.5.0, Rscript with sf/sfnetworks/tidygraph/dplyr present.

| Stage | Result | Notes |
|---|---|---|
| `pytest` | 16 passed | 37 NumPy 2.5 deprecation warnings (`Setting the shape on a NumPy array`) — cosmetic |
| `ruff check .` | clean | after fixing one pre-existing F541 in the run-friction-pipeline skill |
| 01 friction build | PASS, 274 s | 24 surfaces / 14 files; barge ice gating Jul−Jan = +43,974,500 valid px; overland floor OK; Bethel reachable |
| 02 network build | PASS | 82,300 nodes / 90,876 edges; giant 99.7%; all six North Slope gates PASS. **Export step 7 deliberately not run** |
| 03 multimodal join | PASS, 46 s | `edge_month_weights` + `edge_costs` = 1,091,052 rows each; Road friction ∈ [1.0, 2.625]; IceRoad Jan–Mar only; fees 205×0.24 + 8×0.011; zero cost-free passable edge-months |
| 04 duckdb export | PASS | 4 tables; 384 hubs; 82,012/82,300 in giant; edge inventory matches the `EXPECTED` tripwire |

`final_network/*.zip` verified byte-identical (sha256) before and after the
whole run — the network-of-record was never touched.

### Confirmed: the engine/deliverable divergence is real and measurable

Rebuilding stage 02 with the fixed `src/mmnet` yields **90,876 edges** against
the frozen deliverable's **90,921** — a 45-edge gap. The pre-fix/post-fix
disagreement documented in `CLAUDE.md` is therefore not hypothetical; it has a
number now. Freeze-vs-rebuild remains an open owner decision.

### Operational notes for the next runner

- Every `run_all.sh` invokes bare `python3`, not the venv interpreter.
  Activate the venv (or prepend `.venv/bin` to PATH) or the stages will run
  against system Python and fail on imports.
- `workflows/02_network_build/run_all.sh` pipes every step through
  `|| true`, so the script exits 0 even when a step fails. Read the log; do
  not trust its exit code.
- That same script's **step 7 overwrites `final_network/`**. To test the
  build without touching the network-of-record, run `04_build_network.py`
  and `05_verify_north_slope.py` directly, as this run did.
