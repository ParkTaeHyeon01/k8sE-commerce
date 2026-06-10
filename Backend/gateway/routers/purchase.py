from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import auth_pb2
import product_pb2
from grpc_client import get_auth_stub, get_product_stub
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

    product_stub = get_product_stub()
    auth_stub    = get_auth_stub()

    # 배송지 주소 스냅샷
    shipping_address = ""
    if body.address_id > 0:
        addr_res = auth_stub.GetAddresses(auth_pb2.GetAddressesRequest(user_id=user_id))
        for addr in addr_res.addresses:
            if addr.id == body.address_id:
                detail = f" {addr.address_detail}" if addr.address_detail else ""
                shipping_address = f"[{addr.zipcode}] {addr.address}{detail} ({addr.recipient} {addr.phone})"
                break

    # 상품 정보 수집 및 총액 계산
    items = []
    total = 0
    for product_id, quantity in cart.items():
        res = product_stub.GetProduct(product_pb2.GetProductRequest(product_id=product_id))
        if not res.found:
            raise HTTPException(status_code=400, detail=f"상품 {product_id}을 찾을 수 없습니다.")
        p = res.product
        if p.stock < quantity:
            raise HTTPException(status_code=400, detail=f"'{p.name}' 재고가 부족합니다. (재고: {p.stock})")
        item_total = p.sale_price * quantity
        total += item_total
        items.append({"product": p, "quantity": quantity, "total": item_total})

    # 포인트 차감
    spend_res = auth_stub.SpendPoints(auth_pb2.SpendPointsRequest(
        user_id=user_id, amount=total, description=f"상품 구매 ({len(items)}건)",
    ))
    if not spend_res.success:
        raise HTTPException(status_code=400, detail=spend_res.message)

    # 재고 감소 + 주문 생성 (실패 시 롤백)
    decremented = []
    try:
        for item in items:
            p        = item["product"]
            quantity = item["quantity"]
            dec_res  = product_stub.DecrementStock(product_pb2.DecrementStockRequest(
                product_id=p.product_id, quantity=quantity,
            ))
            if not dec_res.success:
                raise Exception(f"'{p.name}' 재고 감소 실패")
            decremented.append({"product_id": p.product_id, "quantity": quantity})

            auth_stub.CreateOrder(auth_pb2.CreateOrderRequest(
                user_id=user_id, product_id=p.product_id, product_name=p.name,
                product_image=p.image_url, quantity=quantity,
                unit_price=p.sale_price, total_price=item["total"],
                shipping_address=shipping_address,
            ))
    except Exception as e:
        # 롤백: 포인트 환불 + 이미 감소된 재고 복구
        auth_stub.RefundPoints(auth_pb2.RefundPointsRequest(
            user_id=user_id, amount=total, description="구매 실패 환불",
        ))
        for d in decremented:
            product_stub.IncrementStock(product_pb2.IncrementStockRequest(
                product_id=d["product_id"], quantity=d["quantity"],
            ))
        raise HTTPException(status_code=500, detail=str(e))

    # 장바구니 비우기
    _get_redis().delete(_cart_key(user_id))

    return {
        "success":      True,
        "total":        total,
        "points_after": spend_res.points_after,
        "items_count":  len(items),
    }


@router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int, request: Request):
    user     = get_current_user(request)
    auth_stub = get_auth_stub()

    res = auth_stub.CancelOrder(auth_pb2.CancelOrderRequest(
        order_id=order_id, user_id=user["user_id"],
    ))
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)

    # 재고 복구
    if res.product_id and res.quantity > 0:
        product_stub = get_product_stub()
        product_stub.IncrementStock(product_pb2.IncrementStockRequest(
            product_id=res.product_id, quantity=res.quantity,
        ))

    return {"success": True, "refund_amount": res.refund_amount}
