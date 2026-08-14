<!-- Package doc for source_scripts/mmnet — THE single canonical copy of the engine
     (the two other historical copies were deleted in the 2026-08 two-repo
     merge; this one carries the 4 bugfixes: assemble reset_index mis-snap
     fix, scoped warnings, py<3.10 typing, nullable-string names).
     Installed via the repo-root pyproject (source_scripts layout). -->

# mmnet — the multimodal network engine (package doc)

A reusable, region-agnostic **multimodal spatial-network builder** — plus the skills that teach an
agent (or a person) how to use it. Give it a `profile.yaml` describing your region's modes, layers, and
connection rules; it produces a single **connected multimodal network** (road + water + air + any mode
you add) as GeoPackages you can map, analyze, or route on.

It is a **hybrid build**: the bundled **R / sfnetworks** oracle does the hard planar noding of each land
mode, and **Python connects everything once** (snaps hubs, snaps airports onto the road, builds barge
transfers at ports, welds/bridges proximate pieces, and pulls coastal pieces into the giant). The engine
has **no region-specific code** — everything region-specific is DATA in the profile.

## What's in here

```
source_scripts/mmnet/
├── mmnet/                    # the engine (pip-installable Python package + bundled R oracle)
├── skills/                   # how to USE it (Claude-Code SKILL.md files)
│   ├── define-network-profile/     # author/extend the profile.yaml (the judgment)
│   └── build-and-verify-network/   # run the pipeline + prove connectivity
├── examples/alaska/          # a full worked profile + proof gate (Alaska bulk-fuel network)
└── pyproject.toml
```

## Install

```bash
uv pip install -e .   # from the repo root (source_scripts layout)          # Python deps: geopandas, shapely, networkx, matplotlib, pandas, numpy, scipy, pydantic, pyyaml
```

The **build step also needs R** on the PATH with `sf`, `sfnetworks`, `tidygraph`, `dplyr` (R does the
per-mode noding; Python does the rest).

## Quick start

```python
import mmnet
net = mmnet.run_pipeline("examples/alaska/profile.yaml")   # -> ./examples/alaska/output/03_network__{nodes,edges}.gpkg
print(net.summary())
```

Outputs (GeoPackages + a `reports/03_network.md`) land next to the profile, or wherever you point
`MMNET_PROJECT`. `run_pipeline` returns the canonical Stage-03 network; if the profile enables
`join_components`, a separate `04_network_joined` is also written.

## Use the skills

The `skills/` folder holds two Claude-Code skills that encode the conventions and judgment for building a
network (so you don't re-explain them):

- **`define-network-profile`** — author or extend a `profile.yaml`: add a mode/layer, pick the right
  connection primitive (`transfers` vs `snaps` vs `bridges` vs `connect_to_giant` vs `join_components`),
  and validate.
- **`build-and-verify-network`** — run `mmnet.run_pipeline` and PROVE the result is a correctly connected
  network (don't call it done until the connectivity proof passes).

To make them available to Claude Code, copy `skills/*` into a discovered skills folder (e.g. your
project's `.claude/skills/`), or just read them as the authoring/build guides.

## Adapt to a new region

1. Copy `examples/alaska/profile.yaml` to `examples/<your-region>/profile.yaml`.
2. Repoint every path to your data, set `crs.target` (a **projected**, meters CRS), map your inventory
   columns, and declare your `modes`/`layers`/`anchors`/connection rules — follow the
   **`define-network-profile`** skill.
3. `python -c "from mmnet.config import validate_profile; print(validate_profile('examples/<region>/profile.yaml')[1] or 'PASS')"`.
4. Build + prove with **`build-and-verify-network`**.

No engine edits required — adding a mode or a connection rule is a profile change.

## The build, in one line

`consolidate → tag → hubs → build → (optional) join`. The profile drives all of it; the mmnet package
stays region-agnostic. See `mmnet/r_oracle/CONTRACT.md` for the R↔Python file contract.
