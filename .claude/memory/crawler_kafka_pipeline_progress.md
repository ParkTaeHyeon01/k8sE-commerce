---
name: crawler-kafka-pipeline-progress
description: "크롤링→Kafka→MongoDB 파이프라인 완료. 인기순 정렬·카테고리 동적화·전통주 오염 수정까지 완료 (2026-06-09)"
metadata:
  node_type: memory
  type: project
  originSessionId: 51a360da-2793-4782-ae28-44b40057d280
---

크롤러 → Kafka → MongoDB 적재 파이프라인 + 프론트 UI + 백엔드 성능개선 전부 완료.
이번 세션에서 인기순 정렬 정확도, 카테고리 동적화, 데이터 오염 수정까지 추가 완료.

## 완료된 전체 작업

### 파이프라인 (커밋 7a1c995)
- 크롤러 → Kafka producer → consumer → MongoDB 적재 e2e 완료

### 프론트엔드 + 백엔드 (커밋 b5186ba)
- 다크 네이비 테마, 사이드바 카테고리, 상단 탭 네비
- Redis TTL 300초, $facet 집계, pre-warm 등 성능 개선

### 인기순 정렬 정확도 개선 (2026-06-09, 미커밋)
- `Crawler/rank_updater.py` 전면 재작성
  - 카테고리별 루프 → **전체 판매량순(sorted_type=1) 페이지 파라미터 순회**로 변경
  - `page=1,2,3...&per_page=96` 방식 — 빈 페이지 나올 때까지 전부 수집
  - 실행 시 기존 rank 전체 초기화 후 새 순위 입력 (구방식 중복 1위 문제 해결)
  - 페이지 수집 즉시 MongoDB 업데이트 (배치 X)
  - best: 1,356건(15페이지), sales: 8,295건(87페이지)
  - `MAX_PAGES=0` = 제한 없음 (환경변수로 조절 가능)
- `Backend/product/servicer.py` rank 정렬 수정
  - null rank 상품은 `$ifNull` → 999999 처리해 순위 있는 상품 뒤로 밀림

### 카테고리 동적화 (2026-06-09, 미커밋)
- `Crawler/category_crawler.py` 신규: Kurly 필터 API → MongoDB categories 컬렉션
- `Backend/proto/product.proto`: `ListCategories` RPC 추가, proto 재생성
- `Backend/product/servicer.py`: `ListCategories` — products.distinct로 실제 크롤된 카테고리만 반환
  - target="" (전체 탭) → best+sales 합집합, code 기준 중복 제거
- `Backend/gateway/routers/categories.py` 신규: `/categories?target=` REST 엔드포인트
- `Frontend/src/api.js`: `fetchCategories(target="")` 추가
- `Frontend/src/pages/ProductList.jsx`: target 변경 시 카테고리 동적 재조회

### 전통주 오염 수정 (2026-06-09, 미커밋)
- `Crawler/pages.py`: `SALES_FOOD_CATEGORIES` — sales에서 전통주(251) 제외
- `Kafka/mongo_loader.py`: `category_code/name`을 `$setOnInsert`로 변경 (재크롤 시 덮어쓰기 방지)
- MongoDB에서 오염된 전통주 문서 5건 수동 삭제

### 전체 탭 인기순 제거 (2026-06-09, 미커밋)
- `Frontend/src/pages/ProductList.jsx`: 전체 탭에서 인기순 옵션 숨김, 전체→다른 탭 이동 시 자동 초기화

## 현재 크롤러 목록
| 파일 | 역할 | 실행방식 |
|------|------|---------|
| `Crawler/main.py` | 상품 목록+상세 전체 수집 → Kafka | CRAWL_TARGET=best/sales |
| `Crawler/rank_updater.py` | 판매량순 순위만 수집 → MongoDB 직접 | CRAWL_TARGET=best/sales |
| `Crawler/category_crawler.py` | 카테고리 목록 수집 → MongoDB | 대상 없음(best+sales 동시) |

## 카테고리 코드 (실제 Kurly 기준)
채소(907), 과일·견과·쌀(908), 수산·해산·건어물(909), 정육·가공육·달걀(910),
국·반찬·메인요리(911), 간편식·밀키트·샐러드(912), 면·양념·오일(913), 생수·음료(914),
커피·차(383), 간식·과자·떡(249), 베이커리(915), 유제품(018), 건강식품(032),
와인·위스키·데낄라(722), 전통주(251) — sales에는 전통주 없음

**How to apply**: 다음 작업은 k8s 매니페스트(CronJob 3개, Deployment, ConfigMap) 및 Dockerfile 작성.
Dockerfile은 기능 구현 완료 후 사용자 요청 시에만 작성할 것 ([[dev-environment-and-deploy]]).
미커밋 변경사항 많음 — git commit/push 필요.
