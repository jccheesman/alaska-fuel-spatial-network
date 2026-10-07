# Known upstream inventory data bugs

One note per confirmed defect in the published bulk-fuel inventory, so the next person does not
rediscover it. Each says what it looks like, why it happens, and which config row handles it.
Referenced from the inventory-QC skills as `[[note_name]]`.

| Note | Records | Handled by |
|---|---|---|
| [aea_shared_tank_farm_ids](aea_shared_tank_farm_ids.md) | 51 (2022) / 42 (2025) | `shared_farm_id` detector; corrections (6 relabel-to-keep-farm) |
| [aea_within_farm_copies](aea_within_farm_copies.md) | 66 deleted by AEA in 2025 | `within_farm_copies` detector; count a farm once |
| [aea_unalaska_unalakleet_swap](aea_unalaska_unalakleet_swap.md) | 2 | corrections (approved 2026-10-05) |
| [aea_map_point_vs_latlon](aea_map_point_vs_latlon.md) | 12 | `map_point_disagrees` detector |
| [gateway_drops_unlisted_communities](gateway_drops_unlisted_communities.md) | ~130 | gateway file is evidence only |
