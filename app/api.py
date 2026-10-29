import json
import logging
import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

from app.contracts import PdfRequest
from app.kafka_producer import publish_request
from app.sanitize import sanitize_payload
from app.sse_manager import register_connection, unregister_connection, send_to_connection, get_finished_result
from app.storage import storage
from app.config import settings

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


class WebhookPayload(BaseModel):
    request_id: str
    status: str  # "ready" или "failed"
    url: str | None = None
    reason: str | None = None


@router.post("/generate_tour", status_code=202)
def generate_pdf(request: PdfRequest):
    request.payload = sanitize_payload(request.payload)
    try:
        body = json.dumps(request.model_dump(mode="json")).encode("utf-8")
        publish_request(request.request_id, body)
    except Exception:
        log.exception("Kafka unavailable")
        raise HTTPException(status_code=503, detail="Kafka unavailable")
    return {"request_id": request.request_id, "status": "pending"}


@router.get("/events/{request_id}")
async def pdf_events(request_id: str):
    finished = get_finished_result(request_id)  # если фронт затупил

    async def event_generator():
        if finished:
            yield {"data": json.dumps(finished)}
            return

        queue = register_connection(request_id)  # create
        try:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=60.0)
                yield {"data": json.dumps(message)}
            except asyncio.TimeoutError:
                yield {"data": json.dumps({"status": "faiiled", "reason": "timeout"})}
        finally:  # when front disconnected or we sent a msg - remove
            unregister_connection(request_id)

    return EventSourceResponse(
        event_generator(),
        ping=15,  # keep-alive for nginx
        send_timeout=10.0,  # if a user closed the tap, finish after 10sec
        headers={"Cache-Control": "no-cache"}
    )


@router.post("/internal/pdf-ready")
async def pdf_ready(payload: WebhookPayload):
    message = {
        "status": payload.status,
        "url": payload.url,
        "reason": payload.reason
    }
    delivered = await send_to_connection(payload.request_id, message)
    log.info("Webhook %s for %s, delivered=%s", payload.status, payload.request_id, delivered)
    return {"ok": True, "delivered": delivered}


@router.get("/download/{request_id}")
def download_pdf(request_id: str):
    key = f"{request_id}.pdf"

    if not storage.exists(key):
        raise HTTPException(status_code=404, detail="PDF not found")

    stream = storage.get_file_stream(key)  # поток данных из Silo
    if not stream:
        raise HTTPException(status_code=500, detail="Failed to read file from storage")

    return StreamingResponse(
        stream,
        media_type="application/pdf",
        headers={
            # Эта строчка заставляет браузер скачать файл с именем "tour_{request_id}.pdf"
            "Content-Disposition": f'attachment; filename="tour_{request_id}.pdf"'
        }
    )
