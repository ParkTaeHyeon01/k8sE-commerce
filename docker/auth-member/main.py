import logging
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")
from concurrent import futures

import grpc
import auth_pb2_grpc
from db import init_db, seed_admin
from servicer import AuthServicer

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("auth-member")

_PORT = os.environ.get("AUTH_GRPC_PORT", "50052")


def serve():
    init_db()
    seed_admin()
    log.info("DB 초기화 및 관리자 시드 완료")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServicer(), server)
    server.add_insecure_port(f"[::]:{_PORT}")
    server.start()
    log.info(f"auth-member gRPC 서버 시작 - port {_PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
