# Invisible Heat model card

## What it does
- Turns a free weather forecast into an hour-by-hour work-rest plan for an outdoor work site in India.
- Every number in a plan comes from deterministic code. The AI only explains and answers questions, and a number check blocks any number that no tool produced.

## Method
- Heat stress: WBGT (Wet Bulb Globe Temperature) by the Liljegren 2008 method, using thermofeel 2.3.0 (ECMWF, Apache-2.0). Same physics as OSHA's online WBGT calculator.
- Shade WBGT is the same calculation with solar radiation set to zero.
- Direct-beam share of sunlight: Open-Meteo direct radiation when available, otherwise the Erbs 1982 split.
- Limits: NIOSH 2016 REL = 56.7 − 11.5·log10(M) for acclimatised workers, RAL = 59.9 − 14.1·log10(M) for new workers. Light, moderate and heavy work use 180, 300 and 415 W.
- Rest minutes per hour: 15, 30, 45 or stop work, by how far planning WBGT is above the limit (bands of 1 °C). This band table is the project's own planning rule inspired by NIOSH guidance, not an official standard.
- Planning margin: +1.0 °C on every forecast hour; +0.5 °C more if the forecast is over 18 hours old.
- New workers: NIOSH acclimatisation, 20% of normal exposure on day 1, rising 20% a day.
- Water: one 240 ml cup per 17.5 minutes of work, at most 6 cups an hour, plus 10% buffer, in 20 litre cans.

## Personal mode, water and sensors
- Personal and family risk levels use NIOSH light-activity limits (REL healthy, RAL vulnerable). This is a planning rule, not medical advice.
- Rain categories are IMD's published 24-hour thresholds, applied to a forecast. They are not IMD warnings.
- Warm nights follow IMD's definition, recreated with ERA5 normals.
- River-flood signals come from GloFAS discharge against the point's own history. They exist only for river grid points (Guwahati, Patna).
- Drinking-water and shade points come from OpenStreetMap (ODbL). Coverage in India is patchy: 7 points around Kharghar against 658 around Delhi. Community points show only after 2 independent reports and are labelled unverified.
- Site sensors (DHT22) correct the air temperature and humidity; wind and sun still come from the forecast.

## Inputs
- Live plans: Open-Meteo forecast (best_match), fetched twice a day, about 11 km grid, free for non-commercial use.
- Kharghar replay and audit: ERA5 reanalysis via the Open-Meteo archive (CC BY 4.0), about 25 km grid.

## Validation
- WBGT vs OSHA's online calculator, 15 hours in Chennai with the same inputs and solar irradiance: mean absolute difference 0.21 °C, largest 0.49 °C, our values 0.18 °C lower on average (OSHA output read to 1 °F). Test: tests/test_heatcore_wbgt.py.
- NIOSH limits match the worked example (REL 28.2 °C, RAL 25.0 °C at 300 W).
- Kharghar, 16 April 2023 (ERA5): WBGT in sun about 31 °C at noon against a 28.2 °C limit for moderate work; the recreated IMD rule declares no heatwave (38.8 °C, +3.5 °C above normal).

## Known errors and limits
- A 11–25 km weather grid stands in for a work site. Tin roofs, concrete and lack of shade make real sites hotter.
- ERA5 smooths humid extremes, so audit counts are a minimum.
- The IMD heatwave rule is recreated on one grid cell per city; it is not IMD's official declaration record.
- One deterministic forecast, no ensemble: plans never state probabilities.
- No Indian heat-illness outcome data exists to test against, so we make no claim about lives saved. The design aim is to reduce exposure.
- The first-aid page is fixed text, not medical advice or diagnosis.

## Privacy
- Headcounts only. No worker names, phone numbers or IDs.
- Supervisor chat IDs are stored encrypted, looked up by keyed hash, and never logged.
- Worker devices are anonymous random tokens, stored as keyed hashes.
- All data stays in the AWS Mumbai region (ap-south-1). Supervisors can delete their data with /delete_my_data.
