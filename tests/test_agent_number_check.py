from agent.number_check import canon, numbers_in_text, verify_numbers

TOOLS = [{"stop_from": 12, "stop_to": 15, "water": {"cans_20l": 6}, "peak_wbgt": 31.4,
          "new_workers": {"fraction": 0.2}, "forecast_issued": "2026-10-10T12:00:00"}]


def test_canon():
    assert canon("06") == "6" and canon("28.20") == "28.2" and canon("6:00") == "6"


def test_passes_when_numbers_come_from_tools():
    reply = "Kal 12 se 3 baje tak kaam band. 6 can paani. Peak WBGT 31.4. Naye log 20% kaam."
    assert verify_numbers(reply, TOOLS) == []


def test_flags_invented_numbers():
    assert verify_numbers("Kaam 1 se 4 baje tak band. 9 can.", TOOLS) == ["1", "4", "9"]


def test_ignores_list_markers_and_allows_108():
    reply = "1. Chhaon mein jao.\n2. Paani piyo.\n3. Behoshi ho to 108."
    assert verify_numbers(reply, TOOLS) == []


def test_extracts_times():
    assert numbers_in_text("subah 6:30 se 10:00") == ["6:30", "10"]
