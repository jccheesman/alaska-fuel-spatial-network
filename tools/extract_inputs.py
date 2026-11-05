#!/usr/bin/env python3
"""Extract the committed inputs/*.zip bundles into their gitignored working dirs.

  inputs/raw_facility_data/2022/bulk_fuel_data.zip -> inputs/bulk_fuel_data/
  inputs/data_for_network_build.zip  -> inputs/data_for_network_build/
  inputs/region_and_census_data.zip  -> inputs/region_and_census_data/
  inputs/network_raw.zip             -> data/raw/          (optional, local only: a bundle of
                                        the public downloads for workflow 02 — never
                                        committed or deposited; see DATA.md §4.1)

It also copies the hand-edited ice-road layer out of the extracted
data_for_network_build/ into data/raw/connectivity/ice_roads/ice_roads_150m_3338/,
where workflow 02's SPEC table reads it: that layer is the owner's own merge of three
sources and exists nowhere else, so the repository is its home. The other workflow 02
raw layers are public downloads (DATA.md §4.1).

One gate for workflows 00-03: run this once after cloning. The zips are plain
git blobs (no Git LFS). __MACOSX resource forks and .DS_Store entries are skipped.
Extraction is idempotent.

Run:  python tools/extract_inputs.py
"""
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # repo root

TARGETS = {
    ROOT / "inputs" / "raw_facility_data" / "2022" / "bulk_fuel_data.zip": ROOT / "inputs",
    ROOT / "inputs" / "data_for_network_build.zip": ROOT / "inputs",
    ROOT / "inputs" / "region_and_census_data.zip": ROOT / "inputs",
    # network_raw.zip: destination depends on how its members are rooted —
    # resolved dynamically in main() (see _network_raw_dest).
    ROOT / "inputs" / "network_raw.zip": None,
}


def _network_raw_dest(zf: zipfile.ZipFile) -> "Path":
    """Pick the extract root so files land at <repo>/data/raw/... either way.

    Bundles rooted at 'data/raw/...' extract at the repo root; bundles rooted
    at 'facilities/...', 'boundaries/...' etc. extract under data/raw/.
    """
    names = [n for n in zf.namelist() if not n.startswith("__MACOSX/")]
    if any(n.startswith("data/raw/") for n in names):
        return ROOT
    return ROOT / "data" / "raw"


def main() -> None:
    extracted = 0
    for zpath, dest in TARGETS.items():
        if not zpath.exists():
            if zpath.name == "network_raw.zip":
                continue  # optional local bundle; the public layers are downloads (DATA.md §4.1)
            print(f"skip: {zpath.relative_to(ROOT)} not present"
                  " (clone incomplete? the zips are plain git blobs, no LFS)")
            continue
        with zipfile.ZipFile(zpath) as zf:
            if dest is None:  # network_raw.zip — root depends on member layout
                dest = _network_raw_dest(zf)
            dest.mkdir(parents=True, exist_ok=True)
            members = [m for m in zf.namelist()
                       if not m.startswith("__MACOSX/") and not m.endswith(".DS_Store")]
            zf.extractall(dest, members=members)
        rel = dest.relative_to(ROOT) if dest != ROOT else Path(".")
        print(f"extracted {zpath.relative_to(ROOT)} -> {rel}/")
        extracted += 1

    # Nested shapefile bundle: friction_costs.load_ice_road_communities reads
    # inputs/bulk_fuel_data/raw/Fuel_Delivery_Method.shp, which ships zipped
    # one level deeper inside raw_facility_data/2022/bulk_fuel_data.zip.
    fdm_zip = ROOT / "inputs" / "bulk_fuel_data" / "raw" / "Fuel_Delivery_Method.zip"
    if fdm_zip.exists():
        with zipfile.ZipFile(fdm_zip) as zf:
            zf.extractall(fdm_zip.parent)
        print(f"extracted nested {fdm_zip.relative_to(ROOT)} -> {fdm_zip.parent.relative_to(ROOT)}/")

    # The hand-edited ice-road layer ships inside data_for_network_build.zip; workflow 02
    # reads it from the data/raw layout, so put a copy there (plain files, no geo libs).
    ice_src = ROOT / "inputs" / "data_for_network_build" / "ice_roads_150m_3338"
    ice_dst = ROOT / "data" / "raw" / "connectivity" / "ice_roads" / "ice_roads_150m_3338"
    if ice_src.is_dir():
        ice_dst.mkdir(parents=True, exist_ok=True)
        for f in ice_src.iterdir():
            if f.is_file() and f.name.startswith("Ice_Roads."):
                shutil.copy2(f, ice_dst / f.name)
        print(f"copied the ice-road layer -> {ice_dst.relative_to(ROOT)}/ (workflow 02 raw layout)")

    if not extracted:
        raise SystemExit("nothing extracted — are the committed zips present? (see DATA.md section 1)")


if __name__ == "__main__":
    main()
