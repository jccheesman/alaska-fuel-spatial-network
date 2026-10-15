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

**Handled by:** `04_detect.py::shared_farm_id` (names the farm's own record or `NONE`).
**Owner rule (2026-10-08):** a farm whose own record matches its coordinates + community keeps that
row; the other rows on the id, which repeat the farm's position and `total_capacity`, are copies and
are excluded (`corrections.csv`, `field=exclude`, guarded by `old_value=tank_farm_id=<id>` so an
AEA fix that re-keys a row retires the drop). 16 farms resolved this way (27 rows excluded, 2025).
A farm with no matching row has no clear winner and stays in the decision queue: farms 179 (Wales /
Holy Cross), 415 (Selawik / Kiana), 694 (Teller / Saint Michael / Savoonga), 710 (Chefornak /
Kipnuk / Tuntutuliak / Nightmute / Tununak) — 12 rows. Earlier relabels Nightmute→Iliamna and
Napakiak→Kwethluk (2026-10-06) gave farms 621 and 830 their own record. Ask AEA to correct the
`Tank_Farm_ID` on the orphan rows; the excluded communities' farms exist but have no usable record
until then.
