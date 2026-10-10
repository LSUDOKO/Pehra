"""Fetch drinking-water and shade points per city from OpenStreetMap (ODbL) and cache them.

    uv run python scripts/fetch_osm_points.py [--cities delhi,chennai] [--upload BUCKET]

The public Overpass API is rate-limited, so this runs offline (compute once); the bot only reads
places/{city}.json. Writes out/places/{city}.json and optionally uploads to the heat bucket.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parents[1]))

from heatcore.cities import CITIES  # noqa: E402

MIRRORS = ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
           "https://overpass.private.coffee/api/interpreter")
HEADERS = {"User-Agent": "invisible-heat-hackathon/0.2 (github.com/LSUDOKO/Pehra)"}
RADIUS_M = 15000
OUT = Path("out/places")


def query(lat: float, lon: float) -> str:
    a = f"(around:{RADIUS_M},{lat},{lon})"
    return (f"[out:json][timeout:60];("
            f"nwr{a}[amenity=drinking_water];nwr{a}[amenity=water_point];"
            f"nwr{a}[drinking_water=yes][amenity!=toilets];nwr{a}[amenity=shelter];"
            f");out center 2000;")


def kind_of(tags: dict) -> str:
    if tags.get("amenity") == "shelter":
        return "shelter"
    if tags.get("amenity") == "water_point":
        return "water_point"
    return "drinking_water"


def fetch(lat: float, lon: float) -> list[dict]:
    last = None
    for attempt in range(6):
        url = MIRRORS[attempt % len(MIRRORS)]
        try:
            r = requests.post(url, data={"data": query(lat, lon)}, headers=HEADERS, timeout=90)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("application/json"):
                pts = []
                for el in r.json()["elements"]:
                    c = el if "lat" in el else el.get("center")
                    if not c:
                        continue
                    tags = el.get("tags", {})
                    pts.append({"lat": round(c["lat"], 6), "lon": round(c["lon"], 6), "kind": kind_of(tags),
                                "name": (tags.get("name") or tags.get("name:en") or "")[:60],
                                "osm": f"{el['type']}/{el['id']}"})
                return pts
            last = f"{r.status_code} from {url}"
        except requests.RequestException as e:
            last = str(e)
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"overpass failed: {last}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", default=",".join(CITIES))
    ap.add_argument("--upload")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for key in a.cities.split(","):
        c = CITIES[key]
        pts = fetch(c.lat, c.lon)
        doc = {"city": key, "source": "OpenStreetMap contributors (ODbL)", "radius_m": RADIUS_M,
               "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "points": pts}
        (OUT / f"{key}.json").write_text(json.dumps(doc))
        counts = {k: sum(p["kind"] == k for p in pts) for k in ("drinking_water", "water_point", "shelter")}
        print(f"{c.name:24s} {len(pts):5d} points {counts}")
        if a.upload:
            import boto3
            boto3.client("s3").upload_file(str(OUT / f"{key}.json"), a.upload, f"places/{key}.json",
                                           ExtraArgs={"ContentType": "application/json"})
        time.sleep(5)


if __name__ == "__main__":
    main()
