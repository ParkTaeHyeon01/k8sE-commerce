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
├── proto/product.proto    ← gRPC 인터페이스 정의
├── product/               ← gRPC 서버 (MongoDB 조회)
└── gateway/               ← FastAPI REST API (gRPC 호출 후 JSON 반환)
```

### Product gRPC 서버

```powershell
cd Backend/product
python main.py
```

- 포트: **50051**
- 제공 RPC:
  - `ListProducts` — 목록 조회 (페이지네이션, 정렬, 카테고리 필터)
  - `GetProduct` — 상품 상세 조회
  - `ListCategories` — 카테고리 목록 (실제 크롤된 카테고리만 반환)

### Gateway FastAPI

```powershell
cd Backend/gateway
python -m uvicorn main:app --port 8000
```

- 포트: **8000**
- Swagger 문서: `http://localhost:8000/docs`

**엔드포인트**

| 메서드 | URL | 설명 |
|--------|-----|------|
| GET | `/products` | 상품 목록 |
| GET | `/products/{product_id}` | 상품 상세 |
| GET | `/categories` | 카테고리 목록 |
| GET | `/health` | 헬스체크 |

**`/products` 쿼리 파라미터**

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `target` | `""` | `best` / `sales` / `""` (전체) |
| `category_code` | `""` | 카테고리 코드 (예: `907`) |
| `page` | `1` | 페이지 번호 |
| `page_size` | `20` | 페이지당 상품 수 |
| `sort_by` | `""` | `rank` / `price_asc` / `price_desc` / `discount_desc` |

**`/categories` 쿼리 파라미터**

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `target` | `""` | `best` / `sales` / `""` (전체 = best+sales 합집합) |

### Proto 재생성 (proto 수정 시)

```powershell
cd Backend
python -m grpc_tools.protoc -I proto --python_out=product --grpc_python_out=product proto/product.proto
python -m grpc_tools.protoc -I proto --python_out=gateway --grpc_python_out=gateway proto/product.proto
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
2. cd Kafka          → python main.py
3. cd Backend/product → python main.py
4. cd Backend/gateway → python -m uvicorn main:app --port 8000
5. cd Frontend        → npm run dev
```

### 포트 요약

| 서비스 | 포트 |
|--------|------|
| Kafka | 9092 |
| MongoDB | 27017 |
| Redis | 6379 |
| MariaDB | 3306 |
| Product gRPC | 50051 |
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

### Step 5. 앱 ConfigMap / Secret 적용

```bash
kubectl apply -f k8s/apps/product/
kubectl apply -f k8s/apps/gateway/
kubectl apply -f k8s/apps/auth-member/
kubectl apply -f k8s/apps/kafka-consumer/
kubectl apply -f k8s/apps/crawler/
```

### Step 6. Deployment / Service 적용 (준비 중)

```bash
kubectl apply -f k8s/apps/product/deployment.yaml
kubectl apply -f k8s/apps/gateway/deployment.yaml
# ... 각 서비스
```

### Step 7. Istio Gateway / HTTPRoute 적용 (준비 중)

```bash
kubectl apply -f k8s/istio/gateway.yaml
kubectl apply -f k8s/istio/httproutes/
```

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
