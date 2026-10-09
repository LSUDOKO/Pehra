# 09 · Security, privacy and Cedar policies

Cedar is AWS's open-source authorization language. Using it in the deployed system satisfies the "AWS open-source tool" requirement and enforces the project's two trust rules **outside the prompt**.

**Verify Cedar syntax against the current docs** (https://docs.cedarpolicy.com) and the Python binding (`cedarpy` or similar) before coding. The policies below are a starting design.

## Trust rules to enforce

1. **The AI cannot loosen a limit.** Only a human with role `Supervisor` (for their own site) can loosen, with a reason.
2. **Privacy:** individual worker data is not visible to organisations; labour departments see aggregates only.

## Entities

```
Principal types: Supervisor, Contractor, LabourOfficer, SystemAgent (the AI), Worker (anonymous token), Insurer (roadmap)
Resource types: Site, Plan, Override, CheckIn, Record, AuditDataset
Actions: ViewPlan, ApprovePlan, OverridePlan, LoosenPlan, StrictenPlan, LogCheckIn, ViewCheckInsAggregate, ViewCheckInsRaw, ReadRecord, ReadAudit
Context: { reason_length: Long, direction: String ("stricter" | "looser") }
```

## Policies (starting point)

```cedar
// Supervisors manage their own site's plan.
permit (
  principal is Supervisor,
  action in [Action::"ViewPlan", Action::"ApprovePlan", Action::"StrictenPlan"],
  resource is Plan
) when { resource.site.owner == principal };

// Supervisors may loosen only with a real reason.
permit (
  principal is Supervisor,
  action == Action::"LoosenPlan",
  resource is Plan
) when {
  resource.site.owner == principal &&
  context.reason_length >= 10
};

// The AI agent can view and make plans stricter. It can never loosen.
permit (
  principal is SystemAgent,
  action in [Action::"ViewPlan", Action::"StrictenPlan"],
  resource is Plan
);

forbid (
  principal is SystemAgent,
  action in [Action::"LoosenPlan", Action::"OverridePlan"],
  resource
);

// No one may loosen without a reason, regardless of role.
forbid (
  principal,
  action == Action::"LoosenPlan",
  resource
) unless { context.reason_length >= 10 };

// Workers (anonymous token) can only log check-ins at the site their token belongs to.
permit (
  principal is Worker,
  action == Action::"LogCheckIn",
  resource is Site
) when { principal.site == resource };

// Organisations see aggregates, never raw check-ins.
permit (
  principal in [Contractor::"any", LabourOfficer::"any"],
  action == Action::"ViewCheckInsAggregate",
  resource is Site
) when { principal.tenant == resource.tenant || principal is LabourOfficer };

forbid (
  principal,
  action == Action::"ViewCheckInsRaw",
  resource
) unless { principal is Supervisor && resource.owner == principal };
```

Adapt entity naming/hierarchy to match the Cedar schema you write. Keep policies in `cedar/policies/*.cedar` and the schema in `cedar/schema.cedarschema`.

## Where to call Cedar

- Before applying any override in the Lambda that handles the override callback.
- Before returning any record or check-in query.
- Before any tool call by the agent that mutates state (there should be none on the weekend build).

Create a `authorize(principal, action, resource, context)` helper wrapping the Cedar engine; log decisions (allow/deny, policy id, action) without personal data.

## Cedar tests (must exist; demo-able in the video)

| Test | Expected |
|---|---|
| SystemAgent → LoosenPlan | **Deny** |
| Supervisor (own site) → LoosenPlan, reason 4 chars | **Deny** |
| Supervisor (own site) → LoosenPlan, reason ≥ 10 chars | **Allow** |
| Supervisor (other site) → LoosenPlan | **Deny** |
| Worker token → LogCheckIn at own site | **Allow** |
| Worker token → LogCheckIn at other site | **Deny** |
| Contractor → ViewCheckInsRaw | **Deny** |

## Privacy rules (DPDP-aware, not legal advice)

- Store **headcounts**, not names. No worker names, phone numbers or ID numbers anywhere.
- Supervisor Telegram `chat_id` is stored hashed (HMAC-SHA256 with a secret) where possible; keep a reversible copy only if needed to send messages, encrypted, and never log it.
- Worker device tokens are random, stored hashed, and rotate periodically.
- Record consent: first message to a supervisor says what is stored, and offers `/delete_my_data`.
- Implement `/delete_my_data`: removes the site's non-record items. Object-Locked records expire at retention end; state this in the privacy note.
- Data stays in `ap-south-1`.
- Retention: check-ins and alerts expire by TTL after 90 days unless inside a Locked record.

## Secrets and keys

- Telegram bot token: AWS Secrets Manager (or SSM SecureString). Never commit.
- Telegram webhook: verify the `X-Telegram-Bot-Api-Secret-Token` header.
- Site tokens: 128-bit random, URL-safe; rate-limit by token and by IP (API Gateway usage plan or a DynamoDB counter).
- No public write endpoints without a token.

## Abuse and safety considerations

- QR page can be spammed: apply per-token rate limit (e.g. 10 events/minute) and dedupe symptom reports within 2 minutes.
- Symptom alerts go to the supervisor only; never broadcast.
- The product gives first aid and a pointer to 108. It does not diagnose or replace medical care.
