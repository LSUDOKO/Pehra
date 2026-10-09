# 01 · Overview

## The problem

India's heat alerts that trigger any action (paid breaks, work stoppages, insurance payouts) are built on **maximum temperature** and heatwave duration. But the human body is harmed by **heat and humidity together**, plus sun and wind. A humid 36 °C day can be more dangerous for a construction worker than a dry 42 °C day, yet only the second one triggers an official heatwave.

Result: many dangerous working days happen with **no official warning**, so no one changes work hours. Workers most affected: construction, agriculture, brick kilns, salt pans, street vendors, delivery riders, sanitation workers. New and migrant workers who aren't used to the heat are at the highest risk.

Detailed evidence is in `03-research.md`.

## The idea

Use **WBGT** (Wet Bulb Globe Temperature), the international standard for workplace heat stress used by OSHA, NIOSH, Qatar, Singapore and the military. Compute it from free weather forecasts, convert it into a concrete hour-by-hour plan using public NIOSH formulas, and deliver it where supervisors already are (Telegram now, WhatsApp later), in Hindi voice.

## The three users

| User | What they need | What Invisible Heat gives them |
|---|---|---|
| **Site supervisor** (e.g. "Ramesh", 40 workers, Chennai) | What to do tomorrow, in plain Hindi, without forms | A 7 pm voice note with stop window, rest minutes per hour, water order, reduced schedule for new workers. Approve/Override buttons. Voice Q&A. |
| **Worker** | Rest when it's dangerous; help if feeling sick | A QR poster at the site: tap to log a break, tap "chakkar aa raha hai" for fixed first-aid steps and a supervisor alert. Picture poster of today's plan. No app, no account. |
| **Organisation** (contractor, labour department, insurer, researcher) | Proof that heat was managed; data to act on | Monthly compliance PDF, aggregate views, insurance trigger API, open audit dataset. |

## A day with the app (use this story in the demo)

Ramesh supervises 40 workers on a building site in Chennai.

- **7:00 pm.** A Hindi voice note arrives on Telegram:
  > "Kal 12 se 3 baje tak kaam rokna hai. Sarkari heatwave warning nahi hai, lekin garmi aur nami milke khatarnak hai. Subah 6 baje shuru karo. 10 baje ke baad har ghante 15 minute aaram. Jo 3 naye mazdoor aaye hain, woh aadha kaam karenge. 6 bade paani ke can mangwa lo."
  He taps **Approve**. If he changes the plan, he must type a reason, which is saved.
  (Numbers in this example are illustrative. Real output comes from the engine.)
- **Morning.** He tells the bot by voice: "40 log, 10 bhaari kaam, 3 naye aaye." The crew profile updates.
- **11:00 am.** The newer forecast is hotter. A new alert: stop at 11:30, not 12. He acknowledges.
- **12:05 pm.** Workers scan the QR poster and tap "Aaram shuru". One worker taps "Chakkar aa raha hai"; he gets first-aid steps and Ramesh gets an alert.
- **Any time.** He asks, "Kya hum 2 baje concrete daal sakte hain?" Reply: not at 2 pm; the coolest 4-hour window is 6–10 am tomorrow.
- **Evening.** The day's record (plan, approval, re-check, breaks, symptom reports) is locked. The contractor's monthly PDF includes it.

## The three parts of the product

| Part | What it does |
|---|---|
| **See it:** the Invisible Heat Audit | For selected districts (all of India later), counts days when WBGT crossed safe-work limits but India's temperature-based heatwave rule (recreated in code) would not have declared a heatwave. Also counts how many fell outside March–June, when heatwave bulletins don't run. |
| **Plan it:** the daily work-rest plan | Turns tomorrow's forecast into hourly work and rest minutes, a stop window, a water order, a reduced schedule for new workers. Hindi voice, text, picture poster. |
| **Prove it:** sign-off and record | Approve or override with a reason, a midday re-check, worker break check-ins, and a tamper-proof daily record. |

## Positioning against the closest existing tool

SHRAM (UC Berkeley IECC, launched Sept 2026) gives district-level heat-stress forecasts by email. Credit it in the README.

**Our line:** *SHRAM tells a district how hot it will be. We tell a site supervisor what to do hour by hour, and keep a record that it was done.*

## Why this wins on the judging criteria

- **Idea & Impact:** lives and wages, not convenience. A real tragedy (Kharghar 2023) as proof of the gap.
- **Built on AWS:** natural fit for Lambda, Step Functions, DynamoDB, S3, Bedrock, Polly, Transcribe, plus open-source Strands, Cedar, SAM.
- **Design & usability:** Hindi voice, no app for workers, picture poster.
- **Execution:** one city flow, fully working.
- **Demo:** the Kharghar replay is a strong opening moment.
