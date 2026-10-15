# Facility and hub aggregation errors: investigation report

Scope: harness `refine-tools-MCP` (= `grounded-main`, `be2af1f5`) and data repo `refine-synthetic-connectors` (`0df2c28`, export `4c89339`).
No repository file was changed. All working copies are in a scratch directory outside both repos. No contact fields were read.

## Root causes, in order of impact

| # | Root cause | Step (file : function) | Effect | Fix belongs in |
|---|---|---|---|---|
| R1 | **Coordinate and label errors in the AEA inventory.** Every case the first audit listed is present byte-for-byte in `Utilities_Bulk_Fuel_Inventory.csv`. | source | 104 facilities need a correction; 41 hubs touched | source corrections |
| R2 | **The conflict check only runs inside a TIGER place.** A labelled facility outside any place polygon is never compared with its label. It forms its own one-site hub, wherever it sits. | data `tag.py : assign_community_region` (L110–124, `comparable = has_place & has_comm`) | Unalaska on Norton Sound (Hub_62), Bethel at 67.8°N (Hub_308), Prudhoe Bay on the Kenai (Hub_356) and others; 26 one-site hubs consist only of a raw-flagged facility | data repo |
| R3 | **Hub grouping key is `(raw community string, TIGER place, borough)`.** Mode is not a key and capacity is never a key. Any labelled site in a different place, or outside every place, gets its own hub. | data `hubs.py : aggregate_hubs` (L203–236) + `profile.yaml hubs.group_by: [community, city, region]` | 64 labels split into 158 hubs. Fairbanks alone has 11 exported hubs plus 1 lost. Spelling variants of one CommunityID split hubs too. | data repo |
| R4 | **Snapping has no distance limit and overwrites on collision.** A hub snaps to the nearest road or ice-road node however far away. If two hubs pick the same node, the later one overwrites the earlier one's row. | data `assemble.py : connect_multimodal` (L155–170) | 9 hub IDs vanish (82, 184, 196, 231, 235, 257, 316, 343, 384). 52 hubs moved more than 10 km and 34 more than 25 km. The `hubs.py` docstring promises a `max_snap_dist_m` drop that does not exist. | data repo |
| R5 | **50 m consolidation merges copied-coordinate stacks across communities.** The merged site takes the label of the first CSV row. | data `consolidate.py : consolidate_facilities` (L151, L170) | 32 sites built from 107 facilities of 2–6 communities. For example, Hub_387 "Chefornak" sits at Atmautluak and overwrote the real Atmautluak hub. | source + data repo |
| R6 | **Unlabelled sites outside a place fall back to one group per borough.** | data `hubs.py : aggregate_hubs` (L205–210 coalesce) | 20 hubs of unlabelled sites; 11 are spread over more than 30 km (Hub_83: 165 km, Hub_85: 472 km) | data repo |
| R7 | **The harness maps by straight-line nearest hub**, ignoring real membership, mode and community. | harness `build_hub_facility_map.py : build` | 121 of the 1,624 facilities with high-confidence membership are staged at a hub they did not aggregate into (83 local, 38 remote) | harness |
| R8 | **The harness relabels hubs by a local-facility vote**, with a lexical tie-break and remote facilities excluded. | harness `label_network_concepts.py : _hub_communities` (L109–125) | 39 hub labels differ from the community that built the hub: 16 renamed, 20 erased, 3 unnamed groups named | harness |

### The two headline cases

- **Unalaska on Norton Sound.** The cause is source plus hub builder.
  - In the CSV, f001606 (row 1770) is labelled Unalaska but sits at 63.89194, -160.68420, inside Unalakleet. f000147 (row 1756) is labelled Unalakleet but sits at 53.882740, -166.550742, in Dutch Harbor. Both rows carry the CommunityID that matches their label, so the coordinates are the swapped field.
  - The hub builder handles the two halves differently. f000147 is inside the Unalaska place, so the cross-borough rule drops it silently. f001606 is outside the Unalakleet place, so it is never checked. It becomes the one-site hub Hub_62 (capacity 1,000 = f001606 alone).
  - `_hub_communities` then names the hub after its only local facility.
- **Bethel above the Arctic Circle.** The cause is a source latitude typo plus the hub builder.
  - f000283 (row 313) is stored at 67.79558, -161.76110, where 60.79558 is correct. The site is outside every place in the Northwest Arctic Borough, so it becomes its own group, Hub_308 (capacity 6,000 = f000283 alone).
  - The hub snapped 54.5 km to the nearest road node, which is outside the giant component.
  - The harness then erased the label: the only member is 54 km from the hub, so it counts as "remote" and cannot vote, and the hub falls back to "Northwest Arctic hub".

## How membership was recovered

No intermediate output records members. `02_hubs.gpkg` is never committed, and the exported nodes carry only `hub_id`, `deliv_meth` and `hub_cap`. Census TIGER places and the borough polygons are not committed either, and census.gov is blocked by this environment's network policy, so the tag step could not simply be rerun.

Instead I reran stages 01 and 01b's inputs exactly and recovered membership from three invariants of the code:

1. **Consolidation reproduces exactly.** Normalize → `consolidate_facilities` (unchanged code, profile params) gives 1,901 rows → 1,443 sites. The delivery-method fallback filled 44 sites by name and 3 by nearest; 47 stay blank and are dropped.
2. **Hub ID order is the order of each group's first site** in `ast_facility_id` sort order (`groupby(sort=False)`). Hub_1..12 match by hand: Juneau, Kasigluk, Fort Wainwright, Fairbanks, and so on.
3. **`hub_cap` is the exact sum of member capacities.** Members share one community string. An unlabelled site can join a named group only if it lies inside that place (enforced as within 30 km).

A dynamic-programming pass aligns hub IDs to opener sites, then integer programs fill each hub to its exact capacity, with geographic plausibility checks. Result:

- **385 exported hubs:** 376 high confidence (exact capacity, plausible geography). 4 have exact capacity but doubtful geography: Hub_40 and Hub_341 in Fairbanks, Hub_63, Hub_87. 5 are unresolved: Hub_1 Juneau and Hub_11 Anchorage are each short by one site; Hub_85, Hub_342 and Hub_345 are borough-fallback groups.
- **9 lost hub IDs:** members identified with medium confidence. The leftover named groups are Slana, Bettles Field, Coldfoot, Atmautluak, Fairbanks (one site), Elfin Cove and Petersburg, plus unlabelled sites.
- **7 sites removed by the cross-borough conflict drop.** Every one is a raw-flagged facility sitting inside another community's place: f000147, f000508, f001773, f001585, f000358, the Holy Cross stack and Point Baker SYN-55.
- **Caveats.** About 15 hub pairs break the ID-order rule, mostly where same-capacity sites can be swapped. Equal-capacity swaps inside one community cannot be told apart, but they don't affect any conclusion below.

Membership per facility is in `hub_membership_by_facility.csv`. Per-hub cause columns are in `hub_causes.csv`.

---

## Stage 1: raw AEA inventory

**Source check.** The CSV extracted from the data repo's `inputs/bulk_fuel_data.zip` has SHA-256 `132338fe…e1fb5e1`, and the regions zip has `bd51068e…bba0246c`. Both match `inputs/facility_sources/README.md`. `python build_facility_tables.py --check` reports **IDENTICAL** on all six tables. The `facilities` table is therefore an exact load. Every listed facility's raw lat/lon/community equals the database values, so no error was introduced by the loader.

**What the loader drops or invents:**
- **63 rows have no coordinates and are dropped** (3 of them have an ASTFacilityID; 25,000 gal). By community: Anchorage 9, Dillingham 5, Whittier 4, Naknek 3, St. Paul 3, and 1–2 each for Bethel, Cold Bay, Emmonak, Fairbanks, Kasigluk, Kotzebue, McGrath, Platinum, St. George, Adak, Aniak, Atka, Chignik, False Pass, Gambell, Kalskag, Kaltag, Kwethluk, Nightmute, Noorvik, Point Lay, Point McKenzie, Point Thomson, Portage Creek, Prudhoe Bay, Saint Michael, Selawik, Shishmaref, St. Mary's and White Mountain.
- **681 rows get synthetic IDs.**
- **No ASTFacilityID repeats**, so "keep the first row" never fires.

| Finding | Verdict | Evidence (raw CSV) |
|---|---|---|
| Unalaska ↔ Unalakleet swapped (f001606, f000147) | **Confirmed, source.** The coordinates are the swapped field. | Rows 1770 and 1756. Each label matches its CommunityID. 15 of 15 neighbours within 15 km of f001606 are Unalakleet. |
| f000283 Bethel, latitude 67.79558 | **Confirmed, source typo** | The 67→60 one-digit edit lands in Bethel. |
| f000120 Kodiak, latitude 54.85306 | **Confirmed, source typo** | The AEA feature geometry (X/Y) of the same row is 57.79468, -152.39286 (Kodiak). This beats the one-digit candidate 57.8531. |
| f000093 New Stuyahok, longitude -159.3748 | **Confirmed, source typo** | -157.3748 lands in New Stuyahok. |
| **New: f000268 Coldfoot, longitude -131.69972** | **Confirmed, source typo** | The point is in Yukon, Canada, and outside every AEA region. The row's own geometry gives 67.27808, -150.26877. It is the only one of 6 rows where geometry and lat/lon disagree that the first audit missed (single-site label, so no medoid test). |
| 4 possible typos: f000917, f000228, f000486, f000386 | **In the source; whether they are typos is unresolved** | Offsets are 4–55 km and the AEA geometry agrees with the stored values, so confirm with AEA. f000917 Delta Junction shares its erroneous spot with f001773 "Healy" (copied). |
| 13 other probable label errors | **Confirmed as stored in source; which field is wrong is decided case by case** | CommunityID always agrees with the label. 4 points duplicate another community's site within 50 m (copied coordinates: f001469, f000292, f000129, f001579). 9 are independent points whose label probably names the operator's home community (f000534, f000508, f001192, f000531, f001218, f000732, f001585, f000358, f001399). |
| 51 facilities on mixed-label stacks (5 named points) | **Confirmed, source** | Exact shared lat/lon across 2–6 communities. The 60.85686, -162.27653 point is in **Atmautluak**. |
| Same community spelled two ways | **Confirmed and widened: 8 CommunityIDs carry 2 names (30 facilities)** | Clark's Point/Clarks Point, Saint Mary's/Saint Marys, Saint George/…Island, Saint Paul/…Island, Bettles/Bettles Field, Naukati/Naukati Bay, Kalskag/Upper Kalskag, Dutch Harbor/Unalaska |
| 97 missing community names | **Confirmed, source** | None has a CommunityID either, so they can only be filled spatially. |
| 94 missing delivery methods | **Confirmed, source** | The data repo fills 47 from AEA `Fuel_Delivery_Method`; the harness fills none. |
| 3 outside every AEA region | **Confirmed.** 2 are typos (Coldfoot, Kodiak). | f000831 Haines (59.50, -136.45) sits at the BC border, which is plausible. |
| 57 far-from-label sites (40 isolated, 17 with split neighbours) | **Unresolved** | Many look like remote sites (camps, stations, airstrips) labelled with an administrative community. That can't be proven without fields we may not read. |

## Stage 2: hub aggregation (data repo)

| Finding | Verdict | Evidence |
|---|---|---|
| Labelled sites outside places bypass the conflict check and become one-site hubs | **Confirmed (R2)** | `tag.py` L110: `comparable = has_place & has_comm`. 26 one-site hubs consist only of a raw-flagged facility: Hub_62 Unalaska, Hub_308 Bethel, Hub_356 Prudhoe Bay, Hub_388 Craig (f000534), Hub_350 Livengood, Hub_111 Trapper Creek, Hub_347 Glennallen, Hub_358 Valdez, Hub_344 and Hub_346 "Fairbanks", Hub_353 Palmer, Hub_49 Wrangell (3 copied rows). |
| Cross-borough conflicts are silently dropped | **Confirmed** | 7 sites removed (listed above). The swap partner f000147 disappears instead of being corrected, and the stage only prints a count. |
| Communities split into several hubs | **Confirmed: key is `(community string, TIGER place, borough)` (R3)** | 64 labels → 158 hubs. Fairbanks has 11 exported plus 1 lost hub, all with build label "Fairbanks". Nine are within the city area, and the in-town ones are all mode `Road`. |
| Split caused by capacity-based grouping | **Rejected** | Capacity only drives `classify_hub_type` (Supplier/Receiver). There is no capacity-based grouping. |
| Split caused by mode | **Rejected** | `delivery_method` is not in `group_by`; modes are unioned. |
| Split caused by snapping | **Rejected as cause; snapping only moves hubs** | Snapping never splits a group. |
| Hubs moved by snapping | **Confirmed (R4)** | 52 hubs moved more than 10 km from their member centroid and 34 more than 25 km (Hub_308 Bethel 54.5 km, Cape Yakataga 140 km). There is no distance limit, and `snap_target` covers road and ice road only, so barge- or plane-only villages snap to any road. |
| Hubs lost to snap collisions | **Confirmed (R4)**. Members are medium confidence. | 9 missing hub IDs. `nodes_gdf.loc[ni, c] = row.get(c)` overwrites. Examples: Atmautluak was overwritten by phantom Hub_387 "Chefornak". The Slana group landed on Chistochina's node (Hub_309, which the harness then calls Slana). Petersburg f000228 (typo) and Coldfoot f000268 (typo; its centroid falls in Yukon) are both lost. |
| Copied-coordinate stacks merged across communities | **Confirmed (R5)** | 32 consolidated sites / 107 facilities. The label is the first CSV row's (`_first_notna`). Examples: Hub_278 "Atqasuk" absorbs the Kaktovik, Nuiqsut, Point Hope and Point Lay stack; Hub_225 "Kaltag" absorbs Koyukuk. |
| Unlabelled sites grouped per borough | **Confirmed (R6)** | 20 hubs; 11 spread more than 30 km. Hub_83 (4 unlabelled sites, 165 km) and Hub_294 (1 unlabelled site) have no community in the build. The harness names them Selawik and Palmer. |
| Region differs from facilities' region (1 hub) | **Explained by R4 and R6** | The snapped node lands in another AEA region. |

## Stage 3: facility-to-hub assignment and labels (harness)

| Finding | Verdict | Evidence |
|---|---|---|
| `hub_facility_map` links facilities to a hub other than the one they aggregated into | **Confirmed (R7)** | 121 of 1,624 high-confidence facilities (83 local, 38 remote); 136 of 1,729 including medium confidence. Mostly in split communities (a nearer sibling hub wins) and among unlabelled sites (37). Another 94 facilities belong to no surviving hub: 47 never built, 38 in lost hubs, 9 dropped. They are still mapped to the nearest hub. |
| Staging hub doesn't serve the facility's mode (48) | **Confirmed** | A mode-aware nearest rule changes those 48 rows and raises agreement with the true membership from 1,593 to 1,613 of 1,729. |
| Community-aware nearest rule | **Rejected as the main fix** | It changes 130 rows but agreement falls to 1,590, because split hubs share a label. |
| Hub labels differ from the build's community | **Confirmed (R8): 39 hubs** | **16 renamed:** Chistochina→Slana, Fritz Creek→Homer, Fort Wainwright→Seward, Fort Richardson→Anchorage, Birchwood→Eagle River, Juneau→Gustavus (Hub_345, membership unresolved), Valdez→Cordova, Port Moller→Nelson Lagoon, Napakiak→Kwethluk, Kalskag→Upper Kalskag, Delta Junction→**Healy** (a 1–1 tie won lexically by `key > best`), Kaltag→Koyukuk, Stevens Village→Arctic Village, Ketchikan→Petersburg, Chiniak→Kodiak, Chefornak→Atmautluak. **20 erased** because all members are more than 25 km away (e.g. Bethel Hub_308, Cape Yakataga, Cordova Hub_157). **3 unnamed groups named:** Palmer Hub_294, Ruby Hub_85, Selawik Hub_83. |
| Far-away labels (13 listed) | **Explained** | **10 come from the build** (R1+R2+R3): hubs of 1–3 sites whose label matches their own members — Unalaska Hub_62, Prudhoe Bay Hub_356, Fairbanks Hub_341 (membership doubtful) and Hub_346, Palmer Hub_161 (2 Palmer sites outside places, 29 km apart) and Hub_353, Livengood Hub_350, Craig Hub_388, Trapper Creek Hub_111, Haines Hub_360 (3 genuine Haines sites; f000831 near the BC border pulls it). **3 come from the harness** (R8): Healy Hub_120 (build label Delta Junction; one local Delta Junction site and one local Healy site, f001773, a copied point; "Healy" wins the 1–1 tie lexically), Palmer Hub_294 (one unlabelled site), Selawik Hub_83 (an unlabelled borough-fallback group). |

## Proposed fixes (not applied) and what each would fix

### Source corrections (`corrections_by_facility.csv`, 104 rows)
Key the file by facility id (both `facility_pid` and AEA `ASTFacilityID`/CSV row). Apply it **once, upstream**: the data repo's `00_normalize_raw.py` (or `io_readers.read_facilities_raw`), with the harness `build_facility_tables.build_tables` reading the same file, so both repos see identical positions.
- **High confidence: 4 typos and 22 spelling fixes.** The typos fix Bethel Hub_308, the Kodiak point in the Pacific, New Stuyahok, and the lost Coldfoot hub.
- **Medium-high: the Unalaska/Unalakleet swap.** Removes Hub_62 and restores f000147.
- **Medium: 51 stack members and 4 copied points** (moved to their own community's medoid), plus **9 relabels**.
- **For AEA to confirm: the 4 short-offset typos.**
- **Reach:** 41 hubs touched. 18 hubs consist entirely of corrected facilities and would move or disappear. 10 of the 39 harness label errors are removed at the source.

### Data repo (upstream `source_scripts/mmnet`, never `mmnet-toolkit/`)
1. **`steps/tag.py : assign_community_region`.** Run the conflict test for every labelled facility, using the borough of the point versus the borough of the labelled place, not only inside a place. Write conflicts to a reported table instead of silently dropping them. → about 26 one-site hubs (R2) plus the 7 silent drops.
2. **`steps/hubs.py : aggregate_hubs`** (with `profile.yaml hubs.group_by`). Group on a canonical community, `tag._canon` plus CommunityID, within the borough, and stop using the TIGER place as a split key. → 64 split labels / 158 hubs collapse to roughly 70. Fairbanks goes from 12 to 1–2.
3. **`steps/hubs.py`.** For unlabelled sites outside places, use the existing 5 km buffer-union path instead of one group per borough → 20 hubs (R6).
4. **`steps/consolidate.py : consolidate_facilities`.** Never merge rows with different community labels (cannot-link inside the 50 m clustering) → 32 mixed sites / 107 facilities (R5).
5. **`assemble.py : connect_multimodal`.** Detect two hubs on one node and merge or fail loudly instead of overwriting; record `snap_dist_m`; enforce the `max_snap_dist_m` the docstring promises → 9 lost hubs and 34 hubs moved more than 25 km (R4).
6. **`pipeline.run_pipeline` + `06_export_final_network.py`.** Export a `hub_members` table (`hub_id`, `ast_facility_id`, `community`) beside the nodes. This permanently closes the membership gap; nothing downstream would need to guess.

Fixes 2–6 change the network of record and need an owner-approved re-export (zips, checksums, `EXPECTED`, edge-keyed tables).

### Harness repo
1. **`build_facility_tables.py : build_tables`.** Apply the shared corrections file and log the 63 dropped rows. → the 104 corrections in `facilities`.
2. **`agentic_harness_workflow/build_hub_facility_map.py : build`.** Use exported membership when present (fixes 121–136 rows). Until then, use the mode-aware nearest hub (48 rows). Keep `last_mile`.
3. **`agentic_harness_workflow/label_network_concepts.py : _hub_communities`.** Take the community from build membership. Don't name unlabelled borough-fallback hubs after one nearby facility. Drop the lexical tie-break, and don't erase labels just because members are remote. → 39 hub labels.
4. Until membership is exported, `recover_hub_membership` (the reconstruction above) could ship as a checked tool, but option 6 above is the real fix.

## Files
- `corrections_by_facility.csv`: facility id, CSV row, field, current value, proposed value, evidence, confidence.
- `hub_membership_by_facility.csv`: per facility, its build site, the hub it aggregated into, confidence, current `hub_facility_map` hub, and mode-aware alternative.
- `hub_causes.csv`: per hub, build label vs harness label, members, snap distance, spread, raw-flagged members.
- `assignment_mismatches.csv`: the 121 high-confidence mismatches.
- `map1_coordinate_errors.png`, `map2_copied_coordinates.png`, `map3_fairbanks_split.png` (EPSG:3338) — in `../maps/`.

Archived 2026-10-09 under `docs/data_audit/` (see its README for the workbooks, maps, diagrams and
evidence that followed this report). The proposed fixes above were carried out: see
`docs/INVENTORY_QC_PLAN.md` decisions 1–12 and the phase table.
