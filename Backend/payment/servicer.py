import os
import grpc
import auth_pb2
import auth_pb2_grpc
import product_pb2
import product_pb2_grpc
import payment_pb2
import payment_pb2_grpc
from logger import get_logger

_log = get_logger("payment-grpc")

_AUTH_ADDR    = os.environ.get("AUTH_GRPC_ADDR",    "localhost:50052")
_PRODUCT_ADDR = os.environ.get("PRODUCT_GRPC_ADDR", "localhost:50051")


def _auth_stub():
    return auth_pb2_grpc.AuthServiceStub(grpc.insecure_channel(_AUTH_ADDR))

def _product_stub():
    return product_pb2_grpc.ProductServiceStub(grpc.insecure_channel(_PRODUCT_ADDR))


class PaymentServicer(payment_pb2_grpc.PaymentServiceServicer):

    def Checkout(self, request, context):
        user_id    = request.user_id
        address_id = request.address_id
        cart_items = {item.product_id: item.quantity for item in request.items}

        auth_stub    = _auth_stub()
        product_stub = _product_stub()

        # 배송지 주소 스냅샷
        shipping_address = ""
        if address_id > 0:
            addr_res = auth_stub.GetAddresses(auth_pb2.GetAddressesRequest(user_id=user_id))
            for addr in addr_res.addresses:
                if addr.id == address_id:
                    detail = f" {addr.address_detail}" if addr.address_detail else ""
                    shipping_address = f"[{addr.zipcode}] {addr.address}{detail} ({addr.recipient} {addr.phone})"
                    break

        # 상품 정보 수집 및 총액 계산
        items = []
        total = 0
        for product_id, quantity in cart_items.items():
            res = product_stub.GetProduct(product_pb2.GetProductRequest(product_id=product_id))
            if not res.found:
                return payment_pb2.CheckoutResponse(success=False, message=f"상품 {product_id}을 찾을 수 없습니다.")
            p = res.product
            if p.stock < quantity:
                return payment_pb2.CheckoutResponse(success=False, message=f"'{p.name}' 재고가 부족합니다. (재고: {p.stock})")
            item_total = p.sale_price * quantity
            total += item_total
            items.append({"product": p, "quantity": quantity, "total": item_total})

        # 포인트 차감
        spend_res = auth_stub.SpendPoints(auth_pb2.SpendPointsRequest(
            user_id=user_id, amount=total, description=f"상품 구매 ({len(items)}건)",
        ))
        if not spend_res.success:
            return payment_pb2.CheckoutResponse(success=False, message=spend_res.message)

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
            _log.error(f"결제 실패 - user_id={user_id} error={e}")
            return payment_pb2.CheckoutResponse(success=False, message=str(e))

        _log.info(f"결제 완료 - user_id={user_id} total={total} items={len(items)}")
        return payment_pb2.CheckoutResponse(
            success=True, total=total,
            points_after=spend_res.points_after, items_count=len(items),
        )

    def CancelOrder(self, request, context):
        auth_stub    = _auth_stub()
        product_stub = _product_stub()

        res = auth_stub.CancelOrder(auth_pb2.CancelOrderRequest(
            order_id=request.order_id, user_id=request.user_id,
        ))
        if not res.success:
            return payment_pb2.CancelOrderResponse(success=False, message=res.message)

        # 재고 복구
        if res.product_id and res.quantity > 0:
            product_stub.IncrementStock(product_pb2.IncrementStockRequest(
                product_id=res.product_id, quantity=res.quantity,
            ))

        _log.info(f"주문 취소 완료 - order_id={request.order_id} refund={res.refund_amount}")
        return payment_pb2.CancelOrderResponse(
            success=True, refund_amount=res.refund_amount,
        )
