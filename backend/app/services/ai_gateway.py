"""AI Gateway with mock streaming responses for MVP."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from typing import Any


class AIGateway:
    """Gateway to AI providers.

    MVP uses a mock implementation so that no external API key is required.
    """

    # Built-in prompt registry for demonstration.
    _PROMPTS: dict[str, str] = {
        "bug_analysis": (
            "You are a senior engineer. Analyze the following error, identify the root "
            "cause, list affected files, and propose a fix. Error: {error_input}"
        ),
        "fix_plan": (
            "Based on the root cause below, generate a unified diff patch. Keep changes "
            "minimal and safe. Root cause: {root_cause}"
        ),
        "arch_governance": (
            "You are a software architect. Review the project for {issue_type} and "
            "suggest a refactoring plan with a diff. Project: {project_path}"
        ),
    }

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the gateway with an optional API key.

        Args:
            api_key: Provider API key. Defaults to ``KIMI_API_KEY`` env var.
        """
        self._api_key = api_key or os.environ.get("KIMI_API_KEY")

    def get_prompt(self, prompt_name: str, variables: dict[str, Any]) -> str:
        """Render a registered prompt template.

        Args:
            prompt_name: Name of the prompt template.
            variables: Variables to interpolate into the template.

        Returns:
            Rendered prompt text.

        Raises:
            KeyError: If the prompt name is unknown.
        """
        template = self._PROMPTS[prompt_name]
        return template.format(**variables)

    async def generate(
        self,
        prompt_name: str,
        variables: dict[str, Any],
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """Generate a mock AI response.

        Args:
            prompt_name: Name of the prompt template to use.
            variables: Variables for the prompt template.
            stream: Whether to stream chunks. Mock always streams.

        Yields:
            Text chunks of the mock response.
        """
        # Validate that the prompt exists; mock ignores actual content.
        self.get_prompt(prompt_name, variables)
        # Acknowledge the prompt briefly, then emit a canned response.
        chunks = [
            "[AI 分析中] ",
            f"基于提示 `{prompt_name}` 生成 mock 回复。",
            "\n\n",
            "建议检查相关代码路径并补充单元测试覆盖。",
        ]
        for chunk in chunks:
            await asyncio.sleep(0.05)
            yield chunk

    async def generate_non_stream(
        self,
        prompt_name: str,
        variables: dict[str, Any],
    ) -> str:
        """Generate a complete mock AI response.

        Args:
            prompt_name: Name of the prompt template to use.
            variables: Variables for the prompt template.

        Returns:
            Full response text.
        """
        chunks = [chunk async for chunk in self.generate(prompt_name, variables)]
        return "".join(chunks)

    async def chat(self, system: str, user: str) -> str:
        """Generate a mock chat-style response.

        Args:
            system: System instruction.
            user: User message.

        Returns:
            Full response text.
        """
        # MVP mock: echo a refined version of the user content.
        await asyncio.sleep(0.05)
        return (
            f"[AI 优化结果]\n基于以下提示优化：{user[:80]}...\n"
            "建议保持原有结构，补充类型注解与错误处理，并确保变更最小化。"
        )
