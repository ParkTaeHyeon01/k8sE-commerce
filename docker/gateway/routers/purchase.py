from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import grpc
import payment_pb2
from grpc_client import get_payment_stub
from auth_middleware import get_current_user
from routers.cart import _get_cart, _get_redis, _cart_key

router = APIRouter()


class CheckoutBody(BaseModel):
    address_id: int = 0


@router.post("/cart/checkout")
def checkout(body: CheckoutBody, request: Request):
    user    = get_current_user(request)
    user_id = user["user_id"]
    cart    = _get_cart(user_id)
    if not cart:
        raise HTTPException(status_code=400, detail="장바구니가 비어 있습니다.")

    items = [payment_pb2.CartItem(product_id=pid, quantity=qty) for pid, qty in cart.items()]
    try:
        res = get_payment_stub().Checkout(payment_pb2.CheckoutRequest(
            user_id=user_id, items=items, address_id=body.address_id,
        ))
    except grpc.RpcError as e:
        raise HTTPException(status_code=502, detail=f"결제 서비스 오류: {e.code().name}")

    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)

    # 결제 성공 시 장바구니 비우기 (Redis는 gateway에서 관리)
    _get_redis().delete(_cart_key(user_id))

    return {
        "success":      True,
        "total":        res.total,
        "points_after": res.points_after,
        "items_count":  res.items_count,
    }


@router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int, request: Request):
    user = get_current_user(request)
    try:
        res = get_payment_stub().CancelOrder(payment_pb2.CancelOrderRequest(
            order_id=order_id, user_id=user["user_id"],
        ))
    except grpc.RpcError as e:
        raise HTTPException(status_code=502, detail=f"결제 서비스 오류: {e.code().name}")

    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)

    return {"success": True, "refund_amount": res.refund_amount}
