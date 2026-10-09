import pytest

from heatcore.niosh import limits, ral, rel


@pytest.mark.parametrize(
    "m, exp_rel, exp_ral",
    [(180, 30.76, 28.10), (300, 28.21, 24.97), (415, 26.59, 22.99)],
)
def test_rel_ral(m, exp_rel, exp_ral):
    assert rel(m) == pytest.approx(exp_rel, abs=0.05)
    assert ral(m) == pytest.approx(exp_ral, abs=0.05)


def test_worked_example_300w():
    assert round(rel(300), 1) == 28.2
    assert round(ral(300), 1) == 25.0


def test_limits_by_workload():
    out = limits("moderate")
    assert out["metabolic_rate_w"] == 300 and out["rel_c"] == 28.2


def test_rejects_non_positive():
    with pytest.raises(ValueError):
        rel(0)
