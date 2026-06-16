# k8sE-commerce 워크북

마켓컬리 인기/할인 상품을 크롤링해 보여주는 쇼핑몰 서비스.  
k8s CI/CD 시연을 목적으로 한 MSA 구조의 MVP 프로젝트.

---

## 목차

1. [아키텍처](#1-아키텍처)
2. [환경 설정](#2-환경-설정)
3. [환경변수](#3-환경변수)
4. [크롤러](#4-크롤러)
5. [Kafka Consumer](#5-kafka-consumer)
6. [백엔드](#6-백엔드)
7. [프론트엔드](#7-프론트엔드)
8. [전체 실행 순서](#8-전체-실행-순서)
9. [API 명세서](#9-api-명세서)

---

## 1. 아키텍처

### 전체 흐름

```
[마켓컬리]
    │  Playwright 크롤링
    ▼
[Crawler] ──Kafka Producer──▶ [Kafka Broker] ──Consumer──▶ [Kafka Consumer]
                                                                    │
[rank_updater] ─────────────────────────────────────────────────▶  │ → MongoDB
[category_crawler] ──────────────────────────────────────────────▶ │ → MongoDB
                                                                    ▼
                                                              [MongoDB]
                                                                    │
                                                       [Product gRPC 서버 :50051]
                                                                    │ gRPC
                                        [Auth-Member gRPC 서버 :50052] ─── [MariaDB]
                                        [Payment gRPC 서버 :50053]   ─── (MariaDB/포인트)
                                                                    │
                                                       [Gateway FastAPI :8000]
                                                                    │ REST/JSON
                                                       [Frontend React :5173]
```

### 기술 스택

| 레이어 | 기술 | 역할 |
|--------|------|------|
| 크롤러 | Python + Playwright | 마켓컬리 상품 수집 |
| 메시지 큐 | Apache Kafka (KRaft) | 크롤러 → 적재 파이프라인 |
| 상품 DB | MongoDB | 크롤링 상품 데이터 (스키마 유동적) |
| 회원 DB | MariaDB | 회원/인증/포인트 (정합성 필요) |
| 캐시 | Redis | API 응답 캐시 |
| 백엔드 통신 | gRPC | 서비스 간 내부 통신 |
| API Gateway | FastAPI | REST → gRPC 변환 (BFF) |
| 프론트엔드 | React + Vite | 상품 목록/상세 UI |
| 인프라 | Kubernetes + GitLab CI | 컨테이너 오케스트레이션 + CI/CD |
| 스토리지 | Longhorn | k8s 퍼시스턴트 볼륨 (3-replica) |
| 서비스 메시 | Istio | 트래픽 제어, mTLS, 진입 게이트웨이 |

### 서비스 구성

**Crawler (3종류)**

| 파일 | 역할 | 소요시간 |
|------|------|---------|
| `main.py` | 상품 목록 + 상세 전체 수집 → Kafka | ~4시간 |
| `rank_updater.py` | 판매량순 순위만 수집 → MongoDB | ~10분 |
| `category_crawler.py` | 카테고리 목록 수집 → MongoDB | ~5초 |

**Backend**

| 서비스 | 포트 | DB |
|--------|------|----|
| product gRPC 서버 | 50051 | MongoDB |
| auth-member gRPC 서버 | 50052 | MariaDB |
| payment gRPC 서버 | 50053 | MariaDB (포인트 차감) |
| gateway FastAPI | 8000 | - (gRPC 경유, Redis 캐시) |

**크롤 대상**
- **베스트(best)**: `kurly.com/collection-groups/market-best`
- **할인(sales)**: `kurly.com/collection-groups/market-sales-group`
- 수집 카테고리: 채소, 과일·견과·쌀, 수산·해산·건어물, 정육·가공육·달걀, 국·반찬·메인요리, 간편식·밀키트·샐러드, 면·양념·오일, 생수·음료, 커피·차, 간식·과자·떡, 베이커리, 유제품, 건강식품, 와인·위스키·데낄라, 전통주(베스트만)

### 왜 두 DB를 쓰는가?
- **MongoDB**: 상품 데이터는 카테고리마다 필드가 조금씩 달라 스키마가 유동적 → Document DB 적합
- **MariaDB**: 회원/포인트는 트랜잭션과 정합성이 중요 → RDBMS 적합

---

## 2. 환경 설정

### Python 3.11+

```bash
python --version
```

### Node.js 18+

```bash
node --version
npm --version
```

### Kafka (KRaft 모드 — Zookeeper 없음)

> Kafka 4.x부터 KRaft 전용. Zookeeper 설정 필요 없음.

**설치**
1. [kafka.apache.org](https://kafka.apache.org/downloads) 에서 다운로드
2. `C:\kafka`에 압축 해제

**초기 설정 (최초 1회)**
```powershell
# Cluster ID 생성
C:\kafka\bin\windows\kafka-storage.bat random-uuid
# 출력된 UUID를 아래 명령에 사용

C:\kafka\bin\windows\kafka-storage.bat format `
  -t <위에서-나온-UUID> `
  -c C:\kafka\config\kraft\server.properties
```

**실행**
```powershell
C:\kafka\bin\windows\kafka-server-start.bat C:\kafka\config\kraft\server.properties
```

**토픽 생성 (최초 1회)**
```powershell
C:\kafka\bin\windows\kafka-topics.bat `
  --create --topic crawled-products `
  --bootstrap-server localhost:9092 `
  --partitions 1 --replication-factor 1
```

### MongoDB (WSL2)

```bash
# WSL2 터미널에서
sudo systemctl start mongod
sudo systemctl status mongod  # 상태 확인
```

### Redis

```powershell
# Windows
redis-server
```

```bash
# 또는 WSL2에서
sudo service redis-server start
```

### MariaDB

```powershell
# Windows 서비스
Start-Service -Name "MariaDB"
```

### Python 패키지 설치

```powershell
cd Crawler
pip install -r requirements.txt
playwright install chromium

cd ..\Kafka
pip install -r requirements.txt

cd ..\Backend\product
pip install -r requirements.txt

cd ..\gateway
pip install -r requirements.txt
```

### Frontend

```powershell
cd Frontend
npm install
```

---

## 3. 환경변수

### 루트 `.env` (백엔드 전체 공통)

`.env.example`을 복사해서 생성:

```powershell
cp .env.example .env
```

```env
# 수집 대상: best(베스트) 또는 sales(할인)
CRAWL_TARGET=best

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_PRODUCT_TOPIC=crawled-products
KAFKA_CONSUMER_GROUP=product-loader

# MongoDB
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=ecommerce

# Redis (로컬 개발: 읽기/쓰기 동일 서버 사용)
REDIS_WRITE_URL=redis://localhost:6379/0
REDIS_READ_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=60

# Product gRPC 서버
PRODUCT_GRPC_PORT=50051

# Gateway
PRODUCT_GRPC_ADDR=localhost:50051
CORS_ORIGINS=http://localhost:5173
```

> MongoDB 인증이 있는 경우:  
> `MONGODB_URI=mongodb://admin:k8spass%23@localhost:27017/?authSource=admin`  
> (`#` → `%23` URL 인코딩)

### `Frontend/.env`

```env
VITE_API_BASE=http://localhost:8000
```

### 파일 구조

```
k8sE-commerce/
├── .env              ← 백엔드 전체 공통 (Crawler, Kafka, Backend 모두 이 파일 읽음)
├── .env.example      ← 예시 파일 (git 추적됨)
└── Frontend/
    └── .env          ← Vite 전용 (VITE_API_BASE)
```

---

## 4. 크롤러

### 상품 크롤러 (`main.py`)

마켓컬리 상품 목록 + 상세페이지를 수집해 Kafka로 전송.

```powershell
cd Crawler

# 베스트 상품 수집
$env:CRAWL_TARGET="best"
python main.py

# 할인 상품 수집
$env:CRAWL_TARGET="sales"
python main.py
```

> **소요시간**: 카테고리 15개 × 상품 ~100건 × 상세페이지 수집 → 약 3~4시간  
> **중단 후 재시작 안전**: product_id 기준 upsert라 중복 없음

**동작 흐름**
```
카테고리 목록 순회
  └─▶ 목록 페이지 스크롤 → 상품 카드 파싱
        └─▶ 각 상품 상세페이지 방문 → 상세 이미지 수집
              └─▶ Kafka로 전송 (status="ready")
              └─▶ 실패 시 status="draft"로 전송 (다음 크롤링 때 재시도)
크롤링 완료 후 sync 메시지 전송 (목록에서 빠진 상품 targets에서 제거)
```

### 순위 업데이터 (`rank_updater.py`)

판매량순(sorted_type=1) 페이지를 순회해 `best_rank` / `sales_rank` 갱신.  
상세페이지 방문 없어 빠름.

```powershell
cd Crawler

$env:CRAWL_TARGET="best"
python rank_updater.py

$env:CRAWL_TARGET="sales"
python rank_updater.py
```

> **소요시간**: 약 5~10분  
> **동작**: 실행마다 기존 순위 전체 초기화 → 새 순위 입력  
> **수집량**: 96개/페이지, 마지막 페이지까지 자동 순회 (best ~1,356건, sales ~8,295건)

### 카테고리 크롤러 (`category_crawler.py`)

마켓컬리 필터 API에서 카테고리 목록을 가져와 MongoDB `categories` 컬렉션에 저장.  
Playwright 불필요 — 매우 빠름.

```powershell
cd Crawler
python category_crawler.py
```

> **소요시간**: 약 5초  
> **결과**: 베스트 ~30개, 할인 ~25개 (비식품 포함 전체)

---

## 5. Kafka Consumer

크롤러가 Kafka에 보낸 상품 데이터를 읽어 MongoDB에 저장하는 컨슈머.  
크롤러와 **동시에** 실행해야 한다.

```powershell
cd Kafka
python main.py
```

### 동작 흐름

```
Kafka 토픽(crawled-products) 구독
  └─▶ 상품 메시지 수신
        └─▶ MongoDB products 컬렉션에 upsert
              - product_id 기준 중복 없음
              - targets 배열에 best/sales 누적 ($addToSet)
              - category_code/name은 최초 저장 후 유지 ($setOnInsert)

  └─▶ sync 메시지 수신 (크롤링 완료 신호)
        └─▶ 이번 크롤링에서 안 보인 상품 → targets에서 해당 target 제거
        └─▶ Redis 캐시 전체 삭제 (새 데이터 즉시 반영)
```

### MongoDB 상품 도큐먼트 구조

```json
{
  "product_id": "12345678",
  "name": "상품명",
  "sale_price": 9900,
  "original_price": 12000,
  "discount_rate": 17,
  "image_url": "https://...",
  "detail_url": "https://kurly.com/goods/12345678",
  "category_code": "907",
  "category_name": "채소",
  "targets": ["best", "sales"],
  "status": "ready",
  "best_rank": 5,
  "sales_rank": 12,
  "detail_blocks": [
    { "type": "image", "value": "https://..." }
  ],
  "crawled_at": "2026-06-09T12:00:00Z"
}
```

**status 필드**
- `ready`: 상세페이지 수집 완료 → 서비스에 노출
- `draft`: 상세페이지 수집 실패 → 숨김, 다음 크롤링 때 재시도

---

## 6. 백엔드

```
Backend/
├── proto/                 ← gRPC 인터페이스 정의 (.proto)
├── product/               ← gRPC 서버 (MongoDB 조회)
├── auth-member/           ← gRPC 서버 (회원/포인트/주문, MariaDB)
├── payment/               ← gRPC 서버 (결제/포인트 차감, MariaDB)
└── gateway/               ← FastAPI REST API (gRPC 호출 후 JSON 반환)
```

### Product gRPC 서버

```powershell
cd Backend/product
python main.py
```

- 포트: **50051**
- 제공 RPC: `ListProducts`, `GetProduct`, `ListCategories`, `UpdateStock`, `DeleteProduct`

### Auth-Member gRPC 서버

```powershell
cd Backend/auth-member
python main.py
```

- 포트: **50052**
- 제공 RPC: `Register`, `Login`, `GetMe`, `GetPoints`, `GetOrders`, `GetAddresses`, `AddAddress`, `SetDefaultAddress`, `DeleteAddress`, `WithdrawUser`
- 관리자 RPC: `AdminListUsers`, `AdminAdjustPoints`, `AdminSetAdmin`, `AdminDeleteUser`, `AdminRestoreUser`, `AdminGetAllOrders`
- 시작 시 MariaDB 테이블 자동 생성 + 관리자 계정 시드

### Payment gRPC 서버

```powershell
cd Backend/payment
python main.py
```

- 포트: **50053**
- 제공 RPC: `Checkout` (포인트 차감 + 주문 생성), `CancelOrder` (포인트 환불)

### Gateway FastAPI

```powershell
cd Backend/gateway
python -m uvicorn main:app --port 8000
```

- 포트: **8000**
- Swagger 문서: `http://localhost:8000/docs`
- 장바구니는 Redis에 직접 저장 (TTL 7일)

**라우터 구성**

| prefix | 설명 |
|--------|------|
| `/auth` | 회원가입 · 로그인 |
| `/me` | 내 정보 · 포인트 · 주문내역 · 배송지 |
| `/products` | 상품 목록 · 상세 · 자동완성 |
| `/categories` | 카테고리 목록 |
| `/cart` | 장바구니 (Redis) |
| `/cart/checkout` | 포인트 결제 |
| `/orders/{id}/cancel` | 주문 취소 |
| `/admin` | 관리자 전용 (상품·회원·주문 관리) |

> 전체 엔드포인트는 [API 명세서](api-spec.md) 참고

### Proto 재생성 (proto 수정 시)

```powershell
cd Backend
python -m grpc_tools.protoc -I proto --python_out=product --grpc_python_out=product proto/product.proto
python -m grpc_tools.protoc -I proto --python_out=gateway --grpc_python_out=gateway proto/product.proto
python -m grpc_tools.protoc -I proto --python_out=auth-member --grpc_python_out=auth-member proto/auth.proto
python -m grpc_tools.protoc -I proto --python_out=gateway --grpc_python_out=gateway proto/auth.proto
python -m grpc_tools.protoc -I proto --python_out=payment --grpc_python_out=payment proto/payment.proto
python -m grpc_tools.protoc -I proto --python_out=gateway --grpc_python_out=gateway proto/payment.proto
```

---

## 7. 프론트엔드

React + Vite 기반 쇼핑몰 UI.

```powershell
cd Frontend
npm install   # 최초 1회
npm run dev
```

브라우저에서 `http://localhost:5173` 접속.

### 화면 구성

| 경로 | 화면 | 설명 |
|------|------|------|
| `/` | 홈 | 카테고리 카드 목록 |
| `/products` | 상품 목록 | 탭(전체/베스트/할인) + 사이드바 카테고리 + 정렬 |
| `/products/:id` | 상품 상세 | 이미지, 가격, 상세 블록 |

### 상품 목록 기능

- **탭**: 전체 / 베스트 / 할인 전환
- **카테고리**: 탭에 따라 동적으로 로드 (마켓컬리 카테고리 기반)
- **정렬**: 기본순 / 인기순(베스트·할인 탭만) / 낮은 가격순 / 높은 가격순 / 할인율 높은순

---

## 8. 전체 실행 순서

### 최초 세팅 (데이터 없는 경우)

**Step 1. 인프라 시작** — 각각 별도 터미널

```powershell
# Kafka
C:\kafka\bin\windows\kafka-server-start.bat C:\kafka\config\kraft\server.properties
```
```bash
# MongoDB (WSL2)
sudo systemctl start mongod
```
```powershell
# Redis
redis-server

# MariaDB
Start-Service -Name "MariaDB"
```

**Step 2. 환경변수 설정**

```powershell
cp .env.example .env
```

**Step 3. Kafka Consumer 시작**

```powershell
cd Kafka
python main.py
```

**Step 4. 카테고리 수집**

```powershell
cd Crawler
python category_crawler.py
```

**Step 5. 상품 크롤링** — 터미널 2개에서 동시 실행

```powershell
# 터미널 1
cd Crawler; $env:CRAWL_TARGET="best"; python main.py

# 터미널 2
cd Crawler; $env:CRAWL_TARGET="sales"; python main.py
```

**Step 6. 순위 업데이트** — 크롤링 완료 후

```powershell
cd Crawler
$env:CRAWL_TARGET="best";  python rank_updater.py
$env:CRAWL_TARGET="sales"; python rank_updater.py
```

**Step 7. 백엔드 서버 시작**

```powershell
# 터미널 1
cd Backend/product; python main.py

# 터미널 2
cd Backend/auth-member; python main.py

# 터미널 3
cd Backend/payment; python main.py

# 터미널 4
cd Backend/gateway; python -m uvicorn main:app --port 8000
```

**Step 8. 프론트엔드**

```powershell
cd Frontend; npm run dev
```

`http://localhost:5173` 접속.

---

### 재시작 (데이터 있는 경우)

```
1. Kafka / MongoDB / Redis / MariaDB 시작
2. cd Kafka              → python main.py
3. cd Backend/product    → python main.py
4. cd Backend/auth-member → python main.py
5. cd Backend/payment    → python main.py
6. cd Backend/gateway    → python -m uvicorn main:app --port 8000
7. cd Frontend           → npm run dev
```

### 포트 요약

| 서비스 | 포트 |
|--------|------|
| Kafka | 9092 |
| MongoDB | 27017 |
| Redis | 6379 |
| MariaDB | 3306 |
| Product gRPC | 50051 |
| Auth-Member gRPC | 50052 |
| Payment gRPC | 50053 |
| Gateway REST | 8000 |
| Frontend | 5173 |

---


---

## 9. API 명세서

**Base URL**: `http://<cluster-ip>/api` (인그레스 경유)  
**인증**: JWT Bearer 토큰 (`Authorization: Bearer <token>`)  
**인증 필요 항목**: 🔒 표시

---

## 목차

1. [인증 (Auth)](#1-인증-auth)
2. [내 정보 (Me)](#2-내-정보-me)
3. [상품 (Products)](#3-상품-products)
4. [카테고리 (Categories)](#4-카테고리-categories)
5. [장바구니 (Cart)](#5-장바구니-cart)
6. [주문/결제 (Purchase)](#6-주문결제-purchase)
7. [관리자 (Admin)](#7-관리자-admin)
8. [공통 응답](#8-공통-응답)

---

## 1. 인증 (Auth)

### POST `/auth/register` — 회원가입

| 항목 | 내용 |
|------|------|
| 인증 | 불필요 |
| Content-Type | application/json |

**Request Body**
```json
{
  "username": "홍길동",
  "email": "user@example.com",
  "password": "password123"
}
```

**Response 200**
```json
{
  "token": "<JWT>",
  "message": "회원가입 완료"
}
```

**Response 400** — 이메일 중복 등
```json
{ "detail": "이미 사용 중인 이메일입니다." }
```

---

### POST `/auth/login` — 로그인

| 항목 | 내용 |
|------|------|
| 인증 | 불필요 |
| Content-Type | application/json |

**Request Body**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response 200**
```json
{
  "token": "<JWT>",
  "message": "로그인 성공"
}
```

**Response 401** — 이메일/비밀번호 불일치
```json
{ "detail": "이메일 또는 비밀번호가 올바르지 않습니다." }
```

---

## 2. 내 정보 (Me)

### GET `/me` 🔒 — 내 프로필 조회

**Response 200**
```json
{
  "id": 1,
  "username": "홍길동",
  "email": "user@example.com",
  "points": 5000,
  "is_admin": false,
  "created_at": "2025-01-01T00:00:00"
}
```

---

### GET `/me/points` 🔒 — 포인트 조회

**Response 200**
```json
{ "points": 5000 }
```

---

### GET `/me/orders` 🔒 — 주문 내역 조회

**Response 200**
```json
{
  "orders": [
    {
      "id": 1,
      "product_id": "abc123",
      "product_name": "유기농 사과",
      "product_image": "https://...",
      "quantity": 2,
      "unit_price": 3000,
      "total_price": 6000,
      "status": "completed",
      "created_at": "2025-06-01T12:00:00",
      "shipping_address": "서울시 강남구 ..."
    }
  ]
}
```

---

### GET `/me/addresses` 🔒 — 배송지 목록 조회

**Response 200**
```json
{
  "addresses": [
    {
      "id": 1,
      "recipient": "홍길동",
      "phone": "010-1234-5678",
      "zipcode": "12345",
      "address": "서울시 강남구 테헤란로 1",
      "address_detail": "101호",
      "is_default": true
    }
  ]
}
```

---

### POST `/me/addresses` 🔒 — 배송지 추가

**Request Body**
```json
{
  "recipient": "홍길동",
  "phone": "010-1234-5678",
  "zipcode": "12345",
  "address": "서울시 강남구 테헤란로 1",
  "address_detail": "101호"
}
```

**Response 200**
```json
{ "success": true, "address_id": 3 }
```

---

### PUT `/me/addresses/{address_id}/default` 🔒 — 기본 배송지 변경

| 파라미터 | 위치 | 설명 |
|---------|------|------|
| address_id | Path | 배송지 ID |

**Response 200**
```json
{ "success": true }
```

---

### DELETE `/me/addresses/{address_id}` 🔒 — 배송지 삭제

**Response 200**
```json
{ "success": true }
```

---

### DELETE `/me` 🔒 — 회원 탈퇴

**Response 200**
```json
{ "success": true }
```

---

## 3. 상품 (Products)

### GET `/products` — 상품 목록 조회

| 파라미터 | 위치 | 타입 | 기본값 | 설명 |
|---------|------|------|--------|------|
| target | Query | string | `""` | `best` \| `sales` \| (빈값=전체) |
| category_code | Query | string | `""` | 카테고리 코드 (예: `907`) |
| page | Query | int | `1` | 페이지 번호 (1부터) |
| page_size | Query | int | `20` | 페이지당 상품 수 (최대 100) |
| sort_by | Query | string | `""` | `rank` \| `price_asc` \| `price_desc` \| `discount_desc` |
| q | Query | string | `""` | 검색어 |

**Response 200**
```json
{
  "products": [
    {
      "product_id": "abc123",
      "name": "유기농 사과",
      "image_url": "https://...",
      "original_price": 5000,
      "sale_price": 3500,
      "discount_rate": 30,
      "category_code": "908",
      "category_name": "과일·견과·쌀",
      "stock": 99,
      "rank": 1
    }
  ],
  "total": 120,
  "page": 1,
  "page_size": 20
}
```

---

### GET `/products/suggest` — 검색 자동완성

| 파라미터 | 위치 | 타입 | 설명 |
|---------|------|------|------|
| q | Query | string | 검색어 (최소 1자) |

**Response 200**
```json
{
  "suggestions": ["사과", "사과즙", "사과잼"]
}
```

---

### GET `/products/{product_id}` — 상품 상세 조회

| 파라미터 | 위치 | 설명 |
|---------|------|------|
| product_id | Path | 상품 ID |

**Response 200**
```json
{
  "product_id": "abc123",
  "name": "유기농 사과",
  "image_url": "https://...",
  "detail_images": ["https://...", "https://..."],
  "original_price": 5000,
  "sale_price": 3500,
  "discount_rate": 30,
  "category_code": "908",
  "category_name": "과일·견과·쌀",
  "stock": 99,
  "rank": 1
}
```

**Response 404**
```json
{ "detail": "상품을 찾을 수 없습니다" }
```

---

## 4. 카테고리 (Categories)

### GET `/categories` — 카테고리 목록

| 파라미터 | 위치 | 타입 | 기본값 | 설명 |
|---------|------|------|--------|------|
| target | Query | string | `best` | `best` \| `sales` |

**Response 200**
```json
{
  "categories": [
    { "code": "907", "name": "채소" },
    { "code": "908", "name": "과일·견과·쌀" }
  ]
}
```

---

## 5. 장바구니 (Cart)

### GET `/cart` 🔒 — 장바구니 조회

**Response 200**
```json
{
  "items": [
    {
      "product_id": "abc123",
      "name": "유기농 사과",
      "image_url": "https://...",
      "sale_price": 3500,
      "stock": 99,
      "quantity": 2,
      "total_price": 7000
    }
  ],
  "total": 7000
}
```

---

### POST `/cart` 🔒 — 장바구니 담기

**Request Body**
```json
{
  "product_id": "abc123",
  "quantity": 2
}
```

**Response 200**
```json
{ "success": true, "quantity": 2 }
```

**Response 400** — 재고 없음
```json
{ "detail": "재고가 없습니다." }
```

**Response 404** — 상품 없음
```json
{ "detail": "상품을 찾을 수 없습니다." }
```

---

### PUT `/cart/{product_id}` 🔒 — 장바구니 수량 변경

| 파라미터 | 위치 | 설명 |
|---------|------|------|
| product_id | Path | 상품 ID |

**Request Body**
```json
{ "quantity": 3 }
```
> `quantity`가 0 이하면 해당 상품이 장바구니에서 제거됩니다.

**Response 200**
```json
{ "success": true }
```

---

### DELETE `/cart/{product_id}` 🔒 — 장바구니 특정 상품 제거

**Response 200**
```json
{ "success": true }
```

---

### DELETE `/cart` 🔒 — 장바구니 전체 비우기

**Response 200**
```json
{ "success": true }
```

---

## 6. 주문/결제 (Purchase)

### POST `/cart/checkout` 🔒 — 장바구니 결제 (포인트 차감)

**Request Body**
```json
{ "address_id": 1 }
```

**Response 200**
```json
{
  "success": true,
  "total": 7000,
  "points_after": 43000,
  "items_count": 1
}
```

**Response 400** — 장바구니가 비어 있거나 포인트 부족
```json
{ "detail": "포인트가 부족합니다." }
```

**Response 502** — Payment 서비스 오류
```json
{ "detail": "결제 서비스 오류: UNAVAILABLE" }
```

---

### POST `/orders/{order_id}/cancel` 🔒 — 주문 취소 (포인트 환불)

| 파라미터 | 위치 | 설명 |
|---------|------|------|
| order_id | Path | 주문 ID |

**Response 200**
```json
{ "success": true, "refund_amount": 7000 }
```

---

## 7. 관리자 (Admin)

> 모든 엔드포인트에 관리자 계정의 JWT가 필요합니다. 🔒  
> 일반 사용자가 호출하면 `403 Forbidden`

### 상품 관리

#### GET `/admin/products` — 상품 전체 목록

| 파라미터 | 위치 | 타입 | 기본값 | 설명 |
|---------|------|------|--------|------|
| page | Query | int | `1` | 페이지 번호 |
| page_size | Query | int | `50` | 페이지당 수 |
| q | Query | string | `""` | 검색어 |
| sort_by | Query | string | `""` | 정렬 기준 |
| search_by | Query | string | `""` | `name` \| `product_id` |

**Response 200**
```json
{
  "products": [
    {
      "product_id": "abc123",
      "name": "유기농 사과",
      "sale_price": 3500,
      "discount_rate": 30,
      "category_name": "과일·견과·쌀",
      "stock": 99,
      "image_url": "https://..."
    }
  ],
  "total": 500,
  "page": 1,
  "page_size": 50
}
```

---

#### PUT `/admin/products/{product_id}/stock` — 재고 수정

**Request Body**
```json
{ "stock": 100 }
```

**Response 200**
```json
{ "success": true }
```

---

#### DELETE `/admin/products/{product_id}` — 상품 삭제

**Response 200**
```json
{ "success": true }
```

---

### 회원 관리

#### GET `/admin/users` — 회원 전체 목록

**Response 200**
```json
{
  "users": [
    {
      "id": 1,
      "username": "홍길동",
      "email": "user@example.com",
      "points": 5000,
      "is_admin": false,
      "is_active": true,
      "created_at": "2025-01-01T00:00:00",
      "deactivated_by": ""
    }
  ]
}
```

---

#### PUT `/admin/users/{user_id}/points` — 포인트 조정

| 파라미터 | 위치 | 설명 |
|---------|------|------|
| user_id | Path | 회원 ID |

**Request Body**
```json
{
  "amount": 10000,
  "description": "이벤트 지급"
}
```
> `amount`가 양수면 지급, 음수면 차감

**Response 200**
```json
{ "success": true, "points_after": 15000 }
```

---

#### PUT `/admin/users/{user_id}/admin` — 관리자 권한 변경

**Request Body**
```json
{ "is_admin": true }
```

**Response 200**
```json
{ "success": true }
```

---

#### DELETE `/admin/users/{user_id}` — 회원 비활성화

**Response 200**
```json
{ "success": true }
```

---

#### POST `/admin/users/{user_id}/restore` — 회원 복구

**Response 200**
```json
{ "success": true }
```

---

### 주문 관리

#### GET `/admin/orders` — 전체 주문 조회

**Response 200**
```json
{
  "orders": [
    {
      "id": 1,
      "user_id": 1,
      "product_id": "abc123",
      "product_name": "유기농 사과",
      "product_image": "https://...",
      "quantity": 2,
      "unit_price": 3500,
      "total_price": 7000,
      "status": "completed",
      "created_at": "2025-06-01T12:00:00"
    }
  ]
}
```

---

## 8. 공통 응답

### 헬스체크

#### GET `/health`

```json
{ "status": "ok" }
```

---

### HTTP 에러 형식

```json
{ "detail": "에러 메시지" }
```

| 코드 | 의미 |
|------|------|
| 400 | 잘못된 요청 (유효성 오류, 포인트 부족 등) |
| 401 | 인증 실패 (토큰 없음 또는 만료) |
| 403 | 권한 없음 (관리자 전용 엔드포인트) |
| 404 | 리소스 없음 |
| 502 | 내부 gRPC 서비스 오류 |

---

### 인증 헤더

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
