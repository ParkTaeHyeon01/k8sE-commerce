import os
from concurrent import futures

import grpc
import product_pb2
import product_pb2_grpc
from pymongo import MongoClient

_MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
_MONGODB_DB  = os.environ.get("MONGODB_DB", "ecommerce")

_client = MongoClient(_MONGODB_URI)
_col    = _client[_MONGODB_DB]["products"]


def _doc_to_summary(doc):
    return product_pb2.ProductSummary(
        product_id=doc.get("product_id", ""),
        name=doc.get("name", ""),
        sale_price=doc.get("sale_price") or 0,
        original_price=doc.get("original_price") or 0,
        discount_rate=doc.get("discount_rate") or 0,
        image_url=doc.get("image_url") or "",
        category_name=doc.get("category_name") or "",
        stock=int(doc.get("stock")) if doc.get("stock") is not None else 0,
    )


class BenchmarkServicer(product_pb2_grpc.ProductServiceServicer):
    def ListProducts(self, request, context):
        target    = request.target or "best"
        page      = max(request.page, 1)
        page_size = request.page_size if request.page_size > 0 else 20

        pipeline = [
            {"$match": {"status": "ready", "targets": target}},
            {"$project": {"detail_blocks": 0, "ngrams": 0}},
            {"$facet": {
                "total":    [{"$count": "n"}],
                "products": [
                    {"$skip":  (page - 1) * page_size},
                    {"$limit": page_size},
                    {"$project": {"_id": 0}},
                ],
            }},
        ]
        result = list(_col.aggregate(pipeline))
        total  = result[0]["total"][0]["n"] if result and result[0]["total"] else 0
        docs   = result[0]["products"] if result else []

        return product_pb2.ListProductsResponse(
            products=[_doc_to_summary(d) for d in docs],
            total=total,
            page=page,
            page_size=page_size,
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    product_pb2_grpc.add_ProductServiceServicer_to_server(BenchmarkServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("벤치마크 gRPC 서버 시작 - 포트 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
