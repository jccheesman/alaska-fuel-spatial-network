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
| `final_network/network_joined_nodes.zip` | `f6775915ca4d0d8c3ee796019755442e7bd98de9905d55c75650672d0f75f6c3` |
| `final_network/network_joined_edges.zip` | `2104767a4721c333d41a20fde095d86424b15ecf6a5bfa4c0d077249b85d4503` |

| Pending | note |
|---|---|
| `inputs/network_raw.zip` | not yet committed — license-gated; see inputs/README.md |

## final_network zip members (the current network-of-record)

Re-exported 2026-10-15 by `06_export_final_network.py` — a rebuild carrying the
phase-5 hub builder, the corrected 2025 facility inventory, the 25 km
connect-to-giant / barge-transfer reach, and the 2 km snap-to-edge hub fallback
(see `final_network/README.md`). Supersedes the 2026-09-15 AK-DOT-only export.
sha256 per member is also written to `final_network/MANIFEST.sha256`; `.cpg` and
`.prj` are format-fixed and carry over unchanged.

| Member | sha256 | md5 |
|---|---|---|
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.dbf` | `4728ca43b6bc6a25389d6e9b4d4a4947053665a97a2ae3c6c7b383434de37fc2` | `b0fda5a840f80ca5f6da90f615128349` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shp` | `a7d2e07bc4e7e034517e003652a9ce196ecc1d38befadba396e576c8da1a93df` | `ee75104dfa6b0c2845067d5cc4a3535f` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shx` | `6c1004650dee04ea0197874ea2a7bbb80643076bdc89953a4e5a14566896641a` | `f102775eb5ff2f21e02bf7e480ed9be9` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.dbf` | `ad8efc33385de8b75c0235eefc90f82f09188de1a3d0c6f094af1dd7e4bfdd11` | `d98ffc70b1d045e74d26b085b1ffa71b` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shp` | `03177acd4ef97d8f702f921f6db53f387034ea73202d4625a0f6051b2c287374` | `acc2dc25e39448c3bfb74b572b4a0efa` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shx` | `6d6177912bcd5fc5a9cc0a55d1ac0ae080b67401879b19e08fb1a99824940070` | `94a980f2ec7fc83085431dba7d3339d9` |

## Tracked air CSVs

| File | sha256 |
|---|---|
| `inputs/air/airports_ak_dotpf.csv` | `046facdcf4f4a2cfc143d1803f5ef4ef7ef2e68003f699e80fdfeed5697ceca2` |
| `inputs/air/flight_paths_combined.csv` | `0f4229e04b9e2c3b1a1dc697d099ec75f80420cd27fe49531433f11f626d735b` |
| `inputs/air/flight_paths.xlsx` | `c7734ec0b1173da46786c09752b040463ab5c2b9de0ffed9065c16324ebbfcd6` |
