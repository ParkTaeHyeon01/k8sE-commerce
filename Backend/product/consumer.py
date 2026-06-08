# product 서비스 - Kafka Consumer
# 흐름: products.crawled 토픽 구독 -> 메시지 수신 -> MongoDB에 저장
# 접속 정보는 모두 환경변수로 주입받는다 (배포 환경마다 값이 다르기 때문)
import json
import os

from kafka import KafkaConsumer
from pymongo import MongoClient

from logger import get_logger

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "products.crawled")
KAFKA_GROUP_ID = os.environ.get("KAFKA_GROUP_ID", "product-service")

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "ecommerce")
MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION", "products")


def create_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
        group_id=KAFKA_GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
    )


def run() -> None:
    startup_logger = get_logger("product-consumer", "-")
    startup_logger.info("Kafka Consumer 시작")

    consumer = create_consumer()
    collection = MongoClient(MONGODB_URI)[MONGODB_DB][MONGODB_COLLECTION]

    for record in consumer:
        message = record.value
        logger = get_logger("product-consumer", message.get("trace_id", "-"))
        try:
            collection.insert_one(message)
            logger.info(f"저장 완료 - {message.get('group')}/{message.get('category_name')} | {message.get('name')}")
        except Exception as e:
            logger.error(f"저장 실패 - {message.get('name')}: {e}")


if __name__ == "__main__":
    run()
