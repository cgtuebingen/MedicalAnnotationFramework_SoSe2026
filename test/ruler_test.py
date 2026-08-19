import pytest

from taplt.ui.ruler import calculate_tick_interval


@pytest.mark.parametrize(
    "visible_span, expected",
    [
        (0, 1.0),
        (-10, 1.0),
        (1, 0.2),
        (1000, 200),
        (1200, 500),
        (10000, 2000),
        (200, 50),
        (50, 10),
    ],
)
def test_calculate_tick_interval_prefers_nice_steps(visible_span, expected):
    assert calculate_tick_interval(visible_span) == expected