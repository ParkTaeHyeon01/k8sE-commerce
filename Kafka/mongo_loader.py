# MongoDB 적재 모듈 - product_id 기준 upsert로 products 컬렉션에 반영한다
#
# upsert를 쓰는 이유: 크롤러가 상품을 완성하는 즉시 보내고, 같은 상품이 여러 컬렉션
# (베스트/할인)에 등장하거나 재크롤링으로 다시 들어올 수 있다. product_id로 매칭해
# 덮어쓰면 중복 문서 없이 항상 최신 상태로 수렴하고, 크롤러가 중간에 멈췄다 재시작해도
# 안전하다 (멱등성).
import os
from datetime import datetime, timezone

from pymongo import MongoClient

_MONGODB_URI = os.environ["MONGODB_URI"]
_MONGODB_DB = os.environ.get("MONGODB_DB", "ecommerce")
_COLLECTION_NAME = "products"

# 메시지에서 그대로 옮겨 담을 필드들 (targets/updated_at은 별도 처리)
_FIELDS = (
    "category_code", "category_name", "name",
    "original_price", "sale_price", "discount_rate", "delivery_info",
    "image_url", "detail_url", "detail_blocks",
    "status", "trace_id", "crawled_at",
)


def get_collection():
    """products 컬렉션 핸들을 반환한다."""
    client = MongoClient(_MONGODB_URI)
    return client[_MONGODB_DB][_COLLECTION_NAME]


def upsert_product(collection, product: dict) -> None:
    """상품 데이터 하나를 product_id 기준으로 upsert한다.

    - targets는 $addToSet으로 누적 (베스트/할인 양쪽에 등장해도 사라지지 않게)
    - status는 메시지의 값을 그대로 반영 (draft -> ready 전환은 크롤러가 결정)
    """
    fields = {key: product[key] for key in _FIELDS if key in product}
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    collection.update_one(
        {"product_id": product["product_id"]},
        {
            "$set": fields,
            "$addToSet": {"targets": product["target"]},
        },
        upsert=True,
    )
