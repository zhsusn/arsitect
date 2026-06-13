"""OpenAI-compatible HTTP LLM provider."""

from __future__ import annotations

import json

import httpx

from app.core.config import settings

from .base import LLMProvider, OnChunk


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible HTTP provider."""

    def __init__(
        self,
        api_base: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        """Initialize with optional overrides.

        Args:
            api_base: Base URL for the API. Defaults to
                ``settings.OPENAI_API_BASE``.
            api_key: API key. Defaults to ``settings.OPENAI_API_KEY``.
            model: Model name. Defaults to ``settings.OPENAI_MODEL``.
        """
        self.api_base = (api_base or settings.OPENAI_API_BASE or "").rstrip("/")
        self.api_key = api_key or settings.OPENAI_API_KEY or ""
        self.model = model or settings.OPENAI_MODEL

    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        """Generate a complete response via OpenAI-compatible API."""
        return await self.generate_stream(prompt, on_chunk=None, temperature=temperature)

    async def generate_stream(
        self,
        prompt: str,
        on_chunk: OnChunk | None,
        *,
        temperature: float = 0.2,
    ) -> str:
        """Stream a response from an OpenAI-compatible endpoint.

        Args:
            prompt: The prompt to send as a user message.
            on_chunk: Optional chunk callback.
            temperature: Sampling temperature.

        Returns:
            The complete response text.

        Raises:
            RuntimeError: If the gateway is not configured.
        """
        if not self.api_base or not self.api_key:
            raise RuntimeError("OpenAI gateway is not configured")
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": True,
        }

        chunks: list[str] = []
        async with (
            httpx.AsyncClient(timeout=120) as client,
            client.stream("POST", url, headers=headers, json=payload) as resp,
        ):
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:].strip()
                if data == "[DONE]":
                    break
                try:
                    delta = json.loads(data)
                    content = delta["choices"][0]["delta"].get("content", "")
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                if content:
                    chunks.append(content)
                    await self._emit_chunk(on_chunk, content)
        return "".join(chunks).strip()

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        on_chunk: OnChunk | None,
        *,
        temperature: float = 0.2,
    ) -> str:
        """Stream a chat response using the native chat endpoint.

        Args:
            messages: Conversation history as ``{"role": ..., "content": ...}``.
            on_chunk: Optional chunk callback.
            temperature: Sampling temperature.

        Returns:
            The complete response text.
        """
        if not self.api_base or not self.api_key:
            raise RuntimeError("OpenAI gateway is not configured")
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        chunks: list[str] = []
        async with (
            httpx.AsyncClient(timeout=120) as client,
            client.stream("POST", url, headers=headers, json=payload) as resp,
        ):
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:].strip()
                if data == "[DONE]":
                    break
                try:
                    delta = json.loads(data)
                    content = delta["choices"][0]["delta"].get("content", "")
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                if content:
                    chunks.append(content)
                    await self._emit_chunk(on_chunk, content)
        return "".join(chunks).strip()
