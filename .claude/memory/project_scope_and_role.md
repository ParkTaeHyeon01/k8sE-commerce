---
name: project-scope-and-role
description: k8sE-commerce 프로젝트의 전체 성격(k8s CI/CD 시연 중심)과 사용자의 담당 영역(개발 + data)
metadata: 
  node_type: memory
  type: project
  originSessionId: 4e827445-bbda-4abd-bc52-9e363a20499a
---

이 프로젝트는 강사가 제시한 "k8s - CI/CD project Tech Stack" 과제로, **애플리케이션 기능 자체보다 k8s 기반 CI/CD 파이프라인 구축과 시연이 메인 목표**다.

## 강사 지침 핵심
- 애플리케이션 개발은 최소화: API를 "보여주기" 수준으로만 구현
- 파이프라인 구축 → 시연이 필수 (발표는 짧게, 데모 중심)
- 계층 구조: SaaS(GitLab+ArgoCD 후보) → PaaS(k8s) → IaaS(AWS)
- 역할 분리: k8s infra 설계, CI/CD, 보안/네트워크, 개발, 모니터링(observability), 부하테스트(k6/카오스엔지니어링), **data(DB, Kafka, Redis, crawling)**
- 산출물: 워크북(.doc/노션)

## 사용자 담당 영역
**개발 + data(DB, Kafka, Redis, crawling)** — 즉 이 대화의 작업 범위(크롤러, Kafka, MariaDB/MongoDB, Redis, FastAPI 백엔드)는 모두 사용자의 직접 담당 영역이다.

**크롤링 대상 (2026-06-08 변경, 중요)**: 처음엔 쿠팡/G마켓을 검토했으나 **마켓컬리(Kurly)로 최종 변경**함. 자세한 구조와 이유는 [[crawler-target-kurly]] 참고. 과거 세션 메모에 "쿠팡/G마켓 크롤러"라는 표현이 남아있다면 모두 마켓컬리 기준으로 갱신된 것으로 이해할 것.

**Why**: 강사가 전체 발표 구조를 짜면서 각 팀원에게 영역을 배분했고, 사용자는 데이터 파이프라인과 개발을 맡음.

**How to apply**: 앞으로 크롤러/DB/Kafka/Redis/백엔드 작업을 설계할 때 "정교함"보다 **"데모에서 안정적으로 파이프라인 흐름을 보여줄 수 있는 최소 구성"**을 우선시할 것. 과도한 기능 추가나 추상화는 지양.
