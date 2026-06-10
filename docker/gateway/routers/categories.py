# 카테고리 목록 REST 엔드포인트
# GET /categories?target=best|sales → ListCategories gRPC
from fastapi import APIRouter, Query
from google.protobuf.json_format import MessageToDict
import product_pb2
from grpc_client import get_product_stub

router = APIRouter()


@router.get("")
def list_categories(
    target: str = Query(default="best", description="best | sales"),
):
    stub = get_product_stub()
    resp = stub.ListCategories(product_pb2.ListCategoriesRequest(target=target))
    return MessageToDict(resp, preserving_proto_field_name=True)
