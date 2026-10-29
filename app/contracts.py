"""
Контракт сообщений для PDF-генератора.
Этот файл — источник правды. Смежники (конфигуратор, профиль) импортируют
TourPdfPayload и валидируют данные перед отправкой в Kafka.
"""
from datetime import date
from enum import Enum
from pydantic import BaseModel, Field


class Route(BaseModel):
    from_place: str = Field(..., description="Город отправления")
    to_place: str = Field(..., description="Город назначения")


class Dates(BaseModel):
    date_from: date
    date_to: date


class Accommodation(BaseModel):
    name: str = Field(..., description="Название отеля для отображения")
    partner_url: str | None = Field(None, description="Ссылка на партнёра (Яндекс Путешествия)")


class TransferType(str, Enum):
    NEEDED = "needed"
    SELF = "self"
    OWN_CAR = "own_car"


class Transfer(BaseModel):
    type: TransferType
    parking_needed: bool | None = Field(
        None, description="Только для OWN_CAR: нужна ли парковка"
    )


class Travelers(BaseModel):
    adults: int | None = Field(None, ge=0)
    children: int = Field(None, ge=0)
    group_ski_level: str | None = None


class Accessibility(BaseModel):
    barrier_free: bool = False
    ramps_and_lifts: bool = False
    adapted_accommodation: bool = False


class Comfort(BaseModel):
    low_physical_load: bool = False
    calm_slopes: bool = False
    infrastructure_nearby: bool = False


class Support(BaseModel):
    escort: bool = False
    equipment_help: bool = False
    personal_instructor: bool = False


class AdditionalOptions(BaseModel):
    accessibility: Accessibility = Accessibility()
    comfort: Comfort = Comfort()
    support: Support = Support()


class Price(BaseModel):
    tickets: int | None = None
    accommodation: int | None = None
    transfer: int | None = None
    total: int


class TourPdfPayload(BaseModel):
    """Содержимое PDF для одного тура."""
    route: Route
    dates: Dates
    activity: list[str]
    accommodation: Accommodation
    transfer: Transfer
    travelers: Travelers | None = None
    additional_options: AdditionalOptions = AdditionalOptions()
    price: Price


class PdfRequest(BaseModel):
    """Обёртка сообщения в Kafka: конверт + payload."""
    request_id: str
    template_id: str = "tour"
    payload: TourPdfPayload
    callback: dict | None = None
