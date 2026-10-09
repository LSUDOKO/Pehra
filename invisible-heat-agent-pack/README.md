# Invisible Heat: build pack for an AI coding agent

**Project:** Invisible Heat, a heat-safety platform for India's outdoor workers
**Event:** Environmental Hacks (Bharat Builds Tour, Event 02), WeMakeDevs × AWS Builder Center
**Track:** 02 Heat and Water
**Team:** Mavricks (leader: Arpit Singh; member: Pradyuman Sharma)
**Hackathon window:** 8–11 October 2026. Submissions open 11 Oct 2026, 8:00 am IST.
**Pack written:** 9 October 2026, evening IST

## One-line pitch

India warns workers about heat with a thermometer, but workers are harmed by heat and humidity together. Invisible Heat turns the weather forecast into an hour-by-hour work-rest plan for each worksite (based on WBGT, the international heat-stress measure), sends it as a Hindi voice note, lets workers log rest and symptoms, keeps a tamper-proof record, and audits how many dangerous days India's official alerts never flagged.

## How the agent should use this pack

Read the files in this order. Each file is self-contained, but later files assume the earlier ones.

| File | What it contains | Read when |
|---|---|---|
| `00-AGENT-INSTRUCTIONS.md` | Ground rules, priorities, what not to do | First, always |
| `01-overview.md` | Problem, users, product, the "day with the app" story | Before designing anything |
| `02-hackathon-rules.md` | Eligibility, judging criteria, submission checklist | Before scoping |
| `03-research.md` | Statistics, the policy gap, existing tools, global precedents | When writing README, blog, video |
| `04-science-spec.md` | WBGT, NIOSH limits, work-rest algorithm, acclimatisation, water, IMD rule | Before writing any calculation code |
| `05-data-sources.md` | Weather APIs and datasets, exact variables, access | Before writing data code |
| `06-features.md` | Every feature with priority and acceptance criteria | When planning tasks |
| `07-architecture.md` | AWS services, diagram, DynamoDB schema, APIs, scale, failure modes | Before writing infra code |
| `08-agent-spec.md` | Strands agent: tools, prompt, number check, fallback, test set | Before writing agent code |
| `09-security-cedar.md` | Cedar policies, privacy rules, secrets | Before writing auth code |
| `10-build-plan.md` | Repo layout, ordered task list, timeline, what is left out | To execute the build |
| `11-demo-and-submission.md` | 3-minute video script, blog outline, judge Q&A | Last day |
| `12-limits-and-claims.md` | What the project must never claim | Before writing any user-facing text |
| `13-sources.md` | All source links | When citing |
| `14-idea-research-appendix.md` | How this idea was chosen over others | Background only |

## The golden rules (details in 00-AGENT-INSTRUCTIONS.md)

1. **Numbers come from code, never from the LLM.** The AI explains; tools calculate.
2. **The AI can never loosen a safety limit.** Only a human can, with a written reason.
3. **One flow working end to end beats ten half-built features.** Build in the order in `10-build-plan.md`.
4. **Use only free services and the AWS Free Tier.** Paid features are listed as "left out" and must not be built.
5. **Everything must be honest.** No "lives saved" claims. Label simulated data.
