"""
in-memory gRPC 서버 — 시나리오 2 (순수 직렬화/전송 속도 비교용)
실제 DB 없이 고정 데이터 20개를 protobuf로 반환
포트 50055
"""
import sys
import os
from concurrent import futures

import grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Backend", "product"))

import product_pb2
import product_pb2_grpc

_PRODUCTS = [
    product_pb2.ProductSummary(
        product_id=f"test-{i:04d}",
        name=f"테스트 상품 {i}",
        sale_price=10000 + i * 100,
        original_price=15000 + i * 100,
        discount_rate=30 + (i % 10),
        image_url="https://example.com/image.jpg",
        category_code="100",
        category_name="식품",
        targets=["best"],
        delivery_info="새벽배송",
        stock=100,
    )
    for i in range(20)
]


class InMemoryProductServicer(product_pb2_grpc.ProductServiceServicer):
    def ListProducts(self, request, context):
        return product_pb2.ListProductsResponse(
            products=_PRODUCTS,
            total=len(_PRODUCTS),
            page=1,
            page_size=20,
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    product_pb2_grpc.add_ProductServiceServicer_to_server(InMemoryProductServicer(), server)
    server.add_insecure_port("[::]:50055")
    server.start()
    print("in-memory gRPC 서버 시작 - 포트 50055")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
