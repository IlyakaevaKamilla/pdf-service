from typing import Annotated

from fastapi import Depends

from app.service.pdf import PDFService, get_pdf_service

PDFServiceDep = Annotated[PDFService, Depends(get_pdf_service)]
