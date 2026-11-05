#!/usr/bin/env python3
"""Fetch the large intermediates from the project's Zenodo deposit (DATA.md, path 2).

The repository holds everything under 50 MB. The rasters do not fit (the friction
inputs are ~7 GB, the finished stack ~300 MB), so they live in a Zenodo deposit
that complements this repository. This script downloads one or more groups from
it, verifies every file against the deposit's own md5, and unpacks each into the
folder the pipeline reads, under the names the pipeline expects (nothing is
renamed; see friction_paths.RASTER_NAMES).

  group            deposit file          unpacks into                               used by
  friction_inputs  friction_inputs.zip   inputs/friction_rasters/                   workflow 01 (build the stack)
  friction_stack   friction_stack.zip    outputs/01_friction_build/friction_stack/  workflow 03 (weight the network)
  river_ice_work   river_ice_work.zip    inputs/river_ice_work/                     the ArcGIS river-ice step (path 3)

The network build (workflow 02) has no deposit group: its hand-edited layers
(ice roads, manual connections) are in the repository and its other raw layers
are public downloads (DATA.md §4.1).

Each zip's members are laid out exactly as the destination folder (for example
friction_inputs.zip holds sea_ice/… and river_ice/… sub-folders and the three
static rasters at its top level). A zip whose members are rooted at the
destination's own name (friction_rasters/…) is accepted too.

Run (stdlib only; works straight after cloning):
    python tools/fetch_archive.py --list                       # what the deposit holds
    python tools/fetch_archive.py --group friction_stack       # one group
    python tools/fetch_archive.py --group all                  # everything
    python tools/fetch_archive.py --record 10.5281/zenodo.NNNNNNN --group friction_inputs

Until the deposit is published ZENODO_RECORD below is None, and the script
exits 3 (the drivers' "documented input absent" code) with a message, unless
--record is given. Downloads are kept in <repo>/.archive/ so a re-run verifies
instead of re-downloading; --no-keep deletes each zip after unpacking.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # repo root (runs before the project env exists)
GATE_EXIT = 3

# The Zenodo record of the deposit that complements this repository.
# Set it to the record id ("1234567") or the DOI ("10.5281/zenodo.1234567")
# once the deposit is published; a concept DOI (always the latest version)
# works as well. Until then, pass --record on the command line.
ZENODO_RECORD: str | None = None

ZENODO_API = "https://zenodo.org/api/records/{record}"

GROUPS = {
    "friction_inputs": {
        "file": "friction_inputs.zip",
        "dest": ROOT / "inputs" / "friction_rasters",
        "what": "the five friction inputs on the canonical grid (slope, land cover, "
                "permafrost, 12 sea ice, 12 river ice), ~7 GB",
    },
    "friction_stack": {
        "file": "friction_stack.zip",
        "dest": ROOT / "outputs" / "01_friction_build" / "friction_stack",
        "what": "the finished friction stack (overland, road_base, barge_01..12), ~300 MB",
    },
    "river_ice_work": {
        "file": "river_ice_work.zip",
        "dest": ROOT / "inputs" / "river_ice_work",
        "what": "the river-ice working directory: the Brown reach points and the two NHD river masks",
    },
}


def resolve_record_id(record: str) -> str:
    """'10.5281/zenodo.1234567', 'https://doi.org/…', 'https://zenodo.org/records/1234567'
    or '1234567' -> '1234567'."""
    r = record.strip().rstrip("/")
    for sep in ("zenodo.", "records/", "record/"):
        if sep in r:
            r = r.rsplit(sep, 1)[1]
    if not r.isdigit():
        raise SystemExit(f"fetch_archive: cannot read a Zenodo record id from {record!r}")
    return r


def fetch_record(record_id: str) -> dict:
    with urllib.request.urlopen(ZENODO_API.format(record=record_id), timeout=60) as resp:
        return json.load(resp)


def record_files(record: dict) -> dict[str, dict]:
    """{file name: {'url': …, 'md5': …, 'size': …}} from a Zenodo record JSON."""
    out = {}
    for f in record.get("files", []):
        md5 = f.get("checksum", "")
        out[f["key"]] = {
            "url": f["links"]["self"],
            "md5": md5.split(":", 1)[1] if md5.startswith("md5:") else md5,
            "size": f.get("size"),
        }
    return out


def md5_of(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as resp, open(tmp, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        for chunk in iter(lambda: resp.read(1 << 20), b""):
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {dest.name}: {done / 1e6:,.0f} / {total / 1e6:,.0f} MB", end="", flush=True)
    print()
    tmp.replace(dest)


def extract_root(zf: zipfile.ZipFile, dest: Path) -> Path:
    """Members rooted at the destination's own folder name unpack one level up."""
    names = [n for n in zf.namelist() if not n.startswith("__MACOSX/")]
    if names and all(n.startswith(dest.name + "/") for n in names):
        return dest.parent
    return dest


def unpack(zip_path: Path, dest: Path) -> int:
    with zipfile.ZipFile(zip_path) as zf:
        root = extract_root(zf, dest)
        members = [m for m in zf.namelist()
                   if not m.startswith("__MACOSX/") and not m.endswith(".DS_Store")]
        root.mkdir(parents=True, exist_ok=True)
        zf.extractall(root, members=members)
    return len(members)


def install_group(name: str, files: dict[str, dict], keep: bool = True,
                  verify: bool = True, downloader=download) -> None:
    g = GROUPS[name]
    entry = files.get(g["file"])
    if entry is None:
        raise SystemExit(f"fetch_archive: the deposit has no file {g['file']!r} "
                         f"(group {name}); it holds: {sorted(files)}")
    cache = ROOT / ".archive" / g["file"]
    if cache.exists() and verify and entry["md5"] and md5_of(cache) == entry["md5"]:
        print(f"[{name}] {g['file']} already downloaded and verified")
    else:
        print(f"[{name}] downloading {g['file']} ({(entry['size'] or 0) / 1e6:,.0f} MB)")
        downloader(entry["url"], cache)
        if verify and entry["md5"]:
            got = md5_of(cache)
            if got != entry["md5"]:
                cache.unlink()
                raise SystemExit(f"fetch_archive: md5 mismatch for {g['file']}: deposit says "
                                 f"{entry['md5']}, download has {got}. Deleted; run again.")
            print(f"[{name}] md5 verified")
    n = unpack(cache, g["dest"])
    print(f"[{name}] unpacked {n} member(s) into {g['dest'].relative_to(ROOT)}/")
    if not keep:
        cache.unlink()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--record", default=ZENODO_RECORD,
                    help="Zenodo record id or DOI (default: ZENODO_RECORD in this file)")
    ap.add_argument("--group", action="append", choices=[*GROUPS, "all"],
                    help="which group to fetch; repeatable; 'all' for every group")
    ap.add_argument("--list", action="store_true", help="list the deposit's files and stop")
    ap.add_argument("--no-keep", action="store_true", help="delete each zip after unpacking")
    ap.add_argument("--no-verify", action="store_true", help="skip the md5 check (not recommended)")
    args = ap.parse_args(argv)

    if not args.record:
        print("GATE: the Zenodo deposit for this repository is not published yet, so there is")
        print("  no archive to fetch from. Until it is: regenerate the data from the raw sources")
        print("  (DATA.md path 3), or pass --record <zenodo id or DOI> if you have a draft record.")
        return GATE_EXIT

    record_id = resolve_record_id(args.record)
    files = record_files(fetch_record(record_id))
    if args.list or not args.group:
        print(f"Zenodo record {record_id}:")
        for key, f in sorted(files.items()):
            group = next((n for n, g in GROUPS.items() if g["file"] == key), "-")
            print(f"  {key:28s} {(f['size'] or 0) / 1e6:10,.0f} MB  md5 {f['md5'] or '-'}  group {group}")
        if not args.group:
            print("\nPick a group with --group (one of: " + ", ".join(GROUPS) + ", all).")
        return 0

    groups = list(GROUPS) if "all" in args.group else args.group
    for name in groups:
        install_group(name, files, keep=not args.no_keep, verify=not args.no_verify)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
