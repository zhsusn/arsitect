"""Kimi CLI LLM provider."""

from __future__ import annotations

import asyncio
import os

from app.core.config import settings

from .base import LLMProvider, OnChunk


class KimiCLIProvider(LLMProvider):
    """Kimi CLI provider — spawns `kimi` subprocess in print mode.

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
        """Initialize with an optional CLI path.

        Args:
            cli_path: Path to the ``kimi`` executable. Defaults to
                ``settings.KIMI_CLI_PATH``.
        """
        self.cli_path = cli_path or settings.KIMI_CLI_PATH

    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        """Generate a complete response via Kimi CLI."""
        return await self.generate_stream(prompt, on_chunk=None, temperature=temperature)

    async def generate_stream(
        self,
        prompt: str,
        on_chunk: OnChunk | None,
        *,
        temperature: float = 0.2,
    ) -> str:
        """Stream a response from Kimi CLI.

        Args:
            prompt: The prompt to send.
            on_chunk: Optional chunk callback.
            temperature: Ignored — Kimi CLI does not expose temperature.

        Returns:
            The complete response text.
        """
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

        print(f"[KIMI CLI] spawning {' '.join(cmd[:4])} ...")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        # Close stdin immediately; we pass the prompt via -p.
        if proc.stdin is not None:
            proc.stdin.close()

        chunks: list[str] = []
        stderr_chunks: list[bytes] = []

        async def _read_stdout() -> None:
            assert proc.stdout is not None
            while True:
                raw = await proc.stdout.read(1024)
                if not raw:
                    break
                text = raw.decode("utf-8", errors="replace")
                text = _strip_surrogates(text)
                chunks.append(text)
                print(f"[KIMI CLI] stdout chunk ({len(text)} chars)")
                await self._emit_chunk(on_chunk, text)

        async def _read_stderr() -> None:
            assert proc.stderr is not None
            while True:
                raw = await proc.stderr.read(1024)
                if not raw:
                    break
                stderr_chunks.append(raw)

        await asyncio.gather(_read_stdout(), _read_stderr())
        await proc.wait()

        stderr = b"".join(stderr_chunks).decode("utf-8", errors="replace")
        stderr = _strip_surrogates(stderr)
        print(f"[KIMI CLI] exit code {proc.returncode}")
        if stderr:
            print(f"[KIMI CLI] stderr: {stderr!r}")

        result = "".join(chunks).strip()

        # Kimi CLI exits with 1 when the step limit is hit, but it usually still
        # produced useful content.  Treat non-zero exit codes as fatal only when
        # no output was captured.
        if proc.returncode != 0 and not result:
            raise RuntimeError(
                f"Kimi CLI failed (exit {proc.returncode}): {stderr or 'no output'}"
            )
        return result


def _strip_surrogates(text: str) -> str:
    """Remove UTF-16 surrogate characters that cannot be JSON-serialized."""
    return "".join(c for c in text if not (0xD800 <= ord(c) <= 0xDFFF))
