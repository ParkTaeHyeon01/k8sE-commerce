---
name: search-feature
description: "상품 목록 검색바 + 자동완성 + nGram 인덱스 기반 부분 문자열 검색 구현 완료 (커밋 87995c6, 2026-06-10)"
metadata:
  type: project
---

헤더 검색창 제거, ProductList 페이지에 검색바 내장. 커밋 87995c6, 푸시 완료.

## 검색 분기 로직 (Backend/product/servicer.py)

| search_by | 검색 방식 | 사용 곳 |
|---|---|---|
| `""` 단일 토큰 | `{ ngrams: "토큰" }` 배열 인덱스 | 상품 목록 |
| `""` 다중 토큰 | `{ ngrams: { $all: [...] } }` 배열 인덱스 | 상품 목록 |
| `"name"` | `$regex` 이름 부분검색 | 관리자 상품명 검색 |
| `"id"` | `product_id` 정확 매치 | 관리자 상품번호 검색 |

- "삼겹" → ngrams에 "삼겹" 토큰이 있는 상품 → "삼겹살" 포함 상품 검색 가능
- "500g" → ngrams에 "500g" 토큰 → 숫자+단위 검색 가능
- "삼겹살 500g" → $all 로 AND 검색
- textScore sort 완전 제거 (ngrams 검색에서 불필요)

## nGram 생성 (Backend/product/ngram.py, Kafka/mongo_loader.py)
- 2~4글자 n-gram + 단어 전체 포함
- "삼겹살" → {"삼겹", "겹살", "삼겹살"}
- 크롤링 저장(mongo_loader.py)·마이그레이션 양쪽 동일 로직

## 인덱스
- MongoDB products.ngrams 배열 인덱스 (Backend/product/db.py, 서비스 시작 시 자동 생성)
- 기존 2,159개 상품 migrate_ngrams.py 로 일괄 마이그레이션 완료

## 자동완성
- `GET /products/suggest?q=` — keywords 컬렉션, prefix $regex, 상위 8개
- 프론트: debounce 200ms

## proto 변경
- `ListProductsRequest`에 `string search_by = 7` 추가

## 프론트 변경 파일
- `Frontend/src/App.jsx` — 헤더 검색창 제거
- `Frontend/src/pages/ProductList.jsx` — 검색바 내장, 자동완성, 탭 변경 시 검색 초기화
- `Frontend/src/api.js` — fetchSuggest, adminGetProducts(search_by 포함)
- `Frontend/src/index.css` — .product-search-*, .suggest-list, .suggest-item 추가

**Why**: 검색은 상품 목록에서만, $text는 숫자/부분문자열 한계로 nGram 배열 인덱스로 교체.
**How to apply**: 검색 수정 시 ngrams 배열 구조와 make_ngrams() 함수 참고.
