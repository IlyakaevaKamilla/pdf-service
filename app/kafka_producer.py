from confluent_kafka import Producer
from app.config import settings

_producer: Producer | None = None


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})
    return _producer


def publish_request(request_id: str, payload_json: bytes) -> None:
    producer = get_producer()
    producer.produce(topic=settings.kafka_input_topic, key=request_id, value=payload_json)
    producer.flush(timeout=5)


def publish_to_dlq(raw: bytes, reason: str) -> None:
    producer = get_producer()
    producer.produce(
        topic=settings.kafka_dlq_topic,
        value=raw,
        headers=[("error_reason", reason.encode())],
    )
    producer.flush(timeout=5)
