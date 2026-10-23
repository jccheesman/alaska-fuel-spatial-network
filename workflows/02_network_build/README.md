# Workflow 02 — spatial-network build (act b)

Builds the connected multimodal transport graph (road + barge + air +
seasonal ice road) with the region-agnostic `source_scripts/mmnet` engine. Every
region-specific choice is DATA in `profile.yaml` (this directory) — improve
the model by editing the profile, not the code.

## Run order (complete — including the steps the old README omitted)

```bash
python 00_normalize_raw.py       # data/raw -> data/interim (EPSG:3338, canonical cols, MANIFEST)
python 01_prep_waterway.py       # NWN -> data/interim/ak_waterway.gpkg  (required by stage 04!)
python 02_prep_airways.py        # OD legs -> airways.geojson + air_nodes + boundary
python 03_fetch_basemap.py       # Natural Earth (figures only; needed by figure_scripts/plot_paper_network.py)
python 04_build_network.py       # validate_profile + mmnet stages 01->04 + reports
python 05_verify_north_slope.py  # connectivity assertion gate
python 06_export_final_network.py  # -> final_network/ zips + sha256 manifest (DELIBERATE step)
# or: bash run_all.sh            # chains all of it with input gates
```

Raw inputs: `data/raw/**` (not in the repository; download and regenerate —
the file-by-file layout and sources are in `DATA.md` §1.2–1.3 and §4.1), the
air CSVs tracked at `inputs/air/`, and the manual-connections shapefile.
The **facility inventory** is not the raw AEA CSV: `00_normalize_raw.py` reads
the published `facilities_clean.csv` from workflow 00 (`00_inventory_qc`, latest
release) — QC a release there before building.
Requires `Rscript` + sf/sfnetworks/tidygraph/dplyr for the noding oracle.

## Outputs and the downstream consumer

Engine artifacts: `outputs/02_network_build/{output,reports}` (gpkg stages
01→04, QGIS projects via `viz/`, connectivity reports).

**The consumer of this workflow is workflow 03** (`03_multimodal_join`): step
06 exports the joined network into the top-level `final_network/` as the
frozen handoff (zips + manifest). The committed handoff is the
network-of-record — re-export deliberately, never casually
(`final_network/README.md` explains the edge_id contract and the pre-fix
engine provenance).

## Engine docs

`docs/ARCHITECTURE.md` (stage chain, R↔Python seam, extend-by-profile
recipes) · `source_scripts/mmnet/r_oracle/CONTRACT.md`.
