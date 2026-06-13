"""Artifact Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArtifactTreeFileDTO(BaseModel):
    """File entry in artifact tree."""

    artifact_id: str = Field(description="产物ID")
    file_name: str = Field(description="文件名")
    file_type: str = Field(description="文件类型")
    file_size_bytes: int = Field(description="文件大小（字节）")
    current_version: int = Field(description="当前版本号")
    external_status: str = Field(description="外部状态")
    stale_flag: bool = Field(description="过期标记")
    updated_at: str | None = Field(default=None, description="更新时间")


class ArtifactTreeDirectoryDTO(BaseModel):
    """Directory entry in artifact tree."""

    directory: str = Field(description="目录路径")
    files: list[ArtifactTreeFileDTO] = Field(description="文件列表")


class ArtifactContentDTO(BaseModel):
    """Artifact content response."""

    artifact_id: str = Field(description="产物ID")
    content: str = Field(description="文件内容")
    total_lines: int = Field(default=0, description="总行数")
    content_hash: str = Field(default="", description="内容哈希")
    is_partial: bool = Field(default=False, description="是否为部分内容")


class SaveContentRequestDTO(BaseModel):
    """Request to save artifact content."""

    content: str = Field(description="文件内容")
    expected_hash: str | None = Field(
        default=None, description="预期的内容哈希，用于冲突检测"
    )


class ArtifactVersionDTO(BaseModel):
    """Artifact version snapshot."""

    model_config = ConfigDict(from_attributes=True)

    version_id: str = Field(description="版本ID")
    artifact_id: str = Field(description="产物ID")
    version_number: int = Field(description="版本号")
    operation_type: str = Field(description="操作类型")
    created_by: str | None = Field(default=None, description="创建人")
    created_at: datetime = Field(description="创建时间")


class DiffResponseDTO(BaseModel):
    """Diff between two versions."""

    from_version: int = Field(description="起始版本")
    to_version: int = Field(description="目标版本")
    from_content: str = Field(description="起始版本内容")
    to_content: str = Field(description="目标版本内容")


class ArtifactStatusDTO(BaseModel):
    """Artifact status response."""

    artifact_id: str = Field(description="产物ID")
    external_status: str = Field(description="外部状态")
    file_size_bytes: int = Field(description="文件大小（字节）")
    current_version: int = Field(description="当前版本号")
    content_hash: str = Field(default="", description="内容哈希")
    updated_at: str | None = Field(default=None, description="更新时间")
