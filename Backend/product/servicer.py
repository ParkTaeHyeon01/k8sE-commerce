# gRPC 서비스 구현체
# ListProducts: Redis 캐시 우선 조회 → 미스 시 MongoDB 쿼리 후 캐시 저장
# GetProduct: product_id 기준 단건 조회 (캐시 없음 - 상세는 요청 빈도 낮음)
import re
import product_pb2
import product_pb2_grpc
from db import cache_get, cache_set, get_collection, get_categories_collection
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
        stock=doc.get("stock") if doc.get("stock") is not None else 100,
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
        stock=doc.get("stock") if doc.get("stock") is not None else 100,
    )


class ProductServicer(product_pb2_grpc.ProductServiceServicer):

    def ListProducts(self, request, context):
        page      = max(request.page, 1)
        page_size = request.page_size if request.page_size > 0 else 20
        target    = request.target or ""
        cat_code  = request.category_code or ""
        sort_by   = request.sort_by or ""
        search    = request.search or ""

        # 검색어가 없을 때만 캐시 사용 (검색은 조합이 너무 다양해 캐시 효율 낮음)
        if not search:
            cache_key = f"list:{target}:{cat_code}:{page}:{page_size}:{sort_by}"
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
        if search:
            search_by = request.search_by or ""
            if search_by == "id":
                query["product_id"] = search
            elif search_by == "name" or re.fullmatch(r"\d+", search):
                # 관리자 상품명 검색 또는 숫자 단독 ($text는 숫자 토큰 인덱싱 안 함)
                query["name"] = {"$regex": re.escape(search), "$options": "i"}
            else:
                query["$text"] = {"$search": search}

        # count + find 를 $facet 한 번으로 합쳐 MongoDB 왕복 1회 절감
        _SORT = {
            "product_id_asc":  {"product_id": 1},
            "product_id_desc": {"product_id": -1},
            "name_asc":        {"name": 1},
            "name_desc":       {"name": -1},
            "category_asc":    {"category_name": 1},
            "category_desc":   {"category_name": -1},
            "price_asc":       {"sale_price": 1},
            "price_desc":      {"sale_price": -1},
            "discount_asc":    {"discount_rate": 1},
            "discount_desc":   {"discount_rate": -1},
            "stock_asc":       {"stock": 1},
            "stock_desc":      {"stock": -1},
        }

        if search and not sort_by and "$text" in query:
            # $text 검색일 때만 textScore 정렬 ($regex/$exact에는 사용 불가)
            sort_stage = {
                "_add": {"$addFields": {"_score": {"$meta": "textScore"}}},
                "_sort": {"$sort": {"_score": -1}},
            }
        elif not sort_by:
            sort_by = "rank"
            if target == "best":
                rank_expr = {"$ifNull": ["$best_rank", 999999]}
            elif target == "sales":
                rank_expr = {"$ifNull": ["$sales_rank", 999999]}
            else:
                rank_expr = {"$min": [
                    {"$ifNull": ["$best_rank",  999999]},
                    {"$ifNull": ["$sales_rank", 999999]},
                ]}
            sort_stage = {
                "_add": {"$addFields": {"_rank_sort": rank_expr}},
                "_sort": {"$sort": {"_rank_sort": 1}},
            }
        elif sort_by == "rank":
            # sort_by 미지정 시 인기순 기본 적용
            if target == "best":
                rank_expr = {"$ifNull": ["$best_rank", 999999]}
            elif target == "sales":
                rank_expr = {"$ifNull": ["$sales_rank", 999999]}
            else:
                # 전체 탭: best_rank / sales_rank 중 더 높은 순위(작은 숫자) 사용
                rank_expr = {"$min": [
                    {"$ifNull": ["$best_rank",  999999]},
                    {"$ifNull": ["$sales_rank", 999999]},
                ]}
            sort_stage = {
                "_add": {"$addFields": {"_rank_sort": rank_expr}},
                "_sort": {"$sort": {"_rank_sort": 1}},
            }
        elif sort_by in _SORT:
            sort_stage = {"$sort": _SORT[sort_by]}
        else:
            sort_stage = None

        pipeline = [
            {"$match": query},
            {"$project": {"detail_blocks": 0}},
        ]
        if sort_stage:
            if isinstance(sort_stage, dict) and "_add" in sort_stage:
                pipeline.append(sort_stage["_add"])
                pipeline.append(sort_stage["_sort"])
            else:
                pipeline.append(sort_stage)
        pipeline.append({"$facet": {
            "total":    [{"$count": "n"}],
            "products": [
                {"$skip": (page - 1) * page_size},
                {"$limit": page_size},
                {"$project": {"_id": 0, "_score": 0, "_rank_sort": 0}},
            ],
        }})

        col = get_collection()
        result = list(col.aggregate(pipeline))
        total = result[0]["total"][0]["n"] if result and result[0]["total"] else 0
        docs  = result[0]["products"] if result else []

        if not search:
            cache_set(cache_key, {"products": docs, "total": total})
        _log.info(f"목록 조회 - target={target} cat={cat_code} search='{search}' page={page} total={total}")

        return product_pb2.ListProductsResponse(
            products=[_doc_to_summary(d) for d in docs],
            total=total,
            page=page,
            page_size=page_size,
        )

    def ListCategories(self, request, context):
        target = request.target  # 빈 문자열이면 전체

        cat_col = get_categories_collection()
        cat_query = {"target": target} if target else {}
        docs = list(cat_col.find(cat_query, {"_id": 0, "code": 1, "name": 1, "count": 1}).sort("name", 1))

        # 전체 탭은 best+sales 카테고리가 중복될 수 있으므로 code 기준 중복 제거
        seen = set()
        categories = []
        for d in docs:
            if d["code"] not in seen:
                seen.add(d["code"])
                categories.append(product_pb2.Category(code=d["code"], name=d["name"], count=d.get("count", 0)))

        _log.info(f"카테고리 목록 조회 - target='{target}' count={len(categories)}")
        return product_pb2.ListCategoriesResponse(categories=categories)

    def GetProduct(self, request, context):
        product_id = request.product_id
        col = get_collection()
        doc = col.find_one({"product_id": product_id}, {"_id": 0})
        if not doc:
            _log.info(f"상품 없음 - product_id={product_id}")
            return product_pb2.GetProductResponse(found=False)
        _log.info(f"상품 조회 - product_id={product_id}")
        return product_pb2.GetProductResponse(product=_doc_to_detail(doc), found=True)

    def UpdateStock(self, request, context):
        col = get_collection()
        result = col.update_one(
            {"product_id": request.product_id},
            {"$set": {"stock": request.stock}},
        )
        # 해당 상품 캐시 무효화
        from db import cache_delete_pattern
        cache_delete_pattern(f"list:*")
        _log.info(f"재고 수정 - product_id={request.product_id} stock={request.stock}")
        return product_pb2.UpdateStockResponse(success=result.modified_count > 0)

    def DeleteProduct(self, request, context):
        col = get_collection()
        result = col.delete_one({"product_id": request.product_id})
        from db import cache_delete_pattern
        cache_delete_pattern(f"list:*")
        _log.info(f"상품 삭제 - product_id={request.product_id}")
        return product_pb2.DeleteProductResponse(success=result.deleted_count > 0)

    def DecrementStock(self, request, context):
        col = get_collection()
        # 재고 부족 시 실패 반환
        result = col.find_one_and_update(
            {"product_id": request.product_id, "stock": {"$gte": request.quantity}},
            {"$inc": {"stock": -request.quantity}},
            return_document=True,
            projection={"stock": 1},
        )
        if not result:
            _log.info(f"재고 부족 - product_id={request.product_id} quantity={request.quantity}")
            return product_pb2.DecrementStockResponse(success=False, stock_after=0)
        from db import cache_delete_pattern
        cache_delete_pattern(f"list:*")
        _log.info(f"재고 감소 - product_id={request.product_id} -{request.quantity} → {result['stock']}")
        return product_pb2.DecrementStockResponse(success=True, stock_after=result["stock"])

    def IncrementStock(self, request, context):
        col = get_collection()
        result = col.find_one_and_update(
            {"product_id": request.product_id},
            {"$inc": {"stock": request.quantity}},
            return_document=True,
            projection={"stock": 1},
        )
        if not result:
            return product_pb2.IncrementStockResponse(success=False, stock_after=0)
        from db import cache_delete_pattern
        cache_delete_pattern(f"list:*")
        _log.info(f"재고 복구 - product_id={request.product_id} +{request.quantity} → {result['stock']}")
        return product_pb2.IncrementStockResponse(success=True, stock_after=result["stock"])
