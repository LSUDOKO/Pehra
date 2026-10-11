# Submission text (paste into the form)

**Project:** Pehra · Invisible Heat
**Track:** 02 Heat and Water
**Team:** Mavricks (Arpit Singh, Pradyuman Sharma)

## Links
- Repo: https://github.com/LSUDOKO/Pehra
- Website: https://yj61i9i7g0.execute-api.ap-south-1.amazonaws.com/
- Bot: https://t.me/Pehra_AWS_bot (Telegram) · WhatsApp test number +1 555-648-9580 (demo, pre-approved recipients only)
- Audit: https://yj61i9i7g0.execute-api.ap-south-1.amazonaws.com/audit
- Video: <YouTube link>
- Blog: <AWS Builder Center link>

## Problem (2 lines)
India's heat alerts that trigger action use temperature, not humidity. Workers and families are harmed by heat and humidity together, so many dangerous days pass with no warning: 4,372 such city-days in 12 cities from 2021 to 2025, by our audit (a minimum).

## What we built (4 lines)
A WhatsApp/Telegram assistant that turns the free forecast into hour-by-hour WBGT-based plans in Hindi (text, voice note, and phone calls for alerts). Site supervisors get work-rest plans with Approve/Override. Workers use a QR page with no app. Families anywhere in India get a 07:00 plan with stricter limits for the elderly, babies and pregnant women.
Water too: nearest drinking-water and shade points, heavy-rain and river-flood alerts, warm nights, and a ₹600 ESP32 sensor (also runs in Wokwi) for site-measured WBGT, water-tank and drain levels. Each day's record is hash-chained in S3 Object Lock, with a monthly compliance PDF.

## How AWS is used
- **Lambda + EventBridge Scheduler:** compute WBGT once per city/tile, three times a day; 07:00 family plans, 19:00 site plans, 10:30/13:30 re-checks, 23:30 records.
- **Step Functions:** each plan waits up to 12 h for Approve/Override (`waitForTaskToken`), with retries and history.
- **Bedrock + Strands Agents (open source):** answers questions; tools do every calculation; a number check blocks invented numbers.
- **Cedar (open source):** the AI can never loosen a plan; devices write only to their own stream; raw worker data stays private.
- **Polly and Transcribe (hi-IN):** Hindi voice notes, phone-call audio and voice crew updates.
- **DynamoDB, S3 (Object Lock), SQS + DLQs, API Gateway, SSM, CloudWatch, SAM (open source):** storage, tamper-proof records, rate-limited sending, secrets, alarms and a one-command deploy in ap-south-1.

## What works, what is simulated
- **Works (deployed, tested live):**
  - site plans with voice, Approve/Override and Cedar;
  - re-check alerts;
  - the worker QR page and symptom alerts;
  - personal/family mode and the water finder;
  - rain, flood and warm-night lines;
  - sensors posting from Wokwi;
  - records and the hash chain;
  - the audit page.
- **Simulated or sample:** the re-check demo uses a "+1.5 °C SIMULATED" forecast; the compliance PDF uses a labelled sample month; WhatsApp uses Meta's test number; calls use a Twilio trial; the illustrated characters are not real people.
- **Validation:** WBGT within 0.21 °C (mean) of OSHA's calculator on 15 cases; Cedar decision tests; a 40-question agent test set with 0 invented numbers shipped (see the README for the latest run).

## What's next
WhatsApp scheduled templates, an Indian caller ID, Tamil/Bengali/Odia voices, ECMWF ensembles for probabilities, labour-department dashboards, insurance triggers, and pilots with SEWA-type groups.

## AI tools used
Claude Code (Anthropic) built most of the code, tests and docs under the team's direction. Codex helped with UI polish. Amazon Nova Pro on Bedrock powers runtime answers. Polly and Transcribe handle voice.
