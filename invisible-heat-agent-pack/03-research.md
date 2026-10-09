# 03 · Research findings

Research compiled 3 October 2026 (earlier session) and extended 9 October 2026. Items marked **(unverified)** came from the team's brief and were not independently re-checked in this pack; check before quoting in the README, blog or video. Links are in `13-sources.md`.

## 1. The problem in numbers

| Figure | Detail | Source |
|---|---|---|
| 247 billion | Potential work hours India lost to heat in 2024, about US$194 bn of income. Agriculture 66% of the loss, construction 20%. | Lancet Countdown 2025 |
| ~30.5 °C | Wet-bulb temperature at which young healthy adults lost control of body temperature in the lab (the 35 °C figure often quoted is too high). | Vecellio et al. 2022 |
| 9 in 10 | Workers worldwide exposed to excessive heat were exposed outside a heatwave. 8 in 10 heat injuries at work also happen outside heatwaves. | ILO, July 2024 |
| 82% | Chennai workers above WBGT safety limits in the hot season. Even in the cool season, 42% were above them. | Venugopal et al. 2016 |
| 2.4× | Odds of miscarriage for pregnant workers with high heat exposure in Tamil Nadu (n = 800). | BJOG 2024 |
| 13–14 | People who died of heatstroke at an open-air event in Kharghar, Navi Mumbai, 16 April 2023. IMD had issued no heatwave warning that day. | Wikipedia, citing The Hindu, CNN, HT |
| 530 vs 4 | 2020 heat deaths recorded by NCRB vs NDMA. An excess-mortality study estimates ~3,400 extra deaths on a single extreme-heat day. | NCRB, NDMA, excess-mortality study |
| >70% | Share of US worker heat deaths in the first week on the job (acclimatisation data). | NIOSH/OSHA |

**Kharghar caution:** use Kharghar in the demo only if your own WBGT calculation for that day and place shows danger. If it does not, use a different documented day.

## 2. The gap, stated precisely

Use this exact framing. **Do not say "IMD ignores humidity."** IMD publishes an experimental heat index and a "hot and humid" definition; neither triggers any action.

### IMD's heatwave rule (what triggers action)
- Applies only if max temperature ≥ 40 °C (plains), ≥ 30 °C (hills), ≥ 37 °C (coast).
- Heatwave: 4.5–6.4 °C above normal, or ≥ 45 °C. Severe: > 6.4 °C above normal, or ≥ 47 °C.
- Must hold at 2 or more stations for 2 consecutive days. Normals are 1991–2020.
- Colour alerts (yellow/orange/red) depend on how many days the heatwave lasts.

### Everything downstream inherits the temperature-only gap
- **Delhi 2024:** paid break 12–3 "till temperatures come down below 40 °C".
- **Maharashtra SOP, April 2026:** 12–4 break, but only under orange/red alerts.
- **NDMA gig-worker advisory 2025:** triggered by IMD orange/red alerts; not legally binding.
- **Labour Ministry advisory, April 2026:** no threshold at all.
- **Heat insurance for women workers:** SEWA's scheme triggers on NASA satellite temperature; MHT with Go Digit on a 2-day temperature threshold. In 2025–26 SEWA paid out about 3% of premiums and MHT paid nothing in Ahmedabad in 2025. A SEWA coordinator has asked for wet-bulb to be added.
- **Season mismatch:** moist heatwaves occur during monsoon breaks, but IMD heatwave bulletins run only March to June.
- **No outdoor standard:** the OSH Code (in force since Nov 2025) sets no numeric heat limits. State Factories Rules cap indoor wet-bulb at about 30 °C. Nothing covers outdoor work.
- **No published verification of WBGT forecasts for India** found in team searches (only a research pilot without skill numbers).

## 3. What already exists

| Tool | What it does | Humidity / WBGT? | What's missing |
|---|---|---|---|
| **SHRAM** (UC Berkeley IECC, launched Sept 2026) | District-level heat-stress forecasts for all India, 1/3/7 days, workload and sun/shade options | Own index EHI-N* (includes humidity); not WBGT | Email alerts only, SMS "coming soon". No work-rest schedules, acclimatisation, site-level plans |
| OSHA-NIOSH Heat Safety Tool | US app: heat index, risk level, precautions | Heat index only | US-focused, no WBGT, no plan, no sign-off |
| US NWS experimental WBGT forecast | Gridded WBGT map | WBGT | US only; a map, not a plan |
| Kestrel 5400 | Handheld WBGT meter with work/rest alarms | WBGT | Hardware cost per site; measures now, doesn't forecast |
| IMD experimental heat index | Feels-like temperature, colour bands | Humidity, not WBGT | Public-facing; triggers no action |
| Sunny Lives (SEEDS + Microsoft) | Heat risk per building from roof type | No | Homes, not workplaces or hours |
| Zomato/Blinkit, Swiggy, Amazon | Rest points, water, cooling gear for delivery workers | No published thresholds | Comfort measures; no change to shifts |
| SEWA / MHT heat insurance | Parametric payouts to women informal workers | Temperature only | Near-zero payouts 2025; humid days never trigger |
| State working-hour orders | Kerala calendar 12–3 rest; Delhi below-40 °C rule; Odisha 11–3 | No | Blunt and uniform |

Features tagged "first in India" in this project mean "we found no Indian tool doing this". That is a search result, not proof. Say it that way.

## 4. Global precedents

Model suggested for India: Singapore's thresholds, Italy's forecast-triggered rules, Qatar's absolute stop with a posted schedule.

| Country | Rule | Basis |
|---|---|---|
| Qatar (Decision 17/2021) | All outdoor work stops above WBGT 32.1 °C. Calendar ban 10:00–15:30, 1 June to 15 Sept. Daily schedule must be posted at the site. | WBGT |
| Singapore (MOM) | Hourly WBGT monitoring. Rest 10 min/hour at WBGT ≥ 32, 15 min/hour at ≥ 33 for heavy work. 7-day acclimatisation for new workers. | WBGT |
| Italy (Worklimate, INAIL + CNR) | 3-day WBGT risk forecasts. Puglia and Basilicata ban outdoor work 12:30–16:00 on forecast "high" days. | WBGT forecast |
| Spain, Greece | Hours adjusted on weather alerts; Greece stops outdoor work above 40 °C. | Alerts / temperature |
| USA | NWS experimental WBGT forecasts. OSHA proposed rule uses heat-index triggers and is not yet final. | Heat index |

## 5. Scientific warnings relevant to the build

- Simplified WBGT formulas can be off by 3–5 °C in humid conditions, often by three risk categories. Use the Liljegren method.
- ERA5 reanalysis smooths extremes and underestimates humid heat. Audit counts are therefore **minimums**.
- Open-Meteo's `wet_bulb_temperature` uses the Stull formula without a pressure term. Do not use it for outdoor work decisions.
- Weather grids are ~25 km wide; a worksite can be hotter (tin roofs, concrete). State this limit.

## 6. LLM reliability evidence (why numbers stay out of the model)

- GPT-4 got only 37% of immediate disaster-response actions right in the RESPONSE benchmark.
- LLM urgency ratings for the same crisis message varied across languages.
These support the design rule: the LLM never calculates a number and never loosens a limit.

## 7. Government health data (for plausibility checks only)

NPCCHH suspected heatstroke cases: 2022: 4,481; 2023: 19,402; 2024 (to July): 48,385. Use only as an indicative state-year comparison with invisible-heat-day counts. Do not claim causation.

## 8. Other hackathon projects seen (for novelty awareness)

Public projects found by the team: "HeatCredit" (Heat and Water track) and "Air Quality Advisor" for Delhi (Air track). Track-wise competition counts are not published; no claim can be made about which track has fewer entries.

## 9. Related research found via alphaXiv (background, not required reading)

- Indoor air quality dynamics in India (arXiv 2407.14393)
- Temporal deep-learning calibration of low-cost air sensors (arXiv 2604.21527)
- Urban heat indices from low-cost networks, Switzerland (arXiv 2606.09364)
- Waste sorting ML in Ghana (arXiv 2608.25759)
These informed the idea screening in `14-idea-research-appendix.md`. None is a dependency of this build.
