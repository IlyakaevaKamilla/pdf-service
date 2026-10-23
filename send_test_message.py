import json
import uuid
from confluent_kafka import Producer
from app.config import settings

producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})

message = {
    "request_id": str(uuid.uuid4()),
    "template_id": "tour",
    "payload": {
        "route": {"from_place": "Москва", "to_place": "Красная Поляна"},
        "dates": {"date_from": "2025-01-15", "date_to": "2025-01-22"},
        "activity": ["горные лыжи", "сноуборд"],
        "accommodation": {
            "name": "Отель Роза Хутор",
            "partner_url": "https://travel.yandex.ru/hotels/example"
        },
        "transfer": {"type": "own_car", "parking_needed": True},
        "travelers": {"adults": 2, "children": 1, "group_ski_level": "продвинутый"},
        "additional_options": {
            "accessibility": {"barrier_free": True},
            "comfort": {"calm_slopes": True, "infrastructure_nearby": True},
            "support": {"personal_instructor": True}
        },
        "price": {"tickets": 1000, "accommodation": 1000, "transfer": None, "total": 2000}
    }
}

producer.produce(
    topic=settings.kafka_input_topic,
    key=message["request_id"],
    value=json.dumps(message).encode("utf-8"),
)
producer.flush()
print(f"Отправлено: {message['request_id']}")