"""
FinSight AI — Middleware
Request logging, rate limiting, and security middleware.
"""

import time
from typing import Callable

import structlog
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with timing information."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        request_id = request.headers.get("X-Request-ID", "")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            request_id=request_id,
            client_ip=request.client.host if request.client else "unknown",
        )

        # Add timing header
        response.headers["X-Process-Time-Ms"] = str(round(duration_ms, 2))
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed sliding window rate limiter."""

    EXEMPT_PATHS = {"/api/v1/health", "/api/v1/ready", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks and docs
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Import here to avoid circular imports
        from app.core.redis import redis_manager

        if redis_manager.client is None:
            # If Redis is down, allow all requests (graceful degradation)
            return await call_next(request)

        # Identify client
        client_ip = request.client.host if request.client else "unknown"
        rate_key = f"rate_limit:{client_ip}:{request.url.path}"

        # Check rate limit
        current_count = await redis_manager.increment(rate_key, expire_seconds=60)

        if current_count > settings.rate_limit_per_minute:
            logger.warning(
                "rate_limit_exceeded",
                client_ip=client_ip,
                path=request.url.path,
                count=current_count,
            )
            return Response(
                content='{"detail":"Rate limit exceeded. Please try again later."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(settings.rate_limit_per_minute),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, settings.rate_limit_per_minute - current_count)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
