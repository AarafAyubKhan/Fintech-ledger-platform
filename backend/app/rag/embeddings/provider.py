"""
FinSight AI — Embedding Provider Abstraction
Supports Gemini and OpenAI embeddings with a unified interface.
"""

from abc import ABC, abstractmethod

import structlog

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]: ...


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Google Gemini embedding provider."""

    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        self._model_name = settings.embedding_model
        self._dimension = settings.embedding_dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        import google.generativeai as genai

        embeddings = []
        # Process in batches of 100
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            result = genai.embed_content(
                model=f"models/{self._model_name}",
                content=batch,
                task_type="retrieval_document",
            )
            if isinstance(result["embedding"][0], list):
                embeddings.extend(result["embedding"])
            else:
                embeddings.append(result["embedding"])

        return embeddings

    async def embed_query(self, text: str) -> list[float]:
        import google.generativeai as genai

        result = genai.embed_content(
            model=f"models/{self._model_name}",
            content=text,
            task_type="retrieval_query",
        )
        return result["embedding"]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model_name = "text-embedding-3-small"
        self._dimension = 1536

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await self.client.embeddings.create(
                model=self._model_name,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
        return embeddings

    async def embed_query(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=self._model_name,
            input=text,
        )
        return response.data[0].embedding


def get_embedding_provider(provider: str | None = None) -> EmbeddingProvider:
    """Factory function for embedding providers."""
    provider_name = provider or settings.default_embedding_provider

    if provider_name == "gemini":
        if not settings.gemini_api_key:
            return OpenAIEmbeddingProvider()
        return GeminiEmbeddingProvider()
    elif provider_name == "openai":
        if not settings.openai_api_key:
            return GeminiEmbeddingProvider()
        return OpenAIEmbeddingProvider()
    else:
        raise ValueError(f"Unknown embedding provider: {provider_name}")
