from fastapi import APIRouter, status

from app.core.config import settings
from app.core.dependencies import check_opensearch, check_postgres, check_redis

router = APIRouter()


@router.get("/")
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "running",
        "environment": settings.app_env,
    }


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", status_code=status.HTTP_200_OK)
def ready() -> dict[str, object]:
    checks = {
        "postgres": check_postgres(),
        "redis": check_redis(),
        "opensearch": check_opensearch(),
    }
    is_ready = all(checks.values())

    return {
        "status": "ready" if is_ready else "degraded",
        "checks": checks,
    }
