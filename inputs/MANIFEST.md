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
| `final_network/network_joined_nodes.zip` | `3f50dfb80b034f252cd2d84ee3a4d1bf19a2c1d93ff518bd10c9edf9e6d3bc75` |
| `final_network/network_joined_edges.zip` | `4b1ffe008b07049cd2fe0d4d5311a4831693290cb01a08dd5f747c1a167fda20` |

| Pending | note |
|---|---|
| `inputs/network_raw.zip` | not yet committed — license-gated; see inputs/README.md |

## final_network zip members (the frozen network-of-record)

Byte-identical preservation verified at merge time (md5 per member below;
matches the pre-merge zips exactly — only `__MACOSX` cruft was stripped).

| Member | sha256 | md5 |
|---|---|---|
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.dbf` | `6ad1482497b02ba4f509e89d374e802ff8b5fea1474530a8e9427115bc18bb35` | `12218c8c053d4657dba7fc55e6d4f16a` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shp` | `048e2f491d9064683556e15a67ac22e74e987544c78705814e9761b29cf983d3` | `90b7552f032cbd51a4f746fc7ef6c761` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shx` | `2a8f033b66813ced97d8a7647f020ef0818486980eddf139e9059e08306fd14c` | `0a1acb4790cb291af6afa29a9c97737d` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.dbf` | `155bca9279d3ef29bf21106ea7b8d50797ffaf9c655df880d989ce3e0ad3d9b6` | `5a78c68daa7ed8e64500b90eb88052d8` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shp` | `5775ff06a4e8cee67a98376f9a290e74255daba9d7021ed390813ab30be88c33` | `9ecce229986615b7c4e0229f29c5f59f` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shx` | `3615cb2c473ba266a32bb69eaad0fa0213be9339acd97d588687db288248660d` | `c258ee38ce6d026d3702e10c4e77bc2d` |

## Tracked air CSVs

| File | sha256 |
|---|---|
| `inputs/air/airports_ak_dotpf.csv` | `046facdcf4f4a2cfc143d1803f5ef4ef7ef2e68003f699e80fdfeed5697ceca2` |
| `inputs/air/flight_paths_combined.csv` | `0f4229e04b9e2c3b1a1dc697d099ec75f80420cd27fe49531433f11f626d735b` |
| `inputs/air/flight_paths.xlsx` | `c7734ec0b1173da46786c09752b040463ab5c2b9de0ffed9065c16324ebbfcd6` |
