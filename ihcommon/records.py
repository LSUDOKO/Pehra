"""Proof-of-rest daily records: one JSON per site per day, SHA-256 hash-chained.

Each record carries the previous day's hash, so changing any past record breaks
every later link. Records are written to an S3 Object Lock bucket.
"""

import hashlib
import json
from collections import Counter

GENESIS = "0" * 64


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode()


def record_hash(record: dict) -> str:
    body = {k: v for k, v in record.items() if k != "hash"}
    return hashlib.sha256(canonical(body)).hexdigest()


def build_record(site_id: str, date: str, plan_item: dict | None, overrides: list[dict],
                 alerts: list[dict], checkins: list[dict], prev_hash: str, sample: bool = False) -> dict:
    """Counts only for check-ins: no device hashes, no names."""
    by_type = Counter(c["type"] for c in checkins)
    by_hour = Counter(f"{c['type']}@{c['SK'].split('#')[2][11:13]}" for c in checkins)
    rec = {
        "schema": "invisible-heat/record/v1", "site_id": site_id, "date": date, "sample": sample,
        "plan": (plan_item or {}).get("plan"),
        "plan_status": (plan_item or {}).get("status", "none"),
        "approved_at": (plan_item or {}).get("approved_at"),
        "overrides": [{"direction": o["direction"], "reason": o["reason"], "actor_role": o["actor_role"],
                       "decision": o.get("decision"), "at": o["SK"].split("#", 2)[2]} for o in overrides],
        "alerts": [{"kind": a["kind"], "at": a["SK"].split("#", 2)[2], "acked_at": a.get("acked_at"),
                    "simulated": a.get("simulated", False)} for a in alerts],
        "checkins": {"counts": dict(by_type), "by_hour": dict(sorted(by_hour.items()))},
        "prev_hash": prev_hash,
    }
    rec["hash"] = record_hash(rec)
    return rec


def verify_chain(records: list[dict]) -> list[str]:
    """Return a list of problems (empty = chain verifies). Records sorted by date."""
    problems, prev = [], None
    for r in sorted(records, key=lambda r: r["date"]):
        if record_hash(r) != r["hash"]:
            problems.append(f"{r['date']}: content does not match its hash")
        if prev is not None and r["prev_hash"] != prev["hash"]:
            problems.append(f"{r['date']}: prev_hash does not match {prev['date']}")
        prev = r
    return problems
