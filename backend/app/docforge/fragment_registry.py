"""FragmentRegistry — document fragment lifecycle CRUD + state machine."""

from __future__ import annotations

import contextlib
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fragment import Fragment


@dataclass
class FragmentCreateDTO:
    """DTO for fragment creation."""

    project_id: str
    title: str
    slug: str
    doc_type: str
    content: str
    module_id: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class FragmentDTO:
    """DTO for fragment read."""

    fragment_id: str
    project_id: str
    module_id: str | None
    title: str
    slug: str
    doc_type: str
    content: str
    state: str
    version_number: int
    content_hash: str
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class FragmentRegistry:
    """Fragment lifecycle manager.

    State machine::

        DRAFT --> REVIEW --> APPROVED --> DEPRECATED
          ^         |
          +---------+ (REJECTED)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def create(self, dto: FragmentCreateDTO) -> FragmentDTO:
        content_hash = hashlib.sha256(dto.content.encode()).hexdigest()
        meta_str = ""
        if dto.metadata:
            import json

            meta_str = json.dumps(dto.metadata, ensure_ascii=False)

        fragment = Fragment(
            project_id=dto.project_id,
            module_id=dto.module_id,
            title=dto.title,
            slug=dto.slug,
            doc_type=dto.doc_type,
            content=dto.content,
            content_hash=content_hash,
            state="DRAFT",
            version_number=1,
            metadata_json=meta_str,
        )
        self.db.add(fragment)
        await self.db.flush()
        await self.db.refresh(fragment)
        return self._to_dto(fragment)

    async def get(self, fragment_id: str) -> FragmentDTO | None:
        result = await self.db.execute(select(Fragment).where(Fragment.fragment_id == fragment_id))
        fragment = result.scalar_one_or_none()
        return self._to_dto(fragment) if fragment else None

    async def list_by_project(
        self, project_id: str, doc_type: str | None = None
    ) -> list[FragmentDTO]:
        query = select(Fragment).where(Fragment.project_id == project_id)
        if doc_type:
            query = query.where(Fragment.doc_type == doc_type)
        result = await self.db.execute(query)
        return [self._to_dto(f) for f in result.scalars().all()]

    async def update_content(self, fragment_id: str, new_content: str) -> FragmentDTO:
        fragment = await self._get_entity(fragment_id)
        if fragment.state != "DRAFT":
            raise ValueError(f"Cannot update: state is {fragment.state}, expected DRAFT")
        fragment.content = new_content
        fragment.content_hash = hashlib.sha256(new_content.encode()).hexdigest()
        fragment.version_number += 1
        await self.db.flush()
        return self._to_dto(fragment)

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------
    async def submit_for_review(self, fragment_id: str) -> FragmentDTO:
        return await self._transition(fragment_id, "DRAFT", "REVIEW")

    async def approve(self, fragment_id: str) -> FragmentDTO:
        return await self._transition(fragment_id, "REVIEW", "APPROVED")

    async def reject(self, fragment_id: str) -> FragmentDTO:
        return await self._transition(fragment_id, "REVIEW", "DRAFT")

    async def deprecate(self, fragment_id: str) -> FragmentDTO:
        fragment = await self._get_entity(fragment_id)
        fragment.state = "DEPRECATED"
        await self.db.flush()
        return self._to_dto(fragment)

    # ------------------------------------------------------------------
    # PageSpec query (for SketchGenerator)
    # ------------------------------------------------------------------
    async def get_pagespecs(self, project_id: str) -> list[dict[str, Any]]:
        """Return all PageSpecs from PRD fragment metadata."""
        fragments = await self.list_by_project(project_id, doc_type="PRD")
        pagespecs: list[dict[str, Any]] = []
        import json

        for frag in fragments:
            if frag.metadata and "pagespecs" in frag.metadata:
                pagespecs.extend(frag.metadata["pagespecs"])
            elif frag.metadata_json:
                try:
                    meta = json.loads(frag.metadata_json)
                    if "pagespecs" in meta:
                        pagespecs.extend(meta["pagespecs"])
                except json.JSONDecodeError:
                    pass
        return pagespecs

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    async def _get_entity(self, fragment_id: str) -> Fragment:
        result = await self.db.execute(select(Fragment).where(Fragment.fragment_id == fragment_id))
        fragment = result.scalar_one_or_none()
        if not fragment:
            raise ValueError(f"Fragment not found: {fragment_id}")
        return fragment

    async def _transition(self, fragment_id: str, expected: str, next_state: str) -> FragmentDTO:
        fragment = await self._get_entity(fragment_id)
        if fragment.state != expected:
            raise ValueError(f"Expected {expected}, got {fragment.state}")
        fragment.state = next_state
        await self.db.flush()
        return self._to_dto(fragment)

    @staticmethod
    def _to_dto(fragment: Fragment) -> FragmentDTO:
        metadata = None
        if fragment.metadata_json:
            import json

            with contextlib.suppress(json.JSONDecodeError):
                metadata = json.loads(fragment.metadata_json)
        return FragmentDTO(
            fragment_id=fragment.fragment_id,
            project_id=fragment.project_id,
            module_id=fragment.module_id,
            title=fragment.title,
            slug=fragment.slug,
            doc_type=fragment.doc_type,
            content=fragment.content,
            state=fragment.state,
            version_number=fragment.version_number,
            content_hash=fragment.content_hash,
            metadata=metadata,
            created_at=fragment.created_at,
            updated_at=fragment.updated_at,
        )
