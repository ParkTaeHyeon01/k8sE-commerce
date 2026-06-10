# gRPC vs REST 벤치마크

## 실행 순서

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 서버 3개 실행 (터미널 각각)

```bash
# 터미널 1 — product gRPC 서버 (시나리오 1용)
cd Backend/product
python main.py

# 터미널 2 — REST 서버 (시나리오 1, 2 공용)
cd benchmark
python rest_server.py

# 터미널 3 — in-memory gRPC 서버 (시나리오 2용)
cd benchmark
python inmemory_grpc_server.py
```

### 3. 벤치마크 실행

```bash
cd benchmark
python run_bench.py          # 기본 100회
python run_bench.py --n 200  # 200회 반복
```

## 예상 출력

```
====================================================
  gRPC vs REST 벤치마크  (100회 반복)
====================================================

[시나리오 1]  실제 MongoDB 쿼리 포함

  gRPC  (product 서버 직접, localhost:50051)
  평균 응답       3.20 ms
  중앙값          2.90 ms
  최소/최대    1.80 / 12.40 ms
  처리량          312 req/s
  페이로드      8,400 bytes

  REST  (FastAPI + MongoDB, localhost:50054/products)
  평균 응답       8.50 ms
  ...

  ➜ gRPC가 REST 대비 2.7배 빠름

----------------------------------------------------

[시나리오 2]  In-memory 고정 데이터 (순수 직렬화/전송)

  gRPC  (in-memory 서버, localhost:50055)
  평균 응답       0.45 ms
  페이로드      1,240 bytes

  REST  (in-memory, localhost:50054/products/inmemory)
  평균 응답       1.80 ms
  페이로드      3,800 bytes

  ➜ gRPC가 REST 대비 4.0배 빠름
====================================================
```

## 시나리오 설명

| 시나리오 | 목적 |
|---|---|
| 1. DB 포함 | 실제 운영 환경과 동일 조건 비교 (DB IO 포함) |
| 2. In-memory | 순수 직렬화/전송 속도만 비교 (gRPC 장점이 가장 선명하게 나타남) |
