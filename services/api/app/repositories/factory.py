from __future__ import annotations

from ..core.config import Settings
from ..db.session import create_db_engine, create_session_factory, initialize_database
from .closet_items import InMemoryClosetItemRepository, SqlAlchemyClosetItemRepository
from .image_analysis_jobs import InMemoryImageAnalysisRepository, SqlAlchemyImageAnalysisRepository


def build_repositories(settings: Settings):
    if settings.repository_backend == "sqlite":
        engine = create_db_engine(settings.database_url)
        initialize_database(engine)
        session_factory = create_session_factory(engine)
        return {
            "closet_repository": SqlAlchemyClosetItemRepository(session_factory),
            "image_analysis_repository": SqlAlchemyImageAnalysisRepository(session_factory),
            "db_engine": engine,
            "db_session_factory": session_factory,
        }

    return {
        "closet_repository": InMemoryClosetItemRepository(),
        "image_analysis_repository": InMemoryImageAnalysisRepository(),
        "db_engine": None,
        "db_session_factory": None,
    }

