# Kafka producer 모듈 - 완성된 상품 데이터를 상품 단위로 즉시 전송한다
# (모았다가 끝에 한번에 보내지 않는 이유: 크롤러가 중간에 멈춰도 이미 보낸 상품은
#  안전하게 적재되고, product_id 기준 upsert라 재실행 시 중복 걱정 없이 이어갈 수 있다)
import json
import os

from confluent_kafka import Producer

# 로컬 개발 중에는 .env에서, k8s에서는 ConfigMap/Secret으로 주입된 값을 그대로 사용한다
_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_TOPIC = os.environ.get("KAFKA_PRODUCT_TOPIC", "crawled-products")


def create_producer() -> Producer:
    """Kafka producer 인스턴스를 생성한다."""
    return Producer({"bootstrap.servers": _BOOTSTRAP_SERVERS})


def send_product(producer: Producer, logger, trace_id: str, product: dict) -> None:
    """상품 데이터 하나를 Kafka로 전송한다.

    product_id를 메시지 키로 사용해 같은 상품의 메시지가 같은 파티션에 모이도록 하고,
    트레이스 ID를 메시지에 함께 실어 크롤러 -> Kafka -> 백엔드까지 추적이 이어지게 한다.
    """
    payload = {**product, "trace_id": trace_id}
    key = product["product_id"].encode("utf-8")
    value = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def _on_delivery(err, _msg):
        if err:
            logger.error(f"Kafka 전송 실패 - product_id={product['product_id']}: {err}")
        else:
            logger.info(
                f"Kafka 전송 완료 - product_id={product['product_id']} "
                f"status={product.get('status')}"
            )

    producer.produce(_TOPIC, key=key, value=value, callback=_on_delivery)
    # 전송 콜백을 처리할 수 있도록 큐를 짧게 폴링한다 (블로킹하지 않음)
    producer.poll(0)


def send_sync(producer: Producer, logger, trace_id: str, target: str, product_ids: list[str], crawled_at: str) -> None:
    """이번 크롤링 사이클에서 확인된 product_id 전체 목록을 정리(sync) 메시지로 전송한다.

    원본 사이트의 베스트/할인 목록은 수시로 바뀌므로, 이번에 보이지 않은 상품은
    targets 배열에서 빠져야 한다 (그래야 더 이상 베스트/할인 메뉴에 노출되지 않음).
    이 한 건의 메시지로 컨슈머가 "안 보인 상품의 target 제거"를 일괄 처리한다.
    """
    payload = {
        "type": "sync",
        "target": target,
        "product_ids": product_ids,
        "trace_id": trace_id,
        "crawled_at": crawled_at,
    }
    key = f"sync:{target}".encode("utf-8")
    value = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def _on_delivery(err, _msg):
        if err:
            logger.error(f"Kafka 정리(sync) 메시지 전송 실패 - target={target}: {err}")
        else:
            logger.info(f"Kafka 정리(sync) 메시지 전송 완료 - target={target} 상품 {len(product_ids)}건")

    producer.produce(_TOPIC, key=key, value=value, callback=_on_delivery)
    producer.poll(0)


def flush(producer: Producer) -> None:
    """전송 큐에 남아있는 메시지를 모두 내보낸다 (크롤링 종료 시 호출)."""
    producer.flush()
