"""Pure functions for price analytics. Each price is one simulated trading-day close."""

import statistics


def daily_return(previous: float | None, current: float) -> float | None:
    if previous is None or previous == 0:
        return None
    return current / previous - 1


def moving_average(prices: list[float], window: int) -> float | None:
    if len(prices) < window:
        return None
    return sum(prices[-window:]) / window


def returns(prices: list[float]) -> list[float]:
    return [curr / prev - 1 for prev, curr in zip(prices, prices[1:])]


def volatility(prices: list[float]) -> float | None:
    """Standard deviation of daily returns (not annualised)."""
    r = returns(prices)
    if len(r) < 2:
        return None
    return statistics.stdev(r)


def compute_metrics(prices: list[float]) -> dict:
    """Metrics for the newest price, given prices ordered oldest -> newest."""
    previous = prices[-2] if len(prices) >= 2 else None
    return {
        "daily_return": daily_return(previous, prices[-1]),
        "ma_5": moving_average(prices, 5),
        "ma_20": moving_average(prices, 20),
    }
