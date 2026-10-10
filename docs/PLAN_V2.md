# Invisible Heat v2 — plan: heat **and water**, for workers **and everyone**

Track 02's brief is *"Too much water, too little of it, and the heat in between"* (examples: heatwaves, floods,
monsoon waterlogging, droughts, water tankers). v1 covers worksite heat very well, but only one user group and
only heat. v2 keeps the same engine and design (compute once, look up many; numbers from code; Hindi voice;
Cedar; free tiers) and adds three things:

1. **Everyone, not just site supervisors.** A personal or family mode for any person on WhatsApp or Telegram.
2. **Water, both "too little" and "too much".** A nearby drinking-water and shade finder, plus heavy-rain and flood alerts.
3. **The heat people miss: warm nights.**

Everything below uses free data: Open-Meteo forecast, archive and flood APIs, OpenStreetMap, and the stack that is already deployed.

## Research behind each feature

| Finding | Source | What we build |
|---|---|---|
| NWS + CDC **HeatRisk** turns forecasts into a 5-colour health scale with actions per level, and counts night temperatures and humidity | CDC HeatRisk guidance; NOAA HeatRisk overview | Personal 5-level heat risk with an action list per level |
| Older adults, children, pregnant women and people with chronic illness are at higher risk (WHO heat-health guidance 2026; CDC clinical guidance) | WHO Europe HHAP guidance; CDC | A household profile (counts only) with stricter limits for vulnerable members |
| Warm nights are rising faster than hot days: about 70% of districts have 5+ more very warm nights per summer, and many Heat Action Plans ignore night heat (CEEW 2025, 734 districts) | CEEW via Business Standard | Night-heat flag in every plan, plus a warm-nights count in the audit |
| 9 in 10 Delhi street vendors had no free clean water at work, and it got worse in the heat (WIEGO survey) | WIEGO via Down to Earth / IndiaSpend | "Paani aur chhaon": nearest drinking water and shade, with community-added points |
| Odisha's app maps heat shelters and water kiosks; Andhra Pradesh reports 54,380 cooling shelters | PreventionWeb; South Asian Voices | The same idea on WhatsApp, with no app to install |
| NDMA asked app platforms to pause outdoor work 11:00–16:00 on orange and red days; there is no WBGT-based guidance for riders | NDMA advisory via WRI India / Down to Earth | A rider/vendor activity profile: personal break windows from WBGT |
| Monsoon waterlogging and floods are in the track brief; IMD has fixed rainfall categories (heavy ≥ 64.5 mm/day, very heavy ≥ 115.6, extremely heavy ≥ 204.5) | Track page; IMD | Heavy-rain work and travel alerts; river-flood alerts from GloFAS where a site is near a river |

## Features, priority and acceptance

### P0 — build before submission (core of the new demo)

**V2-01 · Personal and family mode ("Garmi Saathi")**
- `/start` asks: *Site supervisor* or *Mere aur parivar ke liye* (for me and my family).
- Location: city name or a shared location on WhatsApp or Telegram. Forecasts are cached per 0.25° tile and computed once per tile per run, on first request. That generalises compute-once beyond the 10 fixed cities.
- Household profile, counts only and no names: adults, elderly (65+), young children (<5), pregnant, chronic illness, works outdoors (yes/no).
- Risk level per hour, a project rule built on the existing engine: WBGT in **shade** (or sun if they work outdoors) against the NIOSH limit for light activity, REL for healthy adults and the stricter RAL for vulnerable members. Five levels: *kam / saavdhaan / zyada / bahut zyada / khatarnak*, each with fixed actions.
- **Accept:** a 07:00 message with today's level for healthy adults and for vulnerable members, the coolest hours for errands, walks and school runs, a night-heat line, and a water reminder from fixed guidance. Every number comes from code; there is no medical advice beyond fixed text.

**V2-02 · Family call alert ("Dadi ko call")**
- Opt-in: `/family_call +91…` registers an elderly relative's phone, with their consent. On a *bahut zyada* or *khatarnak* day, they get a short fixed Hindi call at 08:00: stay indoors from X to Y, drink water, call 108 for confusion or fainting. Uses the Twilio module that already exists.
- **Accept:** the call happens only on high-risk days, at most once a day, and stops with `/family_call_off`.

**V2-03 · "Paani aur chhaon" — nearest drinking water and shade**
- OpenStreetMap points (`amenity=drinking_water`, `water_point`, `shelter`) are pre-fetched per city into S3. The public Overpass API is rate-limited, so the lookup never calls it live.
- WhatsApp or Telegram: share a location, or ask "paani kahan milega?". The reply is the 3 nearest points with distance and a map link.
- Community points: "/add_paani" plus a location. A point shows as *community-reported* after 2 independent reports; nothing personal is stored.
- **Accept:** a reply in under 3 s from cached data, with OSM attribution (ODbL), a "not verified" label on community points, and an honest "no points known near you" when that's the case.

**V2-04 · Heavy-rain and waterlogging alerts ("too much water")**
- Daily rain forecast from the same ingest, with no extra provider. IMD categories: heavy, very heavy, extremely heavy.
- Site plan: a fixed line, e.g. "Bhaari baarish: khudai, scaffolding aur bijli ka kaam band; paani nikasi check karein" (heavy rain: stop digging, scaffolding and electrical work; check drainage). Personal: a travel and waterlogging warning.
- **Accept:** the alert fires only at "heavy" or above, tests cover the category edges, and the message names the forecast run.

### P1 — if time allows before submission

**V2-05 · Warm nights.** A night heat flag from the overnight minimum temperature and night WBGT (the IMD warm-night rule recreated: departure ≥ 4.5 °C on a hot day). Supervisor version: a labour-camp sleeping advisory. Personal version: sleep-cooling tips. **Accept:** the line appears only on flagged nights; tests on edge cases.

**V2-06 · More user types: school, market vendor, delivery rider.** Same engine, different fixed templates:
- School: hold assembly indoors and move sports before X.
- Vendor: shade and water timing.
- Rider: personal break windows, light-to-moderate workload.

**Accept:** `/register` asks the type, and each type gets its own template; no new maths.

**V2-07 · Heat and Water Audit v2.** Add warm nights and heavy-rain days per city for 2021–2025 to the audit page, so the headline covers both halves of the track. Same caveats (ERA5 smooths extremes, so counts are a minimum).

### P2 — stretch or roadmap

**V2-08 · River-flood alert.** GloFAS river discharge from the Open-Meteo Flood API, only at river grid points. Alert when the forecast discharge passes that point's own historical 95th percentile. It works only for sites near rivers (verified: data at Guwahati on the Brahmaputra, none at the Chennai coast).
**V2-09 · Water tanker / supply day reminder.** Households log their tanker or supply days; the bot reminds them on heat days to store water. Roadmap.
**V2-10 · More languages.** Tamil, Bengali, Odia text (voice needs a paid GPU TTS). Roadmap.

## Architecture changes (small)

- `ingest_forecast`: also store `precipitation`, `precipitation_probability` and the daily minimum temperature in the same per-city object; add a per-tile cache for personal users (S3 key by rounded lat/lon, filled on demand, expired by lifecycle rule).
- New `heatcore/personal.py` (risk levels, coolest windows, night flag), `heatcore/rain.py` (IMD rain categories), `heatcore/places.py` (nearest points, haversine).
- New `scripts/fetch_osm_points.py`, which writes `places/{city}.json` to S3.
- DynamoDB: `PERSON#{hash}` profile (counts only), `PLACE#{city}` community points with report counts.
- New EventBridge schedule at 07:00 IST for personal messages (fan-out through the same SQS queue and sender).
- Cedar: `Person` principal can only read and update its own profile; community points are public, raw reporters private.

## Order of work (about 45 commits)

| Block | Work | Commits |
|---|---|---|
| A | `heatcore` personal risk levels, coolest windows, rain categories, warm-night flag, nearest-place search, with tests | ~12 |
| B | Ingest adds rain and minimum temperature, a per-tile cache, OSM points script and S3 upload | ~6 |
| C | Bot: user-type choice at `/start`, personal registration with location, household profile, 07:00 personal message, family call opt-in | ~10 |
| D | Paani-chhaon finder (location → nearest points), community add with 2-report rule | ~5 |
| E | Heavy-rain lines in site plans and personal messages, re-check covers rain | ~4 |
| F | SAM template (schedule, permissions, lifecycle), deploy, live smoke test | ~4 |
| G | README, model card, audit v2 (if P1), demo script update | ~4 |

## Honesty rules (from 12-limits-and-claims.md, extended)

- Personal risk levels are this project's own rule built on NIOSH limits; they are **not** a medical assessment or IMD's warning.
- First-aid and health actions are fixed text. Never "safe"; say "lower risk".
- OSM coverage in India is patchy; say so and show the count of known points.
- Community water points are unverified until two people report them, and even then are labelled "community-reported".
- Rain alerts use IMD's published categories on a forecast; they are not IMD warnings.
- No claim of lives saved.

## Sources

- CDC, How to use the HeatRisk Tool: https://www.cdc.gov/heat-health/hcp/clinical-guidance/how-to-use-the-heatrisk-tool-and-air-quality-index.html
- NOAA HeatRisk overview: https://www.wpc.ncep.noaa.gov/heatrisk/overview.html
- CEEW district heat-risk assessment (reported): https://www.business-standard.com/india-news/extreme-heat-india-risk-night-temperatures-humidity-district-impact-2025-125052200879_1.html
- WIEGO vendor survey (reported): https://www.downtoearth.org.in/climate-change/sweltering-summers-india-must-safeguard-workforce-from-heatwaves-warn-experts-82819
- Odisha heat plan: https://www.preventionweb.net/news/indias-odisha-readies-pioneering-plan-combat-deadly-heat
- Andhra cooling shelters: https://southasianvoices.org/policy-lessons-from-the-front-lines-tackling-extreme-heat-in-india/
- NDMA platform advisory (reported): https://wri-india.org/perspectives/rising-heats-invisible-burden-delivery-workers
- WHO heat-health guidance (2026): https://mb.cision.com/Public/15083/4361767/9efb66ce0ef156ad.pdf
- Track brief: https://www.wemakedevs.org/aws/env


## Status (10 Oct 2026, night)

| Item | Status |
|---|---|
| V2-01 personal and family mode | Done, deployed, live smoke test (city and tile) |
| V2-02 family call | Done (needs Twilio keys to ring) |
| V2-03 water and shade finder | Done; OSM points for 10 cities (Guwahati and Patna pending an Overpass retry); community points with the 2-report rule |
| V2-04 heavy-rain alerts | Done (sites and personal) |
| V2-05 warm nights | Done; normals for all 12 cities |
| V2-06 school, vendor, rider types | Done |
| V2-07 audit v2 | Done: 4,372 invisible heat days, 90 heavy-rain days, 68 warm nights (12 cities) |
| V2-08 river-flood signal | Done for Guwahati and Patna |
| Sensors (ESP32 / Wokwi / web simulator) | Done; Wokwi run verified against the live API |
