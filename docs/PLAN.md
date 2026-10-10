# Invisible Heat — phased implementation plan

Source of truth: `invisible-heat-agent-pack/` (read `00-AGENT-INSTRUCTIONS.md` first).
Goal: Weekend features from `06-features.md`, deployed with SAM, in 110+ small one-line commits.
Never-cut list: F-01, F-02, F-06, F-07, F-08, F-20, F-27, F-28, Cedar, Strands.

Commit style: one line, `area: what changed` (e.g. `heatcore: add NIOSH REL/RAL limits`).

---

## Phase 0 — Repo scaffold (commits 1–8)
1. docs: add Invisible Heat agent build pack
2. docs: add phased implementation plan
3. chore: add pyproject with uv and pytest config
4. chore: add gitignore for python, sam and env files
5. chore: add heatcore package skeleton
6. chore: add ruff lint config
7. ci: add GitHub Actions test workflow
8. docs: add DECISIONS log

## Phase 1 — Science core `heatcore/` (commits 9–34) · F-01..F-05, F-29
9. heatcore: add workload classes and metabolic rates
10. heatcore: add NIOSH REL and RAL formulas
11. test: cover REL/RAL at 180, 300, 415 W
12. heatcore: add solar zenith helper
13. heatcore: add WBGT sun/shade via thermofeel Liljegren
14. heatcore: estimate direct beam with Erbs split
15. test: add WBGT fixture hours vs OSHA calculator
16. heatcore: add exceedance band table as config constant
17. heatcore: map exceedance to rest minutes and status
18. test: cover plan band boundaries 0/1/2/3
19. heatcore: compute hourly work-rest plan
20. heatcore: detect contiguous stop window
21. test: cover stop window detection
22. heatcore: add forecast uncertainty margin and stale flag
23. test: cover stale margin
24. heatcore: add new-worker acclimatisation schedule
25. heatcore: add returning-worker schedule
26. test: cover acclimatisation day fractions
27. heatcore: add water cups and 20L can order
28. test: cover water can rounding with buffer
29. heatcore: add find_window reschedule search
30. test: cover find_window least-bad flagging
31. heatcore: add never-looser plan guard
32. test: cover never-looser guard
33. heatcore: add plan dataclasses and JSON serialisation
34. docs: write PLAN_ALGORITHM.md

## Phase 2 — Data + Kharghar replay (commits 35–44) · F-06
35. heatcore: add Open-Meteo forecast client
36. heatcore: add Open-Meteo ERA5 archive client
37. heatcore: normalise hourly frames to IST
38. test: add recorded Open-Meteo fixture
39. heatcore: add IMD heatwave rule
40. test: cover IMD rule edges and persistence
41. scripts: add Kharghar 16 Apr 2023 replay
42. scripts: print WBGT vs limit table in replay
43. docs: record Kharghar replay result
44. heatcore: add city registry with lat/lon

## Phase 3 — Hindi text + templates (commits 45–50) · F-28
45. heatcore: add fixed Hindi plan template
46. heatcore: add fixed first-aid text constant
47. heatcore: add rest summary formatter
48. test: template fills only from plan fields
49. heatcore: add English template variant
50. heatcore: add alert and recheck templates

## Phase 4 — AWS foundation with SAM (commits 51–62)
51. infra: add SAM template skeleton
52. infra: add DynamoDB single table with GSI and TTL
53. infra: add heat store and poster buckets
54. infra: add Object Lock records bucket
55. infra: add plan and outgoing SQS queues with DLQs
56. infra: add Telegram secret in Secrets Manager
57. infra: add shared Lambda layer for heatcore
58. functions: add ddb repository helpers
59. functions: add structured JSON logger with hashed ids
60. functions: add ingest_forecast lambda
61. infra: schedule ingest twice a day with EventBridge
62. infra: add CloudWatch alarm on forecast age

## Phase 5 — Telegram bot + plan flow (commits 63–78) · F-07, F-08, F-36
63. functions: add Telegram API client
64. functions: add telegram_webhook with secret check
65. bot: add /start with privacy notice
66. bot: add /register site flow
67. bot: add /crew typed roster
68. bot: add /plan_now command
69. functions: add plan_worker with idempotency key
70. infra: add plan Step Functions state machine
71. sfn: add waitForTaskToken approval step
72. bot: add Approve and Override buttons
73. bot: handle override direction and reason
74. functions: add rate-limited sender lambda
75. functions: add Polly Hindi voice synthesis
76. sender: send voice note to Telegram
77. infra: schedule 19:00 IST daily plan fan-out
78. bot: add /delete_my_data

## Phase 6 — Cedar (commits 79–85) · F-08 enforcement
79. cedar: add schema
80. cedar: add plan policies (AI never loosens)
81. cedar: add check-in and privacy policies
82. cedar: add authorize helper with cedarpy
83. test: add the 7 Cedar decision tests
84. bot: enforce Cedar on override callback
85. docs: document Cedar decisions

## Phase 7 — Strands agent (commits 86–96) · F-11, F-12, F-27
86. agent: add tool wrappers over heatcore
87. agent: add search_guidance local index
88. agent: add parse_crew_roster rule parser
89. agent: add number check
90. test: cover number check
91. agent: add Strands Bedrock agent with system prompt
92. agent: regenerate once then fall back to template
93. bot: route free-text questions to agent
94. test: add agent question set
95. scripts: add agent eval runner
96. functions: add Transcribe voice roster

## Phase 8 — Recheck + worker side (commits 97–106) · F-09, F-16, F-17, F-18
97. functions: add recheck lambda comparing plans
98. infra: schedule 10:30 IST recheck
99. bot: store alert acknowledgements
100. functions: add checkin_api with rate limit
101. web: add worker QR page
102. web: add Chakkar button with fixed first aid
103. checkin: alert supervisor on symptom
104. web: add printable picture poster
105. functions: generate site QR code
106. test: cover checkin rate limit and dedupe

## Phase 9 — Records, audit, report (commits 107–116) · F-20, F-21, F-22
107. functions: add nightly record with hash chain
108. scripts: add verify_hash_chain
109. test: cover hash chain verification
110. scripts: add mini audit for 10 cities
111. web: add audit results page with caveats
112. functions: add monthly compliance PDF
113. scripts: seed sample month (labelled sample)
114. web: add model card page
115. infra: add CloudWatch dashboard
116. ci: add SAM deploy workflow

## Phase 10 — Deploy, docs, submission (commits 117–125)
117. deploy: first sam deploy to ap-south-1
118. fix: issues found in deployed e2e run
119. test: add e2e daily plan test
120. docs: write README
121. docs: add architecture diagram
122. docs: add failure-mode table and limits
123. docs: add AI tools used and credits
124. docs: add demo video script notes
125. chore: tag submission-v1

---

## Status (10 Oct 2026)

| Phase | Status |
|---|---|
| 0 Scaffold | Done |
| 1 Science core | Done; 0.21 °C mean difference vs OSHA calculator |
| 2 Data + Kharghar replay | Done; replay shows danger with no heatwave |
| 3 Hindi templates | Done |
| 4 AWS foundation (SAM) | Template written, `sam validate --lint` clean, `sam build` passes |
| 5 Telegram bot + plan flow | Done (tested with fakes and moto) |
| 6 Cedar | Done |
| 7 Strands agent | Done; live eval pending Bedrock account verification |
| 8 Re-check + worker side | Done |
| 9 Records, audit, report | Done |
| 10 Deploy + submission | README, architecture, demo script done. **Remaining:** `sam deploy`, set Telegram webhook, run agent eval, record video, tag `submission-v1` |
