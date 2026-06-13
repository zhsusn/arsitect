"""LLM gateway for governance auto-fix.

Primary provider: Kimi CLI (`kimi --print --quiet --input-format text`).
Fallback provider: OpenAI-compatible HTTP endpoint.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import re
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.core.config import settings

OnChunk = Callable[[str], Awaitable[None] | None] | None


class LLMGateway(ABC):
    """Abstract LLM gateway."""

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


class KimiCLIGateway(LLMGateway):
    """Kimi CLI gateway — spawns `kimi` subprocess in one-shot print mode.

    The prompt is passed via the ``-p`` command-line argument and a strict
    ``--max-steps-per-turn 1`` guard is applied so that Kimi CLI behaves like a
    plain text generator instead of an agent that may explore the filesystem
    indefinitely.
    """

    # Prefix every prompt with a strong system instruction that forbids tool
    # usage.  Kimi CLI is an agent by default; without this guard it may try to
    # read files or spawn subagents, causing long hangs or non-deterministic
    # output.
    _TOOL_BAN = (
        "[系统指令] 你是一个纯文本回答助手。"
        "禁止调用任何工具、禁止读取文件、禁止执行命令、禁止探索项目。"
        "只根据题目中给出的信息直接回答，不要进行任何外部操作。\n\n"
    )

    def __init__(self, cli_path: str | None = None) -> None:
        self.cli_path = cli_path or settings.KIMI_CLI_PATH

    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        return await self.generate_stream(prompt, on_chunk=None, temperature=temperature)

    async def generate_stream(
        self,
        prompt: str,
        on_chunk: OnChunk | None,
        *,
        temperature: float = 0.2,
    ) -> str:
        del temperature  # Not supported by Kimi CLI.
        cmd = [
            self.cli_path,
            "--quiet",
            "--max-steps-per-turn",
            "1",
            "-p",
            self._TOOL_BAN + prompt,
        ]
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("KIMI_CLI_NO_ANALYTICS", "1")

        await self._emit_chunk(on_chunk, f"执行命令：{' '.join(cmd[:4])} ...")
        print(f"[KIMI CLI] spawning {' '.join(cmd[:4])} ...")

        # Uvicorn on Windows forces a SelectorEventLoop which does not support
        # asyncio subprocess transports.  Run the CLI in a worker thread using
        # synchronous subprocess instead.
        def _run_sync() -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                cmd,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                timeout=120,
            )

        try:
            completed = await asyncio.to_thread(_run_sync)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"Kimi CLI timed out after 120s") from exc

        stderr = _strip_surrogates(completed.stderr)
        print(f"[KIMI CLI] exit code {completed.returncode}")
        if stderr:
            print(f"[KIMI CLI] stderr: {stderr!r}")

        result = _strip_surrogates(completed.stdout).strip()
        if completed.returncode != 0 and not result:
            raise RuntimeError(
                f"Kimi CLI failed (exit {completed.returncode}): {stderr or 'no output'}"
            )

        await self._emit_chunk(on_chunk, result)
        return result


def _strip_surrogates(text: str) -> str:
    """Remove UTF-16 surrogate characters that cannot be JSON-serialized."""
    return "".join(c for c in text if not (0xD800 <= ord(c) <= 0xDFFF))


class OpenAILLMGateway(LLMGateway):
    """OpenAI-compatible HTTP gateway."""

    def __init__(
        self,
        api_base: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_base = (api_base or settings.OPENAI_API_BASE or "").rstrip("/")
        self.api_key = api_key or settings.OPENAI_API_KEY or ""
        self.model = model or settings.OPENAI_MODEL

    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        return await self.generate_stream(prompt, on_chunk=None, temperature=temperature)

    async def generate_stream(
        self,
        prompt: str,
        on_chunk: OnChunk | None,
        *,
        temperature: float = 0.2,
    ) -> str:
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


class NoOpLLMGateway(LLMGateway):
    """Fallback when LLM is disabled — always raises."""

    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        raise RuntimeError("LLM provider is disabled")

    async def generate_stream(
        self,
        prompt: str,
        on_chunk: OnChunk | None,
        *,
        temperature: float = 0.2,
    ) -> str:
        raise RuntimeError("LLM provider is disabled")


def get_llm_gateway() -> LLMGateway:
    """Return the configured LLM gateway."""
    provider = settings.GOVERNANCE_LLM_PROVIDER.lower()
    if provider == "kimi":
        return KimiCLIGateway()
    if provider == "openai":
        return OpenAILLMGateway()
    return NoOpLLMGateway()
