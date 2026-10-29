from justhtml import JustHTML

from app.contracts import TourPdfPayload


def sanitize_string(text: str) -> str:
    if not text:
        return text

    doc = JustHTML(text, fragment=True)
    return doc.to_html(pretty=False)


def sanitize_payload(payload: TourPdfPayload):
    payload.route.from_place = sanitize_string(payload.route.from_place)
    payload.route.to_place = sanitize_string(payload.route.to_place)

    payload.activity = [sanitize_string(activity) for activity in payload.activity]

    payload.accommodation.name = sanitize_string(payload.accommodation.name)

    if payload.travelers:
        payload.travelers.group_ski_level = sanitize_string(payload.travelers.group_ski_level)

    return payload
