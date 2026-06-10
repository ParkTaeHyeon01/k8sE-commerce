from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import auth_pb2
import product_pb2
from grpc_client import get_auth_stub, get_product_stub
from auth_middleware import get_current_admin

router = APIRouter()


# ── 상품 관리 ──────────────────────────────────────────────

@router.get("/products")
def admin_list_products(request: Request, page: int = 1, page_size: int = 50):
    get_current_admin(request)
    stub = get_product_stub()
    res  = stub.ListProducts(product_pb2.ListProductsRequest(page=page, page_size=page_size))
    return {
        "products": [_product_to_dict(p) for p in res.products],
        "total": res.total, "page": res.page, "page_size": res.page_size,
    }


class UpdateStockBody(BaseModel):
    stock: int


@router.put("/products/{product_id}/stock")
def admin_update_stock(product_id: str, body: UpdateStockBody, request: Request):
    get_current_admin(request)
    if body.stock < 0:
        raise HTTPException(status_code=400, detail="재고는 0 이상이어야 합니다.")
    stub = get_product_stub()
    res  = stub.UpdateStock(product_pb2.UpdateStockRequest(product_id=product_id, stock=body.stock))
    return {"success": res.success}


@router.delete("/products/{product_id}")
def admin_delete_product(product_id: str, request: Request):
    get_current_admin(request)
    stub = get_product_stub()
    res  = stub.DeleteProduct(product_pb2.DeleteProductRequest(product_id=product_id))
    return {"success": res.success}


# ── 회원 관리 ──────────────────────────────────────────────

@router.get("/users")
def admin_list_users(request: Request):
    get_current_admin(request)
    stub = get_auth_stub()
    res  = stub.AdminListUsers(auth_pb2.AdminListUsersRequest())
    return {"users": [_user_to_dict(u) for u in res.users]}


class AdjustPointsBody(BaseModel):
    amount:      int
    description: str = ""


@router.put("/users/{user_id}/points")
def admin_adjust_points(user_id: int, body: AdjustPointsBody, request: Request):
    get_current_admin(request)
    stub = get_auth_stub()
    res  = stub.AdminAdjustPoints(auth_pb2.AdminAdjustPointsRequest(
        user_id=user_id, amount=body.amount, description=body.description,
    ))
    return {"success": res.success, "points_after": res.points_after}


class SetAdminBody(BaseModel):
    is_admin: bool


@router.put("/users/{user_id}/admin")
def admin_set_admin(user_id: int, body: SetAdminBody, request: Request):
    get_current_admin(request)
    stub = get_auth_stub()
    res  = stub.AdminSetAdmin(auth_pb2.AdminSetAdminRequest(user_id=user_id, is_admin=body.is_admin))
    return {"success": res.success}


@router.delete("/users/{user_id}")
def admin_delete_user(user_id: int, request: Request):
    get_current_admin(request)
    stub = get_auth_stub()
    res  = stub.AdminDeleteUser(auth_pb2.AdminDeleteUserRequest(user_id=user_id))
    return {"success": res.success}


@router.post("/users/{user_id}/restore")
def admin_restore_user(user_id: int, request: Request):
    get_current_admin(request)
    stub = get_auth_stub()
    res  = stub.AdminRestoreUser(auth_pb2.AdminRestoreUserRequest(user_id=user_id))
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return {"success": res.success}


# ── 주문 관리 ──────────────────────────────────────────────

@router.get("/orders")
def admin_get_all_orders(request: Request):
    get_current_admin(request)
    stub = get_auth_stub()
    res  = stub.AdminGetAllOrders(auth_pb2.AdminGetAllOrdersRequest())
    return {"orders": [_order_to_dict(o) for o in res.orders]}


# ── 변환 헬퍼 ──────────────────────────────────────────────

def _product_to_dict(p) -> dict:
    return {
        "product_id": p.product_id, "name": p.name,
        "sale_price": p.sale_price, "discount_rate": p.discount_rate,
        "category_name": p.category_name, "stock": p.stock,
        "image_url": p.image_url,
    }


def _user_to_dict(u) -> dict:
    return {
        "id": u.id, "username": u.username, "email": u.email,
        "points": u.points, "is_admin": u.is_admin,
        "is_active": u.is_active, "created_at": u.created_at,
        "deactivated_by": u.deactivated_by,
    }


def _order_to_dict(o) -> dict:
    return {
        "id": o.id, "user_id": o.user_id, "product_id": o.product_id,
        "product_name": o.product_name, "product_image": o.product_image,
        "quantity": o.quantity, "unit_price": o.unit_price,
        "total_price": o.total_price, "status": o.status, "created_at": o.created_at,
    }
