# aea_shared_tank_farm_ids

**Looks like:** several records on one exact coordinate, each labelled with a different community
(e.g. 60.85686, -162.27653 carries Chefornak, Kipnuk, Nightmute, Tuntutuliak and Tununak). The data
repo's 50 m consolidation merged each stack into one site named after the first CSV row, which is how
a "Chefornak" hub came to sit in Atmautluak and overwrite the real Atmautluak hub.

**Why:** every AEA-sourced record (no `ASTFacilityID`) takes its coordinates, `Total_Capacity`,
evaluation id, delivery method and inspection date from its `Tank_Farm_ID`; 21 farm ids (2022) carry
records from 2–6 communities. Only the community name/id differs, so the label is the record's own
data and the position/capacity were borrowed from the wrong farm. AEA's Dec-2025 release moved three
of these records (Hooper Bay, Noorvik, Point Lay) into their labelled communities, supporting that
reading. Six farms (179 Ambler, 415 Buckland, 621 Iliamna, 694 Brevig Mission, 710 Atmautluak,
830 Kwethluk) have NO correctly-labelled row at all.

**Handled by:** `04_detect.py::shared_farm_id` (names the farm's own record or `NONE`);
corrections.csv relabels one row per orphan farm (Nightmute→Iliamna, Napakiak→Kwethluk approved
2026-10-06; the other four pending); the remaining rows are open in the review queue (move to own
community with capacity unknown, or drop). Ask AEA to correct the `Tank_Farm_ID` on these records.
