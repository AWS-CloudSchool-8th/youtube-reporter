from fastapi import FastAPI
from shared_lib.core.config import settings
from shared_lib.core.redis_client import redis_client

app = FastAPI(
    title="SharedLib Utility API",
    description="For config/redis/database health checking",
    version=settings.VERSION
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/redis/ping")
def redis_ping():
    redis_client.redis.set("ping", "pong", ex=10)
    return {"ping": redis_client.get("ping")}
