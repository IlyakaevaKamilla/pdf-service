from typing import Annotated

from fastapi import Depends

from app.dependencies.auth import get_current_user_id
from app.service.pdf import PDFService, get_pdf_service

PDFServiceDep = Annotated[PDFService, Depends(get_pdf_service)]
UserDep = Annotated[int, Depends(get_current_user_id)]
