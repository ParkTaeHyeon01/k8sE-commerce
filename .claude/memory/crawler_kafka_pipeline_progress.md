---
name: crawler-kafka-pipeline-progress
description: "크롤링→Kafka→MongoDB 파이프라인 + 인기순/카테고리/전통주/회원관리까지 완료 (커밋 9a27c3c, 2026-06-10)"
metadata:
  node_type: memory
  type: project
  originSessionId: 51a360da-2793-4782-ae28-44b40057d280
---

커밋 9a27c3c 기준 전체 구현 완료.

## 완료된 전체 작업

### 파이프라인 (커밋 7a1c995)
- 크롤러 → Kafka producer → consumer → MongoDB 적재 e2e 완료

### 프론트엔드 + 백엔드 (커밋 b5186ba)
- 다크 네이비 테마, 사이드바 카테고리, 상단 탭 네비
- Redis TTL 300초, $facet 집계, pre-warm 등 성능 개선

### 인기순 정렬 정확도 개선
- `Crawler/rank_updater.py`: 전체 판매량순 페이지 순회 방식, best_rank/sales_rank 독립 관리
- `mongo_loader.py`에서 rank 저장 제거 — rank_updater 독립 운영
- null rank → $ifNull 999999 처리 (순위 없는 상품 뒤로)

### 카테고리 동적화
- `Crawler/category_crawler.py`: Kurly 필터 API → MongoDB categories 컬렉션
- `Crawler/main.py`: 상품 크롤러가 MongoDB categories에서 카테고리 동적 로드 (폴백 하드코딩)
- 식품 카테고리만 필터링 (FOOD_CATEGORY_CODES 기준)
- `Backend/product/servicer.py` ListCategories: 상품 없어도 카테고리 표시, 가나다순 정렬

### 전통주 처리
- best에만 있는 전통주(251) 정상 분리 — SALES_FOOD_CATEGORIES에서 제외
- 상세페이지 로그인 필요 상품: LoginRequiredError → detail_blocks=[], status=ready

### 회원 탈퇴/정지 구분 (커밋 9a27c3c)
- DB: users.deactivated_by VARCHAR(10) 컬럼 추가
- proto: WithdrawUser, AdminRestoreUser RPC 추가, UserSummary.deactivated_by 필드
- 일반 탈퇴(deactivated_by='user'): 재활성화 불가
- 관리자 정지(deactivated_by='admin'): AdminRestoreUser로 복구 가능
- 로그인 메시지 분기: "탈퇴한 계정" vs "관리자에 의해 정지된 계정"
- Admin.jsx: 정지/탈퇴 뱃지 구분, 정지 해제 버튼 (admin 정지만)
- MyPage.jsx: 회원 탈퇴 버튼 추가

### UI 안정화 (커밋 9a27c3c)
- 상품 카드: flex-direction:column + card-body flex:1 → 품절/재고 상관없이 카드 높이 통일
- 어드민 버튼: width:88px 고정 → 텍스트 길이 달라도 레이아웃 불변
- MyPage 버튼: mypage-actions 컨테이너, 로그아웃/탈퇴 구분 스타일

## 현재 크롤러 목록
| 파일 | 역할 | 실행방식 |
|------|------|---------|
| `Crawler/main.py` | 상품 목록+상세 전체 수집 → Kafka | CRAWL_TARGET=best/sales |
| `Crawler/rank_updater.py` | 판매량순 순위만 수집 → MongoDB 직접 | CRAWL_TARGET=best/sales |
| `Crawler/category_crawler.py` | 카테고리 목록 수집 → MongoDB | best+sales 동시 |

## 다음 작업 후보
- k8s 매니페스트 (CronJob 3개, Deployment, ConfigMap, Secret)
- Dockerfile 작성 (기능 구현 완료됐으므로 가능)
- k6 부하테스트 시나리오 구현

**How to apply**: Dockerfile/k8s는 사용자 요청 시에만 작성.
