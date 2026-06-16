# k8sE-commerce 워크북

마켓컬리 인기/할인 상품을 크롤링해 보여주는 쇼핑몰 서비스.  
k8s CI/CD 시연을 목적으로 한 MSA 구조의 MVP 프로젝트.

---

## 목차

1. [아키텍처](#1-아키텍처)
2. [환경 설정](#2-환경-설정)
3. [환경변수](#3-환경변수)
4. [크롤러](#4-크롤러)
5. [Kafka Consumer](#5-kafka-consumer)
6. [백엔드](#6-백엔드)
7. [프론트엔드](#7-프론트엔드)
8. [전체 실행 순서](#8-전체-실행-순서)
9. [k8s 배포](#9-k8s-배포)
10. [운영 이슈 & 트러블슈팅](#10-운영-이슈--트러블슈팅)
11. [API 명세서](api-spec.md)

---

## 1. 아키텍처

### 전체 흐름

```
[마켓컬리]
    │  Playwright 크롤링
    ▼
[Crawler] ──Kafka Producer──▶ [Kafka Broker] ──Consumer──▶ [Kafka Consumer]
                                                                    │
[rank_updater] ─────────────────────────────────────────────────▶  │ → MongoDB
[category_crawler] ──────────────────────────────────────────────▶ │ → MongoDB
                                                                    ▼
                                                              [MongoDB]
                                                                    │
                                                       [Product gRPC 서버 :50051]
                                                                    │ gRPC
                                        [Auth-Member gRPC 서버 :50052] ─── [MariaDB]
                                        [Payment gRPC 서버 :50053]   ─── (MariaDB/포인트)
                                                                    │
                                                       [Gateway FastAPI :8000]
                                                                    │ REST/JSON
                                                       [Frontend React :5173]
```

### 기술 스택

| 레이어 | 기술 | 역할 |
|--------|------|------|
| 크롤러 | Python + Playwright | 마켓컬리 상품 수집 |
| 메시지 큐 | Apache Kafka (KRaft) | 크롤러 → 적재 파이프라인 |
| 상품 DB | MongoDB | 크롤링 상품 데이터 (스키마 유동적) |
| 회원 DB | MariaDB | 회원/인증/포인트 (정합성 필요) |
| 캐시 | Redis | API 응답 캐시 |
| 백엔드 통신 | gRPC | 서비스 간 내부 통신 |
| API Gateway | FastAPI | REST → gRPC 변환 (BFF) |
| 프론트엔드 | React + Vite | 상품 목록/상세 UI |
| 인프라 | Kubernetes + GitLab CI | 컨테이너 오케스트레이션 + CI/CD |
| 스토리지 | Longhorn | k8s 퍼시스턴트 볼륨 (3-replica) |
| 서비스 메시 | Istio | 트래픽 제어, mTLS, 진입 게이트웨이 |

### 서비스 구성

**Crawler (3종류)**

| 파일 | 역할 | 소요시간 |
|------|------|---------|
| `main.py` | 상품 목록 + 상세 전체 수집 → Kafka | ~4시간 |
| `rank_updater.py` | 판매량순 순위만 수집 → MongoDB | ~10분 |
| `category_crawler.py` | 카테고리 목록 수집 → MongoDB | ~5초 |

**Backend**

| 서비스 | 포트 | DB |
|--------|------|----|
| product gRPC 서버 | 50051 | MongoDB |
| auth-member gRPC 서버 | 50052 | MariaDB |
| payment gRPC 서버 | 50053 | MariaDB (포인트 차감) |
| gateway FastAPI | 8000 | - (gRPC 경유, Redis 캐시) |

**크롤 대상**
- **베스트(best)**: `kurly.com/collection-groups/market-best`
- **할인(sales)**: `kurly.com/collection-groups/market-sales-group`
- 수집 카테고리: 채소, 과일·견과·쌀, 수산·해산·건어물, 정육·가공육·달걀, 국·반찬·메인요리, 간편식·밀키트·샐러드, 면·양념·오일, 생수·음료, 커피·차, 간식·과자·떡, 베이커리, 유제품, 건강식품, 와인·위스키·데낄라, 전통주(베스트만)

### 왜 두 DB를 쓰는가?
- **MongoDB**: 상품 데이터는 카테고리마다 필드가 조금씩 달라 스키마가 유동적 → Document DB 적합
- **MariaDB**: 회원/포인트는 트랜잭션과 정합성이 중요 → RDBMS 적합

---

## 2. 환경 설정

### Python 3.11+

```bash
python --version
```

### Node.js 18+

```bash
node --version
npm --version
```

### Kafka (KRaft 모드 — Zookeeper 없음)

> Kafka 4.x부터 KRaft 전용. Zookeeper 설정 필요 없음.

**설치**
1. [kafka.apache.org](https://kafka.apache.org/downloads) 에서 다운로드
2. `C:\kafka`에 압축 해제

**초기 설정 (최초 1회)**
```powershell
# Cluster ID 생성
C:\kafka\bin\windows\kafka-storage.bat random-uuid
# 출력된 UUID를 아래 명령에 사용

C:\kafka\bin\windows\kafka-storage.bat format `
  -t <위에서-나온-UUID> `
  -c C:\kafka\config\kraft\server.properties
```

**실행**
```powershell
C:\kafka\bin\windows\kafka-server-start.bat C:\kafka\config\kraft\server.properties
```

**토픽 생성 (최초 1회)**
```powershell
C:\kafka\bin\windows\kafka-topics.bat `
  --create --topic crawled-products `
  --bootstrap-server localhost:9092 `
  --partitions 1 --replication-factor 1
```

### MongoDB (WSL2)

```bash
# WSL2 터미널에서
sudo systemctl start mongod
sudo systemctl status mongod  # 상태 확인
```

### Redis

```powershell
# Windows
redis-server
```

```bash
# 또는 WSL2에서
sudo service redis-server start
```

### MariaDB

```powershell
# Windows 서비스
Start-Service -Name "MariaDB"
```

### Python 패키지 설치

```powershell
cd Crawler
pip install -r requirements.txt
playwright install chromium

cd ..\Kafka
pip install -r requirements.txt

cd ..\Backend\product
pip install -r requirements.txt

cd ..\gateway
pip install -r requirements.txt
```

### Frontend

```powershell
cd Frontend
npm install
```

---

## 3. 환경변수

### 루트 `.env` (백엔드 전체 공통)

`.env.example`을 복사해서 생성:

```powershell
cp .env.example .env
```

```env
# 수집 대상: best(베스트) 또는 sales(할인)
CRAWL_TARGET=best

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_PRODUCT_TOPIC=crawled-products
KAFKA_CONSUMER_GROUP=product-loader

# MongoDB
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=ecommerce

# Redis (로컬 개발: 읽기/쓰기 동일 서버 사용)
REDIS_WRITE_URL=redis://localhost:6379/0
REDIS_READ_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=60

# Product gRPC 서버
PRODUCT_GRPC_PORT=50051

# Gateway
PRODUCT_GRPC_ADDR=localhost:50051
CORS_ORIGINS=http://localhost:5173
```

> MongoDB 인증이 있는 경우:  
> `MONGODB_URI=mongodb://admin:k8spass%23@localhost:27017/?authSource=admin`  
> (`#` → `%23` URL 인코딩)

### `Frontend/.env`

```env
VITE_API_BASE=http://localhost:8000
```

### 파일 구조

```
k8sE-commerce/
├── .env              ← 백엔드 전체 공통 (Crawler, Kafka, Backend 모두 이 파일 읽음)
├── .env.example      ← 예시 파일 (git 추적됨)
└── Frontend/
    └── .env          ← Vite 전용 (VITE_API_BASE)
```

---

## 4. 크롤러

### 상품 크롤러 (`main.py`)

마켓컬리 상품 목록 + 상세페이지를 수집해 Kafka로 전송.

```powershell
cd Crawler

# 베스트 상품 수집
$env:CRAWL_TARGET="best"
python main.py

# 할인 상품 수집
$env:CRAWL_TARGET="sales"
python main.py
```

> **소요시간**: 카테고리 15개 × 상품 ~100건 × 상세페이지 수집 → 약 3~4시간  
> **중단 후 재시작 안전**: product_id 기준 upsert라 중복 없음

**동작 흐름**
```
카테고리 목록 순회
  └─▶ 목록 페이지 스크롤 → 상품 카드 파싱
        └─▶ 각 상품 상세페이지 방문 → 상세 이미지 수집
              └─▶ Kafka로 전송 (status="ready")
              └─▶ 실패 시 status="draft"로 전송 (다음 크롤링 때 재시도)
크롤링 완료 후 sync 메시지 전송 (목록에서 빠진 상품 targets에서 제거)
```

### 순위 업데이터 (`rank_updater.py`)

판매량순(sorted_type=1) 페이지를 순회해 `best_rank` / `sales_rank` 갱신.  
상세페이지 방문 없어 빠름.

```powershell
cd Crawler

$env:CRAWL_TARGET="best"
python rank_updater.py

$env:CRAWL_TARGET="sales"
python rank_updater.py
```

> **소요시간**: 약 5~10분  
> **동작**: 실행마다 기존 순위 전체 초기화 → 새 순위 입력  
> **수집량**: 96개/페이지, 마지막 페이지까지 자동 순회 (best ~1,356건, sales ~8,295건)

### 카테고리 크롤러 (`category_crawler.py`)

마켓컬리 필터 API에서 카테고리 목록을 가져와 MongoDB `categories` 컬렉션에 저장.  
Playwright 불필요 — 매우 빠름.

```powershell
cd Crawler
python category_crawler.py
```

> **소요시간**: 약 5초  
> **결과**: 베스트 ~30개, 할인 ~25개 (비식품 포함 전체)

---

## 5. Kafka Consumer

크롤러가 Kafka에 보낸 상품 데이터를 읽어 MongoDB에 저장하는 컨슈머.  
크롤러와 **동시에** 실행해야 한다.

```powershell
cd Kafka
python main.py
```

### 동작 흐름

```
Kafka 토픽(crawled-products) 구독
  └─▶ 상품 메시지 수신
        └─▶ MongoDB products 컬렉션에 upsert
              - product_id 기준 중복 없음
              - targets 배열에 best/sales 누적 ($addToSet)
              - category_code/name은 최초 저장 후 유지 ($setOnInsert)

  └─▶ sync 메시지 수신 (크롤링 완료 신호)
        └─▶ 이번 크롤링에서 안 보인 상품 → targets에서 해당 target 제거
        └─▶ Redis 캐시 전체 삭제 (새 데이터 즉시 반영)
```

### MongoDB 상품 도큐먼트 구조

```json
{
  "product_id": "12345678",
  "name": "상품명",
  "sale_price": 9900,
  "original_price": 12000,
  "discount_rate": 17,
  "image_url": "https://...",
  "detail_url": "https://kurly.com/goods/12345678",
  "category_code": "907",
  "category_name": "채소",
  "targets": ["best", "sales"],
  "status": "ready",
  "best_rank": 5,
  "sales_rank": 12,
  "detail_blocks": [
    { "type": "image", "value": "https://..." }
  ],
  "crawled_at": "2026-06-09T12:00:00Z"
}
```

**status 필드**
- `ready`: 상세페이지 수집 완료 → 서비스에 노출
- `draft`: 상세페이지 수집 실패 → 숨김, 다음 크롤링 때 재시도

---

## 6. 백엔드

```
Backend/
├── proto/                 ← gRPC 인터페이스 정의 (.proto)
├── product/               ← gRPC 서버 (MongoDB 조회)
├── auth-member/           ← gRPC 서버 (회원/포인트/주문, MariaDB)
├── payment/               ← gRPC 서버 (결제/포인트 차감, MariaDB)
└── gateway/               ← FastAPI REST API (gRPC 호출 후 JSON 반환)
```

### Product gRPC 서버

```powershell
cd Backend/product
python main.py
```

- 포트: **50051**
- 제공 RPC: `ListProducts`, `GetProduct`, `ListCategories`, `UpdateStock`, `DeleteProduct`

### Auth-Member gRPC 서버

```powershell
cd Backend/auth-member
python main.py
```

- 포트: **50052**
- 제공 RPC: `Register`, `Login`, `GetMe`, `GetPoints`, `GetOrders`, `GetAddresses`, `AddAddress`, `SetDefaultAddress`, `DeleteAddress`, `WithdrawUser`
- 관리자 RPC: `AdminListUsers`, `AdminAdjustPoints`, `AdminSetAdmin`, `AdminDeleteUser`, `AdminRestoreUser`, `AdminGetAllOrders`
- 시작 시 MariaDB 테이블 자동 생성 + 관리자 계정 시드

### Payment gRPC 서버

```powershell
cd Backend/payment
python main.py
```

- 포트: **50053**
- 제공 RPC: `Checkout` (포인트 차감 + 주문 생성), `CancelOrder` (포인트 환불)

### Gateway FastAPI

```powershell
cd Backend/gateway
python -m uvicorn main:app --port 8000
```

- 포트: **8000**
- Swagger 문서: `http://localhost:8000/docs`
- 장바구니는 Redis에 직접 저장 (TTL 7일)

**라우터 구성**

| prefix | 설명 |
|--------|------|
| `/auth` | 회원가입 · 로그인 |
| `/me` | 내 정보 · 포인트 · 주문내역 · 배송지 |
| `/products` | 상품 목록 · 상세 · 자동완성 |
| `/categories` | 카테고리 목록 |
| `/cart` | 장바구니 (Redis) |
| `/cart/checkout` | 포인트 결제 |
| `/orders/{id}/cancel` | 주문 취소 |
| `/admin` | 관리자 전용 (상품·회원·주문 관리) |

> 전체 엔드포인트는 [API 명세서](api-spec.md) 참고

### Proto 재생성 (proto 수정 시)

```powershell
cd Backend
python -m grpc_tools.protoc -I proto --python_out=product --grpc_python_out=product proto/product.proto
python -m grpc_tools.protoc -I proto --python_out=gateway --grpc_python_out=gateway proto/product.proto
python -m grpc_tools.protoc -I proto --python_out=auth-member --grpc_python_out=auth-member proto/auth.proto
python -m grpc_tools.protoc -I proto --python_out=gateway --grpc_python_out=gateway proto/auth.proto
python -m grpc_tools.protoc -I proto --python_out=payment --grpc_python_out=payment proto/payment.proto
python -m grpc_tools.protoc -I proto --python_out=gateway --grpc_python_out=gateway proto/payment.proto
```

---

## 7. 프론트엔드

React + Vite 기반 쇼핑몰 UI.

```powershell
cd Frontend
npm install   # 최초 1회
npm run dev
```

브라우저에서 `http://localhost:5173` 접속.

### 화면 구성

| 경로 | 화면 | 설명 |
|------|------|------|
| `/` | 홈 | 카테고리 카드 목록 |
| `/products` | 상품 목록 | 탭(전체/베스트/할인) + 사이드바 카테고리 + 정렬 |
| `/products/:id` | 상품 상세 | 이미지, 가격, 상세 블록 |

### 상품 목록 기능

- **탭**: 전체 / 베스트 / 할인 전환
- **카테고리**: 탭에 따라 동적으로 로드 (마켓컬리 카테고리 기반)
- **정렬**: 기본순 / 인기순(베스트·할인 탭만) / 낮은 가격순 / 높은 가격순 / 할인율 높은순

---

## 8. 전체 실행 순서

### 최초 세팅 (데이터 없는 경우)

**Step 1. 인프라 시작** — 각각 별도 터미널

```powershell
# Kafka
C:\kafka\bin\windows\kafka-server-start.bat C:\kafka\config\kraft\server.properties
```
```bash
# MongoDB (WSL2)
sudo systemctl start mongod
```
```powershell
# Redis
redis-server

# MariaDB
Start-Service -Name "MariaDB"
```

**Step 2. 환경변수 설정**

```powershell
cp .env.example .env
```

**Step 3. Kafka Consumer 시작**

```powershell
cd Kafka
python main.py
```

**Step 4. 카테고리 수집**

```powershell
cd Crawler
python category_crawler.py
```

**Step 5. 상품 크롤링** — 터미널 2개에서 동시 실행

```powershell
# 터미널 1
cd Crawler; $env:CRAWL_TARGET="best"; python main.py

# 터미널 2
cd Crawler; $env:CRAWL_TARGET="sales"; python main.py
```

**Step 6. 순위 업데이트** — 크롤링 완료 후

```powershell
cd Crawler
$env:CRAWL_TARGET="best";  python rank_updater.py
$env:CRAWL_TARGET="sales"; python rank_updater.py
```

**Step 7. 백엔드 서버 시작**

```powershell
# 터미널 1
cd Backend/product; python main.py

# 터미널 2
cd Backend/auth-member; python main.py

# 터미널 3
cd Backend/payment; python main.py

# 터미널 4
cd Backend/gateway; python -m uvicorn main:app --port 8000
```

**Step 8. 프론트엔드**

```powershell
cd Frontend; npm run dev
```

`http://localhost:5173` 접속.

---

### 재시작 (데이터 있는 경우)

```
1. Kafka / MongoDB / Redis / MariaDB 시작
2. cd Kafka              → python main.py
3. cd Backend/product    → python main.py
4. cd Backend/auth-member → python main.py
5. cd Backend/payment    → python main.py
6. cd Backend/gateway    → python -m uvicorn main:app --port 8000
7. cd Frontend           → npm run dev
```

### 포트 요약

| 서비스 | 포트 |
|--------|------|
| Kafka | 9092 |
| MongoDB | 27017 |
| Redis | 6379 |
| MariaDB | 3306 |
| Product gRPC | 50051 |
| Auth-Member gRPC | 50052 |
| Payment gRPC | 50053 |
| Gateway REST | 8000 |
| Frontend | 5173 |

---

## 9. k8s 배포

### 클러스터 구성

| 구성 | 내용 |
|------|------|
| 노드 | master 1 + worker 3 (총 4대) |
| k8s 버전 | 1.31.9 |
| OS | Ubuntu 24.04 |
| CNI | Calico |
| LoadBalancer | MetalLB |
| 스토리지 | Longhorn |
| 서비스 메시 | Istio |
| 백업 | Velero + MinIO |

### 네임스페이스 구조

```
frontend-ns       → Frontend (React)
gateway-ns        → Gateway (FastAPI)
backend-ns        → product / auth-member / payment gRPC 서버
kafka-consumer-ns → Kafka Consumer
crawler-ns        → Crawler (CronJob)
kafka-ns          → Kafka Broker (인프라)
mariadb-ns        → MariaDB
mongodb-ns        → MongoDB
redis-ns          → Redis
```

### Step 1. 네임스페이스 생성

```bash
kubectl apply -f k8s/namespaces.yaml
kubectl get ns
```

### Step 2. MongoDB Operator 설치

> 기존 `community-operator` 차트는 deprecated. 신규 통합 차트 `mongodb-kubernetes` 사용.

```bash
helm repo add mongodb https://mongodb.github.io/helm-charts
helm repo update
helm upgrade --install mongodb-kubernetes-operator mongodb/mongodb-kubernetes \
  --namespace mongodb-ns
```

설치 확인:
```bash
kubectl get pods -n mongodb-ns
```

### Step 3. Redis OT Operator 설치

> Operator Pod는 `ot-operators` 네임스페이스에 설치. 실제 Redis는 `redis-ns`에 배포.

```bash
helm repo add ot-helm https://ot-container-kit.github.io/helm-charts
helm repo update
helm upgrade redis-operator ot-helm/redis-operator \
  --install --namespace ot-operators
```

설치 확인:
```bash
kubectl get pods -n ot-operators
```

### Step 3-1. Kafka (Strimzi) Operator 설치

> KRaft 모드 지원. Operator Pod는 `kafka-ns`에 설치.

```bash
helm repo add strimzi https://strimzi.io/charts/
helm repo update
helm upgrade --install strimzi strimzi/strimzi-kafka-operator \
  --namespace kafka-ns
```

설치 확인:
```bash
kubectl get pods -n kafka-ns
```

### Step 3-2. Sealed Secrets 설치

> Secret 암호화 도구. `kube-system`에 설치, `fullnameOverride` 필수 (kubeseal CLI 연동).

```bash
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm repo update
helm install sealed-secrets -n kube-system \
  --set-string fullnameOverride=sealed-secrets-controller \
  sealed-secrets/sealed-secrets
```

설치 확인:
```bash
kubectl get pods -n kube-system | grep sealed
```

### Step 4. DB 인프라 적용

```bash
kubectl apply -f k8s/infra/mariadb.yaml
kubectl apply -f k8s/infra/mongodb.yaml
kubectl apply -f k8s/infra/redis.yaml
```

상태 확인:
```bash
# MariaDB
kubectl get statefulset -n mariadb-ns
kubectl get pvc -n mariadb-ns

# MongoDB (3대 ReplicaSet)
kubectl get mongodbcommunity -n mongodb-ns
kubectl get pods -n mongodb-ns

# Redis (1 master + 2 follower)
kubectl get redisreplication -n redis-ns
kubectl get pods -n redis-ns
```

### DB 접속 정보

| DB | 사용자 | 비밀번호 | DB명 |
|----|--------|----------|------|
| MariaDB | kevin | k8spass# | ecommerce |
| MongoDB | kevin | k8spass# | ecommerce |
| Redis | - | k8spass# | - |

> URI의 `#`은 `%23`으로 URL 인코딩  
> 예: `mongodb://kevin:k8spass%23@mongodb-svc.mongodb-ns.svc.cluster.local:27017/?authSource=ecommerce`

### Redis 읽기/쓰기 분리

| 용도 | 서비스명 | 설명 |
|------|----------|------|
| 쓰기 | `redis-svc-master.redis-ns` | INSERT / DELETE |
| 읽기 | `redis-svc-follower.redis-ns` | GET (캐시 조회) |

### Step 5. GitLab CI/CD + ArgoCD 배포 흐름

앱 서비스(product, auth-member, payment, gateway, frontend, crawler, kafka-consumer)는  
**GitLab CI → Harbor → ArgoCD → Helm Chart** 파이프라인으로 자동 배포된다.

```
app-repo main 브랜치 push
  └─▶ GitLab CI (.gitlab-ci.yml)
        ├─ docker build + trivy scan
        ├─ docker push → Harbor (192.168.0.64)
        └─ manifest-repo/helm-charts/values.yaml tag 자동 업데이트
              └─▶ ArgoCD가 변경 감지 → 클러스터에 자동 싱크
```

**GitLab CI 파이프라인 단계**

| Stage | 내용 |
|-------|------|
| test | Runner 연결 확인 |
| sonar-scan | SonarQube 코드 품질 분석 (main 브랜치만) |
| build-scan-push | 7개 이미지 빌드 + Trivy 취약점 스캔 + Harbor push |
| update-manifest | values.yaml의 모든 `tag:` 필드를 `$CI_COMMIT_SHORT_SHA`로 갱신 후 manifest-repo push |

**ArgoCD Application 확인**

```bash
kubectl get application -n argocd
# 예시 출력
# NAME          SYNC STATUS   HEALTH STATUS
# ecommerce     Synced        Healthy
```

**수동 싱크 (필요 시)**

```bash
argocd app sync ecommerce
```

**Helm Chart 구조 (manifest-repo)**

```
helm-charts/
├── Chart.yaml
├── values.yaml           ← CI가 tag 자동 갱신
└── templates/
    ├── apps/
    │   ├── product/      ← Deployment + Service
    │   ├── auth-member/
    │   ├── payment/
    │   ├── gateway/
    │   ├── frontend/
    │   ├── kafka-consumer/
    │   └── crawler/      ← CronJob 5개 (best/sales 크롤·순위, 카테고리)
    └── infra/
        ├── mariadb.yaml
        ├── mongodb.yaml
        ├── redis.yaml
        ├── kafka.yaml    ← Strimzi KafkaNodePool + Kafka CR
        ├── networkpolicy-mariadb.yaml
        ├── networkpolicy-mongodb.yaml
        └── networkpolicy-redis.yaml
```

**CronJob 스케줄 (crawler-ns)**

| CronJob | 스케줄 | 역할 |
|---------|--------|------|
| crawler-best | 매일 02:00 | 베스트 상품 전체 크롤링 |
| crawler-sales | 매일 02:30 | 할인 상품 전체 크롤링 |
| rank-updater-best | 매일 06:00 | 베스트 순위 갱신 |
| rank-updater-sales | 매일 06:30 | 할인 순위 갱신 |
| category-crawler | 매일 01:00 | 카테고리 목록 갱신 |

### FQDN 패턴

클러스터 내부 서비스 주소:

```
{서비스명}.{네임스페이스}.svc.cluster.local:{포트}

예)
mongodb-svc.mongodb-ns.svc.cluster.local:27017
redis-svc-master.redis-ns.svc.cluster.local:6379
mariadb-svc.mariadb-ns.svc.cluster.local:3306
product-svc.backend-ns.svc.cluster.local:50051
```

---

## 10. 운영 이슈 & 트러블슈팅

### 10-1. Harbor/GitLab IP 변경 (0.54 → 0.64)

Harbor·GitLab 서버 IP가 변경된 경우 다음 위치를 모두 업데이트해야 한다.

| 파일 | 변경 내용 |
|------|-----------|
| `manifest-repo/helm-charts/values.yaml` | 모든 이미지 `repository` 필드 |
| `manifest-repo/k8s/infra/mariadb.yaml` | image 주소 |
| `manifest-repo/k8s/infra/redis.yaml` | image 주소 |
| `app-repo/.gitlab-ci.yml` | manifest-repo clone URL |

**git remote URL 변경**

```bash
# 기존 remote 확인
git remote -v

# 새 IP로 pull/push (URL 인코딩 주의: # → %23)
git pull http://root:k8spass%23@192.168.0.64:8929/team4-group/manifest-repo.git main
git push http://root:k8spass%23@192.168.0.64:8929/team4-group/manifest-repo.git main
```

**각 노드 containerd insecure registry 설정 (setup-harbor-registry.sh)**

Harbor IP 변경 시 모든 k8s 노드의 containerd 설정도 갱신해야 한다.

```bash
# manifest-repo/k8s/setup-harbor-registry.sh 실행
bash k8s/setup-harbor-registry.sh
```

스크립트 내용:
```bash
HARBOR_IP="192.168.0.64"
NODES=("192.168.0.68" "192.168.0.57" "192.168.0.59" "192.168.0.60")
# 각 노드에 /etc/containerd/certs.d/${HARBOR_IP}/hosts.toml 생성 후 containerd 재시작
```

---

### 10-2. NetworkPolicy 트러블슈팅

#### Calico iptables 모드 — kube-apiserver egress

**증상**: mongodb-kubernetes-operator CrashLoopBackOff, 로그에 `TLS handshake timeout` (대상: `10.233.0.1:443`)

**원인**: Calico는 iptables 정책을 kube-proxy DNAT **이후**에 평가한다.  
따라서 NetworkPolicy에는 ClusterIP(`10.233.0.1:443`)가 아닌 **실제 kube-apiserver 엔드포인트 IP**를 써야 한다.

```bash
# 실제 kube-apiserver 엔드포인트 확인
kubectl get endpoints kubernetes -n default
```

**수정 (manifest-repo/helm-charts/templates/infra/networkpolicy-mongodb.yaml)**

```yaml
egress:
- ports:
  - port: 6443        # kube-apiserver 실제 포트
    protocol: TCP
  to:
  - ipBlock:
      cidr: 192.168.0.68/32   # master 노드 실제 IP
```

#### mariadb-ns — istiod egress 누락

**증상**: `mariadb-0` 파드의 `istio-proxy` 컨테이너 Startup probe 실패  
(`connect: connection refused` on `10.233.100.141:15021`)

**원인**: `mariadb-ns`에 `default-deny-all` NetworkPolicy는 있으나 istiod 통신 허용 정책이 없어 istio-proxy가 istiod에 연결 불가

**수정**: `manifest-repo/helm-charts/templates/infra/networkpolicy-mariadb.yaml` 추가

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-egress-istiod
  namespace: mariadb-ns
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: istio-system
    ports:
    - port: 15012
      protocol: TCP
    - port: 15010
      protocol: TCP
    - port: 15017
      protocol: TCP
    - port: 15014
      protocol: TCP
```

> 동일 패턴이 `mongodb-ns`, `redis-ns`에도 적용되어 있음. Istio가 활성화된 네임스페이스에 `default-deny-all`을 적용할 경우 반드시 istiod egress를 허용해야 한다.

---

### 10-3. CronJob 파드 자동 정리

**증상**: CronJob 완료 후 파드가 5분이 지나도 삭제되지 않음

**원인**: `successfulJobsHistoryLimit: 1`(기본값)이면 CronJob controller가 마지막 성공 Job을 보존하므로 `ttlSecondsAfterFinished`가 동작하지 않는다.

**수정**: `successfulJobsHistoryLimit: 0`으로 변경

```yaml
spec:
  successfulJobsHistoryLimit: 0   # 0 = 성공 Job 즉시 관리 해제 → TTL 동작
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      ttlSecondsAfterFinished: 300  # 완료 후 5분 뒤 자동 삭제
```

> Istio 사이드카가 있는 CronJob은 메인 컨테이너 종료 후 사이드카도 같이 종료되어야 한다.  
> 아래 어노테이션 필수:
> ```yaml
> annotations:
>   proxy.istio.io/config: '{"holdApplicationUntilProxyStarts": true, "proxyMetadata": {"EXIT_ON_ZERO_ACTIVE_CONNECTIONS": "true"}}'
> ```
> 메인 컨테이너 종료 시 `quitquitquit` 엔드포인트 호출도 추가:
> ```bash
> command: ["/bin/sh", "-c", "python main.py; python -c \"import urllib.request; urllib.request.urlopen('http://localhost:15020/quitquitquit', data=b'')\" 2>/dev/null || true"]
> ```

---

### 10-4. Orphan Pod 강제 삭제 (finalizer stuck)

**증상**: Job 삭제 후에도 파드가 `Completed` 상태로 영구히 남음  
`kubectl delete pod --grace-period=0 --force` 도 실패

**원인**: `batch.kubernetes.io/job-tracking` finalizer가 걸려 있고, 해당 Job이 이미 삭제된 경우 finalizer를 처리할 주체가 없어 stuck

**시도한 방법들 (모두 실패)**

| 방법 | 실패 원인 |
|------|-----------|
| `--grace-period=0 --force` | finalizer 있으면 무시됨 |
| `kubectl proxy` + json-patch | Istio mutating webhook이 개입해 spec 변경 → 422 에러 |
| `kubectl proxy` + merge-patch | 동일 |
| namespace `istio-injection=disabled` | `istio-revision-tag-default` webhook이 별도 동작 |
| Istio webhook 2개 임시 삭제 | Kyverno 등 다른 webhook이 동일하게 동작 |

**최종 해결: etcdctl 직접 삭제**

```bash
# etcd 환경변수 확인
sudo cat /etc/etcd.env | grep -E "CERT|KEY|CA"

# etcd에서 직접 삭제 (모든 webhook 우회)
sudo ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/ssl/etcd/ssl/ca.pem \
  --cert=/etc/ssl/etcd/ssl/admin-k8s-master3.pem \
  --key=/etc/ssl/etcd/ssl/admin-k8s-master3-key.pem \
  del /registry/pods/<namespace>/<pod-name>
```

> kubespray 설치 클러스터: etcd cert 경로는 `/etc/ssl/etcd/ssl/`  
> kubeadm 설치 클러스터: `/etc/kubernetes/pki/etcd/`

---

### 10-5. 서비스명 및 Favicon 변경

**서비스명**: `HAN-IP`

`app-repo/Frontend/index.html` 및 `app-repo/docker/frontend/index.html`:
```html
<title>HAN-IP</title>
```

**Favicon**: 식품 이커머스 컨셉 (녹색 배경 + 흰색 쇼핑카트 + 잎사귀)

`app-repo/Frontend/public/favicon.svg`:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
  <rect width="48" height="48" rx="10" fill="#2E8B57"/>
  <path d="M8 13h5l7 19h14l4-13H18" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="20" cy="36" r="3" fill="white"/>
  <circle cx="30" cy="36" r="3" fill="white"/>
  <path d="M33 7 Q39 3 41 9 Q35 13 33 7Z" fill="#90EE90"/>
</svg>
```

**주의**: Vite의 `public/` 폴더 파일은 빌드 후 `dist/` 루트에 복사된다.  
`index.html`의 경로는 `/favicon.svg` (❌ `/public/favicon.svg`)

```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
```

**CI 빌드 컨텍스트 주의**:  
`.gitlab-ci.yml`의 `docker build` 컨텍스트는 `./Frontend`이므로  
실제 빌드에 포함되는 파일은 `Frontend/` 하위 파일이다.  
`docker/frontend/` 의 파일은 CI 빌드에 포함되지 않는다.
