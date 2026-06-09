"""
FinSight AI — FastAPI Application Factory
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import get_settings
from app.core.database import engine, init_db
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestLoggingMiddleware, RateLimitMiddleware
from app.core.redis import redis_manager
from app.api.v1 import auth, users, documents, conversations, reports, research, admin, health

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    logger.info("Starting FinSight AI", env=settings.app_env)

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Connect to Redis
    await redis_manager.connect()
    logger.info("Redis connected")

    yield

    # Cleanup
    await redis_manager.disconnect()
    await engine.dispose()
    logger.info("FinSight AI shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Agentic Financial Intelligence Platform — Multi-agent AI system for financial research, analysis, and report generation with citation-backed RAG.",
        version="1.0.0",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # ── Middleware ────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # ── Exception Handlers ──────────────────────────────────
    register_exception_handlers(app)

    # ── API Routes ───────────────────────────────────────────
    api_prefix = "/api/v1"
    app.include_router(health.router, prefix=api_prefix, tags=["Health"])
    app.include_router(auth.router, prefix=f"{api_prefix}/auth", tags=["Authentication"])
    app.include_router(users.router, prefix=f"{api_prefix}/users", tags=["Users"])
    app.include_router(documents.router, prefix=f"{api_prefix}/documents", tags=["Documents"])
    app.include_router(conversations.router, prefix=f"{api_prefix}/conversations", tags=["Conversations"])
    app.include_router(reports.router, prefix=f"{api_prefix}/reports", tags=["Reports"])
    app.include_router(research.router, prefix=f"{api_prefix}/research", tags=["Research"])
    app.include_router(admin.router, prefix=f"{api_prefix}/admin", tags=["Admin"])

    return app


app = create_app()
