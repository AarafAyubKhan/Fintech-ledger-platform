"""
FinSight AI — LLM Provider Abstraction
Supports Gemini (primary) and OpenAI with a unified interface.
"""

from abc import ABC, abstractmethod
from typing import Any

import structlog

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Generate a completion. Returns {"content": str, "tokens": int}."""
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        response_format: dict | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Generate a structured JSON response."""
        ...


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        self.model = genai.GenerativeModel(self.model_name)

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        response = await self.model.generate_content_async(
            full_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )

        content = response.text if response.text else ""
        tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens = getattr(response.usage_metadata, "total_token_count", 0)

        return {"content": content, "tokens": tokens}

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        response_format: dict | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        import json

        format_instruction = ""
        if response_format:
            format_instruction = (
                "\n\nRespond ONLY with valid JSON matching this schema:\n"
                f"{json.dumps(response_format, indent=2)}"
            )

        full_prompt = f"{system_prompt}{format_instruction}\n\n{prompt}"

        response = await self.model.generate_content_async(
            full_prompt,
            generation_config={
                "temperature": temperature,
                "response_mime_type": "application/json",
            },
        )

        content = response.text if response.text else "{}"
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"raw": content}

        tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens = getattr(response.usage_metadata, "total_token_count", 0)

        return {"content": parsed, "tokens": tokens}


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model_name = settings.openai_model

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0

        return {"content": content, "tokens": tokens}

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        response_format: dict | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        import json

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"raw": content}

        tokens = response.usage.total_tokens if response.usage else 0

        return {"content": parsed, "tokens": tokens}


def get_llm_provider(provider: str | None = None) -> LLMProvider:
    """Factory function to get the configured LLM provider."""
    provider_name = provider or settings.default_llm_provider

    if provider_name == "gemini":
        if not settings.gemini_api_key:
            logger.warning("Gemini API key not set, falling back to OpenAI")
            return OpenAIProvider()
        return GeminiProvider()
    elif provider_name == "openai":
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not set, falling back to Gemini")
            return GeminiProvider()
        return OpenAIProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
