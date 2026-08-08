# research/ — decision records behind the engine's rules

Eight tracked sandboxes, one per design question the network build had to
answer. Each contains numbered scripts + a FINDINGS.md (the decision record);
their conclusions are already PORTED into the engine/profile — these folders
are the evidence, not live pipeline. Generated `out/` dirs are gitignored.

| Sandbox | Question it answered | Where the rule landed |
|---|---|---|
| `road_road_connect/` | When may two road components weld? | profile `bridges` (road↔road, 3 km) |
| `ice_ice_connect/` | Ice↔ice welds | profile `bridges` |
| `road_ice_connect/` | Ice↔road bridging + North Slope options | profile `bridges` + connect-to-giant |
| `waterway_network/` | Full-Alaska marine network extraction | `01_prep_waterway.py` (README here predates it — see FINDINGS.md) |
| `flights_network/` | Which air data is trustworthy | official AK DOT&PF swap (`inputs/air/`) |
| `airport_connection/` | How airports attach (snap vs transfer) | `build._snap_airways_to_road` |
| `multimodal_network/` | Air's role in connectivity | `inspect.mode_contribution` |
| `param_check/` | Are the profile tolerances plausible? | profile tolerance values |
