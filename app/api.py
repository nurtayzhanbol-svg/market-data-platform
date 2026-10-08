import json
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from app import config, db
from app.analytics import volatility
SUMMARY_CACHE_KEY = "summary"
cache = redis.Redis.from_url(config.REDIS_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    with db.connect() as conn:
        db.init_schema(conn)
    yield


app = FastAPI(title="Real-Time Market Data Platform", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/symbols")
def list_symbols() -> list[str]:
    with db.connect() as conn:
        return db.symbols(conn)


@app.get("/prices/{symbol}")
def prices(symbol: str, limit: int = Query(50, ge=1, le=1000)) -> list[dict]:
    with db.connect() as conn:
        rows = db.price_history(conn, symbol.upper(), limit)
    if not rows:
        raise HTTPException(404, f"no prices for {symbol}")
    return rows


@app.get("/analytics/{symbol}")
def analytics(symbol: str) -> dict:
    with db.connect() as conn:
        rows = db.price_history(conn, symbol.upper(), 21)
    if not rows:
        raise HTTPException(404, f"no prices for {symbol}")
    latest = rows[0]
    oldest_first = [r["price"] for r in reversed(rows)]
    return {
        "symbol": symbol.upper(),
        "ts": latest["ts"],
        "price": latest["price"],
        "daily_return": latest["daily_return"],
        "ma_5": latest["ma_5"],
        "ma_20": latest["ma_20"],
        "volatility_20d": volatility(oldest_first),
    }


@app.get("/summary")
def summary() -> dict:
    """Latest price of every symbol, cached in Redis for SUMMARY_CACHE_TTL seconds."""
    cached = cache.get(SUMMARY_CACHE_KEY)
    if cached is not None:
        return {"cached": True, "symbols": json.loads(cached)}

    with db.connect() as conn:
        rows = db.latest_per_symbol(conn)
    data = jsonable_encoder(rows)
    cache.set(SUMMARY_CACHE_KEY, json.dumps(data), ex=config.SUMMARY_CACHE_TTL)
    return {"cached": False, "symbols": data}
