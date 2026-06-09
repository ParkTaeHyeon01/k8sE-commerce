# MongoDB / Redis 연결 모듈
import json
import os

import redis
from pymongo import MongoClient

_mongo_client: MongoClient | None = None
_redis_client: redis.Redis | None = None

_MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
_MONGODB_DB  = os.environ.get("MONGODB_DB", "ecommerce")
_REDIS_URL   = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
_CACHE_TTL   = int(os.environ.get("CACHE_TTL_SECONDS", "60"))


def get_collection():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(_MONGODB_URI)
    return _mongo_client[_MONGODB_DB]["products"]


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(_REDIS_URL, decode_responses=True)
    return _redis_client


def cache_get(key: str) -> dict | list | None:
    try:
        raw = get_redis().get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def cache_set(key: str, value: dict | list) -> None:
    try:
        get_redis().setex(key, _CACHE_TTL, json.dumps(value, ensure_ascii=False))
    except Exception:
        pass
