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
| `final_network/network_joined_nodes.zip` | `6976a7cf9cce3f8466cde82f1953f4bb959e938e666d4430186270b4ad5debae` |
| `final_network/network_joined_edges.zip` | `dacf1a7622d082a5e38b567c093c45b84a72ba3e92afc9510a172bb8b7c74c60` |

| Pending | note |
|---|---|
| `inputs/network_raw.zip` | optional local bundle of the six public downloads — never committed; see DATA.md §4.1 |
| the rasters (`inputs/friction_rasters/`, the friction stack), `inputs/river_ice_work/` | not in the repository — in the Zenodo deposit; `tools/fetch_archive.py` verifies each download against the deposit's own checksums |

## final_network zip members (the current network-of-record)

Re-exported 2026-11-18 (second export of the day) by
`06_export_final_network.py` on branch `barge-landing-fixes` at `d2c0483`
(`docs/CHANGELOG.md`): the landing-class naming rule retypes the four
BargeAirTransfer landings as BargeRoadTransfer, the Port MacKenzie anchor
exclusion removes its ports landing, the facility-56 correction moves the
Anchorage hub into Anchorage city, and 12 road-less Barge hubs land on 100 m
site stubs. Nodes 84,110 → 84,134, edges 93,061 → 93,080 (Road 55,539 →
55,551, BargeRoadTransfer 298 → 309, BargeAirTransfer 4 → 0); hubs 328 and
components 4 unchanged. Supersedes the first 2026-11-18 export
(waterway-network-updates).
sha256 per member is also written to `final_network/MANIFEST.sha256`; `.cpg` and
`.prj` are format-fixed and carry over unchanged.

| Member | sha256 | md5 |
|---|---|---|
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.dbf` | `57045749045b9be48897d47d627574f428e3bf0ff00842f1c7246df643ec970f` | `320c016d7882ee3503bbe634ec7a7fdf` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shp` | `f7318a2363d2424002661397a3329edd506e5751af686d9c17fe0f85b02fdb14` | `1bb6bb46a8b779fbbcd6241043e833b3` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shx` | `5a1f2e2685451893460f8235382be22ac1a0d224fff6e5a1fc4206968c64b9c9` | `2c11ee9811d16db1f0ed4c85d8f5e5a8` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.dbf` | `6e1b3b3f4ffef2bc66d09ce07bab0b4f51953af3b22826ac0c2726e07c8d1e7e` | `57db8c6e712832fdafa95706633971aa` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shp` | `0a73589cdda2cf2958b8fa10553a5729f985e05fb9e8b24593f11542ad286220` | `be39fb20d22711bbb710dd14018028b9` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shx` | `2bdf0ee86b5bfb6dd86d691e406481c198329cc29d5e6e33b294d158e031e075` | `15c8cf7626fd7472581ecc4dd7026e42` |

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
