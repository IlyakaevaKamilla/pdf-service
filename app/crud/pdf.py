from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import UserPDFHistory


def get_pdf_by_request_id(session: Session, request_id: str) -> UserPDFHistory | None:
    return session.execute(
        select(UserPDFHistory).where(UserPDFHistory.request_id == request_id)
    ).scalar_one_or_none()


def search_user_history(
    session: Session,
    user_id: int,
    from_place: str | None = None,
    to_place: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    activity: str | None = None,
) -> list[UserPDFHistory]:
    """Searches trips in user's history with filters."""
    query = select(UserPDFHistory).where(UserPDFHistory.user_id == user_id)

    if from_place:
        query = query.where(UserPDFHistory.from_place == from_place)
    if to_place:
        query = query.where(UserPDFHistory.to_place == to_place)
    if date_from:
        query = query.where(UserPDFHistory.date_from == date_from)
    if date_to:
        query = query.where(UserPDFHistory.date_to == date_to)
    if activity:
        query = query.where(UserPDFHistory.activity.like(f"%{activity}%"))

    return list(session.execute(query).scalars().all())
