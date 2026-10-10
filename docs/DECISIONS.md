# Decisions log

Where a library or data source didn't match the build pack, we followed the library and wrote it down here.

| Date | Decision | Why |
|---|---|---|
| 2026-10-09 | Python 3.12 for local dev and Lambda | thermofeel/numpy wheels and Lambda `python3.12` runtime; system Python is 3.14 |
| 2026-10-09 | Erbs decomposition implemented in `heatcore.solar` | thermofeel 2.3.0 has no Erbs helper; its `calculate_wbgt_liljegren` takes `fdir` (direct-beam fraction) directly |
| 2026-10-09 | Prefer Open-Meteo `direct_radiation` for the direct fraction; Erbs only as fallback | measured/modelled split beats an empirical estimate when the API provides it |
| 2026-10-09 | Centre each Open-Meteo hour 30 min before its UTC label | radiation is a preceding-hour mean; in IST this gives whole-hour plan rows |
| 2026-10-10 | Bedrock via India geo inference profiles (`in.anthropic.claude-haiku-4-5…` for plan intros, `in.anthropic.claude-sonnet-5` for Q&A) | keeps model processing inside India; Claude 5.5 models are only offered as `global.` profiles in ap-south-1 |
| 2026-10-10 | Plan messages = short AI intro (number-checked) + fixed template body | stop times, rest minutes and water must never depend on the model; AI explains, template carries the numbers |
| 2026-10-10 | Symptom messages are routed to fixed first-aid text before any model call | first aid must never be generated, even when Bedrock is up |
| 2026-10-10 | Agent tools take no `site_id`; they are bound to the supervisor's own site | the model cannot read another site's data |
| 2026-10-10 | Secrets in SSM SecureString, not Secrets Manager | free tier; pack allows either |
| 2026-10-10 | Forecast ingest three times a day (05:30, 09:30, 17:30 IST) instead of two | the 10:30 re-check needs a morning run; still one call per city per run |
| 2026-10-10 | Sender limited with SQS `ScalingConfig.MaximumConcurrency: 2`, not reserved concurrency | new accounts often have a 10-concurrency limit, which does not allow reservations |
| 2026-10-10 | Object Lock in GOVERNANCE mode, 90-day default retention | tamper-evident records that an admin can still clean up after the hackathon; COMPLIANCE mode is a one-line change |
| 2026-10-10 | Public links derived from the API's own domain at request time | putting the HTTP API URL in function env vars creates a CloudFormation cycle |
| 2026-10-10 | Webhook answers fast; questions and voice go to an async assistant Lambda | Telegram expects a quick webhook response; Bedrock and Transcribe can take tens of seconds |
| 2026-10-10 | Audit "danger" uses shade WBGT | conservative choice; sun counts are reported alongside |
| 2026-10-10 | Polly input in Roman-script Hindi | Kajal (hi-IN, neural) accepts it; Devanagari comparison left for listening tests |
| 2026-10-10 | Default runtime model: Amazon Nova Pro (`apac.amazon.nova-pro-v1:0`) | Claude on Bedrock needs an AWS Marketplace subscription; the account returned INVALID_PAYMENT_INSTRUMENT. Nova needs none. Claude stays a parameter switch |
| 2026-10-10 | Plan intro = one AI sentence (Roman Hindi, no numbers) + fixed action line | Nova's second sentences were awkward Hindi; Devanagari or any number makes the intro fall back |
| 2026-10-10 | Strip `<thinking>` tags from model output | Nova sometimes emits them |
| 2026-10-10 | Eval scorer accepts 12h/24h times and Devanagari "ओवरराइड" | the model answered correctly in those forms; scores re-computed from saved answers |
