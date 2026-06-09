# product gRPC 서버 진입점
# 흐름: 환경변수 로드 -> gRPC 서버 시작 -> ListProducts / GetProduct 요청 처리
import os
from concurrent import futures
from pathlib import Path

import grpc
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

import product_pb2_grpc
from logger import get_logger
from servicer import ProductServicer

_GRPC_PORT = os.environ.get("PRODUCT_GRPC_PORT", "50051")

_log = get_logger("product-grpc")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    product_pb2_grpc.add_ProductServiceServicer_to_server(ProductServicer(), server)
    server.add_insecure_port(f"[::]:{_GRPC_PORT}")
    server.start()
    _log.info(f"product gRPC 서버 시작 - 포트 {_GRPC_PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
