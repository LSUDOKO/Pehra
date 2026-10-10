import json
from datetime import UTC, datetime

import boto3
import pytest

from ihcommon import config, locdata


@pytest.fixture
def bucket(ddb_table, monkeypatch):
    s3 = boto3.client("s3", region_name="ap-south-1")
    s3.create_bucket(Bucket="heat", CreateBucketConfiguration={"LocationConstraint": "ap-south-1"})
    monkeypatch.setattr(config, "HEAT_BUCKET", "heat")
    return s3


def test_location_key_city_or_tile():
    assert locdata.location_key(13.05, 80.25)[0] == "chennai"
    key, lat, lon, river = locdata.location_key(25.31, 83.01)  # Varanasi -> tile
    assert key == "t25.25_83.00" and (lat, lon) == (25.25, 83.0) and river is None
    assert locdata.location_key(25.6, 85.14)[3] == (25.62, 85.15)  # Patna has a river point


def test_tile_computed_once_then_cached(bucket, monkeypatch):
    calls = []

    def fake_build(key, lat, lon, now, river=None):
        calls.append(key)
        return {"city": key, "issued_at": now.isoformat(), "hours": [], "wx": []}

    monkeypatch.setattr(locdata, "build_doc", fake_build)
    now = datetime(2026, 10, 10, 6, 0, tzinfo=UTC)
    locdata.get_doc(25.31, 83.01, now)
    locdata.get_doc(25.30, 83.02, now)  # same tile
    assert calls == ["t25.25_83.00"]
    assert json.loads(bucket.get_object(Bucket="heat", Key="heat/t25.25_83.00/latest.json")["Body"].read())


def test_conditions_rain_night_and_flood():
    wx = [{"t": f"2026-05-01T{h:02d}:00:00", "temp": 42 if h == 14 else 33, "precip": 0, "pprob": 0}
          for h in range(24)] + [{"t": "2026-05-02T03:00:00", "temp": 31, "precip": 0}]
    doc = {"wx": wx, "flood_forecast": [100, 500]}
    normals = {"tmin": {"05-01": 25.0}, "flood": {"p95": 300, "p99": 600}}
    c = locdata.conditions(doc, normals, "2026-05-01")
    assert c["night"]["warm_night"] == "warm" and c["rain"]["category"] == "none"
    assert c["flood"]["level"] == "high"
