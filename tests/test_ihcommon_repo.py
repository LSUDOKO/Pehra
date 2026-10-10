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


def test_person_roundtrip_and_listing(ddb_table):
    person = {"place": "Varanasi", "lat": 25.3, "lon": 83.0, "household": {"elderly": 1}}
    repo.put_person(ddb_table, "p1", person)
    repo.update_person(ddb_table, "p1", family_enc="x")
    assert repo.get_person(ddb_table, "p1")["family_enc"] == "x"
    repo.update_person(ddb_table, "p1", family_enc=None)
    assert "family_enc" not in repo.get_person(ddb_table, "p1")
    assert [p["owner_hash"] for p in repo.list_people(ddb_table)] == ["p1"]


def test_community_point_needs_two_reporters(ddb_table):
    assert repo.report_point(ddb_table, "delhi", 28.63151, 77.21672, "community_water", "aaaa") == 1
    assert repo.report_point(ddb_table, "delhi", 28.63151, 77.21672, "community_water", "aaaa") == 1
    assert repo.community_points(ddb_table, "delhi") == []
    assert repo.report_point(ddb_table, "delhi", 28.63152, 77.21671, "community_water", "bbbb") == 2
    assert len(repo.community_points(ddb_table, "delhi")) == 1
