"""Forecast + context for any location, computed once per city or 0.25-degree tile and cached on S3.

Fixed cities are refreshed by the scheduled ingest. A personal user anywhere in India maps to a
tile; the first request for a tile computes it and every other user in that tile reuses it.
"""

import json
from datetime import UTC, datetime, timedelta

import boto3
from botocore.exceptions import ClientError

from heatcore.cities import CITIES, nearest_city
from heatcore.climatology import normals_by_mmdd
from heatcore.flood import classify, percentile
from heatcore.heat import compute_heat, heat_to_json, wx_rows
from heatcore.nights import night_summary, warm_night
from heatcore.openmeteo import fetch_daily, fetch_flood, fetch_forecast, parse_hourly
from heatcore.rain import daily_rain
from ihcommon import config

MODEL = "Open-Meteo best_match"
TILE_DEG = 0.25
CITY_RADIUS_KM = 25.0
MAX_AGE = timedelta(hours=12)


def location_key(lat: float, lon: float) -> tuple[str, float, float, tuple | None]:
    """(key, lat, lon, river point) - a fixed city if within 25 km, else a 0.25-degree tile."""
    c = nearest_city(lat, lon, CITY_RADIUS_KM)
    if c:
        return c.key, c.lat, c.lon, c.river
    tl = round(round(lat / TILE_DEG) * TILE_DEG, 2)
    tn = round(round(lon / TILE_DEG) * TILE_DEG, 2)
    return f"t{tl:.2f}_{tn:.2f}", tl, tn, None


def build_doc(key: str, lat: float, lon: float, now: datetime, river=None) -> dict:
    payload = fetch_forecast(lat, lon, days=4)
    heat = compute_heat(parse_hourly(payload), lat, lon)
    doc = {"city": key, "run_id": now.strftime("%Y%m%dT%H%MZ"), "model": MODEL,
           "issued_at": now.isoformat(), "lat": lat, "lon": lon,
           "hours": heat_to_json(heat), "wx": wx_rows(payload)}
    if river:
        try:
            doc["flood_forecast"] = fetch_flood(*river, days=7)
        except Exception:
            doc["flood_forecast"] = None
    return doc


def _s3():
    return boto3.client("s3", region_name=config.REGION)


def _get_json(key: str) -> dict | None:
    try:
        return json.loads(_s3().get_object(Bucket=config.HEAT_BUCKET, Key=key)["Body"].read())
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return None
        raise


def _put_json(key: str, doc: dict) -> None:
    _s3().put_object(Bucket=config.HEAT_BUCKET, Key=key, Body=json.dumps(doc).encode(),
                     ContentType="application/json")


def get_doc(lat: float, lon: float, now: datetime | None = None) -> dict:
    """Latest forecast doc for a location; tiles are filled on demand."""
    now = now or datetime.now(UTC)
    key, klat, klon, river = location_key(lat, lon)
    doc = _get_json(f"heat/{key}/latest.json")
    fresh = doc and now - datetime.fromisoformat(doc["issued_at"]) < MAX_AGE
    if not fresh and (key.startswith("t") or doc is None):
        doc = build_doc(key, klat, klon, now.replace(second=0, microsecond=0), river)
        _put_json(f"heat/{key}/latest.json", doc)
    return doc


def get_normals(key: str, lat: float, lon: float, river=None) -> dict:
    """tmax/tmin normals per calendar day (1991-2020, ERA5) and flood percentiles; computed once."""
    cached = _get_json(f"normals/{key}.json")
    if cached:
        return cached
    d = fetch_daily(lat, lon, "1991-01-01", "2020-12-31", ("temperature_2m_max", "temperature_2m_min"))
    out = {"tmax": normals_by_mmdd(d["temperature_2m_max"]), "tmin": normals_by_mmdd(d["temperature_2m_min"])}
    if river:
        hist = fetch_flood(*river, start="1991-01-01", end="2020-12-31")
        if any(h is not None for h in hist):
            out["flood"] = {"p95": percentile(hist, 0.95), "p99": percentile(hist, 0.99)}
    _put_json(f"normals/{key}.json", out)
    return out


def conditions(doc: dict, normals: dict | None, day: str) -> dict:
    """Rain, night heat and river flood for one local day, all from code."""
    wx = doc.get("wx") or []
    out = {"rain": daily_rain(wx, day) if wx else None}
    night = night_summary(wx, day) if wx else {"night_min_c": None, "day_max_c": None}
    flag = "none"
    if normals and night["night_min_c"] is not None and night["day_max_c"] is not None:
        md = day[5:]
        if md in normals.get("tmin", {}):
            flag = warm_night(night["day_max_c"], night["night_min_c"], normals["tmin"][md])
            night["tmin_normal_c"] = normals["tmin"][md]
    night["warm_night"] = flag
    out["night"] = night
    ff = doc.get("flood_forecast")
    if ff and normals and normals.get("flood"):
        out["flood"] = classify(ff, normals["flood"]["p95"], normals["flood"]["p99"])
    return out


def city_doc_keys() -> list[str]:
    return list(CITIES)
