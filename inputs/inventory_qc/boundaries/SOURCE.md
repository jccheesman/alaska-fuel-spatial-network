# Community boundaries used by the label check (stage 05)

Supplied by the owner 2026-10-06. Public data; tracked here (the repo's blanket `*.zip`
ignore is negated for this folder). Both are EPSG:3338.

| File | Layer | Features | Matched by | sha256 |
|---|---|---|---|---|
| `City_Boundaries.zip` | DCRA incorporated city boundaries (`CommunityN`, `CommunityI` GUID, `Incorporat` class) | 145 | `community_id` GUID, else canonical name | `f767c70907ab1c1abb168b43907ed91e6a8ea108bdef69ee64a4f39e9fbfe4c4` |
| `Census_Designated_Place_Boundaries.zip` | Census Designated Place boundaries (`Name` … CDP) | 208 | canonical name (" CDP" suffix stripped) | `baf88dd448b3883b25f5184ee82103c2e2b16ece713090a2107b21086aadef9f` |

Not covered, by owner decision (2026-10-06): borough / census-area boundaries. Communities
without a city or CDP boundary (unified city-boroughs such as Anchorage, Juneau, Sitka,
Wrangell; military bases; unincorporated places without a CDP) are not tested and are kept
as labelled.

Replacing either file: update the sha256 here and in `inputs/MANIFEST.md`, re-run
`workflows/00_inventory_qc/run_all.sh`, and review `boundary_summary.csv` for changes.
