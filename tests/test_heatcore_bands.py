import pytest

from heatcore.bands import band_for


@pytest.mark.parametrize(
    "e, rest, status",
    [
        (-2.0, 0, "normal"), (0.0, 0, "normal"),
        (0.01, 15, "caution"), (1.0, 15, "caution"),
        (1.01, 30, "high"), (2.0, 30, "high"),
        (2.01, 45, "very_high"), (3.0, 45, "very_high"),
        (3.01, 60, "stop"), (9.0, 60, "stop"),
    ],
)
def test_plan_bands(e, rest, status):
    assert band_for(e) == (rest, status)
