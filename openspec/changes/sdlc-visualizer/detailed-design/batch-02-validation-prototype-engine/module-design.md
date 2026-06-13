# 批次二详细设计文档：架构验证 + 原型服务 + 执行引擎

> **批次编号**: Batch-02
> **目标**: 能验证架构一致性，能生成可交互原型，能执行 Skill
> **周期**: 4 周
> **组件数**: 6 个
> **前置依赖**: Batch-01（C4 DSL 基线 + 架构图渲染 + 草图生成）
> **验收标准**: 见附录 A

---

## 目录

1. [设计概览](#一设计概览)
2. [CrossLayerValidator](#二crosslayervalidator)
3. [InterfaceContractStore](#三interfacecontractstore)
4. [OpenUIClient](#四openuiclient)
5. [PocketFlowEngine](#五pocketflowengine)
6. [ArtifactEditor](#六artifacteditor)
7. [C4ReverseLocator](#七c4reverselocator)
8. [API 接口总览](#八api-接口总览)
9. [测试策略](#九测试策略)
10. [附录 A：验收标准](#附录-a验收标准)

---

## 一、设计概览

### 1.1 批次架构图

```
================================================================================
                          前端 (React 19 + Vite 6)
================================================================================
  +------------------+  +------------------+  +------------------+
  | C4ValidatorPanel |  | OpenUIPreview    |  | SkillExecutor    |
  | (校验结果展示)    |  | (iframe 预览)    |  | (执行控制台)      |
  +--------+---------+  +--------+---------+  +--------+---------+
           |                     |                      |
================================================================================
                          后端 (FastAPI 0.115)
================================================================================
           |                     |                      |
  +--------v---------+  +--------v---------+  +--------v---------+
  |CrossLayerValidatr|  | OpenUIClient     |  | PocketFlowEngine |
  | (CV-01)          |  | (OU-01)          |  | (PE-01)          |
  |                  |  |                  |  |                  |
  | VAL-001~008      |  | 提示词组装        |  | prep→exec→post  |
  | 跨层一致性校验    |  | OpenUI服务调用   |  | 子进程生命周期    |
  |                  |  | 降级线框生成      |  | 超时管理         |
  +--------+---------+  +--------+---------+  +--------+---------+
           |                     |                      |
           +----------+----------+                      |
                      |                                 |
  +-------------------v--------+  +---------------------v--------+
  | C4BaselineStore            |  | CLIAdapter                   |
  | InterfaceContractStore     |  | KimiCLIAdapter               |
  | BindingRegistry            |  | (预留 MCPAdapter)            |
  +----------------------------+  +------------------------------+
           |                                 |
  +--------v---------+              +--------v---------+
  | C4ReverseLocator |              | ArtifactEditor   |
  | (CL-01)          |              | (AE-01)          |
  |                  |              |                  |
  | 节点→代码文件    |              | 平台内编辑       |
  | 代码→DSL节点    |              | 冲突检测         |
  +------------------+              +------------------+
```

### 1.2 核心数据流

```
流 1: 架构验证
  C4BaselineStore ──→ CrossLayerValidator ──→ 校验报告
  BindingRegistry ──→ (引用一致性校验)

流 2: 原型生成
  C4BaselineStore ──→ OpenUIClient ──→ OpenUI Docker ──→ HTML 原型
  InterfaceContractStore ──→ (接口契约输入)
  降级: OpenUI 不可用时 ──→ Wireframe 静态降级

流 3: Skill 执行
  Skill 定义 ──→ PocketFlowEngine ──→ Kimi CLI ──→ 产物
                         │                    │
                         └─────── 超时管理 ────┘
                         └─────── 日志捕获 ────┘

流 4: 反向定位
  C4 DSL 节点 ──→ C4ReverseLocator ──→ 本地代码文件
  本地代码文件 ──→ C4ReverseLocator ──→ C4 DSL 节点

流 5: 产物编辑
  ArtifactStore ──→ ArtifactEditor ──→ 冲突检测 ──→ 保存/覆盖
```

### 1.3 批次时间线

```
Week 1: 架构验证 + 接口契约
  ├─ Day 1-2:  CrossLayerValidator (VAL-001~008 规则)
  ├─ Day 3-4:  InterfaceContractStore (接口 CRUD + 状态机)
  └─ Day 5-7:  集成测试 + 校验面板前端

Week 2: OpenUI 原型服务
  ├─ Day 8-10: OpenUIClient (提示词组装 + HTTP 调用)
  ├─ Day 11-12: 降级策略 (Wireframe fallback)
  └─ Day 13-14: OpenUIPreview 前端 (iframe + 视口切换)

Week 3: Skill 执行引擎
  ├─ Day 15-17: PocketFlowEngine (三阶段模型)
  ├─ Day 18-19: CLIAdapter 抽象层
  └─ Day 20-21: 超时管理 + 日志捕获

Week 4: 产物编辑 + 反向定位
  ├─ Day 22-24: ArtifactEditor (编辑 + 冲突检测)
  ├─ Day 25-26: C4ReverseLocator (双向映射)
  └─ Day 27-28: 集成测试 + 端到端验证
```



---

## 二、CrossLayerValidator (CV-01)

**文件**: `backend/app/c4/cross_layer_validator.py`
**依赖**: C4BaselineStore, BindingRegistry
**被依赖**: C4ValidatorPanel（前端校验结果展示）

### 2.1 设计目标

- 执行 VAL-001~VAL-008 八条跨层一致性校验规则
- 校验 C4 各层级之间的引用一致性
- 校验 C4 与 SDLC 产物之间的数据一致性
- 生成结构化校验报告（错误/警告/通过）

### 2.2 VAL-001~VAL-008 规则定义

| 规则 | 名称 | 校验内容 | 严重度 |
|------|------|----------|--------|
| VAL-001 | 外部系统引用一致性 | PRD 定义的外部系统必须在 ARCH 中有对应容器 | ERROR |
| VAL-002 | 实体定义一致性 | API 的 DTO 字段必须能在 DOMAIN_MODEL 实体属性中找到映射 | WARNING |
| VAL-003 | 容器归属一致性 | 下游文档引用的 container_id 必须在 ARCH 中存在 | ERROR |
| VAL-004 | 组件归属一致性 | 组件归属的容器必须在 ARCH 中定义 | ERROR |
| VAL-005 | 接口归属一致性 | 组件声明的接口必须在 API_DESIGN 中有详细契约 | WARNING |
| VAL-006 | 实体-表映射一致性 | DB 表映射的实体必须在 DOMAIN_MODEL 中存在 | ERROR |
| VAL-007 | 属性-字段映射一致性 | DB 字段映射的属性必须在对应实体中存在 | WARNING |
| VAL-008 | 页面类型推断一致性 | PageType 与 DomainMapper 推断结果冲突时以人工标注为准 | INFO |

### 2.3 核心实现

```python
# backend/app/c4/cross_layer_validator.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
from enum import Enum
import yaml

from app.c4.baseline_store import C4BaselineStore
from app.c4.binding_registry import BindingRegistry

class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class RuleId(str, Enum):
    VAL_001 = "VAL-001"  # 外部系统引用一致性
    VAL_002 = "VAL-002"  # 实体定义一致性
    VAL_003 = "VAL-003"  # 容器归属一致性
    VAL_004 = "VAL-004"  # 组件归属一致性
    VAL_005 = "VAL-005"  # 接口归属一致性
    VAL_006 = "VAL-006"  # 实体-表映射一致性
    VAL_007 = "VAL-007"  # 属性-字段映射一致性
    VAL_008 = "VAL-008"  # 页面类型推断一致性

@dataclass
class ValidationIssue:
    rule_id: str
    severity: Severity
    message: str
    c4_node_id: Optional[str] = None
    c4_level: Optional[str] = None
    suggestion: str = ""

@dataclass
class ValidationReport:
    project_id: str
    passed: bool
    error_count: int
    warning_count: int
    info_count: int
    issues: List[ValidationIssue] = field(default_factory=list)
    summary: str = ""

class CrossLayerValidator:
    """
    跨层校验器 — C4 架构一致性验证

    职责:
    1. 加载 C4Workspace 和 BindingRegistry
    2. 按顺序执行 VAL-001~VAL-008
    3. 收集并分类问题
    4. 生成结构化报告
    """

    def __init__(
        self,
        baseline_store: C4BaselineStore,
        binding_registry: BindingRegistry,
    ):
        self.baseline = baseline_store
        self.bindings = binding_registry

    async def validate(self, project_id: str) -> ValidationReport:
        """
        执行全量校验

        Args:
            project_id: 项目 ID

        Returns:
            ValidationReport: 校验报告
        """
        issues: List[ValidationIssue] = []

        # 1. 加载当前 C4 DSL
        baseline = await self.baseline.read_current(project_id)
        if not baseline:
            return ValidationReport(
                project_id=project_id, passed=False,
                error_count=1, warning_count=0, info_count=0,
                issues=[ValidationIssue(
                    rule_id=RuleId.VAL_001, severity=Severity.ERROR,
                    message="No C4 baseline found for this project",
                    suggestion="Run document extraction pipeline first",
                )],
            )

        # 解析 DSL
        workspace = self._parse_dsl(baseline.dsl_content)

        # 2. 执行各条规则
        issues.extend(self._check_val001_external_systems(workspace))
        issues.extend(self._check_val003_container_refs(workspace))
        issues.extend(self._check_val004_component_containers(workspace))
        issues.extend(self._check_val006_entity_table_mapping(workspace))

        # 3. 统计
        errors = len([i for i in issues if i.severity == Severity.ERROR])
        warnings = len([i for i in issues if i.severity == Severity.WARNING])
        infos = len([i for i in issues if i.severity == Severity.INFO])

        # 4. 生成报告
        passed = errors == 0
        summary = self._generate_summary(project_id, errors, warnings, infos)

        return ValidationReport(
            project_id=project_id, passed=passed,
            error_count=errors, warning_count=warnings, info_count=infos,
            issues=issues, summary=summary,
        )

    async def validate_incremental(
        self, project_id: str, changed_nodes: List[str]
    ) -> ValidationReport:
        """
        增量校验 — 仅校验变更涉及的节点

        Args:
            project_id: 项目 ID
            changed_nodes: 变更的 C4 节点 ID 列表
        """
        # 加载完整 DSL 但只检查 changed_nodes 相关的问题
        baseline = await self.baseline.read_current(project_id)
        if not baseline:
            return ValidationReport(project_id=project_id, passed=False, error_count=0, warning_count=0, info_count=0)

        workspace = self._parse_dsl(baseline.dsl_content)
        issues: List[ValidationIssue] = []

        # 只检查与 changed_nodes 相关的问题
        container_ids = {c["id"] for c in workspace.containers}
        for node_id in changed_nodes:
            if node_id in container_ids:
                issues.extend(self._check_container_ref(workspace, node_id))

        errors = len([i for i in issues if i.severity == Severity.ERROR])
        return ValidationReport(
            project_id=project_id, passed=errors == 0,
            error_count=errors, warning_count=0, info_count=0,
            issues=issues,
        )

    # ============================================================
    # VAL-001: 外部系统引用一致性
    # ============================================================
    def _check_val001_external_systems(
        self, workspace: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """PRD 定义的外部系统必须在 ARCH 中有对应容器"""
        issues = []
        model = workspace.get("model", {})
        external_systems = model.get("externalSystems", [])
        containers = {c["id"] for c in model.get("containers", [])}

        for ext in external_systems:
            ext_id = ext["id"]
            # 外部系统应该在某个容器中被引用
            found = any(
                ext_id in str(rel.get("target", "")) or ext_id in str(rel.get("description", ""))
                for rel in model.get("relationships", [])
            )
            if not found:
                issues.append(ValidationIssue(
                    rule_id=RuleId.VAL_001,
                    severity=Severity.WARNING,
                    message=f"External system '{ext_id}' is not referenced by any container",
                    c4_node_id=ext_id,
                    c4_level="L1",
                    suggestion=f"Add a relationship from a container to {ext_id}",
                ))

        return issues

    # ============================================================
    # VAL-003: 容器归属一致性
    # ============================================================
    def _check_val003_container_refs(
        self, workspace: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """下游文档引用的 container_id 必须在 ARCH 中存在"""
        issues = []
        model = workspace.get("model", {})
        containers = {c["id"] for c in model.get("containers", [])}

        # 检查组件引用的 container_id
        for component in model.get("components", []):
            container_id = component.get("properties", {}).get("container_id")
            if container_id and container_id not in containers:
                issues.append(ValidationIssue(
                    rule_id=RuleId.VAL_003,
                    severity=Severity.ERROR,
                    message=f"Component '{component['id']}' references unknown container '{container_id}'",
                    c4_node_id=component["id"],
                    c4_level="L3",
                    suggestion=f"Define container '{container_id}' in ARCH document or fix the reference",
                ))

        return issues

    # ============================================================
    # VAL-004: 组件归属一致性
    # ============================================================
    def _check_val004_component_containers(
        self, workspace: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """组件归属的容器必须在 ARCH 中定义"""
        issues = []
        model = workspace.get("model", {})
        containers = {c["id"] for c in model.get("containers", [])}

        for component in model.get("components", []):
            comp_id = component["id"]
            container_id = component.get("properties", {}).get("container_id")

            if not container_id:
                issues.append(ValidationIssue(
                    rule_id=RuleId.VAL_004,
                    severity=Severity.WARNING,
                    message=f"Component '{comp_id}' has no container_id specified",
                    c4_node_id=comp_id,
                    c4_level="L3",
                    suggestion="Add container_id to the component definition",
                ))
            elif container_id not in containers:
                issues.append(ValidationIssue(
                    rule_id=RuleId.VAL_004,
                    severity=Severity.ERROR,
                    message=f"Component '{comp_id}' belongs to undefined container '{container_id}'",
                    c4_node_id=comp_id,
                    c4_level="L3",
                    suggestion=f"Define container '{container_id}' or fix the container_id",
                ))

        return issues

    # ============================================================
    # VAL-006: 实体-表映射一致性
    # ============================================================
    def _check_val006_entity_table_mapping(
        self, workspace: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """DB 表映射的实体必须在 DOMAIN_MODEL 中存在"""
        issues = []
        model = workspace.get("model", {})
        entities = {e["id"] for e in model.get("entities", [])}

        # 从 tables 中提取 entity 引用（通过 properties.entity_map）
        # 这里简化处理：检查 table 名称是否与 entity 匹配
        for table in model.get("entities", []):  # tables 通常也在 entities 中
            if "table" in str(table.get("properties", {})).lower():
                mapped_entity = table.get("properties", {}).get("mapped_entity")
                if mapped_entity and mapped_entity not in entities:
                    issues.append(ValidationIssue(
                        rule_id=RuleId.VAL_006,
                        severity=Severity.ERROR,
                        message=f"Table '{table['id']}' maps to undefined entity '{mapped_entity}'",
                        c4_node_id=table["id"],
                        c4_level="L2",
                        suggestion=f"Define entity '{mapped_entity}' in DOMAIN_MODEL",
                    ))

        return issues

    # ============================================================
    # 增量校验辅助
    # ============================================================
    def _check_container_ref(
        self, workspace: Dict, container_id: str
    ) -> List[ValidationIssue]:
        """检查单个容器的引用完整性（增量用）"""
        issues = []
        model = workspace.get("model", {})

        # 检查是否有组件引用此容器
        components = [
            c for c in model.get("components", [])
            if c.get("properties", {}).get("container_id") == container_id
        ]

        if not components:
            issues.append(ValidationIssue(
                rule_id=RuleId.VAL_004,
                severity=Severity.INFO,
                message=f"Container '{container_id}' has no components defined",
                c4_node_id=container_id,
                c4_level="L2",
                suggestion="Add components to this container in DETAIL_DESIGN",
            ))

        return issues

    # ============================================================
    # 工具方法
    # ============================================================
    @staticmethod
    def _parse_dsl(dsl_content: str) -> Dict[str, Any]:
        """解析 DSL YAML"""
        return yaml.safe_load(dsl_content)

    @staticmethod
    def _generate_summary(
        project_id: str, errors: int, warnings: int, infos: int
    ) -> str:
        status = "PASSED" if errors == 0 else "FAILED"
        return f"[{status}] Project {project_id}: {errors} errors, {warnings} warnings, {infos} infos"
```



---

## 三、InterfaceContractStore (IC-01)

**文件**: `backend/app/c4/interface_contract_store.py`
**依赖**: DatabaseAdapter
**被依赖**: OpenUIClient, PrototypeArchBinder (P2)

### 3.1 设计目标

- 独立存储接口契约（不嵌入 C4 DSL）
- 支持冻结/草稿/gap/废弃四种状态
- 按 Container 查询接口
- 供 OpenUI 原型服务消费（接口 → 提示词）

### 3.2 核心实现

```python
# backend/app/c4/interface_contract_store.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# ============================================================
# 数据模型
# ============================================================
class ContractStatus(str, Enum):
    DRAFT = "draft"         # 草稿态
    FROZEN = "frozen"       # 评审通过锁定
    GAP = "gap"             # 双向绑定检测到原型有但契约无
    DEPRECATED = "deprecated"  # 废弃保留历史

@dataclass
class InterfaceContract:
    contract_id: str
    project_id: str
    container_id: str       # 归属的 C4 Container
    endpoint_path: str      # 如 /api/users
    method: str             # GET/POST/PUT/DELETE
    summary: str = ""       # 接口描述
    request_schema: Optional[Dict] = None   # 请求体 Schema
    response_schema: Optional[Dict] = None  # 响应体 Schema
    status: str = "draft"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class InterfaceContractStore:
    """
    接口契约表 — 独立存储接口定义

    职责:
    1. 接口契约 CRUD
    2. 状态管理（draft/frozen/gap/deprecated）
    3. 按 Container 查询
    4. 供 OpenUI 生成提示词使用
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # CRUD
    # ============================================================
    async def create(self, contract: InterfaceContract) -> str:
        """创建接口契约"""
        from app.db.models import InterfaceContract as ContractModel
        record = ContractModel(
            project_id=contract.project_id,
            container_id=contract.container_id,
            endpoint_path=contract.endpoint_path,
            method=contract.method,
            summary=contract.summary,
            request_schema=contract.request_schema,
            response_schema=contract.response_schema,
            status=ContractStatus.DRAFT,
        )
        self.db.add(record)
        await self.db.flush()
        return str(record.id)

    async def get(self, contract_id: str) -> Optional[InterfaceContract]:
        """获取单个契约"""
        from app.db.models import InterfaceContract as ContractModel
        result = await self.db.execute(
            select(ContractModel).where(ContractModel.id == contract_id)
        )
        record = result.scalar_one_or_none()
        return self._to_dto(record) if record else None

    async def list_by_container(self, project_id: str, container_id: str) -> List[InterfaceContract]:
        """查询 Container 下的所有接口"""
        from app.db.models import InterfaceContract as ContractModel
        result = await self.db.execute(
            select(ContractModel)
            .where(ContractModel.project_id == project_id)
            .where(ContractModel.container_id == container_id)
            .where(ContractModel.status != ContractStatus.DEPRECATED)
        )
        return [self._to_dto(r) for r in result.scalars().all()]

    async def list_by_project(self, project_id: str) -> List[InterfaceContract]:
        """查询项目下所有有效接口"""
        from app.db.models import InterfaceContract as ContractModel
        result = await self.db.execute(
            select(ContractModel)
            .where(ContractModel.project_id == project_id)
            .where(ContractModel.status.in_([ContractStatus.DRAFT, ContractStatus.FROZEN]))
        )
        return [self._to_dto(r) for r in result.scalars().all()]

    async def update_schema(
        self, contract_id: str, request_schema: Optional[Dict] = None,
        response_schema: Optional[Dict] = None
    ):
        """更新接口 Schema"""
        from app.db.models import InterfaceContract as ContractModel
        updates = {}
        if request_schema is not None:
            updates["request_schema"] = request_schema
        if response_schema is not None:
            updates["response_schema"] = response_schema
        if updates:
            await self.db.execute(
                update(ContractModel)
                .where(ContractModel.id == contract_id)
                .values(**updates)
            )

    # ============================================================
    # 状态管理
    # ============================================================
    async def freeze(self, contract_id: str):
        """冻结契约: draft → frozen"""
        from app.db.models import InterfaceContract as ContractModel
        await self.db.execute(
            update(ContractModel)
            .where(ContractModel.id == contract_id)
            .values(status=ContractStatus.FROZEN)
        )

    async def mark_gap(self, contract_id: str):
        """标记为 gap: draft → gap（原型有但契约无）"""
        from app.db.models import InterfaceContract as ContractModel
        await self.db.execute(
            update(ContractModel)
            .where(ContractModel.id == contract_id)
            .values(status=ContractStatus.GAP)
        )

    async def deprecate(self, contract_id: str):
        """废弃契约"""
        from app.db.models import InterfaceContract as ContractModel
        await self.db.execute(
            update(ContractModel)
            .where(ContractModel.id == contract_id)
            .values(status=ContractStatus.DEPRECATED)
        )

    # ============================================================
    # 供 OpenUI 使用的批量导出
    # ============================================================
    async def export_for_openui(self, project_id: str) -> str:
        """导出为 OpenUI 提示词可用的接口列表文本"""
        contracts = await self.list_by_project(project_id)
        lines = ["Available Endpoints:"]
        for c in contracts:
            req_fields = ""
            if c.request_schema:
                fields = c.request_schema.get("properties", {})
                req_fields = ", ".join(fields.keys())
                req_fields = f" (fields: {req_fields})"

            resp_fields = ""
            if c.response_schema:
                fields = c.response_schema.get("properties", {})
                resp_fields = ", ".join(fields.keys())
                resp_fields = f" → {resp_fields}"

            lines.append(f"- {c.method} {c.endpoint_path}{req_fields}{resp_fields}")

        return "\n".join(lines)

    @staticmethod
    def _to_dto(record) -> InterfaceContract:
        return InterfaceContract(
            contract_id=str(record.id),
            project_id=record.project_id,
            container_id=record.container_id,
            endpoint_path=record.endpoint_path,
            method=record.method,
            summary=record.summary or "",
            request_schema=record.request_schema,
            response_schema=record.response_schema,
            status=record.status.value if hasattr(record.status, "value") else str(record.status),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
```

---

## 四、OpenUIClient (OU-01)

**文件**: `backend/app/c4/open_ui_client.py`
**依赖**: C4BaselineStore, InterfaceContractStore
**被依赖**: OpenUIPreview（前端）

### 4.1 设计目标

- 基于 C4 Container + 接口契约组装提示词
- 调用本地 OpenUI Docker 服务生成 HTML 原型
- 多页面拆分与存储
- OpenUI 不可用时 Wireframe 静态降级
- 服务健康检测

### 4.2 核心实现

```python
# backend/app/c4/open_ui_client.py
import asyncio
import aiohttp
import hashlib
from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime

from app.c4.baseline_store import C4BaselineStore
from app.c4.interface_contract_store import InterfaceContractStore

@dataclass
class OpenUIGenerationResult:
    spec_id: str
    status: str              # GENERATED / FALLBACK / ERROR
    html_content: Optional[str]
    page_count: int
    page_titles: List[str]
    prompt_text: str         # 提交给 OpenUI 的提示词
    duration_ms: int
    error_message: Optional[str] = None

class OpenUIClient:
    """
    OpenUI 原型服务客户端

    职责:
    1. 从 C4 DSL 提取 Container 信息
    2. 从 InterfaceContractStore 获取接口列表
    3. 组装结构化提示词
    4. 调用 OpenUI Docker HTTP API
    5. 多页面 HTML 拆分
    6. 降级: OpenUI 不可用时生成 Wireframe
    """

    # OpenUI 服务配置
    DEFAULT_BASE_URL = "http://localhost:3000"
    GENERATE_TIMEOUT = 15  # 秒
    HEALTH_TIMEOUT = 5

    def __init__(
        self,
        baseline_store: C4BaselineStore,
        contract_store: InterfaceContractStore,
        base_url: str = DEFAULT_BASE_URL,
    ):
        self.baseline = baseline_store
        self.contracts = contract_store
        self.base_url = base_url.rstrip("/")

    # ============================================================
    # 健康检测
    # ============================================================
    async def check_health(self) -> Dict[str, any]:
        """检测 OpenUI 服务可用性"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health",
                    timeout=aiohttp.ClientTimeout(total=self.HEALTH_TIMEOUT),
                ) as resp:
                    return {
                        "available": resp.status == 200,
                        "status_code": resp.status,
                        "latency_ms": 0,  # 可添加计时
                    }
        except Exception as e:
            return {
                "available": False,
                "status_code": 0,
                "error": str(e),
            }

    # ============================================================
    # 主生成流程
    # ============================================================
    async def generate_from_c4(
        self, project_id: str, spec_name: str = "prototype"
    ) -> OpenUIGenerationResult:
        """
        从 C4 + 接口契约生成原型

        流程:
        1. 获取 C4 DSL (L2 Container)
        2. 获取接口契约
        3. 组装提示词
        4. 检测 OpenUI 健康
        5. 调用 OpenUI 或降级
        6. 拆分页面
        """
        start_time = datetime.utcnow()

        # 1. 获取 C4 DSL
        workspace = await self.baseline.read_current(project_id)
        if not workspace:
            return self._error_result("No C4 DSL found")

        import yaml
        dsl_data = yaml.safe_load(workspace.dsl_content)
        containers = dsl_data.get("workspace", {}).get("model", {}).get("containers", [])

        if not containers:
            return self._error_result("No containers found in C4 DSL")

        # 2. 获取接口契约
        all_contracts = await self.contracts.list_by_project(project_id)
        contracts_by_container: Dict[str, List] = {}
        for c in all_contracts:
            contracts_by_container.setdefault(c.container_id, []).append(c)

        # 3. 组装提示词
        prompt = self._assemble_prompt(containers, contracts_by_container)

        # 4. 检测健康
        health = await self.check_health()

        # 5. 生成
        if health["available"]:
            html_result = await self._call_openui(prompt)
            status = "GENERATED"
        else:
            html_result = self._build_fallback_wireframe(containers, all_contracts)
            status = "FALLBACK"

        # 6. 拆分页面
        pages = self._split_pages(html_result)
        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return OpenUIGenerationResult(
            spec_id=f"openui-{hashlib.md5(prompt.encode()).hexdigest()[:8]}",
            status=status,
            html_content=html_result,
            page_count=len(pages),
            page_titles=[p.get("title", f"Page {i+1}") for i, p in enumerate(pages)],
            prompt_text=prompt,
            duration_ms=duration,
        )

    # ============================================================
    # 提示词组装
    # ============================================================
    def _assemble_prompt(
        self, containers: List[Dict], contracts_by_container: Dict[str, List]
    ) -> str:
        """组装 OpenUI 提示词"""
        lines = [
            "You are a UI generation assistant.",
            "Generate a complete, interactive single-page HTML prototype.",
            "",
            "System Overview:",
        ]

        for container in containers:
            cid = container["id"]
            cname = container.get("name", cid)
            tech = container.get("technology", "")
            desc = container.get("description", "")
            lines.append(f"- {cname} ({tech}): {desc}")

            # 添加该容器的接口
            container_contracts = contracts_by_container.get(cid, [])
            if container_contracts:
                lines.append(f"  Endpoints:")
                for c in container_contracts:
                    lines.append(f"  - {c.method} {c.endpoint_path}: {c.summary}")

        lines.extend([
            "",
            "Requirements:",
            "- Use semantic HTML5, embedded CSS, and vanilla JS.",
            "- Include navigation, data tables or forms based on endpoints.",
            "- Support responsive layout.",
            "- Output a complete standalone HTML file.",
            "- Use Chinese UI labels where appropriate.",
            "- Split multiple pages with <!-- PAGE: PageName --> comments.",
        ])

        return "\n".join(lines)

    # ============================================================
    # OpenUI HTTP 调用
    # ============================================================
    async def _call_openui(self, prompt: str) -> str:
        """调用 OpenUI Docker 服务"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={"prompt": prompt, "format": "html"},
                timeout=aiohttp.ClientTimeout(total=self.GENERATE_TIMEOUT),
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"OpenUI returned {resp.status}")
                result = await resp.json()
                return result.get("html", "")

    # ============================================================
    # 降级: Wireframe 静态 HTML
    # ============================================================
    def _build_fallback_wireframe(
        self, containers: List[Dict], contracts: List
    ) -> str:
        """OpenUI 不可用时生成降级线框"""
        lines = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='utf-8'>",
            "<style>",
            "body{font-family:sans-serif;background:#f5f5f5;padding:20px}",
            ".banner{background:#fff3cd;border:1px solid #ffc107;padding:12px;margin-bottom:20px;color:#856404}",
            ".container-box{background:white;border:2px solid #999;padding:16px;margin-bottom:16px}",
            ".container-title{font-size:16px;font-weight:bold;color:#333;margin-bottom:8px}",
            ".endpoint{padding:8px;background:#f0f0f0;margin:4px 0;font-size:13px;color:#666;border-left:3px solid #4a90d9}",
            ".wireframe-placeholder{height:100px;background:repeating-linear-gradient(45deg,#f0f0f0,#f0f0f0 10px,#e0e0e0 10px,#e0e0e0 20px);margin:8px 0;display:flex;align-items:center;justify-content:center;color:#999}",
            "</style></head><body>",
            '<div class="banner">⚠️ OpenUI service unavailable. Showing wireframe fallback.</div>',
        ]

        for container in containers:
            cid = container["id"]
            cname = container.get("name", cid)
            tech = container.get("technology", "")
            lines.append(f'<div class="container-box">')
            lines.append(f'<div class="container-title">{cname} [{tech}]</div>')

            # 接口列表
            container_contracts = [c for c in contracts if c.container_id == cid]
            if container_contracts:
                lines.append('<div style="font-size:12px;color:#666;margin-bottom:8px">Endpoints:</div>')
                for c in container_contracts:
                    method_color = {"GET": "#4a90d9", "POST": "#5cb85c", "PUT": "#f0ad4e", "DELETE": "#d9534f"}
                    color = method_color.get(c.method, "#666")
                    lines.append(f'<div class="endpoint"><span style="color:{color};font-weight:bold">{c.method}</span> {c.endpoint_path}</div>')
            else:
                lines.append('<div class="wireframe-placeholder">[Page Layout Placeholder]</div>')

            lines.append('</div>')

        lines.append("</body></html>")
        return "\n".join(lines)

    # ============================================================
    # 页面拆分
    # ============================================================
    def _split_pages(self, html_content: str) -> List[Dict]:
        """按 <!-- PAGE: PageName --> 拆分多页面"""
        import re
        pattern = r"<!--\s*PAGE:\s*(.*?)\s*-->"
        splits = re.split(pattern, html_content)

        if len(splits) <= 1:
            # 单页面
            return [{"title": "Main Page", "content": html_content}]

        pages = []
        # splits[0] 是 PAGE 之前的内容（忽略）
        for i in range(1, len(splits), 2):
            title = splits[i].strip()
            content = splits[i + 1] if i + 1 < len(splits) else ""
            pages.append({"title": title, "content": content})

        return pages

    def _error_result(self, message: str) -> OpenUIGenerationResult:
        return OpenUIGenerationResult(
            spec_id="", status="ERROR", html_content=None,
            page_count=0, page_titles=[], prompt_text="",
            duration_ms=0, error_message=message,
        )
```



---

## 五、PocketFlowEngine (PE-01)

**文件**: `backend/app/engine/pocketflow_engine.py`
**依赖**: CLIAdapter, ProjectContext
**被依赖**: DAGScheduler (Batch-03)

### 5.1 设计目标

- 实现 PocketFlow 三阶段执行模型：prep → exec → post
- 封装 Kimi CLI 子进程调用
- 超时管理（90s SIGTERM + 30s SIGKILL）
- 输入产物注入、输出捕获、日志收集
- 支持未来扩展 MCPAdapter

### 5.2 核心实现

```python
# backend/app/engine/pocketflow_engine.py
import asyncio
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from app.common.project_context import ProjectContext

class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    KILLED = "killed"

@dataclass
class ExecutionResult:
    skill_id: str
    status: ExecutionStatus
    exit_code: int
    stdout: str
    stderr: str
    output_artifacts: List[str]
    log_path: str
    duration_ms: int

@dataclass
class SkillConfig:
    """Skill 配置"""
    skill_id: str
    name: str
    file_path: str
    inputs: List[str]          # 输入产物路径
    outputs: List[str]         # 输出产物路径
    env: Dict[str, str] = None  # 环境变量
    timeout: float = 90.0      # 执行超时（秒）
    kill_timeout: float = 30.0 # SIGKILL 等待时间

class CLIAdapter:
    """
    CLI 适配器抽象基类

    职责: 统一不同 CLI 工具的调用接口
    当前实现: KimiCLIAdapter
    未来扩展: MCPAdapter
    """

    async def execute(
        self, skill_path: str, inputs: Dict[str, str],
        env: Optional[Dict[str, str]] = None,
        timeout: float = 90.0, kill_timeout: float = 30.0,
    ) -> ExecutionResult:
        raise NotImplementedError

    def build_command(self, skill_path: str, inputs: Dict[str, str]) -> List[str]:
        raise NotImplementedError

class KimiCLIAdapter(CLIAdapter):
    """
    Kimi CLI 适配器

    调用方式: kimi run <skill_file> --input <key>=<path>...
    """

    def build_command(self, skill_path: str, inputs: Dict[str, str]) -> List[str]:
        cmd = ["kimi", "run", skill_path]
        for key, value in inputs.items():
            cmd.extend(["--input", f"{key}={value}"])
        return cmd

    async def execute(
        self, skill_path: str, inputs: Dict[str, str],
        env: Optional[Dict[str, str]] = None,
        timeout: float = 90.0, kill_timeout: float = 30.0,
    ) -> ExecutionResult:
        cmd = self.build_command(skill_path, inputs)
        skill_id = Path(skill_path).stem

        # 启动子进程
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**env, "PYTHONUNBUFFERED": "1"} if env else {"PYTHONUNBUFFERED": "1"},
        )

        start_time = time.time()
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            duration_ms = int((time.time() - start_time) * 1000)

            return ExecutionResult(
                skill_id=skill_id,
                status=ExecutionStatus.SUCCESS if process.returncode == 0 else ExecutionStatus.ERROR,
                exit_code=process.returncode,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                output_artifacts=[],  # 从 stdout 解析或从约定目录读取
                log_path="",
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            # 超时处理: 先 SIGTERM，再 SIGKILL
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=kill_timeout)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

            return ExecutionResult(
                skill_id=skill_id,
                status=ExecutionStatus.TIMEOUT,
                exit_code=-1,
                stdout="",
                stderr=f"Execution timed out after {timeout}s",
                output_artifacts=[],
                log_path="",
                duration_ms=int(timeout * 1000),
            )

class PocketFlowEngine:
    """
    PocketFlow 执行引擎

    三阶段执行模型:
    1. PREP: 准备输入产物，验证前置条件，计算哈希
    2. EXEC: 调用 CLI 执行 Skill，超时管理，日志收集
    3. POST: 捕获输出，验证产物完整性，触发 Gate
    """

    def __init__(
        self,
        cli_adapter: CLIAdapter,
        project_ctx: ProjectContext,
        logs_dir: str = "./logs",
    ):
        self.cli = cli_adapter
        self.ctx = project_ctx
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, skill: SkillConfig) -> ExecutionResult:
        """
        完整三阶段执行

        Args:
            skill: Skill 配置

        Returns:
            ExecutionResult: 执行结果
        """
        # === PREP 阶段 ===
        prep_result = await self._prep_phase(skill)

        # === EXEC 阶段 ===
        exec_result = await self._exec_phase(skill, prep_result)

        # === POST 阶段 ===
        if exec_result.status == ExecutionStatus.SUCCESS:
            return await self._post_phase(skill, exec_result)

        return exec_result

    # ============================================================
    # PREP 阶段
    # ============================================================
    async def _prep_phase(self, skill: SkillConfig) -> Dict[str, Any]:
        """
        PREP: 准备输入产物

        1. 验证输入产物存在
        2. 计算输入哈希（用于变更检测）
        3. 准备环境变量
        """
        artifacts_dir = self.ctx.artifacts_dir
        input_hashes = {}
        input_paths = {}

        for input_path in skill.inputs:
            full_path = artifacts_dir / input_path
            if not full_path.exists():
                raise FileNotFoundError(
                    f"Input artifact not found: {input_path} "
                    f"(project={self.ctx.project_id})"
                )
            content = full_path.read_text("utf-8")
            input_hashes[input_path] = hashlib.sha256(content.encode()).hexdigest()
            input_paths[input_path] = str(full_path.resolve())

        return {
            "input_hashes": input_hashes,
            "input_paths": input_paths,
            "work_dir": str(self.ctx.artifacts_dir),
        }

    # ============================================================
    # EXEC 阶段
    # ============================================================
    async def _exec_phase(
        self, skill: SkillConfig, prep_result: Dict[str, Any]
    ) -> ExecutionResult:
        """
        EXEC: 调用 CLI 执行

        1. 组装命令
        2. 启动子进程
        3. 超时管理（SIGTERM → SIGKILL）
        4. 收集 stdout/stderr
        5. 写入日志文件
        """
        result = await self.cli.execute(
            skill_path=skill.file_path,
            inputs=prep_result["input_paths"],
            env=skill.env,
            timeout=skill.timeout,
            kill_timeout=skill.kill_timeout,
        )

        # 写入日志
        log_path = self._write_log(skill.skill_id, result)
        result.log_path = log_path

        return result

    # ============================================================
    # POST 阶段
    # ============================================================
    async def _post_phase(
        self, skill: SkillConfig, exec_result: ExecutionResult
    ) -> ExecutionResult:
        """
        POST: 捕获输出，验证产物

        1. 扫描输出产物
        2. 验证产物完整性
        3. 计算输出哈希
        """
        artifacts_dir = self.ctx.artifacts_dir
        output_artifacts = []

        for output_pattern in skill.outputs:
            full_path = artifacts_dir / output_pattern
            if full_path.exists():
                output_artifacts.append(output_pattern)

        exec_result.output_artifacts = output_artifacts
        return exec_result

    # ============================================================
    # 日志管理
    # ============================================================
    def _write_log(self, skill_id: str, result: ExecutionResult) -> str:
        """写入执行日志"""
        timestamp = int(time.time())
        log_file = self.logs_dir / f"{skill_id}_{timestamp}.log"

        log_content = f"""=== Skill Execution Log ===
Skill: {skill_id}
Status: {result.status.value}
Exit Code: {result.exit_code}
Duration: {result.duration_ms}ms
Timestamp: {timestamp}

=== STDOUT ===
{result.stdout}

=== STDERR ===
{result.stderr}
"""
        log_file.write_text(log_content, "utf-8")
        return str(log_file)

    async def get_logs(self, skill_id: str, limit: int = 100) -> List[str]:
        """获取最近的日志文件列表"""
        log_files = sorted(
            self.logs_dir.glob(f"{skill_id}_*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return [f.name for f in log_files[:limit]]
```

---

## 六、ArtifactEditor (AE-01)

**文件**: 
- 后端: `backend/app/artifacts/artifact_editor.py`
- 前端: `frontend/src/components/ArtifactEditor.tsx`

**依赖**: ArtifactStore
**被依赖**: StageDetailPanel

### 6.1 设计目标

- 平台内产物编辑（不离开平台）
- 保存时外部哈希校验（冲突检测）
- 编辑后自动标记状态变化
- 支持 Markdown, YAML, JSON 格式

### 6.2 后端实现

```python
# backend/app/artifacts/artifact_editor.py
import hashlib
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime

from app.common.artifact_store import ArtifactStore

@dataclass
class EditResult:
    success: bool
    new_hash: str
    conflict_detected: bool
    message: str
    previous_hash: Optional[str] = None

class ArtifactEditor:
    """
    产物编辑器

    职责:
    1. 读取产物内容
    2. 编辑后保存
    3. 保存时冲突检测（外部修改检测）
    4. 编辑后标记产物状态
    """

    def __init__(self, store: ArtifactStore):
        self.store = store

    async def read(self, relative_path: str) -> str:
        """读取产物内容"""
        return await self.store.read(relative_path)

    async def save(
        self, relative_path: str, new_content: str,
        expected_hash: Optional[str] = None,
    ) -> EditResult:
        """
        保存编辑后的产物

        Args:
            relative_path: 产物相对路径
            new_content: 新内容
            expected_hash: 编辑前客户端知道的哈希（用于冲突检测）

        Returns:
            EditResult: 保存结果
        """
        # 1. 检查外部变更（如果提供了 expected_hash）
        if expected_hash is not None:
            changed, current_hash = self.store.check_external_change(relative_path)
            if changed and current_hash != expected_hash:
                return EditResult(
                    success=False,
                    new_hash="",
                    conflict_detected=True,
                    message=f"Conflict detected: file was modified externally. "
                            f"Expected hash: {expected_hash[:16]}..., "
                            f"Current hash: {current_hash[:16]}...",
                    previous_hash=expected_hash,
                )

        # 2. 写入新内容
        file_path, new_hash = await self.store.write(
            relative_path, new_content,
            commit_message=f"Edit {relative_path}",
        )

        return EditResult(
            success=True,
            new_hash=new_hash,
            conflict_detected=False,
            message=f"Saved successfully. New hash: {new_hash[:16]}...",
        )

    def compute_hash(self, content: str) -> str:
        """计算内容哈希（客户端预览用）"""
        return hashlib.sha256(content.encode()).hexdigest()
```

### 6.3 前端实现

```tsx
// frontend/src/components/ArtifactEditor.tsx
import { useState, useCallback } from "react";

interface ArtifactEditProps {
  projectId: string;
  artifactPath: string;
  initialContent: string;
  initialHash: string;
  format: "md" | "yaml" | "json" | "txt";
  onSave?: (path: string, content: string) => void;
}

export function ArtifactEditor({
  projectId, artifactPath, initialContent, initialHash, format, onSave,
}: ArtifactEditProps) {
  const [content, setContent] = useState(initialContent);
  const [currentHash, setCurrentHash] = useState(initialHash);
  const [saving, setSaving] = useState(false);
  const [conflict, setConflict] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setConflict(null);
    setSaved(false);

    try {
      const res = await fetch(`/api/v1/artifacts/${artifactPath}/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content, expected_hash: currentHash }),
      });
      const result = await res.json();

      if (result.conflict_detected) {
        setConflict(result.message);
      } else if (result.success) {
        setCurrentHash(result.new_hash);
        setSaved(true);
        onSave?.(artifactPath, content);
      }
    } catch (e) {
      setConflict(String(e));
    } finally {
      setSaving(false);
    }
  }, [content, currentHash, artifactPath, onSave]);

  const isModified = content !== initialContent;

  return (
    <div className="artifact-editor">
      <div className="toolbar">
        <span className="path">{artifactPath}</span>
        <span className="hash" title={currentHash}>hash: {currentHash.slice(0, 8)}...</span>
        {isModified && <span className="modified">● Modified</span>}
        {saved && <span className="saved">Saved</span>}
        <button onClick={handleSave} disabled={!isModified || saving}>
          {saving ? "Saving..." : "Save"}
        </button>
      </div>

      {conflict && (
        <div className="conflict-banner">
          ⚠️ {conflict}
          <button onClick={() => window.location.reload()}>Reload</button>
        </div>
      )}

      <textarea
        className={`editor editor-${format}`}
        value={content}
        onChange={(e) => { setContent(e.target.value); setSaved(false); }}
        spellCheck={false}
      />
    </div>
  );
}
```

---

## 七、C4ReverseLocator (CL-01)

**文件**: `backend/app/c4/reverse_locator.py`
**依赖**: C4BaselineStore, BindingRegistry
**被依赖**: C4Browser (点击节点跳转代码)

### 7.1 设计目标

- Component/Code 级 C4 节点 → 本地代码文件路径
- 本地代码文件 → C4 DSL 节点（反向）
- 基于 BindingRegistry 的映射关系

### 7.2 核心实现

```python
# backend/app/c4/reverse_locator.py
import os
from typing import Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path

from app.c4.baseline_store import C4BaselineStore
from app.c4.binding_registry import BindingRegistry

@dataclass
class CodeLocation:
    """代码位置信息"""
    file_path: str           # 本地文件绝对路径
    line_number: Optional[int] = None
    snippet: Optional[str] = None

@dataclass
class NodeLocation:
    """C4 节点位置"""
    node_id: str
    node_type: str           # Component / Code
    level: str               # L3 / L4
    dsl_path: str            # 在 DSL 中的路径

class C4ReverseLocator:
    """
    C4 反向定位器

    职责:
    1. C4 节点 → 代码文件 (locate_code)
    2. 代码文件 → C4 节点 (locate_node)
    3. 基于 BindingRegistry 的 LOCATES_AT 关系
    """

    def __init__(
        self,
        baseline_store: C4BaselineStore,
        binding_registry: BindingRegistry,
        code_base_dir: str = "./projects",
    ):
        self.baseline = baseline_store
        self.bindings = binding_registry
        self.code_base_dir = Path(code_base_dir)

    # ============================================================
    # 正向: C4 节点 → 代码文件
    # ============================================================
    async def locate_code(
        self, project_id: str, c4_node_id: str
    ) -> Optional[CodeLocation]:
        """
        根据 C4 节点 ID 定位到本地代码文件

        策略:
        1. 先查 BindingRegistry（精确映射）
        2. 再按约定路径推导（兜底）
        """
        # 1. 查绑定关系
        bindings = await self.bindings.query_by_c4_node(project_id, c4_node_id)
        locates_at = [b for b in bindings if b.relation_type == "locates_at"]

        if locates_at:
            # 使用绑定的文件路径
            binding = locates_at[0]  # 取第一个
            file_path = binding.source_location or ""
            if file_path and os.path.exists(file_path):
                return CodeLocation(file_path=file_path)

        # 2. 约定路径推导
        return self._infer_code_path(project_id, c4_node_id)

    # ============================================================
    # 反向: 代码文件 → C4 节点
    # ============================================================
    async def locate_node(
        self, project_id: str, file_path: str
    ) -> Optional[NodeLocation]:
        """
        根据代码文件路径找到对应的 C4 节点
        """
        # 1. 查绑定关系
        bindings = await self.bindings.query_by_artifact(project_id, file_path)
        for binding in bindings:
            if binding.c4_level in ("L3", "L4"):
                return NodeLocation(
                    node_id=binding.c4_node_id,
                    node_type="Component" if binding.c4_level == "L3" else "Code",
                    level=binding.c4_level,
                    dsl_path=f"model.components.{binding.c4_node_id}",
                )

        # 2. 文件名匹配（兜底）
        return await self._match_by_filename(project_id, file_path)

    # ============================================================
    # 批量查询
    # ============================================================
    async def locate_codes_batch(
        self, project_id: str, node_ids: List[str]
    ) -> Dict[str, Optional[CodeLocation]]:
        """批量定位代码"""
        results = {}
        for node_id in node_ids:
            results[node_id] = await self.locate_code(project_id, node_id)
        return results

    async def locate_nodes_batch(
        self, project_id: str, file_paths: List[str]
    ) -> Dict[str, Optional[NodeLocation]]:
        """批量定位节点"""
        results = {}
        for file_path in file_paths:
            results[file_path] = await self.locate_node(project_id, file_path)
        return results

    # ============================================================
    # 内部方法
    # ============================================================
    def _infer_code_path(
        self, project_id: str, c4_node_id: str
    ) -> Optional[CodeLocation]:
        """按约定推导代码路径"""
        # 约定: {project_dir}/src/{component_name}/{file_name}.py
        project_dir = self.code_base_dir / project_id

        # 常见模式匹配
        patterns = [
            f"src/**/{c4_node_id}.py",
            f"src/**/{c4_node_id.lower()}.py",
            f"src/**/controllers/{c4_node_id}.py",
            f"**/{c4_node_id}.py",
        ]

        for pattern in patterns:
            matches = list(project_dir.rglob(pattern.replace("**/*", "").replace("*.py", ".py")))
            if matches:
                return CodeLocation(file_path=str(matches[0]))

        return None

    async def _match_by_filename(
        self, project_id: str, file_path: str
    ) -> Optional[NodeLocation]:
        """通过文件名匹配 C4 节点"""
        filename = Path(file_path).stem  # 如 "UserController"

        # 加载 DSL 查找匹配的组件
        baseline = await self.baseline.read_current(project_id)
        if not baseline:
            return None

        import yaml
        try:
            data = yaml.safe_load(baseline.dsl_content)
            components = data.get("workspace", {}).get("model", {}).get("components", [])
            for comp in components:
                if filename.lower() in comp["id"].lower() or filename.lower() in comp.get("name", "").lower():
                    return NodeLocation(
                        node_id=comp["id"],
                        node_type="Component",
                        level="L3",
                        dsl_path=f"model.components.{comp['id']}",
                    )
        except yaml.YAMLError:
            pass

        return None
```



---

## 八、API 接口总览

### 8.1 路由定义

```python
# backend/app/api/v1/validation.py
from fastapi import APIRouter, Depends, HTTPException

from app.c4.cross_layer_validator import CrossLayerValidator, ValidationReport
from app.c4.baseline_store import C4BaselineStore
from app.c4.binding_registry import BindingRegistry
from app.db.database import get_db

router = APIRouter(prefix="/validation", tags=["Validation"])

async def get_validator(db = Depends(get_db)):
    return CrossLayerValidator(C4BaselineStore(db), BindingRegistry(db))

@router.get("/cross-layer")
async def validate_cross_layer(
    project_id: str,
    validator: CrossLayerValidator = Depends(get_validator),
):
    """执行全量跨层校验"""
    report = await validator.validate(project_id)
    return {
        "passed": report.passed,
        "error_count": report.error_count,
        "warning_count": report.warning_count,
        "info_count": report.info_count,
        "issues": [
            {"rule_id": i.rule_id, "severity": i.severity.value,
             "message": i.message, "c4_node_id": i.c4_node_id,
             "suggestion": i.suggestion}
            for i in report.issues
        ],
        "summary": report.summary,
    }

@router.post("/cross-layer/incremental")
async def validate_incremental(
    project_id: str,
    changed_nodes: list[str],
    validator: CrossLayerValidator = Depends(get_validator),
):
    """增量校验 — 仅校验变更节点"""
    report = await validator.validate_incremental(project_id, changed_nodes)
    return {"passed": report.passed, "issues": report.issues}


# backend/app/api/v1/openui.py
from fastapi import APIRouter, Depends

from app.c4.open_ui_client import OpenUIClient, OpenUIGenerationResult
from app.c4.baseline_store import C4BaselineStore
from app.c4.interface_contract_store import InterfaceContractStore
from app.db.database import get_db

router = APIRouter(prefix="/openui", tags=["OpenUI"])

async def get_openui_client(db = Depends(get_db)):
    return OpenUIClient(C4BaselineStore(db), InterfaceContractStore(db))

@router.get("/health")
async def openui_health(client: OpenUIClient = Depends(get_openui_client)):
    """检测 OpenUI 服务健康"""
    return await client.check_health()

@router.post("/generate")
async def generate_prototype(
    project_id: str,
    spec_name: str = "prototype",
    client: OpenUIClient = Depends(get_openui_client),
):
    """从 C4 + 接口契约生成原型"""
    result = await client.generate_from_c4(project_id, spec_name)
    return {
        "spec_id": result.spec_id,
        "status": result.status,
        "html": result.html_content,
        "page_count": result.page_count,
        "page_titles": result.page_titles,
        "prompt_text": result.prompt_text,
        "duration_ms": result.duration_ms,
        "error": result.error_message,
    }


# backend/app/api/v1/contracts.py
from fastapi import APIRouter, Depends

from app.c4.interface_contract_store import (
    InterfaceContractStore, InterfaceContract,
)
from app.db.database import get_db

router = APIRouter(prefix="/contracts", tags=["Interface Contracts"])

async def get_store(db = Depends(get_db)):
    return InterfaceContractStore(db)

@router.post("/")
async def create_contract(contract: InterfaceContract, store = Depends(get_store)):
    contract_id = await store.create(contract)
    return {"contract_id": contract_id}

@router.get("/container/{container_id}")
async def list_container_contracts(
    project_id: str, container_id: str, store = Depends(get_store),
):
    contracts = await store.list_by_container(project_id, container_id)
    return {"contracts": contracts}

@router.post("/{contract_id}/freeze")
async def freeze_contract(contract_id: str, store = Depends(get_store)):
    await store.freeze(contract_id)
    return {"status": "frozen"}


# backend/app/api/v1/engine.py
from fastapi import APIRouter, Depends, BackgroundTasks

from app.engine.pocketflow_engine import PocketFlowEngine, SkillConfig, ExecutionResult
from app.common.project_context import ProjectContext

router = APIRouter(prefix="/engine", tags=["Execution Engine"])

@router.post("/execute")
async def execute_skill(
    background_tasks: BackgroundTasks,
    project_id: str,
    skill: SkillConfig,
):
    """执行单个 Skill"""
    with ProjectContext(project_id) as ctx:
        from app.engine.pocketflow_engine import KimiCLIAdapter
        engine = PocketFlowEngine(KimiCLIAdapter(), ctx)
        result = await engine.execute(skill)
        return {
            "skill_id": result.skill_id,
            "status": result.status.value,
            "exit_code": result.exit_code,
            "stdout": result.stdout[:2000],  # 截断
            "stderr": result.stderr[:2000],
            "output_artifacts": result.output_artifacts,
            "duration_ms": result.duration_ms,
        }

@router.get("/logs/{skill_id}")
async def get_skill_logs(skill_id: str, limit: int = 10):
    """获取 Skill 执行日志"""
    import glob, os
    log_files = sorted(
        glob.glob(f"./logs/{skill_id}_*.log"),
        key=os.path.getmtime, reverse=True,
    )[:limit]
    return {"logs": [os.path.basename(f) for f in log_files]}


# backend/app/api/v1/locator.py
from fastapi import APIRouter, Depends

from app.c4.reverse_locator import C4ReverseLocator, CodeLocation, NodeLocation
from app.c4.baseline_store import C4BaselineStore
from app.c4.binding_registry import BindingRegistry
from app.db.database import get_db

router = APIRouter(prefix="/locator", tags=["Reverse Locator"])

async def get_locator(db = Depends(get_db)):
    return C4ReverseLocator(C4BaselineStore(db), BindingRegistry(db))

@router.get("/code")
async def locate_code(
    project_id: str, node_id: str,
    locator: C4ReverseLocator = Depends(get_locator),
):
    """C4 节点 → 代码文件"""
    location = await locator.locate_code(project_id, node_id)
    if not location:
        raise HTTPException(404, f"Code location not found for node {node_id}")
    return {"file_path": location.file_path, "exists": os.path.exists(location.file_path)}

@router.get("/node")
async def locate_node(
    project_id: str, file_path: str,
    locator: C4ReverseLocator = Depends(get_locator),
):
    """代码文件 → C4 节点"""
    node = await locator.locate_node(project_id, file_path)
    if not node:
        raise HTTPException(404, f"C4 node not found for file {file_path}")
    return {"node_id": node.node_id, "type": node.node_type, "level": node.level}
```

### 8.2 API 端点汇总

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/validation/cross-layer` | 全量跨层校验 |
| POST | `/api/v1/validation/cross-layer/incremental` | 增量校验 |
| GET | `/api/v1/openui/health` | OpenUI 健康检测 |
| POST | `/api/v1/openui/generate` | 生成原型 |
| POST | `/api/v1/contracts/` | 创建接口契约 |
| GET | `/api/v1/contracts/container/{id}` | 查询容器接口 |
| POST | `/api/v1/contracts/{id}/freeze` | 冻结契约 |
| POST | `/api/v1/engine/execute` | 执行 Skill |
| GET | `/api/v1/engine/logs/{skill_id}` | 查询日志 |
| GET | `/api/v1/locator/code` | 节点→代码 |
| GET | `/api/v1/locator/node` | 代码→节点 |

---

## 九、测试策略

### 9.1 单元测试

```python
# tests/test_cross_layer_validator.py
import pytest
from app.c4.cross_layer_validator import CrossLayerValidator, RuleId, Severity

class TestCrossLayerValidator:
    def test_val003_unknown_container_ref(self):
        """组件引用了不存在的容器"""
        workspace = {
            "workspace": {
                "model": {
                    "containers": [{"id": "WebApp"}],
                    "components": [
                        {"id": "Ctrl", "properties": {"container_id": "NonExistent"}}
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val003_container_refs(workspace)

        assert len(issues) == 1
        assert issues[0].rule_id == RuleId.VAL_003
        assert issues[0].severity == Severity.ERROR
        assert "NonExistent" in issues[0].message

    def test_val003_valid_container_ref(self):
        """组件引用了存在的容器"""
        workspace = {
            "workspace": {
                "model": {
                    "containers": [{"id": "WebApp"}],
                    "components": [
                        {"id": "Ctrl", "properties": {"container_id": "WebApp"}}
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val003_container_refs(workspace)
        assert len(issues) == 0

    def test_val004_missing_container_id(self):
        """组件没有 container_id"""
        workspace = {
            "workspace": {
                "model": {
                    "containers": [{"id": "API"}],
                    "components": [{"id": "Ctrl", "properties": {}}],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val004_component_containers(workspace)

        assert len(issues) == 1
        assert issues[0].rule_id == RuleId.VAL_004
```

```python
# tests/test_open_ui_client.py
import pytest
from app.c4.open_ui_client import OpenUIClient

class TestOpenUIClient:
    def test_assemble_prompt(self):
        client = OpenUIClient(None, None)
        containers = [
            {"id": "Web", "name": "Web App", "technology": "React", "description": "Frontend"},
        ]
        contracts = {
            "Web": [
                type("C", (), {"method": "GET", "endpoint_path": "/api/users", "summary": "List users"})(),
            ]
        }
        prompt = client._assemble_prompt(containers, contracts)

        assert "Web App" in prompt
        assert "GET /api/users" in prompt
        assert "You are a UI generation assistant" in prompt

    def test_split_pages(self):
        client = OpenUIClient(None, None)
        html = """<html><!-- PAGE: Home --><body>Home</body><!-- PAGE: Detail --><body>Detail</body></html>"""
        pages = client._split_pages(html)

        assert len(pages) == 2
        assert pages[0]["title"] == "Home"
        assert pages[1]["title"] == "Detail"

    def test_split_single_page(self):
        client = OpenUIClient(None, None)
        pages = client._split_pages("<html><body>Single</body></html>")
        assert len(pages) == 1
```

```python
# tests/test_pocketflow_engine.py
import pytest
import asyncio
from app.engine.pocketflow_engine import PocketFlowEngine, SkillConfig, KimiCLIAdapter

class TestPocketFlowEngine:
    @pytest.mark.asyncio
    async def test_prep_phase_missing_input(self):
        """PREP 阶段检测到缺失的输入产物"""
        from app.common.project_context import ProjectContext

        ctx = ProjectContext("test-proj", base_dir="/tmp/test")
        engine = PocketFlowEngine(KimiCLIAdapter(), ctx)

        skill = SkillConfig(
            skill_id="test",
            name="Test Skill",
            file_path="test.py",
            inputs=["nonexistent.md"],
            outputs=["output.md"],
        )

        with pytest.raises(FileNotFoundError):
            await engine._prep_phase(skill)

    def test_kimi_cli_build_command(self):
        adapter = KimiCLIAdapter()
        cmd = adapter.build_command("skill.py", {"input": "/path/to/input.md"})
        assert cmd == ["kimi", "run", "skill.py", "--input", "input=/path/to/input.md"]
```

```python
# tests/test_reverse_locator.py
import pytest
from app.c4.reverse_locator import C4ReverseLocator

class TestC4ReverseLocator:
    def test_infer_code_path(self):
        """按约定推导代码路径"""
        locator = C4ReverseLocator(None, None, code_base_dir="/tmp")
        # 没有文件系统，返回 None
        result = locator._infer_code_path("test", "UserController")
        # 由于目录不存在，返回 None
        assert result is None
```

---

## 附录 A：验收标准

### A.1 功能验收（6 项）

| # | 组件 | 验收项 | 验证方法 |
|---|------|--------|----------|
| 1 | CrossLayerValidator | VAL-001~008 规则执行正确 | 单元测试覆盖每条规则 |
| 2 | InterfaceContractStore | CRUD + 状态机正常 | 单元测试 + API 测试 |
| 3 | OpenUIClient | 健康检测 + 提示词组装 + 降级 | mock OpenUI 服务测试 |
| 4 | PocketFlowEngine | 三阶段执行 + 超时管理 | 集成测试（使用 mock CLI） |
| 5 | ArtifactEditor | 编辑 + 冲突检测 | 前后端集成测试 |
| 6 | C4ReverseLocator | 节点→代码 + 代码→节点 | 单元测试 |

### A.2 端到端验收

```
[ ] E2E-01: C4 DSL 变更 → 增量校验 → 仅校验变更节点 → 报告正确
[ ] E2E-02: C4 DSL + 接口契约 → OpenUIClient → HTML 原型生成
[ ] E2E-03: OpenUI 服务不可用 → 自动降级 Wireframe → 用户可查看
[ ] E2E-04: Skill 配置 → PocketFlowEngine → 三阶段执行 → 超时处理
[ ] E2E-05: 产物编辑 → 外部修改 → 冲突检测 → 提示用户
[ ] E2E-06: 点击 C4 组件节点 → 反向定位 → 打开对应代码文件
```

### A.3 性能验收

| 指标 | 目标 |
|------|------|
| 跨层校验 | < 200ms / 100 个节点 |
| OpenUI 调用 | < 15s（含降级） |
| Skill 执行 | 按配置 timeout 执行 |
| 反向定位 | < 50ms |
| 冲突检测 | < 10ms |

---

> **文档结束**
>
> 批次：Batch-02（架构验证 + 原型服务 + 执行引擎）
> 组件数：6 个
> 预计周期：4 周
> 版本：v1.0

