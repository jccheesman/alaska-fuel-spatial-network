# Conventions for the 2026-11-17 cost derivation record

## Status tiers (what "ready" means, and how a figure that is not ready still works in the model)

Every rate and fee carries exactly one status. The model needs a number for every mode, so "not ready" never
means "no number": it means the number is carried with a weaker label and a wider range, and results that depend
on it are flagged.

| Tier | Meaning | Rule for the model |
|---|---|---|
| **Derived** | Three or more genuinely independent methods agree within about 3x, and their inputs were checked in the source documents. This is the skill's standard. | Apply the point and range. |
| **Provisional** | Evidence exists but falls short: fewer than three independent methods, or the methods agree on a total but not on its form. | Use the best estimate with its (wide) range, labelled provisional. A result that depends on it is reported with the range, not the point alone. |
| **Assumed** | No tariff, contract, invoice or usable price evidence. The figure is an engineering estimate or a carried-over value. | Keep the applied value (or the stated estimate) with a wide range, labelled assumed. Never change it on this evidence. Replace it when a source is found. |

## Input types (the "derived versus assumed" tables)

| Type | Meaning |
|---|---|
| **Quoted** | A number read from a source document. Give the document, the page and the exact words or table cell. |
| **Computed** | Arithmetic on quoted inputs only (unit conversion, inflation, division by a distance). Show the inputs. |
| **Measured** | Read from the project's own data: network miles, hub positions, the FY2025 price table decoded from the PCE report. Say which table. |
| **Assumed** | Not in any source: a payload, a speed, a dollar year the source does not state, a share, an origin port, a judgement between two readings. Say who chose it and what happens if it is wrong. |
| **Owner decision** | Chosen by the owner (JC). Give the date. |

## References

Name the local document by its file name under `cost_derivation_resources/` and the page. Give the public link
when `DOWNLOAD_LIST.md` or the chapter has one. Do not invent a link.
