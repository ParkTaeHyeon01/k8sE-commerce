# MongoDB / Redis / 인메모리 연결 모듈
import json
import os
import time

import redis
from pymongo import MongoClient

_mongo_client: MongoClient | None = None
_redis_client: redis.Redis | None = None

_MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
_MONGODB_DB  = os.environ.get("MONGODB_DB", "ecommerce")
_REDIS_URL   = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
_CACHE_TTL   = int(os.environ.get("CACHE_TTL_SECONDS", "300"))

# 프로세스 내 1차 캐시 — Redis보다 빠름, 재시작 시 초기화
_mem: dict = {}


def _mem_get(key: str):
    item = _mem.get(key)
    if item and time.time() < item["exp"]:
        return item["val"]
    return None


def _mem_set(key: str, val, ttl: int = _CACHE_TTL) -> None:
    _mem[key] = {"val": val, "exp": time.time() + ttl}


def get_collection():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(_MONGODB_URI)
        col = _mongo_client[_MONGODB_DB]["products"]
        # 목록 쿼리 필터 필드에 복합 인덱스 — 최초 연결 시 1회 생성
        col.create_index([("status", 1), ("targets", 1), ("category_code", 1)])
    return _mongo_client[_MONGODB_DB]["products"]


def get_categories_collection():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(_MONGODB_URI)
    return _mongo_client[_MONGODB_DB]["categories"]


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(_REDIS_URL, decode_responses=True, socket_connect_timeout=1)
    return _redis_client


def cache_get(key: str) -> dict | list | None:
    # 1차: 인메모리
    hit = _mem_get(key)
    if hit is not None:
        return hit
    # 2차: Redis
    try:
        raw = get_redis().get(key)
        if raw:
            val = json.loads(raw)
            _mem_set(key, val)
            return val
    except Exception:
        pass
    return None


def cache_set(key: str, value: dict | list) -> None:
    _mem_set(key, value)
    try:
        get_redis().setex(key, _CACHE_TTL, json.dumps(value, ensure_ascii=False))
    except Exception:
        pass
