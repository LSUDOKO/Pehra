# 06 · Features

Every feature has an ID, a priority and acceptance criteria. Build only **Weekend** features unless all are done and tested.

**Priority tags**
- **Weekend**: build for the hackathon (by Sun 11 Oct morning).
- **Stretch**: build only if every Weekend item is done.
- **Roadmap**: design only. Do not build. Mention in README and video.

**Free-tools rule:** nothing here may need WhatsApp Business, SMS, phone calls, GPU endpoints or hardware.

---

## A. Heat engine (the science underneath everything)

### F-01 · WBGT in sun and shade — Weekend
Compute hourly `wbgt_sun` and `wbgt_shade` from a forecast using the Liljegren method (`04-science-spec.md` §4.1).
**Accept:** matches OSHA calculator on fixture hours within a documented tolerance; unit tests pass.

### F-02 · Hour-by-hour work-rest plan — Weekend
Per hour: work minutes, rest minutes, status, for light/moderate/heavy tasks, plus a stop window (§4.4).
**Accept:** plan produced for tomorrow for Chennai in under 5 s from cached data; band-boundary tests pass.

### F-03 · Acclimatisation for new arrivals — Weekend
Reduced schedule for new workers (20% day 1, +20%/day) and returning workers (50/60/80/100) (§4.5).
**Accept:** plan includes a separate line for new workers when `new_count > 0`.

### F-04 · Water order — Weekend
Cans of 20 L for the day, with 10% buffer (§4.6).
**Accept:** "6 bade paani ke can" style output matches the arithmetic.

### F-05 · Forecast uncertainty margin — Weekend (single-forecast margin), Stretch (ensemble)
Weekend: fixed +1.0 °C margin (+0.5 °C if data is stale). Stretch: ensemble percentile margin and "X% chance" wording.

### F-06 · Kharghar replay — Weekend (**must**)
A command and a web/Telegram view that runs the engine on 16 April 2023 at Kharghar (ERA5 archive) and prints hourly WBGT, IMD-rule result, and the plan the app would have sent.
**Accept:** output shows WBGT vs NIOSH limit by hour and states whether the IMD rule would have declared a heatwave. Use in the video only if the result shows danger (see `12-limits-and-claims.md`).

---

## B. Supervisor features

### F-07 · Daily plan on Telegram, Hindi text and voice — Weekend (**must**)
EventBridge triggers at 19:00 IST. For each registered site, send the plan as Hindi text and a Polly voice note.
**Accept:** message includes stop window, rest minutes by period, water cans, new-worker line, forecast run time, and Approve/Override buttons. Voice note plays on Telegram.

### F-08 · Approve / Override with reason — Weekend (**must**)
Supervisor taps Approve or Override. Override that makes the plan **stricter** needs no extra approval but still asks for a reason; override that makes it **looser** requires the supervisor role and a typed reason of at least 10 characters. Everything is logged.
**Accept:** looser overrides are blocked for the AI and for any non-supervisor principal by a Cedar policy test (see `09-security-cedar.md`).

### F-09 · Midday re-check — Weekend
At 10:30 IST (and 13:30 if time) rerun the plan with the newest forecast. If any remaining hour becomes stricter, send an alert; the supervisor must acknowledge.
**Accept:** alert sent only when the new plan is stricter; acknowledgement stored.

### F-10 · Crew roster by voice — Weekend (**Should**)
Supervisor sends a voice note: "40 log, 10 bhaari kaam, 3 naye aaye." Transcribe (Hindi) → agent extracts `{headcount, heavy_count, new_count}` → confirm back in text → save.
**Accept:** the extracted numbers are shown back for confirmation before being saved. If transcription confidence is low, ask for a typed message.

### F-11 · Task-aware rescheduling — Weekend (**Should**)
"Concrete pour tomorrow, 4 hours" → coolest 4-hour window across the next 3 days (§4.4 step 6).
**Accept:** returns window, expected status, and a warning if no window is below "high".

### F-12 · Voice and text Q&A — Weekend (text), Stretch (voice)
Agent answers questions grounded in today's plan and tool outputs (e.g. "Kya hum 2 baje concrete daal sakte hain?").
**Accept:** every number in the reply appears in a tool output (number check, `08-agent-spec.md`).

### F-13 · Red-day escalation — Roadmap
If a "stop work" plan isn't acknowledged within an hour, repeat the voice note and alert the contractor on Telegram.

### F-14 · Weekly heat outlook — Roadmap
Monday message: which days of the week are dangerous, to plan heavy work early in the week.

### F-15 · Many sites per contractor — Roadmap
A contractor with 12 sites sees which sites need action today.

---

## C. Worker features (no app, no account)

### F-16 · Break check-in by QR code — Weekend (**Should**)
Each site has a QR code linking to a simple mobile page (`/s/{site_token}`). Large button "Aaram shuru" (break start) and "Aaram khatam" (break end).
**Accept:** works on a low-end phone browser; stores `site_id`, timestamp, anonymous random device token, event type; no names. Rate-limit per token.

### F-17 · "Chakkar aa raha hai" button — Weekend (**Should**)
Big red button on the same page. Shows **fixed first-aid text** (never generated): stop work, move to shade, drink water, loosen clothes, call 108 if confusion, fainting, or no sweating. Sends an alert to the supervisor's Telegram with time and (optional) count of reports in the last hour.
**Accept:** first-aid text is a constant; supervisor receives the alert within 10 s. Page says "This is first aid, not a diagnosis."

### F-18 · Picture poster for the site — Weekend (**Should**)
Printable one-page poster (HTML → PDF in the browser or server-side) showing today's plan with pictures/icons: work, rest, water, stop, plus the site QR.
**Accept:** readable without reading Hindi; generated daily; stored in S3 with a short link.

### F-19 · Workers' own languages — Roadmap
Hindi and English now (Polly). Bengali, Odia and Tamil later via AI4Bharat Indic Parler-TTS on a GPU endpoint (**paid, left out**).

---

## D. Organisation features

### F-20 · Proof-of-rest record — Weekend (**must**)
Each day, write a JSON record per site (plan, approvals/overrides with reasons, re-check alerts and acknowledgements, break events, symptom reports counts) to S3 with **Object Lock (compliance or governance mode)**. Include a SHA-256 hash of the record and the previous day's hash (chain).
**Accept:** record cannot be modified after write; hash chain verifies with a script.

### F-21 · Contractor compliance report (monthly PDF) — Weekend (**Should**)
Generated from the records: days with plans, approvals, overrides with reasons, breaks logged, symptom reports (counts only).
**Accept:** PDF generated from a sample month of seeded data (clearly marked as sample).

### F-22 · Invisible Heat Audit (mini) — Weekend (**Should**), full — Stretch
5–10 districts over 2021–2025 (Weekend). All India 2000–2025 with Step Functions Distributed Map (Stretch). Counts invisible heat days and how many fall outside March–June. Output Parquet to S3, query with Athena or pandas, plus a simple results page.
**Accept:** headline number with caveat ("a minimum; ERA5 smooths extremes; IMD rule approximated on a grid").

### F-23 · Shadow insurance trigger — Stretch
In SEWA/MHT districts, compare days their temperature triggers fired vs days WBGT was dangerous. Untested hypothesis; report whatever the data shows.

### F-24 · Labour-department view — Roadmap
District officers see which registered sites got danger plans and which overrode them. Aggregates only; Cedar forbids individual worker data.

### F-25 · Insurance trigger API — Roadmap
`GET /v1/danger-days?district=X&season=Y` for insurers; API key per partner.

### F-26 · Open audit dataset + public API — Roadmap
Publish the audit dataset with a 2-page brief for SEWA/MHT, NDMA and the Labour Ministry.

---

## E. Trust and reliability

### F-27 · Number check on every AI answer — Weekend (**must**)
See `08-agent-spec.md`. Every number in the AI's text must match a tool output; otherwise regenerate once, then send a fixed template.

### F-28 · Template fallback — Weekend (**must**)
If Bedrock or Polly fails, the plan still goes out as fixed-text Hindi.

### F-29 · Stale-data flag — Weekend
Every plan states the forecast model and issue time; if older than 18 hours, add a stale flag and +0.5 °C margin.

### F-30 · Forecast accuracy check — Stretch
Hit/false-alarm rates for "WBGT ≥ 31 °C" at 1/2/3 days ahead (§4.11).

### F-31 · Forecast correction model — Stretch
(§4.10)

### F-32 · Model card page — Weekend (**Should**)
One public page: method, inputs, known errors, validation numbers, limits.

### F-33 · Weekly published accuracy — Roadmap
"Last week our danger alerts were right X out of Y times."

### F-34 · Site sensor correction — Roadmap
A photo of a cheap thermometer-hygrometer at the site (read by Textract/Bedrock) or an ESP32 black-globe sensor via IoT Core corrects the 25 km forecast. Hardware path is paid/left out.

---

## F. Scale features (design now, demonstrate lightly)

### F-35 · Compute-once heat grids — Weekend (design), Stretch (all-India)
Forecast processed once per run into a tile store; every site is a lookup. Weekend: a handful of cities cached as one S3 object per city per run. Stretch: grid tiles in Parquet.

### F-36 · SQS fan-out + rate-limited sender — Weekend (**Should**)
Plans are generated by workers consuming SQS (idempotent per `site_id + date`); outgoing Telegram messages go through a separate queue with rate limiting.
**Accept:** re-running the same date does not send duplicates (idempotency key tested).

### F-37 · Load test — Stretch
Simulate 100,000 synthetic sites through the Distributed Map / SQS path and report runtime. Do not send real messages.

### F-38 · Multi-tenant — Roadmap (design only)
Cognito groups per contractor; tenant ID in every key.

---

## Cut order if time runs out (cut from the bottom up)

1. F-37, F-30, F-31, F-23, F-22 (full)
2. F-21 (compliance PDF), F-18 (poster)
3. F-16/F-17 (worker QR page)
4. F-10, F-11 (voice roster, rescheduling)
5. F-36 (SQS fan-out)

**Never cut:** F-01, F-02, F-06, F-07, F-08, F-20, F-27, F-28, plus Cedar and Strands in the deployed system.
