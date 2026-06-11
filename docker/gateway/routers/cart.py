import json
import os
import redis
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from auth_middleware import get_current_user
from grpc_client import get_product_stub
import product_pb2

router = APIRouter()

_REDIS_WRITE_URL = os.environ.get("REDIS_WRITE_URL", "redis://localhost:6379/0")
_REDIS_READ_URL  = os.environ.get("REDIS_READ_URL",  "redis://localhost:6379/0")
_CART_TTL        = 60 * 60 * 24 * 7  # 7일

_redis_write_client = None
_redis_read_client  = None


def _get_write_redis():
    global _redis_write_client
    if _redis_write_client is None:
        _redis_write_client = redis.from_url(_REDIS_WRITE_URL, decode_responses=True, protocol=2)
    return _redis_write_client


def _get_read_redis():
    global _redis_read_client
    if _redis_read_client is None:
        _redis_read_client = redis.from_url(_REDIS_READ_URL, decode_responses=True, protocol=2)
    return _redis_read_client


def _cart_key(user_id: int) -> str:
    return f"cart:{user_id}"


def _get_cart(user_id: int) -> dict:
    raw = _get_read_redis().get(_cart_key(user_id))
    return json.loads(raw) if raw else {}


def _save_cart(user_id: int, cart: dict):
    _get_write_redis().setex(_cart_key(user_id), _CART_TTL, json.dumps(cart))


@router.get("")
def get_cart(request: Request):
    user = get_current_user(request)
    cart = _get_cart(user["user_id"])
    # 상품 정보 조회
    items = []
    stub = get_product_stub()
    for product_id, quantity in cart.items():
        res = stub.GetProduct(product_pb2.GetProductRequest(product_id=product_id))
        if res.found:
            p = res.product
            items.append({
                "product_id":    p.product_id,
                "name":          p.name,
                "image_url":     p.image_url,
                "sale_price":    p.sale_price,
                "stock":         p.stock,
                "quantity":      quantity,
                "total_price":   p.sale_price * quantity,
            })
    total = sum(i["total_price"] for i in items)
    return {"items": items, "total": total}


class AddToCartBody(BaseModel):
    product_id: str
    quantity:   int = 1


@router.post("")
def add_to_cart(body: AddToCartBody, request: Request):
    user = get_current_user(request)
    if body.quantity < 1:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")

    # 재고 확인
    stub = get_product_stub()
    res  = stub.GetProduct(product_pb2.GetProductRequest(product_id=body.product_id))
    if not res.found:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    cart = _get_cart(user["user_id"])
    current_qty  = cart.get(body.product_id, 0)
    new_qty      = current_qty + body.quantity
    # 재고 초과 방지
    new_qty = min(new_qty, res.product.stock)
    if new_qty < 1:
        raise HTTPException(status_code=400, detail="재고가 없습니다.")

    cart[body.product_id] = new_qty
    _save_cart(user["user_id"], cart)
    return {"success": True, "quantity": new_qty}


class UpdateCartBody(BaseModel):
    quantity: int


@router.put("/{product_id}")
def update_cart(product_id: str, body: UpdateCartBody, request: Request):
    user = get_current_user(request)
    cart = _get_cart(user["user_id"])
    if product_id not in cart:
        raise HTTPException(status_code=404, detail="장바구니에 없는 상품입니다.")
    if body.quantity < 1:
        del cart[product_id]
    else:
        # 재고 확인
        stub = get_product_stub()
        res  = stub.GetProduct(product_pb2.GetProductRequest(product_id=product_id))
        if res.found:
            body.quantity = min(body.quantity, res.product.stock)
        cart[product_id] = body.quantity
    _save_cart(user["user_id"], cart)
    return {"success": True}


@router.delete("/{product_id}")
def remove_from_cart(product_id: str, request: Request):
    user = get_current_user(request)
    cart = _get_cart(user["user_id"])
    cart.pop(product_id, None)
    _save_cart(user["user_id"], cart)
    return {"success": True}


@router.delete("")
def clear_cart(request: Request):
    user = get_current_user(request)
    _get_write_redis().delete(_cart_key(user["user_id"]))
    return {"success": True}
