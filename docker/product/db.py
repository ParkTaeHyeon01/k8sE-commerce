# MongoDB / Redis / 인메모리 연결 모듈
import json
import os
import time

import redis
from pymongo import MongoClient

_mongo_client: MongoClient | None = None
_redis_write: redis.Redis | None = None
_redis_read:  redis.Redis | None = None

_MONGODB_URI      = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
_MONGODB_DB       = os.environ.get("MONGODB_DB", "ecommerce")
_REDIS_WRITE_URL  = os.environ.get("REDIS_WRITE_URL", "redis://localhost:6379/0")
_REDIS_READ_URL   = os.environ.get("REDIS_READ_URL",  "redis://localhost:6379/0")
_CACHE_TTL        = int(os.environ.get("CACHE_TTL_SECONDS", "300"))

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
        col.create_index("ngrams")  # nGram 배열 인덱스 — 부분 문자열 검색용
    return _mongo_client[_MONGODB_DB]["products"]


def get_categories_collection():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(_MONGODB_URI)
    return _mongo_client[_MONGODB_DB]["categories"]


def get_write_redis() -> redis.Redis:
    global _redis_write
    if _redis_write is None:
        _redis_write = redis.from_url(_REDIS_WRITE_URL, decode_responses=True, socket_connect_timeout=1, protocol=2)
    return _redis_write


def get_read_redis() -> redis.Redis:
    global _redis_read
    if _redis_read is None:
        _redis_read = redis.from_url(_REDIS_READ_URL, decode_responses=True, socket_connect_timeout=1, protocol=2)
    return _redis_read


def cache_get(key: str) -> dict | list | None:
    # 1차: 인메모리
    hit = _mem_get(key)
    if hit is not None:
        return hit
    # 2차: Redis
    try:
        raw = get_read_redis().get(key)
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
        get_write_redis().setex(key, _CACHE_TTL, json.dumps(value, ensure_ascii=False))
    except Exception:
        pass


def cache_delete_pattern(pattern: str) -> None:
    # 인메모리 캐시 전체 초기화 (패턴 매칭 비용보다 단순 초기화가 빠름)
    _mem.clear()
    try:
        r = get_write_redis()
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except Exception:
        pass
