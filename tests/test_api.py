from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import api

client = TestClient(api.app)
TS = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FakeConn:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeCache:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value


def test_prices_404_for_unknown_symbol(monkeypatch):
    monkeypatch.setattr(api.db, "connect", FakeConn)
    monkeypatch.setattr(api.db, "price_history", lambda conn, symbol, limit: [])
    assert client.get("/prices/XYZ").status_code == 404


def test_analytics_returns_latest_metrics_and_volatility(monkeypatch):
    rows = [  # newest first, as the database returns them
        {"ts": TS, "price": 99.0, "daily_return": -0.1, "ma_5": None, "ma_20": None},
        {"ts": TS, "price": 110.0, "daily_return": 0.1, "ma_5": None, "ma_20": None},
        {"ts": TS, "price": 100.0, "daily_return": None, "ma_5": None, "ma_20": None},
    ]
    monkeypatch.setattr(api.db, "connect", FakeConn)
    monkeypatch.setattr(api.db, "price_history", lambda conn, symbol, limit: rows)

    body = client.get("/analytics/aapl").json()
    assert body["symbol"] == "AAPL"
    assert body["price"] == 99.0
    assert round(body["volatility_20d"], 4) == 0.1414


def test_summary_is_served_from_cache_on_second_call(monkeypatch):
    calls = []
    monkeypatch.setattr(api, "cache", FakeCache())
    monkeypatch.setattr(api.db, "connect", FakeConn)
    monkeypatch.setattr(
        api.db,
        "latest_per_symbol",
        lambda conn: calls.append(1) or [{"symbol": "AAPL", "ts": TS, "price": 100.0}],
    )

    first = client.get("/summary").json()
    second = client.get("/summary").json()

    assert first["cached"] is False
    assert second["cached"] is True
    assert second["symbols"][0]["symbol"] == "AAPL"
    assert len(calls) == 1
