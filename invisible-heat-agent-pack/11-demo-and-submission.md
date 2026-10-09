# 11 · Demo video, blog and judge Q&A

## Video: under 3:00, recorded, on YouTube

There is no live demo; judges see only this video. Show real running software, name each AWS service on screen.

| Time | Content | Notes |
|---|---|---|
| 0:00–0:20 | Kharghar, 16 April 2023: 13–14 died of heatstroke; IMD had issued no heatwave warning. "India warns with a thermometer." | **Only use if your own replay shows danger for that day.** Otherwise open with the audit finding instead. |
| 0:20–0:50 | The Kharghar replay / audit view: thermometer says no warning; WBGT says dangerous. Headline invisible-heat-days number with "a minimum" caveat. | Side by side. |
| 0:50–2:00 | A Chennai site. Hindi voice note arrives; supervisor adds 3 new workers by voice; plan changes; Approve; a worker scans the QR poster and taps "Aaram shuru"; midday forecast worsens and the system alerts again. | One real supervisor quote or voice clip if you can get it (even from a relative who supervises). Label simulated pieces on screen. |
| 2:00–2:30 | Architecture diagram; name each service. Show Cedar denying the AI trying to loosen a limit. | Cedar denial on screen is a strong moment. |
| 2:30–3:00 | One failure case (Bedrock down → fixed-text plan), what's next (roadmap), team. | Honest limits. |

### Recording tips
- Screen-record the phone for Telegram; screen-record the AWS console for Step Functions and CloudWatch.
- Voiceover in clear English with Hindi snippets subtitled.
- Mark anything simulated: "simulated forecast", "sample data".
- Export 1080p; check audio levels; add subtitles.

## Writeup (short, for the submission form)

Problem (2 lines) → What we built (4 lines) → How AWS is used (service list with one-line reasons) → What works / what's simulated → What's next.

## Blog (AWS Builder Center; top 5 blogs win AirPods)

Outline:
1. The Kharghar story and the humidity gap (150 words)
2. What WBGT is, in plain words, with one chart (hour-by-hour WBGT vs limit)
3. The design: compute once for India, look up per site (diagram)
4. How we kept the AI honest: tools do the maths, number check, Cedar
5. What fought back (real build problems: Hindi voice, rate limits, Object Lock)
6. Results: validation numbers, test set numbers, audit headline (with caveats)
7. Limits and what's next (pilot partners, insurance triggers)
8. AI tools used (list them)

Link the blog in the submission.

## README must include

Problem, what it does, screenshot/gif, architecture diagram, AWS services and why, how to run/deploy, test commands, results (validation + agent test set + audit), limits, privacy note, credits (SHRAM, thermofeel, NIOSH, Open-Meteo/ECMWF/ERA5), **AI tools used**, licences.

## Judging self-assessment (team's estimate before building)

| Criterion | Now | How to raise it |
|---|---|---|
| Idea & Impact | 8/10 | One real supervisor's quote or voice clip |
| Built on AWS | 8/10 | One-line reason per service; SAM template; compute-once design; failure-mode table |
| Design & usability | 6.5/10 | Hindi voice, worker QR page with no app, picture poster |
| Execution | 5–8/10 | Keep the must list; one flow working perfectly |
| Demo video | 7–9/10 | Show the science side by side; show a failure |

## Likely judge questions

| Question | Answer |
|---|---|
| Why Step Functions and not just Lambda? | Approval can take hours; Step Functions waits, retries and keeps history. |
| Does it scale to a million sites? | Heat is computed once per forecast run; a site is a lookup. Plans fan out through SQS and the same code runs for 100 or a million sites. |
| What if Bedrock or the forecast fails? | Previous forecast with a stale flag; fixed-text plan without the AI. |
| Security? | Least-privilege roles, tokens in Secrets Manager, no worker personal data, headcounts only, Cedar policies. |
| Why not ML for heat? | WBGT is physics; ML is used where it helps, e.g. correcting forecasts against stations. |
| Isn't this SHRAM? | SHRAM gives district forecasts by email. We give a site plan, acclimatisation, Hindi voice, sign-off and a record. |
| How do you know workers actually rested? | Workers check in themselves through the QR page, so the record doesn't depend only on the supervisor. |
| Can the AI make a mistake that hurts someone? | It can't calculate or loosen limits; numbers come from code, Cedar blocks loosening, and a template fallback exists. Workers/supervisors can always override stricter. |
| What's your evidence it helps? | Not claimed yet. We show validation of the calculation and the audit; a pilot would measure heat-illness reports, breaks taken and work done. |

## Pitch lines

- "India warns workers about heat with a thermometer. The body feels heat and humidity together."
- "SHRAM tells a district how hot it will be. We tell a site supervisor what to do hour by hour, and keep a record that it was done."
- "Heat is computed once for all of India. A million sites cost the same to compute as one."
- "The AI explains. Code calculates. Cedar decides what the AI is not allowed to do."
