# product gRPC 서버 진입점
# 흐름: 환경변수 로드 -> gRPC 서버 시작 -> ListProducts / GetProduct 요청 처리
import os
import threading
from concurrent import futures
from pathlib import Path

import grpc
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

import product_pb2
import product_pb2_grpc
from logger import get_logger
from servicer import ProductServicer

_GRPC_PORT = os.environ.get("PRODUCT_GRPC_PORT", "50051")

_log = get_logger("product-grpc")


def _prewarm(svc: ProductServicer) -> None:
    """서버 시작 후 자주 쓰이는 쿼리를 미리 캐시에 올린다."""
    targets = ["", "best", "sales"]
    count = 0
    for target in targets:
        try:
            svc.ListProducts(
                product_pb2.ListProductsRequest(target=target, page=1, page_size=20),
                context=None,
            )
            count += 1
        except Exception as e:
            _log.error(f"pre-warm 실패 - target={target}: {e}")
    _log.info(f"캐시 pre-warm 완료 - {count}/{len(targets)}개 쿼리")


def serve():
    svc = ProductServicer()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    product_pb2_grpc.add_ProductServiceServicer_to_server(svc, server)
    server.add_insecure_port(f"[::]:{_GRPC_PORT}")
    server.start()
    _log.info(f"product gRPC 서버 시작 - 포트 {_GRPC_PORT}")
    # 백그라운드에서 캐시 pre-warm (서버 응답에 영향 없음)
    threading.Thread(target=_prewarm, args=(svc,), daemon=True).start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
