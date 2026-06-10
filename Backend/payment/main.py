import os
from concurrent import futures
from pathlib import Path

import grpc
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

import payment_pb2_grpc
from logger import get_logger
from servicer import PaymentServicer

_GRPC_PORT = os.environ.get("PAYMENT_GRPC_PORT", "50053")
_log = get_logger("payment-grpc")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    payment_pb2_grpc.add_PaymentServiceServicer_to_server(PaymentServicer(), server)
    server.add_insecure_port(f"[::]:{_GRPC_PORT}")
    server.start()
    _log.info(f"payment gRPC 서버 시작 - 포트 {_GRPC_PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
