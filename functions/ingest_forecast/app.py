"""Fetch the forecast three times a day, compute WBGT, rain, night heat and river flow once per city.

Every site plan later reads heat/{city}/latest.json; nothing else calls a weather API for cities.
Normals (1991-2020) and flood percentiles are computed once per city and cached.
"""

from datetime import UTC, datetime

from heatcore.cities import CITIES
from ihcommon import heatstore, locdata, repo
from ihcommon.log import log, metric


def ingest_city(key: str, now: datetime) -> dict:
    city = CITIES[key]
    doc = locdata.build_doc(key, city.lat, city.lon, now, city.river)
    s3_key = heatstore.put_heat(key, doc["run_id"], doc)
    t = repo.table()
    for sk in (f"RUN#{doc['run_id']}", "LATEST"):
        t.put_item(Item={"PK": f"HEAT#{key}", "SK": sk, "s3_key": s3_key,
                         "issued_at": now.isoformat(), "ttl": repo.ttl_in(30)})
    try:
        locdata.get_normals(key, city.lat, city.lon, city.river)  # cached after the first run
    except Exception as e:
        log("normals_failed", city=key, error=str(e)[:200])
    return {"city": key, "hours": len(doc["hours"]), "s3_key": s3_key,
            "flood": doc.get("flood_forecast") is not None}


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
