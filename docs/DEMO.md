# 3-minute demo script (recorded, no live demo)

Mark anything simulated on screen ("WhatsApp test number", "Twilio trial call", "simulated forecast", "Wokwi simulator"). Never say "safe" or "saves lives".

| Time | Show | Say |
|---|---|---|
| 0:00–0:20 | Kharghar replay (`scripts/kharghar_replay.py`) | "16 April 2023, Kharghar. People died of heatstroke at an open-air event. There was no heatwave warning. India warns with a thermometer." |
| 0:20–0:40 | /audit page | "Across 12 cities, 4,372 such days in five years had no heatwave declared, half of them outside the heatwave season. Plus heavy rain and warm nights. Heat and water, together." |
| 0:40–1:30 | Phone, WhatsApp: supervisor sends `plan` → Hindi plan + voice note + Approve; voice "40 log, 10 bhaari, 3 naye"; worker scans the poster QR → "Chakkar aa raha hai" → WhatsApp alert, and the phone rings with a Hindi call | "One supervisor, forty workers. No app for workers." |
| 1:30–2:00 | Same bot, *Mere aur parivar ke liye*: share location → 5 taps → family forecast; `/paani` → nearest drinking water; `/family_call` → grandmother's phone rings | "Not only for workers: every family, any place in India, with the stricter limit for the elderly and children." |
| 2:00–2:20 | Wokwi ESP32: drag the DHT22 to 40 °C → "site 12 °C hotter than forecast", red LED, alert on the phone; drag the HC-SR04 → tank low / drain flooding | "A ₹600 sensor fixes the 25 km forecast grid at the site, and watches the water." |
| 2:20–2:45 | Architecture diagram; Step Functions history; `pytest tests/test_cedar_policies.py -v` → SystemAgent LoosenPlan **DENY** | "Tools do the maths, the AI explains, Cedar makes sure the AI can never loosen a plan." |
| 2:45–3:00 | Bedrock off → same plan as fixed Hindi text; team | "If the AI fails, the plan still goes out." |

## Blog outline (AWS Builder Center)
1. Kharghar and the humidity gap; heat and water together.
2. WBGT in plain words; personal levels for families.
3. Compute once, look up per site or tile.
4. Keeping the AI honest: tools, number check, Cedar.
5. Water: OSM water points, rain and flood signals, sensors in Wokwi.
6. What fought back: Hindi voice, the IST half-hour offset, Object Lock, Bedrock access, Overpass rate limits, a wrong river grid cell.
7. Results: OSHA validation 0.21 °C, agent test set, audit v2, live smoke tests.
8. Limits, roadmap, AI tools used.
