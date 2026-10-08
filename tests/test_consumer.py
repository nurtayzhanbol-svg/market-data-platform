import json

from app import consumer


def test_process_computes_metrics_from_history(monkeypatch):
    saved = {}
    monkeypatch.setattr(consumer.db, "recent_prices", lambda conn, symbol, n: [100.0, 102.0, 104.0, 106.0])
    monkeypatch.setattr(
        consumer.db,
        "insert_price",
        lambda conn, symbol, ts, price, metrics: saved.update(symbol=symbol, price=price, **metrics) or True,
    )

    tick = {"symbol": "AAPL", "ts": "2026-01-01T00:00:00+00:00", "price": 108.0}
    assert consumer.process(None, json.dumps(tick).encode())

    assert saved["ma_5"] == 104.0
    assert round(saved["daily_return"], 4) == round(108 / 106 - 1, 4)
    assert saved["ma_20"] is None


def test_process_reports_duplicate(monkeypatch):
    monkeypatch.setattr(consumer.db, "recent_prices", lambda conn, symbol, n: [])
    monkeypatch.setattr(consumer.db, "insert_price", lambda *args: False)

    tick = {"symbol": "AAPL", "ts": "2026-01-01T00:00:00+00:00", "price": 100.0}
    assert not consumer.process(None, json.dumps(tick).encode())
