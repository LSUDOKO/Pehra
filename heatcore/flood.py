"""River-flood signal from GloFAS river discharge (Open-Meteo Flood API, CC BY 4.0).

Only meaningful at river grid points. Alert when forecast discharge passes the point's own
historical 95th percentile (severe above the 99th). A screening signal, not an official warning.
"""


def percentile(values: list[float], q: float) -> float:
    v = sorted(x for x in values if x is not None)
    if not v:
        raise ValueError("no discharge history")
    idx = (len(v) - 1) * q
    lo, hi = int(idx), min(int(idx) + 1, len(v) - 1)
    return round(v[lo] + (v[hi] - v[lo]) * (idx - lo), 1)


def classify(forecast: list[float | None], p95: float, p99: float) -> dict:
    vals = [x for x in forecast if x is not None]
    if not vals:
        return {"available": False}
    peak = round(max(vals), 1)
    level = "severe" if peak > p99 else "high" if peak > p95 else "normal"
    return {"available": True, "peak_m3s": peak, "p95_m3s": p95, "p99_m3s": p99, "level": level,
            "alert": level != "normal"}


def flood_signal(forecast: list[float | None], history: list[float | None]) -> dict:
    if not any(h is not None for h in history):
        return {"available": False}
    return classify(forecast, percentile(history, 0.95), percentile(history, 0.99))
