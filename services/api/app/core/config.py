from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    service_name: str = "Fitlog"
    version: str = "0.1.0"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        service_name=os.getenv("FITLOG_SERVICE_NAME", "Fitlog"),
        version=os.getenv("FITLOG_VERSION", "0.1.0"),
        environment=os.getenv("FITLOG_ENVIRONMENT", "local"),
        api_v1_prefix=os.getenv("FITLOG_API_V1_PREFIX", "/api/v1"),
    )

