# gateway 진입점 - FastAPI REST 서버
# 흐름: 브라우저/프론트 REST 요청 → gRPC로 내부 서비스 호출 → JSON 응답 반환
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import categories, products
from routers import auth, me, cart, purchase, admin

app = FastAPI(title="k8sE-commerce Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router,    prefix="/products",    tags=["products"])
app.include_router(categories.router,  prefix="/categories",  tags=["categories"])
app.include_router(auth.router,        prefix="/auth",        tags=["auth"])
app.include_router(me.router,          prefix="/me",          tags=["me"])
app.include_router(cart.router,        prefix="/cart",        tags=["cart"])
app.include_router(purchase.router,    tags=["purchase"])
app.include_router(admin.router,       prefix="/admin",       tags=["admin"])


@app.get("/health")
def health():
    return {"status": "ok"}
