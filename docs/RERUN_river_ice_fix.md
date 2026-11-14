# Re-running after the river-ice / marine-leak fix

What changed, in one line: **river ice may now only gate cells that are
actually rivers, may only be extrapolated 25 km, falls back to a k-nearest
median beyond that — and the upstream arcpy stage no longer invents p_ice = 0
for cells it could not measure.**

Diagnosis, measurements and the failed first attempt at tier 3 are in
`docs/TEST_LOG.md` (2026-08-20); the arcpy truncation defect is the 2026-08-21
entry there and `docs/FINDING_eucallocation_truncation.md`. This document is
the operational half: what to run, in what order, and what each guard protects
so none of it gets removed by accident later.

## Status

| | |
|---|---|
| Track A (Python) | **applied and verified**, 2026-08-20 |
| Track B (ArcGIS) | **applied to source 2026-08-21, not yet run** — needs the ArcGIS machine |
| Regression gate | `qa_friction_stack.check_year_round_ports` — passing |

Track B stopped being optional on 2026-08-21. It now carries a correctness fix
— the `EucAllocation` truncation — not just data hygiene.

Files carrying the fix:

```
source_scripts/friction_surface/friction_paths.py          WATERWAY_RIVER_MASK_TIF
source_scripts/friction_surface/friction_config.py         RIVER_SEGMENT_*, RIVER_ICE_FILL_MAX_KM,
                                                           RIVER_ICE_FALLBACK_K
source_scripts/friction_surface/friction_surface.py        the three-tier gate
source_scripts/friction_surface/qa/qa_friction_stack.py    check_year_round_ports
source_scripts/friction_surface/friction_preprocessing/
    build_brown_polygon_mask.py                            marine clip on the NHDArea join
    river_ice_full_pipeline.py                             EucAllocation stage removed (arcpy)
workflows/01_friction_build/01_build_corridor_masks.py     emits the river mask
diagnostics/01_friction_build/plot_river_ice_marine_leak.py   diagnostic figure
```

---

## Before you start: checkpoint

The rasters are expensive and not in git.

```bash
cd "$REPO"
git status --short && git rev-parse --short HEAD
cp -R outputs/01_friction_build outputs/01_friction_build.bak_preclip
cp -R inputs/friction_rasters/river_ice inputs/friction_rasters/river_ice.bak_preclip
```

Rollback is at the bottom.

---

## Track A — downstream (Python only, ~1–2 h)

The load-bearing fix. Works against the river-ice rasters you already have,
leak and all, because the gate is clipped to the river mask.

### A1. Build both corridor masks

```bash
python workflows/01_friction_build/01_build_corridor_masks.py
```

Writes `waterway_mask_150m.tif` (unchanged) and `waterway_river_mask_150m.tif`
(new — 24 reviewed NWN segments, 86,789 cells, 1.67 MB). Expect:

```
[waterway] river/marine split: 24 of 320 features are freshwater rivers (...);
4 candidate(s) rejected on review
```

**If it raises instead**, the drift detector has fired — the NWN extract no
longer matches the reviewed allowlist. Re-audit `RIVER_SEGMENT_KEY_IDS` /
`RIVER_SEGMENT_REJECTED` in `friction_config` against the new file. Do not work
around it: an unreviewed river/marine split is what caused the bug.

### A2. Rebuild the friction stack

```bash
python workflows/01_friction_build/02_build_friction_stack.py
```

Two new log lines. Per run:

```
river/marine split: 86,789 of 501,684 waterway cells (17.3%) are freshwater
river and river-ice gated; the other 414,895 are salt water and sea-ice gated
```

Per month:

```
month 02 river ice: 77,657 IDW / 4,734 nearest-filled / 4,398 k-nearest-median
```

Those three tiers should roughly match 89.5% / 5.5% / 5.1%. A tier-3 count far
above ~4,400 means the cap is rejecting more than expected; a tier-1 count near
68,000 means you are running against a flowline-only river-ice mask.

Runtime is unchanged — the KD-tree now has a distance bound, if anything
slightly faster.

### A3. QA

```bash
python workflows/01_friction_build/03_qa_friction_stack.py
```

Check 2 must pass:

```
[OK]   year-round ports
year-round ports OK: all 8 Gulf/SE ports navigable in 12/12 months
seasonal sites OK: ... open in August, closed in February
```

Run against the pre-fix stack it reports 8 failures (Ketchikan, Sitka, Juneau,
Petersburg, Kodiak, Seward, Valdez, Whittier). That is the regression it exists
to catch, and a useful before/after check.

**Egegik is the one to watch.** No IDW coverage and no covered cell within
25 km, so it can only be reached by tier 3. If Egegik opens in February, tier 3
returned zero.

### A4. Diagnostic figure (optional, worth it)

```bash
python diagnostics/01_friction_build/plot_river_ice_marine_leak.py
```

On a correct stack the red "river-ice leak" class is **empty**. Pre-fix it held
288,954 cells. Clearest single check that the fix took.

### A5. Re-weight the network and rebuild downstream

```bash
bash workflows/03_multimodal_join/run_all.sh
bash workflows/04_duckdb_export/run_all.sh
```

Workflow 02 does **not** need re-running — the network geometry is unchanged,
only the friction sampled along it.

---

## Track B — upstream (ArcGIS Pro)

Two changes ride together here, and only the second changes model results:

| change | fixes | model impact |
|---|---|---|
| marine clip on the NHDArea join (B1) | 4 Lake/Pond polygons put 396 marine cells in the river-ice domain | 9 cells on the Stikine — hygiene |
| `EucAllocation` removed (already applied to source) | 73,526 gap cells per winter month held a truncated p_ice of 0 or 1 instead of their neighbour's value | **~4,900 corridor cells stop reading as open water in January** |

The second is why Track B is no longer optional. `EucAllocation` is a zone
tool; handed a float p_ice raster it truncates to integer, so every cell it
filled inherited 0 (any neighbour below 1.0) or 1. Those cells arrive in the
friction build as tier-1 *measured* values, where nothing flags them.

### B1. Rebuild the Brown masks with the marine clip

```bash
cd source_scripts/friction_surface/friction_preprocessing
PYTHONPATH=../../.. python build_brown_polygon_mask.py
```

`PYTHONPATH` matters: without it `friction_config` is not importable and the
marine clip cannot run. Expected:

```
  Marine clip: 296 marine NWN segments
    dropped 4 polygon(s), 371.3 km2
      Stikine River              ftype 364    225.1 km2
      Porcupine River            ftype 364    141.0 km2
      Kenai River                ftype 364      4.8 km2
      Kuparuk River              ftype 364      0.5 km2
  Polygons after marine clip:  963 (was 967)
```

**This is where the clip happens — not in arcpy.** Skip it and B2 re-reads the
old 967-polygon file and produces identical rasters.

### B2. Re-run the river-ice IDW

```
"C:\Program Files\ArcGIS\Pro\bin\Python\scripts\propy.bat" river_ice_full_pipeline.py
```

Edit `PROJECT_ROOT` first. arcpy is Windows-only, so if the repo lives on macOS
move `brown_river_polygons/`, `brown_river_flowlines/` and
`waterFilledMedians2000_2023.geojson` across — **and move the current
`river_ice_full_pipeline.py` with them**, or you will re-run the version that
still calls `EucAllocation`. Bring
`<PROJECT_ROOT>/AK_Stack_150m/river_ice_{01..12}.tif` back.

Confirm on the ArcGIS machine before running:

```bash
grep -c EucAllocation river_ice_full_pipeline.py    # expect 1 — the comment only
grep -n "final  = Con" river_ice_full_pipeline.py   # expect Con(~IsNull(mask_r), clamped)
```

The 12 rasters now carry NoData where the pipeline has no source, roughly 73k
cells per winter month. That is the fix landing, not a failure — the friction
build fills those cells under its own 25 km cap.

### B3. Re-align to the friction grid, then redo A2–A5

```bash
python -m friction_surface.friction_preprocessing.pad_river_ice_to_grid
```

**Easy to skip and it silently invalidates the run.** arcpy writes to
`AK_Stack_150m/`; the friction build reads `inputs/friction_rasters/river_ice/`.
Without this you rebuild against the old rasters and conclude nothing changed.

Tier 1 drops on two counts: the four clipped polygons carried 315
river-network cells, and the ~4,900 corridor cells the arcpy fallback used to
invent are now NoData. Tiers 2 and 3 absorb both. Expect the 89.5 / 5.5 / 5.1
split to move by roughly five points out of tier 1 — check it against the
prediction in `docs/TEST_LOG.md` (2026-08-21).

Those cells go from p_ice near 0 to near 0.78, so **more** river cells block in
winter, not fewer. Marine sites are untouched: `check_year_round_ports` must
still pass 12/12 on all eight Gulf/SE ports.

### B4. Confirm the truncation is gone

```bash
python - <<'EOF'
import numpy as np, rasterio
with rasterio.open("inputs/friction_rasters/river_ice/river_ice_01.tif") as s:
    v = s.read(1)
v = v[v != -9999.0]
print(f"valid cells      {v.size:,}")
print(f"distinct values  {np.unique(np.round(v,6)).size:,}")
print(f"exactly 0.0      {(v==0).sum():,}  ({(v==0).mean()*100:.2f}%)")
print(f"exactly 1.0      {(v==1).sum():,}  ({(v==1).mean()*100:.2f}%)")
EOF
```

**Pass** — the exactly-0.0 share drops sharply and the distinct-value count
rises. Pre-fix, 73,526 of those cells were drawn from just 85 distinct values,
84% of them exactly 0.0.

**Fail** — a large block still sits at exactly 0.0. `EucAllocation` is still in
the script, or the ArcGIS machine ran an older copy of it.

---

## Verify the fix took

```bash
python - <<'PY'
import rasterio, numpy as np, pyproj
from rasterio.windows import from_bounds
T = pyproj.Transformer.from_crs("EPSG:4326","EPSG:3338",always_xy=True)
mw = rasterio.open("outputs/01_friction_build/waterway_mask_150m.tif")
PORTS = {"Egegik":(-157.4,58.22), "Ugashik":(-157.6,57.55),
         "Naknek":(-156.9,58.72), "Ketchikan":(-131.65,55.34)}
R = 3000.0
for name,(lon,lat) in PORTS.items():
    x,y = T.transform(lon,lat)
    w = from_bounds(x-R,y-R,x+R,y+R,transform=mw.transform)
    net = mw.read(1,window=w,boundless=True,fill_value=0) == 1
    out = []
    for m in range(1,13):
        with rasterio.open(f"outputs/01_friction_build/friction_stack/barge_{m:02d}.tif") as s:
            a = s.read(1,window=w,boundless=True,fill_value=-9999) != -9999
        out.append("#" if (net & a).any() else ".")
    print(f"{name:<12} J F M A M J J A S O N D   {' '.join(out)}")
PY
```

**Pass** — Bristol Bay closed through winter, Ketchikan open all twelve:

```
Egegik       . . . . # # # # # # . .
Ugashik      . . . . # # # # # # . .
Naknek       . . . . # # # # # # . .
Ketchikan    # # # # # # # # # # # #
```

**Fail** — a `#` in the J or D column for any Bristol Bay river. Tier 3
returned zero; check the build log for `river-ice fallback:` and confirm the
count is non-zero.

---

## What each guard protects

Nothing here is redundant. Removing any one row reopens a distinct failure.

| guard | stops | if removed |
|---|---|---|
| river-mask clip on the **fill target** | river ice copied onto salt water | 288,954 cells blocked in February; Gulf and Inside Passage shut Nov–Apr |
| river-mask clip on the **gate** | river ice values *already* over salt water in the raster | 396 marine cells blocked, incl. Dry Strait and the Petersburg approach |
| **25 km cap** (`RIVER_ICE_FILL_MAX_KM`) | fill borrowing across watersheds | Ugashik takes its freeze date from 150 km away, "Dahl Creek" from 227 km |
| **k-nearest tier 3** (`RIVER_ICE_FALLBACK_K`) | uncovered rivers reading as never-frozen | all of Bristol Bay navigable in February |
| **marine clip** in `build_brown_polygon_mask` | salt water entering the IDW mask at source | the 396 above return whenever the river-ice product is rebuilt |
| **no `EucAllocation`** in `river_ice_full_pipeline` | arcpy filling unmeasured cells with a truncated p_ice | ~4,900 corridor cells read as open water in January, as tier-1 "measured" values nothing downstream flags |

The first two look redundant and are not: the fill clip stops ice being
*copied* to salt water; the gate clip stops ice that is *already there* from
being read. Different failures, different mechanisms.

The last row is a deletion, and it is deliberate that nothing replaced it. The
friction build's cascade already fills those cells, under a distance cap the
arcpy one never had. Re-adding a fill upstream would put two fill policies back
on nested domains — which is how both of this month's defects got in.

Tier 3 must stay **k-nearest**, not a latitude band. The band was tried first
and shipped Egegik navigable in January — Alaska's freeze gradient is not
north-south enough, and Egegik's band contained only Southeast rainforest
rivers 1,200–1,400 km east. See `docs/TEST_LOG.md`.

---

## Rollback

```bash
cd "$REPO"
rm -rf outputs/01_friction_build && mv outputs/01_friction_build.bak_preclip outputs/01_friction_build
rm -rf inputs/friction_rasters/river_ice && mv inputs/friction_rasters/river_ice.bak_preclip inputs/friction_rasters/river_ice
git checkout -- source_scripts/friction_surface/friction_config.py \
                source_scripts/friction_surface/friction_surface.py
```

Then re-run A2–A5 to rebuild from the restored inputs. Once satisfied:

```bash
rm -rf outputs/01_friction_build.bak_preclip inputs/friction_rasters/river_ice.bak_preclip
```

---

## Still open

- **Kvichak opened** rather than closed under the k-nearest fallback (1,478
  cells in January, 1,113 in December). Plausible — it drains Iliamna Lake and
  large lake-fed rivers hold open water later — but unpredicted and therefore
  unverified.
- **NHD membership check.** `tools/nhd_river_marine_check.py` has not been run
  against the full NHD. It would settle Egegik / Ugashik / Naknek (no Brown
  coverage) and the two naming anomalies below.
- **"Dahl Creek"** — the NWN segment sits at Port Clarence on the Seward
  Peninsula, ~800 km from the Kobuk village it is named after, and borrows its
  p_ice from 227 km away. Most likely a brackish lagoon misfiled as a creek,
  and the most likely false positive in the river mask.
- **Buckland River** — NWN geometry sits mid-Kotzebue Sound, ~120 km from the
  real mouth. Currently classified marine. Not load-bearing (Kotzebue Sound is
  sea-ice gated either way).
- **Kuskokwim Bay** — a 474.9 km² ftype-364 polygon labelled "Kuskokwim River"
  is salt water and stays in the IDW mask, because no NWN segment runs through
  it. Harmless for routing; still wrong if that mask is reused.
- **The port's mask is ~3% larger** than arcpy's (18,802 cells of 585k),
  assumed to be cell-centre rasterisation differing at polygon boundaries but
  not proven. It does not affect the truncation finding, which was measured
  inside arcpy's own mask — but it is the open question if
  `tools/river_ice_interp.py` is ever revisited as a replacement rather than a
  diagnostic.
- **`MARINE_LINEHAUL_SEASON_MONTHS`** is unused. Its Jun–Oct envelope describes
  western Alaska; wiring it in globally would close Southeast and Southcentral
  for seven months and recreate this bug by another route. There is a caution
  comment on it now.
