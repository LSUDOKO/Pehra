import copy

from ihcommon.records import GENESIS, build_record, verify_chain

CHK = [{"type": "break_start", "SK": "CHK#2026-10-11#2026-10-11T12:05:00+05:30#abc123"},
       {"type": "symptom", "SK": "CHK#2026-10-11#2026-10-11T12:40:00+05:30#def456"}]
OVR = [{"direction": "looser", "reason": "client inspection at noon", "actor_role": "Supervisor",
        "decision": "allow", "SK": "OVR#2026-10-11#2026-10-11T07:10:00+05:30"}]


def chain(n=3):
    out, prev = [], GENESIS
    for d in range(n):
        r = build_record("s1", f"2026-10-1{d}", {"plan": {"x": d}, "status": "approved"}, OVR, [], CHK, prev)
        out.append(r)
        prev = r["hash"]
    return out


def test_chain_verifies():
    assert verify_chain(chain()) == []


def test_tampering_breaks_the_chain():
    recs = chain()
    bad = copy.deepcopy(recs)
    bad[1]["overrides"][0]["reason"] = "edited later"
    assert any("2026-10-11" in p for p in verify_chain(bad))


def test_record_has_counts_not_device_ids():
    r = chain(1)[0]
    assert r["checkins"]["counts"] == {"break_start": 1, "symptom": 1}
    assert "abc123" not in str(r)
