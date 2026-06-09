# 05. Kafka Consumer

크롤러가 Kafka에 보낸 상품 데이터를 읽어 MongoDB에 저장하는 컨슈머.

## 실행

```powershell
cd Kafka
python main.py
```

크롤러와 **동시에** 실행해야 한다. 크롤러가 Kafka에 메시지를 보내면 컨슈머가 즉시 MongoDB에 적재.

## 동작 흐름

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

## MongoDB 상품 도큐먼트 구조

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

## status 필드
- `ready`: 상세페이지 수집 완료 → 서비스에 노출
- `draft`: 상세페이지 수집 실패 → 숨김, 다음 크롤링 때 재시도
