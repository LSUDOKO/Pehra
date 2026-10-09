# 02 · Hackathon rules and judging

Source: event page https://www.wemakedevs.org/aws/env and rules page https://www.wemakedevs.org/aws/env/rules (re-check both before submitting; rules can change).

## Event facts

- Environmental Hacks, Event 02 of the Bharat Builds Tour (WeMakeDevs × AWS).
- Online Thursday 8 Oct to Sunday 11 Oct 2026. Optional in-person build day at DTU, Delhi, Saturday 10 Oct (adds nothing to score).
- Teams of 1–4. **You cannot change your team after submitting.**
- Submissions open 11 Oct 2026, 8:00 am IST.
- Prize pool ₹20 lakh. Each track winner: ₹2,00,000 cash + $2,000 AWS credits. Top 4 runners-up across tracks: $1,000 AWS credits per team.
- Top 10 students across all tracks: fast-track interviews at Amazon (6-month internship and full-time roles).
- Top 5 blogs on AWS Builder Center: AirPods.

## Eligibility for prizes (mandatory)

The project must **use at least one AWS open-source tool OR be deployed on AWS.** Invisible Heat does both:
- Open source: Strands Agents SDK, Cedar, SAM CLI (optionally LocalStack, Finch).
- Deployed: Lambda, API Gateway, Step Functions, DynamoDB, S3, Bedrock, Polly, Transcribe, EventBridge, SQS, CloudWatch.

Each participant should verify student status on **AWS Builder Center** (required to compete per the event page).

## Judging criteria

| # | Criterion | What judges ask | How Invisible Heat answers |
|---|---|---|---|
| 1 | Idea and Impact | Real environmental problem? What changes for people? | Heat stress on outdoor workers; plans on days with no official warning; Kharghar replay |
| 2 | Built on AWS | Uses AWS open source or services | Serverless pipeline + Strands + Cedar + SAM; compute-once design |
| 3 | Design and usability | Can someone outside the team use it? | Hindi voice on Telegram; workers use a QR page, no app; picture poster |
| 4 | Execution | Does it work? One working feature beats five that almost do | One city end to end, deployed |
| 5 | Demo video | 3 minutes, recorded; no live demo | Script in `11-demo-and-submission.md` |

Judges score what was built, not what was spent. Local builds and AWS deployments are scored equally. Each track is judged separately.

## Submission checklist

- [ ] Public GitHub repo, history within event dates
- [ ] README: problem, what it does, architecture, AWS services and why, how to run, limits, AI tools used, credit to SHRAM
- [ ] Deployed URL (worker QR page or a simple web page) and Telegram bot handle
- [ ] Video under 3 minutes on YouTube showing the product and where AWS fits
- [ ] Short writeup (problem, build, AWS)
- [ ] Blog on AWS Builder Center (for the AirPods prize), linked in the submission
- [ ] Every team member verified on AWS Builder Center
- [ ] Team finalised before submitting (2 of 4 seats filled; add others first if wanted)

## AWS credits

New AWS accounts start with up to $200 Free Tier credits. The organisers give $25 more on request (one form per team, leader fills it) once credits run out. Keep usage inside the free tier; set an AWS Budgets alert at a low amount.
