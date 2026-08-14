# TEST LOG — end-to-end verification runs

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
