# gateway_drops_unlisted_communities

**Looks like:** the ACEP/UAF Alaska Energy Data Gateway `public_bulk_fuel.csv` (CC-BY-4.0) has no rows
for Haines, Eagle River, Fort Wainwright, Fort Richardson, Chugiak, Girdwood, Cape Yakataga and
others, and none of the 97 unlabelled records.

**Why:** the gateway build joins the inventory to its own canonical community list and drops
records whose community is not on it (~130). It also adds 295 AEA-2024 assessment rows with no ids
that may duplicate older farm rows, and places some records at community points rather than tank
positions.

**Handled by:** owner decision 2026-10-06 — the gateway file is **evidence only** (used by the
`public_says` check and the `external_disagrees` detector when present), never merged. Its canonical
names informed `aliases.csv`.
