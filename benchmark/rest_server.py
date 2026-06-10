"""
REST 벤치마크 서버 — gRPC와 동일한 MongoDB 쿼리를 JSON으로 반환
포트 50054
"""
import os
import uvicorn
from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI()

_MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
_MONGODB_DB  = os.environ.get("MONGODB_DB", "ecommerce")

_client = MongoClient(_MONGODB_URI)
_col    = _client[_MONGODB_DB]["products"]

# 시나리오 2용 in-memory 고정 데이터 (gRPC in-memory 서버와 동일한 20개)
_INMEMORY = [
    {
        "product_id":     f"test-{i:04d}",
        "name":           f"테스트 상품 {i}",
        "sale_price":     10000 + i * 100,
        "original_price": 15000 + i * 100,
        "discount_rate":  30 + (i % 10),
        "image_url":      "https://example.com/image.jpg",
        "category_code":  "100",
        "category_name":  "식품",
        "targets":        ["best"],
        "delivery_info":  "새벽배송",
        "stock":          100,
    }
    for i in range(20)
]


@app.get("/products")
def list_products(target: str = "best", page: int = 1, page_size: int = 20):
    """시나리오 1: 실제 MongoDB 쿼리"""
    query = {"status": "ready"}
    if target:
        query["targets"] = target

    pipeline = [
        {"$match": query},
        {"$project": {"detail_blocks": 0, "_id": 0, "ngrams": 0}},
        {"$facet": {
            "total":    [{"$count": "n"}],
            "products": [
                {"$skip":  (page - 1) * page_size},
                {"$limit": page_size},
            ],
        }},
    ]
    result = list(_col.aggregate(pipeline))
    total = result[0]["total"][0]["n"] if result and result[0]["total"] else 0
    docs  = result[0]["products"] if result else []
    return {"products": docs, "total": total, "page": page, "page_size": page_size}


@app.get("/products/inmemory")
def list_products_inmemory():
    """시나리오 2: in-memory 고정 데이터 (순수 직렬화/전송 속도 비교용)"""
    return {"products": _INMEMORY, "total": len(_INMEMORY), "page": 1, "page_size": 20}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=50054)
