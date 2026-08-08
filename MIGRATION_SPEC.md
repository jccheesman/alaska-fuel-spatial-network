# Migration spec — one public GitHub repo for the multimodal weighted spatial network

**Goal.** Merge `alaska-fuel-spatial-network` (friction layer + edge weighting + DuckDB, Julia's
public repo) and `alaska_network_mmnet` (multimodal network build, Diego's local-only repo) into
one public repository whose structure narrates the process: (a) friction-layer build,
(b) spatial-network build, (c) join into a multimodal network with weighted edges,
(d) export to DuckDB.

**Constraints honored.** Single top-level `inputs/` for all datasets; both codebases move
mostly as-is (packages intact, scripts renamed/renumbered only); full GitHub best practice
(LICENSE, CITATION.cff, CI, one env spec, LFS, reasoned `.gitignore`); house style
(numbered `NN_verb_noun` stage scripts, producer-numbered outputs, `CLAUDE.md` lab notebook,
one-command reproduction).

Evidence base: 5-auditor + critic + 3-architect workflow run of 2026-08-05
(session `386a0a6e`, run `wf_83e1e979-93b`).

---

## 1. Diagnostic summary

### Repo A — alaska-fuel-spatial-network (friction / weighting / DuckDB)

Pipeline: GEE + ArcGIS preprocessing → corridor masks → friction stack
(`overland.tif`, `road_base.tif`, `barge_01..12.tif`, 150 m EPSG:3338 grid anchored to
`lulc.tif`) → ingest delivered network → sample friction along every edge per month
(`edge_month_weights`, 1,091,052 rows) → join $-rates from `friction_costs.py`
(`edge_costs`) → `fuel_network.duckdb`.

Strengths: friction-vs-cost separation enforced; single-source config
(`friction_config.py`, `friction_costs.py`); EXPECTED-inventory tripwire; provenance docs
(`EXTERNAL_DATA.md`, `inputs/README.md`); QA chain + one pytest module.

Key defects:
- README's 3-step run order **omits `build_corridor_masks.py`** — skipping it silently
  severs ~18 % of waterway edges in the barge surfaces.
- README advertises a `--skip-surfaces` flag that does not exist, and claims
  `load_final_network.py` "extracts the zips" — it does not (fresh-clone FileNotFoundError).
- `EXTERNAL_DATA.md` claims the 4.7 GB GEE stack and ~7 GB `friction_inputs/` are "on disk"
  — **they exist on no machine here**; the friction half is currently unrunnable locally.
- Transfer-fee inference code duplicated verbatim in `assemble_weighted_graph.py`
  (canonical home: `friction_costs.py`).
- Bridge/IceRoad "weld" disambiguation duplicated in `load_final_network.py` and
  `weight_network_edges.py` (sync-by-convention).
- `hub_facility_map` probed and stubbed (`backfill_facility_edges` NotImplementedError) but
  has **no writer and no source data anywhere** — routing layer is externally blocked.
- No LICENSE, no CITATION.cff, no CI, no single reproduce command.

### Repo B — alaska_network_mmnet (network build)

Pipeline: `normalize_raw` → `prep_waterway` → `prep_airways` → mmnet engine stages
01 consolidate → 01b tag → 02 hubs → 03 build (R sfnetworks noding + Python multimodal
assembly: hub snap, transfers, welds/bridges, connect-to-giant) → 04 join-to-giant →
`export_final_shapefile.py` → `final_network/network_joined_{nodes,edges}.shp`
(82,300 nodes / 90,921 edges / 384 hubs / 21 components / 99.65 % giant).

Strengths: region-as-data design (`profile.yaml` single config surface); `run_all.sh`
one-command driver; conventional-commit history; tracked `research/` sandboxes with
FINDINGS.md (house-style decision records); pydantic-validated config; R-oracle contract.

Key defects:
- **No git remote** — 1.3 GB of work, including the only regeneration path for the delivered
  network, exists on one machine.
- Unrunnable from a fresh clone: `data/raw/**` gitignored with **zero download URLs**
  anywhere tracked.
- Stale air-data story: README/ARCHITECTURE describe retired `air_flight_paths_od.csv` +
  global `airports.csv`; the real tracked inputs (`flight_paths_combined.csv`,
  `airports_ak_dotpf.csv`) are mentioned nowhere; `extract_od_table.py` is dead;
  `prep_waterway.py` missing from the documented run order.
- Committed notebooks bake `/home/diegoarias/...` absolute paths.
- `run_all.sh` depends on `explain/verify_north_slope.py` inside a folder whose README says
  "rm -rf when done".
- Export to `final_network/` is manual, not in `run_all.sh`, and never documents its consumer.

### Cross-repo findings (the merge drivers)

1. **Three diverging `mmnet` copies.** Oldest: `alaska_network_mmnet/mmnet` — the copy that
   **built the delivered network** (pip-installed, netweave-era). Middle:
   `alaska_network_mmnet/mmnet-toolkit/mmnet` (drives the TAPS sibling study). Newest =
   **canonical**: `alaska-fuel-spatial-network/mmnet-toolkit/mmnet` — carries 4 strict fixes
   (assemble.py `roads.reset_index(drop=True)` mis-snap fix; scoped warnings; py<3.10 typing;
   nullable-string names). Both pyprojects claim `mmnet 0.1.0`.
2. **The delivered network was built with pre-fix code.** Freeze it (checksummed, provenance
   note) and the `edge_id = shapefile row order` + EXPECTED-inventory contracts stay valid;
   rebuild with the fixed engine and counts may change, invalidating every edge_id-keyed
   table. This is an owner decision (§6).
3. **Handoff is in sync today**: repo A's `final_network/*.zip` members are md5-identical to
   repo B's shapefiles (exported 2026-07-20). The copy/zip step is scripted nowhere.
4. **False alarm resolved**: the two `Utilities_Bulk_Fuel_Inventory.csv` copies differ only
   in line endings (CRLF/BOM vs LF) — same 1,901-row AEA snapshot. Normalize to LF once.
5. **External coupling**: `alaska_network_pipeline_mmnet` (TAPS study) editable-installs
   `mmnet` from an **absolute path** into `alaska_network_mmnet/mmnet-toolkit` and diffs
   `../alaska_network_mmnet/profile.yaml`. Do not delete/move the old repo-B tree until TAPS
   is repointed.
6. **Ownership**: repo A history is entirely Julia Cheesman's (`github.com/jccheesman`);
   repo B entirely Diego's. Publishing account, attribution, and CITATION.cff author order
   need a joint decision.
7. Committed zips carry junk (`__MACOSX/`, `.DS_Store`, a `.pyc`, a
   `.claude/settings.local.json` — inspected, no secrets). Repo A `.git` is already 82 MB
   from plain-blob zips; use LFS for all new/moved zips.

---

## 2. Target architecture

Name suggestion: **`alaska-fuel-multimodal-network`** (GitHub redirects the old URL if the
existing repo is renamed; keep the old name if the manuscript already cites it — §6).

```
alaska-fuel-multimodal-network/
├── README.md                      # the four-act narrative (01→04), quickstart, badges, paper link
├── LICENSE                        # NEW — code license; data terms live in inputs/README.md
├── CITATION.cff                   # NEW — paper + software metadata (needs title/DOI/authors)
├── CLAUDE.md                      # NEW — lab notebook: | Script | Does | Outputs | Knobs | Finding |
├── EXTERNAL_DATA.md               # rewritten: committed vs regenerable-only (stale claims dropped)
├── pyproject.toml                 # ONE env spec: packages mmnet + friction_surface (src-layout)
├── uv.lock                        # pinned lockfile (replaces 4 fragmented dep specs)
├── run_all.sh                     # one-command reproduction; each stage gated with a clear
│                                  #   "regenerate via X" message when its inputs are absent
├── .gitignore                     # merged regimes, reason comment per block
├── .gitattributes                 # LFS: inputs/**/*.zip, final_network/*.zip
├── .github/workflows/ci.yml      # uv sync + ruff + pytest + validate_profile
│                                  #   + workflow-03 dry-run ingest smoke from committed zips
├── .claude/skills/                # 6 playbooks (4 friction + 2 network), paths repointed
│
├── inputs/                        # ← constraint 2: EVERY input dataset, one home
│   ├── README.md                  # provenance + download URL per dataset (covers repo B at last)
│   ├── MANIFEST.md                # sha256 of committed files + expected hashes for fetched data
│   ├── bulk_fuel_data.zip         # LFS; repacked clean; facilities CSV LF-normalized (one snapshot)
│   ├── data_for_network_build.zip # LFS; repacked clean (junk stripped)
│   ├── region_and_census_data.zip # LFS
│   ├── network_raw.zip            # NEW, LFS — repo B's data/raw (AKDOT, GRIP4, NWN, TIGER,
│   │                              #   ports, ice roads, facilities) — pending license check (§6)
│   ├── air/                       # tracked flat CSVs: flight_paths_combined, airports_ak_dotpf
│   ├── gee_exports/               # GITIGNORED — 4.7 GB AK_Stack_150m.zip, regenerate in GEE
│   └── friction_rasters/          # GITIGNORED — ~7 GB (was friction_surface/friction_inputs/)
│
├── src/                           # installable library code (constraint 3: moved intact)
│   ├── mmnet/                     # THE canonical engine = repo A's toolkit copy (4 bugfixes);
│   │   ├── …, steps/, r_oracle/   #   the other two copies are DELETED
│   └── friction_surface/          # repo A's package unchanged except friction_paths.py repoint
│       ├── friction_config.py     # friction knobs — single source of truth
│       ├── friction_costs.py      # every dollar — now the ONLY fee-inference copy
│       ├── …, friction_preprocessing/, qa/
│
├── workflows/                     # the narrative spine — thin numbered drivers, logic in src/
│   ├── 01_friction_build/         # act (a)
│   │   ├── README.md              # run order INCLUDING the corridor-mask step
│   │   ├── 00_preflight_inputs.py         → grid gates
│   │   ├── 01_build_corridor_masks.py     → outputs/01_…/waterway_mask_150m.tif
│   │   ├── 02_build_friction_stack.py     → outputs/01_…/friction_stack/ (14 tifs)
│   │   ├── 03_qa_friction_stack.py        → 14-file contract, ice gating, value floor
│   │   └── viz/                   # friction figure generators
│   ├── 02_network_build/          # act (b)
│   │   ├── README.md              # full run order incl. prep_waterway; names its consumer
│   │   ├── profile.yaml           # THE network config surface (single canonical copy)
│   │   ├── 00_normalize_raw.py … 03_fetch_basemap.py
│   │   ├── 04_build_network.py            → mmnet.run_pipeline (stages 01→04 + reports)
│   │   ├── 05_verify_north_slope.py       # assertion gate, rescued from explain/
│   │   ├── 06_export_final_network.py     → final_network/*.zip + sha256 manifest
│   │   └── viz/                   # QGIS + network figure exports
│   ├── 03_multimodal_join/        # act (c)
│   │   ├── README.md              # contracts: edge_id = row order; EXPECTED inventory;
│   │   │                          #   strict any-NoData ⇒ impassable
│   │   ├── 01_extract_network_handoff.py  # NEW ~20 lines (fixes fresh-clone failure)
│   │   ├── 02_load_final_network.py       → network_nodes / network_edges
│   │   ├── 03_weight_network_edges.py     → edge_month_weights (consumes stage-02 edge_class)
│   │   └── 04_assemble_weighted_graph.py  → edge_costs + nx.MultiGraph
│   │                                      #   (fee duplicate deleted; imports friction_costs)
│   └── 04_duckdb_export/          # act (d)
│       ├── README.md              # full 4-table schema; hub_facility_map = documented future work
│       ├── 01_run_validation_queries.py   # monthly passability by mode
│       └── 02_inspect_schema.py           # ad-hoc inspector
│
├── final_network/                 # frozen network-of-record: the 02→03 handoff
│   ├── README.md                  # field dictionary + inventory + sha256 + PRE-FIX provenance note
│   └── network_joined_{nodes,edges}.zip   # LFS; member shapefiles byte-preserved (edge_id contract)
│
├── data/                          # GITIGNORED intermediates of workflow 02 (interim/processed/basemap)
├── outputs/                       # gitignored regenerables + committed deliverables
│   ├── README.md                  # tracked contract: File | Producer stage | Content
│   ├── 01_friction_build/  02_network_build/  fuel_network.duckdb   # gitignored, reasons given
│   ├── figures/  final_network_plots/  tables/  analysis/           # committed publication artifacts
├── tests/                         # test_friction_surface.py + room for mmnet smokes
├── docs/                          # ARCHITECTURE.md (fixed), DATA_CONTRACTS.md (NEW, all
│                                  #   inter-stage contracts on one page), API.md, JETSTREAM.md
├── research/                      # repo B's 8 decision-record sandboxes + NEW index README
├── supplementary/                 # cost-derivations, cost-verification, sensitivity (from A)
└── tools/                         # extract_inputs.py, build_notebooks.py (relative root),
                                   #   gen_api_docs.py, query helpers
```

Design decisions and why:
- **`src/` + `workflows/`** wins over flat scripts or two preserved islands: packages move
  intact (constraint 3) while the four numbered workflow dirs narrate the process
  (constraint 1) and give each act its own README, config surface, and run order — the
  "better combined workflow".
- **Canonical mmnet = repo A's toolkit copy** (newest, 4 fixes). The delivered network stays
  frozen with an explicit built-pre-fix note; the engine and the deliverable are allowed to
  disagree, loudly, until the owners decide (§6).
- **`final_network/` becomes an internal pipeline edge** — workflow 02 writes it (now with
  zips + sha256), workflow 03 extracts and ingests it. Committed zips let users run acts
  (c)–(d) without acts (a)–(b).
- **DuckDB is written where the code already writes it** (acts c stages) — act (d) validates
  and documents the deliverable rather than moving the writer, minimizing code change.

## 3. Required code edits (exhaustive — everything else is `git mv`)

1. `src/friction_surface/friction_paths.py` — PROJECT_ROOT for src-layout; RASTER_DIR →
   `inputs/friction_rasters`, stack/mask dirs → `outputs/01_friction_build/`; DB →
   `outputs/fuel_network.duckdb`; **remove the import-time `os.chdir`**; add a unit test
   asserting resolved paths from a fake CWD.
2. `DB_PATH` in the three join scripts + `plot_weighted_network.py` →
   `outputs/fuel_network.duckdb`, anchored absolutely from repo root.
3. `04_assemble_weighted_graph.py` — delete the duplicated FEE_MODE/`_lookup_fee`/
   `infer_transfer_fees` block; import from `friction_surface.friction_costs`.
4. `03_weight_network_edges.py` — read `edge_class` from the DB instead of re-deriving the
   IceRoad/weld rule from the raw shapefile.
5. `06_export_final_network.py` — drop the sys.path hack; write zips + sha256 manifest;
   output to top-level `final_network/`.
6. `tools/build_notebooks.py` — relative project root (kills baked absolute paths); drop the
   committed `.ipynb` (regenerable) or regenerate + commit per house convention (§6).
7. `01_extract_network_handoff.py` + `tools/extract_inputs.py` — new thin extract helpers.
8. `run_all.sh` (root) — new orchestrator chaining the four workflow `run_all.sh`/drivers
   with input gates.

## 4. Migration plan (ordered)

1. **Safety first**: give `alaska_network_mmnet` a remote (private GitHub) and push — its
   history and hand-digitized data currently exist on one disk. `git gc` its 44 MB of loose
   objects.
2. Settle §6 decisions 1–4 (identity, license, paper metadata, freeze-vs-rebuild).
3. Create the merged repo (recommended: new repo, import both histories via subtree merges
   with `--allow-unrelated-histories` so both authors' commits survive; archive the old
   public repo with a pointer README, or rename it — GitHub redirects).
4. `.gitattributes` (LFS patterns) and merged `.gitignore` **before any `git add`**
   (repo B's on-disk junk — `.venv`, egg-info, `__pycache__`, `__MACOSX`, `.qgz` — is one
   bad `git add .` from the public repo).
5. Move packages: canonical mmnet → `src/mmnet`; `friction_surface/` → `src/`; delete the
   two stale mmnet copies and both `mmnet-toolkit` shells; one `pyproject.toml` + `uv.lock`.
6. Move and renumber stage scripts into `workflows/` per the tree; make the edits of §3;
   move-only commits separate from edit commits so rename detection and blame survive.
7. Consolidate `inputs/`: repack the three existing zips (strip junk, LF-normalize the
   facilities CSV); build `network_raw.zip` from repo B's `data/raw` (pending license check);
   write `MANIFEST.md` with sha256s. **Preserve `final_network` zip members byte-identical**
   (verify md5s — the edge_id contract depends on them).
8. Docs pass, fixing every audited stale claim: corridor-mask step into the canonical run
   order; phantom `--skip-surfaces` removed; air-data story rewritten around
   `flight_paths_combined.csv`; `prep_waterway` documented; handoff producer/consumer named;
   `EXTERNAL_DATA.md` truthful about what exists where; `DATA_CONTRACTS.md` created.
9. Delete dead weight: `extract_od_table.py`, the `hub_facility_map` probe + stub (or mark
   future-work per §6), `example_skills/`, stale `explain/` duplication (gate script moves
   to workflow 02).
10. New top-level files: README, LICENSE, CITATION.cff, CLAUDE.md lab notebook (one row per
    numbered script, Finding column, Caution row for the pre-fix network-of-record).
11. CI: uv sync + ruff + pytest + `validate_profile` + the one data-backed smoke committed
    zips permit (extract handoff → `02_load_final_network --dry-run` validating the
    82,300/90,921 inventory).
12. Verification gates before first push: fresh-clone smoke of acts (c)–(d) end-to-end;
    `grep -r` sweep for old paths (`friction_surface/friction_inputs`, `mmnet-toolkit`,
    `scripts/run_all`, absolute `/home/diegoarias`); pytest green; notebooks (if kept)
    execute headlessly.
13. Repoint the TAPS study (`alaska_network_pipeline_mmnet`) to install mmnet from the
    merged repo; only then archive the old repo-B working tree.
14. Full friction rebuild on the machine that regenerates the GEE stack before tagging a
    release — the friction half cannot be end-to-end verified here (§1).

## 5. Best-practice checklist the merged repo satisfies

LICENSE + data-terms note · CITATION.cff · narrative README with badges and one-command
quickstart · single pinned env (uv) · CI on every push · LFS for binary data ·
reason-commented `.gitignore` · per-dataset provenance with URLs and sha256 manifest ·
no absolute paths, no committed junk, no filename spaces · numbered stages with
producer-numbered outputs · single config surface per workflow · documented inter-stage
contracts · CLAUDE.md lab notebook · tests + smoke of the deliverable · frozen deliverable
checksummed with honest provenance.

## 6. Open decisions (owners only — nothing here blocks starting steps 1, 5–9)

1. **Publishing identity**: which account/org hosts the merged repo; archive vs rename the
   existing `jccheesman/alaska-fuel-spatial-network`; CITATION.cff author order. Requires
   Julia's sign-off.
2. **License** (MIT/BSD-3/Apache-2) **and data redistribution**: confirm AEA inventory,
   AKDOT roads, GRIP4 (CC-BY), USACE NWN terms permit committing `network_raw.zip`;
   otherwise it becomes a fetch script + hash manifest.
3. **Paper metadata**: Data-in-Brief title/authors/DOI — appears nowhere in either repo.
4. **Freeze or rebuild**: keep the pre-fix network-of-record (contracts stay valid) or
   rebuild with the fixed engine and re-derive EXPECTED counts, `edge_month_weights`,
   `edge_costs`. A rebuild also quantifies the mis-snap fix's real impact.
5. **Repo name**: keep (already cited?) vs `alaska-fuel-multimodal-network`.
6. `hub_facility_map` stub: delete from the public release or document as the routing-layer
   extension point (the 384-hub↔1,838-facility mapping exists nowhere on this machine).
7. Scope: do `research/`, `explain/` narratives, notebooks, and the Jetstream guide ship
   publicly (recommended: research yes, explain no, notebooks regenerated-or-dropped,
   Jetstream pruned) — or move to a private archive?
8. Long-term home of the big rasters (4.7 GB GEE stack, ~7 GB friction inputs): Zenodo/
   ScholarWorks deposit with DOI vs regenerate-only instructions.
9. `mmnet`'s future: stays vendored in `src/` (proposed) or graduates to its own
   repo/PyPI that this repo and the TAPS study pin.
