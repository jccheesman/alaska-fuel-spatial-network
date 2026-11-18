# Summary of the November 2026 cost re-derivation

**Nothing below is applied.** `friction_costs.py` in the data repo is unchanged. This is the summary of the
November 2026 re-derivation; the detail is in `docs/cost_derivation/2026-11/` and the history in
`DECISION_LOG.md`.

### Result by rate

| Rate or fee | Applied today | Re-derived | Range | Status | Key sources (`docs/cost_derivation/2026-11/SOURCES.md`) |
|---|---|---|---|---|---|
| Ocean line-haul barge, per gallon-mile | 0.0010 (blended) | 0.00021 | 0.00013 to 0.00028 | Derived | S02, S04, S05 |
| Coastal small barge to a village | 0.0010 (blended) | $0.45 per delivery + 0.0010 per mile | all-in 0.40 to 1.21 per delivery | Provisional | S02, S15, S03 |
| River barge | 0.0010 (blended) | $0.50 per delivery + 0.0013 per channel mile | fixed 0.20 to 0.80; per mile 0.0009 to 0.0044 | Provisional | S03, S01, S02, S15 |
| Road, per gallon-mile | 0.0007 | 0.0007 (confirmed) | 0.00055 to 0.0011 | Derived | S04, S13, S35 |
| Plane, per gallon-mile | 0.025 | 0.016 | 0.013 to 0.024 | Provisional | S03, S02, S01, S15 |
| Ice road, per gallon-mile | 0.010 | keep 0.010 | applied 0.004 to 0.025; the evidence spans 0.006 to 0.030 | Assumed | S24, S15, S25, S13 |
| Barge to overland fee | 0.24 at every crossing | by place: origin port 0.01, remote hub 0.12, village landing 0.046 or zero | see chapter 05 | Provisional | S09, S07, S08, S02, S12 |
| Barge to ice road, overland to ice road, plane to overland fees | 0.011, 0.022, 0.025 | unchanged | | Assumed | none (no source prices these events) |

Status meanings (`docs/cost_derivation/2026-11/CONVENTIONS.md`): **Derived** meets the three-method standard; **Provisional**
is the best estimate on evidence that falls short, carried with a wide range; **Assumed** has no source evidence
and keeps the applied value. The model has a number for every mode in all three cases; the label says how far to
trust it. One headline status per rate was set when the record was assembled; where a part of a rate is weaker
than the headline, the full addendum says so.

### Assembly rules (the assistant's proposal, for the owner to confirm; not derived)

These settle the overlaps between the per-segment results, so that no handling is billed twice or dropped.

1. **Village landing fee is zero wherever a delivery charge is applied.** The coastal $0.45 and the river $0.50
   fixed parts already include discharge at the village. The $0.046 village figure applies only in a design with
   no delivery charge.
2. **The river delivery charge must be carried explicitly if the 0.24 fees are cut.** On Nenana routes today the
   two 0.24 fees ($0.48) happen to stand in for the river fixed part. Cutting them without adding the delivery
   charge would drop about $0.44 to $0.50 per gallon from every river haul.
3. **Hub discharge is billed once**, at the remote hub, and not again at the origin or the village.
4. **No fixed part on the ocean rate.** If a two-part ocean form is ever wanted, the matched pair is $0.06 per
   voyage with 0.00017 per mile, never a fixed part on top of 0.00021.

### What applying it depends on

- **A marine or river class for every waterway edge** and a type for every barge landing (road-system port,
  line-haul or dock-served port, coastal village, river village). The data repo's marine / river water label is
  being built for this. The landing classes still need a reviewed rule.
- **Southeast Alaska.** The coastal figure describes seasonal lighterage in Western and Northern Alaska. Ice-free,
  dock-served towns (Ketchikan, Sitka, Klawock) show $0.12 to $0.34 and belong in the dock-served class.
- **One change to the network of record:** rates, fees, the edge classes and any new barge links together, then one
  workflow 03 rerun, one export, one harness adoption and regenerated reference answers.

### Open

- A second independent review of the three verdicts that overturn applied values (plane, the 0.24 fee, 0.011).
- Evidence gaps per addendum; the source search prompt is in `harness: blind_derivations/working_2026-11-17/GEMINI_SOURCE_SEARCH_PROMPT.md`.
- Errata in this and the other chapters: `docs/cost_derivation/2026-11/errata.md` (seven reported defects confirmed, fifteen
  more found). Touching this chapter: F2, F6, F7. Corrections owed in the data repo at the next edit of the cost
  file: items 5a, 5b, 6, 7, F9, F12, F13.

### Second batch of sources (2026-11-18): no status changed

Nine more documents were read in full and the four affected segments were re-derived blind and checked
(`docs/cost_derivation/2026-11/supplement_*_2026-11-18.md`). None supplies a tariff, contract or invoice for moving fuel.

| Segment | What the new documents gave | Effect |
|---|---|---|
| Plane | Two carriers' published air cargo rates per pound (2026). One is the page the plane chapter already used. | A loose ceiling ($5.68 to $8.07 per gallon to Allakaket, against the existing ceiling of $3.48 to $3.70). Provisional, 0.016, unchanged. |
| Ice road | A 2014 estimate of $450 to $600 per cubic yard to haul gravel from Utqiagvik to Atqasuk by ice road. | About 0.027 per gallon-mile if fuel moved the same way, on four assumed inputs: a consistency check on the sled regime (0.026), not a method. Assumed, 0.010, unchanged. |
| Coastal small barge | A construction barging rate of $12,000 to $15,000 per day (about 2008); a 2006 group purchase price for seven Norton Sound villages. | The day rate is 1.2 to 1.5 times the vessel-day cost already used. Provisional, unchanged. |
| River barge | The same day rate; sailings per season by river reach; draft limits. | Brackets the day cost already used. The load per sailing, which decides the per-mile part (0.0014 or 0.0035), is in no document. Provisional, unchanged. | S03, S01, S02, S15 |
