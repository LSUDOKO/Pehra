# 3-minute demo script (recorded, no live demo)

Mark anything simulated on screen. Never say "safe" or "saves lives".

| Time | Show | Say |
|---|---|---|
| 0:00–0:20 | Kharghar replay output (`scripts/kharghar_replay.py`) | "16 April 2023, Kharghar. People died of heatstroke at an open-air event. There was no heatwave warning. India warns with a thermometer." |
| 0:20–0:50 | Replay table side by side: temperature 38.8 °C and "no heatwave" vs WBGT 30.8 °C above the 28.2 °C limit; then the /audit page | "Heat and humidity together crossed the work limit. Across 10 cities, 3,459 such days in five years had no heatwave declared. That is a minimum." |
| 0:50–2:00 | Phone: Telegram plan + Hindi voice note → voice crew update → plan changes → Approve → worker scans poster QR, taps "Aaram shuru" → SIMULATED midday forecast → re-check alert → acknowledge | "One supervisor, forty workers, Chennai." Label the re-check as a simulated forecast. |
| 2:00–2:30 | Architecture diagram (`docs/architecture.md`); Step Functions execution history; `pytest tests/test_cedar_policies.py -v` showing SystemAgent → LoosenPlan **DENY** | "Tools do the maths, the AI explains, and Cedar makes sure the AI can never loosen a plan." |
| 2:30–3:00 | Set `AgentEnabled=false` (or Bedrock down) → same plan arrives as fixed Hindi text; roadmap; team | "If the AI fails, the plan still goes out. Next: WhatsApp, more languages, pilot partners." |

## Blog outline (AWS Builder Center)
1. Kharghar and the humidity gap.
2. WBGT in plain words, with one hour-by-hour chart.
3. Compute once, look up per site.
4. Keeping the AI honest: tools, number check, Cedar.
5. What fought back: Hindi voice, IST half-hour offset, Object Lock at bucket creation, Bedrock account verification.
6. Results: OSHA validation 0.21 °C, Cedar tests, audit headline with caveats, agent test-set numbers as measured.
7. Limits and what's next.
8. AI tools used.
