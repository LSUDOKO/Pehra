# 10 · Build plan

Start: Friday 9 Oct 2026, evening IST. Hard stop for new features: Sunday 11 Oct, ~12:00 IST. Submissions open Sunday 8:00 am IST, so aim to submit as soon as the video and README are ready.

## Roles (team Mavricks; adapt if needed)

| Role | Owns |
|---|---|
| Data and science (Pradyuman) | `heatcore`: WBGT, NIOSH limits, plan algorithm, IMD rule, audit, validation |
| AWS pipeline | SAM, Lambda, Step Functions, S3, Athena, SQS |
| AI agent | Strands tools, number check, test set, Cedar |
| UX and story | Telegram bot text, Hindi voice, worker page, poster, video, blog |

With only two people, one person takes science + agent, the other AWS + UX/story.

## Repository layout

```
invisible-heat/
├─ README.md
├─ template.yaml                 # SAM
├─ samconfig.toml
├─ heatcore/                     # pure Python, no AWS imports
│  ├─ wbgt.py
│  ├─ niosh.py
│  ├─ plan.py
│  ├─ acclimatisation.py
│  ├─ water.py
│  ├─ imd_rule.py
│  ├─ audit.py
│  └─ templates_hi.py
├─ functions/
│  ├─ ingest_forecast/
│  ├─ plan_worker/
│  ├─ telegram_webhook/
│  ├─ sender/
│  ├─ checkin_api/
│  ├─ recheck/
│  ├─ nightly_record/
│  └─ report_pdf/
├─ agent/
│  ├─ tools.py
│  ├─ agent.py
│  ├─ number_check.py
│  └─ guidance_index/            # vetted short passages for search_guidance
├─ cedar/
│  ├─ schema.cedarschema
│  ├─ policies/*.cedar
│  └─ tests/
├─ web/
│  ├─ worker/                    # QR page (static, tiny)
│  ├─ poster/
│  └─ audit/                     # results page
├─ tests/
│  ├─ test_heatcore_*.py
│  ├─ agent_questions.jsonl
│  └─ e2e_daily_plan.py
├─ scripts/
│  ├─ kharghar_replay.py
│  ├─ run_audit.py
│  └─ verify_hash_chain.py
├─ docs/
│  ├─ PLAN_ALGORITHM.md
│  ├─ MODEL_CARD.md
│  ├─ DECISIONS.md
│  └─ architecture.md
└─ .github/workflows/deploy.yml
```

## Ordered tasks

### Block 1 — Friday night (science core, offline)
1. Create repo, `heatcore/` package, pytest, CI skeleton. First commit date must be on/after 8 Oct.
2. Implement `niosh.py` (REL/RAL) + tests (§4.3).
3. Implement `wbgt.py` using thermofeel; fixture vs OSHA calculator (§4.1).
4. Implement `plan.py` (bands, stop window, reschedule), `acclimatisation.py`, `water.py` + tests.
5. Implement `scripts/kharghar_replay.py` using Open-Meteo archive (16 Apr 2023, Kharghar).
6. **Checkpoint:** run the replay and read the result. If it doesn't show danger at plausible hours, note it and plan the video story accordingly (see `12-limits-and-claims.md`).

### Block 2 — Saturday morning (pipeline and bot)
7. SAM template skeleton: DynamoDB table, S3 buckets (Object Lock bucket created with `ObjectLockEnabled: true`), SQS queues + DLQs, Secrets.
8. `ingest_forecast` Lambda (EventBridge twice a day): fetch Open-Meteo for registered cities, compute WBGT, store one JSON per city per run in S3, pointer in DynamoDB.
9. `telegram_webhook` Lambda: `/start`, `/register` (site name, city), crew message, Approve/Override callbacks. Verify webhook secret.
10. `plan_worker` Lambda + Step Functions plan flow with `waitForTaskToken`; idempotency.
11. Template Hindi messages (`templates_hi.py`) and the sender Lambda with rate limiting.
12. Polly voice note generation; send as Telegram voice (OGG/Opus where supported; otherwise audio file).
13. **Checkpoint:** from a real phone, receive the 19:00-style plan on demand via `/plan_now`.

### Block 3 — Saturday afternoon (agent, Cedar)
14. Strands agent with tools + number check + fallback.
15. Cedar schema, policies, `authorize()` helper, tests; wire into override callback.
16. Voice roster (Transcribe → parse → confirm).
17. `find_window` rescheduling via text question.
18. Re-check Lambda + alert + acknowledgement.
19. **Checkpoint:** run the agent test set (even 15 questions); log numbers.

### Block 4 — Saturday evening/night (worker side, records, audit)
20. Worker QR page + `checkin_api` + symptom alert.
21. Nightly record with Object Lock + hash chain + verify script.
22. Poster (HTML → printable) with QR.
23. Mini audit for 5–10 cities (2021–2025), Parquet to S3, results page with caveats.
24. Compliance PDF from seeded sample data (clearly labelled).
25. Deploy via SAM to `ap-south-1`; test end to end from scratch on the deployed stack.

### Block 5 — Sunday morning (no new features)
26. Record the 3-minute video (`11-demo-and-submission.md`).
27. README, model card, architecture diagram, failure-mode table, AI tools used, credits.
28. Publish the blog on AWS Builder Center.
29. Submit as soon as the form opens (8:00 am IST). Everyone verified on Builder Center first.

## Definition of done (Weekend)

- [ ] Deployed stack reachable; Telegram bot responds
- [ ] `/plan_now` returns a correct Hindi plan + voice for Chennai
- [ ] Approve and Override work; looser override blocked without reason; AI cannot loosen (Cedar test passes)
- [ ] Midday re-check alert works on a forced stricter forecast (can be simulated; label it)
- [ ] Kharghar replay output reproducible
- [ ] Worker QR page logs a break and a symptom; supervisor gets alert
- [ ] Nightly record written with Object Lock; hash chain verifies
- [ ] Agent number check active; test set results published
- [ ] Mini audit headline number with caveats
- [ ] README complete; video <3 min; blog published

## Left out on purpose (do not build)

These need a paid account, a phone number, or hardware, so they wait until there's a partner:

- WhatsApp business messages (Meta verification and per-message charges)
- SMS alerts (DLT registration in India)
- Automated phone calls and missed-call numbers (Amazon Connect or a telecom number)
- Tamil, Bengali and Odia neural voices (GPU endpoint)
- ESP32 site sensors on AWS IoT Core
- Any cost-per-site claims or cost tables

## Cut order

See `06-features.md`, bottom. Always protect the core flow.

## Commit hygiene

- Commit early and often; messages describe the change.
- Commit messages end with the attribution lines the tool provides.
- No secrets in history. If one slips in, rotate it immediately.
- Tag the submitted commit `submission-v1`.

## Deployment notes

- `sam deploy --guided` once; save config.
- Set the Telegram webhook to the API Gateway URL with a secret token.
- Create an AWS Budgets alert (e.g. at a few dollars) in case of runaway usage.
- Keep Lambda timeouts short; set reserved concurrency on the sender to respect rate limits.
