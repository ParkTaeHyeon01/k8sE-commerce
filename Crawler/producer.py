# Kafka 프로듀서 - 크롤링한 상품 데이터를 JSON 메시지로 전송
# 브로커 주소/토픽은 환경변수로 주입받는다 (배포 환경마다 값이 다르기 때문)
import json
import os

from kafka import KafkaProducer

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "products.crawled")


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
    )


def send_product(producer: KafkaProducer, message: dict) -> None:
    """상품 메시지 1건을 토픽으로 전송한다 (trace_id 포함된 dict)."""
    producer.send(KAFKA_TOPIC, value=message)
