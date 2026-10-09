# 12 · Limits and claims to avoid

Everything user-facing (README, blog, video, bot messages) must respect this file.

## Limits to state openly

- Weather grids are about 25 km wide (Open-Meteo forecast ~11 km; ECMWF 0.25°): a site-level plan built on district-scale weather. Tin roofs, concrete and lack of shade make real sites hotter.
- There is no open Indian heat-illness data, so **no claim of lives saved**. Say "designed to reduce exposure".
- The IMD rule is recreated on a grid and is **not** IMD's official declaration record. The "2 or more stations" condition is approximated.
- ERA5 smooths extremes; audit counts are a **minimum**.
- The work-rest bands in `04-science-spec.md` §4.4 are this project's own planning rule inspired by NIOSH guidance, not a quoted standard.
- Open-Meteo's free API and some datasets are non-commercial.
- The first-aid page is not medical advice or diagnosis.
- Single forecast, no ensemble in the weekend build: do not claim probabilities.

## Claims to avoid

| Don't say | Why | Say instead |
|---|---|---|
| "IMD ignores humidity" | IMD publishes an experimental heat index and a "hot and humid" definition; they just trigger nothing | "India's heatwave alerts that trigger action use temperature, not humidity" |
| "This saves lives" / "prevents heatstroke" | No outcome evidence | "Designed to reduce exposure" |
| "Safe" | Heat risk is never zero | "Lower risk" or state the plan |
| "First in India" (flat) | Search result, not proof | "We found no Indian tool doing this" |
| "Kharghar victims would have been saved" | Speculation | "On that day there was no official warning; our calculation shows WBGT of X" (only if true) |
| Linking Uddanam kidney disease to heat | Cause not established | Leave it out |
| "35 °C wet-bulb is the human limit" | Lab data suggest ~30.5 °C for young healthy adults in humid heat | Quote Vecellio 2022 correctly |
| Any ₹-per-site, cost-saving or "40% cheaper" claims | Unmeasured; cost content was removed | Omit |
| "SHRAM doesn't exist / we are the only ones" | SHRAM is the closest tool | Credit SHRAM and differentiate |
| Track-competition claims ("fewest entries") | No data | Omit |
| Any statement about the AI "knowing" medical conditions | It gives fixed first-aid text only | Describe it accurately |

## Simulated vs real

Mark on screen and in the README anything simulated: forecasts forced to worsen for the re-check demo, sample compliance report data, seeded check-ins, any quote not from a real supervisor.

## Maps and boundaries

Public maps of India must use the official external boundary.

## Required disclosures

- List every AI coding tool used (including this agent) in the writeup. The rules require it.
- Credit data and software: Open-Meteo/ECMWF/ERA5 (CC BY 4.0 where applicable), thermofeel (Apache-2.0), NIOSH criteria, SHRAM, OSHA WBGT calculator for validation.
- Do not reproduce ACGIH tables (copyrighted).
- No project code before 8 Oct 2026; repo history must match the event dates.
