import random

from app.producer import next_price


def test_next_price_stays_positive_and_close():
    rng = random.Random(42)
    price = 100.0
    for _ in range(1000):
        new = next_price(price, rng)
        assert new > 0
        assert abs(new / price - 1) < 0.15  # 2% daily volatility: a 7-sigma move is ~15%
        price = new


def test_next_price_is_reproducible_with_seed():
    assert next_price(100.0, random.Random(1)) == next_price(100.0, random.Random(1))
