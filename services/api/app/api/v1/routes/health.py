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

