# 04 · Science specification

All calculations in this file must live in a pure Python package (`heatcore/`) with no AWS dependencies, so they can be unit-tested offline. Every user-facing number comes from here.

**Verify library signatures before coding.** Names below are from the team's research; check the installed version.

## 4.1 WBGT (Wet Bulb Globe Temperature)

- **Method:** Liljegren 2008 via `thermofeel.calculate_wbgt_liljegren` (thermofeel 2.3.0, Apache-2.0, from ECMWF). Same physics as OSHA's online WBGT calculator.
- **Outdoor WBGT in sun:** computed with full radiation.
- **WBGT in shade:** the same call with solar radiation set to zero.
- **Solar geometry (zenith angle, cos zenith):** from `earthkit-meteo` or thermofeel helpers.
- **Direct-beam radiation:** open forecast data does not provide it directly. Estimate it from global horizontal radiation using the **Erbs decomposition** in thermofeel.
- **Inputs per hour:** air temperature, dew point (or relative humidity), 10 m wind speed, surface pressure, downward shortwave radiation, location (lat/lon), time (UTC).
- **Output per hour:** `wbgt_sun`, `wbgt_shade` in °C.

**Do not use:** the Australian BoM simplified WBGT, or Open-Meteo's wet-bulb, for outdoor work decisions. (Simplified WBGT can be off by 3–5 °C in humid air.)

### Validation task
Compare `wbgt_sun` for 10–20 sample hours against OSHA's online WBGT calculator (https://www.osha.gov/heat-exposure/wbgt-calculator). Report mean absolute difference in the README. Include this as a test fixture.

## 4.2 Work intensity and metabolic rate

Use three workload classes mapped to NIOSH metabolic rates (watts). Pick these defaults and document them; they are planning values, not measurements:

| Class | Hindi label | M (W) | Examples |
|---|---|---|---|
| light | halka kaam | 180 | supervising, light carrying, flagging |
| moderate | madhyam kaam | 300 | masonry, bar-bending, loading light items |
| heavy | bhaari kaam | 415 | concrete pouring, digging, heavy lifting |

NIOSH 2016 gives light/moderate/heavy as 180, 300, 415 W reference ranges in its criteria tables. Confirm in the NIOSH document (https://www.cdc.gov/niosh/docs/2016-106/) and cite.

## 4.3 NIOSH exposure limits (public domain formulas)

For metabolic rate `M` in watts:

- **REL** (acclimatised workers): `WBGT_REL = 56.7 − 11.5 · log10(M)`
- **RAL** (unacclimatised workers): `WBGT_RAL = 59.9 − 14.1 · log10(M)`

Worked example (use as a unit test): at M = 300 W, `REL = 56.7 − 11.5·log10(300) = 28.2 °C`, `RAL = 59.9 − 14.1·log10(300) = 25.0 °C`.
(Compute exact values in code; tests should assert to ±0.05 °C.)

**Do not reproduce ACGIH tables** (copyrighted). Use only the NIOSH formulas.

## 4.4 Hourly work-rest plan algorithm

Goal: for each hour of the working day, output `work_minutes` and `rest_minutes` summing to 60, plus flags.

Inputs: hourly `wbgt_sun` (or `wbgt_shade` if the crew works fully in shade; default sun), workload class, crew composition (acclimatised count, new-worker count), forecast uncertainty margin.

Algorithm (deterministic, document it in `docs/PLAN_ALGORITHM.md`):

1. For each hour `h`, take `W = wbgt_h + margin` where `margin` ≥ 0 (see 4.7).
2. Let `limit = REL(M)` for acclimatised workers, `RAL(M)` for unacclimatised.
3. Compute the **exceedance** `E = W − limit`.
4. Map `E` to rest minutes per hour using these bands:

| Exceedance E (°C) | Rest min/hour | Status |
|---|---|---|
| E ≤ 0 | 0 | normal |
| 0 < E ≤ 1 | 15 | caution |
| 1 < E ≤ 2 | 30 | high |
| 2 < E ≤ 3 | 45 | very high |
| E > 3 | 60 | stop work |

These bands are the **project's own planning rule** inspired by NIOSH work/rest guidance and Singapore's 10/15 min-per-hour structure. They are not a quoted standard. Label them as such in the README. Make the band table a single config constant so it can be changed.

5. **Stop window:** contiguous hours where status is "stop work" (60 rest min). Output as `stop_from`, `stop_to`.
6. **Reschedule heavy tasks:** for a requested task of duration `D` hours and workload class, search the next 3 days for the contiguous window with the lowest maximum exceedance. If no window has status ≤ caution, return the least-bad window and flag it.
7. **Never output a plan looser than the computed one.** Overrides are separate (see `06-features.md` F-12 and `09-security-cedar.md`).

## 4.5 Acclimatisation (NIOSH)

- **New (never worked in heat):** at most 20% of normal exposure on day 1, then +20% per day (20, 40, 60, 80, 100).
- **Returning (experienced worker back after a break):** 50%, 60%, 80%, then 100% on day 4.
- Apply to the *exposure time* (work minutes in the hot window). Output a reduced schedule for the new workers: `allowed_work_minutes = base_work_minutes × fraction`.
- Use RAL (not REL) as their limit until day 5.
- Store only `new_count` and `day_number` per crew group, not names.

## 4.6 Water plan (NIOSH)

- One cup (≈ 240 ml) every 15–20 minutes of work; no more than 6 cups per hour.
- Cups per worker for an hour: `cups = min(6, round(work_minutes / 17.5))` (one cup per ~17.5 min of work, the midpoint of 15–20).
- Total litres for the day = Σ over working hours of `headcount × cups × 0.24`.
- Express as **number of 20-litre cans, rounded up**, plus 10% buffer.

## 4.7 Forecast uncertainty margin

Weekend version (single deterministic forecast): `margin = 1.0 °C` added to WBGT for planning, and a stale-data flag adds a further 0.5 °C.
Stretch version: use the ECMWF 51-member ensemble; margin = (90th percentile − median) of WBGT per hour, minimum 0.5 °C. State "X% chance WBGT goes above Y between A and B" only if ensembles are actually used.

## 4.8 The IMD heatwave rule (to recreate in code)

Used by the audit only, to decide whether an official heatwave would have been declared.

Inputs: gridded daily maximum temperature (IMD gridded data via `imdlib`, 1° grid, or ERA5 daily max as a proxy) and 1991–2020 daily normals.

Rule per grid cell/day:
1. Region type threshold: plains ≥ 40 °C, hills ≥ 30 °C, coastal ≥ 37 °C (use a region lookup; a simple state/region tag is acceptable and must be documented).
2. If threshold met: heatwave if departure from normal is 4.5–6.4 °C, or max ≥ 45 °C; severe if departure > 6.4 °C or max ≥ 47 °C.
3. Persistence: require 2 consecutive days.
4. "At 2 or more stations" can only be approximated on a grid (require ≥ 2 adjacent cells in a district). **State this approximation in the README.**

An **invisible heat day** for a district = a day when WBGT (shade or sun, chosen and documented) at ≥ 1 representative hour exceeded the NIOSH REL for **moderate work** (28.2 °C reference) **and** no heatwave day was flagged by the IMD rule recreated above. Count separately how many such days fall outside March–June.

Important: because ERA5 underestimates humid extremes, counts are a minimum. Say so wherever the number appears.

## 4.9 Critical physiological limit (context only)

Critical wet-bulb temperature ≈ 30.55 ± 0.98 °C in humid conditions (Vecellio 2022); lower for older adults (Wolf 2023). Do not use this as a work limit; it is a survivability bound shown for context.

## 4.10 Forecast bias correction (stretch)

A small model (e.g., gradient-boosted regression or ridge) that corrects forecast 2 m temperature and humidity using NOAA GHCNh observations from ~374 Indian stations. Train on part of the stations, test on the rest, report error before and after. Skip if time is short.

## 4.11 Forecast accuracy check (stretch)

Using Open-Meteo Previous Runs API (forecasts 1–7 days ahead since Jan 2024) vs ERA5, compute hit rate and false-alarm rate for the event "WBGT ≥ 31 °C" at 1, 2, 3 days ahead for ~20 cities over 2024 and 2025 summers. Publish the numbers. We found no published WBGT forecast verification for India.

## 4.12 Unit tests required

- `test_rel_ral`: REL/RAL at 180, 300, 415 W.
- `test_wbgt_known_case`: fixture against OSHA calculator values.
- `test_plan_bands`: boundaries of the exceedance table (0, 1, 2, 3).
- `test_acclimatisation_days`: day 1..5 fractions for new workers; returning schedule.
- `test_water_cans`: rounding up with buffer.
- `test_never_looser`: a function that takes a plan and an AI-modified plan and asserts per-hour rest minutes are ≥ the base plan.
- `test_imd_rule_edge`: exactly 40.0 °C plains; 45.0 °C absolute; 2-day persistence.
