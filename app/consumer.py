"""Reads price ticks from Kafka, computes analytics and stores them in PostgreSQL."""

import json

from confluent_kafka import Consumer

from app import config, db
from app.analytics import compute_metrics

def process(conn, raw_value: bytes) -> bool:
    tick = json.loads(raw_value)
    history = db.recent_prices(conn, tick["symbol"], 19)
    metrics = compute_metrics(history + [tick["price"]])
    return db.insert_price(conn, tick["symbol"], tick["ts"], tick["price"], metrics)


def main() -> None:
    conn = db.connect()
    db.init_schema(conn)
    consumer = Consumer(
        {
            "bootstrap.servers": config.KAFKA_BOOTSTRAP,
            "group.id": "analytics",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([config.KAFKA_TOPIC])
    print(f"consumer: listening on topic {config.KAFKA_TOPIC}", flush=True)

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"consumer: kafka error {msg.error()}", flush=True)
            continue
        process(conn, msg.value())
        # Commit only after the row is saved: at-least-once delivery.
        consumer.commit(message=msg)


if __name__ == "__main__":
    main()
