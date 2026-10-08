import os

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "market-prices")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://market:market@localhost:5432/market")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

SYMBOLS = os.getenv("SYMBOLS", "AAPL,MSFT,NVDA,AMZN").split(",")
TICK_SECONDS = float(os.getenv("TICK_SECONDS", "1"))
SUMMARY_CACHE_TTL = int(os.getenv("SUMMARY_CACHE_TTL", "5"))
