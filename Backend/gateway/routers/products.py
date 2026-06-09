# 상품 관련 REST 엔드포인트
# GET /products          → ListProducts gRPC
# GET /products/{id}     → GetProduct gRPC
from fastapi import APIRouter, HTTPException, Query
from google.protobuf.json_format import MessageToDict
import product_pb2
from grpc_client import get_product_stub

router = APIRouter()


@router.get("")
def list_products(
    target: str = Query(default="", description="best | sales | (빈값=전체)"),
    category_code: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="", description="rank | price_asc | price_desc | discount_desc"),
):
    stub = get_product_stub()
    resp = stub.ListProducts(product_pb2.ListProductsRequest(
        target=target,
        category_code=category_code,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
    ))
    return MessageToDict(resp, preserving_proto_field_name=True)


@router.get("/{product_id}")
def get_product(product_id: str):
    stub = get_product_stub()
    resp = stub.GetProduct(product_pb2.GetProductRequest(product_id=product_id))
    if not resp.found:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    return MessageToDict(resp.product, preserving_proto_field_name=True)
