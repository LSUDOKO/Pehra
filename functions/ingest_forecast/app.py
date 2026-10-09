"""Fetch the forecast twice a day, compute WBGT once per city, store it on S3.

Every site plan later reads heat/{city}/latest.json; nothing else calls a weather API.
"""

from datetime import UTC, datetime

from heatcore.cities import CITIES
from heatcore.heat import compute_heat, heat_to_json
from heatcore.openmeteo import fetch_forecast, parse_hourly
from ihcommon import heatstore, repo
from ihcommon.log import log, metric

MODEL = "Open-Meteo best_match"


def ingest_city(key: str, now: datetime) -> dict:
    city = CITIES[key]
    rows = parse_hourly(fetch_forecast(city.lat, city.lon, days=4))
    heat = compute_heat(rows, city.lat, city.lon)
    run_id = now.strftime("%Y%m%dT%H%MZ")
    doc = {"city": key, "run_id": run_id, "model": MODEL, "issued_at": now.isoformat(),
           "lat": city.lat, "lon": city.lon, "hours": heat_to_json(heat)}
    s3_key = heatstore.put_heat(key, run_id, doc)
    t = repo.table()
    for sk in (f"RUN#{run_id}", "LATEST"):
        t.put_item(Item={"PK": f"HEAT#{key}", "SK": sk, "s3_key": s3_key,
                         "issued_at": now.isoformat(), "ttl": repo.ttl_in(30)})
    return {"city": key, "hours": len(heat), "s3_key": s3_key}


def handler(event, _ctx):
    now = datetime.now(UTC).replace(second=0, microsecond=0)
    cities = (event or {}).get("cities") or list(CITIES)
    done, failed = [], []
    for key in cities:
        try:
            done.append(ingest_city(key, now))
        except Exception as e:  # one bad city must not block the rest
            failed.append(key)
            log("ingest_failed", city=key, error=str(e))
    metric("ForecastIngested", len(done))
    if failed:
        metric("ForecastIngestFailed", len(failed))
    log("ingest_done", ok=len(done), failed=failed)
    return {"ok": done, "failed": failed}
