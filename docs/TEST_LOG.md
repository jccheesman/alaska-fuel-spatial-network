# TEST LOG — end-to-end verification runs

## 2026-11-18 — waterway-network-updates branch: full rebuild from committed state

Fresh workflow-02 run (prep regenerated from scratch: `data/interim` manifest
removed first) on branch `waterway-network-updates`: the owner-curated waterway
as the network source, the 26-feature manual layer (19 Barge lines), and the
new QA checks wired into the driver. Everything the branch will change at the
next export, verified before exporting anything.

### Gates and results

| Gate | Result |
|---|---|
| `qa/00_check_manual_barge` (July + marine-only) | PASS (1 accepted exception: Skwentna, river line) |
| `01_prep_waterway` (curated source) | 315/320 lines, 30,617 km, 4 raw components |
| mmnet build + welds | PASS — 13 manual-barge endpoints welded |
| `05_verify_north_slope` | PASS (all five checks; waterway 100% connected) |
| `qa/06_barge_hub_access` | PASS (18 known exceptions, 0 new) |
| Stage 03 → 04 | 16 components → 4, giant 100.0% |
| Full pytest suite | 210 passed, 1 skipped |

Deterministic: identical counts to the two prior builds of the same inputs.

### Expected changes vs the frozen 2026-11-16 network-of-record (at the next export)

| Quantity | 2026-11-16 (frozen) | This build | Δ |
|---|---|---|---|
| Nodes | 84,094 | 84,110 | +16 |
| Edges (joined) | 93,046 | 93,061 | +15 |
| Hubs | 328 | 328 | 0 |
| Components (joined) | 4 | 4 | 0 |
| Waterway | 34,178 | 34,179 | +1 (curated lines re-segment; 17 manual lines added) |
| BargeRoadTransfer | 286 | 298 | +12 (new barge-hub landings) |
| BargeAirTransfer | 2 | 4 | +2 (Kongiganak, Kwigillingok land at shared airport-road nodes) |
| BargeConnector | 0 | 1 | +1 (new type: a barge-barge shore weld) |
| RoadConnector | 1,498 | 1,497 | −1 |
| Road / IceRoad / Air / other transfers | — | — | unchanged |

Newly barge-reachable at the export: the 8 harbour-closure ports (Kodiak,
Unalaska, Akutan, Port Lions, Saint George, Saint Paul, Point Hope, Kaktovik —
all approaches sample 0 NoData on the EXISTING barge surface) and the 17 hubs
served by manual lines. The export additionally requires: new `EXPECTED` in
`fuel_network/load.py` (incl. the `BargeConnector` type), full workflow-03
rerun, zips + checksums, and clearing 36 rows of
`inputs/network_qc/accepted_barge_exceptions.csv`.


## 2026-08-06 — mode-A end-to-end (owner's machine, conda `akful`, macOS)

First full run of the merged repo on real data. Mode A = everything rebuilt
fresh EXCEPT the frozen network-of-record stays the ingest source.

### Data staging

- Canonical wide-grid rasters located on the owner's machine (the audit's
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

## 2026-08-07 — full four-stage run on a second machine (Linux, Python 3.13)

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

Rebuilding stage 02 with the fixed `source_scripts/mmnet` yields **90,876 edges** against
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

### 2026-08-07 (same day) — the three operational notes above are now fixed

The gotchas recorded in the previous entry were defects, not facts of life.
All three are closed:

- **Bare `python3`** — the four stage drivers and the root `run_all.sh` now
  source `workflows/_lib.sh` and call `resolve_python`, which prefers an
  active `$VIRTUAL_ENV`, then `.venv/bin/python`, and only then falls back to
  `python3` *with a warning*. No stage can silently run against system Python.
- **`|| true` masking failures** — stage 02's eleven `| grep … || true` steps
  are replaced by `run_step`, which filters the same noise but preserves the
  real exit status and aborts the stage on failure. Verified by injecting a
  step that exits 7: the driver now exits 7 instead of 0.
- **Step 7 overwriting the network-of-record** — the export is now opt-in
  (`EXPORT_FINAL_NETWORK=1`). The default run prints what a re-export would
  invalidate and skips it.

Two contracts were added on top:

- A stage that is missing a documented input exits `GATE_EXIT` (3) and the
  top-level `run_all.sh` reports it as *skipped*; any other non-zero exit is
  reported as *failed* and makes `run_all.sh` itself exit non-zero. Missing
  data and a broken build no longer look identical.
- CI hashes `final_network/*.zip` against the expected sha256 on every run, so
  an accidental re-export of the network-of-record fails the build rather than
  quietly redefining `edge_id`.

**`tests/test_mmnet.py` added — 16 tests, suite now 32.** `mmnet` (3,280
lines) previously had none. The new tests pin the engine's own documented
promises: connector determinism under row permutation (shapefile read order
must not change which edges get welded), tolerance gating on welds and
giant-joins, shore-landing vs weld labelling (stage 03 maps those onto cost
rates), hub supplier/receiver classification, the NetworkTables↔networkx
round-trip, and that the shipped `profile.yaml` still validates.

## 2026-08-08 — release packaging (T2–T4b of the work brief)

All edits below are documentation, metadata, test config, and a new
cross-platform driver; no pipeline stage was re-run (the cheap verification
tier gates every change: 32 tests green, ruff clean, `bash -n` on all five
drivers, dry-run ingest, validation queries, and the two `final_network`
zip sha256s unchanged against the CI pins).

### Publication metadata (T2)

- `CITATION.cff` added (CFF 1.2.0): authors Julia Cheesman and Diego Arias
  Arana (LICENSE order), MIT, type software, repository-code
  `github.com/jccheesman/alaska-fuel-spatial-network`; commented
  `preferred-citation` placeholder for the future Data-in-Brief DOI (not
  invented). `CONTRIBUTING.md` added: reproduce via README Quickstart +
  EXTERNAL_DATA.md; the frozen network-of-record and the cost/friction
  constants change only by owner decision.

### Known code smells closed (T3)

- Stale `friction_inputs` prose (the pre-merge name of
  `inputs/friction_rasters/`) fixed in docstrings/comments across
  `friction_preprocessing/{__init__,align_permafrost,pad_river_ice_to_grid,
  pad_sea_ice_to_grid}.py`, `check_grid_exports.py`, and
  `qa/qa_river_ice_thresholds.py`. Prose only — no logic touched. Three
  LIVE-CODE constants still name the old layout and were deliberately left
  for an owner decision: `workflows/01_friction_build/viz/plot_sea_ice_padding.py:32`,
  `source_scripts/friction_surface/qa/compare_lulc_grids.py:28`,
  `source_scripts/friction_surface/qa/qa_river_ice_thresholds.py:40`.
- The 37 "Setting the shape on a NumPy array" DeprecationWarnings DID
  reproduce under the current lock (Python 3.13.3 / NumPy 2.5.1).
  `-W error::DeprecationWarning` traced them to rasterio's
  `DatasetReader.read()` (`rasterio/_io.pyx`), not repo code. One
  message-anchored `filterwarnings` entry added under
  `[tool.pytest.ini_options]` (no module qualifier — NumPy's stacklevel
  attributes the warning to the *calling* module, so only the exact message
  can target it). Suite warnings dropped 51 → 14; the shape warning is gone.

### Notebook narration (T4)

- CLAUDE.md's staleness warning for `tools/build_notebooks.py` was mostly
  outdated: the old flat-repo tokens are gone. What remained was a root-level
  `profile.yaml` narration (now points at
  `workflows/02_network_build/profile.yaml`) and the legacy `NETWEAVE_*` env
  names in the SETUP cell (now canonical `MMNET_*`; config.py keeps the old
  names as fallback). `output/` narration left alone — `mmnet.io_writers`
  genuinely writes `project_root()/"output"`. CLAUDE.md caution row updated.

### Cross-platform driver + CI matrix (T4b)

- `run_all.py` added at the repo root: pure-stdlib Windows twin of
  `run_all.sh`, mirroring `_lib.sh`'s three contracts (venv-first interpreter
  resolution incl. `Scripts\python.exe`; `run_step` with merged/buffered
  output, stage-02 noise filter, and verbatim exit-status propagation;
  `GATE_EXIT=3` skip-vs-fail summary, byte-identical wording). Supports
  `--only <stage>` and `--profile`. The bash drivers are untouched.
- Portability audit: `shell=True|os.system|/tmp` grep over
  source_scripts/workflows/tools is clean; the one fix was `source_scripts/mmnet/build.py`
  resolving `Rscript` via `shutil.which` with a clear install message when
  absent (the R oracle is a documented every-OS requirement, not a Windows
  bug).
- CI split into a 3-OS matrix (`ubuntu/macos/windows`: install, ruff, pytest,
  profile validation, extract+dry-run smoke, network-of-record hash) and an
  ubuntu-only `bash-contracts` job (shell syntax, run-script contract, and a
  new **driver parity** step: both drivers run in pristine clones and must
  report the same summary and exit code).
- **Local parity verified 2026-08-08 (Linux)**: two fresh clones of this
  repo; `bash run_all.sh` and `python run_all.py` both reported
  `skipped: 01_friction_build 02_network_build 03_multimodal_join`,
  `failed: none`, exit 0 (stage 04's validation queries pass on the partial
  ingest-only duckdb). Full logs differ only in the clone path and one
  child script's nondeterministic dict-print ordering. **Windows/macOS proof
  is the first CI matrix run on the new remote** — if a lane fails, fix
  forward; do not delete the matrix.

## 2026-08-20 — river-ice marine leak: diagnosis, fix, verification

A defect found by inspecting winter routes, not by a failing test: **in
February, 0 of 501,684 waterway cells statewide were navigable** — the Gulf of
Alaska, the Inside Passage and Kodiak included, against year-round
twice-weekly commercial barge service on those exact routes.

### Root cause

`friction_surface.extend_ice_nearest` filled river ice onto uncovered cells
from the nearest covered cell with **no distance bound and no river/marine
distinction**, targeting the whole waterway corridor. In winter every covered
cell is frozen, so the entire marine network inherited a frozen p_ice. A
second, independent path existed in the product itself: four NHDArea
`ftype 364` Lake/Pond polygons put 396 marine cells inside the river-ice
domain, so `river_ice_MM.tif` carried real interpolated values over Dry
Strait, Kuskokwim Bay, Knik Arm and Chatham Strait.

Evidence that isolated it: off-network open water beside the blocked network
cells was navigable in the same month, so sea ice could not be the cause.
February probes — open Gulf 100% open, but 0 of 714 network cells off Seward,
0 of 951 at Ketchikan, 0 of 321 in the Inside Passage.

### Fix — three tiers, both barriers load-bearing

| tier | source | cells | share |
|---|---|---|---|
| 1 | Brown IDW value | 77,657 | 89.5% |
| 2 | nearest covered cell within `RIVER_ICE_FILL_MAX_KM` = 25 km | 4,734 | 5.5% |
| 3 | median of the `RIVER_ICE_FALLBACK_K` = 200 nearest covered cells | 4,398 | 5.1% |

River ice is clipped to `waterway_river_mask_150m.tif` (24 reviewed NWN
segments, 86,789 cells, 17.3% of the corridor) in BOTH the fill target and
the gate. The gate clip is not redundant: it is what catches the 396 marine
cells contaminated at source.

The 25 km cap exists because the unbounded fill was two behaviours wearing one
name — Yukon cells borrowed from 1.5 km away (interpolation), Ugashik from
149.6 km and "Dahl Creek" from 227.5 km (fabrication across watersheds).

### Gates and results

| Gate | Result |
|---|---|
| River mask vs reviewed allowlist | PASS — 86,789 cells, 0 disagreement, strict subset of the waterway mask |
| Marine cells in the river mask | PASS — 0 |
| Marine cells blocked in the Gulf/SE, any winter month | PASS — 0 (the 3,753 still blocked are all river: Kvichak, Stikine, Susitna) |
| `check_year_round_ports` | PASS — Ketchikan, Sitka, Juneau, Petersburg, Kodiak, Seward, Valdez, Whittier navigable 12/12 |
| Seasonal control | PASS — Nome open Jun–Oct, Utqiagvik Aug–Oct, from the sea-ice climatology alone |
| Bristol Bay tier-3 rivers | PASS after the k-nearest fix — Egegik/Ugashik/Naknek closed Jan, Feb, Dec |

### Waterway passability by month (reference values, this build)

**Read the length-weighted series.** The edge-count series is dominated by the
dense interior river network: in February 33,075 short interior edges are
blocked (mean centroid 64.46N 154.58W) against 1,024 long Gulf/SE edges
passable (57.73N 138.15W), so by count February reads 0.030 while by length it
is 0.511. The two answer different questions and only the second is
comparable to cell-level figures.

| month | by count | by length | (pre-fix, by count) |
|---|---|---|---|
| Jan | 0.141 | 0.530 | 0.130 |
| Feb | 0.030 | 0.511 | 0.000 |
| Mar | 0.030 | 0.511 | 0.000 |
| Apr | 0.049 | 0.544 | 0.042 |
| May | 0.878 | 0.748 | 0.878 |
| Jun | 0.972 | 0.868 | 0.971 |
| Jul | 0.999 | 0.908 | 0.999 |
| Aug | 1.000 | 0.982 | 1.000 |
| Sep | 1.000 | 0.982 | 0.999 |
| Oct | 0.587 | 0.860 | 0.584 |
| Nov | 0.133 | 0.689 | 0.126 |
| Dec | 0.043 | 0.556 | 0.014 |

The pre-fix `Feb 0.000 / Mar 0.000` in the 2026-08-06 entry above is the
signature of this bug, not a reference value. Do not compare a fresh build
against it.

### A wrong turn worth recording

Tier 3 was first implemented as a **latitude band** (median of covered cells
within ±0.75°), on the reasoning that Alaska's freeze gradient is
north-south. It is not — the maritime/continental gradient is at least as
strong. Egegik's band contained only Taku, Stikine and a mislabelled
"Porcupine" polygon in Chatham Strait, all Southeast rainforest rivers
1,200–1,400 km east, because Kvichak (58.88N) and Nushagak (59.0N) sit just
above its ceiling. The build shipped with **Egegik navigable in January,
November and December** and Ugashik in January and November. A fallback added
to stop 227 km borrowing had reached 1,400 km instead.

Replaced with the k-nearest median. Verified source selection: Egegik now
draws 100% from Nushagak/Kvichak at 89 km, Ugashik 100% at 149 km, Dahl Creek
85% from Buckland at 228 km. Post-fix, every cell whose status changed across
the four winter months was a river cell and none were marine; changed-cell
centroids all sit at ~58N 158W.

### Outstanding

- **Kvichak opened** rather than closed under the k-nearest fallback (1,478
  cells in January, 1,113 in December). Plausible — it drains Iliamna Lake and
  large lake-fed rivers hold open water later — but unpredicted and therefore
  unverified. Local knowledge of freeze-up near Levelock or Igiugig would
  settle it cheaply.
- **"DAHL CREEK, AK"** (740 cells) runs 65.28N 166.35W → 65.51N 165.48W, in
  Port Clarence / Grantley Harbor on the Seward Peninsula — roughly 800 km
  from Dahl Creek on the Kobuk. Probably a brackish lagoon route rather than
  the creek it is named for. Currently classified river; low stakes because
  Norton Sound sea ice closes it either way.
- **"BUCKLAND RIVER"** NWN geometry sits mid-Kotzebue Sound, ~120 km from the
  real mouth; rejected from the river allowlist on those grounds.
- Marine-clip provenance: confirm `river_ice_*.tif` were regenerated after
  `build_brown_polygon_mask.py` gained the clip. Measured downstream effect if
  not: 9 cells on the Stikine.

### Artifacts

`outputs/analysis/`: `river_ice_marine_leak.png` (February classification map
+ monthly curve), `river_ice_coverage_gap.png` (the 18,478 cells outside the
IDW), `waterway_river_mask.png` (the mask with SE Alaska and Bristol Bay
insets), `brown_flowlines_and_polygons.png`,
`waterway_river_marine_classification.csv` (all 320 NWN segments),
`nwn_vs_brown_flowlines.csv` (NHD cross-check, 4 disagreements, all recall
gaps). Regenerate the first with
`diagnostics/01_friction_build/plot_river_ice_marine_leak.py`.

---

## 2026-08-21 — arcpy NN fallback truncates p_ice to 0 or 1

Found while prototyping a pure-Python port of `river_ice_full_pipeline.py`.
The port was built to answer a scoping question (can the arcpy and Python
workflows be merged?); it instead surfaced a live defect in the arcpy stage.
**Decision taken: keep both workflows for now, fix the defect in place.**
Full write-up in `docs/FINDING_eucallocation_truncation.md`.

### The defect

`process_data_month` closed with `nn_fill = EucAllocation(clamped)`.
`EucAllocation` is a *zone* tool — a float input is truncated to integer
before allocation. Every stage-3 gap cell therefore inherited **0** (any
neighbour below 1.0) or **1** (a neighbour at exactly 1.0), never the
neighbour's actual p_ice.

### Evidence, from arcpy's own two rasters

`provenance_01.tif` marks the tier-3 cells; sample `river_ice_01.tif` there:

| | |
|---|---|
| tier-3 cells, month 01 | 73,526 |
| distinct values among them | **85** |
| exactly 0.0 | 61,753 (84.0%) |
| exactly 1.0 | 10,988 (14.9%) |
| tier 1, distinct values (200k sample) | 9,921 |
| tier 2, distinct values | 46,016 |

A continuous field does not produce 85 distinct values over 73,526 cells.
The few non-0/1 values are bilinear bleed from the Step 7 alignment. This
measurement does not depend on the port at all.

### Cost, on the NWN river corridor

| | arcpy | true nearest (port) |
|---|---|---|
| tier-3 corridor cells | 4,898 | 4,898 |
| exactly 0.0 | 4,880 (99.6%) | — |
| mean p_ice | **0.0005** | **0.7780** |
| below `RIVER_ICE_THRESHOLD` (0.15) | 4,894 | 4 |

Those cells enter the friction build as tier-1 "measured" values, so nothing
downstream flags them. This is the ~7% of tier 1 that the earlier provenance
cross-tab showed arriving from the arcpy fallback.

### What validated the comparison

Port run on arcpy's **native** (pre-alignment) grid, read off
`provenance_01.tif`, so no resampling is in the loop:

| stage | agreement |
|---|---|
| river-mask membership | 99.98% — 18,802 python-only cells of 585k |
| tier assignment 1/2/3 | 99.58% of shared cells |
| tier 1 (polygon median) | mean abs diff **0.0032** |
| tier 2 (IDW: power 2, 12 pts, 50 km) | mean abs diff **0.00065** |
| tier 3 (EucAllocation) | mean abs diff **0.66**, 80% differ by >0.05 |

The IDW row is the control: a `cKDTree` reimplementation reproduces arcpy's
`Idw` to 6.5e-4. The divergence is confined to the one stage. Port kept as a
diagnostic at `diagnostics/01_friction_build/river_ice_interp.py` — **not** wired into the pipeline.

### The fix

`EucAllocation` deleted; those cells are left NoData
(`final = Con(~IsNull(mask_r), clamped)`). Nothing replaces it, because the
friction build already has a better gap-filler: `extend_ice_nearest` capped at
`RIVER_ICE_FILL_MAX_KM = 25 km` and clipped to the river mask, falling back to
`fill_by_nearest_median` (K = 200). Two fill policies collapse to one, and the
unbounded one is the one retired.

Applied to `river_ice_full_pipeline.py` 2026-08-21. **Not yet run** — needs the
ArcGIS machine. Before/after diff kept at `arcpy-eucallocation-fix.patch`.

### Predictions to check on the next ArcGIS run

- `river_ice_MM.tif` loses roughly 73k cells per winter month to NoData.
- The friction build's three-tier split moves off 89.5 / 5.5 / 5.1: tier 1
  should drop by ~4,900 corridor cells, tiers 2 and 3 absorbing them.
- Those cells go from p_ice ≈ 0 to ≈ 0.78, so **more** river cells block in
  winter, not fewer. Marine sites (Ketchikan, Juneau, Kodiak…) are unaffected;
  `check_year_round_ports` must still pass 12/12 on all eight.

### Caveats

- One month (01) only, against the June/July 2026 arcpy output and the
  pre-marine-clip 967-polygon mask — the same inputs that run consumed.
- The port's mask carries ~3% more cells than arcpy's. Attributed to
  cell-centre rasterisation differing at polygon boundaries; **not proven**.
  It does not affect the tier-3 result, which is measured inside arcpy's own
  mask.
