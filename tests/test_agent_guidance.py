from agent.guidance import search_guidance


def test_water_query_finds_niosh():
    out = search_guidance("kitna paani dena chahiye")
    assert out and "NIOSH" in out[0]["source"]


def test_imd_query():
    assert "IMD" in search_guidance("IMD heatwave warning nahi hai")[0]["source"]


def test_unrelated_query_empty():
    assert search_guidance("xyzzy") == []
