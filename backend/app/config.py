"""
FinSight AI — Application Configuration
Pydantic Settings for type-safe environment variable management.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    app_name: str = "FinSight AI"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: str = "DEBUG"

    # ── Backend Server ───────────────────────────────────────
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_workers: int = 4
    secret_key: str = "change-me-in-production"
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    # ── PostgreSQL ───────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "finsight"
    postgres_user: str = "finsight"
    postgres_password: str = "finsight_dev_password"
    database_url: str = ""

    @computed_field  # type: ignore[misc]
    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis ────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_url: str = ""

    @computed_field  # type: ignore[misc]
    @property
    def effective_redis_url(self) -> str:
        if self.redis_url:
            return self.redis_url
        password_part = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{password_part}{self.redis_host}:{self.redis_port}/0"

    # ── Qdrant ───────────────────────────────────────────────
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""
    qdrant_collection: str = "finsight_documents"

    # ── MinIO / S3 ───────────────────────────────────────────
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "finsight-documents"
    minio_use_ssl: bool = False

    # ── AI Providers ─────────────────────────────────────────
    gemini_api_key: str = ""
    openai_api_key: str = ""
    default_llm_provider: Literal["gemini", "openai"] = "gemini"
    default_embedding_provider: Literal["gemini", "openai"] = "gemini"

    gemini_model: str = "gemini-2.0-flash"
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-004"
    embedding_dimension: int = 768

    # ── JWT Authentication ───────────────────────────────────
    jwt_secret_key: str = "jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # ── Google OAuth ─────────────────────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── Rate Limiting ────────────────────────────────────────
    rate_limit_per_minute: int = 100
    rate_limit_burst: int = 20

    # ── Document Processing ──────────────────────────────────
    max_upload_size_mb: int = 50
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_chunks_per_query: int = 10

    # ── Observability ────────────────────────────────────────
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"

    @computed_field  # type: ignore[misc]
    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
