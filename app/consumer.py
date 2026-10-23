import json
import logging
from confluent_kafka import Consumer, Producer, KafkaError
from pydantic import ValidationError

from app.config import settings
from app.contracts import PdfRequest
from app.renderer import render_tour_pdf
from app.storage import storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def make_consumer() -> Consumer:
    return Consumer({
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "group.id": settings.kafka_group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })


def make_producer() -> Producer:
    return Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})


def send_to_dlq(producer: Producer, raw: bytes, reason: str):
    producer.produce(
        topic=settings.kafka_dlq_topic,
        value=raw,
        headers=[("error_reason", reason.encode())],
    )
    producer.flush()


def handle_message(msg, producer: Producer) -> None:
    raw = msg.value()
    try:
        data = json.loads(raw.decode("utf-8"))
        request = PdfRequest(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        log.error("Невалидное сообщение, уходит в DLQ: %s", e)
        send_to_dlq(producer, raw, f"validation: {e}")
        return

    key = f"{request.request_id}.pdf"

    # Идемпотентность: если файл уже есть — пропускаем
    if storage.exists(key):
        log.info("PDF для %s уже есть, пропускаем", request.request_id)
        return

    pdf_bytes = render_tour_pdf(request.payload)
    url = storage.save(key, pdf_bytes)
    log.info("PDF готов: %s (%s)", request.request_id, url)


def run():
    consumer = make_consumer()
    producer = make_producer()
    consumer.subscribe([settings.kafka_input_topic])
    log.info("Консьюмер запущен, слушаем %s", settings.kafka_input_topic)

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                log.error("Kafka error: %s", msg.error())
                continue

            try:
                handle_message(msg, producer)
                consumer.commit(message=msg)
            except Exception as e:
                log.exception("Ошибка обработки, не коммитим: %s", e)
                # не коммитим — Kafka отдаст снова
    finally:
        consumer.close()


if __name__ == "__main__":
    run()
