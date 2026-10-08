import psycopg
from psycopg.rows import dict_row

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    id           BIGSERIAL PRIMARY KEY,
    symbol       TEXT NOT NULL,
    ts           TIMESTAMPTZ NOT NULL,
    price        DOUBLE PRECISION NOT NULL,
    daily_return DOUBLE PRECISION,
    ma_5         DOUBLE PRECISION,
    ma_20        DOUBLE PRECISION,
    UNIQUE (symbol, ts)
);
"""


def connect() -> psycopg.Connection:
    return psycopg.connect(config.DATABASE_URL, row_factory=dict_row, autocommit=True)


def init_schema(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA)


def insert_price(conn, symbol: str, ts: str, price: float, metrics: dict) -> bool:
    """Returns False if this (symbol, ts) was already stored, so replays are harmless."""
    cur = conn.execute(
        """
        INSERT INTO prices (symbol, ts, price, daily_return, ma_5, ma_20)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol, ts) DO NOTHING
        """,
        (symbol, ts, price, metrics["daily_return"], metrics["ma_5"], metrics["ma_20"]),
    )
    return cur.rowcount == 1


def recent_prices(conn, symbol: str, n: int) -> list[float]:
    """Last n prices for a symbol, ordered oldest -> newest."""
    rows = conn.execute(
        "SELECT price FROM prices WHERE symbol = %s ORDER BY ts DESC LIMIT %s",
        (symbol, n),
    ).fetchall()
    return [r["price"] for r in reversed(rows)]


def price_history(conn, symbol: str, limit: int) -> list[dict]:
    return conn.execute(
        """
        SELECT ts, price, daily_return, ma_5, ma_20
        FROM prices WHERE symbol = %s ORDER BY ts DESC LIMIT %s
        """,
        (symbol, limit),
    ).fetchall()


def symbols(conn) -> list[str]:
    rows = conn.execute("SELECT DISTINCT symbol FROM prices ORDER BY symbol").fetchall()
    return [r["symbol"] for r in rows]


def latest_per_symbol(conn) -> list[dict]:
    return conn.execute(
        """
        SELECT DISTINCT ON (symbol) symbol, ts, price, daily_return, ma_5, ma_20
        FROM prices ORDER BY symbol, ts DESC
        """
    ).fetchall()
