# A relabel keeps the old community's code

**What it looks like.** A record the owner relabelled (a `community_name`
correction) is published with the new label but the OLD community's
`community_id`, the DCRA community GUID that came with the raw record. Its
`community_relation` reads `elsewhere` and `community_distance_km` is the
distance to the community it was moved away from (838.67 km for the FAA Nome
station tanks, still measured to Fairbanks).

**Why it happens.** A `community_name` correction changes only that column.
The boundary check (stage 05) prefers `community_id` when the code names a city
boundary, and falls back to the community key only when it does not. So when
the OLD community is a city, the check measures against the old city. When the
old community is a census place (no city boundary), the check falls back to
the label and the relation comes out right, but the stored code is still the
old one.

**Why it matters.** The network build's `remote_site_km` rule (20 km, profile
`hubs`) makes any site farther than that from its community its own hub, using
this distance. A relabelled site with the old code can therefore become a
separate hub instead of joining the community it was relabelled to.

**How it is handled.** A second, owner-approved correction row per record,
`field = community_id`, old = the old community's code, new = the new
community's `CommunityID` in the State of Alaska DCRA Community Overview. Write
it with every relabel. Check for leftovers by comparing each published record's
`community_id` with its `community_name`'s DCRA code.

| Records | Handled |
|---|---|
| 1058, 1060 (Fairbanks → Nome) and 7 earlier relabels (754, 898, 1680, 1654, 322, 592, 595) | corrections approved 2026-11-16 ([owner_review_2026-11-16](owner_review_2026-11-16.md)) |
| 1197 (Delta Junction → Healy Lake) | with its relabel, 2026-11-16 |
| 51, 104, 632, 1858 (old community a census place; relation already right) | open question for the owner |
