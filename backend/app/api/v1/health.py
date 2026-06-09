"""
FinSight AI — Health Check Endpoints
Kubernetes-compatible liveness and readiness probes.
"""

from fastapi import APIRouter

from app.config import get_settings
from app.core.redis import redis_manager
from app.schemas import HealthResponse

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness probe — is the application running?"""
    services = {"api": "healthy"}

    # Check Redis
    if redis_manager.client:
        try:
            await redis_manager.client.ping()
            services["redis"] = "healthy"
        except Exception:
            services["redis"] = "unhealthy"
    else:
        services["redis"] = "not_connected"

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.app_env,
        services=services,
    )


@router.get("/ready")
async def readiness_check() -> dict:
    """Readiness probe — is the application ready to serve traffic?"""
    checks = {}

    # Check database
    try:
        from app.core.database import engine
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        checks["database"] = "ready"
    except Exception as e:
        checks["database"] = f"not_ready: {str(e)}"

    # Check Redis
    if redis_manager.client:
        try:
            await redis_manager.client.ping()
            checks["redis"] = "ready"
        except Exception:
            checks["redis"] = "not_ready"
    else:
        checks["redis"] = "not_connected"

    all_ready = all(v == "ready" for v in checks.values())
    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
    }
