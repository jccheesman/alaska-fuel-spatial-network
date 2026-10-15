# Stage 03 — multimodal network: connectivity report

- nodes / edges: **84,089** / **92,900**
- components: **55**  ·  giant: **98.9%** (83,182 nodes)
- fuel hubs reachable: **245/271** (90.4%)

### Per-mode reachability (share of each mode's nodes in the giant)

| mode | nodes | in giant | % |
| --- | --- | --- | --- |
| Road | 48,955 | 48,091 | 98.2% |
| Air | 151 | 151 | 100.0% |
| IceRoad | 931 | 888 | 95.4% |
| Waterway | 34,133 | 34,133 | 100.0% |

### Marginal contribution of the Air mode (with vs without)

| metric | without | with |
| --- | --- | --- |
| components | 173 | 55 |
| giant nodes | 81,555 | 83,182 |
| fuel hubs in giant | 207 | 245 |

- **1,627 nodes (38 fuel hubs)** reach the giant ONLY via Air.

## Feedback

<!-- FEEDBACK:START (your notes below are preserved on re-run) -->

**Observations:** _what does the output show? (counts, distributions, geometry, anything off)_

**Decision:** _keep as-is / change a parameter / change the method / change the data_

**Improvement for the agent:** _the concrete change the methodology should adopt (which step, which param/function, what to do differently)_
<!-- FEEDBACK:END -->
