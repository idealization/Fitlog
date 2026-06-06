from __future__ import annotations

from fastapi import FastAPI

from .api.v1.router import api_router
from .core.config import Settings, get_settings
from .repositories.closet_items import InMemoryClosetItemRepository
from .repositories.image_analysis_jobs import InMemoryImageAnalysisRepository


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(
        title=resolved_settings.service_name,
        version=resolved_settings.version,
        description="AI wardrobe and outfit recommendation API.",
    )
    app.state.settings = resolved_settings
    app.state.closet_repository = InMemoryClosetItemRepository()
    app.state.image_analysis_repository = InMemoryImageAnalysisRepository()
    app.include_router(api_router, prefix=resolved_settings.api_v1_prefix)

    @app.get("/", tags=["root"])
    def root() -> dict[str, str]:
        return {
            "service": resolved_settings.service_name,
            "version": resolved_settings.version,
            "status": "ok",
        }

    return app


app = create_app()
