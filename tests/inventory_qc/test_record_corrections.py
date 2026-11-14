"""The scripted half of record-facility-corrections: a filled review queue -> correction rows.
Never decides, validates values, asks instead of guessing."""
import importlib.util

import pandas as pd

import repo_paths as rp
ROOT = rp.ROOT
S = ROOT / ".claude" / "skills" / "record-facility-corrections" / "scripts" / "record_corrections.py"
spec = importlib.util.spec_from_file_location("rc", S); rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)
LABEL = rc.qc.latest_release()
Q = pd.read_csv(rp.INVENTORY_QC_OUT / LABEL / "review_queue.csv", dtype=str, keep_default_na=False)
# The live queue shrinks as the owner decides (2 rows, one record, after the 2026-11-14 reviews);
# the fixture needs six rows with DISTINCT records, so dedupe then pad with queue-shaped rows for
# published records that carry no correction yet (plan() refuses already-decided (record, field)
# pairs, and a duplicated record would make two decisions collide on one id).
Q = Q.drop_duplicates("record_id").reset_index(drop=True)
if len(Q) < 6:
    _fac = pd.read_csv(rp.INVENTORY_QC_OUT / LABEL / "facilities_clean.csv", dtype=str, keep_default_na=False)
    _fac = _fac[~_fac["record_id"].isin(set(rc.qc.corrections()["record_id"])) & ~_fac["record_id"].isin(set(Q["record_id"]))]
    _pad = pd.DataFrame("", index=range(6 - len(Q)), columns=Q.columns)
    _take = _fac.head(6 - len(Q)).reset_index(drop=True)
    for _c in Q.columns:
        if _c in _take.columns:
            _pad[_c] = _take[_c]
    _pad["source"] = "boundary"
    _pad["detector"] = "boundary_mismatch"
    _pad["priority"] = "review"
    _pad["detail"] = "synthetic fixture row (see header comment)"
    Q = pd.concat([Q, _pad], ignore_index=True)


def _filled(**over):
    q = Q.head(6).copy()
    q["decision"] = ["approve with my value", "reject", "remote site", "skip for now", "exclude", ""]
    q["your_value"] = ["Unalaska", "", "", "", "", ""]
    q["notes"] = ["owner: label fix", "", "repeater", "", "copy row", ""]
    q["reviewed_by"] = "JC"; q["reviewed_on"] = "2026-10-08"
    for k, v in over.items():
        q.loc[0, k] = v
    return q


def test_each_decision_maps_to_the_right_row():
    corr, remote, questions = rc.plan(_filled(), LABEL, "test.xlsx")
    assert not questions
    by = corr.set_index("record_id")
    assert by.loc[Q.record_id[0], "field"] == "community_name" and by.loc[Q.record_id[0], "new_value"] == "Unalaska"
    assert by.loc[Q.record_id[0], "old_value"] == Q.community_name[0] or by.loc[Q.record_id[0], "old_value"] != ""
    assert by.loc[Q.record_id[1], "field"] == "(no change)" and by.loc[Q.record_id[1], "status"] == "rejected"
    assert list(remote["record_id"]) == [Q.record_id[2]]
    assert by.loc[Q.record_id[3], "status"] == "pending"
    assert by.loc[Q.record_id[4], "field"] == "exclude" and by.loc[Q.record_id[4], "status"] == "approved"
    assert Q.record_id[5] not in by.index, "an undecided row writes nothing"
    assert (corr["reviewer"] == "JC").all() and (corr["reviewed_on"] == "2026-10-08").all()


def test_coordinates_are_parsed_and_range_checked():
    corr, _, questions = rc.plan(_filled(your_value="61.5, -150.1"), LABEL, "t")
    me = corr[corr.record_id == Q.record_id[0]]
    assert set(me["field"]) == {"latitude", "longitude"} and set(me["new_value"]) == {"61.5", "-150.1"}
    _, _, questions = rc.plan(_filled(your_value="61.5, 150.1", detector="one_digit_typo"), LABEL, "t")
    assert questions and "west negative" in questions[0][1]


def test_ambiguity_becomes_a_question_not_a_row():
    q = _filled(); q.loc[1, "your_value"] = "Nome"                     # reject with a value
    corr, _, questions = rc.plan(q, LABEL, "t")
    assert any("reject but your_value" in m for _, m in questions) and Q.record_id[1] not in set(corr.record_id)
    q = _filled(); q.loc[0, "reviewed_on"] = "2099-01-01"
    _, _, questions = rc.plan(q, LABEL, "t")
    assert any("future" in m for _, m in questions)
    q = _filled(); q.loc[0, "reviewed_by"] = ""
    _, _, questions = rc.plan(q, LABEL, "t")
    assert any("reviewed_by" in m for _, m in questions)
