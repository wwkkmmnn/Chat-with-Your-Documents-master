from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.dependencies import get_app_services, get_settings
from backend.routes.chat import router as chat_router
from backend.routes.health import router as health_router
from backend.routes.sessions import router as sessions_router
from backend.routes.upload import router as upload_router
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _mount_mcp_if_available(app: FastAPI) -> None:
    try:
        from fastapi_mcp import FastApiMCP
    except ImportError:
        logger.info("fastapi_mcp is not installed; MCP mount skipped.")
        return

    try:
        FastApiMCP(app).mount()
        logger.info("MCP endpoint mounted successfully.")
    except Exception as exc:  # pragma: no cover - optional integration
        logger.warning("Failed to mount MCP endpoint: %s", exc)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Document RAG + web search + SSE streaming assistant prototype.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api", tags=["health"])
    app.include_router(upload_router, prefix="/api", tags=["upload"])
    app.include_router(sessions_router, prefix="/api", tags=["sessions"])
    app.include_router(chat_router, prefix="/api", tags=["chat"])

    @app.on_event("startup")
    def _startup() -> None:
        get_app_services()
        logger.info("Application startup complete.")

    _mount_mcp_if_available(app)
    return app


app = create_app()
