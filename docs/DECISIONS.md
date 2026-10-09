# Decisions log

Where a library or data source didn't match the build pack, we followed the library and wrote it down here.

| Date | Decision | Why |
|---|---|---|
| 2026-10-09 | Python 3.12 for local dev and Lambda | thermofeel/numpy wheels and Lambda `python3.12` runtime; system Python is 3.14 |
| 2026-10-09 | Erbs decomposition implemented in `heatcore.solar` | thermofeel 2.3.0 has no Erbs helper; its `calculate_wbgt_liljegren` takes `fdir` (direct-beam fraction) directly |
| 2026-10-09 | Prefer Open-Meteo `direct_radiation` for the direct fraction; Erbs only as fallback | measured/modelled split beats an empirical estimate when the API provides it |
| 2026-10-09 | Centre each Open-Meteo hour 30 min before its UTC label | radiation is a preceding-hour mean; in IST this gives whole-hour plan rows |
