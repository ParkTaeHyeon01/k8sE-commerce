---
name: search-feature
description: "상품 목록 검색바 + 자동완성 + 관리자 검색 구현 완료 (미커밋, 2026-06-10)"
metadata:
  type: project
---

헤더 검색창 제거, ProductList 페이지에 검색바 내장. 미커밋 상태.

## 검색 분기 로직 (Backend/product/servicer.py)

| search_by | 검색 방식 | 사용 곳 |
|---|---|---|
| `""` | `$text` 역전 인덱스 | 상품 목록 일반 검색 |
| `""` + 숫자 단독 | `$regex` 이름 부분검색 | 상품 목록 숫자 검색 (확정) |
| `"name"` | `$regex` 이름 부분검색 | 관리자 상품명 검색 |
| `"id"` | `product_id` 정확 매치 | 관리자 상품번호 검색 |

- `$text` + textScore 정렬은 `"$text" in query`일 때만 적용 (중요: $regex 쿼리에 textScore 적용하면 MongoDB 500 에러)

## 자동완성
- `GET /products/suggest?q=` — keywords 컬렉션, prefix $regex, 상위 8개
- 프론트: debounce 200ms, searchRef 클릭 외부 감지

## proto 변경
- `ListProductsRequest`에 `string search_by = 7` 추가
- product_pb2.py 양쪽(Backend/product/, Backend/gateway/) 재컴파일 완료

## 프론트 변경 파일
- `Frontend/src/App.jsx` — 헤더 검색창 제거
- `Frontend/src/pages/ProductList.jsx` — 검색바 내장, 자동완성, 탭 변경 시 검색 초기화
- `Frontend/src/api.js` — fetchSuggest, adminGetProducts(search_by 포함)
- `Frontend/src/index.css` — .product-search-*, .suggest-list, .suggest-item 추가

**Why**: 검색은 상품 목록에서만 있는 게 자연스럽다는 사용자 결정.
**How to apply**: 추후 검색 수정 시 search_by 분기 로직과 textScore 충돌 주의.
