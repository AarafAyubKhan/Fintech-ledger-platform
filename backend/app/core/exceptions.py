"""
FinSight AI — Custom Exception Handlers
Structured error responses for the API.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
import structlog

logger = structlog.get_logger()


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} not found: {resource_id}",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class RateLimitException(AppException):
    def __init__(self):
        super().__init__(
            message="Rate limit exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class DocumentProcessingException(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class AgentExecutionException(AppException):
    def __init__(self, message: str, agent_name: str = ""):
        self.agent_name = agent_name
        super().__init__(
            message=f"Agent execution error ({agent_name}): {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> ORJSONResponse:
        logger.error(
            "app_exception",
            message=exc.message,
            status_code=exc.status_code,
            path=request.url.path,
        )
        return ORJSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> ORJSONResponse:
        logger.warning(
            "validation_error",
            path=request.url.path,
            errors=str(exc.errors()),
        )
        return ORJSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": True,
                "message": "Validation error",
                "detail": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
        logger.exception(
            "unhandled_exception",
            path=request.url.path,
            error=str(exc),
        )
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "message": "Internal server error",
                "detail": str(exc) if settings_debug() else "An unexpected error occurred",
            },
        )


def settings_debug() -> bool:
    from app.config import get_settings
    return get_settings().debug
