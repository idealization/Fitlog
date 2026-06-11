from __future__ import annotations

from fastapi import FastAPI

from .api.v1.router import api_router
from .core.config import Settings, get_settings
from .repositories.factory import build_repositories
from .services.upload_storage import LocalUploadStorage


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(
        title=resolved_settings.service_name,
        version=resolved_settings.version,
        description="AI wardrobe and outfit recommendation API.",
    )
    app.state.settings = resolved_settings
    repositories = build_repositories(resolved_settings)
    app.state.closet_repository = repositories["closet_repository"]
    app.state.image_analysis_repository = repositories["image_analysis_repository"]
    app.state.notification_repository = repositories["notification_repository"]
    app.state.recommendation_repository = repositories["recommendation_repository"]
    app.state.db_engine = repositories["db_engine"]
    app.state.db_session_factory = repositories["db_session_factory"]
    app.state.upload_storage = LocalUploadStorage(resolved_settings.upload_storage_root)
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
