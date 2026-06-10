from fastapi import APIRouter, Request
from pydantic import BaseModel
import auth_pb2
from grpc_client import get_auth_stub
from auth_middleware import get_current_user

router = APIRouter()


@router.get("")
def get_me(request: Request):
    user = get_current_user(request)
    stub = get_auth_stub()
    res  = stub.GetMe(auth_pb2.GetMeRequest(user_id=user["user_id"]))
    return {
        "id": res.id, "username": res.username, "email": res.email,
        "points": res.points, "is_admin": res.is_admin, "created_at": res.created_at,
    }


@router.get("/points")
def get_points(request: Request):
    user = get_current_user(request)
    stub = get_auth_stub()
    res  = stub.GetPoints(auth_pb2.GetPointsRequest(user_id=user["user_id"]))
    return {"points": res.points}


@router.get("/orders")
def get_orders(request: Request):
    user = get_current_user(request)
    stub = get_auth_stub()
    res  = stub.GetOrders(auth_pb2.GetOrdersRequest(user_id=user["user_id"]))
    return {"orders": [_order_to_dict(o) for o in res.orders]}


@router.get("/addresses")
def get_addresses(request: Request):
    user = get_current_user(request)
    stub = get_auth_stub()
    res  = stub.GetAddresses(auth_pb2.GetAddressesRequest(user_id=user["user_id"]))
    return {"addresses": [_addr_to_dict(a) for a in res.addresses]}


class AddressBody(BaseModel):
    recipient:      str
    phone:          str
    zipcode:        str
    address:        str
    address_detail: str = ""


@router.post("/addresses")
def add_address(body: AddressBody, request: Request):
    user = get_current_user(request)
    stub = get_auth_stub()
    res  = stub.AddAddress(auth_pb2.AddAddressRequest(
        user_id=user["user_id"], recipient=body.recipient, phone=body.phone,
        zipcode=body.zipcode, address=body.address, address_detail=body.address_detail,
    ))
    return {"success": res.success, "address_id": res.address_id}


@router.put("/addresses/{address_id}/default")
def set_default_address(address_id: int, request: Request):
    user = get_current_user(request)
    stub = get_auth_stub()
    stub.SetDefaultAddress(auth_pb2.SetDefaultAddressRequest(
        user_id=user["user_id"], address_id=address_id,
    ))
    return {"success": True}


@router.delete("")
def withdraw_user(request: Request):
    """회원 탈퇴 — 사용자 본인이 직접 요청, 재활성화 불가"""
    user = get_current_user(request)
    stub = get_auth_stub()
    res  = stub.WithdrawUser(auth_pb2.WithdrawUserRequest(user_id=user["user_id"]))
    if not res.success:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=res.message)
    return {"success": True}


@router.delete("/addresses/{address_id}")
def delete_address(address_id: int, request: Request):
    user = get_current_user(request)
    stub = get_auth_stub()
    stub.DeleteAddress(auth_pb2.DeleteAddressRequest(
        user_id=user["user_id"], address_id=address_id,
    ))
    return {"success": True}


def _addr_to_dict(a) -> dict:
    return {
        "id": a.id, "recipient": a.recipient, "phone": a.phone,
        "zipcode": a.zipcode, "address": a.address,
        "address_detail": a.address_detail, "is_default": a.is_default,
    }


def _order_to_dict(o) -> dict:
    return {
        "id": o.id, "product_id": o.product_id, "product_name": o.product_name,
        "product_image": o.product_image, "quantity": o.quantity,
        "unit_price": o.unit_price, "total_price": o.total_price,
        "status": o.status, "created_at": o.created_at,
        "shipping_address": o.shipping_address,
    }
