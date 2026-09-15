# inputs & final_network — checksums

sha256 of every committed data artifact. Regenerate this table after any
deliberate repack (`shasum -a 256 <file>`); CI and reviewers use it to catch
accidental data drift. The final_network member checksums are ALSO the
edge_id-contract guard: those shapefile bytes define the row order every
DuckDB table is keyed by (see final_network/README.md).

## Committed zips

| File | sha256 |
|---|---|
| `inputs/bulk_fuel_data.zip` | `184181c0c89d486ae92feb1ab4015b7aef2d986e549b412061136ad7d761102d` |
| `inputs/data_for_network_build.zip` | `c11708c68da39b76a66511b735fa7983bfebac3d4167fde0fdf3c7ce5df0babf` |
| `inputs/region_and_census_data.zip` | `e8c36f6329804b0378277a8c449de984c553ca4bba5bdfb4cbae68684d8e2eb3` |
| `final_network/network_joined_nodes.zip` | `30808a7f0f6bf470cfa9ebb5dc31406d840ea9e90f24ef1a4b42c343c77006ac` |
| `final_network/network_joined_edges.zip` | `558dfa5b88ad93b93fa8ef0f78da6054dcb19f1439207e52fcb140cb6bacf6ea` |

| Pending | note |
|---|---|
| `inputs/network_raw.zip` | not yet committed — license-gated; see inputs/README.md |

## final_network zip members (the current network-of-record)

Re-exported 2026-09-12 by `06_export_final_network.py` — a rebuild with the
fixed `source_scripts/mmnet` engine that includes the user-authored
manual-connections layer (supersedes the 2026-07-20 pre-fix frozen export).
sha256 per member is also written to `final_network/MANIFEST.sha256`; `.cpg`
and `.prj` are format-fixed and carry over unchanged.

| Member | sha256 | md5 |
|---|---|---|
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.dbf` | `36dfac57c741cb3b28ebf0f2d65379f1e4ad2b90ece6a83513e57a1e0673d108` | `0e218ad115b212ba5acf1df4ea5844ce` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shp` | `0e31f0dffde6c31df10f7047c91da5fb1a872ad7d299a12c30061e8bf2648804` | `c733dd3f46a0d8479eddb8baea44e730` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shx` | `b19dc9b432b4291bce7815ddad706b888f383d24f16ec6cc36b56139389e6bd9` | `4e1e656539362d2a2e726508c628edb4` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.dbf` | `03c7ef15bf2ff6e2d30578536a8d65d390d3353f65c079d41f46c7918e2c37cf` | `2925c9dc50c10a748ba57d1879c6f483` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shp` | `f986f0f0f274154bbcb689eae0183bc85b39a625026b3348175565bff7be5bc1` | `fb5bc7fb0c01e8f0261171bfbd4b55da` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shx` | `3e74cbd8f725589c80b17d36acecc56e7acd30670c855cee615a9aeffc931213` | `22886ce47addb5e4b2c72af80c24db86` |

## Tracked air CSVs

| File | sha256 |
|---|---|
| `inputs/air/airports_ak_dotpf.csv` | `046facdcf4f4a2cfc143d1803f5ef4ef7ef2e68003f699e80fdfeed5697ceca2` |
| `inputs/air/flight_paths_combined.csv` | `0f4229e04b9e2c3b1a1dc697d099ec75f80420cd27fe49531433f11f626d735b` |
| `inputs/air/flight_paths.xlsx` | `c7734ec0b1173da46786c09752b040463ab5c2b9de0ffed9065c16324ebbfcd6` |
