from ihcommon import repo

SITE = {"site_id": "s1", "name": "Site A", "city": "chennai", "lat": 13.08, "lon": 80.27,
        "site_token": "tok123", "tenant_id": "t1"}


def test_site_lookups(ddb_table):
    repo.put_site(ddb_table, SITE, "hash1", "enc")
    assert repo.get_site(ddb_table, "s1")["lat"] == 13.08
    assert repo.site_for_chat(ddb_table, "hash1")["site_id"] == "s1"
    assert repo.site_for_token(ddb_table, "tok123")["site_id"] == "s1"
    assert [s["site_id"] for s in repo.list_sites(ddb_table)] == ["s1"]


def test_idempotency_claim_once(ddb_table):
    assert repo.claim_idempotency(ddb_table, "s1#2026-10-11")
    assert not repo.claim_idempotency(ddb_table, "s1#2026-10-11")


def test_plan_roundtrip(ddb_table):
    plan = {"date": "2026-10-11", "plan_hash": "h", "forecast_issued": "x", "generated_at": "y",
            "water": {"cans_20l": 3}}
    repo.put_plan(ddb_table, "s1", plan)
    repo.update_plan(ddb_table, "s1", "2026-10-11", status="approved")
    got = repo.get_plan(ddb_table, "s1", "2026-10-11")
    assert got["status"] == "approved" and got["plan"]["water"]["cans_20l"] == 3


def test_rate_limit(ddb_table):
    assert not any(repo.rate_limited(ddb_table, "dev", 3) for _ in range(3))
    assert repo.rate_limited(ddb_table, "dev", 3)


def test_delete_site_data(ddb_table):
    repo.put_site(ddb_table, SITE, "hash1", "enc")
    repo.put_crew(ddb_table, "s1", "2026-10-11", {"headcount": 40})
    repo.put_checkin(ddb_table, "s1", "2026-10-11", "break_start", "abcdef12")
    site = repo.get_site(ddb_table, "s1")
    assert repo.delete_site_data(ddb_table, site) >= 5
    assert repo.get_site(ddb_table, "s1") is None
    assert repo.site_for_token(ddb_table, "tok123") is None
