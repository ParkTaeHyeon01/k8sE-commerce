"""
카테고리 크롤러 — 컬리 필터 API를 직접 호출해 베스트/세일 카테고리 목록을 수집하고 MongoDB에 저장
k8s CronJob으로 하루 1~2회 실행하면 컬리 카테고리 변경이 자동 반영된다

컬리 필터 API 응답 구조:
  data[].key == "category" 인 항목의 values[] 에 {key(코드), name, product_counts} 포함
  Playwright 없이 requests로 직접 호출 가능 (인증 불필요)
"""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).parent.parent / ".env")

from logger import get_logger

_MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
_MONGODB_DB  = os.environ.get("MONGODB_DB", "ecommerce")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.kurly.com/",
}

# target → 컬리 필터 API URL
_FILTER_URLS = {
    "best":  "https://api.kurly.com/collection/v2/home/sites/market/product-collections/market-best-logic/filters?parent_code=market-best",
    "sales": "https://api.kurly.com/collection/v2/home/sites/market/product-collections/market-sales-main1/filters?parent_code=market-sales",
}

_LABELS = {"best": "베스트", "sales": "할인"}


def fetch_categories(target: str, logger) -> list[dict]:
    """컬리 필터 API에서 카테고리 목록을 가져온다."""
    url = _FILTER_URLS[target]
    resp = requests.get(url, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    payload = resp.json()

    categories = []
    for group in payload.get("data", []):
        if group.get("key") != "category":
            continue
        for item in group.get("values", []):
            code = str(item.get("key", ""))
            name = item.get("name", "")
            count = item.get("product_counts", 0)
            if code.isdigit() and name:
                categories.append({"code": code, "name": name, "count": count})

    return categories


def save_categories(col, target: str, categories: list[dict]) -> None:
    """이번 수집 결과로 해당 target의 카테고리를 완전 교체한다."""
    if not categories:
        return
    now = datetime.now(timezone.utc).isoformat()
    col.delete_many({"target": target})
    col.insert_many([{"target": target, "updated_at": now, **c} for c in categories])


def run() -> None:
    trace_id = str(uuid.uuid4())
    logger = get_logger("category-crawler", trace_id)

    client = MongoClient(_MONGODB_URI)
    col = client[_MONGODB_DB]["categories"]

    for target, label in _LABELS.items():
        logger.info(f"카테고리 수집 시작 — {label}")
        try:
            cats = fetch_categories(target, logger)
            if cats:
                save_categories(col, target, cats)
                logger.info(f"{label} 카테고리 {len(cats)}건 저장")
                for c in cats:
                    logger.debug(f"  [{c['code']}] {c['name']} ({c['count']}건)")
            else:
                logger.error(f"{label} 카테고리 수집 실패 — 0건")
        except Exception as e:
            logger.error(f"{label} 카테고리 수집 오류: {e}")

    client.close()


if __name__ == "__main__":
    run()
