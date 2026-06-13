"""PermissionManager — project-level RBAC."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.project_member import ProjectMember


class Role(StrEnum):
    """Project roles ordered by privilege."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VISITOR = "visitor"


class Permission(StrEnum):
    """Fine-grained permissions."""

    PROJECT_READ = "project:read"
    PROJECT_WRITE = "project:write"
    PROJECT_DELETE = "project:delete"
    SKILL_EXECUTE = "skill:execute"
    SKILL_EDIT = "skill:edit"
    GATE_APPROVE = "gate:approve"
    GATE_BYPASS = "gate:bypass"
    DSL_EDIT = "dsl:edit"
    SETTINGS_READ = "settings:read"
    SETTINGS_WRITE = "settings:write"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.OWNER: set(Permission),
    Role.ADMIN: {
        Permission.PROJECT_READ,
        Permission.PROJECT_WRITE,
        Permission.SKILL_EXECUTE,
        Permission.SKILL_EDIT,
        Permission.GATE_APPROVE,
        Permission.GATE_BYPASS,
        Permission.DSL_EDIT,
        Permission.SETTINGS_READ,
        Permission.SETTINGS_WRITE,
    },
    Role.MEMBER: {
        Permission.PROJECT_READ,
        Permission.PROJECT_WRITE,
        Permission.SKILL_EXECUTE,
        Permission.GATE_APPROVE,
        Permission.DSL_EDIT,
        Permission.SETTINGS_READ,
    },
    Role.VISITOR: {
        Permission.PROJECT_READ,
        Permission.SETTINGS_READ,
    },
}


@dataclass
class MemberInfo:
    """Member info returned by PermissionManager."""

    user_id: str
    project_id: str
    role: str


class PermissionManager:
    """Permission manager.

    Responsibilities:
    1. Role-based access control.
    2. Project-level isolation.
    3. Gate bypass approval authorization.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._session = session

    async def get_user_role(
        self, user_id: str, project_id: str
    ) -> Role | None:
        """Fetch user's role in a project."""
        result = await self._session.execute(
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .where(ProjectMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()
        if member is None:
            return None
        try:
            return Role(member.role)
        except ValueError:
            return None

    async def has_permission(
        self, user_id: str, project_id: str, permission: Permission
    ) -> bool:
        """Check whether user has a permission in a project."""
        role = await self.get_user_role(user_id, project_id)
        if role is None:
            return False
        return permission in ROLE_PERMISSIONS.get(role, set())

    async def can_bypass_gate(
        self, user_id: str, project_id: str
    ) -> bool:
        """Check whether user can bypass a gate."""
        return await self.has_permission(
            user_id, project_id, Permission.GATE_BYPASS
        )

    async def assign_role(
        self, project_id: str, user_id: str, role: Role
    ) -> ProjectMember:
        """Assign or update a user's role in a project."""
        result = await self._session.execute(
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .where(ProjectMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()
        if member is None:
            member = ProjectMember(
                project_id=project_id,
                user_id=user_id,
                role=role.value,
            )
            self._session.add(member)
        else:
            member.role = role.value
        await self._session.flush()
        return member

    async def list_members(self, project_id: str) -> list[MemberInfo]:
        """List members of a project."""
        result = await self._session.execute(
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.joined_at)
        )
        return [
            MemberInfo(
                user_id=m.user_id,
                project_id=m.project_id,
                role=m.role,
            )
            for m in result.scalars().all()
        ]

    async def remove_member(self, project_id: str, user_id: str) -> None:
        """Remove a member from a project."""
        result = await self._session.execute(
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .where(ProjectMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise NotFoundError(
                detail=f"Member '{user_id}' not found in project '{project_id}'"
            )
        await self._session.delete(member)
        await self._session.flush()
