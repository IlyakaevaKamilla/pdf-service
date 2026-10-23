from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import ferropdf
from app.contracts import TourPdfPayload

TEMPLATES_DIR = Path(__file__).parent / "templates"

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
engine = ferropdf.Engine(ferropdf.Options(page_size="A4"))


def render_tour_pdf(payload: TourPdfPayload) -> bytes:
    """Берёт payload, подставляет в HTML-шаблон, рендерит в PDF-байты."""
    template = env.get_template("tour_template.html")
    html = template.render(payload=payload.model_dump())
    pdf_bytes = engine.render(html)
    return pdf_bytes
