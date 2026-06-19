"""Project review API router."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_

from app.infrastructure.database.session import get_db
from app.models.project_review import ProjectReview
from app.schemas.common import PageResponse
from app.schemas.project_review import (
    ProjectReviewCreateDTO,
    ProjectReviewResponseDTO,
    ProjectReviewUpdateDTO,
)

router = APIRouter(prefix="/projects/{project_id}/reviews", tags=["project_reviews"])


@router.get("", response_model=PageResponse[ProjectReviewResponseDTO])
async def list_project_reviews(
    project_id: str,
    review_type: str | None = None,
    item_type: str | None = None,
    page: int = 1,
    page_size: int = 100,
    db: AsyncSession = Depends(get_db),
) -> PageResponse[ProjectReviewResponseDTO]:
    """List review records for a project with optional filtering."""
    conditions = [ProjectReview.project_id == project_id]
    if review_type:
        conditions.append(ProjectReview.review_type == review_type)
    if item_type:
        conditions.append(ProjectReview.item_type == item_type)
    
    stmt = select(ProjectReview).where(and_(*conditions)).order_by(ProjectReview.created_at)
    result = await db.execute(stmt)
    all_items = result.scalars().all()
    
    total = len(all_items)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_items[start:end]
    
    total_pages = (total + page_size - 1) // page_size
    return PageResponse[ProjectReviewResponseDTO](
        data=[ProjectReviewResponseDTO.model_validate(item) for item in paginated],
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@router.post("", response_model=ProjectReviewResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_project_review(
    project_id: str,
    dto: ProjectReviewCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> ProjectReviewResponseDTO:
    """Create a new review record for a project."""
    # Check if review for this item already exists
    existing_stmt = select(ProjectReview).where(
        and_(
            ProjectReview.project_id == project_id,
            ProjectReview.review_type == dto.review_type,
            ProjectReview.item_id == dto.item_id,
        )
    )
    result = await db.execute(existing_stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing
        existing.status = dto.status or existing.status
        existing.notes = dto.notes or existing.notes
        existing.reviewer_id = dto.reviewer_id or existing.reviewer_id
        await db.commit()
        await db.refresh(existing)
        return ProjectReviewResponseDTO.model_validate(existing)
    
    review = ProjectReview(
        review_id=str(uuid4()),
        project_id=project_id,
        review_type=dto.review_type,
        item_id=dto.item_id,
        item_type=dto.item_type,
        status=dto.status,
        notes=dto.notes,
        reviewer_id=dto.reviewer_id,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return ProjectReviewResponseDTO.model_validate(review)


@router.get("/{review_id}", response_model=ProjectReviewResponseDTO)
async def get_project_review(
    project_id: str,
    review_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectReviewResponseDTO:
    """Get a single review record."""
    stmt = select(ProjectReview).where(
        and_(
            ProjectReview.project_id == project_id,
            ProjectReview.review_id == review_id,
        )
    )
    result = await db.execute(stmt)
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return ProjectReviewResponseDTO.model_validate(review)


@router.put("/{review_id}", response_model=ProjectReviewResponseDTO)
async def update_project_review(
    project_id: str,
    review_id: str,
    dto: ProjectReviewUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> ProjectReviewResponseDTO:
    """Update a review record."""
    stmt = select(ProjectReview).where(
        and_(
            ProjectReview.project_id == project_id,
            ProjectReview.review_id == review_id,
        )
    )
    result = await db.execute(stmt)
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if dto.status is not None:
        review.status = dto.status
    if dto.notes is not None:
        review.notes = dto.notes
    if dto.reviewer_id is not None:
        review.reviewer_id = dto.reviewer_id
    
    await db.commit()
    await db.refresh(review)
    return ProjectReviewResponseDTO.model_validate(review)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_review(
    project_id: str,
    review_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a review record."""
    stmt = select(ProjectReview).where(
        and_(
            ProjectReview.project_id == project_id,
            ProjectReview.review_id == review_id,
        )
    )
    result = await db.execute(stmt)
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    await db.delete(review)
    await db.commit()


@router.post("/batch", response_model=list[ProjectReviewResponseDTO])
async def batch_upsert_project_reviews(
    project_id: str,
    items: list[ProjectReviewCreateDTO],
    db: AsyncSession = Depends(get_db),
) -> list[ProjectReviewResponseDTO]:
    """Batch upsert review records."""
    results: list[ProjectReviewResponseDTO] = []
    for dto in items:
        existing_stmt = select(ProjectReview).where(
            and_(
                ProjectReview.project_id == project_id,
                ProjectReview.review_type == dto.review_type,
                ProjectReview.item_id == dto.item_id,
            )
        )
        result = await db.execute(existing_stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.status = dto.status or existing.status
            existing.notes = dto.notes or existing.notes
            existing.reviewer_id = dto.reviewer_id or existing.reviewer_id
            await db.flush()
            results.append(ProjectReviewResponseDTO.model_validate(existing))
        else:
            review = ProjectReview(
                review_id=str(uuid4()),
                project_id=project_id,
                review_type=dto.review_type,
                item_id=dto.item_id,
                item_type=dto.item_type,
                status=dto.status,
                notes=dto.notes,
                reviewer_id=dto.reviewer_id,
            )
            db.add(review)
            await db.flush()
            results.append(ProjectReviewResponseDTO.model_validate(review))
    
    await db.commit()
    return results
