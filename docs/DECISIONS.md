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
