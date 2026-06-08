# Kafka consumer 진입점
# 흐름: crawled-products 토픽 구독 -> 메시지 하나(=상품 하나)마다
#       trace_id로 로깅하며 MongoDB products 컬렉션에 upsert
import json
import os

from dotenv import load_dotenv

# mongo_loader가 모듈 로드 시점에 환경변수를 읽으므로, 그보다 먼저 .env를 적용해야 한다
load_dotenv()

from confluent_kafka import Consumer

from logger import get_logger
from mongo_loader import get_collection, upsert_product

_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_TOPIC = os.environ.get("KAFKA_PRODUCT_TOPIC", "crawled-products")
_GROUP_ID = os.environ.get("KAFKA_CONSUMER_GROUP", "product-loader")

# 시작 시점 상관없이 토픽의 처음부터 읽는다 (이미 처리한 메시지는 upsert라 다시 처리해도 안전)
_CONSUMER_CONFIG = {
    "bootstrap.servers": _BOOTSTRAP_SERVERS,
    "group.id": _GROUP_ID,
    "auto.offset.reset": "earliest",
}


def handle_message(collection, logger_factory, raw_value: bytes) -> None:
    """메시지 하나(상품 하나)를 파싱해 MongoDB에 적재한다."""
    product = json.loads(raw_value.decode("utf-8"))
    trace_id = product.get("trace_id", "unknown")
    logger = logger_factory(trace_id)

    upsert_product(collection, product)
    logger.info(
        f"적재 완료 - product_id={product['product_id']} "
        f"name={product.get('name')} status={product.get('status')}"
    )


def run() -> None:
    base_logger = get_logger("consumer", "startup")
    base_logger.info(f"Kafka consumer 시작 - 토픽: {_TOPIC}, 그룹: {_GROUP_ID}")

    collection = get_collection()
    consumer = Consumer(_CONSUMER_CONFIG)
    consumer.subscribe([_TOPIC])

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                base_logger.error(f"메시지 수신 오류: {msg.error()}")
                continue

            try:
                handle_message(collection, lambda trace_id: get_logger("consumer", trace_id), msg.value())
            except Exception as e:
                base_logger.error(f"메시지 처리 실패 - offset={msg.offset()}: {e}")
                continue

            consumer.commit(msg)
    except KeyboardInterrupt:
        base_logger.info("Kafka consumer 종료 요청 수신")
    finally:
        consumer.close()


if __name__ == "__main__":
    run()
