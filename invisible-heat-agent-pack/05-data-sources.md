# 05 · Data sources

Free sources only. Check each licence and terms before publishing derived data. Verify variable names against the live API before coding.

| Source | Used for | Access | Resolution / delay | Licence |
|---|---|---|---|---|
| **Open-Meteo Forecast API** | **Weekend forecast for the live demo** (hourly temperature, dew point, humidity, wind, pressure, shortwave radiation) | HTTPS, no key | ~11 km, hourly, 7+ days | Free for non-commercial use |
| **Open-Meteo Historical / ERA5** (archive API) | Kharghar replay (16 Apr 2023) and the mini audit | HTTPS, no key | 0.25°, hourly | CC BY 4.0 |
| Open-Meteo Previous Runs API | Forecast accuracy check (stretch) | HTTPS | Forecasts 1–7 days ahead, since Jan 2024 | Free non-commercial |
| ECMWF IFS HRES + ENS open data | Production-grade forecast, ensembles (stretch) | `s3://ecmwf-forecasts` (eu-central-1), AWS Open Data | 0.25°, 3-hourly to 144 h; ~7.5 h after run | CC BY 4.0 |
| ECMWF AIFS (single + ensemble) | Second forecast, faster (stretch) | Same bucket | 0.25°, 6-hourly; ~5.5 h | CC BY 4.0 |
| ERA5 hourly (Open-Meteo copy on AWS) | 25-year audit (stretch) | `s3://openmeteo` (us-west-2) | 0.25°, hourly | CC BY 4.0 |
| NOAA GHCNh | Checking ERA5; correction model (stretch) | NCEI download | ~374 Indian stations with temperature and humidity | NOAA open |
| IMD gridded data via `imdlib` | Recreating IMD's heatwave rule | Python package | Max temperature at 1°, daily | **Check before publishing** |
| District boundaries | Audit by district | geoBoundaries ADM2 / LGD | 736–784 districts depending on source | ODbL |
| WorldPop | Population-weighted audit (stretch) | Download | 100 m | CC BY 4.0 |
| NPCCHH, NCRB heat data | Plausibility only | Parliament answers, data.gov.in | State-year | Government |

## Weekend decision: which forecast to use

For the 36-hour build, **use the Open-Meteo Forecast API** for tomorrow's plan. It is free, needs no key, and returns the variables WBGT needs. Keep the ECMWF-on-S3 path as a documented upgrade.

Pull these hourly variables (confirm names):
`temperature_2m`, `relative_humidity_2m`, `dew_point_2m`, `surface_pressure`, `wind_speed_10m`, `shortwave_radiation`, plus `direct_normal_irradiance` / `diffuse_radiation` if offered (otherwise use the Erbs split).

Note the archive API (ERA5) for the Kharghar replay returns analysis data for 16 April 2023; location approx lat 19.04, lon 73.07. Use hours 10:00–14:00 IST (event was an afternoon outdoor ceremony; verify the actual time window from sources in `13-sources.md` before showing it).

## Sample cities for the audit (Weekend: 5–10)

Chennai, Delhi, Nagpur, Ahmedabad, Navi Mumbai (Kharghar), Bhubaneswar, Hyderabad, Lucknow, Jaipur, Kolkata. Use the last 5 summers (2021–2025) for the Weekend audit.

## Rate and licence cautions

- Open-Meteo's free tier is for **non-commercial** use and has request limits. Cache responses in S3/DynamoDB; batch requests; do not call it per user message.
- Public maps of India must use the official external boundary. Do not publish a map with a non-official boundary.
- IMD gridded data licence: confirm before redistributing derived datasets.

## Caching rule

Forecast ingestion runs **twice a day** (EventBridge). Everything else reads the stored result. A site lookup must never call an external weather API.
