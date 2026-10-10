"""Build 1991-2020 tmax/tmin normals (and flood percentiles for river cities) once, offline.

    uv run python scripts/build_normals.py --upload BUCKET

Uses the audit's cached ERA5 daily files when present (out/audit/cache/{city}_daily2.json),
so it adds no load on the free archive API. Writes normals/{city}.json to the heat bucket.
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from heatcore.cities import CITIES  # noqa: E402
from heatcore.climatology import normals_by_mmdd  # noqa: E402
from heatcore.flood import percentile  # noqa: E402
from heatcore.openmeteo import fetch_daily, fetch_flood  # noqa: E402

CACHE = Path("out/audit/cache")


def daily(key: str) -> tuple[dict, dict]:
    p = CACHE / f"{key}_daily2.json"
    if p.exists():
        d = json.loads(p.read_text())["daily"]
        tx = {t: v for t, v in zip(d["time"], d["temperature_2m_max"], strict=True) if v is not None}
        tn = {t: v for t, v in zip(d["time"], d["temperature_2m_min"], strict=True) if v is not None}
        return tx, tn
    c = CITIES[key]
    d = fetch_daily(c.lat, c.lon, "1991-01-01", "2020-12-31", ("temperature_2m_max", "temperature_2m_min"))
    return d["temperature_2m_max"], d["temperature_2m_min"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upload")
    a = ap.parse_args()
    out_dir = Path("out/normals")
    out_dir.mkdir(parents=True, exist_ok=True)
    for key, c in CITIES.items():
        tx, tn = daily(key)
        doc = {"tmax": normals_by_mmdd(tx), "tmin": normals_by_mmdd(tn)}
        if c.river:
            hist = fetch_flood(*c.river, start="1991-01-01", end="2020-12-31")
            if any(h is not None for h in hist):
                doc["flood"] = {"p95": percentile(hist, 0.95), "p99": percentile(hist, 0.99)}
            time.sleep(3)
        (out_dir / f"{key}.json").write_text(json.dumps(doc))
        print(f"{c.name:24s} tmin normals {len(doc['tmin'])}  flood {doc.get('flood')}")
        if a.upload:
            import boto3
            boto3.client("s3").upload_file(str(out_dir / f"{key}.json"), a.upload, f"normals/{key}.json",
                                           ExtraArgs={"ContentType": "application/json"})


if __name__ == "__main__":
    main()
