"""The seven decisions from 09-security-cedar.md, plus a few more."""

import pytest

from ihcommon.authz import authorize, entity, plan_entity, site_entities, uid

SITE = {"site_id": "s1", "owner_hash": "sup1", "tenant_id": "t1"}
OTHER = {"site_id": "s2", "owner_hash": "sup2", "tenant_id": "t2"}
ENTS = (site_entities(SITE) + site_entities(OTHER) + [plan_entity(SITE, "d"), plan_entity(OTHER, "d"),
        entity("SystemAgent", "ai"), entity("Contractor", "c1", tenant="t1"),
        entity("Worker", "w1", site=uid("Site", "s1"))])
PLAN = uid("Plan", "s1#d")


def ctx(n, d="looser"):
    return {"reason_length": n, "direction": d}


def test_agent_cannot_loosen():
    assert not authorize(uid("SystemAgent", "ai"), "LoosenPlan", PLAN, ENTS, ctx(50))


def test_agent_cannot_override():
    assert not authorize(uid("SystemAgent", "ai"), "OverridePlan", PLAN, ENTS, ctx(50))


def test_agent_can_stricten():
    assert authorize(uid("SystemAgent", "ai"), "StrictenPlan", PLAN, ENTS, ctx(0, "stricter"))


def test_supervisor_short_reason_denied():
    assert not authorize(uid("Supervisor", "sup1"), "LoosenPlan", PLAN, ENTS, ctx(4))


def test_supervisor_real_reason_allowed():
    assert authorize(uid("Supervisor", "sup1"), "LoosenPlan", PLAN, ENTS, ctx(10))


def test_supervisor_other_site_denied():
    assert not authorize(uid("Supervisor", "sup2"), "LoosenPlan", PLAN, ENTS, ctx(30))


def test_worker_own_site_allowed():
    assert authorize(uid("Worker", "w1"), "LogCheckIn", uid("Site", "s1"), ENTS)


def test_worker_other_site_denied():
    assert not authorize(uid("Worker", "w1"), "LogCheckIn", uid("Site", "s2"), ENTS)


def test_contractor_raw_checkins_denied():
    assert not authorize(uid("Contractor", "c1"), "ViewCheckInsRaw", uid("Site", "s1"), ENTS)


@pytest.mark.parametrize("site, ok", [("s1", True), ("s2", False)])
def test_contractor_aggregates_own_tenant_only(site, ok):
    assert authorize(uid("Contractor", "c1"), "ViewCheckInsAggregate", uid("Site", site), ENTS) is ok
