# How to explain this project

## 30-second pitch

"I built a small event-driven backend to learn streaming. A producer publishes simulated daily stock prices to Kafka. A consumer reads each price, computes the daily return and 5- and 20-day moving averages, and stores them in PostgreSQL. A FastAPI service serves price history, analytics and a market summary, and the summary is cached in Redis. The whole stack starts with one `docker compose up`."

## Walk through one price

1. `producer.py` moves the price by a random percentage and sends `{"symbol", "ts", "price"}` to topic `market-prices` with key = symbol.
2. `consumer.py` polls the message, reads the previous 19 prices from Postgres and calls `compute_metrics`.
3. It inserts the row (`ON CONFLICT DO NOTHING`), then commits the Kafka offset.
4. `GET /summary` returns the Redis copy if it exists; otherwise it queries Postgres and stores the result in Redis for 5 seconds.

## Likely questions

**Why Kafka and not the producer writing straight to the database?**
Decoupling. The producer does not need to know who uses the data; more consumers (alerts, another analytics job) can read the same topic. Kafka also buffers messages if the consumer is slow or down.

**What happens if the consumer crashes?**
Offsets are committed after the database insert, so on restart it re-reads uncommitted messages (at-least-once). The unique constraint on `(symbol, ts)` turns duplicates into no-ops, so the result is the same as exactly-once processing.

**Why is the Kafka key the symbol?**
Messages with the same key go to the same partition, and Kafka keeps order within a partition. The moving average needs prices in order.

**How would you scale it?**
More partitions and several consumers in the same consumer group, each owning some partitions (and therefore some symbols). A connection pool in the API. Kafka replication factor 3 in production.

**Why cache only `/summary`?**
It is the endpoint every client would call often and it touches every symbol. History and analytics for one symbol are cheap indexed queries.

**Cache invalidation: TTL or delete on write?**
TTL here. Prices change every second, so deleting the key on every write would mean almost every request misses the cache. With a 5-second TTL the database is hit at most once per 5 seconds, and the trade-off is that the summary can be up to 5 seconds stale. Delete-on-write is better when data changes rarely and must be fresh.

**How is volatility computed?**
Standard deviation of daily returns over the last 20 returns. It is not annualised (you would multiply by √252 for that).

**What would you add next?**
A dead-letter topic for malformed messages, a connection pool, metrics (consumer lag), and an integration test with Testcontainers.

## Exercises for yourself

- Add a `ma_50` column end to end (analytics, db, consumer, API, test).
- Stop the consumer for 30 seconds (`docker compose stop consumer`), start it again and watch it catch up.
- Run two consumers (`docker compose up -d --scale consumer=2`) and explain why only one receives messages with a single partition.
