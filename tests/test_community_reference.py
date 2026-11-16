"""tools/input_prep/build_community_reference.py: the committed DCRA community reference is what
its two committed snapshots give, joined by community GUID, without touching the network."""
import importlib.util

import pandas as pd

import repo_paths as rp

spec = importlib.util.spec_from_file_location(
    "build_community_reference", rp.ROOT / "tools" / "input_prep" / "build_community_reference.py")
bcr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bcr)


def _ref():
    return pd.read_csv(bcr.REFERENCE_CSV, dtype=str, keep_default_na=False)


def test_committed_reference_is_derived_from_the_snapshots():
    assert bcr.main(["--check"]) == 0


def test_one_row_per_community_and_every_overview_row_joins():
    ref = _ref()
    assert ref["community_id"].is_unique
    assert list(ref.columns) == bcr.REFERENCE_COLUMNS
    overview_ids = set(bcr.read_overview()["CommunityID"])
    assert overview_ids <= set(ref["community_id"])
    assert set(ref.loc[ref["in_overview"] == "1", "community_id"]) == overview_ids


def test_no_staff_fields_are_written():
    header = bcr.LOCATIONS_CSV.read_text(encoding="utf-8").splitlines()[0].split(",")
    for banned in ("created_user", "last_edited_user", "Comments", "created_date", "last_edited_date"):
        assert banned not in header


def test_lon_lat_come_from_the_geometry():
    from pyproj import Transformer
    ref = _ref()
    x, y = Transformer.from_crs(4326, 3338, always_xy=True).transform(
        pd.to_numeric(ref["lon"]).values, pd.to_numeric(ref["lat"]).values)
    assert (abs(x - pd.to_numeric(ref["x_3338"])) < 1).all()
    assert (abs(y - pd.to_numeric(ref["y_3338"])) < 1).all()
    assert pd.to_numeric(ref["lat"]).between(51, 72).all()
