---
name: grpc-benchmark
description: gRPC vs REST 실측 벤치마크 결과 및 시각화 — benchmark/ 디렉터리에 서버/스크립트 완비
metadata: 
  node_type: memory
  type: project
  originSessionId: 4e827445-bbda-4abd-bc52-9e363a20499a
---

## 위치
`benchmark/` 디렉터리 (프로젝트 루트)

## 파일 구성
- `rest_server.py` — FastAPI REST 서버 (포트 50054), DB/in-memory 엔드포인트
- `inmemory_grpc_server.py` — in-memory gRPC 서버 (포트 50055), 고정 데이터 반환
- `run_bench.py` — 텍스트 벤치마크 결과 출력 (`python run_bench.py --n 100`)
- `visualize.py` — 선 그래프 시각화, PNG 저장 (`python visualize.py --n 100`)
- `requirements.txt` — fastapi, uvicorn, httpx, grpcio, pymongo

## 실행 순서
1. product gRPC 서버 (Backend/product/main.py, 포트 50051)
2. REST 서버: `python benchmark/rest_server.py`
3. in-memory gRPC 서버: `python benchmark/inmemory_grpc_server.py`
4. 측정: `python benchmark/run_bench.py --n 100`
5. 시각화: `python benchmark/visualize.py --n 100` → benchmark_result.png 생성

## 실측 결과 (2026-06-10, n=100, 로컬 PC)

| 항목 | gRPC | REST |
|---|---|---|
| 응답 시간 중앙값 (DB 포함) | 0.47ms | 4.23ms |
| 응답 시간 중앙값 (In-memory) | 0.31ms | 1.33ms |
| 페이로드 (DB) | 5.0 KB | 13.0 KB |
| 페이로드 (In-memory) | 2.1 KB | 5.3 KB |

- 발표용 요약: 중앙값 기준 **4~9배 빠름**, 페이로드 **2.5배 작음**
- DB 포함 시나리오에서 gRPC가 빠른 이유: product 서버에 Redis 캐시가 있어 0.5ms대 달성

## 주의사항
- MongoDB URI는 이 PC 기준 인증 없음 (`mongodb://localhost:27017/`)
- benchmark_result.png는 .gitignore에 추가 (실측 데이터라 환경마다 다름)

**Why**: gRPC 선택 근거를 발표에서 시각적으로 보여주기 위해 제작. [[docker-k8s-progress]]
