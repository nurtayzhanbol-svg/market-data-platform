import pytest

from app.analytics import compute_metrics, daily_return, moving_average, volatility


def test_daily_return():
    assert daily_return(100.0, 110.0) == pytest.approx(0.10)
    assert daily_return(100.0, 95.0) == pytest.approx(-0.05)


def test_daily_return_without_previous_price():
    assert daily_return(None, 100.0) is None


def test_moving_average_uses_last_window_prices():
    assert moving_average([1, 2, 3, 4, 5, 6], 5) == pytest.approx(4.0)


def test_moving_average_needs_enough_prices():
    assert moving_average([1, 2, 3], 5) is None


def test_volatility():
    # returns: +10%, -10%  -> stdev of [0.1, -0.1]
    assert volatility([100.0, 110.0, 99.0]) == pytest.approx(0.1414, abs=1e-4)
    assert volatility([100.0, 110.0]) is None


def test_compute_metrics_for_first_price():
    assert compute_metrics([100.0]) == {"daily_return": None, "ma_5": None, "ma_20": None}


def test_compute_metrics_with_history():
    prices = [float(p) for p in range(1, 21)]  # 1..20
    m = compute_metrics(prices)
    assert m["daily_return"] == pytest.approx(20 / 19 - 1)
    assert m["ma_5"] == pytest.approx(18.0)
    assert m["ma_20"] == pytest.approx(10.5)
