#!/usr/bin/env python3
"""Extract the committed inputs/*.zip bundles into their gitignored working dirs.

  inputs/bulk_fuel_data.zip          -> inputs/bulk_fuel_data/
  inputs/data_for_network_build.zip  -> inputs/data_for_network_build/
  inputs/region_and_census_data.zip  -> inputs/region_and_census_data/
  inputs/network_raw.zip             -> data/raw/          (workflow 02 sources;
                                        zip pending the data-redistribution
                                        decision — see inputs/README.md)

One gate for workflows 01-03: run this once after cloning (with Git LFS
pulled). __MACOSX resource forks and .DS_Store entries are skipped.
Extraction is idempotent.

Run:  python tools/extract_inputs.py
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # repo root

TARGETS = {
    ROOT / "inputs" / "bulk_fuel_data.zip": ROOT / "inputs",
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
            print(f"skip: {zpath.relative_to(ROOT)} not present"
                  + (" (pending data-redistribution decision — see inputs/README.md)"
                     if zpath.name == "network_raw.zip" else
                     " (Git LFS: run `git lfs pull`?)"))
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
    # one level deeper inside bulk_fuel_data.zip.
    fdm_zip = ROOT / "inputs" / "bulk_fuel_data" / "raw" / "Fuel_Delivery_Method.zip"
    if fdm_zip.exists():
        with zipfile.ZipFile(fdm_zip) as zf:
            zf.extractall(fdm_zip.parent)
        print(f"extracted nested {fdm_zip.relative_to(ROOT)} -> {fdm_zip.parent.relative_to(ROOT)}/")

    if not extracted:
        raise SystemExit("nothing extracted — are the LFS zips present?")


if __name__ == "__main__":
    main()
