"""Stage 04 — structural detectors on the corrected, normalised facility table.

A registry of checks. Each detector declares the schema columns it NEEDS and is skipped
(with a note in the output) when the release lacks them, so a new source runs the subset
it can support. Thresholds come from inputs/inventory_qc/thresholds.csv — never from code.

Every flag is matched against corrections.csv and remote_sites.csv so a record the owner
has already decided on is marked `covered_by` instead of re-raised.

Writes outputs/00_inventory_qc/<release>/flags_structural.csv
    record_id, detector, severity, detail, suggested_field, suggested_value, group_key, covered_by
and detectors_run.csv (detector, status, records_flagged, note).

Run:  python workflows/00_inventory_qc/04_detect.py [--release 2025]
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter

import numpy as np
import pandas as pd
from pyproj import Transformer

from .core import OUT, QC, RELEASES, corrections, latest_release, read_csv, release_manifest, thresholds, write_csv

TO_3338 = Transformer.from_crs("EPSG:4326", "EPSG:3338", always_xy=True)
REGISTRY: list[tuple[str, tuple[str, ...], object]] = []     # (name, needs, fn)


def detector(name: str, needs: tuple[str, ...]):
    def wrap(fn):
        REGISTRY.append((name, needs, fn))
        return fn
    return wrap


def _flag(rid, detector, severity, detail, field="", value="", group=""):
    return dict(record_id=rid, detector=detector, severity=severity, detail=detail,
                suggested_field=field, suggested_value=value, group_key=group)


def _xy(f: pd.DataFrame):
    lon, lat = f["longitude"].astype(float), f["latitude"].astype(float)
    x, y = TO_3338.transform(lon.values, lat.values)
    return pd.Series(x, index=f.index), pd.Series(y, index=f.index)


# ----------------------------------------------------------------------------- detectors
@detector("shared_farm_id", ("tank_farm_id", "community_name", "latitude", "longitude"))
def shared_farm_id(f: pd.DataFrame, th: dict) -> list[dict]:
    """One AEA tank-farm id carrying records labelled with several communities. The farm's
    position/capacity belong to the community it sits in; names the farm's own record when
    one exists (label == the community most other records within 3 km carry)."""
    out = []
    g = f.dropna(subset=["tank_farm_id"])
    x, y = _xy(f.dropna(subset=["latitude", "longitude"]))
    for fid, grp in g.groupby("tank_farm_id"):
        keys = set(grp["community_key"].dropna())
        if len(keys) <= 1:
            continue
        r0 = grp.iloc[0]
        px, py = TO_3338.transform(float(r0["longitude"]), float(r0["latitude"]))
        near = f.loc[x.index[(np.hypot(x - px, y - py) <= 3000)]]
        near = near[(near["tank_farm_id"] != fid)]
        sits = Counter(near["community_key"].dropna()).most_common(1)
        sits_in = sits[0][0] if sits else None
        own = grp[grp["community_key"] == sits_in]
        for r in grp.itertuples():
            if r.community_key == sits_in:
                out.append(_flag(r.record_id, "shared_farm_id", "info",
                                 f"farm {int(float(fid))}: this is the farm's own record ({sits_in}); {len(grp)-1} other label(s) share the id",
                                 group=f"farm:{int(float(fid))}"))
            else:
                hint = (f"farm's own record exists ({', '.join(own.record_id)})" if len(own)
                        else f"NO record labelled {sits_in}: consider relabelling one row to keep the farm")
                out.append(_flag(r.record_id, "shared_farm_id", "high",
                                 f"farm {int(float(fid))} sits in {sits_in} but this record is labelled {r.community_name}; "
                                 f"position + total_capacity are the farm's, not {r.community_name}'s. {hint}",
                                 field="latitude;longitude", value="", group=f"farm:{int(float(fid))}"))
    return out


@detector("within_farm_copies", ("tank_farm_id", "total_capacity", "community_key"))
def within_farm_copies(f: pd.DataFrame, th: dict) -> list[dict]:
    """Several rows on one farm id with the same label and the same total: the farm total is
    repeated per row, so summing rows over-counts capacity."""
    out = []
    g = f.dropna(subset=["tank_farm_id"])
    for (fid, key), grp in g.groupby(["tank_farm_id", "community_key"]):
        if len(grp) > 1 and grp["total_capacity"].nunique() == 1:
            for r in grp.iloc[1:].itertuples():
                out.append(_flag(r.record_id, "within_farm_copies", "low",
                                 f"farm {int(float(fid))} ({key}): {len(grp)} rows repeat total {r.total_capacity}; count it once",
                                 group=f"farm:{int(float(fid))}"))
    return out


@detector("shared_point_labels", ("latitude", "longitude", "community_key"))
def shared_point_labels(f: pd.DataFrame, th: dict) -> list[dict]:
    """One coordinate (within shared_point_m) carrying several community labels."""
    out = []
    g = f.dropna(subset=["latitude", "longitude"])
    tol = th["shared_point_m"]
    x, y = _xy(g)
    key = pd.Series(list(zip((x / tol).round().astype(int), (y / tol).round().astype(int))), index=g.index)
    for k, idx in key.groupby(key).groups.items():
        grp = g.loc[idx]
        keys = set(grp["community_key"].dropna())
        if len(keys) > 1:
            for r in grp.itertuples():
                others = sorted(keys - {r.community_key})
                out.append(_flag(r.record_id, "shared_point_labels", "high",
                                 f"same point as records labelled {', '.join(others)}",
                                 group=f"point:{k[0]}:{k[1]}"))
    return out


def _one_digit_edits(v: float):
    s = f"{v:.4f}"
    for i, ch in enumerate(s):
        if ch.isdigit():
            for d in "0123456789":
                if d != ch:
                    yield float(s[:i] + d + s[i + 1:])


@detector("one_digit_typo", ("latitude", "longitude", "community_key"))
def one_digit_typo(f: pd.DataFrame, th: dict) -> list[dict]:
    """A record far from its label's cluster where a single-digit coordinate edit lands within
    typo_match_km of that cluster."""
    out = []
    g = f.dropna(subset=["latitude", "longitude", "community_key"]).copy()
    x, y = _xy(g)
    g["x"], g["y"] = x, y
    med = {}
    for k, grp in g.groupby("community_key"):
        P = grp[["x", "y"]].to_numpy()
        if len(P) == 1:
            med[k] = P[0]
        else:
            D = np.sqrt(((P[:, None] - P[None]) ** 2).sum(-1))
            med[k] = P[D.sum(1).argmin()]
    spread = th["label_spread_km"] * 1000
    match = th["typo_match_km"] * 1000
    for r in g.itertuples():
        mx, my = med[r.community_key]
        if np.hypot(r.x - mx, r.y - my) <= spread:
            continue
        lat, lon = float(r.latitude), float(r.longitude)
        for cand_lat, cand_lon, fld in ([(c, lon, "latitude") for c in _one_digit_edits(lat)] +
                                        [(lat, c, "longitude") for c in _one_digit_edits(lon)]):
            cx, cy = TO_3338.transform(cand_lon, cand_lat)
            if np.hypot(cx - mx, cy - my) <= match:
                out.append(_flag(r.record_id, "one_digit_typo", "high",
                                 f"{np.hypot(r.x-mx, r.y-my)/1000:.0f} km from the {r.community_key} cluster; "
                                 f"editing one digit of {fld} to {cand_lat if fld=='latitude' else cand_lon:.4f} lands within {th['typo_match_km']:.0f} km",
                                 field=fld, value=f"{cand_lat if fld=='latitude' else cand_lon:.6f}"))
                break
    return out


@detector("map_point_disagrees", ("map_x", "map_y", "latitude", "longitude"))
def map_point_disagrees(f: pd.DataFrame, th: dict) -> list[dict]:
    """The publisher's map point and the lat/lon columns disagree by > 100 m (AEA edits the map
    geometry without updating lat/lon — the map point is usually the corrected one WHEN they
    disagree; agreement proves nothing, 6 of the 8 corrected records were wrong in both).
    Runs on corrected records too: stage 02 recomputes their map point from the corrected
    lat/lon (owner 2026-11-14, Option 2), so a flag here on one would mean the sync failed."""
    out = []
    g = f.dropna(subset=["map_x", "map_y", "latitude", "longitude"])
    x, y = _xy(g)
    d = np.hypot(x - g["map_x"].astype(float), y - g["map_y"].astype(float))
    inv = Transformer.from_crs("EPSG:3338", "EPSG:4326", always_xy=True)
    for rid, dist, mx, my in zip(g["record_id"], d, g["map_x"].astype(float), g["map_y"].astype(float)):
        if dist > 100:
            lon, lat = inv.transform(mx, my)
            out.append(_flag(rid, "map_point_disagrees", "high",
                             f"map point is {dist/1000:.1f} km from lat/lon; map point = {lat:.5f}, {lon:.5f}",
                             field="latitude;longitude", value=f"{lat:.6f};{lon:.6f}"))
    return out


@detector("missing_fields", ("record_id",))
def missing_fields(f: pd.DataFrame, th: dict) -> list[dict]:
    out = []
    for r in f.itertuples():
        miss = [c for c in ("latitude", "longitude", "community_name", "delivery_method", "total_capacity")
                if c in f.columns and (getattr(r, c) is None or (isinstance(getattr(r, c), float) and np.isnan(getattr(r, c))))]
        if miss:
            out.append(_flag(r.record_id, "missing_fields", "info", "missing: " + ", ".join(miss)))
    return out


CAPACITY_COMPONENTS = ("gasoline_capacity", "diesel_capacity", "jet_fuel_capacity", "other_fuel_capacity")


@detector("capacity_mismatch", ("total_capacity",) + CAPACITY_COMPONENTS)
def capacity_mismatch(f: pd.DataFrame, th: dict) -> list[dict]:
    """total_capacity vs the sum of the POPULATED per-fuel capacities (blank components are
    omitted, not zero). Components above the total are a physical contradiction (high);
    below may just be an incomplete breakdown (medium). Both are owner review items
    (owner 2026-11-14: all go to the queue) — never repaired by arithmetic."""
    out = []
    tol = th["capacity_mismatch_gal"]
    g = f.dropna(subset=["total_capacity"])
    comp = g[list(CAPACITY_COMPONENTS)].astype(float)
    total = g["total_capacity"].astype(float)
    s = comp.sum(axis=1)                        # NaN components count as 0 = omitted
    populated = comp.notna().any(axis=1)
    bad = populated & ((s - total).abs() > tol)
    for rid, t, c in zip(g.loc[bad, "record_id"], total[bad], s[bad]):
        above = c > t
        out.append(_flag(rid, "capacity_mismatch", "high" if above else "medium",
                         f"total {t:g} gal vs populated fuel sum {c:g} gal "
                         f"({'components exceed total' if above else 'components below total — breakdown may be incomplete'})"))
    return out


@detector("placeholder_inspection_date", ("last_inspected",))
def placeholder_inspection_date(f: pd.DataFrame, th: dict) -> list[dict]:
    """A pre-1900 inspection date is a database placeholder (the Esri 1899-12-30 epoch), not an
    inspection. 07_publish blanks it in the clean table; this flag is the record of each one."""
    g = f.dropna(subset=["last_inspected"])
    old = g[g["last_inspected"].astype(str).str[:4] < "1900"]
    return [_flag(r.record_id, "placeholder_inspection_date", "info",
                  f"last_inspected {r.last_inspected} is a pre-1900 placeholder; published blank",
                  field="last_inspected", value="")
            for r in old.itertuples()]


@detector("alaska_envelope", ("latitude", "longitude"))
def alaska_envelope(f: pd.DataFrame, th: dict) -> list[dict]:
    """Broad plausibility envelope: lat 50..72 N, lon <= -129 E or >= 170 E (the western
    Aleutians cross the antimeridian). Expected to flag nothing on a corrected release —
    it exists so a future release's gross coordinate error cannot arrive silently."""
    g = f.dropna(subset=["latitude", "longitude"])
    lat, lon = g["latitude"].astype(float), g["longitude"].astype(float)
    bad = ~(lat.between(50, 72) & ((lon <= -129) | (lon >= 170)))
    return [_flag(r.record_id, "alaska_envelope", "high",
                  f"({r.latitude}, {r.longitude}) lies outside the broad Alaska envelope")
            for r in g[bad].itertuples()]


@detector("spelling_variants", ("community_id", "community_name"))
def spelling_variants(f: pd.DataFrame, th: dict) -> list[dict]:
    """One publisher community id carrying several raw spellings (after aliases)."""
    out = []
    g = f.dropna(subset=["community_id", "community_name"])
    for cid, grp in g.groupby("community_id"):
        names = sorted(set(grp["community_name"]))
        if len(names) > 1:
            main = grp["community_name"].mode().iat[0]
            for r in grp[grp["community_name"] != main].itertuples():
                out.append(_flag(r.record_id, "spelling_variants", "medium",
                                 f"community id {cid} is spelled {names}; most common: {main}",
                                 field="community_name", value=main, group=f"cid:{cid}"))
    return out


@detector("release_diff", ("record_id",))
def release_diff(f: pd.DataFrame, th: dict) -> list[dict]:
    """Records edited upstream since the previous release (from the ingest diff) — evidence,
    e.g. a map-point move that confirms or retires a correction."""
    man = release_manifest(f.attrs["release"])
    if "diff_file" not in man:
        return []
    d = read_csv(RELEASES / f.attrs["release"] / man["diff_file"])
    d = d[(d["change"] == "edited") & ~d["field"].isin(["map_x", "map_y", "last_edited"])]
    return [_flag(r.record_id, "release_diff", "info", f"upstream edited {r.field}: {r.old_value!r} -> {r.new_value!r}")
            for r in d.itertuples()]


# ----------------------------------------------------------------------------- run
def run(label: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    f = read_csv(OUT / label / "facilities_normalised.csv")
    f.attrs["release"] = label
    th = thresholds()
    flags, ran = [], []
    for name, needs, fn in REGISTRY:
        missing = [c for c in needs if c not in f.columns or f[c].notna().sum() == 0]
        if missing:
            ran.append(dict(detector=name, status="skipped", records_flagged=0, note=f"release lacks {missing}"))
            continue
        res = fn(f, th)
        flags.extend(res)
        ran.append(dict(detector=name, status="ran", records_flagged=len({r['record_id'] for r in res}), note=""))
    F = pd.DataFrame(flags, columns=["record_id", "detector", "severity", "detail", "suggested_field", "suggested_value", "group_key"])
    # coverage by existing decisions
    corr = corrections()
    status = corr.groupby("record_id")["status"].agg(lambda s: "approved" if "approved" in set(s) else ("pending" if "pending" in set(s) else "rejected"))
    exc = pd.read_csv(QC / "remote_sites.csv", dtype=str, keep_default_na=False) if (QC / "remote_sites.csv").exists() else pd.DataFrame(columns=["record_id"])
    F["covered_by"] = F["record_id"].map(lambda r: f"correction:{status[r]}" if r in status.index else ("exception" if r in set(exc["record_id"]) else ""))
    F = F.sort_values(["severity", "detector", "group_key", "record_id"], key=lambda s: s.map({"high": 0, "medium": 1, "low": 2, "info": 3}) if s.name == "severity" else s).reset_index(drop=True)
    return F, pd.DataFrame(ran)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--release", default=None)
    a = ap.parse_args(argv)
    label = a.release or latest_release()
    F, ran = run(label)
    write_csv(F, OUT / label / "flags_structural.csv")
    write_csv(ran, OUT / label / "detectors_run.csv")
    for r in ran.itertuples():
        print(f"  {r.detector:22s} {r.status:8s} {r.records_flagged:5d} {r.note}")
    new = F[(F["covered_by"] == "") & (F["severity"].isin(["high", "medium"]))]
    print(f"release {label}: {len(F)} flags on {F['record_id'].nunique()} records; "
          f"{new['record_id'].nunique()} records with high/medium flags not yet covered by a decision")
    return 0


if __name__ == "__main__":
    sys.exit(main())
