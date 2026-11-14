"""Stages 02-07 of workflow 00 on the committed 2025 release: guards, normalisation, publish checks."""
import pandas as pd
import pytest

from inventory_qc import apply_corrections as apply_mod
from inventory_qc import assign_facility_ids as ids_mod
from inventory_qc import assign_region as reg_mod
from inventory_qc import core as qc
from inventory_qc import normalise as norm_mod
from inventory_qc import publish as pub_mod

LABEL = qc.latest_release()


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory):
    """Run 02 -> 03 -> 03b -> 05b -> 07 into a temporary outputs dir so tests never touch tracked outputs."""
    tmp = tmp_path_factory.mktemp("qc")
    with pytest.MonkeyPatch.context() as mp:   # the stage modules are shared: undo OUT afterwards
        for m in (qc, apply_mod, norm_mod, ids_mod, reg_mod, pub_mod):
            mp.setattr(m, "OUT", tmp)
        fac, excl, log = apply_mod.apply(LABEL)
        qc.write_csv(fac, tmp / LABEL / "facilities_corrected.csv")
        qc.write_csv(excl, tmp / LABEL / "excluded.csv")
        qc.write_csv(log, tmp / LABEL / "corrections_log.csv")
        nfac, rep = norm_mod.normalise(LABEL)
        qc.write_csv(nfac, tmp / LABEL / "facilities_normalised.csv")
        A, _, _ = ids_mod.assign(LABEL); qc.write_csv(A, tmp / LABEL / "facility_ids_assigned.csv")
        R, _, _ = reg_mod.assign(LABEL); qc.write_csv(R, tmp / LABEL / "region_assignment.csv")
        clean, checks = pub_mod.publish(LABEL)
        yield dict(fac=fac, excl=excl, log=log, nfac=nfac, rep=rep, clean=clean, checks=checks, tmp=tmp)


def test_every_approved_correction_applies(pipeline):
    log = pipeline["log"]
    assert not log["outcome"].str.startswith("skipped").any(), log[log["outcome"].str.startswith("skipped")]
    assert (log["outcome"] == "applied").sum() == (qc.corrections()["status"] == "approved").sum()


def test_old_value_guard_blocks_a_stale_correction(monkeypatch, tmp_path):
    corr = qc.corrections()
    stale = corr[corr["status"] == "approved"].iloc[[0]].copy()
    stale["old_value"] = "not-the-current-value"
    monkeypatch.setattr(apply_mod, "corrections", lambda: stale)
    _, _, log = apply_mod.apply(LABEL)
    assert log["outcome"].iloc[0] == "skipped-old-value-mismatch"


def test_nothing_disappears_silently(pipeline):
    rel = qc.read_release(LABEL)
    assert len(rel) == len(pipeline["fac"]) + len(pipeline["excl"])
    assert pipeline["excl"].empty or pipeline["excl"]["exclusion_reason"].notna().all()


def test_normalise_collapses_known_variants(pipeline):
    keys = set(pipeline["nfac"]["community_key"].dropna())
    for variant in ("DUTCH HARBOR", "ST PAUL ISLAND", "ST GEORGE ISLAND", "KALSKAG", "BETTLES"):
        assert variant not in keys
    assert {"UNALASKA", "ST PAUL", "ST MARYS", "CLARKS POINT", "BETTLES FIELD"} <= keys


def test_delivery_flags_parse(pipeline):
    f = pipeline["nfac"]
    both = f[f["delivery_method"] == "Plane or Barge"]
    assert len(both) and (both["delivery_plane"] == "true").all() and (both["delivery_barge"] == "true").all()
    assert (f.loc[f["delivery_method"].isna(), "delivery_plane"].isna()).all()


def test_publish_checks_pass(pipeline):
    failed = [c for c in pipeline["checks"] if not c[1]]
    assert not failed, failed


def test_published_columns_are_schema_or_derived(pipeline):
    cols = list(pd.read_csv(pipeline["clean"], nrows=0).columns)
    allowed = set(qc.schema()["name"]) | set(qc.DERIVED)
    assert set(cols) <= allowed
    assert not any(w in c.lower() for c in cols for w in pub_mod.CONTACT_WORDS)


def test_regression_fixtures_fail_on_uncorrected_data():
    """The fixtures must actually detect the raw errors (otherwise they prove nothing)."""
    raw = qc.read_release(LABEL).dropna(subset=["latitude", "longitude"])
    results = [pred(raw) for _, pred in pub_mod.FIXTURES]
    assert not all(results), "every fixture passed on the UNCORRECTED release"


def test_placeholder_dates_published_blank(pipeline):
    """Pre-1900 inspection dates are database placeholders, published blank (owner 2026-11-14);
    the raw values stay in the release snapshot."""
    clean = pd.read_csv(pipeline["clean"], dtype=str)
    li = clean["last_inspected"].dropna()
    assert not (li.str[:4] < "1900").any()
    raw = qc.read_release(LABEL)["last_inspected"].dropna()
    assert (raw.str[:4] < "1900").any(), "the snapshot keeps the raw placeholder values"


def test_capacity_status_describes_never_repairs(pipeline):
    """capacity_status: ok | missing (unknown stays unknown, never zero) | mismatch (the 12
    audit cases); total_capacity itself is untouched by the status."""
    clean = pd.read_csv(pipeline["clean"], dtype=str)
    assert set(clean["capacity_status"]) == {"ok", "missing", "mismatch"}
    assert (clean["capacity_status"] == "mismatch").sum() == 12
    missing = clean["total_capacity"].isna()
    assert (clean.loc[missing, "capacity_status"] == "missing").all()
    assert (clean.loc[~missing, "capacity_status"] != "missing").all()
    raw = qc.read_release(LABEL).set_index("record_id")
    kept = clean.set_index("record_id")["total_capacity"].dropna()
    assert (raw.loc[kept.index, "total_capacity"].astype(float) == kept.astype(float)).all()


def test_coordinate_sync_and_source(pipeline):
    """Option 2 (owner 2026-11-14): one canonical position. A lat/lon correction also recomputes
    the publisher map point, logged as applied-sync; coordinate_source names the provenance."""
    from pyproj import Transformer
    import math
    clean = pd.read_csv(pipeline["clean"], dtype=str)
    assert set(clean["coordinate_source"].fillna("")) == {"publisher", "owner_correction", ""}
    located = clean["latitude"].notna() & clean["longitude"].notna()
    assert (clean.loc[~located, "coordinate_source"].fillna("") == "").all()
    corrected = clean[clean["coordinate_source"] == "owner_correction"]
    assert len(corrected) == 8
    to_map = Transformer.from_crs(4326, 3338, always_xy=True)
    for r in corrected.itertuples():
        x, y = to_map.transform(float(r.longitude), float(r.latitude))
        assert math.hypot(x - float(r.map_x), y - float(r.map_y)) < 1, r.community_name
    log = pipeline["log"]
    sync = log[log["outcome"] == "applied-sync"]
    assert len(sync) == 16 and set(sync["field"]) == {"map_x", "map_y"}
    assert set(sync["record_id"]) == set(corrected["record_id"])
    assert sync["new_value"].ne(sync["old_value"]).all(), "a no-op sync would hide a stale guard"
