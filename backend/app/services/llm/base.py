"""Abstract base class for LLM providers."""

from __future__ import annotations

import inspect
import json
import re
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

OnChunk = Callable[[str], Awaitable[None] | None]


class LLMProvider(ABC):
    """Abstract LLM provider.

    Implementations must support both blocking and streaming generation.
    """

    @abstractmethod
    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        """Return the raw LLM response text for the given prompt."""
        raise NotImplementedError

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        on_chunk: OnChunk | None,
        *,
        temperature: float = 0.2,
    ) -> str:
        """Stream the LLM response and return the complete text.

        Args:
            prompt: The prompt to send.
            on_chunk: Callback invoked for each streamed chunk. May be sync or
                async.
            temperature: Sampling temperature (provider permitting).

        Returns:
            The concatenated response text.
        """
        raise NotImplementedError

    async def generate_json(self, prompt: str, *, temperature: float = 0.2) -> dict[str, Any]:
        """Return parsed JSON from the LLM response."""
        text = await self.generate(prompt, temperature=temperature)
        return self._extract_json(text)

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        on_chunk: OnChunk | None,
        *,
        temperature: float = 0.2,
    ) -> str:
        """Stream a chat-style response.

        Default implementation concatenates messages into a single prompt and
        calls :meth:`generate_stream`. Providers that support native chat APIs
        should override this method.

        Args:
            messages: Conversation history as ``{"role": ..., "content": ...}``.
            on_chunk: Optional chunk callback.
            temperature: Sampling temperature.

        Returns:
            The concatenated response text.
        """
        prompt_parts: list[str] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"[系统指令]\n{content}")
            else:
                prompt_parts.append(f"[{role}]\n{content}")
        prompt = "\n\n".join(prompt_parts)
        return await self.generate_stream(prompt, on_chunk, temperature=temperature)

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """Extract the first JSON object from the response text."""
        text = text.strip()
        if text.startswith("```"):
            # Strip markdown fences
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()
        try:
            return json.loads(text)  # type: ignore[no-any-return]
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM response is not valid JSON: {text[:200]}") from exc

    @staticmethod
    async def _emit_chunk(on_chunk: OnChunk | None, chunk: str) -> None:
        """Invoke the chunk callback, awaiting it if necessary."""
        if on_chunk is None:
            return
        result = on_chunk(chunk)
        if inspect.isawaitable(result):
            await result
