---
name: define-network-profile
description: Author or extend the region's profile.yaml — the single source of truth the mmnet
  build reads. Use when adding a transport mode, a transport layer, an intermodal connection rule
  (transfer / snap / bridge / connect-to-giant / component-join), an anchor, or tuning hub/topology
  parameters for a multimodal network. Do NOT use to edit the mmnet/ engine code (the build is
  region-agnostic — nothing region-specific belongs in code), and do NOT use to RUN the build
  (that's build-and-verify-network).
---

# Define the network profile

The `mmnet` engine is region-agnostic: **every region-specific value lives in one `profile.yaml`**,
never in code. Building or changing a network means editing that file, then running the build. This
skill covers the *authoring* judgment; running + proving is `build-and-verify-network`.

## Core invariants (non-negotiable)

If a proposed change would break any of these, stop and surface the conflict before proceeding.

1. **Profile is DATA; `mmnet/` is region-agnostic.** Never hardcode a region, mode, path, or tolerance
   in the package. A new mode/rule is a profile edit with **no code change** — the build derives its
   modes from the `layers:` registry dynamically.
2. **One connection primitive per intent.** Modes only connect where a rule says so; a mode with no
   rule stays its own component (no edge is fabricated to force a join). Pick deliberately:
   - `transfers:` → a **Transfer EDGE** at an anchor point, added where the anchor is within `max_dist`
     of BOTH modes' nodes (e.g. barge↔road / barge↔ice at ports + barge hubs).
   - `snaps:` → **move an endpoint onto another mode's node** — a SHARED node, **no edge**. This is how
     **airports** connect (Plane→Road @ airports); airports are a `snaps:` rule, **never** a `transfers:`.
   - `bridges:` → a proximity connector when the real gap ≤ `max_dist`: same mode = a WELD (road↔road,
     ice↔ice), distinct modes = a cross-mode BRIDGE (ice↔road).
   - `connect_to_giant:` → a final shore-landing pass that pulls every still-isolated **surface** piece
     into the giant within `max_dist` (this is what joins coastal/North-Slope pieces by sea).
   - `join_components:` → the optional Stage-04 distance join: link every remaining non-giant component
     to the giant within `max_dist`, iterated. `max_dist: 0` disables it (03 stays canonical).
3. **`snap_target: true`** marks the surfaces hubs may land on (Road ∪ Ice Road). Hubs snap only there.
4. **Units.** Distances are METERS in the profile's projected `crs.target` (e.g. EPSG:3338 Alaska
   Albers). Meter thresholds require a projected CRS — `validate_profile` rejects meters on a geographic
   (degree) CRS.
5. **Paths are relative to the profile's own directory** (self-contained), or `root/sub` references.

## Where the canonical values live

- `profile.yaml` — the file you edit: `crs`, `inventory`, `modes`, `tagging`, `layers`, `transfers`,
  `snaps`, `bridges`, `connect_to_giant`, `join_components`, `anchors`, `hubs`, `topology`.
- `mmnet/config.py` — the strict schema (pydantic `extra="forbid"`): `RegionProfile` and the specs
  `ProfileLayerSource`, `TransferSpec`, `SnapSpec`, `BridgeSpec`, `ConnectToGiantSpec`,
  `JoinComponentsSpec`, `HubParams`, `TopologyParams`. Field names/types are enforced here.
- `examples/alaska/profile.yaml` — a complete worked profile to copy from.

## Procedure

1. **State the change** and pick the primitive from invariant #2 (mode? layer? which connection rule?).
2. **Add a transport MODE** = two entries, no code:
   - `modes:` → `{ name: <Mode>, routable: true }`
   - `layers:` → `{ name: <layer>, mode: <Mode>, edge_label: <Label>, kind: line, loader: <loader>,
     source: { type: file, path: <path> }, snap_target: true|false }`
   The `edge_label` is the value that shows up as the edge `type` in the built network.
3. **Add a CONNECTION** = one rule of the right kind (invariant #2), using **mode names** (not labels):
   e.g. `transfers: - { from_mode: Road, to_mode: Barge, anchor: ports, max_dist: 5000 }`, or
   `snaps: - { from_mode: Plane, to_mode: Road, anchor: airports, max_dist: 2000 }`. Declare any new
   point layer under `anchors:`.
4. **Tune a parameter** only with a reason; keep it in the profile (never hardcode downstream).
5. **Validate** before building:
   ```
   python -c "from mmnet.config import validate_profile; p=validate_profile('profile.yaml')[1]; print(p or 'PASS')"
   ```
   Fix every reported problem (unknown key, missing file, bad CRS/units, missing CSV column).
6. **Hand off** to `build-and-verify-network` to run the pipeline and prove connectivity.

## What NOT to do

- Do NOT edit `mmnet/` to add a region-specific mode, path, or tolerance — it goes in `profile.yaml`.
- Do NOT make airports (or any snap-style link) a `transfers:` edge — they **snap** (shared node).
- Do NOT add a mode without a connection rule and expect it to join the network; it will stay isolated
  (that may be intentional — decide, don't assume).
- Do NOT put meter thresholds on a geographic (degree) CRS.
- Do NOT invent profile keys — the schema is strict (`extra="forbid"`); unknown keys fail at load.

## Related

- `build-and-verify-network` — runs the pipeline and proves the result after a profile edit.
- `mmnet/r_oracle/CONTRACT.md` — the R↔Python file contract the build uses.
- `examples/alaska/profile.yaml` — a full worked profile.
