import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI
from internal_middleware import (
    build_request_id_middleware,
    build_user_context_middleware,
)

from app.config import settings
from app.routes.api import router
from app.utils.logging import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("pdf-service is starting up")
    yield
    logger.info("pdf-service is shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/api/pdf/docs",
        redoc_url="/api/pdf/redoc",
        openapi_url="/api/pdf/openapi.json",
    )

    app.middleware("http")(build_request_id_middleware(logger=logger))
    app.middleware("http")(build_user_context_middleware(logger=logger))

    @app.get("/api/pdf/health")
    async def health_check():
        return {"status": "ok"}

    app.include_router(router)

    return app


app = create_app()
