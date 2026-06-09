# gRPC 서비스 구현체
# ListProducts: Redis 캐시 우선 조회 → 미스 시 MongoDB 쿼리 후 캐시 저장
# GetProduct: product_id 기준 단건 조회 (캐시 없음 - 상세는 요청 빈도 낮음)
import product_pb2
import product_pb2_grpc
from db import cache_get, cache_set, get_collection
from logger import get_logger

_log = get_logger("product-grpc")


def _doc_to_summary(doc: dict) -> product_pb2.ProductSummary:
    return product_pb2.ProductSummary(
        product_id=doc.get("product_id", ""),
        name=doc.get("name", ""),
        sale_price=doc.get("sale_price") or 0,
        original_price=doc.get("original_price") or 0,
        discount_rate=doc.get("discount_rate") or 0,
        image_url=doc.get("image_url") or "",
        category_code=doc.get("category_code") or "",
        category_name=doc.get("category_name") or "",
        targets=doc.get("targets") or [],
        delivery_info=doc.get("delivery_info") or "",
    )


def _doc_to_detail(doc: dict) -> product_pb2.ProductDetail:
    blocks = [
        product_pb2.DetailBlock(type=b.get("type", ""), value=b.get("value", ""))
        for b in (doc.get("detail_blocks") or [])
    ]
    return product_pb2.ProductDetail(
        product_id=doc.get("product_id", ""),
        name=doc.get("name", ""),
        sale_price=doc.get("sale_price") or 0,
        original_price=doc.get("original_price") or 0,
        discount_rate=doc.get("discount_rate") or 0,
        image_url=doc.get("image_url") or "",
        detail_url=doc.get("detail_url") or "",
        category_code=doc.get("category_code") or "",
        category_name=doc.get("category_name") or "",
        targets=doc.get("targets") or [],
        delivery_info=doc.get("delivery_info") or "",
        detail_blocks=blocks,
        status=doc.get("status") or "",
        crawled_at=doc.get("crawled_at") or "",
    )


class ProductServicer(product_pb2_grpc.ProductServiceServicer):

    def ListProducts(self, request, context):
        page      = max(request.page, 1)
        page_size = request.page_size if request.page_size > 0 else 20
        target    = request.target or ""
        cat_code  = request.category_code or ""

        cache_key = f"list:{target}:{cat_code}:{page}:{page_size}"
        cached = cache_get(cache_key)
        if cached:
            _log.info(f"캐시 히트 - {cache_key}")
            products = [_doc_to_summary(d) for d in cached["products"]]
            return product_pb2.ListProductsResponse(
                products=products,
                total=cached["total"],
                page=page,
                page_size=page_size,
            )

        # detail_blocks 필터 제거 — status:"ready" 가 이미 보장함 (인덱스 풀활용)
        query: dict = {"status": "ready"}
        if target:
            query["targets"] = target
        if cat_code:
            query["category_code"] = cat_code

        # count + find 를 $facet 한 번으로 합쳐 MongoDB 왕복 1회 절감
        col = get_collection()
        result = list(col.aggregate([
            {"$match": query},
            {"$project": {"detail_blocks": 0}},  # 큰 필드를 facet 전에 제거
            {"$facet": {
                "total":    [{"$count": "n"}],
                "products": [
                    {"$skip": (page - 1) * page_size},
                    {"$limit": page_size},
                    {"$project": {"_id": 0}},
                ],
            }},
        ]))
        total = result[0]["total"][0]["n"] if result and result[0]["total"] else 0
        docs  = result[0]["products"] if result else []

        cache_set(cache_key, {"products": docs, "total": total})
        _log.info(f"목록 조회 - target={target} cat={cat_code} page={page} total={total}")

        return product_pb2.ListProductsResponse(
            products=[_doc_to_summary(d) for d in docs],
            total=total,
            page=page,
            page_size=page_size,
        )

    def GetProduct(self, request, context):
        product_id = request.product_id
        col = get_collection()
        doc = col.find_one({"product_id": product_id}, {"_id": 0})
        if not doc:
            _log.info(f"상품 없음 - product_id={product_id}")
            return product_pb2.GetProductResponse(found=False)
        _log.info(f"상품 조회 - product_id={product_id}")
        return product_pb2.GetProductResponse(product=_doc_to_detail(doc), found=True)
