"""Publishes one simulated daily close per symbol to Kafka every TICK_SECONDS."""

import json
import math
import random
import time
from datetime import datetime, timedelta, timezone

from confluent_kafka import Producer

from app import config

START_PRICE = 100.0
DAILY_VOLATILITY = 0.02


def next_price(price: float, rng: random.Random) -> float:
    """Geometric random walk: the price moves by a random percentage and stays positive."""
    return round(price * math.exp(rng.gauss(0, DAILY_VOLATILITY)), 2)


def main() -> None:
    producer = Producer({"bootstrap.servers": config.KAFKA_BOOTSTRAP})
    rng = random.Random()
    prices = {symbol: START_PRICE for symbol in config.SYMBOLS}
    # Each tick is one simulated trading day, starting from today.
    day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    print(f"producer: sending {config.SYMBOLS} to topic {config.KAFKA_TOPIC}", flush=True)
    while True:
        for symbol in config.SYMBOLS:
            prices[symbol] = next_price(prices[symbol], rng)
            message = {"symbol": symbol, "ts": day.isoformat(), "price": prices[symbol]}
            producer.produce(config.KAFKA_TOPIC, key=symbol, value=json.dumps(message))
        producer.flush()
        day += timedelta(days=1)
        time.sleep(config.TICK_SECONDS)


if __name__ == "__main__":
    main()
