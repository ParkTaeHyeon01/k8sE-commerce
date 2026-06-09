---
name: crawler-target-kurly
description: 크롤링 대상을 마켓컬리(Kurly)로 확정한 결정과 사이트 구조 조사 결과 (URL 패턴, 카드 파싱 구조)
metadata:
  node_type: memory
  type: project
  originSessionId: 4e827445-bbda-4abd-bc52-9e363a20499a
---

크롤링 대상을 **마켓컬리(Kurly, www.kurly.com)** 로 확정함 (2026-06-08). 기존 G마켓 카테고리 기반 코드는 모두 제거하고 컬리 구조에 맞게 재작성함 (커밋 `d0afa30`).

## 핵심 URL 구조
- 베스트: `https://www.kurly.com/collection-groups/market-best?site=MARKET&page=1&collection=market-best-logic`
- 할인(세일): `https://www.kurly.com/collection-groups/market-sales-group?site=MARKET&page=1&collection=market-sales-main1`
- 두 URL 모두 `&filters=category:{코드}` 를 붙이면 **특정 카테고리로 좁혀서 베스트/할인을 가져올 수 있음** (예: `filters=category:910` = 정육·가공육·달걀). 별도 카테고리 페이지 URL을 새로 만들 필요 없이 기존 두 컬렉션 URL을 재활용 가능.
- `site=MARKET`은 "식품 전용"이 아니라 마켓컬리 메인 쇼핑 영역(식품+건강식품+스킨케어/헤어바디 일부 포함) 전체를 가리킴 — 정확히 식품만 필요하면 category 필터로 좁혀야 함.
- 베스트 vs 할인 차이: 베스트(`market-best-logic`)는 인기 상품 모음으로 카테고리별 항목 수가 적고(수십~수백), 할인(`market-sales-main1`)은 항목 풀이 훨씬 큼(수백~수천).

## 카드 파싱 구조 (현재 구현: Crawler/parsers/kurly.py)
- 셀렉터: `article` (클래스명이 `css-xxxxx` 해시값이라 불안정 — 절대 클래스명으로 셀렉팅하지 말 것)
- 카드 텍스트 패턴: `(쿠폰/혜택 뱃지) → 담기 → 배송유형(~배송) → 상품명 → 한줄설명 → 가격정보 → 재고`
- 가격정보: 할인 있으면 "정가/할인율/할인가" 3줄, 없으면 가격 1줄만
- G마켓과 달리 순위(rank) 표시가 없음 — 베스트/할인 두 페이지 카드 구조가 동일해서 파서 1개로 통합 가능했음

## 식품 카테고리 코드 (전체 메뉴 30개 중 식품 15개, 프론트 메뉴 후보)
채소(907), 과일·견과·쌀(908), 수산·해산·건어물(909), 정육·가공육·달걀(910), 국·반찬·메인요리(911), 간편식·밀키트·샐러드(912), 면·양념·오일(913), 생수·음료(914), 커피·차(383), 간식·과자·떡(249), 베이커리(915), 유제품(018), 건강식품(032), 와인·위스키·데낄라(722), 전통주(251)

**Why**: 사용자가 "프론트에 보여줄 메뉴와 카테고리를 추출"하면서 메뉴 클릭 시 실제 카테고리 상품이 보여야 한다고 확정함. 위 URL 구조 덕분에 기존 베스트/할인 컬렉션 코드를 거의 그대로 재사용하면서 카테고리별 수집이 가능해짐.

**How to apply**: 크롤러를 카테고리별로 확장할 때는 `filters=category:{코드}` 파라미터 추가 방식을 우선 검토할 것 (완전히 새로운 URL 빌더를 만들 필요 없음). [[crawler-multi-instance-plan]]과 함께 참고.

## 카테고리별 수집 구현 완료 (2026-06-08, 커밋 e91f4b8)
- 사용자가 "15개 전부 수집"으로 확정 → `Crawler/pages.py`의 `FOOD_CATEGORIES` 딕셔너리에 15개 코드/이름 매핑, `build_url(target, category_code)`로 `filters=category:{코드}` 부착
- `Crawler/main.py`가 `CRAWL_TARGET` x 15개 카테고리를 순회하며 카테고리별로 결과를 분리 저장 (`category_code`, `category_name` 필드 포함)
- 베스트 컬렉션 기준 실제 수집 검증 결과: 총 832건, 카테고리별 1~96건 (와인/전통주처럼 베스트 항목이 적은 카테고리는 1~2건에 불과 — 정상적인 사이트 데이터 특성, 파싱 오류 아님)
