---
name: docker-k8s-progress
description: "Docker 이미지 빌드 및 k8s 수동 배포 준비 현황 — Dockerfile 7개 + ConfigMap/Secret 완료, Deployment/Service YAML 미작성"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4e827445-bbda-4abd-bc52-9e363a20499a
---

## 현재 상태 (2026-06-10)

### 완료
- `docker/` 디렉터리: 서비스별 Dockerfile + `.dockerignore` 작성 완료
  - frontend (멀티스테이지: node:22-alpine 빌드 → nginx:alpine 서빙, nginx.conf SPA 라우팅 포함)
  - gateway (uvicorn :8000)
  - product (gRPC :50051)
  - auth-member (gRPC :50052)
  - payment (gRPC :50053)
  - crawler (playwright chromium 포함)
  - kafka-consumer
- `k8s/` 디렉터리: ConfigMap/Secret YAML 작성 완료
  - `configmap.yaml`: 공통 설정 (Kafka, Redis, gRPC 주소, MariaDB 호스트 등) — localhost → k8s svc 이름으로 변경
  - `configmap-crawler.yaml`: best/sales 크롤러 인스턴스별 분리
  - `secret.yaml`: MONGODB_URI, MARIADB_PASSWORD, JWT_SECRET (CHANGE_ME placeholder)

### 미완료 (수동 배포까지 필요한 것)
- Docker Desktop 미설치 → 이미지 빌드 불가
- k8s Deployment / Service YAML 없음
- 인프라 k8s 설치 계획 없음 (MongoDB, MariaDB, Redis, Kafka)
- k8s 클러스터 확인 필요

## 핵심 결정

- **CI/CD는 나중에 GitLab으로**: 지금은 수동 빌드 & 수동 `kubectl apply` 방식
- **docker/, k8s/ 디렉터리는 git에 포함**: CI/CD에서 참조하므로 .gitignore 제외
- **secret.yaml은 CHANGE_ME placeholder로 git에 포함**: 실제 값은 배포 시 직접 수정
- **frontend VITE_API_BASE**: 빌드 타임 ARG로 주입 (`docker build --build-arg VITE_API_BASE=...`)
- **환경변수 주입 방식**: `envFrom: configMapRef + secretRef`로 모든 서비스 주입

## 수동 배포 순서
1. Docker Desktop 설치
2. `docker build` → 이미지 7개 빌드
3. `docker push` → 레지스트리 (DockerHub 등)
4. k8s Deployment/Service YAML 작성
5. `kubectl apply -f k8s/`

**Why**: CI/CD 준비가 안 된 상태에서 k8s 배포를 먼저 검증하기 위해 수동 방식 선택.
**How to apply**: Dockerfile 빌드 전 Docker Desktop 설치 필요 여부 항상 확인. [[dev-environment-and-deploy]]
