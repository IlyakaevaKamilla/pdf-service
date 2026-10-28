import json
import logging
from confluent_kafka import Consumer, KafkaError
from pydantic import ValidationError

from app.config import settings
from app.contracts import PdfRequest
from app.renderer import render_tour_pdf
from app.storage import storage
from app.kafka_producer import publish_to_dlq

log = logging.getLogger(__name__)


def run():
    consumer = Consumer({
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "group.id": settings.kafka_group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe([settings.kafka_input_topic])
    log.info("Consumer started, listening %s", settings.kafka_input_topic)

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

            raw = msg.value()
            try:
                data = json.loads(raw.decode("utf-8"))
                request = PdfRequest(**data)
            except (json.JSONDecodeError, ValidationError) as e:
                log.error("Invalid message -> DLQ: %s", e)
                publish_to_dlq(raw, f"validation: {e}")
                consumer.commit(message=msg)
                continue

            key = f"{request.request_id}.pdf"
            if storage.exists(key):
                log.info("PDF %s already exists, skip", request.request_id)
                consumer.commit(message=msg)
                continue

            try:
                pdf_bytes = render_tour_pdf(request.payload)
                url = storage.save(key, pdf_bytes)
                log.info("PDF ready: %s (%s)", request.request_id, url)
                consumer.commit(message=msg)
            except Exception as e:
                log.exception("Render failed, not committing: %s", e)
    finally:
        consumer.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
