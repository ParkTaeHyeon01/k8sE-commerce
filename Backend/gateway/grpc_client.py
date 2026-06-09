# gRPC 채널/스텁 싱글턴 - 프로세스 안에서 채널을 재사용한다
import os
import grpc
import product_pb2_grpc

_PRODUCT_ADDR = os.environ.get("PRODUCT_GRPC_ADDR", "localhost:50051")

_channel: grpc.Channel | None = None


def get_product_stub() -> product_pb2_grpc.ProductServiceStub:
    global _channel
    if _channel is None:
        _channel = grpc.insecure_channel(_PRODUCT_ADDR)
    return product_pb2_grpc.ProductServiceStub(_channel)
