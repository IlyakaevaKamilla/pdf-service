import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Response
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

from app.contracts import PdfRequest
from app.routes.query_params import PDFServiceDep, UserDep
from app.sse_manager import (
    get_finished_result,
    register_connection,
    send_to_connection,
    unregister_connection,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


class WebhookPayload(BaseModel):
    request_id: str
    status: str  # "ready" или "failed"
    reason: str | None = None


@router.post("/generate_tour", status_code=202)
def generate_pdf(
    service: PDFServiceDep,
    request: PdfRequest,
    user_id: UserDep,
):
    return service.create_generation_request(request, user_id)


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
            except TimeoutError:
                yield {"data": json.dumps({"status": "faiiled", "reason": "timeout"})}
        finally:  # when front disconnected or we sent a msg - remove
            unregister_connection(request_id)

    return EventSourceResponse(
        event_generator(),
        ping=15,  # keep-alive for nginx
        send_timeout=10.0,  # if a user closed the tap, finish after 10sec
        headers={"Cache-Control": "no-cache"},
    )


@router.post("/internal/pdf-ready")
async def pdf_ready(payload: WebhookPayload):
    arrival = datetime.now()
    log.info(
        f"TIMING: [{payload.request_id}] Вебхук получен в {arrival.strftime('%H:%M:%S.%f')}"
    )
    message = {"status": payload.status, "request_id": payload.request_id}
    delivered = await send_to_connection(payload.request_id, message)
    log.info(
        "Webhook %s for %s, delivered=%s", payload.status, payload.request_id, delivered
    )
    return {"ok": True, "delivered": delivered}


@router.get("/download/{request_id}")
def download_pdf(service: PDFServiceDep, request_id: str):
    file_bytes = service.download_pdf(request_id)
    return Response(
        content=file_bytes,
        media_type="application/pdf",
        headers={
            # заставляет браузер скачать файл с именем "tour_{request_id}.pdf"
            "Content-Disposition": f'attachment; filename="tour_{request_id}.pdf"'
        },
    )


@router.get("/history")
def get_history(
    service: PDFServiceDep,
    user_id: UserDep,
    from_place: str | None = None,
    to_place: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    activity: str | None = None,
):
    return service.get_history(
        user_id,
        from_place=from_place,
        to_place=to_place,
        date_from=date_from,
        date_to=date_to,
        activity=activity,
    )
