"""Mini Invisible Heat Audit: 10 cities, 2021-2025, ERA5 via the Open-Meteo archive.

    uv run python scripts/run_audit.py [--cities chennai,delhi] [--upload BUCKET]

Writes docs/results/audit_summary.json (+ agent/data copy), and per-day rows to
out/audit/days.csv (and days.parquet if pyarrow is installed). Raw API responses are
cached in out/audit/cache so reruns are offline.
"""

import argparse
import csv
import json
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1]))

from heatcore.audit import LIMIT_C, audit_city, daily_max_work_wbgt, summarise  # noqa: E402
from heatcore.cities import CITIES  # noqa: E402
from heatcore.openmeteo import ARCHIVE_URL, HOURLY_VARS, _get  # noqa: E402
from heatcore.wbgt import wbgt_arrays  # noqa: E402

START, END = "2021-01-01", "2025-12-31"
OUT = Path("out/audit")
CACHE = OUT / "cache"


def cached(name: str, params: dict) -> dict:
    p = CACHE / f"{name}.json"
    if p.exists():
        return json.loads(p.read_text())
    data = _get(ARCHIVE_URL, params)
    p.write_text(json.dumps(data))
    time.sleep(1)  # be gentle with the free API
    return data


def city_rows(key: str) -> list[dict]:
    c = CITIES[key]
    hourly = cached(f"{key}_hourly", {"latitude": c.lat, "longitude": c.lon, "start_date": START,
                                       "end_date": END, "hourly": ",".join(HOURLY_VARS),
                                       "wind_speed_unit": "ms", "timezone": "UTC"})["hourly"]
    daily = cached(f"{key}_daily", {"latitude": c.lat, "longitude": c.lon, "start_date": "1991-01-01",
                                     "end_date": END, "daily": "temperature_2m_max",
                                     "timezone": "Asia/Kolkata"})["daily"]
    labels = np.array(hourly["time"], dtype="datetime64[m]")
    centres = labels - np.timedelta64(30, "m")  # radiation is a preceding-hour mean
    arr = {v: np.array([np.nan if x is None else x for x in hourly[v]], float) for v in HOURLY_VARS}
    ok = ~np.isnan(np.column_stack(list(arr.values()))).any(axis=1)
    sun, shade = wbgt_arrays(c.lat, c.lon, centres[ok], arr["temperature_2m"][ok],
                             arr["relative_humidity_2m"][ok], arr["surface_pressure"][ok],
                             arr["wind_speed_10m"][ok], arr["shortwave_radiation"][ok],
                             arr["direct_radiation"][ok])
    ist = [datetime.fromisoformat(str(t)).replace(tzinfo=UTC) + timedelta(hours=5, minutes=30)
           for t in centres[ok]]
    by_day = daily_max_work_wbgt([(t.date().isoformat(), t.hour, float(s), float(h))
                                  for t, s, h in zip(ist, sun, shade, strict=True)])
    pairs = zip(daily["time"], daily["temperature_2m_max"], strict=True)
    tmax_all = {t: v for t, v in pairs if v is not None}
    tmax = {d: v for d, v in tmax_all.items() if START <= d <= END}
    return [{"city": key, **r} for r in audit_city(by_day, tmax, tmax_all, c.region)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", default=",".join(CITIES))
    ap.add_argument("--upload", help="S3 bucket for audit/ Parquet + summary")
    a = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    all_rows, districts = [], []
    for key in a.cities.split(","):
        rows = city_rows(key)
        all_rows += rows
        s = summarise(rows)
        districts.append({"city": CITIES[key].name, "key": key, "region": CITIES[key].region, **s})
        print(f"{CITIES[key].name:24s} invisible(shade) {s['invisible_days_shade']:4d}  "
              f"of which outside Mar-Jun {s['invisible_shade_outside_mar_jun']:4d}  "
              f"heatwave days {s['heatwave_days']:3d}")
    total = summarise(all_rows)
    summary = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"), "period": [START, END],
        "source": "ERA5 reanalysis via Open-Meteo archive (CC BY 4.0)", "limit_c": LIMIT_C,
        "definition": "Invisible heat day: WBGT in shade, 06-19 IST, above the NIOSH REL for moderate "
                      "work on at least one hour, with no heatwave under the recreated IMD rule.",
        "caveats": ["A minimum: ERA5 (~25 km) smooths humid extremes.",
                    "IMD rule recreated on one grid cell per city; not IMD's official record.",
                    "Shade WBGT; sun counts are higher and listed separately."],
        "total": total, "districts": districts}
    for p in (Path("docs/results/audit_summary.json"), Path("agent/data/audit_summary.json")):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(summary, indent=2))
    with (OUT / "days.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0]))
        w.writeheader()
        w.writerows(all_rows)
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        pq.write_table(pa.Table.from_pylist(all_rows), OUT / "days.parquet")
    except ImportError:
        print("pyarrow not installed; skipped Parquet")
    if a.upload:
        import boto3
        s3 = boto3.client("s3")
        if (OUT / "days.parquet").exists():
            s3.upload_file(str(OUT / "days.parquet"), a.upload, "audit/days/days.parquet")
        s3.upload_file("docs/results/audit_summary.json", a.upload, "audit/summary.json")
    print(json.dumps(total, indent=2))


if __name__ == "__main__":
    main()
