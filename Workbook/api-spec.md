# API 명세서

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
