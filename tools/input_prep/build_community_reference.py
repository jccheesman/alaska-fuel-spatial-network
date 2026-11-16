"""The Alaska community reference: DCRA community locations joined to the DCRA Community Overview.

Two State of Alaska DCRA (Division of Community and Regional Affairs) sources, both public,
committed as dated snapshots under inputs/community_reference/ (see SOURCE.md there):

  dcra_community_locations.csv   "Alaska Communities" point layer, every community DCRA tracks
                                 (city, CDP, borough, census area, place of interest), with its
                                 type, active flag, start/end dates and position. Fetched with
                                 --fetch from the map service below; attributes only, the
                                 editor names, editors' comments
                                 and edit dates are never written.
  dcra_community_overview.csv    the Community Overview export (incorporation, borough or census
                                 area, population, federally recognised tribe), byte-for-byte as
                                 the owner downloaded it (2026-10-10).

The joined table, dcra_community_reference.csv, has one row per location-layer community,
joined to the Overview by the DCRA community GUID (CommunityId == CommunityID). It is derived
from the two snapshots only, so --check needs no network and is what tests and reviewers run.

    python tools/input_prep/build_community_reference.py            # re-derive the joined table
    python tools/input_prep/build_community_reference.py --check    # exit 1 if it would change
    python tools/input_prep/build_community_reference.py --fetch    # refresh the location snapshot
                                                                    # from the service, then re-derive

--fetch uses the system trust store; behind a TLS-inspecting proxy point SSL_CERT_FILE at its
CA bundle. After a fetch, update the date, count and sha256 in SOURCE.md and inputs/MANIFEST.md.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import pandas as pd

import repo_paths as rp

BASE = rp.COMMUNITY_REFERENCE
LOCATIONS_CSV = BASE / "dcra_community_locations.csv"
OVERVIEW_CSV = BASE / "dcra_community_overview.csv"
REFERENCE_CSV = BASE / "dcra_community_reference.csv"

SERVICE = ("https://maps.commerce.alaska.gov/server/rest/services/Community_Related/"
           "Community_Locations_and_Boundaries/MapServer/0")

# Layer fields written to the snapshot, in order. Left out on purpose: created_user /
# last_edited_user (names of state staff) and Comments (editors' notes signed with staff
# initials), created_date / last_edited_date (edit bookkeeping that changes without the
# community changing), GlobalID / OBJECTID (database row ids), and x_auxmerc / y_auxmerc
# (the same point in Web Mercator).
LAYER_FIELDS = ["CommunityId", "CommunityName", "CommunityTypeName", "CommunityTypeID",
                "CommunityAreaTypeName", "CommunityAreaTypeID", "IsActive", "StartDate", "EndDate",
                "x", "y", "StatePlaneZone", "AltStatePlaneZone",
                "RODistrictNumber", "RODistrictName", "AltRODistrictNumber", "AltRODistrictName"]
DATE_FIELDS = ("StartDate", "EndDate")
INT_FIELDS = ("CommunityTypeID", "CommunityAreaTypeID", "IsActive", "StatePlaneZone", "AltStatePlaneZone",
              "RODistrictNumber", "AltRODistrictNumber")

# Overview columns carried into the reference, renamed.
OVERVIEW_KEEP = {"IncorporationType": "incorporation", "BoroughCensusArea": "borough_census_area",
                 "Population": "population", "PopulationYear": "population_year",
                 "FederallyRecognizedTribe": "tribe", "IncorporationYear": "incorporation_year"}

REFERENCE_COLUMNS = ["community_id", "community_name", "community_type", "community_type_id",
                     "area_type", "area_type_id", "is_active", "start_date", "end_date",
                     "lon", "lat", "x_3338", "y_3338", "in_overview", "overview_name",
                     *OVERVIEW_KEEP.values()]


def _get(url: str, params: dict) -> dict:
    q = url + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(q, context=ssl.create_default_context(), timeout=60) as r:
        d = json.load(r)
    if "error" in d:
        raise RuntimeError(f"{url}: {d['error']}")
    return d


def fetch() -> pd.DataFrame:
    """Every feature of the layer, paged; geometry in the layer's own EPSG:3338."""
    meta = _get(SERVICE, {"f": "json"})
    page = int(meta.get("maxRecordCount") or 1000)
    have = {f["name"] for f in meta["fields"]}
    missing = [f for f in LAYER_FIELDS if f not in have]
    if missing:
        raise RuntimeError(f"layer no longer has {missing}; review LAYER_FIELDS before refreshing")
    rows, offset = [], 0
    while True:
        d = _get(SERVICE + "/query", {"where": "1=1", "outFields": ",".join(LAYER_FIELDS),
                                      "returnGeometry": "true", "outSR": 3338, "orderByFields": "OBJECTID",
                                      "resultOffset": offset, "resultRecordCount": page, "f": "json"})
        feats = d.get("features", [])
        for f in feats:
            a = {k: f["attributes"].get(k) for k in LAYER_FIELDS}
            g = f.get("geometry") or {}
            a["x_3338"], a["y_3338"] = g.get("x"), g.get("y")
            rows.append(a)
        offset += len(feats)
        if not feats or not d.get("exceededTransferLimit"):
            break
    df = pd.DataFrame(rows, columns=LAYER_FIELDS + ["x_3338", "y_3338"])
    for c in DATE_FIELDS:   # epoch milliseconds -> ISO date (the layer stores dates, not times)
        df[c] = [datetime.fromtimestamp(v / 1000, tz=timezone.utc).date().isoformat() if pd.notna(v) else ""
                 for v in df[c]]
    for c in INT_FIELDS:    # a blank makes pandas store the column as float ("5008.0")
        df[c] = df[c].astype("Int64")
    df["CommunityId"] = df["CommunityId"].str.upper()
    for c in ("x", "y"):
        df[c] = df[c].round(6)
    for c in ("x_3338", "y_3338"):
        df[c] = df[c].round(1)
    return df.sort_values(["CommunityId"]).reset_index(drop=True)


def read_overview() -> pd.DataFrame:
    ov = pd.read_csv(OVERVIEW_CSV, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    ov["CommunityID"] = ov["CommunityID"].str.strip().str.upper()
    return ov


def derive() -> pd.DataFrame:
    loc = pd.read_csv(LOCATIONS_CSV, dtype=str, keep_default_na=False)
    ov = read_overview()
    dup = ov["CommunityID"][ov["CommunityID"].duplicated()]
    if len(dup):
        raise SystemExit(f"Overview repeats CommunityID {sorted(set(dup))}; the join needs one row each")
    if loc["CommunityId"].duplicated().any():
        raise SystemExit("location layer repeats a CommunityId; the join needs one row each")
    ov = ov[["CommunityID", "CommunityName", *OVERVIEW_KEEP]].rename(
        columns={"CommunityID": "community_id", "CommunityName": "overview_name", **OVERVIEW_KEEP})
    ref = loc.rename(columns={"CommunityId": "community_id", "CommunityName": "community_name",
                              "CommunityTypeName": "community_type", "CommunityTypeID": "community_type_id",
                              "CommunityAreaTypeName": "area_type", "CommunityAreaTypeID": "area_type_id",
                              "IsActive": "is_active", "StartDate": "start_date", "EndDate": "end_date",
                              })
    # Position: the layer's geometry (EPSG:3338), which the Overview's X/Y match exactly. The
    # layer's own x/y attributes are not re-computed when an editor moves a point, and lag the
    # geometry for 11 points (Aleutians West Census Area by 800 km), so lon/lat come from the
    # geometry, never from those attributes.
    from pyproj import Transformer
    lon, lat = Transformer.from_crs(3338, 4326, always_xy=True).transform(
        pd.to_numeric(ref["x_3338"]).values, pd.to_numeric(ref["y_3338"]).values)
    ref["lon"], ref["lat"] = [f"{v:.6f}" for v in lon], [f"{v:.6f}" for v in lat]
    ref = ref.merge(ov, on="community_id", how="left", indicator=True)
    ref["in_overview"] = (ref.pop("_merge") == "both").map({True: "1", False: "0"})
    ref = ref.fillna("")
    for c in ("community_type", "area_type", "community_name", "overview_name"):
        ref[c] = ref[c].str.strip()
    return ref[REFERENCE_COLUMNS].sort_values("community_id").reset_index(drop=True)


def to_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False, lineterminator="\n")
    return buf.getvalue().encode("utf-8")


def sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(ref: pd.DataFrame) -> str:
    ov_ids = set(read_overview()["CommunityID"])
    only_ov = len(ov_ids - set(ref["community_id"]))
    act = ref["is_active"] == "1"
    return (f"{len(ref)} communities ({int(act.sum())} active), {int((ref['in_overview'] == '1').sum())} joined "
            f"to the Overview, {only_ov} Overview rows with no location-layer community")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--fetch", action="store_true", help="refresh the location snapshot from the DCRA service first")
    g.add_argument("--check", action="store_true", help="exit 1 if the committed reference is not what the snapshots give")
    a = ap.parse_args(argv)
    if a.fetch:
        BASE.mkdir(parents=True, exist_ok=True)
        LOCATIONS_CSV.write_bytes(to_bytes(fetch()))
        print(f"fetched {LOCATIONS_CSV.name}  sha256 {sha256(LOCATIONS_CSV)}")
    ref = derive()
    new = to_bytes(ref)
    if a.check:
        old = REFERENCE_CSV.read_bytes() if REFERENCE_CSV.exists() else b""
        if old != new:
            print(f"{REFERENCE_CSV.name} is stale: re-run without --check and commit it", file=sys.stderr)
            return 1
        print(f"{REFERENCE_CSV.name} up to date: {summary(ref)}")
        return 0
    REFERENCE_CSV.write_bytes(new)
    print(f"wrote {REFERENCE_CSV.name}: {summary(ref)}  sha256 {sha256(REFERENCE_CSV)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
