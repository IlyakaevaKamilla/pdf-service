import time
from datetime import datetime
import logging
import json

from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.contracts import PdfRequest
from app.kafka_producer import publish_request
from app.sanitize import sanitize_payload
from app.crud.pdf import get_pdf_by_request_id, search_user_history
from app.db.database import get_session

log = logging.getLogger(__name__)


class PDFService:
    def __init__(self, session: Session):
        self.session = session

    def create_generation_request(self, request: PdfRequest, user_id: int) -> dict:
        """Clean, add user_id, send to Kafka."""
        start = datetime.now()
        log.info(f"TIMING: [{request.request_id}] Заявка принята в {start.strftime('%H:%M:%S.%f')}")
        request.user_id = user_id
        request.payload = sanitize_payload(request.payload)
        try:
            body = json.dumps(request.model_dump(mode="json")).encode("utf-8")
            publish_request(request.request_id, body)
        except Exception:
            log.exception("Kafka unavailable")
            raise HTTPException(status_code=503, detail="Kafka unavailable")
        log.info(f"TIMING: [{request.request_id}] Отправлено в Kafka, ответ 202")
        return {"request_id": request.request_id, "status": "pending"}

    def download_pdf(self, request_id: str) -> bytes:
        """Get bytes from DB or raise 404."""
        pdf_file = get_pdf_by_request_id(self.session, request_id)
        if not pdf_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        return pdf_file.file_data

    def get_history(self, user_id: int, **filters):
        """Returns list of trips for history (without bytes)."""
        pdf_files = search_user_history(self.session, user_id, **filters)
        return [
            {
                "request_id": pdf_file.request_id,
                "from_place": pdf_file.from_place,
                "to_place": pdf_file.to_place,
                "date_from": pdf_file.date_from,
                "date_to": pdf_file.date_to,
                "activity": pdf_file.activity,
                "created_at": pdf_file.created_at,
            }
            for pdf_file in pdf_files
        ]


def get_pdf_service(
    session: Session = Depends(get_session),
) -> PDFService:
    return PDFService(session)
