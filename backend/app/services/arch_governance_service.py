"""Architecture governance business logic service."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.c4.governance_fix.llm_gateway import LLMGateway, get_llm_gateway
from app.core.exceptions import NotFoundError
from app.models.cli_session import ArchIssue, ArchIssueSeverity, ArchIssueStatus
from app.schemas.cli import ArchIssueResponse, ArchScanResponse, ExecResult, ScanRule
from app.services.ai_gateway import AIGateway
from app.services.ai_output_parser import AIOutputParser
from app.services.file_backup_service import FileBackupService
from app.services.git_service import GitService
from app.services.prompt_assembler import PromptAssembler
from app.services.validation_service import ValidationService

Sender = Callable[[dict[str, Any]], Awaitable[None]]


class ArchGovernanceService:
    """Architecture governance scans, plan generation and fix execution."""

    _DEFAULT_RULES: list[ScanRule] = [
        ScanRule(
            rule_id="circular-dependency",
            name="循环依赖",
            description="Detect circular imports between modules.",
            enabled=True,
            severity="warning",
        ),
        ScanRule(
            rule_id="god-function",
            name="超大函数",
            description="Detect functions exceeding a reasonable line count.",
            enabled=True,
            severity="warning",
        ),
        ScanRule(
            rule_id="deprecated-api",
            name="废弃接口引用",
            description="Detect usages of deprecated APIs.",
            enabled=True,
            severity="info",
        ),
        ScanRule(
            rule_id="long-parameter-list",
            name="过长参数列表",
            description="Detect functions with too many parameters.",
            enabled=False,
            severity="info",
        ),
    ]

    def __init__(
        self,
        session: AsyncSession,
        ai_gateway: AIGateway | None = None,
        file_backup: FileBackupService | None = None,
        llm_gateway: LLMGateway | None = None,
        git_service: GitService | None = None,
        validation_service: ValidationService | None = None,
    ) -> None:
        """Initialize with an async session.

        Args:
            session: SQLAlchemy async session.
            ai_gateway: Optional AI gateway for plan optimization.
            file_backup: Optional file backup service.
            llm_gateway: Optional LLM gateway for real Kimi CLI calls during fix execution.
            git_service: Optional git service for branch/commit/rollback.
            validation_service: Optional validation service for post-fix checks.
        """
        self._session = session
        self._ai_gateway = ai_gateway or AIGateway()
        self._file_backup = file_backup or FileBackupService()
        self._llm_gateway = llm_gateway or get_llm_gateway()
        print(f"[ARCH SVC] llm_gateway type: {type(self._llm_gateway)}")
        self._git_service = git_service or GitService()
        self._validation_service = validation_service or ValidationService()
        self._prompt_assembler = PromptAssembler(file_backup=self._file_backup)

    async def list_rules(self) -> list[ScanRule]:
        """Return the default scan rule configuration.

        Returns:
            List of scan rules.
        """
        return list(self._DEFAULT_RULES)

    async def update_rules(self, rules: list[ScanRule]) -> list[ScanRule]:
        """Update and return the scan rule configuration.

        Args:
            rules: New rule configuration.

        Returns:
            Updated rules.
        """
        self._DEFAULT_RULES = rules
        return rules

    async def scan_project(
        self,
        project_id: str,
        session_id: str,
        rules: list[str] | None = None,
    ) -> ArchScanResponse:
        """Trigger a mock architecture scan.

        Args:
            project_id: Project ID.
            session_id: CLI session ID.
            rules: Optional rule IDs to enable.

        Returns:
            Scan acceptance response.
        """
        scan_id = f"SCAN-{uuid.uuid4()}"
        enabled_rule_ids = set(rules) if rules else None

        for rule in self._DEFAULT_RULES:
            if enabled_rule_ids is not None and rule.rule_id not in enabled_rule_ids:
                continue
            if not rule.enabled and enabled_rule_ids is None:
                continue
            issue = ArchIssue(
                project_id=project_id,
                session_id=session_id,
                issue_type=rule.rule_id,
                severity=rule.severity,
                rule_id=rule.rule_id,
                title=rule.name,
                description=rule.description,
                location="src/",
                status=ArchIssueStatus.DETECTED,
            )
            self._session.add(issue)

        await self._session.flush()
        return ArchScanResponse(scan_id=scan_id, status="accepted")

    async def list_issues(
        self,
        project_id: str,
        status: str | None = None,
        severity: str | None = None,
    ) -> list[ArchIssue]:
        """List architecture issues for a project.

        Args:
            project_id: Project ID.
            status: Optional status filter.
            severity: Optional severity filter.

        Returns:
            List of architecture issues.
        """
        stmt = select(ArchIssue).where(ArchIssue.project_id == project_id)
        if status:
            stmt = stmt.where(ArchIssue.status == status)
        if severity:
            stmt = stmt.where(ArchIssue.severity == severity)
        stmt = stmt.order_by(
            ArchIssue.severity == ArchIssueSeverity.CRITICAL,
            ArchIssue.severity == ArchIssueSeverity.WARNING,
            ArchIssue.severity == ArchIssueSeverity.INFO,
            ArchIssue.created_at.desc(),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_issue(self, issue_id: str) -> ArchIssue:
        """Fetch an architecture issue by ID.

        Args:
            issue_id: Issue ID.

        Returns:
            Architecture issue.

        Raises:
            NotFoundError: If the issue does not exist.
        """
        issue = await self._session.get(ArchIssue, issue_id)
        if issue is None:
            raise NotFoundError(detail=f"Arch issue '{issue_id}' not found")
        return issue

    async def generate_arch_plan(
        self,
        issue_id: str,
    ) -> ArchIssue:
        """Generate a mock governance plan for an issue.

        Args:
            issue_id: Issue ID.

        Returns:
            Updated architecture issue.
        """
        issue = await self.get_issue(issue_id)
        issue.governance_plan = (
            f"Mock plan for {issue.issue_type}: refactor affected files and "
            "add regression tests."
        )
        issue.refactor_diff = f"--- a/{issue.location}\n+++ b/{issue.location}\n@@ -1 +1 @@\n- old\n+ new\n"
        issue.status = ArchIssueStatus.PLANNED
        issue.updated_at = datetime.now(UTC)
        self._session.add(issue)
        await self._session.flush()
        return issue

    async def execute_governance(
        self,
        issue_id: str,
        action: str = "execute",
    ) -> ExecResult:
        """Simulate executing or skipping an architecture fix.

        Args:
            issue_id: Issue ID.
            action: Either ``execute`` or ``skip``.

        Returns:
            Execution result.

        Raises:
            NotFoundError: If the issue does not exist.
        """
        issue = await self.get_issue(issue_id)
        if action == "skip":
            issue.status = ArchIssueStatus.SKIPPED
            issue.updated_at = datetime.now(UTC)
            self._session.add(issue)
            await self._session.flush()
            return ExecResult(
                success=True,
                output="Issue skipped.",
                error=None,
                branch=None,
            )

        issue.status = ArchIssueStatus.EXECUTED
        issue.executed_at = datetime.now(UTC)
        issue.updated_at = datetime.now(UTC)
        self._session.add(issue)
        await self._session.flush()

        issue.status = ArchIssueStatus.VERIFIED
        issue.updated_at = datetime.now(UTC)
        self._session.add(issue)
        await self._session.flush()

        return ExecResult(
            success=True,
            output="Mock refactor applied and verified.",
            error=None,
            branch=f"arsitect-arch/{issue.id}",
        )

    async def apply_fix_plan(
        self,
        session_id: str,
        project_id: str,
        plan: dict[str, Any],
        sender: Sender,
    ) -> None:
        """Apply a C4 fix plan interactively via WebSocket.

        Iterates over each change set, sends an ``arch-decision`` card and
        waits for the frontend to send an action back through
        ``handle_change_action``.

        Args:
            session_id: CLI session ID.
            project_id: Project ID.
            plan: Fix plan produced by ``/c4/governance/fix-plan``.
            sender: Async callable used to push CLI responses.
        """
        plans = plan.get("plans", [])
        total = sum(len(p.get("changes", [])) for p in plans)
        strategy_prompt = plan.get("strategy_prompt", "")
        current = 0
        print(f"[ARCH FIX] apply_fix_plan session={session_id} total={total} plans={len(plans)}")

        await sender(
            self._build_text(session_id, f"开始执行修复计划，共 {total} 条变更。").model_dump()
        )

        if total == 0:
            await sender(
                self._build_text(
                    session_id, "暂无可自动执行的变更，请在架构治理页面重新扫描。"
                ).model_dump()
            )
            await sender(
                self._build_done(session_id, {"total": 0, "pending": 0}).model_dump()
            )
            return

        pending = 0
        for plan_item in plans:
            for change in plan_item.get("changes", []):
                current += 1
                await sender(
                    self._build_progress(
                        session_id, current, total, f"处理 {change.get('target_path')}"
                    ).model_dump()
                )

                if change.get("auto_applicable") and not change.get(
                    "requires_confirmation", True
                ):
                    await sender(
                        self._build_text(
                            session_id,
                            f"🔄 {change.get('target_path')} 无需确认，自动执行",
                        ).model_dump()
                    )
                    await self.handle_change_action(
                        session_id=session_id,
                        project_id=project_id,
                        command="fix",
                        metadata={
                            "change": change,
                            "project_id": project_id,
                            "strategy_prompt": strategy_prompt,
                        },
                        sender=sender,
                    )
                else:
                    card = self._build_decision_card(change, strategy_prompt)
                    await sender(self._build_card(session_id, card).model_dump())
                    pending += 1

        if pending:
            await sender(
                self._build_text(
                    session_id, f"所有变更已推送，等待用户确认执行（待确认 {pending} 条）。"
                ).model_dump()
            )
        else:
            await sender(
                self._build_text(
                    session_id, "所有自动变更已执行完毕。"
                ).model_dump()
            )
        await sender(
            self._build_done(session_id, {"total": total, "pending": pending}).model_dump()
        )

    async def handle_change_action(
        self,
        session_id: str,
        project_id: str,
        command: str,
        metadata: dict[str, Any],
        sender: Sender,
    ) -> ExecResult:
        """Execute or skip a single change from an interactive fix plan.

        Args:
            session_id: CLI session ID.
            project_id: Project ID.
            command: One of ``fix``, ``skip``, ``edit``.
            metadata: Change metadata, must include the original ``change`` dict.
            sender: Async callable used to push CLI responses.

        Returns:
            Execution result.
        """
        change = metadata.get("change", {})
        if not change:
            return ExecResult(
                success=False,
                output=None,
                error="Missing change metadata",
                branch=None,
            )

        issue_id = change.get("issue_id", "")
        issue = await self._get_or_create_issue(session_id, project_id, issue_id, change)

        if command == "skip":
            issue.status = ArchIssueStatus.SKIPPED
            issue.updated_at = datetime.now(UTC)
            self._session.add(issue)
            await self._session.flush()
            await sender(
                self._build_text(session_id, f"已跳过：{change.get('target_path')}").model_dump()
            )
            return ExecResult(success=True, output="Skipped", error=None, branch=None)

        edited_after = metadata.get("edited_after")
        action = change.get("action", "UPDATE_CODE")
        target_path = change.get("target_path", "")
        user_hint = metadata.get("user_hint") or metadata.get("strategy_prompt") or ""

        # Registry extraction runs the actual extractor instead of asking an LLM.
        if action == "RUN_REGISTRY_EXTRACT":
            try:
                from app.c4 import registry_extractor

                stats = await asyncio.to_thread(
                    registry_extractor.extract_registry, project_id
                )
                issue.status = ArchIssueStatus.EXECUTED
                issue.executed_at = datetime.now(UTC)
                issue.updated_at = datetime.now(UTC)
                issue.exec_result = {"stats": stats}
                self._session.add(issue)
                await self._session.flush()
                summary = (
                    f"已重新抽取 C4 Registry：{stats['components']} 个组件，"
                    f"{stats['relationships']} 条关系"
                )
                await sender(
                    self._build_text(session_id, summary).model_dump()
                )
                return ExecResult(
                    success=True,
                    output=summary,
                    error=None,
                    branch=None,
                )
            except Exception as exc:  # noqa: BLE001
                issue.status = ArchIssueStatus.DETECTED
                issue.exec_result = {"error": str(exc)}
                issue.updated_at = datetime.now(UTC)
                self._session.add(issue)
                await self._session.flush()
                await sender(
                    self._build_text(
                        session_id, f"C4 Registry 抽取失败：{exc}"
                    ).model_dump()
                )
                return ExecResult(
                    success=False,
                    output=None,
                    error=str(exc),
                    branch=None,
                )

        # Deletion does not require LLM code generation.
        if action == "DELETE_FILE":
            try:
                await self._apply_file_change(
                    session_id=session_id,
                    project_id=project_id,
                    target_path=target_path,
                    action=action,
                    content=None,
                )
                issue.status = ArchIssueStatus.EXECUTED
                issue.executed_at = datetime.now(UTC)
                issue.updated_at = datetime.now(UTC)
                self._session.add(issue)
                await self._session.flush()
                await sender(
                    self._build_text(session_id, f"已删除：{target_path}").model_dump()
                )
                return ExecResult(
                    success=True,
                    output=f"Deleted {target_path}",
                    error=None,
                    branch=None,
                )
            except Exception as exc:  # noqa: BLE001
                issue.status = ArchIssueStatus.DETECTED
                issue.exec_result = {"error": str(exc)}
                issue.updated_at = datetime.now(UTC)
                self._session.add(issue)
                await self._session.flush()
                await sender(
                    self._build_text(session_id, f"删除失败：{target_path} - {exc}").model_dump()
                )
                return ExecResult(
                    success=False,
                    output=None,
                    error=str(exc),
                    branch=None,
                )

        file_changes: dict[str, str] = {}
        if edited_after is not None:
            await sender(
                self._build_text(
                    session_id,
                    f"📝 使用用户编辑的修复内容，跳过 AI 重新生成：{target_path}",
                ).model_dump()
            )
            file_changes[target_path] = edited_after
        else:
            await sender(
                self._build_text(
                    session_id,
                    f"🤖 AI 正在读取上下文并生成修复代码：{target_path}",
                ).model_dump()
            )
            try:
                prompt = self._prompt_assembler.assemble_arch_fix_prompt(
                    change,
                    project_id,
                    user_hint=user_hint,
                )
                await sender(
                    self._build_thinking(session_id, "AI 正在分析问题并生成修复方案...").model_dump()
                )

                collected_chunks: list[str] = []

                async def _on_chunk(chunk: str) -> None:
                    collected_chunks.append(chunk)
                    await sender(
                        self._build_thinking(session_id, chunk).model_dump()
                    )

                llm_output = await self._llm_gateway.generate_stream(
                    prompt, on_chunk=_on_chunk
                )
                file_changes = AIOutputParser.parse_file_changes(
                    llm_output, fallback_target=target_path
                )
                sections = AIOutputParser.parse_sections(llm_output)
                if sections.get("root_cause"):
                    await sender(
                        self._build_text(
                            session_id,
                            f"【根因分析】{sections['root_cause']}",
                        ).model_dump()
                    )
                if sections.get("strategy"):
                    await sender(
                        self._build_text(
                            session_id,
                            f"【修复策略】{sections['strategy']}",
                        ).model_dump()
                    )
                await sender(
                    self._build_text(
                        session_id,
                        f"✅ AI 已生成 {len(file_changes)} 个文件的修复代码",
                    ).model_dump()
                )
            except Exception as exc:  # noqa: BLE001
                import traceback
                tb = traceback.format_exc()
                print(f"[ARCH FIX] LLM error: {exc!r}\n{tb}")
                await sender(
                    self._build_text(
                        session_id,
                        f"⚠️ AI 调用失败，使用原始修复方案继续执行：{exc!r}",
                    ).model_dump()
                )
                file_changes = {target_path: change.get("after", "")}

        # Create a dedicated fix branch before touching the filesystem.
        branch_name: str | None = None
        original_branch: str | None = None
        if self._git_service.is_repo():
            original_branch = self._git_service.current_branch()
            branch_name = self._git_service.branch_name_for_change(
                issue_id or target_path.replace("/", "-")
            )
            branch_result = self._git_service.create_branch(branch_name)
            if branch_result["success"]:
                await sender(
                    self._build_text(
                        session_id,
                        f"🌿 已创建修复分支：{branch_name}",
                    ).model_dump()
                )
            else:
                await sender(
                    self._build_text(
                        session_id,
                        f"⚠️ 无法创建修复分支，继续无分支执行：{branch_result.get('error')}",
                    ).model_dump()
                )
                branch_name = None

        applied: list[dict[str, Any]] = []
        errors: list[str] = []
        for path, content in file_changes.items():
            try:
                result = await self._apply_file_change(
                    session_id=session_id,
                    project_id=project_id,
                    target_path=path,
                    action=action,
                    content=content,
                )
                applied.append({"path": path, "result": result})
                await sender(
                    self._build_text(
                        session_id,
                        f"已执行：{path} ({result.get('bytes', 0)} bytes)",
                    ).model_dump()
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{path}: {exc}")
                await sender(
                    self._build_text(session_id, f"执行失败：{path} - {exc}").model_dump()
                )

        if errors and not applied:
            if branch_name:
                self._git_service.reset_hard("HEAD")
                if original_branch:
                    self._git_service.checkout(original_branch)
                await sender(
                    self._build_text(
                        session_id,
                        f"🔄 已回滚修复分支 {branch_name} 并切回 {original_branch}",
                    ).model_dump()
                )
            issue.status = ArchIssueStatus.DETECTED
            issue.exec_result = {"errors": errors, "branch": branch_name}
            issue.updated_at = datetime.now(UTC)
            self._session.add(issue)
            await self._session.flush()
            return ExecResult(
                success=False,
                output=None,
                error="; ".join(errors),
                branch=branch_name,
            )

        # Run project-level validation before committing.
        validation = await self._validation_service.validate_project()
        if not validation["ok"]:
            # Restore all applied files from backups.
            for item in applied:
                rel_backup = item["result"].get("backup_path")
                if not rel_backup:
                    continue
                backup_path = self._file_backup.project_root / rel_backup
                target_abs = self._file_backup.resolve_target(
                    item["path"], project_id
                )
                try:
                    self._file_backup.restore(backup_path, target_abs)
                except Exception as restore_exc:  # noqa: BLE001
                    await sender(
                        self._build_text(
                            session_id,
                            f"⚠️ 回滚文件失败：{item['path']} - {restore_exc}",
                        ).model_dump()
                    )

            if branch_name:
                self._git_service.reset_hard("HEAD")
                if original_branch:
                    self._git_service.checkout(original_branch)
                await sender(
                    self._build_text(
                        session_id,
                        f"🔄 验证失败，已回滚修复分支 {branch_name} 并切回 {original_branch}",
                    ).model_dump()
                )

            issue.status = ArchIssueStatus.DETECTED
            issue.exec_result = {
                "errors": errors,
                "branch": branch_name,
                "validation": validation,
            }
            issue.updated_at = datetime.now(UTC)
            self._session.add(issue)
            await self._session.flush()
            return ExecResult(
                success=False,
                output=None,
                error=validation.get("error", "Validation failed"),
                branch=branch_name,
            )

        await sender(
            self._build_text(
                session_id,
                "✅ 项目级验证通过",
            ).model_dump()
        )

        # Commit the fix if we are on a dedicated branch.
        commit_info: dict[str, Any] | None = None
        if branch_name:
            commit_result = self._git_service.commit(
                f"fix(arch): {change.get('rationale', 'governance fix')[:50]}"
            )
            commit_info = commit_result
            if commit_result["success"]:
                await sender(
                    self._build_text(
                        session_id,
                        f"📝 已提交修复到分支 {branch_name}",
                    ).model_dump()
                )
            else:
                await sender(
                    self._build_text(
                        session_id,
                        f"⚠️ 文件已写入，但提交失败：{commit_result.get('error')}",
                    ).model_dump()
                )

        issue.status = ArchIssueStatus.EXECUTED
        issue.executed_at = datetime.now(UTC)
        issue.updated_at = datetime.now(UTC)
        issue.backup_path = applied[0]["result"].get("backup_path")
        issue.change_data = change
        issue.exec_result = {
            "applied": applied,
            "errors": errors,
            "branch": branch_name,
            "commit": commit_info,
        }
        self._session.add(issue)
        await self._session.flush()

        summary = f"Applied {len(applied)} file(s)"
        if errors:
            summary += f", {len(errors)} failed"
        return ExecResult(
            success=True,
            output=summary,
            error="; ".join(errors) if errors else None,
            branch=branch_name,
        )

    async def _apply_file_change(
        self,
        session_id: str,
        project_id: str,
        target_path: str,
        action: str,
        content: str | None,
    ) -> dict[str, Any]:
        """Backup, apply and verify a single file change.

        Args:
            session_id: CLI session ID.
            project_id: Project ID.
            target_path: Relative target path.
            action: Change action.
            content: New file content, or None for deletions.

        Returns:
            Execution metadata including ``backup_path``.
        """
        absolute_path = self._file_backup.resolve_target(target_path, project_id)
        backup_path = self._file_backup.backup(absolute_path, session_id)
        result = self._file_backup.apply_change(
            absolute_path, action, content, backup_path
        )
        verify = self._file_backup.verify(absolute_path, content)
        if not verify["ok"]:
            self._file_backup.restore(backup_path, absolute_path)
            raise RuntimeError(verify["error"])

        return {
            **result,
            "verified": verify,
            "backup_path": str(
                backup_path.relative_to(self._file_backup.project_root).as_posix()
            ),
        }

    async def optimize_change(
        self,
        project_id: str,
        prompt: str,
        change: dict[str, Any],
    ) -> dict[str, Any]:
        """Optimize a single change using the AI gateway.

        Args:
            project_id: Project ID.
            prompt: User optimization prompt.
            change: Original change dict.

        Returns:
            Optimized change dict.
        """
        target_path = change.get("target_path", "")
        action = change.get("action", "UPDATE_CODE")
        after = change.get("after", "")
        rationale = change.get("rationale", "")

        system_prompt = (
            "You are an expert software architect. Given a proposed file change, "
            "refine the change according to the user's instruction. Return only the "
            "new file content for the 'after' field; do not add explanations."
        )
        user_prompt = (
            f"Project: {project_id}\n"
            f"File: {target_path}\n"
            f"Action: {action}\n"
            f"Rationale: {rationale}\n"
            f"Current content:\n```\n{after}\n```\n\n"
            f"Instruction: {prompt}\n\n"
            "Provide the improved content."
        )

        try:
            optimized = await self._ai_gateway.chat(
                system=system_prompt,
                user=user_prompt,
            )
        except Exception:  # noqa: BLE001
            optimized = after

        optimized_change = dict(change)
        optimized_change["after"] = optimized.strip()
        return optimized_change

    async def _get_or_create_issue(
        self,
        session_id: str,
        project_id: str,
        issue_id: str,
        change: dict[str, Any],
    ) -> ArchIssue:
        """Fetch or create an ArchIssue record for a change.

        Args:
            session_id: CLI session ID.
            project_id: Project ID.
            issue_id: Issue ID from the change.
            change: Change metadata.

        Returns:
            ArchIssue instance.
        """
        if issue_id:
            issue = await self._session.get(ArchIssue, issue_id)
            if issue is not None:
                return issue

        # Only link to session if it exists; otherwise leave FK null.
        from app.models.cli_session import CliSession

        session = await self._session.get(CliSession, session_id)
        linked_session_id = session_id if session is not None else None

        issue = ArchIssue(
            id=f"ARCH-{uuid.uuid4()}",
            project_id=project_id,
            session_id=linked_session_id,
            issue_type=change.get("action", "UPDATE_CODE"),
            severity="warning",
            rule_id=change.get("rule_id"),
            title=f"{change.get('action')} {change.get('target_path')}",
            description=change.get("rationale"),
            location=change.get("target_path"),
            status=ArchIssueStatus.DETECTED,
        )
        self._session.add(issue)
        await self._session.flush()
        return issue

    @staticmethod
    def _build_decision_card(
        change: dict[str, Any], strategy_prompt: str = ""
    ) -> dict[str, Any]:
        """Build an arch-decision CLI card from a change dict."""
        return {
            "type": "arch-decision",
            "data": {
                "change": change,
                "strategy_prompt": strategy_prompt,
                "action": change.get("action"),
                "target_path": change.get("target_path"),
                "before": change.get("before"),
                "after": change.get("after"),
                "rationale": change.get("rationale"),
                "risk_level": change.get("risk_level"),
                "requires_confirmation": change.get("requires_confirmation", True),
                "issue_id": change.get("issue_id"),
            },
            "actions": [
                {"label": "执行", "command": "fix", "style": "primary"},
                {"label": "跳过", "command": "skip", "style": "default"},
                {"label": "编辑", "command": "edit", "style": "default"},
            ],
        }

    @staticmethod
    def _build_text(session_id: str, text: str) -> Any:
        """Build a text CLI response using the schema model."""
        from app.schemas.cli import CliResponse, CliResponsePayload

        return CliResponse(
            type="text",
            session_id=session_id,
            timestamp=_now_ms(),
            payload=CliResponsePayload.model_construct(text=text),
        )

    @staticmethod
    def _build_thinking(session_id: str, text: str) -> Any:
        """Build a thinking CLI response for streaming AI reasoning."""
        from app.schemas.cli import CliResponse, CliResponsePayload

        return CliResponse(
            type="thinking",
            session_id=session_id,
            timestamp=_now_ms(),
            payload=CliResponsePayload.model_construct(text=text),
        )

    @staticmethod
    def _build_progress(session_id: str, current: int, total: int, label: str) -> Any:
        """Build a progress CLI response."""
        from app.schemas.cli import CliProgressPayload, CliResponse, CliResponsePayload

        return CliResponse(
            type="progress",
            session_id=session_id,
            timestamp=_now_ms(),
            payload=CliResponsePayload.model_construct(
                progress=CliProgressPayload(current=current, total=total, label=label)
            ),
        )

    @staticmethod
    def _build_card(session_id: str, card: dict[str, Any]) -> Any:
        """Build a card CLI response."""
        from app.schemas.cli import CliCard, CliResponse, CliResponsePayload

        return CliResponse(
            type="card",
            session_id=session_id,
            timestamp=_now_ms(),
            payload=CliResponsePayload.model_construct(
                card=CliCard.model_validate(card)
            ),
        )

    @staticmethod
    def _build_done(session_id: str, summary: dict[str, Any]) -> Any:
        """Build a done CLI response."""
        from app.schemas.cli import CliResponse, CliResponsePayload

        return CliResponse(
            type="done",
            session_id=session_id,
            timestamp=_now_ms(),
            payload=CliResponsePayload.model_construct(
                text=f"修复计划已推送：{summary}"
            ),
        )

    async def scan_filesystem(
        self,
        project_path: str,
        rules: list[str] | None = None,
    ) -> list[ArchIssueResponse]:
        """Stub filesystem scanner.

        Args:
            project_path: Path to the project root.
            rules: Optional rule IDs to apply.

        Returns:
            Empty list; real implementation would inspect files.
        """
        path = Path(project_path)
        if not path.exists():
            return []
        return []


def _now_ms() -> int:
    """Return the current Unix timestamp in milliseconds."""
    return int(datetime.now(UTC).timestamp() * 1000)
