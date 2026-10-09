# Cedar decision tests

Run: `uv run pytest tests/test_cedar_policies.py -v`

| Test | Expected |
|---|---|
| SystemAgent → LoosenPlan | Deny (`agent-never-loosens`) |
| SystemAgent → OverridePlan | Deny |
| SystemAgent → StrictenPlan | Allow |
| Supervisor (own site) → LoosenPlan, reason 4 chars | Deny (`no-loosen-without-reason`) |
| Supervisor (own site) → LoosenPlan, reason ≥ 10 chars | Allow |
| Supervisor (other site) → LoosenPlan | Deny |
| Worker token → LogCheckIn at own site | Allow |
| Worker token → LogCheckIn at other site | Deny |
| Contractor → ViewCheckInsRaw | Deny |
| Contractor → ViewCheckInsAggregate, own / other tenant | Allow / Deny |

Policies: `cedar/policies/*.cedar`. Schema: `cedar/schema.cedarschema`. Both are validated in CI (`tests/test_cedar_policies.py::test_policies_validate`).
