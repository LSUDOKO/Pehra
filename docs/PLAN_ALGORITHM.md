# Work-rest plan algorithm

All code lives in `heatcore/` (pure Python, no AWS). Same inputs give the same plan.

## Inputs
- Hourly `wbgt_sun` and `wbgt_shade` (°C) from `heatcore.wbgt` (Liljegren 2008 via thermofeel).
- Workload class: light 180 W, moderate 300 W, heavy 415 W (NIOSH 2016 reference values).
- Crew: headcount, heavy-work count, new-worker count and their day number.
- Forecast issue time, used for the uncertainty margin.

## Steps
1. **Margin.** `margin = 1.0 °C`; `+0.5 °C` if the forecast is more than 18 h old (stale). No ensemble is used, so plans never state probabilities.
2. **Limit.** `REL = 56.7 − 11.5·log10(M)` for acclimatised workers, `RAL = 59.9 − 14.1·log10(M)` for new workers until day 5.
3. **Exceedance.** For each working hour (06:00–19:00 IST): `E = (WBGT + margin) − limit`.
4. **Rest minutes** from `heatcore/bands.py`:

| E (°C) | Rest min/hour | Status |
|---|---|---|
| ≤ 0 | 0 | normal |
| 0–1 | 15 | caution |
| 1–2 | 30 | high |
| 2–3 | 45 | very high |
| > 3 | 60 | stop work |

   **This band table is our own planning rule**, inspired by NIOSH work/rest guidance and Singapore's per-hour rest structure. It is not a quoted standard.
5. **Stop window.** The longest run of consecutive "stop" hours in the general (moderate) plan. Heavy-crew stop hours are reported separately.
6. **New workers.** NIOSH acclimatisation: 20/40/60/80/100 % of normal exposure on days 1–5 (returning workers 50/60/80/100 %). Work minutes per hour are scaled down, never up.
7. **Water.** One cup (0.24 L) per 17.5 min of work, max 6 per hour, summed over the crew; 20 L cans rounded up after a 10 % buffer.
8. **Reschedule.** `find_window` searches the next days for the contiguous window with the lowest maximum exceedance, and flags it if even the best one is worse than "caution".
9. **Never looser.** `heatcore.guard` rejects any modified plan with less rest in any hour than the computed plan. Loosening needs a human supervisor and a written reason (enforced by Cedar).

## Output
`heatcore.daily.build_daily_plan` returns one JSON-able dict (plans, rest summary, stop window, new-worker schedule, water, forecast model and issue time, stale flag) plus a SHA-256 `plan_hash`. Every message, poster and record is filled from this dict only.
