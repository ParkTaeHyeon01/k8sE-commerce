from fastapi import APIRouter
from pydantic import BaseModel
import auth_pb2
from grpc_client import get_auth_stub

router = APIRouter()


class RegisterBody(BaseModel):
    username: str
    email:    str
    password: str


class LoginBody(BaseModel):
    email:    str
    password: str


@router.post("/register")
def register(body: RegisterBody):
    stub = get_auth_stub()
    res  = stub.Register(auth_pb2.RegisterRequest(
        username=body.username, email=body.email, password=body.password,
    ))
    if not res.success:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=res.message)
    return {"token": res.token, "message": res.message}


@router.post("/login")
def login(body: LoginBody):
    stub = get_auth_stub()
    res  = stub.Login(auth_pb2.LoginRequest(email=body.email, password=body.password))
    if not res.success:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail=res.message)
    return {"token": res.token, "message": res.message}
