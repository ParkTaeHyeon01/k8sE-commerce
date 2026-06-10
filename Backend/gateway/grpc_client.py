import os
import grpc
import product_pb2_grpc
import auth_pb2_grpc

_PRODUCT_ADDR = os.environ.get("PRODUCT_GRPC_ADDR", "localhost:50051")
_AUTH_ADDR    = os.environ.get("AUTH_GRPC_ADDR",    "localhost:50052")

_product_channel: grpc.Channel | None = None
_auth_channel:    grpc.Channel | None = None


def get_product_stub() -> product_pb2_grpc.ProductServiceStub:
    global _product_channel
    if _product_channel is None:
        _product_channel = grpc.insecure_channel(_PRODUCT_ADDR)
    return product_pb2_grpc.ProductServiceStub(_product_channel)


def get_auth_stub() -> auth_pb2_grpc.AuthServiceStub:
    global _auth_channel
    if _auth_channel is None:
        _auth_channel = grpc.insecure_channel(_AUTH_ADDR)
    return auth_pb2_grpc.AuthServiceStub(_auth_channel)
