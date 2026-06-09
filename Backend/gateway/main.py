# gateway 진입점 - FastAPI REST 서버
# 흐름: 브라우저/프론트 REST 요청 → gRPC로 내부 서비스 호출 → JSON 응답 반환
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import products

app = FastAPI(title="k8sE-commerce Gateway")

# 프론트엔드(React dev server 포함)에서 호출 가능하도록 CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/products", tags=["products"])


@app.get("/health")
def health():
    return {"status": "ok"}
