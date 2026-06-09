# k8sE-commerce 워크북

마켓컬리 인기/할인 상품을 크롤링해 보여주는 쇼핑몰 서비스.  
k8s CI/CD 시연을 목적으로 한 MSA 구조의 MVP 프로젝트.

## 목차

| 번호 | 파일 | 내용 |
|------|------|------|
| 01 | [아키텍처](01_아키텍처.md) | 전체 구조, 기술 스택, 서비스 역할 |
| 02 | [환경 설정](02_환경설정.md) | 로컬 개발 환경 설치 (Kafka, MongoDB, Redis, MariaDB) |
| 03 | [환경변수](03_환경변수.md) | .env 설정 방법 |
| 04 | [크롤러](04_크롤러.md) | 상품 수집, 순위 업데이트, 카테고리 수집 |
| 05 | [Kafka Consumer](05_Kafka_Consumer.md) | 크롤링 데이터 MongoDB 적재 |
| 06 | [백엔드](06_백엔드.md) | gRPC 상품 서버 + FastAPI Gateway |
| 07 | [프론트엔드](07_프론트엔드.md) | React 앱 실행 |
| 08 | [전체 실행 순서](08_전체실행순서.md) | 처음부터 끝까지 한 번에 따라하기 |

## 프로젝트 구조

```
k8sE-commerce/
├── Crawler/          # 마켓컬리 크롤러 (Playwright)
├── Kafka/            # Kafka Consumer → MongoDB 적재
├── Backend/
│   ├── proto/        # gRPC 프로토 정의
│   ├── product/      # 상품 gRPC 서버
│   └── gateway/      # FastAPI REST Gateway
├── Frontend/         # React + Vite
└── Workbook/         # 이 문서
```
