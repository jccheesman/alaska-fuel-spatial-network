"""Stages 04-06 on the committed release: detectors find the audit's known cases, the
boundary check verifies without relabelling, the review queue excludes decided records."""
import pytest

from inventory_qc import apply_corrections as apply_mod
from inventory_qc import boundary_check as bnd_mod
from inventory_qc import core as qc
from inventory_qc import detect as det_mod
from inventory_qc import normalise as norm_mod
from inventory_qc import review_queue as rq_mod

LABEL = qc.latest_release()
# 2022 harness ids of known cases -> AEA record ids
REC = {
    "unalaska_f001606": "{F020D8C7-7FD0-4AFE-85DC-43D1C0A0B5F0}",   # CommunityID shared by the Unalaska rows; record found below by label
}


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("qc2")
    with pytest.MonkeyPatch.context() as mp:   # the stage modules are shared: undo OUT afterwards
        for m in (qc, apply_mod, norm_mod, det_mod, bnd_mod, rq_mod):
            mp.setattr(m, "OUT", tmp)
        fac, excl, log = apply_mod.apply(LABEL)
        qc.write_csv(fac, tmp / LABEL / "facilities_corrected.csv"); qc.write_csv(excl, tmp / LABEL / "excluded.csv"); qc.write_csv(log, tmp / LABEL / "corrections_log.csv")
        nfac, _ = norm_mod.normalise(LABEL); qc.write_csv(nfac, tmp / LABEL / "facilities_normalised.csv")
        F, ran = det_mod.run(LABEL); qc.write_csv(F, tmp / LABEL / "flags_structural.csv")
        Bf, Bs, Bd = bnd_mod.check(LABEL); qc.write_csv(Bf, tmp / LABEL / "flags_boundary.csv"); qc.write_csv(Bd, tmp / LABEL / "boundary_distance.csv")
        Q = rq_mod.build(LABEL)
        yield dict(nfac=nfac, F=F, ran=ran, Bf=Bf, Bs=Bs, Bd=Bd, Q=Q)


def test_every_detector_ran(run):
    assert (run["ran"]["status"] == "ran").all(), run["ran"]


def test_shared_farm_ids_found_with_own_record_named(run):
    """Stack rule (owner 2026-10-08): a farm with a matching own record keeps that row and its
    same-capacity copies are excluded, so farms 108 (Aniak) and 377 (Brevig Mission) no longer
    stack; the four orphan farms (no matching row) stay flagged for the decision queue."""
    F, n = run["F"], run["nfac"]
    s = F[F["detector"] == "shared_farm_id"]
    farms = set(s["group_key"])
    assert {"farm:710", "farm:179", "farm:415", "farm:694"} <= farms          # orphan farms, undecided
    assert not {"farm:108", "farm:377"} & farms                                 # resolved by exclusion
    assert (n["tank_farm_id"] == "108").sum() == 1 and n[n["tank_farm_id"] == "108"]["community_name"].iloc[0] == "Aniak"
    assert "NO record labelled" in " ".join(s[s["group_key"] == "farm:710"]["detail"])
    assert (s["severity"] == "info").sum() == 0, "no orphan farm has an own record"


def test_guarded_exclusion_retires_when_farm_id_changes(run):
    """An exclude row with old_value 'tank_farm_id=N' is skipped (not applied) once upstream changes N."""
    corr = qc.corrections()
    ex = corr[(corr["field"] == "exclude") & corr["old_value"].str.startswith("tank_farm_id=")]
    assert len(ex) == 27
    fac = qc.read_release(LABEL).set_index("record_id")
    assert all(str(fac.at[r.record_id, "tank_farm_id"]) == r.old_value.split("=")[1] for r in ex.itertuples())


def test_corrected_errors_are_no_longer_flagged(run):
    """Bethel typo and the Unalaska swap are fixed by approved corrections -> not re-flagged."""
    n = run["nfac"]
    F, Bf = run["F"], run["Bf"]
    bethel = n[(n["community_name"] == "Bethel")]["record_id"]
    assert not F[F["record_id"].isin(bethel) & (F["detector"] == "one_digit_typo")].shape[0]
    una = n[n["community_name"] == "Unalaska"]["record_id"]
    assert not Bf[Bf["record_id"].isin(una) & (Bf["priority"] == "review")].shape[0]


def test_detector_skips_when_column_missing(run):
    n = run["nfac"].drop(columns=["tank_farm_id"])
    for name, needs, fn in det_mod.REGISTRY:
        if "tank_farm_id" in needs:
            assert any(c not in n.columns for c in needs)


def test_boundary_check_never_changes_data(run):
    """Flags reference records; the normalised table is untouched and no untested community is flagged."""
    Bf, n = run["Bf"], run["nfac"]
    assert set(Bf["record_id"]) <= set(n["record_id"])
    assert "Anchorage" not in set(Bf["community_name"])              # no boundary -> untested, kept
    s = run["Bs"].set_index("outcome")["records"]
    assert s["untested: no boundary for this community"] > 0


def test_boundary_review_flags_catch_known_pending_cases(run):
    """Pending (undecided) known errors stay flagged, marked covered by their pending correction."""
    Bf = run["Bf"]
    craig = Bf[Bf["community_name"] == "Craig"]
    assert len(craig) and (craig["covered_by"] == "correction:pending").any()


def test_outside_is_reported_but_never_reviewed(run):
    """Owner 2026-10-08: a labelled site outside every boundary is a remote site, not a review item.
    It stays in the flags (priority info) and its distance is published for the hub builder."""
    Bf, Bd, Q = run["Bf"], run["Bd"], run["Q"]
    out = Bf[Bf["outcome"] == "outside"]
    assert len(out) and (out["priority"] == "info").all()
    assert not (Q["detector"] == "boundary_outside").any()
    assert (Q["detector"] == "boundary_mismatch").any(), "far mismatches (inside another community) are still reviewed"
    near = Bf[(Bf["outcome"] == "mismatch") & (Bf["own_boundary_km"].astype(float) <= qc.thresholds()["boundary_review_km"])]
    assert len(near) and (near["priority"] == "info").all(), "a neighbouring Census place is the same town"
    assert not set(Q.loc[Q["detector"] == "boundary_mismatch", "record_id"]) & set(near["record_id"])
    assert set(Q.loc[Q["detector"] == "boundary_mismatch", "priority"]) == {"review"}
    assert set(Bd["outcome"]) == {"match", "mismatch", "outside", "untested"}
    assert Bd["record_id"].is_unique and len(Bd) == run["nfac"]["latitude"].notna().sum()
    assert set(Bd["community_relation"]) == {"inside", "adjacent", "remote", "elsewhere", "untested"}
    rel = Bd.set_index("record_id")["community_relation"]
    assert (rel[out["record_id"]] == "remote").all()
    far = Bf[(Bf["outcome"] == "mismatch") & (Bf["priority"] == "review")]["record_id"]
    assert (rel[far] == "elsewhere").all()
    # located_in_place is where the point physically sits; the label is untouched
    n = run["nfac"].set_index("record_id")
    kenai = Bd[(Bd["located_in_place"] == "Nikiski") & (n.loc[Bd["record_id"], "community_name"].values == "Kenai")]
    assert len(kenai) and set(kenai["community_relation"]) == {"adjacent"}


def test_review_queue_excludes_decided_records(run):
    Q = run["Q"]
    corr = qc.corrections()
    assert not set(Q["record_id"]) & set(corr["record_id"])
    assert set(Q["decision"].unique()) <= {""}


# The 12 capacity discrepancies the 2026-11 Astra audit surfaced (owner 2026-11-14: all are
# review items). Six where the populated fuel sum EXCEEDS the total (a physical contradiction)
# and six where it falls short (possibly an incomplete breakdown).
CAPACITY_EXCEEDS = {
    "{EDA71B0B-E7D6-4E52-BD75-CDA27756C3FE}",   # Ambler temp airstrip storage: 2,000 vs 4,000
    "{57802F02-1FE2-4D07-A325-DC027155B116}",   # Chevak Company Corp. store
    "{199DCD38-B4D0-4C40-B569-F661EB0257D1}",   # City of Chuathbaluk
    "{9BA9AAC2-A297-4D86-BA33-73597A255D86}",   # City of Clark's Point
    "{44244771-16B8-40ED-9FF2-2D77E405955A}",   # Thomas Fuel Sales, Crooked Creek
    "{4EA87B2D-C068-44CC-970C-0D53111ACA7E}",   # New Koliganek Village Council: 20,000 vs 175,000
}
CAPACITY_BELOW = {
    "{96E5368E-7124-4460-A687-759DC084F019}",   # Elfin Cove Fuel Co.
    "{748B2C47-6F53-4F18-A713-48B459244BC0}",   # Emmonak Corporation
    "{60AC36FC-11A2-4126-B20C-4FC3BB51A21A}",   # Galena Power Plant
    "{1F3E5119-0B67-402E-BCC6-A6FB3D649C1A}",   # Puvurnaq Power Company
    "{268070AA-D83E-449C-BB0D-3A25985D3464}",   # Levelock Village Council
    "{ED4F5011-31F9-4D8C-88A0-EED50DDE9C4C}",   # Annette Island Gas Service
}


def test_capacity_mismatch_finds_the_twelve_audit_cases(run):
    """Components above the total are high, below are medium; every one reaches the owner's
    queue (2026-11-14) and none carries a suggested value — never repaired by arithmetic."""
    c = run["F"][run["F"]["detector"] == "capacity_mismatch"]
    assert set(c.loc[c["severity"] == "high", "record_id"]) == CAPACITY_EXCEEDS
    assert set(c.loc[c["severity"] == "medium", "record_id"]) == CAPACITY_BELOW
    assert c["suggested_value"].fillna("").eq("").all()
    q = run["Q"][run["Q"]["detector"] == "capacity_mismatch"]
    assert set(q["record_id"]) == CAPACITY_EXCEEDS | CAPACITY_BELOW


def test_placeholder_inspection_dates_are_info_not_review(run):
    """The 9 surviving pre-1900 placeholder dates (Esri 1899-12-30 epoch) are recorded as info
    flags — the paper trail for 07_publish blanking them — and never become review items."""
    p = run["F"][run["F"]["detector"] == "placeholder_inspection_date"]
    assert len(p) == 9 and (p["severity"] == "info").all()
    assert p["detail"].str.contains("1899").all()
    assert not (run["Q"]["detector"] == "placeholder_inspection_date").any()


def test_alaska_envelope_is_clean_on_the_corrected_release(run):
    """The envelope guard exists for FUTURE releases: on the corrected 2025 table every located
    record is inside lat 50..72 / lon <= -129 or >= 170, so it must flag nothing."""
    assert (run["ran"].loc[run["ran"]["detector"] == "alaska_envelope", "status"] == "ran").all()
    assert not (run["F"]["detector"] == "alaska_envelope").any()
