"""Cedar authorization (AWS open source). Wraps cedarpy; logs decisions without personal data."""

import functools
import os
from pathlib import Path

import cedarpy

from ihcommon.log import log, metric, short_hash


def _cedar_dir() -> Path:
    env = os.environ.get("CEDAR_DIR")
    if env:
        return Path(env)
    bundled = Path(__file__).parent / "cedar"           # inside the Lambda layer
    return bundled if bundled.exists() else Path(__file__).parents[1] / "cedar"


@functools.cache
def _engine() -> tuple[cedarpy.PolicySet, cedarpy.Schema]:
    d = _cedar_dir()
    text = "\n".join(p.read_text() for p in sorted((d / "policies").glob("*.cedar")))
    return cedarpy.PolicySet.from_str(text), cedarpy.Schema.from_str(
        (d / "schema.cedarschema").read_text())


def uid(type_: str, id_: str) -> dict:
    return {"type": type_, "id": id_}


def entity(type_: str, id_: str, **attrs) -> dict:
    def conv(v):
        return {"__entity": v} if isinstance(v, dict) and "type" in v else v
    return {"uid": uid(type_, id_), "attrs": {k: conv(v) for k, v in attrs.items()}, "parents": []}


def site_entities(site: dict) -> list[dict]:
    return [entity("Supervisor", site["owner_hash"]),
            entity("Site", site["site_id"], owner=uid("Supervisor", site["owner_hash"]),
                   tenant=site.get("tenant_id", "default"))]


def plan_entity(site: dict, date: str) -> dict:
    return entity("Plan", f"{site['site_id']}#{date}", site=uid("Site", site["site_id"]))


def authorize(principal: dict, action: str, resource: dict, entities: list[dict],
              context: dict | None = None) -> bool:
    policies, schema = _engine()
    req = {"principal": principal, "action": uid("Action", action), "resource": resource,
           "context": context or {}}
    res = cedarpy.is_authorized(req, policies, entities, schema)
    allowed = res.decision == cedarpy.Decision.Allow
    reasons = list(getattr(res.diagnostics, "reasons", []) or [])
    log("authz", principal_type=principal["type"], principal=short_hash(principal["id"]),
        action=action, resource_type=resource["type"], allowed=allowed, policies=reasons)
    metric("AuthzAllow" if allowed else "AuthzDeny", action=action)
    return allowed
