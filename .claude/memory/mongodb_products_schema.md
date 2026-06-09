---
name: mongodb-products-schema
description: MongoDB products 컬렉션 스키마 설계 확정 (product_id 키, targets 배열, status 필드로 노출 제어, 상세 이미지는 URL 배열)
metadata:
  node_type: memory
  type: project
  originSessionId: 51a360da-2793-4782-ae28-44b40057d280
---

크롤링 상품 데이터를 저장할 MongoDB `products` 컬렉션 스키마를 확정함 (2026-06-08, 설계 완료 — 아직 구현 전).

## 확정된 필드 구조
- `_id` (ObjectId): MongoDB 자동 생성 — 우리 시스템의 내부 식별자로 그대로 사용 (별도 ID 체계 만들 필요 없음)
- `product_id` (string, unique index): 컬리 원본 상품 ID (`/goods/{id}`에서 추출) — upsert 매칭 키이자 외부 참조 키. "이름이 비슷해도 product_id가 다르면 별개 상품"으로 취급 (유사도 매칭/병합 로직 없음)
- `targets` (array): 이 상품이 등장한 컬렉션 목록 `["best", "sales"]` — `$addToSet`으로 누적 (단일 값이면 다른 컬렉션에서 사라지는 문제 발생)
- `category_code`, `category_name`, `name`, `original_price`, `sale_price`, `discount_rate`, `delivery_info`, `image_url`, `detail_url`
- ~~상세 전용 필드 `seller`/`package_type`/`unit`/`weight` (라벨 매칭 추출)~~ → **2026-06-09 폐기**: 실제 상세페이지(`#description` 영역, "상품고시정보" 섹션) 조사 결과 거의 모든 라벨 값이 `"상품설명 및 상품이미지 참조"` placeholder라서 구조화해도 의미 있는 데이터가 거의 없음 확인. 라벨-값 매칭 로직 자체를 만들지 않기로 함
- `detail_blocks` (array, **2026-06-09 `detail_images`에서 변경**): `{type: "image"|"text", value}` 형태로 등장 순서를 보존한 블록 배열. `#description .goods_wrap` 영역(소개글/Kurly's Tip 등 실제 본문)을 `:is(img, h3, p.words)`로 순서대로 추출 — 이미지는 `kurly.com` 도메인만, 텍스트는 빈 값 제외. **계기**: 사용자가 원본 상세페이지에서 "이미지 사이에 텍스트/문서 모양"을 발견 → 조사해보니 `#description` 안에 실제 의미있는 본문 텍스트(소개/중량안내/보관법/조리법/활용팁)가 이미지와 번갈아 들어있었음 (이전에 무시했던 "상품고시정보"의 placeholder 텍스트와는 별개). 프론트는 이 배열을 순서대로 렌더링해 원본처럼 이미지-텍스트가 교차되는 상세페이지를 구성할 수 있음. `Crawler/parsers/kurly_detail.py`에 구현 완료
  - **CSS 선택자 주의**: `"A B, C, D"`는 `(A B), C, D`로 해석되어 범위를 벗어남 → `:is()`로 묶어야 제대로 스코프됨 (한 번 이 버그로 페이지 전체의 추천상품 캐러셀 텍스트가 섞여 들어왔던 적 있음)
- `status` (`"draft"` | `"ready"`): **노출 제어 필드** — 목록만 수집되면 `draft`, 상세까지 채워져 upsert되면 `ready`로 전환. 프론트/API는 항상 `status: "ready"`만 조회
- `trace_id`, `crawled_at`, `updated_at`

## 핵심 설계 원칙 (왜 이렇게 했는가)
- 카테고리마다 상세페이지 구조가 들쭉날쭉한 문제 → "라벨로 찾아지면 추출 + 없으면 null + 이미지는 그대로 URL 배열" 방식으로 분기 로직 없이 해결 (사이트가 이미 그렇게 구성해 놓은 걸 그대로 가져오는 셈)
- 이미지는 다운로드/재호스팅하지 않고 URL만 저장 — 스토리지 인프라 불필요, 나중에 필요해지면 필드만 추가하면 됨 (MongoDB 스키마 유연성 활용)
- `status` 필드 하나로 "완벽히 준비된 상품만 노출"과 "상세 크롤링이 끝나는 대로 하나씩 화면에 등장하는 라이브 데모 효과"를 동시에 해결 — 추가 오케스트레이션 로직 없이 쿼리 조건 하나로 끝남

**Why**: 발표에서 "크롤링 → Kafka 정제 → DB 적재 → 서비스 노출"이 실시간으로 보이는 걸 시연하고 싶어했고, 완벽히 준비된 데이터만 보이게 하고 싶다는 요구가 나옴. `status` 필드 하나로 자연스럽게 풀림 — 동시에 "상세를 몇 개나 크롤링할지" 고민까지 해소됨 (다 끝낼 때까지 기다릴 필요 없이 처리되는 대로 하나씩 ready로 전환).

**How to apply**: `product` 서비스(Kafka consumer)가 MongoDB에 적재할 때 이 스키마와 upsert 로직(product_id 키, targets는 $addToSet, status는 list/detail 단계에 따라 draft→ready로 전환)을 그대로 적용할 것. 아직 구현 전이므로 작업 시작 시 이 메모를 기준으로 다시 확인. [[crawler-target-kurly]], [[crawler-multi-instance-plan]]과 함께 참고.

## 프론트 메뉴 구성 결정 (2026-06-09, 추가)
메뉴를 "베스트"/"할인" 2개에서 **"전체"를 추가해 3개**로 구성하기로 함.
- "전체"는 **별도 크롤링이나 필드 추가 없이** 기존 `targets` 배열 설계만으로 해결됨:
  - 베스트 메뉴 → `targets`에 `"best"` 포함된 상품 조회
  - 할인 메뉴 → `targets`에 `"sales"` 포함된 상품 조회
  - 전체 메뉴 → `target` 조건 없이 `status: "ready"` 전체 조회
- `targets`를 배열로 설계해둔 결정이 그대로 들어맞은 사례 — 백엔드 쿼리 조건 하나만 추가하면 됨

**How to apply**: 백엔드 API/프론트 메뉴 작업 시 "전체" 탭은 단순히 `target` 필터를 빼고 `status: "ready"`만 거는 쿼리로 구현하면 됨. 크롤러나 Kafka consumer 쪽 추가 작업 불필요.
