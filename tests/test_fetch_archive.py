"""tools/fetch_archive.py: the deposit-to-folder contract, without touching the network."""
import hashlib
import importlib.util
import zipfile

import pytest

import repo_paths as rp

spec = importlib.util.spec_from_file_location("fetch_archive", rp.ROOT / "tools" / "fetch_archive.py")
fa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fa)


def test_every_group_unpacks_where_the_pipeline_reads():
    assert fa.GROUPS["friction_inputs"]["dest"] == rp.FRICTION_RASTERS
    assert fa.GROUPS["friction_stack"]["dest"] == rp.FRICTION_STACK
    assert "network_raw" not in fa.GROUPS  # workflow 02's raw layers are downloads or in git
    assert fa.GROUPS["river_ice_work"]["dest"] == rp.RIVER_ICE_WORK


@pytest.mark.parametrize("given", [
    "1234567", "10.5281/zenodo.1234567", "https://doi.org/10.5281/zenodo.1234567",
    "https://zenodo.org/records/1234567", "https://zenodo.org/record/1234567/",
])
def test_record_id_is_read_from_any_spelling(given):
    assert fa.resolve_record_id(given) == "1234567"


def test_record_files_reads_zenodo_json():
    record = {"files": [{"key": "friction_stack.zip", "size": 3,
                         "checksum": "md5:abc", "links": {"self": "https://x/y"}}]}
    assert fa.record_files(record) == {"friction_stack.zip": {"url": "https://x/y", "md5": "abc", "size": 3}}


def _make_zip(path, members):
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return hashlib.md5(path.read_bytes()).hexdigest()


def test_install_group_verifies_md5_and_unpacks(tmp_path, monkeypatch):
    monkeypatch.setattr(fa, "ROOT", tmp_path)
    dest = tmp_path / "outputs" / "01_friction_build" / "friction_stack"
    monkeypatch.setitem(fa.GROUPS, "friction_stack", {**fa.GROUPS["friction_stack"], "dest": dest})
    src = tmp_path / "upload.zip"
    md5 = _make_zip(src, {"road_base.tif": b"r", "barge_01.tif": b"b"})
    files = {"friction_stack.zip": {"url": "u", "md5": md5, "size": src.stat().st_size}}

    def fake_download(url, cache):
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(src.read_bytes())

    fa.install_group("friction_stack", files, downloader=fake_download)
    assert (dest / "road_base.tif").read_bytes() == b"r"
    assert (dest / "barge_01.tif").exists()
    assert (tmp_path / ".archive" / "friction_stack.zip").exists()  # kept for re-runs


def test_install_group_rejects_a_corrupt_download(tmp_path, monkeypatch):
    monkeypatch.setattr(fa, "ROOT", tmp_path)
    dest = tmp_path / "stack"
    monkeypatch.setitem(fa.GROUPS, "friction_stack", {**fa.GROUPS["friction_stack"], "dest": dest})
    src = tmp_path / "upload.zip"
    _make_zip(src, {"road_base.tif": b"r"})
    files = {"friction_stack.zip": {"url": "u", "md5": "0" * 32, "size": 1}}

    def fake_download(url, cache):
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(src.read_bytes())

    with pytest.raises(SystemExit, match="md5 mismatch"):
        fa.install_group("friction_stack", files, downloader=fake_download)
    assert not (tmp_path / ".archive" / "friction_stack.zip").exists()
    assert not dest.exists()


def test_members_rooted_at_the_folder_name_unpack_one_level_up(tmp_path):
    src = tmp_path / "z.zip"
    _make_zip(src, {"friction_rasters/a.tif": b"a", "friction_rasters/sea_ice/b.tif": b"b"})
    dest = tmp_path / "inputs" / "friction_rasters"
    fa.unpack(src, dest)
    assert (dest / "a.tif").exists() and (dest / "sea_ice" / "b.tif").exists()


def test_without_a_record_the_script_gates_like_a_driver(capsys):
    assert fa.ZENODO_RECORD is None or fa.resolve_record_id(fa.ZENODO_RECORD)
    rc = fa.main(["--record", ""])
    assert rc == fa.GATE_EXIT
    assert "GATE" in capsys.readouterr().out
