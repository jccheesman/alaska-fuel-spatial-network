# diagnostics/ — evidence base for the two-repo merge

Everything needed to implement the merge of `alaska-fuel-spatial-network` (friction /
weighting / DuckDB) and `alaska_network_mmnet` (multimodal network build) into one public
GitHub repo. Produced by the 2026-08-05 diagnostic workflow (9 agents: 5 auditors, 1
completeness critic, 3 independent architects; run `wf_83e1e979-93b`).

## How to use this folder with Claude Code

1. Read `../MIGRATION_SPEC.md` first — the governing document (diagnostic summary, target
   architecture, required code edits, migration plan, open decisions).
2. Settle the owner decisions in spec §6 (publishing account, license, paper metadata,
   freeze-vs-rebuild). Nothing else blocks on them, but the release does.
3. Start a Claude Code session in this repo and point it at
   `diagnostics/00_IMPLEMENTATION_PLAYBOOK.md` — a self-contained, phase-by-phase
   execution guide with verification gates.
4. During implementation, the numbered reports below are the ground truth to consult when
   a claim needs re-checking — each states exact paths, line numbers, md5s, and sizes.

## Contents

| File | What it holds |
|---|---|
| `00_IMPLEMENTATION_PLAYBOOK.md` | Phase-by-phase execution guide for Claude Code (start here to build the merged repo) |
| `01_diagnostic_friction_repo.md` | Full audit of alaska-fuel-spatial-network: pipeline stages, entry points, config surfaces, issues, notable files |
| `02_diagnostic_network_repo.md` | Full audit of alaska_network_mmnet: same structure |
| `03_data_inventory.md` | Sizes, git-tracked vs on-disk data, zip contents, cross-repo duplication (md5-verified), LFS candidates |
| `04_cross_repo_coupling.md` | The three mmnet copies and which is canonical; the final_network handoff contract (edge_id = row order); git state; DuckDB schema |
| `05_best_practices_audit.md` | GitHub best-practice + house-style gaps, ranked most-severe-first |
| `06_critic_gap_fills.md` | 14 gaps the auditors left, each resolved by direct verification (incl. the two false alarms and the TAPS coupling) |
| `10_proposal_minimal_move.md` | Architecture proposal A (not adopted) — kept for its subtree-merge git mechanics |
| `11_proposal_pipeline_first.md` | Architecture proposal B (not adopted) — kept for its producer-numbered outputs idea and code-edit enumeration |
| `12_proposal_library_workflows_ADOPTED.md` | Proposal C — the adopted basis: full annotated tree, exhaustive old→new file mapping, 18 migration steps |
| `raw/*.json` | Machine-readable originals of all of the above |

## The five facts every implementer must hold

1. Canonical `mmnet` = `alaska-fuel-spatial-network/mmnet-toolkit/mmnet` (newest of three
   copies, 4 bugfixes). The delivered network was built with the oldest, pre-fix copy —
   it stays frozen unless the owners choose a rebuild.
2. `edge_id` = shapefile row order. The `final_network` zip members must remain
   byte-identical (verify md5s after any repack) or every edge_id-keyed DuckDB table
   is invalid.
3. `alaska_network_mmnet` has no git remote — back it up before touching anything.
4. The sibling `alaska_network_pipeline_mmnet` (TAPS study) editable-installs mmnet by
   absolute path from `alaska_network_mmnet` — never move or delete that tree until TAPS
   is repointed.
5. The 4.7 GB GEE stack and ~7 GB friction rasters exist on no local machine; the friction
   half can only be verified by unit tests and dry runs until a GEE re-export.
