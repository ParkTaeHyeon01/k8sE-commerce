# DB 명세서

---

## 1. MariaDB — `ecommerce` 데이터베이스

> 회원 / 포인트 / 주문 / 배송지 관리 (auth-member 서비스)  
> 트랜잭션 정합성이 필요한 데이터 → RDBMS 선택

---

### 테이블: `users`

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `id` | INT | ✗ | AUTO_INCREMENT | PK |
| `username` | VARCHAR(50) | ✗ | — | 사용자 이름 |
| `email` | VARCHAR(255) | ✗ | — | 이메일 (UNIQUE) |
| `password_hash` | VARCHAR(255) | ✗ | — | bcrypt 해시 |
| `points` | INT | ✗ | 100000 | 보유 포인트 (회원가입 시 10만 지급) |
| `is_admin` | TINYINT(1) | ✗ | 0 | 관리자 여부 |
| `is_active` | TINYINT(1) | ✗ | 1 | 활성 여부 (탈퇴 시 0) |
| `deactivated_by` | VARCHAR(50) | ✔ | NULL | 비활성화 처리자 (self / admin) |
| `created_at` | DATETIME | ✗ | CURRENT_TIMESTAMP | 가입 일시 |

- **인덱스**: `idx_email (email)`

---

### 테이블: `point_history`

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `id` | INT | ✗ | AUTO_INCREMENT | PK |
| `user_id` | INT | ✗ | — | FK → users.id |
| `amount` | INT | ✗ | — | 변동 포인트 (양수=지급, 음수=차감) |
| `description` | VARCHAR(255) | ✗ | — | 변동 사유 |
| `created_at` | DATETIME | ✗ | CURRENT_TIMESTAMP | 변동 일시 |

- **인덱스**: `idx_user_id (user_id)`
- **FK**: `user_id` → `users(id)`

---

### 테이블: `shipping_addresses`

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `id` | INT | ✗ | AUTO_INCREMENT | PK |
| `user_id` | INT | ✗ | — | FK → users.id |
| `recipient` | VARCHAR(50) | ✗ | — | 수령인 |
| `phone` | VARCHAR(20) | ✗ | — | 연락처 |
| `zipcode` | VARCHAR(10) | ✗ | — | 우편번호 |
| `address` | VARCHAR(255) | ✗ | — | 기본 주소 |
| `address_detail` | VARCHAR(255) | ✗ | `''` | 상세 주소 |
| `is_default` | TINYINT(1) | ✗ | 0 | 기본 배송지 여부 |

- **인덱스**: `idx_user_id (user_id)`
- **FK**: `user_id` → `users(id)`

---

### 테이블: `orders`

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|:----:|--------|------|
| `id` | INT | ✗ | AUTO_INCREMENT | PK |
| `user_id` | INT | ✗ | — | FK → users.id |
| `product_id` | VARCHAR(50) | ✗ | — | 상품 ID (MongoDB 참조, 스냅샷) |
| `product_name` | VARCHAR(255) | ✗ | — | 주문 시점 상품명 스냅샷 |
| `product_image` | VARCHAR(512) | ✗ | `''` | 주문 시점 이미지 URL 스냅샷 |
| `quantity` | INT | ✗ | 1 | 주문 수량 |
| `unit_price` | INT | ✗ | — | 단가 (주문 시점 스냅샷) |
| `total_price` | INT | ✗ | — | 결제 금액 |
| `shipping_address` | VARCHAR(512) | ✗ | `''` | 배송지 스냅샷 |
| `status` | VARCHAR(20) | ✗ | `'paid'` | 주문 상태 (`paid` / `cancelled`) |
| `created_at` | DATETIME | ✗ | CURRENT_TIMESTAMP | 주문 일시 |

- **인덱스**: `idx_user_id (user_id)`, `idx_status (status)`
- **FK**: `user_id` → `users(id)`

---

## 2. MongoDB — `ecommerce` 데이터베이스

> 크롤링 상품 데이터 (product 서비스)  
> 카테고리마다 필드가 달라 스키마 유동적 → Document DB 선택

---

### 컬렉션: `products`

| 필드 | 타입 | 설명 |
|------|------|------|
| `product_id` | string | 마켓컬리 상품 ID (unique 인덱스) |
| `name` | string | 상품명 |
| `original_price` | int | 정가 |
| `sale_price` | int | 판매가 |
| `discount_rate` | int | 할인율 (%) |
| `image_url` | string | 대표 이미지 URL |
| `detail_url` | string | 마켓컬리 상세페이지 URL |
| `detail_blocks` | array | 상세페이지 블록 (`{type, value}`) |
| `delivery_info` | string | 배송 안내 문구 |
| `category_code` | string | 카테고리 코드 (최초 수집 시 고정) |
| `category_name` | string | 카테고리명 (최초 수집 시 고정) |
| `targets` | array | 노출 대상 (`["best"]`, `["sales"]`, `["best","sales"]`) |
| `status` | string | `ready` (노출) / `draft` (숨김, 상세수집 실패) |
| `best_rank` | int | 베스트 판매 순위 |
| `sales_rank` | int | 할인 판매 순위 |
| `ngrams` | array | 부분 문자열 검색용 n-gram 토큰 |
| `crawled_at` | string | 최초 크롤링 일시 (ISO 8601) |
| `updated_at` | string | 마지막 갱신 일시 (ISO 8601) |
| `trace_id` | string | 크롤링 추적 ID |

- **인덱스**: `product_id` (unique), `targets`, `category_code`, `ngrams` (배열 인덱스)

---

### 컬렉션: `categories`

| 필드 | 타입 | 설명 |
|------|------|------|
| `code` | string | 카테고리 코드 (예: `907`) |
| `name` | string | 카테고리명 (예: `채소`) |
| `target` | string | `best` 또는 `sales` |

---

### 컬렉션: `keywords`

> 검색 자동완성용. 상품명 단어를 분리해 누적 카운트.

| 필드 | 타입 | 설명 |
|------|------|------|
| `text` | string | 키워드 (unique 인덱스) |
| `count` | int | 등장 횟수 |

---

## 3. Redis

> 두 서비스에서 각각 다른 목적으로 사용

### 3-1. 상품 목록 캐시 (product 서비스)

캐시 조회 순서: **인메모리 → Redis → MongoDB**

| 키 패턴 | 타입 | 값 | TTL |
|---------|------|-----|-----|
| `list:{target}:{category_code}:{page}:{page_size}:{sort_by}` | string (JSON) | 상품 목록 + total | 5분 (기본값) |

- 재고 수정 / 상품 삭제 / 크롤링 sync 완료 시 `list:*` 전체 삭제
- 인메모리 캐시는 프로세스 재시작 시 초기화

### 3-2. 장바구니 (gateway 서비스)

| 키 | 타입 | 값 | TTL |
|----|------|-----|-----|
| `cart:{user_id}` | string (JSON) | `{"product_id": quantity, ...}` | 7일 |

- 결제 완료 또는 장바구니 전체 비우기 시 키 삭제

---

## 4. ERD (MariaDB)

```
┌─────────────────────────┐
│          users          │
├─────────────────────────┤
│ PK  id          INT     │
│     username    VARCHAR │
│     email       VARCHAR │◄── UNIQUE
│     password_hash VARCHAR│
│     points      INT     │
│     is_admin    TINYINT │
│     is_active   TINYINT │
│     deactivated_by VARCHAR│
│     created_at  DATETIME│
└────────────┬────────────┘
             │ 1
             │
     ┌───────┼───────────────────────────────┐
     │       │                               │
     │ N     │ N                             │ N
┌────▼───────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐
│   point_history    │  │   shipping_addresses     │  │         orders           │
├────────────────────┤  ├──────────────────────────┤  ├──────────────────────────┤
│PK id       INT     │  │PK id          INT        │  │PK id           INT       │
│FK user_id  INT ────┤  │FK user_id     INT ───────┤  │FK user_id      INT ──────┤
│   amount   INT     │  │   recipient   VARCHAR    │  │   product_id   VARCHAR   │
│   description VARCHAR│ │   phone       VARCHAR    │  │   product_name VARCHAR   │
│   created_at DATETIME│ │   zipcode     VARCHAR    │  │   product_image VARCHAR  │
└────────────────────┘  │   address     VARCHAR    │  │   quantity     INT       │
                        │   address_detail VARCHAR │  │   unit_price   INT       │
                        │   is_default  TINYINT    │  │   total_price  INT       │
                        └──────────────────────────┘  │   shipping_address VARCHAR│
                                                       │   status       VARCHAR   │
                                                       │   created_at   DATETIME  │
                                                       └──────────────────────────┘
```

---

## 5. MongoDB 도큐먼트 예시

### products

```json
{
  "product_id": "12345678",
  "name": "유기농 사과 1kg",
  "original_price": 12000,
  "sale_price": 8400,
  "discount_rate": 30,
  "image_url": "https://img.kurly.com/...",
  "detail_url": "https://www.kurly.com/goods/12345678",
  "category_code": "908",
  "category_name": "과일·견과·쌀",
  "targets": ["best", "sales"],
  "status": "ready",
  "best_rank": 3,
  "sales_rank": 12,
  "ngrams": ["유기농", "사과", "유기", "기농", "사과"],
  "detail_blocks": [
    { "type": "image", "value": "https://img.kurly.com/detail1.jpg" },
    { "type": "image", "value": "https://img.kurly.com/detail2.jpg" }
  ],
  "crawled_at": "2026-06-16T02:00:00Z",
  "updated_at": "2026-06-16T06:00:00Z"
}
```

### keywords

```json
{ "text": "사과", "count": 142 }
{ "text": "유기농", "count": 87 }
```
