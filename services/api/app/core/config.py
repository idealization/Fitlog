from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    service_name: str = "Fitlog"
    version: str = "0.1.0"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    repository_backend: str = "memory"
    database_url: str = "sqlite:///./fitlog.db"
    upload_storage_root: str = ".fitlog/storage"
    image_analysis_provider: str = "deterministic"
    openai_api_key: str | None = field(default=None, repr=False)
    openai_vision_model: str = "gpt-5.4-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    image_analysis_timeout_seconds: float = 30.0
    image_analysis_max_retries: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings(
        service_name=os.getenv("FITLOG_SERVICE_NAME", "Fitlog"),
        version=os.getenv("FITLOG_VERSION", "0.1.0"),
        environment=os.getenv("FITLOG_ENVIRONMENT", "local"),
        api_v1_prefix=os.getenv("FITLOG_API_V1_PREFIX", "/api/v1"),
        repository_backend=os.getenv("FITLOG_REPOSITORY_BACKEND", "memory"),
        database_url=os.getenv("FITLOG_DATABASE_URL", "sqlite:///./fitlog.db"),
        upload_storage_root=os.getenv("FITLOG_UPLOAD_STORAGE_ROOT", ".fitlog/storage"),
        image_analysis_provider=os.getenv("FITLOG_IMAGE_ANALYSIS_PROVIDER", "deterministic"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_vision_model=os.getenv("FITLOG_OPENAI_VISION_MODEL", "gpt-5.4-mini"),
        openai_base_url=os.getenv("FITLOG_OPENAI_BASE_URL", "https://api.openai.com/v1"),
        image_analysis_timeout_seconds=float(os.getenv("FITLOG_IMAGE_ANALYSIS_TIMEOUT_SECONDS", "30")),
        image_analysis_max_retries=int(os.getenv("FITLOG_IMAGE_ANALYSIS_MAX_RETRIES", "2")),
    )
