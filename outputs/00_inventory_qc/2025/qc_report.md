# Inventory QC report — release 2025

Generated 2026-10-08T22:15:25+00:00 by workflows/00_inventory_qc/07_publish.py

- raw release: `Utilities_Bulk_Fuel_Inventory.csv` sha256 `3fbee569c63dccf813d6fa53e608820d53b92e415feb2c7f20556fc0bb0c30b0` (1830 rows, 1767 located)
- clean table: `facilities_clean.csv` sha256 `bddfaabf00edf1a95bf57c315bb196204df26a977744998ac7cedc7addba6a81` (1803 rows, 1740 located)
- excluded: 27 (see `excluded.csv`)
- corrections: 80 applied · 8 pending · 0 rejected · 0 skipped
- community keys: 272 · unlabelled records: 97
- qc_status: 1768 clean · 35 pending_review (withheld from hubs by the build)

## Checks

| check | result | detail |
|---|---|---|
| no undeclared derived column was produced by a stage | PASS | undeclared=[] (declare it in inputs/inventory_qc/derived_columns.csv) |
| row reconciliation | PASS | 1830 release = 1803 clean + 27 excluded |
| every exclusion has a reason | PASS | 27 excluded |
| every applied correction has reviewer + date | PASS | 80 applied |
| only schema + derived columns; no contact columns | PASS | extra=[] contact=[] |
| every declared derived column is present (derived_columns.csv) | PASS | missing=[] |
| fixture: Bethel record f000283 is not above 66°N | PASS |  |
| fixture: no Unalaska-labelled record sits on Norton Sound (lat > 60) | PASS |  |
| fixture: no Unalakleet-labelled record sits in the Aleutians (lat < 60) | PASS |  |
| fixture: no Kodiak-labelled record is in the open Pacific (lat < 56) | PASS |  |
| fixture: no Coldfoot-labelled record is in Yukon, Canada (lon > -141) | PASS |  |
| fixture: spelling variants resolved (no 'Saint Marys', 'Clarks Point', 'Dutch Harbor' labels) | PASS |  |
| deterministic output | PASS | bddfaabf00ed |

## Corrections applied

| record_id | field | old | new | reviewer | date |
|---|---|---|---|---|---|
| `{5AEE4579-120C-418C-965A-911EFB7A4873}` | latitude | 54.853056 | 57.794680 | JC | 2026-10-05 |
| `{5AEE4579-120C-418C-965A-911EFB7A4873}` | longitude | -152.39288 | -152.392880 | JC | 2026-10-05 |
| `{D0D325AD-A296-437B-9213-8A2FD2F3621D}` | latitude | 67.252778 | 67.278080 | JC | 2026-10-06 |
| `{D0D325AD-A296-437B-9213-8A2FD2F3621D}` | longitude | -131.699722 | -150.268770 | JC | 2026-10-06 |
| `{8D408F52-5CE0-4A95-A586-79D54041D7C7}` | latitude | 67.79558 | 60.795580 | JC | 2026-10-07 |
| `{8D408F52-5CE0-4A95-A586-79D54041D7C7}` | longitude | -161.7611 | -161.761100 | JC | 2026-10-07 |
| `{978F2CF3-F873-42E9-A4F4-4744D455FBA9}` | latitude | 59.4571 | 59.457100 | JC | 2026-10-08 |
| `{978F2CF3-F873-42E9-A4F4-4744D455FBA9}` | longitude | -159.3748 | -157.374800 | JC | 2026-10-08 |
| `{A5E8D42A-4A72-4380-B9D4-5CC0084B55D2}` | latitude | 63.89194 | 53.882740 | JC | 2026-10-05 |
| `{A5E8D42A-4A72-4380-B9D4-5CC0084B55D2}` | longitude | -160.6842 | -166.550742 | JC | 2026-10-05 |
| `{621FCC2F-3A90-426E-A211-00250864F71E}` | latitude | 53.88274 | 63.891940 | JC | 2026-10-05 |
| `{621FCC2F-3A90-426E-A211-00250864F71E}` | longitude | -166.550742 | -160.684200 | JC | 2026-10-05 |
| `{B15A52C6-6F30-470D-9BA8-5037E9F1F1EC}` | community_name | Eielson Afb | Anchorage | JC | 2026-10-05 |
| `{BFC59C95-ABE4-4959-BE52-7F09A5308991}` | community_name | Fairbanks | Fort Yukon | JC | 2026-10-05 |
| `{BDC6AEBD-A6BF-4D0C-929B-36D15018837C}` | community_name | Fort Wainwright | Seward | JC | 2026-10-05 |
| `{BACAEA02-40B4-467A-B3B9-39C3197CF50D}` | community_name | King Cove | King Salmon | JC | 2026-10-05 |
| `{EE49D47C-9B92-431B-9D0B-77844BA21CF8}` | community_name | Stevens Village | Arctic Village | JC | 2026-10-05 |
| `{835A9532-B50F-4307-8766-44E644F988D9}` | latitude | 64.856066 | 60.678540 | JC | 2026-10-05 |
| `{835A9532-B50F-4307-8766-44E644F988D9}` | longitude | -147.802751 | -151.380010 | JC | 2026-10-05 |
| `{6D4B4A33-4BA6-4F24-B682-8F598BC19947}` | latitude | 66.54924307 | 55.550680 | JC | 2026-10-05 |
| `{6D4B4A33-4BA6-4F24-B682-8F598BC19947}` | longitude | -152.6327214 | -133.096710 | JC | 2026-10-05 |
| `{60E9F7B5-8A63-4781-81E6-69A693BAD37D}` | community_name | Clarks Point | Clark's Point | JC | nan |
| `{4BEF8811-2274-4D00-AC1C-998D040903CB}` | community_name | Clarks Point | Clark's Point | JC | nan |
| `{14E28DA5-69A4-4D2F-BB92-286834F0B46F}` | community_name | Saint Marys | Saint Mary's | JC | nan |
| `{E7455FE8-21D1-4DB9-B9A2-3E131F07722C}` | community_name | Saint Marys | Saint Mary's | JC | nan |
| `{FB96C24B-7E2D-41A4-BB41-17A5FC20670F}` | community_name | Saint Marys | Saint Mary's | JC | nan |
| `{D74EF297-A73B-4181-A759-56C37FDE41DF}` | community_name | Saint Marys | Saint Mary's | JC | nan |
| `{8AD14672-6D41-4612-9C63-B8526F36290D}` | community_name | Saint Marys | Saint Mary's | JC | nan |
| `{15B249BC-700E-47F6-A75F-F39B21D66AD6}` | community_name | Saint George Island | Saint George | JC | nan |
| `{9F3D036A-E04E-431E-919E-5677FE81308D}` | community_name | Saint George Island | Saint George | JC | nan |
| `{1FF8EE87-BBCC-416D-9B93-4AE5B2704310}` | community_name | Saint George Island | Saint George | JC | nan |
| `{569725C5-F6E9-4B28-96C7-8BDF5BCB6C06}` | community_name | Saint Paul Island | Saint Paul | JC | nan |
| `{66E08F69-68FD-40AD-99B3-7A2007C0697D}` | community_name | Saint Paul Island | Saint Paul | JC | nan |
| `{7AFEC631-2122-4F7A-AA44-2584FAFBC1D0}` | community_name | Saint Paul Island | Saint Paul | JC | nan |
| `{8D19934A-76B9-4669-B600-BFECB43DCCF3}` | community_name | Saint Paul Island | Saint Paul | JC | nan |
| `{52B7BAA3-AC93-4AF7-8E9A-0DEEE954C6EE}` | community_name | Saint Paul Island | Saint Paul | JC | nan |
| `{C2EE3D68-85C8-4D15-8DCF-735AE274FD08}` | community_name | Saint Paul Island | Saint Paul | JC | nan |
| `{4F994E16-6208-479F-B3B2-22194B179F84}` | community_name | Bettles | Bettles Field | JC | nan |
| `{086531C1-92F4-4C8B-95C4-BA197AAAD587}` | community_name | Bettles | Bettles Field | JC | nan |
| `{DFFEA010-C78E-4C70-A5A9-0089FFA544FA}` | community_name | Bettles | Bettles Field | JC | nan |
| `{0C5BEC21-0D02-4217-BB25-11C53F2A57C2}` | community_name | Bettles | Bettles Field | JC | nan |
| `{95BA79A7-EECB-4B9D-8F6C-82D0C48A0838}` | community_name | Bettles | Bettles Field | JC | nan |
| `{A530462C-BE7E-4917-B358-72FCC00AFB68}` | community_name | Naukati | Naukati Bay | JC | nan |
| `{114FF0DE-E8A1-487F-8505-67999F6000EC}` | community_name | Kalskag | Upper Kalskag | JC | nan |
| `{013ABDFD-DB31-4E01-B9E3-9FF760C2BB05}` | community_name | Kalskag | Upper Kalskag | JC | nan |
| `{6B2DF7B5-09D6-4DC1-81C3-144F567B9178}` | community_name | Kalskag | Upper Kalskag | JC | nan |
| `{41C39C16-6197-4AF1-A699-E8B804A72331}` | community_name | Kalskag | Upper Kalskag | JC | nan |
| `{488BFE21-36C1-4EF2-9D43-1DE0A36534D0}` | community_name | Dutch Harbor | Unalaska | JC | nan |
| `{8911BFBD-59A5-485A-86C4-7EA6C3180F66}` | community_name | Dutch Harbor | Unalaska | JC | nan |
| `{7D987B23-D133-42DE-B929-973C9C816886}` | community_name | Dutch Harbor | Unalaska | JC | nan |
| `{F1376769-3624-43A5-9248-CADA5B67B566}` | community_name | Dutch Harbor | Unalaska | JC | nan |
| `{39943186-EB34-4A7C-B510-E1F60F6E5B77}` | community_name | Nightmute | Iliamna | JC | 2026-10-06 |
| `{E8C7FE98-2833-47DB-A566-8D25750D48D2}` | community_name | Napakiak | Kwethluk | JC | 2026-10-06 |
| `{3EDD2A9C-65E1-4B69-95C6-B86EF44C2A59}` | exclude | tank_farm_id=108 | true | JC | 2026-10-08 |
| `{405CC19C-36AB-4808-8AB1-CDE994AED352}` | exclude | tank_farm_id=108 | true | JC | 2026-10-08 |
| `{A6656A06-FB6E-44F6-8DEB-0A79C30970C9}` | exclude | tank_farm_id=108 | true | JC | 2026-10-08 |
| `{29A9858B-A138-476A-942F-BA787BE7179B}` | exclude | tank_farm_id=1087 | true | JC | 2026-10-08 |
| `{32E46B3B-A68A-4AED-A995-44AABFBA609D}` | exclude | tank_farm_id=1087 | true | JC | 2026-10-08 |
| `{678A81B7-2420-44FE-AABF-C45E6E48CC82}` | exclude | tank_farm_id=1095 | true | JC | 2026-10-08 |
| `{EE035FC2-70D9-42A6-B940-D1F97F642616}` | exclude | tank_farm_id=1095 | true | JC | 2026-10-08 |
| `{D16B7CA0-CE7A-4D65-864E-5B2599DECFA6}` | exclude | tank_farm_id=158 | true | JC | 2026-10-08 |
| `{5283F15A-66DA-4487-8444-EC1A2C43934D}` | exclude | tank_farm_id=171 | true | JC | 2026-10-08 |
| `{4EB90598-665E-44BF-BABD-1D75C638BCF2}` | exclude | tank_farm_id=219 | true | JC | 2026-10-08 |
| `{60EDEA84-04E5-4ED4-912D-1CDA85E970A2}` | exclude | tank_farm_id=377 | true | JC | 2026-10-08 |
| `{6EF0C04D-FA10-46F4-A9C4-91EC73504366}` | exclude | tank_farm_id=377 | true | JC | 2026-10-08 |
| `{743459E3-FCB1-4860-9E07-61BE3B6A04B3}` | exclude | tank_farm_id=377 | true | JC | 2026-10-08 |
| `{C558007A-A0AB-4C4D-A836-9CA4EA3BD493}` | exclude | tank_farm_id=377 | true | JC | 2026-10-08 |
| `{F3C6E0AA-DC43-46B0-9BBD-B22D1A9461DF}` | exclude | tank_farm_id=377 | true | JC | 2026-10-08 |
| `{5966569A-E364-492E-AF3E-4EE7DCE3828B}` | exclude | tank_farm_id=385 | true | JC | 2026-10-08 |
| `{63C660C1-0960-4011-81E0-33F443CB730D}` | exclude | tank_farm_id=385 | true | JC | 2026-10-08 |
| `{BA9A56A1-5224-45F0-B0DD-070DBFFB2559}` | exclude | tank_farm_id=385 | true | JC | 2026-10-08 |
| `{D87C846D-981B-4E88-AB27-A2DDBF25E98C}` | exclude | tank_farm_id=385 | true | JC | 2026-10-08 |
| `{11C61E2B-C979-4D51-A901-5BDF8ABBF907}` | exclude | tank_farm_id=397 | true | JC | 2026-10-08 |
| `{52EA8B6C-5DEE-4586-9B19-043A22000B12}` | exclude | tank_farm_id=403 | true | JC | 2026-10-08 |
| `{41F25397-8168-4A24-BE43-C7E6935BB5AB}` | exclude | tank_farm_id=408 | true | JC | 2026-10-08 |
| `{2A288E05-E61D-4E46-AE4D-C7D9102802EA}` | exclude | tank_farm_id=410 | true | JC | 2026-10-08 |
| `{C8EC9D39-F5C7-4B8E-94A5-4B7BE891EF44}` | exclude | tank_farm_id=565 | true | JC | 2026-10-08 |
| `{4533136B-B178-4EEB-8F4E-1BBF21C03ABE}` | exclude | tank_farm_id=621 | true | JC | 2026-10-08 |
| `{3758A00D-FA89-45EA-85FB-DE30F19E5DBC}` | exclude | tank_farm_id=706 | true | JC | 2026-10-08 |
| `{83F3B425-DC65-4A0B-94B5-14D3D08E5901}` | exclude | tank_farm_id=830 | true | JC | 2026-10-08 |
