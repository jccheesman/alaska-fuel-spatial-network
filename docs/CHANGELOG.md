# CHANGELOG — network-of-record versions

Every version of `final_network/` that has been the network-of-record, newest
first. Each re-export is a **new** network-of-record: its shapefile row order
defines `edge_id`, so every edge_id-keyed table (`network_edges`,
`edge_month_weights`, `edge_costs`) belongs to exactly one version below and
must never be joined with another version's tables. The re-export procedure is
in `final_network/README.md`; the contract in `DATA_CONTRACTS.md` §4–5.

Checksums are the first 16 hex digits of the zip's sha256. Full values for the
current version are in `inputs/MANIFEST.md`; earlier zips can be recovered
from git with `git show <commit>:final_network/network_joined_edges.zip`.

| Version | Commit | Nodes | Edges | Hubs | Components | Giant | edges.zip | nodes.zip |
|---|---|---|---|---|---|---|---|---|
| **2026-10-15** (current) | `d7faf7a` | 84,094 | 93,049 | 329 | 4 | 99.99% | `2104767a4721c333` | `f6775915ca4d0d8c` |
| 2026-09-29 re-bake | `4c89339` | 84,089 | 92,978 | 385 | 5 | 99.99% | `302bf150b690e760` | `1bcfdb5e21213e60` |
| 2026-09-15 | `d5cde1f` | 84,089 | 92,978 | 385 | 5 | 99.99% | `56c802470378a39b` | `b03ba3202ae9a4b2` |
| 2026-09-12 | `a2e7a9e` | 82,412 | 91,087 | 384 | 6 | 99.98% | `558dfa5b88ad93b9` | `30808a7f0f6bf470` |
| 2026-07-20 pre-fix freeze | `f455f0e` | 82,300 | 90,921 | 384 | 21 | 99.65% | `4b1ffe008b07049c` | `3f50dfb80b034f25` |

## 2026-10-15 — phase-5 hubs, corrected inventory, wider reach

Commit `d7faf7a`; the hub handoff followed the same day in `e9bf638`, which left the zips unchanged.

- **Hub builder, phase 5:** hubs group by the corrected community label; there's no linking across communities; remote sites are isolated as their own hubs; records with an open owner review item are withheld.
- **Corrected 2025 facility inventory:** workflow 00's `facilities_clean.csv`, with coordinate and label corrections and 71 duplicate rows removed. Hubs went from 385 to 329.
- **Reach:** connect-to-giant and the barge-transfer reach went from 2 km / 5 km to 25 km, plus a 2 km snap-to-edge hub fallback. This rejoined 27 coastal communities and 5 hubs on long edges.
- **Hub handoff:** `final_network/hub_members.csv` and `hub_snaps.csv` were added. `02_load_final_network.py` loads them as the `hub_members` / `hub_snaps` tables.
- Edge types: Road 55,539 · Waterway 34,178 · Air 226 · IceRoad 1,248 · RoadConnector 1,498 · IceRoadConnector 34 · BargeRoadTransfer 289 · BargeIceRoadTransfer 21 · IceRoadRoadTransfer 12 · AirRoadTransfer 2 · BargeAirTransfer 2.
- **Open:** `edge_month_weights` / `edge_costs` were **not** regenerated (they need the friction stack). Rerun workflow 03 in full before using the costed graph.

Related cost change, not a re-export: `31de462` prices BargeAirTransfer as a barge↔overland transfer.

## 2026-09-29 — mode-based connector types (re-bake)

Commit `4c89339`.

- Same topology as 2026-09-15: `edges.shp` is byte-identical and only the `type` attribute in the `.dbf` changed. Row order, and therefore `edge_id`, is unchanged, but the zips and every type-dependent table were regenerated.
- Synthetic connectors are now named by the modes they join: `{Mode}Connector` welds and per-pair `{A}{B}Transfer` handoffs. The generic `Bridge` / `Weld` / `Join` / `Transfer` labels were retired.
- Edge types: Road 55,534 · Waterway 34,178 · Air 226 · IceRoad 1,248 · RoadConnector 1,498 · IceRoadConnector 35 · BargeRoadTransfer 234 · BargeIceRoadTransfer 11 · IceRoadRoadTransfer 12 · AirRoadTransfer 2.

## 2026-09-15 — AK DOT&PF roads only

Commit `d5cde1f`.

- The road source became the 2026-09 AK DOT&PF download alone. The GRIP4 Canada border-stitch was removed, because transnational roads are not fuel-delivery routes.
- The manual-connections layer is still included.
- Edge types (old vocabulary): Road 55,534 · Waterway 34,178 · Bridge 1,482 · IceRoad 1,248 · IceRoadConnector 36 · Transfer 225 · Air 226 · Join 49.
- The weighted tables were regenerated with this export (1,115,736 rows) and reproduced the QA envelope.

## 2026-09-12 — fixed engine + manual connections

Commit `a2e7a9e`.

- First export from `source_scripts/mmnet`, the fixed engine, with the user-authored manual-connections layer (`inputs/mannual_connections/`: 7 barge, 6 plane and 1 road line).
- The engine's `assemble.py` mis-snap fix was verified as a no-op on the Alaska data (2026-08-17: all 384 hub snaps identical). Every count change in this export comes from the manual connections.

## 2026-07-20 — pre-fix freeze

First committed in `f455f0e`, when the repo was restored under version control on 2026-08-07.

- Exported by the original vendored mmnet copy in `alaska_network_mmnet`. That engine predates the four fixes now carried by `source_scripts/mmnet`, so it cannot be reproduced bit-for-bit.
