"""Project context manager using ContextVar."""

from __future__ import annotations

from contextvars import ContextVar, Token
from pathlib import Path
from typing import Any

from git import Repo

_project_ctx: ContextVar[str | None] = ContextVar("project_id", default=None)


class ProjectContext:
    """Manage project directory and Git repo.

    Usage::

        async with ProjectContext(pid, base_dir="./projects") as ctx:
            content = ctx.read_artifact("design.md")
            ctx.write_artifact("output.md", "# Result")
    """

    def __init__(self, project_id: str, base_dir: str = "./projects") -> None:
        self.project_id = project_id
        self.base_dir = Path(base_dir)
        self.project_dir = self.base_dir / project_id
        self.artifacts_dir = self.project_dir / "artifacts"
        self.logs_dir = self.project_dir / "logs"
        self.dsl_dir = self.project_dir / "dsl"
        self._repo: Repo | None = None
        self._token: Token[str | None] | None = None

    def __enter__(self) -> ProjectContext:
        self._token = _project_ctx.set(self.project_id)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.dsl_dir.mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, *args: Any) -> None:
        if self._token:
            _project_ctx.reset(self._token)

    async def __aenter__(self) -> ProjectContext:
        return self.__enter__()

    async def __aexit__(self, *args: Any) -> None:
        self.__exit__(*args)

    @property
    def repo(self) -> Repo:
        """Lazy-load Git repository."""
        if self._repo is None:
            git_dir = self.project_dir / ".git"
            if git_dir.exists():
                self._repo = Repo(self.project_dir)
            else:
                self._repo = Repo.init(self.project_dir)
        return self._repo

    def read_artifact(self, relative_path: str) -> str:
        """Read artifact file as text."""
        full_path = self.artifacts_dir / relative_path
        if not full_path.exists():
            raise FileNotFoundError(
                f"Artifact not found: {relative_path} in project {self.project_id}"
            )
        return full_path.read_text(encoding="utf-8")

    def write_artifact(self, relative_path: str, content: str) -> Path:
        """Write artifact file as text."""
        full_path = self.artifacts_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return full_path

    def get_dsl_path(self, filename: str = "arsitect.aac.yml") -> Path:
        """Return DSL file path."""
        return self.dsl_dir / filename


def get_current_project_id() -> str | None:
    """Return current project ID from context."""
    return _project_ctx.get()
