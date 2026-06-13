#!/usr/bin/env python3
"""Generate interface contract artifacts for the sdlc-visualizer change.

Outputs:
- openspec/changes/sdlc-visualizer/interface-contracts/openapi.yaml
- openspec/changes/sdlc-visualizer/interface-contracts/mock-data.json
- openspec/changes/sdlc-visualizer/interface-contracts/mock-server-config.md
- openspec/changes/sdlc-visualizer/interface-contracts/parallel-dev-plan.md
"""

import json
import yaml
from datetime import datetime
from pathlib import Path

OUT_DIR = Path("openspec/changes/sdlc-visualizer/interface-contracts")

# =============================================================================
# Common / Shared Schemas
# =============================================================================

COMMON_SCHEMAS = {
    "PageRequest": {
        "type": "object",
        "properties": {
            "page": {"type": "integer", "minimum": 1, "default": 1, "description": "页码，从1开始"},
            "page_size": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50, "description": "每页条数"},
            "sort_by": {"type": "string", "description": "排序字段"},
            "sort_order": {"type": "string", "enum": ["asc", "desc"], "default": "desc", "description": "排序方向"},
        },
    },
    "PageResponse": {
        "type": "object",
        "properties": {
            "data": {"type": "array", "items": {}},
            "total_count": {"type": "integer", "description": "总记录数"},
            "page": {"type": "integer", "description": "当前页码"},
            "page_size": {"type": "integer", "description": "每页条数"},
            "total_pages": {"type": "integer", "description": "总页数"},
            "has_next": {"type": "boolean", "description": "是否有下一页"},
            "has_previous": {"type": "boolean", "description": "是否有上一页"},
        },
        "required": ["data", "total_count", "page", "page_size", "total_pages", "has_next", "has_previous"],
    },
    "Problem": {
        "type": "object",
        "description": "RFC 7807 Problem Details",
        "properties": {
            "type": {"type": "string", "format": "uri", "description": "问题类型URI"},
            "title": {"type": "string", "description": "简短可读标题"},
            "status": {"type": "integer", "description": "HTTP状态码"},
            "detail": {"type": "string", "description": "详细描述"},
            "instance": {"type": "string", "format": "uri", "description": "问题发生实例URI"},
        },
        "required": ["type", "title", "status"],
    },
    "HealthCheck": {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
            "version": {"type": "string"},
            "database": {"type": "string", "enum": ["connected", "disconnected"]},
            "uptime_seconds": {"type": "integer"},
            "timestamp": {"type": "string", "format": "date-time"},
        },
        "required": ["status", "version", "database", "timestamp"],
    },
    "FileUploadResult": {
        "type": "object",
        "properties": {
            "file_id": {"type": "string"},
            "file_name": {"type": "string"},
            "file_url": {"type": "string"},
            "file_size_bytes": {"type": "integer"},
            "mime_type": {"type": "string"},
            "uploaded_at": {"type": "string", "format": "date-time"},
            "expires_at": {"type": "string", "format": "date-time", "nullable": True},
        },
        "required": ["file_id", "file_name", "file_url", "mime_type", "uploaded_at"],
    },
    "SearchResult": {
        "type": "object",
        "properties": {
            "result_id": {"type": "string"},
            "entity_type": {"type": "string", "enum": ["project", "artifact", "skill", "gate"]},
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "url_path": {"type": "string"},
            "matched_fields": {"type": "array", "items": {"type": "string"}},
            "score": {"type": "number"},
        },
        "required": ["result_id", "entity_type", "title", "url_path", "score"],
    },
}

# =============================================================================
# Core Entity Schemas (derived from shared/db-schema.md)
# =============================================================================

CORE_ENTITY_SCHEMAS = {
    "Workspace": {
        "type": "object",
        "properties": {
            "workspace_id": {"type": "string", "readOnly": True},
            "workspace_name": {"type": "string", "maxLength": 100},
            "description": {"type": "string", "maxLength": 256, "nullable": True},
            "created_at": {"type": "string", "format": "date-time", "readOnly": True},
            "updated_at": {"type": "string", "format": "date-time", "readOnly": True},
        },
        "required": ["workspace_id", "workspace_name"],
    },
    "Application": {
        "type": "object",
        "properties": {
            "application_id": {"type": "string", "readOnly": True},
            "application_name": {"type": "string", "maxLength": 100},
            "description": {"type": "string", "maxLength": 500, "nullable": True},
            "local_path": {"type": "string", "maxLength": 4096},
            "workspace_id": {"type": "string", "default": "default"},
            "path_accessible": {"type": "boolean", "default": True},
            "last_active_at": {"type": "string", "format": "date-time", "nullable": True},
            "created_at": {"type": "string", "format": "date-time", "readOnly": True},
            "updated_at": {"type": "string", "format": "date-time", "readOnly": True},
        },
        "required": ["application_id", "application_name", "local_path"],
    },
    "Project": {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "readOnly": True},
            "project_name": {"type": "string", "maxLength": 64},
            "project_description": {"type": "string", "maxLength": 256, "nullable": True},
            "project_status": {"type": "string", "enum": ["Draft", "Active", "Archived", "Cancelled"], "default": "Draft"},
            "application_id": {"type": "string"},
            "template_level": {"type": "string", "enum": ["Trivial", "Light", "Standard", "Deep"]},
            "progress_percent": {"type": "integer", "minimum": 0, "maximum": 100, "default": 0},
            "current_stage": {"type": "string", "maxLength": 32, "nullable": True},
            "risk_level": {"type": "string", "enum": ["None", "Low", "Medium", "High"], "default": "None"},
            "last_activity_at": {"type": "string", "format": "date-time", "nullable": True},
            "last_activity_type": {"type": "string", "maxLength": 32, "nullable": True},
            "size_estimate_id": {"type": "string", "nullable": True},
            "created_at": {"type": "string", "format": "date-time", "readOnly": True},
            "updated_at": {"type": "string", "format": "date-time", "readOnly": True},
        },
        "required": ["project_id", "project_name", "application_id", "template_level"],
    },
    "Skill": {
        "type": "object",
        "properties": {
            "skill_id": {"type": "string", "readOnly": True},
            "skill_name": {"type": "string", "maxLength": 128},
            "version": {"type": "string", "maxLength": 32},
            "pattern": {"type": "string", "enum": ["generator", "pipeline", "reviewer", "analyzer", "inversion", "tool-wrapper"]},
            "tags": {"type": "array", "items": {"type": "string"}},
            "platforms": {"type": "array", "items": {"type": "string"}},
            "description": {"type": "string", "maxLength": 512, "nullable": True},
            "directory_path": {"type": "string", "maxLength": 4096},
            "parse_status": {"type": "string", "enum": ["PARSED", "MANUAL_REQUIRED"], "default": "PARSED"},
            "parse_error_reason": {"type": "string", "maxLength": 256, "nullable": True},
            "created_at": {"type": "string", "format": "date-time", "readOnly": True},
            "updated_at": {"type": "string", "format": "date-time", "readOnly": True},
        },
        "required": ["skill_id", "skill_name", "version", "pattern", "directory_path"],
    },
    "Template": {
        "type": "object",
        "properties": {
            "template_id": {"type": "string", "enum": ["Trivial", "Light", "Standard", "Deep"]},
            "template_name": {"type": "string", "maxLength": 64},
            "description": {"type": "string", "maxLength": 256},
            "stage_count": {"type": "integer"},
            "estimated_skill_count": {"type": "integer"},
            "applicable_complexity": {"type": "string", "maxLength": 16},
            "config_json": {"type": "object"},
            "created_at": {"type": "string", "format": "date-time", "readOnly": True},
            "updated_at": {"type": "string", "format": "date-time", "readOnly": True},
        },
        "required": ["template_id", "template_name", "description", "stage_count", "estimated_skill_count", "applicable_complexity", "config_json"],
    },
    "TemplateStage": {
        "type": "object",
        "properties": {
            "stage_id": {"type": "string"},
            "stage_name": {"type": "string", "maxLength": 64},
            "order_index": {"type": "integer"},
            "template_id": {"type": "string", "enum": ["Trivial", "Light", "Standard", "Deep"]},
            "primary_skill_id": {"type": "string", "nullable": True},
            "auxiliary_skill_ids": {"type": "array", "items": {"type": "string"}},
            "gate_id": {"type": "string", "nullable": True},
            "skippable": {"type": "boolean", "default": False},
            "merge_group_id": {"type": "string", "nullable": True},
            "is_present_in": {"type": "string", "enum": ["Trivial", "Light", "Standard", "Deep"], "default": "Standard"},
        },
        "required": ["stage_id", "stage_name", "order_index", "template_id"],
    },
    "ProjectStage": {
        "type": "object",
        "properties": {
            "project_stage_id": {"type": "string", "readOnly": True},
            "project_id": {"type": "string"},
            "stage_id": {"type": "string"},
            "order_index": {"type": "integer"},
            "status": {"type": "string", "enum": ["DEFINED", "SKIPPED", "SCHEDULED", "EXECUTED", "REMOVED", "FROZEN", "ARCHIVED"], "default": "DEFINED"},
            "primary_skill_id": {"type": "string", "nullable": True},
            "skippable": {"type": "boolean", "default": False},
            "is_frozen": {"type": "boolean", "default": False},
            "merge_group_id": {"type": "string", "nullable": True},
            "execution_status": {"type": "string", "default": "NOT_STARTED"},
            "created_at": {"type": "string", "format": "date-time", "readOnly": True},
            "updated_at": {"type": "string", "format": "date-time", "readOnly": True},
        },
        "required": ["project_stage_id", "project_id", "stage_id", "order_index", "status"],
    },
    "StageReviewStatus": {
        "type": "object",
        "properties": {
            "stage_id": {"type": "string"},
            "current_status": {"type": "string", "enum": ["REVIEW_PENDING", "GATE_PENDING", "PASSED", "REVISION_REQUESTED", "REGENERATING"]},
            "previous_status": {"type": "string", "nullable": True},
            "current_version": {"type": "integer", "default": 1},
            "regeneration_batch_id": {"type": "string", "nullable": True},
            "last_submission_id": {"type": "string", "nullable": True},
            "gate_decision_id": {"type": "string", "nullable": True},
            "updated_at": {"type": "string", "format": "date-time"},
        },
        "required": ["stage_id", "current_status"],
    },
    "GateDecision": {
        "type": "object",
        "properties": {
            "decision_id": {"type": "string", "readOnly": True},
            "gate_id": {"type": "string"},
            "project_id": {"type": "string"},
            "gate_type": {"type": "string", "enum": ["1", "2", "2.5", "3", "initiation"]},
            "status": {"type": "string", "enum": ["pending", "passed", "rejected", "bypassed"]},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"], "nullable": True},
            "decision_type": {"type": "string", "enum": ["approve", "reject", "retry", "bypass"], "nullable": True},
            "decision_by": {"type": "string", "nullable": True},
            "decision_at": {"type": "string", "format": "date-time", "nullable": True},
            "duration_sec": {"type": "integer", "minimum": 0, "nullable": True},
            "reason": {"type": "string", "maxLength": 500, "nullable": True},
            "self_check_summary": {"type": "object", "nullable": True},
            "unlocked_stages": {"type": "array", "items": {"type": "string"}},
            "created_at": {"type": "string", "format": "date-time", "readOnly": True},
            "updated_at": {"type": "string", "format": "date-time", "readOnly": True},
        },
        "required": ["decision_id", "gate_id", "project_id", "gate_type", "status"],
    },
    "ArtifactFile": {
        "type": "object",
        "properties": {
            "artifact_id": {"type": "string", "readOnly": True},
            "project_id": {"type": "string"},
            "stage_id": {"type": "string", "nullable": True},
            "skill_id": {"type": "string", "nullable": True},
            "file_name": {"type": "string", "maxLength": 256},
            "file_path": {"type": "string", "maxLength": 4096},
            "file_type": {"type": "string", "enum": ["md", "yaml", "json", "mermaid", "openapi", "txt", "other"]},
            "file_size_bytes": {"type": "integer", "default": 0},
            "current_version": {"type": "integer", "default": 1},
            "external_status": {"type": "string", "enum": ["normal", "modified", "deleted"], "default": "normal"},
            "last_synced_hash": {"type": "string", "maxLength": 64, "nullable": True},
            "last_synced_at": {"type": "string", "format": "date-time", "nullable": True},
            "stale_flag": {"type": "boolean", "default": False},
            "created_at": {"type": "string", "format": "date-time", "readOnly": True},
            "updated_at": {"type": "string", "format": "date-time", "readOnly": True},
        },
        "required": ["artifact_id", "project_id", "file_name", "file_path", "file_type"],
    },
    "ArtifactVersion": {
        "type": "object",
        "properties": {
            "version_id": {"type": "string", "readOnly": True},
            "artifact_id": {"type": "string"},
            "version_number": {"type": "integer"},
            "operation_type": {"type": "string", "enum": ["auto_snapshot", "manual_save", "rollback"]},
            "snapshot_id": {"type": "string", "nullable": True},
            "snapshot_status": {"type": "string", "enum": ["committed", "skipped_size", "skipped_no_repo", "failed"], "nullable": True},
            "content_hash": {"type": "string", "maxLength": 64, "nullable": True},
            "summary": {"type": "string", "maxLength": 512, "nullable": True},
            "created_by": {"type": "string"},
            "created_at": {"type": "string", "format": "date-time", "readOnly": True},
        },
        "required": ["version_id", "artifact_id", "version_number", "operation_type", "created_by"],
    },
    "C4DslStore": {
        "type": "object",
        "properties": {
            "store_id": {"type": "string", "readOnly": True},
            "project_id": {"type": "string"},
            "level": {"type": "string", "enum": ["L1", "L2", "L3", "L4"]},
            "dsl_text": {"type": "string"},
            "generation_mode": {"type": "string", "enum": ["auto", "manual"], "default": "auto"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1, "nullable": True},
            "created_at": {"type": "string", "format": "date-time", "readOnly": True},
            "updated_at": {"type": "string", "format": "date-time", "readOnly": True},
        },
        "required": ["store_id", "project_id", "level", "dsl_text"],
    },
}

# =============================================================================
# Helper functions
# =============================================================================

def make_ref(name: str) -> dict:
    return {"$ref": f"#/components/schemas/{name}"}


def paginated_response(item_schema_ref: str) -> dict:
    return {
        "description": "分页响应",
        "content": {
            "application/json": {
                "schema": {
                    "allOf": [
                        make_ref("PageResponse"),
                        {
                            "properties": {
                                "data": {
                                    "type": "array",
                                    "items": make_ref(item_schema_ref),
                                }
                            }
                        },
                    ]
                }
            }
        },
    }


def problem_response(status: int, title: str) -> dict:
    return {
        "description": title,
        "content": {
            "application/problem+json": {
                "schema": make_ref("Problem"),
                "example": {
                    "type": f"https://api.arsitect.local/errors/{status}",
                    "title": title,
                    "status": status,
                    "detail": "Detailed error message here.",
                    "instance": "/api/v1/example",
                },
            }
        },
    }


def ok_response(schema_ref: str | None = None, description: str = "成功") -> dict:
    resp: dict = {"description": description}
    if schema_ref:
        resp["content"] = {"application/json": {"schema": make_ref(schema_ref)}}
    return resp


def id_path_param(name: str = "id", description: str = "资源唯一标识") -> dict:
    return {"name": name, "in": "path", "required": True, "schema": {"type": "string"}, "description": description}


# =============================================================================
# Endpoint definitions
# Format: (path, method, operation_id, summary, tags, parameters, request_body_schema, response_200_ref, paginated, errors)
# =============================================================================

ENDPOINTS = [
    # -------------------------------------------------------------------------
    # Shared / Global
    # -------------------------------------------------------------------------
    ("/health", "get", "healthCheck", "系统健康检查", ["System"], [], None, "HealthCheck", False, []),
    ("/search", "get", "globalSearch", "全局搜索", ["System"],
     [{"name": "q", "in": "query", "required": True, "schema": {"type": "string", "minLength": 1, "maxLength": 128}},
      {"name": "entity_types", "in": "query", "schema": {"type": "array", "items": {"type": "string", "enum": ["project", "artifact", "skill", "gate"]}}},
      {"name": "project_id", "in": "query", "schema": {"type": "string"}}],
     None, "PageResponse", True, []),
    ("/files/upload", "post", "uploadFile", "通用文件上传", ["System"],
     [], "FileUploadResult", None, False, ["400", "413", "415"]),

    # -------------------------------------------------------------------------
    # DR-001 Project Dashboard
    # -------------------------------------------------------------------------
    ("/applications/{app_id}/projects", "get", "listProjects", "查询项目列表", ["Projects"],
     [id_path_param("app_id", "Application ID")],
     None, "PageResponse", True, ["404"]),
    ("/applications/{app_id}/projects", "post", "createProject", "创建项目", ["Projects"],
     [id_path_param("app_id", "Application ID")],
     "Project", "Project", False, ["400", "409"]),
    ("/projects/{project_id}", "get", "getProject", "获取项目详情", ["Projects"],
     [id_path_param("project_id", "项目ID")],
     None, "Project", False, ["404"]),
    ("/projects/{project_id}", "patch", "updateProject", "更新项目信息", ["Projects"],
     [id_path_param("project_id", "项目ID")],
     "Project", "Project", False, ["400", "404"]),
    ("/projects/{project_id}/archive", "post", "archiveProject", "归档项目", ["Projects"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404", "422"]),
    ("/projects/{project_id}/activate", "post", "activateProject", "项目确认立项", ["Projects"],
     [id_path_param("project_id", "项目ID")],
     None, "Project", False, ["404", "409"]),
    ("/projects/{project_id}/cancel", "post", "cancelProject", "取消项目", ["Projects"],
     [id_path_param("project_id", "项目ID")],
     None, "Project", False, ["404", "409"]),
    ("/applications/{app_id}/risk-alerts", "get", "listAppRiskAlerts", "获取应用风险预警", ["Projects"],
     [id_path_param("app_id", "Application ID")],
     None, None, False, ["404"]),
    ("/projects/{project_id}/risk-alerts", "get", "listProjectRiskAlerts", "获取项目风险详情", ["Projects"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404"]),
    ("/projects/{project_id}/timebox", "get", "getTimebox", "获取Timebox配置", ["Projects"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404"]),
    ("/projects/{project_id}/timebox", "put", "updateTimebox", "更新Timebox配置", ["Projects"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["400", "404"]),

    # -------------------------------------------------------------------------
    # DR-003 Stage Detail
    # -------------------------------------------------------------------------
    ("/stages/{stage_id}/detail", "get", "getStageDetail", "获取Stage详情面板数据", ["Stages"],
     [id_path_param("stage_id", "Stage ID")],
     None, None, False, ["404"]),
    ("/stages/{stage_id}/annotations", "get", "listAnnotations", "获取Stage批注列表", ["Stages"],
     [id_path_param("stage_id", "Stage ID")],
     None, None, False, ["404"]),
    ("/stages/{stage_id}/annotations", "post", "createAnnotation", "创建批注", ["Stages"],
     [id_path_param("stage_id", "Stage ID")],
     None, None, False, ["400", "404"]),
    ("/stages/{stage_id}/annotations/{annotation_id}", "put", "updateAnnotation", "编辑批注", ["Stages"],
     [id_path_param("stage_id", "Stage ID"), id_path_param("annotation_id", "批注ID")],
     None, None, False, ["400", "404"]),
    ("/stages/{stage_id}/annotations/{annotation_id}", "delete", "deleteAnnotation", "删除批注", ["Stages"],
     [id_path_param("stage_id", "Stage ID"), id_path_param("annotation_id", "批注ID")],
     None, None, False, ["404"]),
    ("/stages/{stage_id}/review/submit", "post", "submitReview", "提交审查结果", ["Stages"],
     [id_path_param("stage_id", "Stage ID")],
     None, None, False, ["400", "404", "409"]),
    ("/stages/{stage_id}/regenerate", "post", "triggerRegenerate", "触发重新生成", ["Stages"],
     [id_path_param("stage_id", "Stage ID")],
     None, None, False, ["400", "404", "409"]),
    ("/stages/{stage_id}/versions", "get", "listStageVersions", "获取产物版本历史", ["Stages"],
     [id_path_param("stage_id", "Stage ID")],
     None, None, False, ["404"]),
    ("/stages/{stage_id}/versions/{version_number}/rollback", "post", "rollbackStageVersion", "回滚到指定版本", ["Stages"],
     [id_path_param("stage_id", "Stage ID"), {"name": "version_number", "in": "path", "required": True, "schema": {"type": "integer"}}],
     None, None, False, ["404", "422"]),
    ("/stages/{stage_id}/versions/diff", "get", "diffStageVersions", "版本diff对比", ["Stages"],
     [id_path_param("stage_id", "Stage ID"), {"name": "from_version", "in": "query", "required": True, "schema": {"type": "integer"}}, {"name": "to_version", "in": "query", "required": True, "schema": {"type": "integer"}}],
     None, None, False, ["404"]),

    # -------------------------------------------------------------------------
    # DR-004 Gate Center
    # -------------------------------------------------------------------------
    ("/gates", "get", "listGates", "查询Gate列表", ["Gates"],
     [{"name": "project_id", "in": "query", "required": True, "schema": {"type": "string"}},
      {"name": "gate_type", "in": "query", "schema": {"type": "string"}},
      {"name": "status", "in": "query", "schema": {"type": "string", "enum": ["pending", "passed", "rejected", "bypassed"]}},
      {"name": "sort_by", "in": "query", "schema": {"type": "string"}},
      {"name": "sort_order", "in": "query", "schema": {"type": "string", "enum": ["asc", "desc"]}}],
     None, None, False, []),
    ("/gates/{gate_id}", "get", "getGate", "获取Gate审批详情", ["Gates"],
     [id_path_param("gate_id", "Gate ID")],
     None, None, False, ["404"]),
    ("/gates/{gate_id}/approve", "post", "approveGate", "Gate通过审批", ["Gates"],
     [id_path_param("gate_id", "Gate ID")],
     None, None, False, ["404", "409", "422"]),
    ("/gates/{gate_id}/reject", "post", "rejectGate", "Gate驳回审批", ["Gates"],
     [id_path_param("gate_id", "Gate ID")],
     None, None, False, ["400", "404", "409", "422"]),
    ("/gates/{gate_id}/retry", "post", "retryGate", "重试Gate自检摘要", ["Gates"],
     [id_path_param("gate_id", "Gate ID")],
     None, None, False, ["404"]),
    ("/gates/history", "get", "listGateHistory", "查询Gate决策历史", ["Gates"],
     [{"name": "project_id", "in": "query", "schema": {"type": "string"}},
      {"name": "gate_type", "in": "query", "schema": {"type": "string"}},
      {"name": "decision_type", "in": "query", "schema": {"type": "string", "enum": ["approve", "reject", "retry", "bypass"]}},
      {"name": "start_date", "in": "query", "schema": {"type": "string", "format": "date-time"}},
      {"name": "end_date", "in": "query", "schema": {"type": "string", "format": "date-time"}}],
     None, "PageResponse", True, []),
    ("/gates/history/export", "get", "exportGateHistory", "导出Gate历史记录", ["Gates"],
     [{"name": "project_id", "in": "query", "schema": {"type": "string"}}],
     None, None, False, []),

    # -------------------------------------------------------------------------
    # DR-005 Artifact Viewer
    # -------------------------------------------------------------------------
    ("/artifacts/tree", "get", "getArtifactTree", "获取产物目录树", ["Artifacts"],
     [{"name": "project_id", "in": "query", "required": True, "schema": {"type": "string"}},
      {"name": "search", "in": "query", "schema": {"type": "string"}},
      {"name": "filter_stage", "in": "query", "schema": {"type": "array", "items": {"type": "string"}}},
      {"name": "filter_skill", "in": "query", "schema": {"type": "array", "items": {"type": "string"}}},
      {"name": "filter_type", "in": "query", "schema": {"type": "array", "items": {"type": "string"}}}],
     None, None, False, ["404"]),
    ("/artifacts/{artifact_id}/content", "get", "getArtifactContent", "获取产物文件内容", ["Artifacts"],
     [id_path_param("artifact_id", "产物ID"), {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}}, {"name": "page_size", "in": "query", "schema": {"type": "integer", "default": 100}}],
     None, None, True, ["404"]),
    ("/artifacts/{artifact_id}/content", "put", "saveArtifactContent", "保存产物内容", ["Artifacts"],
     [id_path_param("artifact_id", "产物ID")],
     "ArtifactFile", "ArtifactFile", False, ["400", "404", "409"]),
    ("/artifacts/{artifact_id}/versions", "get", "listArtifactVersions", "获取产物版本历史", ["Artifacts"],
     [id_path_param("artifact_id", "产物ID")],
     None, None, False, ["404"]),
    ("/artifacts/{artifact_id}/versions/diff", "get", "diffArtifactVersions", "产物版本diff对比", ["Artifacts"],
     [id_path_param("artifact_id", "产物ID"), {"name": "from_version", "in": "query", "required": True, "schema": {"type": "integer"}}, {"name": "to_version", "in": "query", "required": True, "schema": {"type": "integer"}}],
     None, None, False, ["404"]),
    ("/artifacts/{artifact_id}/versions/{version_number}/rollback", "post", "rollbackArtifactVersion", "回滚产物版本", ["Artifacts"],
     [id_path_param("artifact_id", "产物ID"), {"name": "version_number", "in": "path", "required": True, "schema": {"type": "integer"}}],
     None, None, False, ["404", "422"]),
    ("/artifacts/{artifact_id}/external-status", "get", "getArtifactExternalStatus", "检测文件外部变更状态", ["Artifacts"],
     [id_path_param("artifact_id", "产物ID")],
     None, None, False, ["404"]),

    # -------------------------------------------------------------------------
    # DR-006 Skill Registry
    # -------------------------------------------------------------------------
    ("/skills/import/scan", "post", "scanSkills", "扫描Skill目录", ["Skills"],
     [], None, None, False, ["400"]),
    ("/skills/import/confirm", "post", "confirmSkillImport", "确认导入Skill", ["Skills"],
     [], None, None, False, ["400", "409"]),
    ("/skills", "get", "listSkills", "查询Skill列表", ["Skills"],
     [{"name": "search", "in": "query", "schema": {"type": "string"}},
      {"name": "pattern", "in": "query", "schema": {"type": "string", "enum": ["generator", "pipeline", "reviewer", "analyzer", "inversion", "tool-wrapper"]}},
      {"name": "status", "in": "query", "schema": {"type": "string", "enum": ["PARSED", "MANUAL_REQUIRED"]}},
      {"name": "platforms", "in": "query", "schema": {"type": "array", "items": {"type": "string"}}}],
     None, None, False, []),
    ("/skills/{skill_id}", "get", "getSkill", "获取Skill详情", ["Skills"],
     [id_path_param("skill_id", "Skill ID")],
     None, "Skill", False, ["404"]),
    ("/skills/{skill_id}", "delete", "deleteSkill", "注销Skill", ["Skills"],
     [id_path_param("skill_id", "Skill ID")],
     None, None, False, ["404"]),
    ("/skills/dag", "get", "getDAG", "获取当前DAG", ["Skills"],
     [], None, None, False, []),
    ("/skills/dag/nodes", "post", "addDAGNode", "添加DAG节点", ["Skills"],
     [], None, None, False, ["400", "409"]),
    ("/skills/dag/nodes/{node_id}", "delete", "deleteDAGNode", "删除DAG节点", ["Skills"],
     [id_path_param("node_id", "节点ID")],
     None, None, False, ["404"]),
    ("/skills/dag/edges", "post", "addDAGEdge", "添加DAG边", ["Skills"],
     [], None, None, False, ["400", "409"]),
    ("/skills/dag/edges/{edge_id}", "delete", "deleteDAGEdge", "删除DAG边", ["Skills"],
     [id_path_param("edge_id", "边ID")],
     None, None, False, ["404"]),
    ("/skills/dag/save", "post", "saveDAG", "保存DAG", ["Skills"],
     [], None, None, False, ["400", "409"]),
    ("/skills/dag/undo", "post", "undoDAG", "撤销DAG操作", ["Skills"],
     [], None, None, False, []),
    ("/skills/dag/redo", "post", "redoDAG", "重做DAG操作", ["Skills"],
     [], None, None, False, []),
    ("/skills/dag/changelog", "get", "listDAGChangelog", "查询DAG变更日志", ["Skills"],
     [{"name": "session_id", "in": "query", "schema": {"type": "string"}}],
     None, None, False, []),

    # -------------------------------------------------------------------------
    # DR-007 Flow Engine
    # -------------------------------------------------------------------------
    ("/projects/{project_id}/execution-plans", "post", "createExecutionPlan", "生成执行计划", ["Execution Plans"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["400", "404", "409"]),
    ("/execution-plans/{plan_id}", "get", "getExecutionPlan", "获取执行计划", ["Execution Plans"],
     [id_path_param("plan_id", "计划ID")],
     None, None, False, ["404"]),
    ("/execution-plans/{plan_id}/validate", "post", "validateExecutionPlan", "校验计划调整", ["Execution Plans"],
     [id_path_param("plan_id", "计划ID")],
     None, None, False, ["400", "404"]),
    ("/execution-plans/{plan_id}/freeze", "post", "freezeExecutionPlan", "冻结执行计划", ["Execution Plans"],
     [id_path_param("plan_id", "计划ID")],
     None, None, False, ["404", "409"]),
    ("/execution-plans/{plan_id}/execute", "post", "executePlan", "启动执行", ["Execution Plans"],
     [id_path_param("plan_id", "计划ID")],
     None, None, False, ["404", "409"]),
    ("/executions/{execution_id}/status", "get", "getExecutionStatus", "查询执行状态", ["Executions"],
     [id_path_param("execution_id", "执行ID")],
     None, None, False, ["404"]),
    ("/executions/{execution_id}/bypass", "post", "bypassExecution", "旁路审批执行", ["Executions"],
     [id_path_param("execution_id", "执行ID")],
     None, None, False, ["400", "404", "409"]),
    ("/executions/{execution_id}/bypass-status", "get", "getBypassStatus", "旁路记录查询", ["Executions"],
     [id_path_param("execution_id", "执行ID")],
     None, None, False, ["404"]),

    # -------------------------------------------------------------------------
    # DR-008 Skill Executor
    # -------------------------------------------------------------------------
    ("/executions/trigger", "post", "triggerExecution", "触发Skill执行", ["Executions"],
     [], None, None, False, ["400", "409"]),
    ("/executions/{execution_id}/logs", "get", "getExecutionLogs", "查询执行日志", ["Executions"],
     [id_path_param("execution_id", "执行ID"), {"name": "keyword", "in": "query", "schema": {"type": "string"}}, {"name": "level", "in": "query", "schema": {"type": "string"}}, {"name": "anchor", "in": "query", "schema": {"type": "string"}}],
     None, None, False, ["404"]),
    ("/executions/{execution_id}/retry", "post", "retryExecution", "重试执行", ["Executions"],
     [id_path_param("execution_id", "执行ID")],
     None, None, False, ["404", "409"]),
    ("/executions/{execution_id}/confirm-release", "post", "confirmRelease", "发布确认", ["Executions"],
     [id_path_param("execution_id", "执行ID")],
     None, None, False, ["400", "404", "409"]),
    ("/executions/{execution_id}/sse", "get", "subscribeExecutionSSE", "SSE状态流订阅", ["Executions"],
     [id_path_param("execution_id", "执行ID")],
     None, None, False, ["404"]),

    # -------------------------------------------------------------------------
    # DR-009 Template Engine
    # -------------------------------------------------------------------------
    ("/templates", "get", "listTemplates", "查询模板列表", ["Templates"],
     [], None, None, False, []),
    ("/templates/{level}", "get", "getTemplate", "获取模板详情", ["Templates"],
     [id_path_param("level", "模板级别").copy()],
     None, "Template", False, ["404"]),
    ("/projects/{project_id}/template-recommendation", "get", "getTemplateRecommendation", "获取推荐模板", ["Templates"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404"]),
    ("/projects/{project_id}/template-deviation/preview", "post", "previewTemplateDeviation", "预览模板偏离影响", ["Templates"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["400", "404"]),
    ("/projects/{project_id}/template-deviation", "post", "confirmTemplateDeviation", "确认模板切换", ["Templates"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["400", "404", "409"]),
    ("/projects/{project_id}/template-deviation", "get", "getTemplateDeviation", "查询当前偏离记录", ["Templates"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404"]),
    ("/projects/{project_id}/stages/{stage_id}/skip", "patch", "toggleStageSkip", "更新跳过标记", ["Templates"],
     [id_path_param("project_id", "项目ID"), id_path_param("stage_id", "Stage ID")],
     None, "ProjectStage", False, ["400", "404", "409"]),
    ("/projects/{project_id}/stages/merge", "post", "mergeStages", "合并Stage", ["Templates"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["400", "404", "409"]),
    ("/projects/{project_id}/stage-sequence", "get", "getStageSequence", "获取Stage序列", ["Templates"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404"]),

    # -------------------------------------------------------------------------
    # DR-010 Complexity Router
    # -------------------------------------------------------------------------
    ("/complexity/triage", "post", "triageComplexity", "执行Triage初估", ["Complexity"],
     [], None, None, False, ["400"]),
    ("/complexity/calculate", "post", "calculateComplexity", "Calibrate实时计算", ["Complexity"],
     [], None, None, False, ["400"]),
    ("/complexity/paths", "get", "listComplexityPaths", "获取四级路径对比", ["Complexity"],
     [{"name": "project_id", "in": "query", "required": True, "schema": {"type": "string"}}],
     None, None, False, ["404"]),
    ("/complexity/select-path", "post", "selectComplexityPath", "确认路径选择", ["Complexity"],
     [], None, None, False, ["400", "409"]),
    ("/complexity/decisions", "get", "listPathDecisions", "获取路径决策日志", ["Complexity"],
     [{"name": "project_id", "in": "query", "required": True, "schema": {"type": "string"}}],
     None, "PageResponse", True, ["404"]),

    # -------------------------------------------------------------------------
    # DR-011 C4 Navigator
    # -------------------------------------------------------------------------
    ("/c4/generate", "post", "generateC4DSL", "自动生成C4 DSL", ["C4"],
     [], None, None, False, ["400", "404"]),
    ("/c4/dsl/{project_id}", "get", "getC4DSL", "获取项目C4 DSL", ["C4"],
     [id_path_param("project_id", "项目ID"), {"name": "level", "in": "query", "schema": {"type": "string", "enum": ["L1", "L2", "L3", "L4"]}}],
     None, None, False, ["404"]),
    ("/c4/dsl/{project_id}/{level}", "put", "saveC4DSL", "保存手动编辑DSL", ["C4"],
     [id_path_param("project_id", "项目ID"), id_path_param("level", "层级")],
     "C4DslStore", None, False, ["400", "404"]),
    ("/c4/export", "post", "exportC4", "导出架构图", ["C4"],
     [], None, None, False, ["400"]),
    ("/c4/nodes/{node_id}/file-mapping", "put", "setC4NodeFileMapping", "设置节点文件映射", ["C4"],
     [id_path_param("node_id", "节点ID")],
     None, None, False, ["400", "404"]),

    # -------------------------------------------------------------------------
    # DR-012 Arch Validation
    # -------------------------------------------------------------------------
    ("/arch-validation/{project_id}/detect", "post", "triggerArchDetection", "手动触发漂移检测", ["Arch Validation"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404", "409"]),
    ("/arch-validation/{project_id}/status", "get", "getArchDetectionStatus", "获取检测会话状态", ["Arch Validation"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404"]),
    ("/arch-validation/{project_id}/diffs", "get", "listArchDiffs", "获取差异列表", ["Arch Validation"],
     [id_path_param("project_id", "项目ID"), {"name": "session_id", "in": "query", "schema": {"type": "string"}}, {"name": "level_filter", "in": "query", "schema": {"type": "array", "items": {"type": "string"}}}, {"name": "type_filter", "in": "query", "schema": {"type": "array", "items": {"type": "string"}}}],
     None, "PageResponse", True, ["404"]),
    ("/arch-validation/{project_id}/diffs/{diff_id}", "get", "getArchDiff", "获取单条差异详情", ["Arch Validation"],
     [id_path_param("project_id", "项目ID"), id_path_param("diff_id", "差异ID")],
     None, None, False, ["404"]),
    ("/arch-validation/{project_id}/scans", "get", "listArchScans", "扫描历史记录", ["Arch Validation"],
     [id_path_param("project_id", "项目ID")],
     None, "PageResponse", True, ["404"]),
    ("/arch-validation/{project_id}/export", "post", "exportArchReport", "导出差异报告", ["Arch Validation"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["400", "404"]),
    ("/arch-validation/{project_id}/config", "get", "getArchScanConfig", "获取扫描配置", ["Arch Validation"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404"]),
    ("/arch-validation/{project_id}/config", "put", "updateArchScanConfig", "更新扫描配置", ["Arch Validation"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["400", "404"]),
    ("/arch-validation/{project_id}/baseline", "get", "getArchBaseline", "获取基线版本信息", ["Arch Validation"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404"]),

    # -------------------------------------------------------------------------
    # DR-013 History
    # -------------------------------------------------------------------------
    ("/history/{app_id}/summary", "get", "getHistorySummary", "获取历史回溯概览", ["History"],
     [id_path_param("app_id", "Application ID")],
     None, None, False, ["404"]),
    ("/history/{app_id}/timeline", "get", "getHistoryTimeline", "获取项目时间线", ["History"],
     [id_path_param("app_id", "Application ID")],
     None, "PageResponse", True, ["404"]),
    ("/history/{app_id}/comparison", "get", "getHistoryComparison", "获取阶段耗时对比", ["History"],
     [id_path_param("app_id", "Application ID")],
     None, None, False, ["404"]),
    ("/history/{app_id}/heatmap", "get", "getHistoryHeatmap", "获取返工热力图", ["History"],
     [id_path_param("app_id", "Application ID")],
     None, None, False, ["404"]),
    ("/history/{app_id}/projects/{project_id}/detail", "get", "getProjectHistoryDetail", "获取单项目执行详情", ["History"],
     [id_path_param("app_id", "Application ID"), id_path_param("project_id", "项目ID")],
     None, None, False, ["404"]),
    ("/history/{app_id}/export", "post", "exportHistory", "导出历史分析报告", ["History"],
     [id_path_param("app_id", "Application ID")],
     None, None, False, ["400", "404"]),

    # -------------------------------------------------------------------------
    # DR-014 Monitoring
    # -------------------------------------------------------------------------
    ("/monitoring/{project_id}/overview", "get", "getMonitoringOverview", "获取监控总览", ["Monitoring"],
     [id_path_param("project_id", "项目ID"), {"name": "change_id", "in": "query", "schema": {"type": "string"}}],
     None, None, False, ["404"]),
    ("/monitoring/{project_id}/stages/{stage_id}/stats", "get", "getStageStats", "获取阶段耗时统计", ["Monitoring"],
     [id_path_param("project_id", "项目ID"), id_path_param("stage_id", "Stage ID")],
     None, None, False, ["404"]),
    ("/monitoring/{project_id}/tokens", "get", "getTokenStats", "获取Token消耗统计", ["Monitoring"],
     [id_path_param("project_id", "项目ID"), {"name": "dimension", "in": "query", "schema": {"type": "string", "enum": ["project", "stage", "skill"], "default": "project"}}, {"name": "time_granularity", "in": "query", "schema": {"type": "string", "enum": ["day", "week", "month"], "default": "day"}}],
     None, None, False, ["404"]),
    ("/monitoring/{project_id}/bottlenecks", "get", "listBottlenecks", "获取瓶颈告警列表", ["Monitoring"],
     [id_path_param("project_id", "项目ID"), {"name": "type_filter", "in": "query", "schema": {"type": "array", "items": {"type": "string", "enum": ["time_bottleneck", "rework_bottleneck", "gate_failed"]}}}, {"name": "severity_filter", "in": "query", "schema": {"type": "string", "enum": ["all", "high", "medium", "low"], "default": "all"}}],
     None, None, False, ["404"]),
    ("/monitoring/{project_id}/members", "get", "listProjectMembers", "获取项目成员列表", ["Monitoring"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404"]),
    ("/monitoring/{project_id}/members", "post", "addProjectMember", "添加项目成员", ["Monitoring"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["400", "403", "404", "409"]),
    ("/monitoring/{project_id}/members/{user_id}/role", "patch", "updateMemberRole", "变更成员角色", ["Monitoring"],
     [id_path_param("project_id", "项目ID"), id_path_param("user_id", "用户ID")],
     None, None, False, ["400", "403", "404", "409", "422"]),
    ("/monitoring/{project_id}/operation-logs", "get", "listOperationLogs", "获取操作日志", ["Monitoring"],
     [id_path_param("project_id", "项目ID")],
     None, "PageResponse", True, ["404"]),
    ("/monitoring/{project_id}/export", "post", "exportDashboard", "导出看板快照", ["Monitoring"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["400", "404"]),

    # -------------------------------------------------------------------------
    # DR-015 App Module
    # -------------------------------------------------------------------------
    ("/applications", "post", "createApplication", "创建Application", ["Applications"],
     [], "Application", "Application", False, ["400", "409"]),
    ("/applications", "get", "listApplications", "查询Application列表", ["Applications"],
     [{"name": "workspace_id", "in": "query", "schema": {"type": "string"}}],
     None, "PageResponse", True, []),
    ("/applications/{app_id}", "get", "getApplication", "获取Application详情", ["Applications"],
     [id_path_param("app_id", "Application ID")],
     None, "Application", False, ["404"]),
    ("/applications/{app_id}", "patch", "updateApplication", "更新Application", ["Applications"],
     [id_path_param("app_id", "Application ID")],
     "Application", "Application", False, ["400", "404", "409"]),
    ("/applications/{app_id}", "delete", "deleteApplication", "删除Application", ["Applications"],
     [id_path_param("app_id", "Application ID")],
     None, None, False, ["404", "409", "422"]),
    ("/applications/{app_id}/path-check", "get", "checkAppPath", "路径可访问性检测", ["Applications"],
     [id_path_param("app_id", "Application ID")],
     None, None, False, ["404"]),
    ("/applications/{app_id}/stats", "get", "getAppStats", "研发管理费统计", ["Applications"],
     [id_path_param("app_id", "Application ID")],
     None, None, False, ["404"]),
    ("/applications/{app_id}/stats/report", "post", "reportAppStats", "执行数据上报", ["Applications"],
     [id_path_param("app_id", "Application ID")],
     None, None, False, ["400", "404"]),
    ("/projects/{project_id}/modules", "post", "createModule", "创建Module", ["Modules"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["400", "404", "409"]),
    ("/projects/{project_id}/modules", "get", "listModules", "查询Module列表", ["Modules"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404"]),
    ("/modules/{module_id}", "patch", "updateModule", "更新Module", ["Modules"],
     [id_path_param("module_id", "模块ID")],
     None, None, False, ["400", "404", "409"]),
    ("/modules/{module_id}", "delete", "deleteModule", "删除Module", ["Modules"],
     [id_path_param("module_id", "模块ID")],
     None, None, False, ["404", "422"]),
    ("/projects/{project_id}/modules/anchor", "post", "anchorModules", "范围锚定", ["Modules"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404", "409"]),
    ("/projects/{project_id}/module-dependencies", "get", "listModuleDependencies", "查询模块依赖", ["Modules"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["404"]),
    ("/projects/{project_id}/module-dependencies", "post", "createModuleDependency", "声明模块依赖", ["Modules"],
     [id_path_param("project_id", "项目ID")],
     None, None, False, ["400", "404", "409"]),

    # -------------------------------------------------------------------------
    # DR-016 PocketFlow
    # -------------------------------------------------------------------------
    ("/pocketflow/execute", "post", "executePocketFlow", "启动PocketFlow执行", ["PocketFlow"],
     [], None, None, False, ["400", "409"]),
    ("/pocketflow/{execution_id}/interrupt", "post", "interruptPocketFlow", "中断PocketFlow执行", ["PocketFlow"],
     [id_path_param("execution_id", "执行ID")],
     None, None, False, ["404", "409"]),
    ("/pocketflow/{execution_id}/status", "get", "getPocketFlowStatus", "查询PocketFlow状态", ["PocketFlow"],
     [id_path_param("execution_id", "执行ID")],
     None, None, False, ["404"]),
    ("/pocketflow/{execution_id}/logs", "get", "getPocketFlowLogs", "查询PocketFlow日志", ["PocketFlow"],
     [id_path_param("execution_id", "执行ID")],
     None, None, False, ["404"]),

    # -------------------------------------------------------------------------
    # DR-017 Bypass
    # -------------------------------------------------------------------------
    ("/bypass/applications", "post", "createBypassApplication", "提交旁路申请", ["Bypass"],
     [], None, None, False, ["400", "409"]),
    ("/bypass/applications/{application_id}", "get", "getBypassApplication", "获取旁路申请详情", ["Bypass"],
     [id_path_param("application_id", "申请ID")],
     None, None, False, ["404"]),
    ("/bypass/applications/{application_id}/authorize", "post", "authorizeBypass", "授权旁路", ["Bypass"],
     [id_path_param("application_id", "申请ID")],
     None, None, False, ["400", "404", "409"]),
    ("/bypass/applications/{application_id}/reject", "post", "rejectBypass", "拒绝旁路", ["Bypass"],
     [id_path_param("application_id", "申请ID")],
     None, None, False, ["400", "404", "409"]),
    ("/bypass/applications/{application_id}/execute-start", "post", "startBypassExecution", "标记旁路执行开始", ["Bypass"],
     [id_path_param("application_id", "申请ID")],
     None, None, False, ["400", "404", "409"]),
    ("/bypass/applications/{application_id}/execute-complete", "post", "completeBypassExecution", "标记旁路执行完成", ["Bypass"],
     [id_path_param("application_id", "申请ID")],
     None, None, False, ["400", "404", "409"]),
    ("/bypass/applications/{application_id}/review", "post", "reviewBypass", "提交补审结论", ["Bypass"],
     [id_path_param("application_id", "申请ID")],
     None, None, False, ["400", "404", "409"]),
    ("/bypass/countdown/{application_id}", "get", "getBypassCountdown", "查询补审倒计时", ["Bypass"],
     [id_path_param("application_id", "申请ID")],
     None, None, False, ["404"]),
    ("/bypass/records", "get", "listBypassRecords", "查询旁路记录列表", ["Bypass"],
     [{"name": "project_id", "in": "query", "schema": {"type": "string"}}, {"name": "status", "in": "query", "schema": {"type": "array", "items": {"type": "string"}}}, {"name": "start_date", "in": "query", "schema": {"type": "string", "format": "date-time"}}, {"name": "end_date", "in": "query", "schema": {"type": "string", "format": "date-time"}}],
     None, "PageResponse", True, []),

    # -------------------------------------------------------------------------
    # DR-018 OpenUI
    # -------------------------------------------------------------------------
    ("/openui/status", "get", "getOpenUIStatus", "查询OpenUI服务状态", ["OpenUI"],
     [], None, None, False, []),
    ("/openui/generate", "post", "generatePrototype", "触发原型生成", ["OpenUI"],
     [], None, None, False, ["400", "422", "503"]),
    ("/openui/launch", "post", "launchOpenUIService", "一键启动OpenUI本地服务", ["OpenUI"],
     [], None, None, False, ["409", "503"]),
    ("/openui/history", "get", "listOpenUIHistory", "获取生成历史", ["OpenUI"],
     [{"name": "project_id", "in": "query", "schema": {"type": "string"}}, {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 5}}],
     None, None, False, []),

    # -------------------------------------------------------------------------
    # DR-019 Wireframe
    # -------------------------------------------------------------------------
    ("/wireframe/generate", "post", "generateWireframe", "触发线框图生成", ["Wireframe"],
     [], None, None, False, ["400", "404", "422"]),
    ("/wireframe/mappings/{page_id}", "put", "updateWireframeMapping", "修正页面类型映射", ["Wireframe"],
     [id_path_param("page_id", "页面ID")],
     None, None, False, ["400", "404"]),
    ("/wireframe/missing-interfaces", "post", "markMissingInterfaces", "提交缺失接口标记", ["Wireframe"],
     [], None, None, False, ["400", "404"]),
    ("/wireframe/pages/{page_id}", "get", "getWireframePage", "获取单页线框图详情", ["Wireframe"],
     [id_path_param("page_id", "页面ID")],
     None, None, False, ["404"]),

    # -------------------------------------------------------------------------
    # DR-020 Proto-Arch Binding
    # -------------------------------------------------------------------------
    ("/binding/scan", "post", "scanBinding", "执行接口覆盖度检测", ["Binding"],
     [], None, None, False, ["400", "409"]),
    ("/binding/reports/{scan_id}", "get", "getBindingReport", "获取检测报告", ["Binding"],
     [id_path_param("scan_id", "扫描ID")],
     None, None, False, ["404"]),
    ("/binding/writeback", "post", "writebackBinding", "执行缺失接口回写", ["Binding"],
     [], None, None, False, ["400", "404", "409"]),
    ("/binding/review/{architecture_change_id}", "post", "reviewBinding", "提交Gate评审结论", ["Binding"],
     [id_path_param("architecture_change_id", "架构变更ID")],
     None, None, False, ["400", "404", "409"]),

    # -------------------------------------------------------------------------
    # DR-021 PageSpec Sketch
    # -------------------------------------------------------------------------
    ("/sketches/generate", "post", "generateSketch", "触发草图生成", ["Sketches"],
     [], None, None, False, ["400", "422"]),
    ("/sketches/{sketch_id}/review", "post", "reviewSketch", "提交草图审查批注", ["Sketches"],
     [id_path_param("sketch_id", "草图ID")],
     None, None, False, ["400", "404"]),
    ("/sketches/{sketch_id}/approve", "post", "approveSketch", "批准草图", ["Sketches"],
     [id_path_param("sketch_id", "草图ID")],
     None, None, False, ["404", "409"]),
    ("/sketches/{sketch_id}/reject", "post", "rejectSketch", "驳回草图", ["Sketches"],
     [id_path_param("sketch_id", "草图ID")],
     None, None, False, ["404", "409"]),
    ("/sketches/{sketch_id}/regenerate", "post", "regenerateSketch", "重新生成草图", ["Sketches"],
     [id_path_param("sketch_id", "草图ID")],
     None, None, False, ["404", "409"]),
    ("/sketches", "get", "listSketches", "查询草图列表", ["Sketches"],
     [{"name": "project_id", "in": "query", "required": True, "schema": {"type": "string"}}, {"name": "status", "in": "query", "schema": {"type": "string"}}],
     None, "PageResponse", True, []),
]

# =============================================================================
# Generation logic
# =============================================================================

def build_paths(endpoints):
    paths = {}
    for path, method, op_id, summary, tags, params, req_schema, res_schema, paginated, errors in endpoints:
        method = method.lower()
        if path not in paths:
            paths[path] = {}

        operation = {
            "operationId": op_id,
            "summary": summary,
            "tags": tags,
        }

        # Parameters
        all_params = []
        for p in params:
            param = dict(p)
            if "schema" in param and isinstance(param["schema"], dict):
                pass  # already dict
            all_params.append(param)
        if paginated and method == "get":
            # Inject page request params
            for pname, pschema, pdesc in [
                ("page", {"type": "integer", "minimum": 1, "default": 1}, "页码"),
                ("page_size", {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}, "每页条数"),
            ]:
                if not any(pp.get("name") == pname for pp in all_params):
                    all_params.append({"name": pname, "in": "query", "schema": pschema, "description": pdesc})
        if all_params:
            operation["parameters"] = all_params

        # Request body
        if req_schema and method in ("post", "put", "patch"):
            if isinstance(req_schema, str):
                operation["requestBody"] = {
                    "required": True,
                    "content": {"application/json": {"schema": make_ref(req_schema)}},
                }
            else:
                operation["requestBody"] = req_schema

        # Responses
        responses = {}
        if res_schema:
            if paginated and method == "get":
                responses["200"] = paginated_response(res_schema)
            else:
                responses["200"] = ok_response(res_schema)
        else:
            if method == "delete":
                responses["204"] = {"description": "删除成功"}
            else:
                responses["200"] = {"description": "成功"}

        # Error responses
        error_map = {
            "400": (400, "请求参数校验失败"),
            "401": (401, "未认证"),
            "403": (403, "权限不足"),
            "404": (404, "资源不存在"),
            "409": (409, "资源冲突或非法状态流转"),
            "413": (413, "请求体过大"),
            "415": (415, "不支持的媒体类型"),
            "422": (422, "业务逻辑错误"),
            "429": (429, "请求频率限制"),
            "500": (500, "服务器内部错误"),
            "503": (503, "服务暂时不可用"),
        }
        for ecode in errors:
            if ecode in error_map:
                status, title = error_map[ecode]
                responses[str(status)] = problem_response(status, title)

        # Default error
        if "500" not in errors:
            responses["500"] = problem_response(500, "服务器内部错误")

        operation["responses"] = responses
        paths[path][method] = operation

    return paths


def build_global_responses():
    return {
        "BadRequest": problem_response(400, "请求参数校验失败"),
        "Unauthorized": problem_response(401, "未认证"),
        "NotFound": problem_response(404, "资源不存在"),
        "TooManyRequests": problem_response(429, "请求频率限制"),
        "Conflict": problem_response(409, "资源冲突"),
    }


def generate_openapi():
    openapi = {
        "openapi": "3.1.0",
        "info": {
            "title": "Arsitect SDLC Visualizer API",
            "version": "1.0.0",
            "description": "Arsitect 可视化驾驶舱 REST API 契约（基于详细设计 20/21 模块导出）",
        },
        "servers": [{"url": "/api/v1", "description": "API v1 基线"}],
        "paths": build_paths(ENDPOINTS),
        "components": {
            "schemas": {**COMMON_SCHEMAS, **CORE_ENTITY_SCHEMAS},
            "responses": build_global_responses(),
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "MVP 阶段为本地会话占位，P1 升级为 JWT",
                }
            },
        },
        "tags": [
            {"name": "System", "description": "系统级接口（健康检查、搜索、文件上传）"},
            {"name": "Applications", "description": "Application 与模块治理（DR-015）"},
            {"name": "Projects", "description": "项目工作台（DR-001）"},
            {"name": "Stages", "description": "阶段详情面板（DR-003）"},
            {"name": "Gates", "description": "审批中心（DR-004）"},
            {"name": "Artifacts", "description": "产物浏览器（DR-005）"},
            {"name": "Skills", "description": "Skill 注册与 DAG 管理（DR-006）"},
            {"name": "Execution Plans", "description": "Skill Flow 编排引擎（DR-007）"},
            {"name": "Executions", "description": "Skill 调度与执行（DR-008）"},
            {"name": "Templates", "description": "模板引擎（DR-009）"},
            {"name": "Complexity", "description": "复杂度路由面板（DR-010）"},
            {"name": "C4", "description": "C4 架构浏览器（DR-011）"},
            {"name": "Arch Validation", "description": "架构验证中心（DR-012）"},
            {"name": "History", "description": "历史回溯（DR-013）"},
            {"name": "Monitoring", "description": "监控看板（DR-014）"},
            {"name": "Modules", "description": "模块治理（DR-015）"},
            {"name": "PocketFlow", "description": "PocketFlow 执行引擎（DR-016）"},
            {"name": "Bypass", "description": "HITL 旁路审批（DR-017）"},
            {"name": "OpenUI", "description": "OpenUI 原型服务（DR-018）"},
            {"name": "Wireframe", "description": "WireframeEngine（DR-019）"},
            {"name": "Binding", "description": "原型-架构双向绑定（DR-020）"},
            {"name": "Sketches", "description": "需求草图服务（DR-021）"},
        ],
    }
    return openapi


# =============================================================================
# Mock data generation
# =============================================================================

def generate_mock_data():
    mock = {}
    for path, method, op_id, summary, tags, params, req_schema, res_schema, paginated, errors in ENDPOINTS:
        if method == "get":
            mock[op_id] = {
                "200": {"status": "success", "data": "TODO: replace with real business value"},
                "404": {"type": "https://api.arsitect.local/errors/404", "title": "资源不存在", "status": 404, "detail": f"Resource for {op_id} not found"},
            }
        elif method == "post":
            mock[op_id] = {
                "200": {"status": "created", "id": "mock-id-123"},
                "400": {"type": "https://api.arsitect.local/errors/400", "title": "请求参数校验失败", "status": 400, "detail": "Invalid request body"},
                "409": {"type": "https://api.arsitect.local/errors/409", "title": "资源冲突", "status": 409, "detail": "Conflict detected"},
            }
        elif method in ("put", "patch"):
            mock[op_id] = {
                "200": {"status": "updated"},
                "400": {"type": "https://api.arsitect.local/errors/400", "title": "请求参数校验失败", "status": 400},
            }
        elif method == "delete":
            mock[op_id] = {
                "204": None,
                "404": {"type": "https://api.arsitect.local/errors/404", "title": "资源不存在", "status": 404},
            }
    return mock


# =============================================================================
# Mock server config markdown
# =============================================================================

def generate_mock_config():
    return """# Mock Server Configuration

## 方案一：Prism（推荐）

```bash
# 安装
npm install -g @stoplight/prism-cli

# 启动 Mock 服务
npx @stoplight/prism-cli mock interface-contracts/openapi.yaml -p 4010
```

前端接入示例：
```typescript
const API_BASE = 'http://localhost:4010/api/v1';
fetch(`${API_BASE}/health`).then(r => r.json());
```

## 方案二：JSON Server（备选）

```bash
npx json-server --watch interface-contracts/mock-data.json --port 4010
```

## CORS 配置

Prism 默认允许所有来源。如需限制：
```bash
npx @stoplight/prism-cli mock interface-contracts/openapi.yaml -p 4010 --cors
```

## 延迟模拟

在 Prism 中可通过 `--delay` 参数模拟网络延迟：
```bash
npx @stoplight/prism-cli mock interface-contracts/openapi.yaml -p 4010 --delay 500
```

## 鉴权绕过

MVP 阶段 Mock 服务不校验 Bearer Token，所有接口公开访问。
P1 阶段需配置 `Authorization: Bearer <token>` Header。
"""


# =============================================================================
# Parallel dev plan markdown
# =============================================================================

def generate_parallel_plan():
    return """# Parallel Development Plan

## 接口依赖 DAG

### P0（无依赖，可先行）
- System: `healthCheck`, `globalSearch`, `uploadFile`
- Applications: `createApplication`, `listApplications`, `getApplication`, `updateApplication`, `deleteApplication`
- Projects: `listProjects`, `createProject`, `getProject`, `updateProject`
- Skills: `scanSkills`, `confirmSkillImport`, `listSkills`, `getSkill`, `deleteSkill`, `getDAG`, `addDAGNode`, ...
- Templates: `listTemplates`, `getTemplate`

### P1（依赖 P0 资源创建）
- Projects 状态流转: `archiveProject`, `activateProject`, `cancelProject`
- Stages: `getStageDetail`, `listAnnotations`, `createAnnotation`, ...（依赖 Project 创建）
- Gates: `listGates`, `getGate`, `approveGate`, `rejectGate`, ...（依赖 Stage 推进）
- Artifacts: `getArtifactTree`, `getArtifactContent`, ...（依赖 Stage 执行产物）
- Execution Plans: `createExecutionPlan`, `getExecutionPlan`, ...（依赖 DAG + Template）
- Executions: `triggerExecution`, `getExecutionStatus`, ...（依赖 Execution Plan）

### P2（依赖 P1 执行数据）
- Monitoring: `getMonitoringOverview`, `getStageStats`, ...（依赖 Execution 完成数据）
- History: `getHistorySummary`, `getHistoryTimeline`, ...（依赖 Project 完成归档）
- Arch Validation: `triggerArchDetection`, `listArchDiffs`, ...（依赖 C4 DSL 基线）
- Bypass: `createBypassApplication`, ...（依赖 Gate 阻塞场景）

## 前端任务边界（基于 Mock 可独立完成）

| 页面 | 依赖 Mock 接口 | 可独立度 |
|------|---------------|:-------:|
| 项目工作台 | `listApplications`, `listProjects`, `createProject` | ✅ 完全独立 |
| Skill 注册中心 | `listSkills`, `scanSkills`, `getDAG` | ✅ 完全独立 |
| 模板管理 | `listTemplates`, `getTemplate` | ✅ 完全独立 |
| 阶段详情 | `getStageDetail`, `listAnnotations` | ⚠️ 需 Mock Project/Stage 数据 |
| 审批中心 | `listGates`, `getGate`, `approveGate` | ⚠️ 需 Mock Gate 数据 |
| 产物浏览器 | `getArtifactTree`, `getArtifactContent` | ⚠️ 需 Mock Artifact 数据 |
| 监控看板 | `getMonitoringOverview` | ❌ 依赖真实执行数据 |
| 历史回溯 | `getHistorySummary` | ❌ 依赖真实归档数据 |

## 后端任务边界

| 模块 | 端点数 | 优先级 | 说明 |
|------|:------:|:------:|------|
| System | 3 | P0 | 健康检查、搜索、上传 |
| DR-015 App | 15 | P0 | Application/Module CRUD |
| DR-001 Projects | 11 | P0 | 项目生命周期管理 |
| DR-006 Skills | 14 | P0 | Skill 注册与 DAG |
| DR-009 Templates | 9 | P0 | 模板与 Stage 序列 |
| DR-003 Stages | 10 | P1 | 阶段详情与批注 |
| DR-004 Gates | 7 | P1 | 审批与决策历史 |
| DR-005 Artifacts | 7 | P1 | 产物浏览与版本 |
| DR-007 Plans | 8 | P1 | 执行计划编排 |
| DR-008 Executions | 6 | P1 | Skill 调度执行 |
| DR-010 Complexity | 5 | P1 | 复杂度评估 |
| DR-011 C4 | 5 | P1 | C4 DSL 管理 |
| DR-012 Validation | 9 | P2 | 架构漂移检测 |
| DR-013 History | 6 | P2 | 历史分析 |
| DR-014 Monitoring | 9 | P2 | 监控看板 |
| DR-016 PocketFlow | 4 | P1 | 执行引擎（内部） |
| DR-017 Bypass | 9 | P2 | 旁路审批 |
| DR-018 OpenUI | 4 | P2 | 原型服务 |
| DR-019 Wireframe | 4 | P2 | 线框图引擎 |
| DR-020 Binding | 4 | P2 | 双向绑定 |
| DR-021 Sketches | 6 | P2 | 草图服务 |

## 联调时间点

| 批次 | 接口范围 | 联调条件 | 预计时间 |
|------|----------|----------|----------|
| 联调 1 | System + App + Projects + Skills + Templates | P0 后端完成 | T+3d |
| 联调 2 | Stages + Gates + Artifacts + Plans + Executions | P1 后端完成 | T+7d |
| 联调 3 | Complexity + C4 + Monitoring | P2 后端完成 | T+12d |
| 联调 4 | OpenUI + Wireframe + Binding + Sketches + History | P2 后端全部完成 | T+18d |

## 版本规划

- 当前基线：`/api/v1`
- 破坏性变更需升级至 `/api/v2`
- 小版本通过 `Accept-Version` Header 协商
- 废弃接口保留 2 个版本周期，返回 `Deprecation` Header

## 风险项

1. **DR-002 画布组件缺失**：SDLC 画布公共组件尚未产出详细设计，其接口将在编码阶段补充。
2. **SSE 端点未完整定义**：`subscribeExecutionSSE` 的事件格式需在编码阶段细化。
3. **Mock 数据占位**：部分复杂嵌套 DTO 使用 `TODO` 占位，需在 task-breakdown 前补充真实示例。
"""


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # OpenAPI YAML
    openapi = generate_openapi()
    with open(OUT_DIR / "openapi.yaml", "w", encoding="utf-8") as f:
        yaml.dump(openapi, f, sort_keys=False, allow_unicode=True, width=120)

    # Mock data JSON
    mock_data = generate_mock_data()
    with open(OUT_DIR / "mock-data.json", "w", encoding="utf-8") as f:
        json.dump(mock_data, f, ensure_ascii=False, indent=2)

    # Mock server config
    with open(OUT_DIR / "mock-server-config.md", "w", encoding="utf-8") as f:
        f.write(generate_mock_config())

    # Parallel dev plan
    with open(OUT_DIR / "parallel-dev-plan.md", "w", encoding="utf-8") as f:
        f.write(generate_parallel_plan())

    print(f"Generated artifacts in {OUT_DIR}:")
    for p in sorted(OUT_DIR.iterdir()):
        print(f"  {p.name:40s}  {p.stat().st_size:>8,} B")
