# Real-Time Market Data Platform

A small event-driven backend: a producer streams simulated stock prices through **Kafka**, a consumer computes analytics and stores them in **PostgreSQL**, and a **FastAPI** service exposes prices, analytics and a **Redis**-cached market summary.

```
producer ──(Kafka topic: market-prices)──> consumer ──> PostgreSQL <── FastAPI ──> client
                                                                         │
                                                                       Redis (summary cache)
```

Prices are simulated: every second the producer publishes one **daily close** per symbol (one tick = one simulated trading day), so moving averages and daily returns are meaningful without waiting for real days.

## Run

Requires Docker with Compose.

```bash
docker compose up -d --build     # kafka, postgres, redis, producer, consumer, api
curl localhost:8000/summary      # after a few seconds
docker compose logs -f consumer  # watch messages being processed
docker compose down -v           # stop and delete data
```

Interactive API docs: http://localhost:8000/docs

## API

| Endpoint | Returns |
|---|---|
| `GET /health` | `{"status": "ok"}` |
| `GET /symbols` | symbols that have data |
| `GET /prices/{symbol}?limit=50` | price history, newest first, with `daily_return`, `ma_5`, `ma_20` |
| `GET /analytics/{symbol}` | latest price, daily return, 5- and 20-day moving averages, 20-day volatility |
| `GET /summary` | latest price for every symbol; `"cached": true` when served from Redis |

## Code

| File | What it does |
|---|---|
| `app/producer.py` | geometric random walk per symbol, publishes JSON to Kafka (key = symbol) |
| `app/consumer.py` | reads a tick, loads the last 19 prices, computes metrics, inserts the row, commits the Kafka offset |
| `app/analytics.py` | pure functions: daily return, moving average, volatility |
| `app/db.py` | table schema and SQL queries (psycopg 3) |
| `app/api.py` | FastAPI endpoints and Redis caching |
| `app/config.py` | settings from environment variables |

## Tests

```bash
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

Unit tests cover the analytics formulas, the producer's random walk, the consumer's processing step and the API (database and Redis are replaced with fakes). `scripts/smoke.sh` checks the running stack end to end.

## Design choices

- **Kafka key = symbol.** All ticks of one symbol go to the same partition, so they arrive in order.
- **At-least-once + idempotent insert.** The consumer commits the offset only after saving the row. If it crashes before committing, the message is read again; `UNIQUE (symbol, ts)` with `ON CONFLICT DO NOTHING` makes the replay harmless.
- **Cache with a TTL.** `/summary` is cached in Redis for 5 seconds. New prices arrive every second, so deleting the cache on every write would make it almost useless; instead clients accept data up to 5 seconds old.
- **Metrics stored at write time.** Each row keeps the metrics that were true when the price arrived, so reading history is a simple `SELECT`.

## Limitations

- Single Kafka broker, single partition, one consumer: no scaling or replication.
- Simulated data only; no real market feed.
- New database connection per API request (fine for a demo; a real service would use a connection pool).
- No authentication.

See [`docs/INTERVIEW.md`](docs/INTERVIEW.md) for how to explain the project and likely interview questions.
