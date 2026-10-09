# 00 · Instructions for the AI coding agent

## Your job

Build the **Weekend** features of Invisible Heat (listed in `06-features.md`) as a working, deployed system on AWS, in the order given in `10-build-plan.md`. The deadline is Sunday 11 October 2026, morning IST. Roughly 30–36 hours of work time remain.

## Priorities, in order

1. **The core flow works end to end for one city (Chennai).** Forecast → WBGT → work-rest plan → Hindi text and voice on Telegram → Approve/Override → saved record.
2. **The Kharghar replay works.** Running the engine on 16 April 2023 at Kharghar, Navi Mumbai, shows the hour-by-hour WBGT and the plan the app would have sent.
3. **It is deployed on AWS** with SAM and uses at least one AWS open-source tool (Strands Agents SDK, Cedar, SAM CLI). This is mandatory for prize eligibility.
4. Everything else in `06-features.md`, Weekend tag, in listed order.
5. Roadmap features: **do not build** unless every Weekend feature is done and tested.

## Hard rules

- **No LLM-generated numbers.** Every number shown to a user (temperatures, WBGT, minutes, litres, times) must come from a deterministic function. The LLM may only rephrase tool outputs. Implement the number check in `08-agent-spec.md`.
- **The AI can never loosen a limit.** Plans can be made stricter by the AI, never looser. Overrides that loosen a plan require a human, a written reason, and are logged. Enforce with Cedar (`09-security-cedar.md`), not only in the prompt.
- **Fallback always exists.** If Bedrock fails, the plan still goes out as a fixed template.
- **Free tier only.** Do not use: WhatsApp Business messaging, SMS, Amazon Connect, telecom numbers, GPU endpoints, IoT hardware, paid APIs. See "Left out on purpose" in `10-build-plan.md`.
- **No worker personal data.** Store headcounts and anonymous check-in tokens only. Never store worker names. Supervisor Telegram chat IDs are stored; do not log them in plain text.
- **Region:** deploy to `ap-south-1` (Mumbai) where the service is available. If a Bedrock model is not available there, use a cross-region inference profile and note it in the README.
- **Secrets** (Telegram bot token) go in AWS Secrets Manager or SSM Parameter Store SecureString, never in code or the repo.
- **Git history must match the event dates** (no project code before 8 Oct 2026). Commit often with clear messages.
- **Record every AI tool used** (including the agent you are) in `README.md` under "AI tools used". The rules require it.

## Verify, don't assume

Library APIs change. Before using these, check current docs (e.g. via Context7, PyPI or GitHub):
- `thermofeel` WBGT function names and argument units
- `strands-agents` Agent/tool/BedrockModel API
- `cedarpy` (Python bindings for Cedar) API
- Amazon Polly Hindi voice names and whether `ogg_opus` output is supported in your region
- Amazon Transcribe `hi-IN` support for OGG/Opus input
- Open-Meteo variable names

If a library doesn't behave as this pack says, follow the library and leave a note in `docs/DECISIONS.md`.

## Testing expectations

- Unit tests for every science function in `04-science-spec.md` with the worked examples given there.
- One end-to-end test that runs the daily plan for a fixed historical date and checks the output shape.
- The 50-question agent test set (`08-agent-spec.md`) can be smaller (15–20) if time is short; report the numbers honestly.

## Style of user-facing text

- Hindi messages in simple spoken Hindi (Roman script for Telegram text is acceptable, Devanagari for voice input to Polly if the voice handles it better; test both).
- Short sentences. One action per sentence.
- Always say which forecast the plan is based on and when it was made.
- Never say "safe". Say "lower risk" or give the plan.
- First-aid messages are fixed text (see `06-features.md`), never generated.

## When stuck

Cut scope, not quality. Use the cut order in `10-build-plan.md`.
