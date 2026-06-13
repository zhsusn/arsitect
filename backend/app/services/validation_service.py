"""Post-fix validation helpers.

Runs lightweight project-level checks after AI CLI changes are applied.
Verification is best-effort: failures are reported so the caller can decide
whether to roll back.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.core.config import settings


class ValidationService:
    """Validate changed files and the project after a fix."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize with a project root.

        Args:
            project_root: Base directory for validation commands. Defaults to
                the configured project root.
        """
        self._project_root = (project_root or settings.project_root).resolve()

    async def validate_file(self, path: Path) -> dict[str, Any]:
        """Run a per-file syntax check.

        Args:
            path: Absolute path to the changed file.

        Returns:
            Dict with ``ok`` and optional ``error``.
        """
        if not path.exists():
            return {"ok": True}

        suffix = path.suffix.lower()
        if suffix == ".py":
            import py_compile

            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                return {"ok": False, "error": f"Python syntax error: {exc}"}

        return {"ok": True}

    async def validate_project(
        self,
        changed_paths: list[Path] | None = None,
    ) -> dict[str, Any]:
        """Run project-level build/test commands if configuration is detected.

        Currently supports:

        - Python projects with ``pyproject.toml`` -> ``python -m pytest -q``
        - Node projects with ``package.json`` -> ``npm run build``

        Args:
            changed_paths: Optional list of changed files for reporting.

        Returns:
            Dict with ``ok``, ``checks`` and optional ``error``.
        """
        checks: list[dict[str, Any]] = []

        pyproject = self._project_root / "pyproject.toml"
        package_json = self._project_root / "package.json"

        if pyproject.exists():
            result = await self._run_command(
                ["python", "-m", "pytest", "-q"],
                cwd=self._project_root / "backend",
            )
            checks.append({"name": "pytest", "ok": result["ok"], "output": result["output"]})
            if not result["ok"]:
                return {
                    "ok": False,
                    "error": f"pytest failed:\n{result['output']}",
                    "checks": checks,
                }

        if package_json.exists():
            result = await self._run_command(
                ["npm", "run", "build"],
                cwd=self._project_root / "frontend",
            )
            checks.append({"name": "npm-build", "ok": result["ok"], "output": result["output"]})
            if not result["ok"]:
                return {
                    "ok": False,
                    "error": f"npm run build failed:\n{result['output']}",
                    "checks": checks,
                }

        return {"ok": True, "checks": checks}

    @staticmethod
    async def _run_command(
        cmd: list[str],
        cwd: Path,
        timeout: float = 120.0,
    ) -> dict[str, Any]:
        """Run a subprocess command asynchronously.

        Args:
            cmd: Command and arguments.
            cwd: Working directory.
            timeout: Maximum runtime in seconds.

        Returns:
            Dict with ``ok``, ``output`` and ``returncode``.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            output = stdout.decode("utf-8", errors="replace")
            return {
                "ok": proc.returncode == 0,
                "output": output,
                "returncode": proc.returncode,
            }
        except TimeoutError:
            if proc.returncode is None:
                proc.kill()
                await proc.wait()
            return {"ok": False, "output": "Command timed out", "returncode": -1}
        except FileNotFoundError as exc:
            return {"ok": False, "output": f"Command not found: {exc}", "returncode": -1}
