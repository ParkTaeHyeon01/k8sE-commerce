---
name: docker-k8s-progress
description: "Docker 이미지 빌드 및 k8s 수동 배포 준비 현황 — Dockerfile 7개 + ConfigMap/Secret + infra YAML 완료, Deployment/Service YAML 미작성"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4e827445-bbda-4abd-bc52-9e363a20499a
---

## 현재 상태 (2026-06-12)

### 완료
- `docker/` 디렉터리: 서비스별 Dockerfile + `.dockerignore` 작성 완료
- `k8s/` 디렉터리 구조 개편 완료
  - `k8s/namespaces.yaml`: 9개 네임스페이스
  - `k8s/apps/{service}/`: ConfigMap + Secret (서비스별 namespace + FQDN 적용)
  - `k8s/infra/mariadb.yaml`: StatefulSet + Headless Service + Secret
  - `k8s/infra/mongodb.yaml`: MongoDBCommunity (SCRAM 인증 + 3대)
  - `k8s/infra/redis.yaml`: RedisReplication (3대)
  - `k8s/istio/authpolicy/`, `k8s/netpol/`, `k8s/sealed-secrets/` 폴더 생성
- Redis 읽기/쓰기 분리 완료
  - REDIS_WRITE_URL (redis-svc-master), REDIS_READ_URL (redis-svc-follower)
  - 코드: product/db.py, gateway/cart.py, gateway/purchase.py, kafka-consumer/main.py
- MongoDB URI readPreference=secondaryPreferred 추가 (gateway, product secret)
- Sealed Secrets 도입 결정 (기존 secret → SealedSecret으로 전환 예정)
- **namespaces.yaml 클러스터 적용 완료** (2026-06-12) — 9개 ns 모두 Active

### 네임스페이스 구조
```
frontend-ns       → frontend
gateway-ns        → gateway
backend-ns        → product, auth-member, payment
kafka-consumer-ns → kafka-consumer
crawler-ns        → crawler
kafka-ns          → kafka broker (인프라)
mariadb-ns        → mariadb
mongodb-ns        → mongodb
redis-ns          → redis
```

### 미완료
- MongoDB Community Operator 설치 (Helm)
- Redis OT Operator 설치 (Helm)
- k8s/infra/ YAML 적용 (mariadb, mongodb, redis)
- k8s Deployment / Service YAML (3단계)
- HPA YAML (4단계)
- Istio Gateway / HTTPRoute YAML (5단계)
- NetworkPolicy YAML
- Sealed Secrets 실제 암호화 (클러스터 구성 후)
- Docker 이미지 빌드 (Docker Desktop 미설치)

### 클러스터 상태 (2026-06-12 확인)
- master 1 + worker 3 (총 4대), k8s 1.31.9, Ubuntu 24.04
- Calico ✅, MetalLB ✅ (IPAddressPool 미설정), metrics-server ✅
- Longhorn ✅, Istio ✅, MinIO ✅, Velero ✅, monitoring ✅
- MongoDB Operator ❌, Redis Operator ❌
- 팀원이 k8s 인프라 구성 담당

## 핵심 결정
- **Sealed Secrets** (Bitnami): Secret 암호화, git 커밋 가능
- **Redis 읽기/쓰기 분리**: master(쓰기) / follower(읽기)
- **MongoDB readPreference**: secondaryPreferred (Secondary 우선 읽기)
- **MariaDB**: StatefulSet 직접 작성 (단일 인스턴스, Operator 불필요)
- **MongoDB**: Community Operator + SCRAM 인증 + 3대 ReplicaSet
- **Redis**: OT Operator + RedisReplication 3대
- **네임스페이스**: 역할별 분리, backend-ns에 product/auth-member/payment 통합

**Why**: k8s 수동 배포 후 CI/CD(GitLab) 연동 예정.
**How to apply**: 팀원 클러스터 구성 완료 후 Sealed Secrets 암호화 → kubectl apply 순서로 진행.
