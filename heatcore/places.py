"""Nearest drinking-water and shade points (haversine on cached OpenStreetMap + community points)."""

import math

EARTH_KM = 6371.0


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_KM * math.asin(math.sqrt(a))


def nearest(points: list[dict], lat: float, lon: float, k: int = 3, max_km: float = 5.0,
            kinds: tuple[str, ...] | None = None) -> list[dict]:
    out = []
    for p in points:
        if kinds and p["kind"] not in kinds:
            continue
        d = distance_km(lat, lon, p["lat"], p["lon"])
        if d <= max_km:
            out.append({**p, "distance_m": int(round(d * 1000, -1))})
    return sorted(out, key=lambda p: p["distance_m"])[:k]


def map_link(lat: float, lon: float) -> str:
    return f"https://maps.google.com/?q={lat:.5f},{lon:.5f}"
