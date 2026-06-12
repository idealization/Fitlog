from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    return {
        "service": settings.service_name,
        "version": settings.version,
        "environment": settings.environment,
        "status": "ok",
    }


@router.get("/runtime-readiness")
def runtime_readiness(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    provider = settings.image_analysis_provider.strip().lower()
    live_provider = provider == "openai"
    provider_configured = not live_provider or bool(settings.openai_api_key)

    return {
        "apiStatus": "ok",
        "environment": settings.environment,
        "repositoryBackend": settings.repository_backend,
        "imageAnalysis": {
            "provider": provider,
            "model": settings.openai_vision_model if live_provider else "fitlog-deterministic-v1",
            "configured": provider_configured,
            "live": live_provider and provider_configured,
        },
    }
