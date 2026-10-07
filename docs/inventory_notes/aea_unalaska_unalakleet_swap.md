# aea_unalaska_unalakleet_swap

**Looks like:** a record labelled Unalaska at 63.89194, -160.68420 (Unalakleet, Norton Sound) and a
record labelled Unalakleet at 53.88274, -166.55074 (Dutch Harbor). Produced the hub `Hub_62`
"Unalaska" on Norton Sound in the 2026-09-29 network-of-record.

**Why:** the two rows' coordinates are swapped; each row's `CommunityID` matches its label, so the
positions are the wrong field, not the names. Still present in AEA's 2025 release and in the ACEP
gateway file.

**Handled by:** corrections.csv (both rows approved 2026-10-05, coordinates swapped back);
`07_publish.py` regression fixtures keep it fixed.
