"""Stages 03b (facility ids from the append-only ledger) and 05b (AEA energy region) on the
committed release: the ledger reproduces every harness id, minting is explicit and appends only,
the region assignment describes (inside / nearest within the cap) and never moves a record, and
the two region tables the harness loads are complete and symmetric."""
import pytest

from inventory_qc import apply_corrections as apply_mod
from inventory_qc import assign_facility_ids as ids_mod
from inventory_qc import assign_region as reg_mod
from inventory_qc import core as qc
from inventory_qc import normalise as norm_mod

LABEL = qc.latest_release()
HAINES_MILE_42 = "{984C8F00-5900-483B-B4A1-43D255646FAC}"   # GSA - Haines, 4 km over the Canadian border


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("qc3")
    with pytest.MonkeyPatch.context() as mp:   # the stage modules are shared: undo OUT afterwards
        for m in (qc, apply_mod, norm_mod, ids_mod, reg_mod):
            mp.setattr(m, "OUT", tmp)
        fac, excl, log = apply_mod.apply(LABEL)
        qc.write_csv(fac, tmp / LABEL / "facilities_corrected.csv")
        nfac, _ = norm_mod.normalise(LABEL); qc.write_csv(nfac, tmp / LABEL / "facilities_normalised.csv")
        A, new_rows, problems = ids_mod.assign(LABEL)
        R, regions, adj = reg_mod.assign(LABEL)
        yield dict(tmp=tmp, nfac=nfac, A=A, new_rows=new_rows, problems=problems, R=R, regions=regions, adj=adj)


# ---------------------------------------------------------------- 03b facility ids

def test_every_located_record_has_a_unique_ledger_id(run):
    A, n = run["A"], run["nfac"]
    located = n["latitude"].notna() & n["longitude"].notna()
    assert not run["problems"], run["problems"]
    assert run["new_rows"].empty, "nothing is minted without --mint"
    ids = A.loc[A["facility_id"] != "", "facility_id"].astype(int)
    assert len(ids) == int(located.sum()) and ids.is_unique
    assert (A.loc[~located.values, "id_source"] == "unlocated").all()
    assert (A.loc[A["facility_id"] != "", "id_source"] == "ledger").all()


def test_ledger_reproduces_the_harness_rule(run):
    """AEA id where the record carries one; else the 2022 file-order synthetic id (1263..1943).
    No record's AEA id differs from its ledger id in the 2025 release."""
    A, n = run["A"], run["nfac"]
    m = A.merge(n[["record_id", "ast_facility_id"]], on="record_id")
    with_aea = m[(m["facility_id"] != "") & m["ast_facility_id"].notna()]
    assert (with_aea["facility_id"].astype(int) == with_aea["ast_facility_id"].astype(int)).all()
    synthetic = m[(m["facility_id"] != "") & m["ast_facility_id"].isna()]["facility_id"].astype(int)
    assert synthetic.between(1263, 1943).all()
    assert (A["aea_id_differs"] != "true").all()
    led = ids_mod.ledger()
    assert led["facility_id"].is_unique and led["record_id"].is_unique
    assert set(led["id_source"]) <= {"aea", "synthetic"}


def test_missing_id_fails_without_mint_and_appends_with_it(run, tmp_path, monkeypatch):
    """A located record absent from the ledger is a failure; --mint appends it (AEA id if it has one,
    else the next free number) and never touches an existing row."""
    led = ids_mod.ledger()
    short = led[led["record_id"] != HAINES_MILE_42]            # drop one record from a COPY of the ledger
    led_path = tmp_path / "facility_ids.csv"
    short.to_csv(led_path, index=False, lineterminator="\n")
    monkeypatch.setattr(ids_mod, "LEDGER", led_path)
    A, new_rows, problems = ids_mod.assign(LABEL)
    assert len(problems) == 1 and "no facility_id" in problems[0] and HAINES_MILE_42 in problems[0]
    assert (A.loc[A["record_id"] == HAINES_MILE_42, "id_source"] == "missing").all()
    A2, new_rows2, problems2 = ids_mod.assign(LABEL, mint=True)
    assert not problems2 and len(new_rows2) == 1
    row = new_rows2.iloc[0]
    assert row["record_id"] == HAINES_MILE_42 and row["id_source"] == "aea" and int(row["facility_id"]) == 857
    assert row["minted_from"] == LABEL
    # a record with no AEA id gets the next free number above every id in use
    short2 = led[led["id_source"] != "synthetic"].iloc[:0]      # empty ledger: everything is missing
    short2.to_csv(led_path, index=False, lineterminator="\n")
    A3, new_rows3, _ = ids_mod.assign(LABEL, mint=True)
    synth = new_rows3[new_rows3["id_source"] == "synthetic"]["facility_id"].astype(int)
    assert synth.min() > int(run["nfac"]["ast_facility_id"].dropna().astype(int).max())
    assert synth.is_unique and len(new_rows3) == int((A3["facility_id"] != "").sum())
    assert (led_path.read_text().count("\n") - 1) == 0, "assign() never writes the ledger; only main --mint does"


# ---------------------------------------------------------------- 05b AEA regions

def test_every_located_record_has_a_region_and_nothing_moves(run):
    R, n = run["R"], run["nfac"]
    located = n["latitude"].notna() & n["longitude"].notna()
    assert len(R) == len(n) and list(R["record_id"]) == list(n["record_id"])
    assert (R.loc[~located.values, "aea_region_relation"] == "untested").all()
    loc = R[located.values]
    assert loc["aea_region"].notna().all()
    assert set(loc["aea_region_relation"]) == {"inside", "nearest"}
    assert (loc.loc[loc["aea_region_relation"] == "inside", "aea_region_distance_km"] == 0).all()


def test_the_one_out_of_polygon_record_takes_the_nearest_region_within_the_cap(run):
    """Mile 42 Haines Highway (labelled Haines) sits 4 km into Canada: nearest region Southeast,
    the next 272 km away. Reported with its distance, never reviewed, never moved."""
    R = run["R"]
    near = R[R["aea_region_relation"] == "nearest"]
    assert list(near["record_id"]) == [HAINES_MILE_42]
    assert near["aea_region"].iloc[0] == "Southeast"
    assert 3.0 < float(near["aea_region_distance_km"].iloc[0]) < qc.thresholds()["aea_region_nearest_km"]


def test_region_tables_are_complete_and_symmetric(run):
    regions, adj, R = run["regions"], run["adj"], run["R"]
    assert len(regions) == 11 and regions["region_name"].is_unique
    assert regions["num_facilities"].sum() == int(R["aea_region"].notna().sum())
    pairs = set(zip(adj["region_a"], adj["region_b"]))
    assert len(pairs) == len(adj) and all((b, a) in pairs for a, b in pairs), "both directions of every pair"
    assert (adj["shared_border_m"] > 0).all()
    assert set(adj["region_a"]) <= set(regions["region_name"])


def test_beyond_the_cap_the_region_stays_blank(run, monkeypatch):
    monkeypatch.setattr(reg_mod, "thresholds", lambda: {"aea_region_nearest_km": 1.0})
    R, regions, _ = reg_mod.assign(LABEL)
    out = R[R["aea_region_relation"] == "outside"]
    assert list(out["record_id"]) == [HAINES_MILE_42] and out["aea_region"].isna().all()
    assert regions.set_index("region_name").at["Southeast", "num_facilities"] == \
        run["regions"].set_index("region_name").at["Southeast", "num_facilities"] - 1
