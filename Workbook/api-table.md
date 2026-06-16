# API 명세서 — PPT용 표

---

## [슬라이드 1] 인증 / 회원

| 메서드 | URL | 설명 | 인증 |
|--------|-----|------|:----:|
| POST | `/auth/register` | 회원가입 | ✗ |
| POST | `/auth/login` | 로그인 | ✗ |
| GET | `/me` | 내 프로필 조회 | ✔ |
| GET | `/me/points` | 포인트 조회 | ✔ |
| GET | `/me/orders` | 주문 내역 조회 | ✔ |
| DELETE | `/me` | 회원 탈퇴 | ✔ |

---

## [슬라이드 2] 배송지

| 메서드 | URL | 설명 | 인증 |
|--------|-----|------|:----:|
| GET | `/me/addresses` | 배송지 목록 조회 | ✔ |
| POST | `/me/addresses` | 배송지 추가 | ✔ |
| PUT | `/me/addresses/{id}/default` | 기본 배송지 변경 | ✔ |
| DELETE | `/me/addresses/{id}` | 배송지 삭제 | ✔ |

---

## [슬라이드 3] 상품 / 카테고리

| 메서드 | URL | 설명 | 인증 |
|--------|-----|------|:----:|
| GET | `/products` | 상품 목록 조회 | ✗ |
| GET | `/products/{id}` | 상품 상세 조회 | ✗ |
| GET | `/products/suggest` | 검색 자동완성 | ✗ |
| GET | `/categories` | 카테고리 목록 | ✗ |

### `/products` 쿼리 파라미터

| 파라미터 | 설명 | 예시 |
|----------|------|------|
| `target` | 필터 | `best` \| `sales` \| (전체) |
| `category_code` | 카테고리 | `907`, `908` … |
| `page` / `page_size` | 페이지네이션 | `1` / `20` |
| `sort_by` | 정렬 | `rank` \| `price_asc` \| `price_desc` \| `discount_desc` |
| `q` | 검색어 | `사과` |

---

## [슬라이드 4] 장바구니 / 결제

| 메서드 | URL | 설명 | 인증 |
|--------|-----|------|:----:|
| GET | `/cart` | 장바구니 조회 | ✔ |
| POST | `/cart` | 상품 담기 | ✔ |
| PUT | `/cart/{product_id}` | 수량 변경 | ✔ |
| DELETE | `/cart/{product_id}` | 상품 제거 | ✔ |
| DELETE | `/cart` | 장바구니 비우기 | ✔ |
| POST | `/cart/checkout` | 결제 (포인트 차감) | ✔ |
| POST | `/orders/{id}/cancel` | 주문 취소 (포인트 환불) | ✔ |

---

## [슬라이드 5] 관리자

| 메서드 | URL | 설명 | 인증 |
|--------|-----|------|:----:|
| GET | `/admin/products` | 상품 전체 목록 | 관리자 |
| PUT | `/admin/products/{id}/stock` | 재고 수정 | 관리자 |
| DELETE | `/admin/products/{id}` | 상품 삭제 | 관리자 |
| GET | `/admin/users` | 회원 전체 목록 | 관리자 |
| PUT | `/admin/users/{id}/points` | 포인트 지급/차감 | 관리자 |
| PUT | `/admin/users/{id}/admin` | 관리자 권한 변경 | 관리자 |
| DELETE | `/admin/users/{id}` | 회원 비활성화 | 관리자 |
| POST | `/admin/users/{id}/restore` | 회원 복구 | 관리자 |
| GET | `/admin/orders` | 전체 주문 조회 | 관리자 |

---

## [슬라이드 6] 공통

### HTTP 상태 코드

| 코드 | 의미 |
|------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 (유효성 오류, 포인트 부족 등) |
| 401 | 인증 실패 (토큰 없음 또는 만료) |
| 403 | 권한 없음 (관리자 전용) |
| 404 | 리소스 없음 |
| 502 | 내부 gRPC 서비스 오류 |

### 인증 방식

| 항목 | 내용 |
|------|------|
| 방식 | JWT Bearer Token |
| 헤더 | `Authorization: Bearer <token>` |
| 발급 | `/auth/login` 또는 `/auth/register` 응답의 `token` 필드 |
| 유효기간 | 서버 설정에 따름 |
