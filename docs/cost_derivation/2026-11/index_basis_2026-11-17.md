# Index basis for the 2026-11-17 record (owner decision: use the downloaded data)

**Convention.** All dollars are restated to 2026 with CPI-U, US city average, all items, not seasonally adjusted
(1982-84 = 100). The 2026 value is the **January-September 2026 average, 332.243** (9 months), from the
downloaded series. This replaces the toolkit's projected 330.0 (difference +0.68%) and the
search-corroborated 332.769 used as a sensitivity in the working files.

**Source of the series.** `shared/cpi/cpiai_datahub_mirror.csv`, downloaded 2026-11-17 from the public
`datasets/cpi-us` mirror of the BLS series (https://github.com/datasets/cpi-us, file `data/cpiai.csv`). Its annual
averages match the values already used in the project (2007 207.342, 2010 218.056, 2022 292.655, 2024 313.689). It is
a mirror, not the BLS table itself; replace it with the BLS download (series CUUR0000SA0) when the owner has it.
2025 has 11 months in the series (October 2025 was not published).

**How to restate a figure.** value_2026 = value_source_year x factor(source year). A figure the working files give
at the 330.0 basis is multiplied by 1.00680. Tariff figures that are 2026 actuals are NOT inflated.

| Source year | CPI-U annual average | months | factor to 2026 (332.243) |
|---|---|---|---|
| 2003 | 183.958 | 12 | x1.8061 |
| 2004 | 188.883 | 12 | x1.7590 |
| 2005 | 195.292 | 12 | x1.7013 |
| 2006 | 201.592 | 12 | x1.6481 |
| 2007 | 207.342 | 12 | x1.6024 |
| 2008 | 215.303 | 12 | x1.5431 |
| 2009 | 214.537 | 12 | x1.5486 |
| 2010 | 218.056 | 12 | x1.5237 |
| 2011 | 224.939 | 12 | x1.4770 |
| 2012 | 229.594 | 12 | x1.4471 |
| 2013 | 232.957 | 12 | x1.4262 |
| 2014 | 236.736 | 12 | x1.4034 |
| 2015 | 237.017 | 12 | x1.4018 |
| 2016 | 240.007 | 12 | x1.3843 |
| 2017 | 245.120 | 12 | x1.3554 |
| 2018 | 251.107 | 12 | x1.3231 |
| 2019 | 255.657 | 12 | x1.2996 |
| 2020 | 258.811 | 12 | x1.2837 |
| 2021 | 270.970 | 12 | x1.2261 |
| 2022 | 292.655 | 12 | x1.1353 |
| 2023 | 304.702 | 12 | x1.0904 |
| 2024 | 313.689 | 12 | x1.0591 |
| 2025 | 321.943 | 11 | x1.0320 |

**Marine freight indexes (sensitivity only, never the base case).** BLS producer price indexes from the owner's
downloaded FRED files (`pdf_text/PCU483113483113.csv` coastal and Great Lakes freight, `PCU483211483211.csv` inland
water freight, `PCU483111483111.csv` deep sea freight). Factors to the 2026 January-October average are in
`shared/inflation_factors.md`: coastal 2010 x1.749, 2007 x1.971, 2005 x2.335, 2022 x1.273; inland 2010 x1.419,
2007 x1.658. Whether Alaska tug-and-barge trade is inside the coastal series is not established.
