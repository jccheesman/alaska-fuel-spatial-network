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
| `final_network/network_joined_nodes.zip` | `b03ba3202ae9a4b23e5bdbf35f7d8c8c17e57ae5c403d3e37724d89297e56da2` |
| `final_network/network_joined_edges.zip` | `56c802470378a39bd4696a8a3000dbc76317c29a9ecc1e21a23a3764c55f52b2` |

| Pending | note |
|---|---|
| `inputs/network_raw.zip` | not yet committed — license-gated; see inputs/README.md |

## final_network zip members (the current network-of-record)

Re-exported 2026-09-15 by `06_export_final_network.py` — a rebuild whose only
road source is the 2026-09 AK DOT&PF Roads download (the GRIP4 Canada
border-stitch was removed; transnational roads are not fuel-delivery routes).
Still includes the user-authored manual-connections layer. Supersedes the
2026-09-12 manual-connections export. sha256 per member is also written to
`final_network/MANIFEST.sha256`; `.cpg` and `.prj` are format-fixed and carry
over unchanged.

| Member | sha256 | md5 |
|---|---|---|
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.dbf` | `34cb74e1c45ff8b8abcb402dbc99f529d0e8dbdeea2d8c67f5419ea9fc377c59` | `0b5cc825c4db635cf8d35203704ede44` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shp` | `7c0ca164709c5c9a4749fdf0e30257abf5ce966955d778e4795304730d1fe0be` | `9685481d30377442f7a455a9de3286d0` |
| `final_network/network_joined_nodes.zip::network_joined_nodes/network_joined_nodes.shx` | `3166471db4fecb778949b29db975bba8bb95816922eecb063dcc5bab091c6719` | `acd6a82a15dae827837537aaf2df724d` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.cpg` | `3ad3031f5503a4404af825262ee8232cc04d4ea6683d42c5dd0a2f2a27ac9824` | `ae3b3df9970b49b6523e608759bc957d` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.dbf` | `7fb928dc99412a27e34def0f6afe63ee6cfb1b39a2d619598a15d8e133f3caca` | `fd23b1bc213c67871ec01a68124ae1bd` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.prj` | `b98ae059b6efe2c3d70a2fe5776e3394ae78ebee1754b2fed102dcf63e25916a` | `91cd91099bd22160267bfb88b8a3e4bf` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shp` | `b67f8e1df5ccb8378fea8c71b6dc81bfa4b9d946e50286c0a8f3f2c8d4d9d226` | `7fac5ddd0283696294daa15f2fc8d56c` |
| `final_network/network_joined_edges.zip::network_joined_edges/network_joined_edges.shx` | `2563340860b0392f6723ac2d10ae84213a0030be0493e57cfdbdaeedbd496f67` | `2e49a99b450e317b001f33fb6044f335` |

## Tracked air CSVs

| File | sha256 |
|---|---|
| `inputs/air/airports_ak_dotpf.csv` | `046facdcf4f4a2cfc143d1803f5ef4ef7ef2e68003f699e80fdfeed5697ceca2` |
| `inputs/air/flight_paths_combined.csv` | `0f4229e04b9e2c3b1a1dc697d099ec75f80420cd27fe49531433f11f626d735b` |
| `inputs/air/flight_paths.xlsx` | `c7734ec0b1173da46786c09752b040463ab5c2b9de0ffed9065c16324ebbfcd6` |
