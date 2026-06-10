# MongoDB 적재 모듈 - product_id 기준 upsert로 products 컬렉션에 반영한다
#
# upsert를 쓰는 이유: 크롤러가 상품을 완성하는 즉시 보내고, 같은 상품이 여러 컬렉션
# (베스트/할인)에 등장하거나 재크롤링으로 다시 들어올 수 있다. product_id로 매칭해
# 덮어쓰면 중복 문서 없이 항상 최신 상태로 수렴하고, 크롤러가 중간에 멈췄다 재시작해도
# 안전하다 (멱등성).
import os
import re
from datetime import datetime, timezone

from pymongo import MongoClient

_MONGODB_URI = os.environ["MONGODB_URI"]
_MONGODB_DB = os.environ.get("MONGODB_DB", "ecommerce")
_COLLECTION_NAME = "products"

# 숫자+단위 패턴 (500g, 1L, 2kg 등) 제거
_UNIT_PATTERN = re.compile(r"\d+(\.\d+)?\s*(ml|ML|l|L|g|G|kg|KG|mg|MG|개|팩|봉|병|캔|박스|세트|인분|번들|plus|Plus)?", re.IGNORECASE)

# 매번 최신값으로 덮어써야 하는 필드
_SET_FIELDS = (
    "name", "original_price", "sale_price", "discount_rate", "delivery_info",
    "image_url", "detail_url", "detail_blocks",
    "status", "trace_id", "crawled_at",
)
# 최초 수집 시에만 저장 — 이후 덮어쓰지 않음
# (같은 상품이 다른 카테고리 번들로 재크롤링되어도 원래 카테고리 유지)
_SET_ON_INSERT_FIELDS = (
    "category_code", "category_name",
)


def get_collection():
    """products 컬렉션 핸들을 반환한다."""
    client = MongoClient(_MONGODB_URI)
    return client[_MONGODB_DB][_COLLECTION_NAME]


def get_keywords_collection():
    client = MongoClient(_MONGODB_URI)
    return client[_MONGODB_DB]["keywords"]


def _extract_keywords(name: str) -> list[str]:
    """상품명에서 의미있는 단어만 추출한다. 숫자/단위/특수문자 제거."""
    cleaned = _UNIT_PATTERN.sub(" ", name)
    words = re.split(r"[\s\[\]()·/\-·,]+", cleaned)
    return [w for w in words if len(w) >= 2]


def upsert_keywords(col, name: str) -> None:
    """상품명 단어들을 keywords 컬렉션에 upsert한다 (count 누적)."""
    for word in _extract_keywords(name):
        col.update_one(
            {"text": word},
            {"$inc": {"count": 1}},
            upsert=True,
        )


def upsert_product(collection, product: dict) -> None:
    """상품 데이터 하나를 product_id 기준으로 upsert한다.

    - targets는 $addToSet으로 누적 (베스트/할인 양쪽에 등장해도 사라지지 않게)
    - category_code/category_name은 $setOnInsert — 최초 수집 카테고리 유지
      (다른 카테고리 번들로 재크롤링되어도 덮어쓰지 않음)
    """
    set_fields = {key: product[key] for key in _SET_FIELDS if key in product}
    set_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    set_on_insert = {key: product[key] for key in _SET_ON_INSERT_FIELDS if key in product}

    collection.update_one(
        {"product_id": product["product_id"]},
        {
            "$set": set_fields,
            "$setOnInsert": set_on_insert,
            "$addToSet": {"targets": product["target"]},
        },
        upsert=True,
    )
    if "name" in product:
        upsert_keywords(get_keywords_collection(), product["name"])


def sync_targets(collection, target: str, product_ids: list[str]) -> int:
    """이번 크롤링에서 보이지 않은 상품을 target에서 제거해 원본 목록과 동기화한다.

    $addToSet은 누적만 하므로, 베스트/할인 목록에서 빠진 상품도 targets에 그대로
    남는 문제가 있었다. 이번 크롤링에서 확인된 product_id 목록(product_ids)에
    없으면서 이 target을 갖고 있는 상품은 $pull로 target을 제거한다.
    (모든 target이 빠지더라도 상품 문서 자체는 삭제하지 않는다 - 상세페이지 등에서
    여전히 조회될 수 있다)
    """
    result = collection.update_many(
        {"targets": target, "product_id": {"$nin": product_ids}},
        {"$pull": {"targets": target}},
    )
    return result.modified_count
