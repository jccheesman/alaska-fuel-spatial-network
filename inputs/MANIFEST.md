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
| `final_network/network_joined_nodes.zip` | `0757b28283fd526e3295e4aadef334095e410f6d7e7bd7715dcd4bc6dc51299c` |
| `final_network/network_joined_edges.zip` | `c8333fa0c4bcda7c77940c346fcf2e9062e99efb57be02ee087b676e9986077e` |

| Pending | note |
|---|---|
| `inputs/network_raw.zip` | optional local bundle of the six public downloads — never committed; see DATA.md §4.1 |
| the rasters (`inputs/friction_rasters/`, the friction stack), `inputs/river_ice_work/` | not in the repository — in the Zenodo deposit; `tools/fetch_archive.py` verifies each download against the deposit's own checksums |

## final_network zip members (the current network-of-record)

Re-exported 2026-11-16 by `06_export_final_network.py` after the owner review of
that day (`docs/inventory_notes/owner_review_2026-11-16.md`, 17 records corrected
by manual approval): ten remote-site hubs fold into their communities' and Healy
Lake gets its own hub (hubs 337 → 328, edges 93,049 → 93,046, BargeRoadTransfer
289 → 286; see `final_network/README.md`). Supersedes the 2026-11-15 export.
sha256 per member is also written to `final_network/MANIFEST.sha256`; `.cpg` and
`.prj` are format-fixed and carry over unchanged.

| Member | sha256 | md5 |
|---|---|---|
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.dbf` | `87baaf959baf15f61747a50cd28100a54fc2a95a21b7481c979b25e14665ab31` | `539748833e8993da3d0f0fcedd574a22` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shp` | `a7d2e07bc4e7e034517e003652a9ce196ecc1d38befadba396e576c8da1a93df` | `ee75104dfa6b0c2845067d5cc4a3535f` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shx` | `6c1004650dee04ea0197874ea2a7bbb80643076bdc89953a4e5a14566896641a` | `f102775eb5ff2f21e02bf7e480ed9be9` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.dbf` | `879ba649d8c340ee079c47c69128ecccc5d2006a58ec84e740e6c267c3a82867` | `e74f3a39d00aee15b618c6b3c64715b4` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shp` | `223c933dabf34afb84900990bcde31aa6fc98c559ca10cad2aa58140e2906f33` | `8358e5088fbe113b7aa08c70aecb0121` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shx` | `903453e8fcad853a6650f989f75c6db8e99ad1198067fe5a50717af37bfd2d29` | `99a265c3757adf66d343cc013edc7c05` |

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
