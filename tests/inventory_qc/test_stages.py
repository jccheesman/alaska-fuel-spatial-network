"""Stages 02-07 of workflow 00 on the committed 2025 release: guards, normalisation, publish checks."""
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows" / "00_inventory_qc"
sys.path.insert(0, str(WF))


def load(name):
    spec = importlib.util.spec_from_file_location(name, WF / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


qc = load("_qc")
apply_mod = load("02_apply_corrections")
norm_mod = load("03_normalise")
pub_mod = load("07_publish")
LABEL = qc.latest_release()


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory):
    """Run 02 -> 03 -> 07 into a temporary outputs dir so tests never touch tracked outputs."""
    tmp = tmp_path_factory.mktemp("qc")
    for m in (qc, apply_mod, norm_mod, pub_mod):
        m.OUT = tmp
    fac, excl, log = apply_mod.apply(LABEL)
    qc.write_csv(fac, tmp / LABEL / "facilities_corrected.csv")
    qc.write_csv(excl, tmp / LABEL / "excluded.csv")
    qc.write_csv(log, tmp / LABEL / "corrections_log.csv")
    nfac, rep = norm_mod.normalise(LABEL)
    qc.write_csv(nfac, tmp / LABEL / "facilities_normalised.csv")
    clean, checks = pub_mod.publish(LABEL)
    return dict(fac=fac, excl=excl, log=log, nfac=nfac, rep=rep, clean=clean, checks=checks, tmp=tmp)


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
