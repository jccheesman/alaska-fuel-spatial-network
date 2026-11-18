# inputs & final_network — checksums

sha256 of every committed data artifact. Regenerate this table after any
deliberate repack (`shasum -a 256 <file>`); CI and reviewers use it to catch
accidental data drift. The final_network member checksums are ALSO the
edge_id-contract guard: those shapefile bytes define the row order every
DuckDB table is keyed by (see final_network/README.md).

## Committed zips

| File | sha256 |
|---|---|
| `inputs/raw_facility_data/2022/bulk_fuel_data.zip` | `184181c0c89d486ae92feb1ab4015b7aef2d986e549b412061136ad7d761102d` |
| `inputs/raw_facility_data/2022/aea_inventory_2022.csv` | see `2022/snapshot_manifest.json` (`snapshot_csv_sha256`) |
| `inputs/raw_facility_data/2025/aea_inventory_2025.csv` | see `2025/snapshot_manifest.json` (`snapshot_csv_sha256`) |
| `inputs/inventory_qc/boundaries/City_Boundaries.zip` | `f767c70907ab1c1abb168b43907ed91e6a8ea108bdef69ee64a4f39e9fbfe4c4` |
| `inputs/inventory_qc/boundaries/Census_Designated_Place_Boundaries.zip` | `baf88dd448b3883b25f5184ee82103c2e2b16ece713090a2107b21086aadef9f` |

Raw inventory files (NOT tracked after 2022; contact fields). Verify a local copy:

| Release | raw `Utilities_Bulk_Fuel_Inventory.csv` sha256 |
|---|---|
| 2022 (inside the zip above) | `132338fe0722bb9338e8c96e53531be2761a1a0497a0dae734d009ba7e1fb5e1` |
| 2025 | `3fbee569c63dccf813d6fa53e608820d53b92e415feb2c7f20556fc0bb0c30b0` |
| `inputs/data_for_network_build.zip` | `c11708c68da39b76a66511b735fa7983bfebac3d4167fde0fdf3c7ce5df0babf` |
| `inputs/region_and_census_data.zip` | `e8c36f6329804b0378277a8c449de984c553ca4bba5bdfb4cbae68684d8e2eb3` |
| `final_network/network_joined_nodes.zip` | `a46585acb160602c7c52bc54e2979ff2e7db2471011a9a1683d3ac9ec8416f61` |
| `final_network/network_joined_edges.zip` | `8e88919ee89931286788439767b8285e62a278f51839daa8489a2b51eca7fe2d` |

| Pending | note |
|---|---|
| `inputs/network_raw.zip` | optional local bundle of the six public downloads — never committed; see DATA.md §4.1 |
| the rasters (`inputs/friction_rasters/`, the friction stack), `inputs/river_ice_work/` | not in the repository — in the Zenodo deposit; `tools/fetch_archive.py` verifies each download against the deposit's own checksums |

## final_network zip members (the current network-of-record)

Re-exported 2026-11-18 by `06_export_final_network.py` on branch
`waterway-network-updates` (`docs/CHANGELOG.md`): the waterway source is the
owner-curated layer (one geometry with the corridor masks — reopens the 8
all-year-closed ports) and the manual layer grows to 19 Barge lines (5 coastal
redraws + 12 new nearshore hubs). Nodes 84,094 → 84,110, edges 93,046 → 93,061
(BargeRoadTransfer 286 → 298, BargeAirTransfer 2 → 4, BargeConnector appears);
hubs 328 and components 4 unchanged. Supersedes the 2026-11-16 hub-key
re-export.
sha256 per member is also written to `final_network/MANIFEST.sha256`; `.cpg` and
`.prj` are format-fixed and carry over unchanged.

| Member | sha256 | md5 |
|---|---|---|
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.dbf` | `d0f9161df4ca8d5cf26b6765c168b6d8a9217ad2f4cefe04e184cd02ef3d4df4` | `37cc21839b63b7a3691274a70e1b5064` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shp` | `48649e30f699a07e74c065fedd8ecc0d3f174fa98fee7e05b4cf82b6e0b31cbc` | `7bfb40ac1051d6d6e5bb170e207cd153` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shx` | `e8b085b2352e909ee5d699e540b0a47383b9fa14aa02f9f85abcea0e0deee02c` | `fffbba3316e33014b2cbd5aabdc8613e` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.dbf` | `fcf67419c734ef8be598c32af51ee904824dfe6fb001928f5fc799ea3d8b18c9` | `2ff0d52530fc49adba88d22d74f9e420` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shp` | `50e9157b0392be874d3b1498480cf96ea8186f27032fb07ebe734ec4dd068e23` | `8ceb1d5160f67c855b3902fc0199df1c` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shx` | `acb8f920fa09a955ffe5d2930a7591f069d86e6a1a63cd3c854cca90e94c6969` | `74fccdee514af2fbb15e2a8e1ba942ea` |

## Tracked air CSVs

| File | sha256 |
|---|---|
| `inputs/air/airports_ak_dotpf.csv` | `046facdcf4f4a2cfc143d1803f5ef4ef7ef2e68003f699e80fdfeed5697ceca2` |
| `inputs/air/flight_paths_combined.csv` | `0f4229e04b9e2c3b1a1dc697d099ec75f80420cd27fe49531433f11f626d735b` |
| `inputs/air/flight_paths.xlsx` | `c7734ec0b1173da46786c09752b040463ab5c2b9de0ffed9065c16324ebbfcd6` |

## Tracked community reference (DCRA; see `inputs/community_reference/SOURCE.md`)

| File | sha256 |
|---|---|
| `inputs/community_reference/dcra_community_locations.csv` | `87163f3577a65ade014a4e4185d98779a1cb316508f4e7d52f15be20dbe15d59` |
| `inputs/community_reference/dcra_community_overview.csv` | `9a045c2b2710b35d48d4c46d87d38d277328c031971964c86b2e6f47de19a81b` |
| `inputs/community_reference/dcra_community_reference.csv` | `aaddb20cb53df7aab22638851ad7f6933322ea6d432f4bd0ad83fb46a2b37d2c` |
