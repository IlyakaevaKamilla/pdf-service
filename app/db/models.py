from datetime import date, datetime

from sqlalchemy import Date, DateTime, LargeBinary, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserPDFHistory(Base):
    __tablename__ = "user_pdf_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    from_place: Mapped[str] = mapped_column(String(100), nullable=False)
    to_place: Mapped[str] = mapped_column(String(100), nullable=False)
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    activity: Mapped[str] = mapped_column(String(100), nullable=False)
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
