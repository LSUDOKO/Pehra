import pytest

from agent.roster import parse_crew_roster, readback


@pytest.mark.parametrize("text, exp", [
    ("40 log, 10 bhaari kaam, 3 naye aaye", (40, 10, 3)),
    ("chalis log hain, das bhari kaam karenge, teen naye", (40, 10, 3)),
    ("४० लोग, १० भारी काम, ३ नए आए", (40, 10, 3)),
    ("चालीस मज़दूर, दस भारी काम", (40, 10, 0)),
    ("25 workers, 5 heavy, 2 new", (25, 5, 2)),
])
def test_parses(text, exp):
    r = parse_crew_roster(text)
    assert (r["headcount"], r["heavy_count"], r["new_count"]) == exp
    assert r["confidence"] == 1.0


def test_inconsistent_counts_low_confidence():
    assert parse_crew_roster("5 log, 10 bhaari")["confidence"] == 0.0


def test_no_numbers():
    assert parse_crew_roster("aaj garmi hai")["confidence"] == 0.0


def test_readback():
    r = parse_crew_roster("40 log, 10 bhaari kaam, 3 naye aaye")
    assert readback(r) == "40 log, 10 bhaari kaam, 3 naye. Sahi hai?"
