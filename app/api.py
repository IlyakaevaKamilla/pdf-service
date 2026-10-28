import json
import logging

from fastapi import APIRouter, HTTPException
from app.contracts import PdfRequest
from app.kafka_producer import publish_request
from app.storage import storage
from app.config import settings

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/pdf/generate", status_code=202)
def generate_pdf(request: PdfRequest):
    try:
        body = json.dumps(request.model_dump(mode="json")).encode("utf-8")
        publish_request(request.request_id, body)
    except Exception:
        log.exception("Kafka unavailable")
        raise HTTPException(status_code=503, detail="Kafka unavailable")
    return {"request_id": request.request_id, "status": "pending"}


@router.get("/api/pdf/status/{request_id}")
def pdf_status(request_id: str):
    key = f"{request_id}.pdf"
    if storage.exists(key):
        url = f"{settings.s3_endpoint_url}/{settings.s3_bucket}/{key}"
        return {"request_id": request_id, "status": "ready", "url": url}
    return {"request_id": request_id, "status": "pending"}
