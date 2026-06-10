import os
import datetime
import jwt
import bcrypt as _bcrypt

import auth_pb2
import auth_pb2_grpc
from db import get_conn

_JWT_SECRET = os.environ.get("JWT_SECRET", "changeme-secret")
_JWT_EXP_HOURS = 24


def _make_token(user_id: int, is_admin: bool) -> str:
    payload = {
        "user_id":  user_id,
        "is_admin": is_admin,
        "exp":      datetime.datetime.utcnow() + datetime.timedelta(hours=_JWT_EXP_HOURS),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm="HS256")


class AuthServicer(auth_pb2_grpc.AuthServiceServicer):

    # ── 인증 ────────────────────────────────────────────────

    def Register(self, request, context):
        username = request.username.strip()
        email    = request.email.strip().lower()
        password = request.password

        if not username or not email or not password:
            return auth_pb2.RegisterResponse(success=False, message="필수 항목을 입력해주세요.")
        if len(password) < 8:
            return auth_pb2.RegisterResponse(success=False, message="비밀번호는 8자 이상이어야 합니다.")

        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    return auth_pb2.RegisterResponse(success=False, message="이미 사용 중인 이메일입니다.")
                hashed = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
                cur.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, hashed),
                )
                user_id = cur.lastrowid
                # 가입 포인트 내역 기록
                cur.execute(
                    "INSERT INTO point_history (user_id, amount, description) VALUES (%s, %s, %s)",
                    (user_id, 100000, "회원가입 축하 포인트"),
                )
        finally:
            conn.close()

        token = _make_token(user_id, False)
        return auth_pb2.RegisterResponse(success=True, message="가입 완료", token=token)

    def Login(self, request, context):
        email    = request.email.strip().lower()
        password = request.password

        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, password_hash, is_admin, is_active, deactivated_by FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
        finally:
            conn.close()

        if not user:
            return auth_pb2.LoginResponse(success=False, message="이메일 또는 비밀번호가 올바르지 않습니다.")
        if not user["is_active"]:
            msg = "관리자에 의해 정지된 계정입니다." if user["deactivated_by"] == "admin" else "탈퇴한 계정입니다."
            return auth_pb2.LoginResponse(success=False, message=msg)
        if not _bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return auth_pb2.LoginResponse(success=False, message="이메일 또는 비밀번호가 올바르지 않습니다.")

        token = _make_token(user["id"], bool(user["is_admin"]))
        return auth_pb2.LoginResponse(success=True, message="로그인 성공", token=token)

    def GetMe(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, email, points, is_admin, created_at FROM users WHERE id = %s AND is_active = 1",
                    (request.user_id,),
                )
                user = cur.fetchone()
        finally:
            conn.close()

        if not user:
            return auth_pb2.GetMeResponse()
        return auth_pb2.GetMeResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            points=user["points"],
            is_admin=bool(user["is_admin"]),
            created_at=str(user["created_at"]),
        )

    # ── 포인트 ──────────────────────────────────────────────

    def GetPoints(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT points FROM users WHERE id = %s", (request.user_id,))
                row = cur.fetchone()
        finally:
            conn.close()
        return auth_pb2.GetPointsResponse(points=row["points"] if row else 0)

    def SpendPoints(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT points FROM users WHERE id = %s AND is_active = 1 FOR UPDATE", (request.user_id,))
                row = cur.fetchone()
                if not row:
                    return auth_pb2.SpendPointsResponse(success=False, message="사용자를 찾을 수 없습니다.")
                if row["points"] < request.amount:
                    return auth_pb2.SpendPointsResponse(success=False, message="포인트가 부족합니다.")
                cur.execute("UPDATE users SET points = points - %s WHERE id = %s", (request.amount, request.user_id))
                cur.execute(
                    "INSERT INTO point_history (user_id, amount, description) VALUES (%s, %s, %s)",
                    (request.user_id, -request.amount, request.description),
                )
                points_after = row["points"] - request.amount
        finally:
            conn.close()
        return auth_pb2.SpendPointsResponse(success=True, message="차감 완료", points_after=points_after)

    def RefundPoints(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET points = points + %s WHERE id = %s", (request.amount, request.user_id))
                cur.execute(
                    "INSERT INTO point_history (user_id, amount, description) VALUES (%s, %s, %s)",
                    (request.user_id, request.amount, request.description),
                )
                cur.execute("SELECT points FROM users WHERE id = %s", (request.user_id,))
                row = cur.fetchone()
        finally:
            conn.close()
        return auth_pb2.RefundPointsResponse(success=True, points_after=row["points"] if row else 0)

    # ── 배송지 ──────────────────────────────────────────────

    def AddAddress(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                # 첫 번째 배송지면 기본으로 설정
                cur.execute("SELECT COUNT(*) as cnt FROM shipping_addresses WHERE user_id = %s", (request.user_id,))
                is_first = cur.fetchone()["cnt"] == 0
                cur.execute(
                    "INSERT INTO shipping_addresses (user_id, recipient, phone, zipcode, address, address_detail, is_default) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (request.user_id, request.recipient, request.phone, request.zipcode, request.address, request.address_detail, 1 if is_first else 0),
                )
                addr_id = cur.lastrowid
        finally:
            conn.close()
        return auth_pb2.AddAddressResponse(success=True, address_id=addr_id)

    def GetAddresses(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, recipient, phone, zipcode, address, address_detail, is_default FROM shipping_addresses WHERE user_id = %s ORDER BY is_default DESC, id ASC",
                    (request.user_id,),
                )
                rows = cur.fetchall()
        finally:
            conn.close()
        addresses = [
            auth_pb2.Address(
                id=r["id"], recipient=r["recipient"], phone=r["phone"],
                zipcode=r["zipcode"], address=r["address"],
                address_detail=r["address_detail"], is_default=bool(r["is_default"]),
            ) for r in rows
        ]
        return auth_pb2.GetAddressesResponse(addresses=addresses)

    def SetDefaultAddress(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE shipping_addresses SET is_default = 0 WHERE user_id = %s", (request.user_id,))
                cur.execute(
                    "UPDATE shipping_addresses SET is_default = 1 WHERE id = %s AND user_id = %s",
                    (request.address_id, request.user_id),
                )
        finally:
            conn.close()
        return auth_pb2.SetDefaultAddressResponse(success=True)

    def DeleteAddress(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM shipping_addresses WHERE id = %s AND user_id = %s",
                    (request.address_id, request.user_id),
                )
        finally:
            conn.close()
        return auth_pb2.DeleteAddressResponse(success=True)

    # ── 주문 ────────────────────────────────────────────────

    def CreateOrder(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO orders (user_id, product_id, product_name, product_image, quantity, unit_price, total_price, shipping_address) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (request.user_id, request.product_id, request.product_name, request.product_image, request.quantity, request.unit_price, request.total_price, request.shipping_address),
                )
                order_id = cur.lastrowid
        finally:
            conn.close()
        return auth_pb2.CreateOrderResponse(success=True, order_id=order_id)

    def GetOrders(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, user_id, product_id, product_name, product_image, quantity, unit_price, total_price, shipping_address, status, created_at FROM orders WHERE user_id = %s ORDER BY created_at DESC",
                    (request.user_id,),
                )
                rows = cur.fetchall()
        finally:
            conn.close()
        orders = [self._row_to_order(r) for r in rows]
        return auth_pb2.GetOrdersResponse(orders=orders)

    def CancelOrder(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, user_id, product_id, quantity, total_price, status FROM orders WHERE id = %s AND user_id = %s",
                    (request.order_id, request.user_id),
                )
                order = cur.fetchone()
                if not order:
                    return auth_pb2.CancelOrderResponse(success=False, message="주문을 찾을 수 없습니다.")
                if order["status"] == "cancelled":
                    return auth_pb2.CancelOrderResponse(success=False, message="이미 취소된 주문입니다.")
                cur.execute("UPDATE orders SET status = 'cancelled' WHERE id = %s", (request.order_id,))
                refund = order["total_price"]
                cur.execute("UPDATE users SET points = points + %s WHERE id = %s", (refund, order["user_id"]))
                cur.execute(
                    "INSERT INTO point_history (user_id, amount, description) VALUES (%s, %s, %s)",
                    (order["user_id"], refund, f"주문 취소 환불 (주문 #{request.order_id})"),
                )
        finally:
            conn.close()
        return auth_pb2.CancelOrderResponse(
            success=True, message="취소 완료",
            refund_amount=order["total_price"],
            product_id=order["product_id"],
            quantity=order["quantity"],
        )

    # ── 관리자 ──────────────────────────────────────────────

    def AdminListUsers(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, username, email, points, is_admin, is_active, deactivated_by, created_at FROM users ORDER BY id")
                rows = cur.fetchall()
        finally:
            conn.close()
        users = [
            auth_pb2.UserSummary(
                id=r["id"], username=r["username"], email=r["email"],
                points=r["points"], is_admin=bool(r["is_admin"]),
                is_active=bool(r["is_active"]), created_at=str(r["created_at"]),
                deactivated_by=r["deactivated_by"] or "",
            ) for r in rows
        ]
        return auth_pb2.AdminListUsersResponse(users=users)

    def AdminDeleteUser(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET is_active = 0, deactivated_by = 'admin' WHERE id = %s", (request.user_id,))
        finally:
            conn.close()
        return auth_pb2.AdminDeleteUserResponse(success=True)

    def AdminRestoreUser(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                # 관리자가 정지한 계정만 복구 가능 (사용자 탈퇴는 복구 불가)
                cur.execute(
                    "UPDATE users SET is_active = 1, deactivated_by = NULL WHERE id = %s AND deactivated_by = 'admin'",
                    (request.user_id,),
                )
                if cur.rowcount == 0:
                    return auth_pb2.AdminRestoreUserResponse(success=False, message="복구할 수 없는 계정입니다.")
        finally:
            conn.close()
        return auth_pb2.AdminRestoreUserResponse(success=True, message="계정이 복구되었습니다.")

    def WithdrawUser(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET is_active = 0, deactivated_by = 'user' WHERE id = %s AND is_active = 1",
                    (request.user_id,),
                )
                if cur.rowcount == 0:
                    return auth_pb2.WithdrawUserResponse(success=False, message="탈퇴 처리에 실패했습니다.")
        finally:
            conn.close()
        return auth_pb2.WithdrawUserResponse(success=True, message="탈퇴가 완료되었습니다.")

    def AdminAdjustPoints(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET points = points + %s WHERE id = %s", (request.amount, request.user_id))
                cur.execute(
                    "INSERT INTO point_history (user_id, amount, description) VALUES (%s, %s, %s)",
                    (request.user_id, request.amount, request.description or "관리자 포인트 조정"),
                )
                cur.execute("SELECT points FROM users WHERE id = %s", (request.user_id,))
                row = cur.fetchone()
        finally:
            conn.close()
        return auth_pb2.AdminAdjustPointsResponse(success=True, points_after=row["points"] if row else 0)

    def AdminSetAdmin(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET is_admin = %s WHERE id = %s", (1 if request.is_admin else 0, request.user_id))
        finally:
            conn.close()
        return auth_pb2.AdminSetAdminResponse(success=True)

    def AdminGetAllOrders(self, request, context):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, user_id, product_id, product_name, product_image, quantity, unit_price, total_price, shipping_address, status, created_at FROM orders ORDER BY created_at DESC"
                )
                rows = cur.fetchall()
        finally:
            conn.close()
        return auth_pb2.AdminGetAllOrdersResponse(orders=[self._row_to_order(r) for r in rows])

    def _row_to_order(self, r: dict) -> auth_pb2.Order:
        return auth_pb2.Order(
            id=r["id"], user_id=r["user_id"], product_id=r["product_id"],
            product_name=r["product_name"], product_image=r["product_image"],
            quantity=r["quantity"], unit_price=r["unit_price"],
            total_price=r["total_price"], status=r["status"],
            created_at=str(r["created_at"]),
            shipping_address=r.get("shipping_address") or "",
        )
