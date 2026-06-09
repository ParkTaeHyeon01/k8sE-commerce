---
name: crawler-multi-instance-plan
description: 크롤러 베스트/할인 분리 운영 — .env 환경변수 기반 단일 크롤러로 구현 완료 (커밋 e91f4b8), k8s CronJob 2개로 운영 예정
metadata:
  node_type: memory
  type: project
  originSessionId: 4e827445-bbda-4abd-bc52-9e363a20499a
---

크롤러를 "베스트용"과 "할인용"으로 나눠 운영하는 구조를 **구현 완료함** (2026-06-08, 커밋 `e91f4b8`, 푸시됨).

## 구현된 내용
- `Crawler/main.py`/`pages.py`: `CRAWL_TARGET` 환경변수(`best`/`sales`)로 컬렉션 선택, 코드/이미지 복제 없이 단일 크롤러로 동작
- **환경변수는 `.env` 파일에서 중앙 관리** — `python-dotenv`로 로드 (`Crawler/.env`는 gitignore, `Crawler/.env.example`로 키 구조만 공유). "로컬은 `.env`, k8s에서는 ConfigMap/Secret으로 같은 키 주입" 방식 (사용자 명시 선호)
- 추가로 식품 카테고리 15개 전체를 `filters=category:{코드}` 파라미터로 순회 수집하도록 확장 (아래 [[crawler-target-kurly]] 참고)
- k8s에서는 같은 이미지로 **CronJob 2개를 다른 설정(`CRAWL_TARGET`)·스케줄로 운영** 예정 — "같은 이미지로 여러 작업을 스케줄링"하는 모습을 보여줄 수 있어 k8s CI/CD 데모 취지([[project-scope-and-role]])에 잘 맞음

**Why**: 사용자가 "크롤러를 여러 개 만들 수 있는지" 물었고, 베스트/할인을 따로 운영하고 싶어함. 완전히 분리된 코드보다 설정 주입형 단일 코드가 MVP 단순성 원칙에 맞음. 이후 "환경변수는 env 파일로 한곳에서 컨트롤"하자는 요구가 추가되어 `.env`+`python-dotenv` 방식으로 구체화됨.

**How to apply**: 이제 구현 완료 상태이므로, 다음 단계는 (1) k8s CronJob 매니페스트 작성 시 `CRAWL_TARGET` 값을 다르게 주입하는 방식 적용, (2) Kafka producer 재구현 시에도 같은 `.env` 패턴 유지. `Crawler/.env.example`을 보면 현재 어떤 키가 필요한지 바로 확인 가능.
