---
name: admin-product-management
description: "관리자 상품 관리 기능 개선 완료 — 상품번호 컬럼, 검색, 컬럼 정렬 (커밋 076786a, 2026-06-10)"
metadata:
  type: project
---

## 구현된 기능 (Frontend/src/pages/Admin.jsx)

### 상품번호 컬럼
- 테이블에 product_id 컬럼 추가 (예: 5031391)

### 검색
- 상품명 / 상품번호 타입 select + 검색 input
- 타입 변경 시 검색어 초기화
- 실패 시 `setProducts([])`, `setTotal(0)` 처리 (빈 테이블 + 0개 표시)

### 컬럼 정렬
- 상품번호/상품명/카테고리/가격/할인율/재고 클릭 정렬
- 순환: asc → desc → null(인기순) → asc
- 다른 컬럼 클릭 시 asc로 초기화
- `sortBy = sortCol && sortDir ? \`${sortCol}_${sortDir}\` : ""`

### 정렬 키 (Backend/product/servicer.py _SORT dict)
product_id/name/category/price/discount/stock × asc/desc = 12개

## 버그 수정
- $regex 검색 + textScore 정렬 충돌 → 500 에러 → CORS 헤더 누락 → "Failed to fetch"
  - 원인: search_by="name"($regex)인데 sort_stage에 $meta:textScore 적용
  - 수정: `if "$text" in query`일 때만 textScore sort 사용
- gateway admin.py에 `grpc.RpcError` 예외 처리 추가 (502 응답 보장)

## 재고 데이터 정리
- stock=null/없는 문서 176개 → 100으로 마이그레이션
- 이후 전체 재고 랜덤 다양화

**How to apply**: 관리자 상품 관리 수정 시 Admin.jsx의 searchType/sortCol/sortDir 상태 참고.
