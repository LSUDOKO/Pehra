# Kharghar replay — 16 April 2023

`uv run python scripts/kharghar_replay.py --json docs/results/kharghar_replay.json`

Data: ERA5 reanalysis via the Open-Meteo archive (CC BY 4.0), grid cell near 19.02 N, 73.05 E. Reanalysis, not the forecast available that evening.

## Result

| | Value |
|---|---|
| Daily max temperature (ERA5) | 38.8 °C |
| 1991–2020 normal (±7 days, ERA5) | 35.3 °C |
| Departure | +3.5 °C |
| Recreated IMD rule (coastal, ≥37 °C and departure ≥4.5 °C) | **No heatwave** |
| Peak WBGT in sun | 30.8 °C at 12:00 IST |
| NIOSH REL, moderate work (300 W) | 28.2 °C |
| Hours above REL (sun, no margin) | 10:00–16:00 IST |
| Plan the app would have sent (with +1.0 °C margin) | Stop work 11:00–14:00; 30–45 min rest/hour around it |

The ceremony was held outdoors in the late morning to early afternoon (window 10:00–14:00 IST used here; verify against the sources in `invisible-heat-agent-pack/13-sources.md` before quoting a time).

## How to say it (see 12-limits-and-claims.md)

"On that day there was no official heatwave warning. Our calculation from ERA5 shows WBGT in the sun of about 31 °C at noon, above the NIOSH limit for moderate work." Do **not** say anyone would have been saved.

Caveats: ERA5 is ~25 km and smooths extremes, so this is likely an underestimate; the IMD rule is recreated on a grid and is not IMD's official record; the work-rest bands are this project's own planning rule.
