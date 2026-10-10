"""Cities with a precomputed heat store (compute once, look up many).

Region tags feed the recreated IMD rule (plains / coastal / hills); they are a
simple documented lookup, not IMD's own station classification.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    key: str
    name: str
    lat: float
    lon: float
    region: str
    river: tuple[float, float] | None = None   # GloFAS river grid point for flood signals


CITIES: dict[str, City] = {c.key: c for c in [
    City("chennai", "Chennai", 13.08, 80.27, "coastal"),
    City("delhi", "Delhi", 28.61, 77.21, "plains"),
    City("nagpur", "Nagpur", 21.15, 79.09, "plains"),
    City("ahmedabad", "Ahmedabad", 23.02, 72.57, "plains"),
    City("kharghar", "Kharghar, Navi Mumbai", 19.04, 73.07, "coastal"),
    City("bhubaneswar", "Bhubaneswar", 20.30, 85.82, "coastal"),
    City("hyderabad", "Hyderabad", 17.39, 78.49, "plains"),
    City("lucknow", "Lucknow", 26.85, 80.95, "plains"),
    City("jaipur", "Jaipur", 26.91, 75.79, "plains"),
    City("kolkata", "Kolkata", 22.57, 88.36, "coastal"),
    City("guwahati", "Guwahati", 26.14, 91.74, "plains", river=(26.17, 91.70)),   # Brahmaputra main channel cell
    City("patna", "Patna", 25.59, 85.14, "plains", river=(25.62, 85.15)),         # Ganga
]}


def nearest_city(lat: float, lon: float, max_km: float = 60.0) -> City | None:
    from heatcore.places import distance_km
    best = min(CITIES.values(), key=lambda c: distance_km(lat, lon, c.lat, c.lon))
    return best if distance_km(lat, lon, best.lat, best.lon) <= max_km else None


def get_city(key: str) -> City:
    k = key.strip().lower().replace(" ", "")
    if k not in CITIES:
        raise KeyError(f"unknown city '{key}'. Known: {', '.join(CITIES)}")
    return CITIES[k]
