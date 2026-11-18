---
name: connect-nearshore-barge-hubs
description: Give a nearshore (ocean) barge-coded hub a real summer barge route — audit its
  access, draft or redraw a manual Barge line that passes the barge-surface and marine-water
  tests, record the evidence, rebuild and verify. Use when a barge-coded coastal hub has no
  barge link or its line is closed by NoData. Do NOT use for inland or river hubs (list them,
  touch nothing), to edit the NWN base layer or the friction surface, or for cost rates.
---

# Connect nearshore barge hubs

A hub whose facilities are barge-served should be reachable by barge in summer. This skill is
the procedure for giving a NEARSHORE hub that route with a hand-drawn line, without bending
any data to pass. It exists because the build only checks that a hub joins the giant by ANY
mode — a village whose road reaches its airport passes with no barge route at all.

## Core invariants (non-negotiable)

1. **The network describes; it does not force.** A line needs evidence: the inventory barge
   flag on the hub's facilities PLUS a document naming barge service (energy plan, lightering
   guide, tariff) — or an owner decision recorded as such. Every line gets a row in
   `inputs/mannual_connections/PROVENANCE.csv`.
2. **Nearshore only, marine water only.** In scope: hubs with marine water
   (`water_class_150m.tif` = 1) within 15 km. Lines run through marine pixels only and never
   follow a river. Inland and river hubs: report "not assessed (inland or river)" — no line,
   no review item, no recommendation. Borderline hubs need the owner's yes BY NAME.
3. **Never bend the data.** Do not touch the friction surface, waterway masks, thresholds or
   the strict NoData rule to make a line pass. Move the line, or report that it cannot pass.
   A genuine surface defect (e.g. the 2026-11-17 corridor-mask source mismatch) is a separate
   finding for the owner + the friction skills (`assign-friction-values`,
   `run-friction-pipeline`).
4. **Manual lines may be redrawn; the NWN base layer is published source** and is never
   hand-edited.

## Where the canonical values live

- Scope + method constants: `friction_config.py` `WATER_CLASS_*`; label built by
  `workflows/01_friction_build/04_build_water_class.py`.
- The line test: `workflows/02_network_build/qa/00_check_manual_barge.py` (the pipeline's own
  75 m sampler; July required, months 6-10 reported; marine-only rule included).
- Access + passability reports: `workflows/02_network_build/qa/06_barge_hub_access.py`
  (topology, post-build) and `workflows/03_multimodal_join/06_qa_barge_passability.py`
  (month-gated, post-weighting).
- Known exceptions: `inputs/network_qc/accepted_barge_exceptions.csv` (kind=hub by community,
  kind=line by shapefile row). A NEW failure fails the stage; a listed one is reported.

## Procedure

1. **Audit.** Run the two reports above; confirm the hub is nearshore in scope and what
   exactly fails (no waterway link vs an edge closed by NoData; manual vs NWN layer —
   NoData whose minimum over 12 months never clears is land or missing coverage, not ice;
   test July, or August-September on the Arctic coast).
2. **Draft in scratch** (never under `inputs/` first): `Mode="Barge"`, EPSG:3338, schema
   `Shape_Leng, Mode` only — the engine drops other per-feature attributes
   (`03_prep_manual_connections.py`), which is why provenance lives in the sidecar CSV.
   - Start ON the network: an existing waterway vertex, or within 100 m of a base waterway
     line (`mmnet/build.py::_weld_barge_landings` inserts the shared vertex). Chained lines
     share an identical vertex.
   - End in open water, 2-5 km offshore (or mid-channel), within the profile's transfer
     reach (25 km) of the hub. Never draw onto a road node or across the shore.
   - Check the nearest-node trap: the transfer goes to the hub's NEAREST waterway node; the
     new end must be that node, or the existing nearest node must have an open path.
3. **Test before the build**: `qa/00_check_manual_barge.py --lines <draft>` must PASS (every
   segment on valid barge pixels in July AND on marine pixels). A coastline from another
   source is a drafting aid, never the test.
4. **Record evidence** in `PROVENANCE.csv` (line, hubs served, action, evidence, reviewer,
   date).
5. **Edit the layer**: replace/append features in
   `inputs/mannual_connections/mannual_connections.shp` (Plane/Road features untouched; the
   old layer stays in git). Show the owner the before/after.
6. **Rebuild workflow 02 WITHOUT the export step** and verify: the "welded N manual-barge
   endpoint(s)" count, one new Barge transfer per hub served, `05_verify_north_slope.py`
   green, `qa/06_barge_hub_access.py` green, the component count, and a summer barge path to
   Anchorage for every hub served.
7. **Hand off**: a re-export is the owner's decision (new network-of-record: new edge_ids,
   full workflow-03 rerun, zips + checksums + EXPECTED + harness adoption). After re-export,
   remove the served hubs' rows from the exceptions CSV.

## What NOT to do

- No ROAD stubs by hand. This skill draws water lines only. A barge hub with no road of its own (no
  road or ice road within `hubs.site_stub_km` of any of its sites) gets a short road stub at its own
  site from the build itself, so that it lands there and takes a barge landing; eight such stubs were
  hand-drawn on 2026-11-18 and replaced by the rule the same day. If a hub needs a stub and did not
  get one, or got one it should not have, report it (`output/02_site_stubs.csv`; review procedure in
  `build-and-verify-network`). What this skill can still do for such a hub is shorten a long landing:
  a barge line that ends a few km off its shore, as for any other nearshore hub.
- No lines, review items or recommendations for inland or river hubs, however barge-flagged.
- No NWN edits, no friction/mask/threshold edits, no cost-rate edits (`friction_costs.py` is
  out of bounds; the label feeds the cost split but this skill never touches rates).
- No export, no commit, unless the owner asks in-session.
- Do not add exceptions to silence a NEW failure without looking at it — the exception file
  is a reviewed list, not a mute button.

## Related

- `define-network-profile` / `build-and-verify-network` — the profile and the rebuild+proof.
- `assign-friction-values` / `run-friction-pipeline` — surface defects found by the audit.
- `record-facility-corrections` — when the audit reveals an inventory flag problem instead.
