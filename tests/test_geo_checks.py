"""fuel_network.geo_checks — the shared geospatial check primitives.

Raster-free where possible; the raster cases build tiny synthetic GeoTIFFs in
tmp_path so CI needs no project data.
"""
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import LineString

from fuel_network import geo_checks as gc


def _write(path, arr, origin=(0.0, 300.0), px=150.0, nodata=None):
    h, w = arr.shape
    with rasterio.open(
            path, "w", driver="GTiff", height=h, width=w, count=1,
            dtype=arr.dtype, crs="EPSG:3338",
            transform=from_origin(origin[0], origin[1], px, px),
            nodata=nodata) as dst:
        dst.write(arr, 1)
    return path


def test_sample_along_uses_midpoint_sampler(tmp_path):
    # 2x4 raster: left half 1, right half NoData
    arr = np.array([[1, 1, -9999, -9999]] * 2, dtype="float32")
    tif = _write(tmp_path / "s.tif", arr, nodata=-9999.0)
    line = LineString([(0, 150), (600, 150)])  # crosses both halves
    xy, seg_len, owner, vals = gc.sample_along([line], [0], tif)
    assert len(xy) == len(seg_len) == len(owner) == len(vals)
    assert (owner == 0).all()
    assert (vals == -9999.0).any() and (vals == 1).any()
    # length weights must sum to the line length
    assert pytest.approx(seg_len.sum(), rel=1e-6) == line.length


def test_per_feature_nodata_fraction(tmp_path):
    arr = np.array([[1, 1, -9999, -9999]] * 2, dtype="float32")
    tif = _write(tmp_path / "s.tif", arr, nodata=-9999.0)
    xy, seg_len, owner, vals = gc.sample_along(
        [LineString([(0, 150), (600, 150)])], [0], tif)
    _, ndf = gc.per_feature_nodata(owner, seg_len, vals, 1, -9999.0)
    assert 0.3 < ndf[0] < 0.7  # half the line over NoData


def test_nearest_class_distance(tmp_path):
    arr = np.zeros((10, 10), dtype="uint8")
    arr[2, 7] = 1  # one target pixel
    tif = _write(tmp_path / "c.tif", arr, origin=(0.0, 1500.0))
    km, px = gc.nearest_class_distance(tif, 75.0, 1425.0, 1, max_km=5)  # pixel (0,0) centre
    assert px is not None
    # target centre at col 7, row 2 -> dx=7 px, dy=2 px
    assert pytest.approx(km * 1000, rel=1e-3) == np.hypot(7, 2) * 150
    km2, px2 = gc.nearest_class_distance(tif, 75.0, 1425.0, 9, max_km=5)  # absent value
    assert np.isnan(km2) and px2 is None


def test_grid_matches(tmp_path):
    a = _write(tmp_path / "a.tif", np.zeros((4, 4), dtype="uint8"))
    b = _write(tmp_path / "b.tif", np.zeros((4, 4), dtype="uint8"))
    c = _write(tmp_path / "c.tif", np.zeros((4, 5), dtype="uint8"))
    ok, msg = gc.grid_matches(a, b)
    assert ok and msg == ""
    ok, msg = gc.grid_matches(a, c)
    assert not ok and "shape" in msg


def test_endpoint_distances():
    targets = np.array([[0.0, 0.0], [100.0, 0.0]])
    d = gc.endpoint_distances([(0.0, 0.0), (103.0, 4.0)], targets)
    assert pytest.approx(d[0], abs=1e-9) == 0.0
    assert pytest.approx(d[1], rel=1e-6) == np.hypot(3, 4)
