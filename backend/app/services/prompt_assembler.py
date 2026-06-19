"""Prompt assembler for architecture governance auto-fix.

Builds a structured prompt from system role, project context, issue context,
current code context, user hints and execution instructions. The layout
follows the design in ``docs/aiclient.txt`` while staying compatible with the
Python backend architecture.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.file_backup_service import FileBackupService


class PromptAssembler:
    """Assemble a complete fix prompt for an LLM.

        The prompt contains enough context for the model to produce a precise,
    minimal change while preserving existing interfaces and project conventions.
    """

    _MAX_FILE_BYTES = 128_000

    def __init__(
        self,
        file_backup: FileBackupService | None = None,
        project_root: Path | None = None,
    ) -> None:
        """Initialize with optional file backup helper.

        Args:
            file_backup: Used to resolve target paths and read current code.
            project_root: Fallback project root when no backup helper is given.
        """
        self._file_backup = file_backup
        self._project_root = project_root

    def assemble_arch_fix_prompt(
        self,
        change: dict[str, Any],
        project_id: str,
        user_hint: str = "",
        project_context: dict[str, Any] | None = None,
    ) -> str:
        """Assemble a complete fix prompt from a change dict.

        Args:
            change: Change metadata including action, target_path, rationale.
            project_id: Project identifier.
            user_hint: Optional user-provided strategy hint.
            project_context: Optional project metadata (tech stack, directory tree).

        Returns:
            The assembled prompt string.
        """
        sections = [
            self._build_system_role(),
            self._build_project_context(project_id, project_context),
            self._build_issue_context(change),
            self._build_code_context(change, project_id),
            self._build_user_hint(user_hint),
            self._build_execution_instruction(change),
        ]
        return "\n\n".join(section for section in sections if section)

    @staticmethod
    def _build_system_role() -> str:
        return (
            "你是一位资深软件架构师，正在通过终端协助开发者进行架构治理。\n"
            "你的任务是根据检测到的问题，生成精确的代码修复方案。\n"
            "修复原则：\n"
            "1. 保持最小改动原则，只修复问题本身，不重构无关代码\n"
            "2. 保持接口兼容性，不破坏现有调用方\n"
            "3. 优先使用项目已有的技术栈和编码风格\n"
            "4. 生成完整的文件内容，而非片段，以便直接写入\n"
            "5. 如果问题无法安全修复，请明确说明原因，不要编造代码"
        )

    def _build_project_context(
        self,
        project_id: str,
        project_context: dict[str, Any] | None,
    ) -> str:
        if project_context:
            tech_stack = ", ".join(project_context.get("tech_stack", []) or [])
            language = project_context.get("language", "")
            framework = project_context.get("framework", "")
            directory_tree = project_context.get("directory_tree", "")
        else:
            tech_stack = "根据文件后缀推断"
            language = ""
            framework = ""
            directory_tree = ""

        parts = [
            "【项目上下文】",
            f"- 项目名称: {project_id}",
        ]
        if tech_stack:
            parts.append(f"- 技术栈: {tech_stack}")
        if language:
            parts.append(f"- 语言: {language}")
        if framework:
            parts.append(f"- 框架: {framework}")
        if directory_tree:
            parts.append(f"- 目录结构:\n{directory_tree}")
        return "\n".join(parts)

    @staticmethod
    def _build_issue_context(change: dict[str, Any]) -> str:
        action = change.get("action", "UPDATE_CODE")
        target_path = change.get("target_path", "")
        rationale = change.get("rationale", "")
        risk_level = change.get("risk_level", "")
        before_preview = change.get("before", "") or ""

        return (
            f"【检测到的架构问题】\n"
            f"- 修复动作: {action}\n"
            f"- 目标路径: {target_path}\n"
            f"- 风险等级: {risk_level}\n"
            f"- 修复理由: {rationale}\n"
            f"- 当前内容预览:\n```\n{before_preview[:2000]}\n```"
        )

    def _build_code_context(
        self,
        change: dict[str, Any],
        project_id: str,
    ) -> str:
        target_path = change.get("target_path", "")
        if not target_path:
            return ""

        try:
            if self._file_backup is not None:
                absolute_path = self._file_backup.resolve_target(target_path, project_id)
            else:
                absolute_path = self._resolve_fallback(target_path)
        except (ValueError, OSError):
            return f"【当前代码】\n（无法读取目标文件：{target_path}）"

        if not absolute_path.exists():
            return f"【当前代码】\n目标文件 {target_path} 不存在，将按创建新文件处理。"

        try:
            content = absolute_path.read_text(encoding="utf-8", errors="replace")
            if len(content.encode("utf-8")) > self._MAX_FILE_BYTES:
                content = content[: self._MAX_FILE_BYTES]
                content = content[: content.rfind("\n")]
                content += "\n\n...（内容已截断以控制 Prompt 长度）"
        except (OSError, UnicodeDecodeError) as exc:
            return f"【当前代码】\n（读取失败：{exc}）"

        return f"【当前代码】\n--- {target_path} ---\n```\n{content}\n```"

    def _resolve_fallback(self, target_path: str) -> Path:
        root = self._project_root or Path.cwd()
        rel = Path(target_path)
        normalized = rel.as_posix().replace("\\", "/")
        if ".." in normalized.split("/"):
            raise ValueError(f"Path traversal not allowed: {target_path}")
        return (root / rel).resolve()

    @staticmethod
    def _build_user_hint(hint: str) -> str:
        hint = (hint or "").strip()
        if not hint:
            return ""
        return f"【用户补充要求】\n{hint}"

    @staticmethod
    def _build_execution_instruction(change: dict[str, Any]) -> str:
        target_path = change.get("target_path", "")
        action = change.get("action", "UPDATE_CODE")
        return (
            f"【执行指令】\n"
            f"请针对上述问题，生成修复后的完整代码文件。\n"
            f"动作类型: {action}\n"
            f"主要目标文件: {target_path}\n"
            "输出格式要求：\n"
            "1. 先给出 根因分析（1-2句话）\n"
            "2. 给出 修复策略说明\n"
            "3. 对每个修改的文件，使用如下格式输出：\n"
            "   === FILE: {文件路径} ===\n"
            "   ```{语言}\n"
            "   {完整文件内容}\n"
            "   ```\n"
            "4. 如果涉及多个文件，请依次输出每个文件的代码块\n"
            "5. 未修改的文件不要输出\n"
            "6. 最后给出 验证建议（如何确认修复成功）"
        )
