"""No-op / disabled LLM provider."""

from __future__ import annotations

from .base import LLMProvider, OnChunk


class NoOpProvider(LLMProvider):
    """Fallback when LLM is disabled — always raises."""

    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        """Raise because the provider is disabled."""
        del prompt, temperature
        raise RuntimeError("LLM provider is disabled")

    async def generate_stream(
        self,
        prompt: str,
        on_chunk: OnChunk | None,
        *,
        temperature: float = 0.2,
    ) -> str:
        """Raise because the provider is disabled."""
        del prompt, on_chunk, temperature
        raise RuntimeError("LLM provider is disabled")
