# 批次一详细设计文档：C4 DSL 基线 + 架构图渲染 + 草图生成

> **批次编号**: Batch-01
> **目标**: 文档能进去，C4 DSL 能出来，能渲染架构图，能生成线框图和草图
> **周期**: 6 周
> **组件数**: 19 个
> **验收标准**: 见文末附录 A

---

## 目录

1. [设计概览](#一设计概览)
2. [基础设施层（5 组件）](#二基础设施层)
3. [文档接入层（3 组件）](#三文档接入层)
4. [提取编排层（2 组件）](#四提取编排层)
5. [编译蒸馏层（1 组件）](#五编译蒸馏层)
6. [存储校验层（2 组件）](#六存储校验层)
7. [消费渲染层（5 组件）](#七消费渲染层)
8. [数据模型总览](#八数据模型总览)
9. [API 接口总览](#九api-接口总览)
10. [测试策略](#十测试策略)
11. [附录 A：验收标准](#附录-a验收标准)

---

## 一、设计概览

### 1.1 批次架构图

```
================================================================================
                          前端 (React 19 + Vite 6)
================================================================================
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ C4Renderer   │  │ArtifactRender│  │WireframeView │  │ SketchView   │
  │ (Mermaid.js) │  │ (Markdown/   │  │ (SVG inline) │  │ (HTML iframe)│
  │              │  │  Mermaid/    │  │              │  │              │
  │  L1/L2/L3/L4 │  │  YAML/JSON)  │  │  页面布局+   │  │  低保真      │
  │  架构图渲染  │  │              │  │  跳转关系    │  │  页面草图    │
  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
         │                 │                 │                 │
         └─────────────────┴─────────────────┴─────────────────┘
                                      │
================================================================================
                          后端 (FastAPI 0.115)
================================================================================
         │                          API 路由层
         │                 ┌─────────────────────────┐
         │                 │ /api/v1/c4/dsl          │
         │                 │ /api/v1/c4/render       │
         │                 │ /api/v1/c4/wireframe    │
         │                 │ /api/v1/c4/sketch       │
         │                 │ /api/v1/artifacts       │
         │                 │ /api/v1/documents       │
         │                 └─────────────────────────┘
         │                          │
  ┌──────▼────────┐  ┌─────────────▼──────────────┐  ┌──────────────────────┐
  │ C4DSLManager  │  │   WireframeEngine          │  │ SketchGenerator      │
  │ (DM-01)       │  │   (WE-01)                  │  │ (SG-01)              │
  │               │  │                            │  │                      │
  │ 读写 DSL 文件 │  │  DomainMapper              │  │ PageSpec 解析        │
  │ 版本管理      │  │  LayoutPlanner             │  │ HTML 草图生成        │
  │ 手动编辑覆盖  │  │  NavigationLinker          │  │                      │
  └──────┬────────┘  └─────────────┬──────────────┘  └──────────┬───────────┘
         │                         │                            │
         │              ┌──────────▼──────────┐                 │
         │              │ C4BaselineStore     │◄────────────────┘
         └──────────────► (CB-01)             │    (读取 L2 entities)
                        │                     │
                        │  arsitect.aac.yml   │
                        │  版本化存储         │
                        │  基线对比回滚       │
                        └──────────┬──────────┘
                                   │
  ┌────────────────────────────────┼──────────────────────────────────────┐
  │                    C4Assembler (CA-01)                               │
  │                    片段 → 去重 → 合并 → DSL                          │
  └────────────────────────────────┬──────────────────────────────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │ C4Extractor (CE-01) │
                        │ 按 doc_type 路由提取 │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │StructuredExtractor    │
                        │(SE-01)                │
                        │@C4- 标签正则提取      │
                        │confidence=1.0         │
                        └──────────┬──────────┘
                                   │
  ┌────────────────────────────────┼──────────────────────────────────────┐
  │                    文档接入层                                         │
  │  DocLinter → DocumentTemplateEngine → FragmentRegistry              │
  └────────────────────────────────┬──────────────────────────────────────┘
                                   │
================================================================================
                          基础设施底座
================================================================================
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │DatabaseAdapt │  │   EventBus   │  │ProjectContext│  │ArtifactStore │
  │  (DB-01)     │  │   (EB-01)    │  │   (PC-01)    │  │   (AS-01)    │
  │              │  │              │  │              │  │              │
  │SQLAlchemy 2.0│  │async pub/sub │  │ContextVar    │  │File I/O +   │
  │AsyncSession  │  │DomainEvent   │  │项目目录/Git  │  │Hash + Git   │
  │SQLite        │  │              │  │              │  │auto-commit  │
  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

### 1.2 核心数据流

```
用户上传 PRD.md
    │
    ▼
DocLinter.lint() ──→ 诊断 + 自动修复
    │
    ▼
DocumentTemplateEngine.validate() ──→ 模板校验
    │
    ▼
StructuredExtractor.extract() ──→ 提取 @C4-System, @C4-Actor 等标签
    │
    ▼
C4Extractor.extract() ──→ 按 PRD 路由提取 C4Snippet[]
    │
    ▼
C4Assembler.assemble() ──→ 去重 + 合并 ──→ C4Workspace
    │
    ▼
C4BaselineStore.write() ──→ 持久化 arsitect.aac.yml
    │
    ├──→ C4DSLManager.read() ──→ C4Renderer.render() ──→ Mermaid 图
    │
    ├──→ C4BaselineStore.read() ──→ WireframeEngine.generate() ──→ SVG
    │
    └──→ FragmentRegistry.read() ──→ SketchGenerator.generate() ──→ HTML
```

### 1.3 文件目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI 入口
│   ├── config.py                   # ConfigManager 配置
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py             # DatabaseAdapter
│   │   ├── models.py               # SQLAlchemy 模型
│   │   └── repositories.py         # 数据访问层
│   ├── common/
│   │   ├── __init__.py
│   │   ├── event_bus.py            # EventBus
│   │   ├── project_context.py      # ProjectContext
│   │   ├── artifact_store.py       # ArtifactStore
│   │   └── config_manager.py       # ConfigManager
│   ├── docforge/
│   │   ├── __init__.py
│   │   ├── doc_linter.py           # DocLinter
│   │   ├── template_engine.py      # DocumentTemplateEngine
│   │   ├── fragment_registry.py    # FragmentRegistry
│   │   ├── structured_extractor.py # StructuredExtractor
│   │   ├── c4_extractor.py         # C4Extractor
│   │   ├── c4_assembler.py         # C4Assembler
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── template_schemas.py # 模板定义
│   │       └── extraction_schemas.py # 提取结果 schema
│   ├── c4/
│   │   ├── __init__.py
│   │   ├── baseline_store.py       # C4BaselineStore
│   │   ├── binding_registry.py     # BindingRegistry
│   │   ├── dsl_manager.py          # C4DSLManager
│   │   ├── dsl_models.py           # DSL 数据模型 (C4Workspace)
│   │   ├── renderer.py             # C4Renderer (后端部分)
│   │   ├── wireframe_engine.py     # WireframeEngine
│   │   └── sketch_generator.py     # SketchGenerator
│   ├── artifacts/
│   │   ├── __init__.py
│   │   └── renderer.py             # ArtifactRenderer (后端支持)
│   └── api/
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           ├── c4.py               # C4 路由
│           ├── documents.py        # 文档路由
│           ├── wireframe.py        # 线框图路由
│           ├── sketch.py           # 草图路由
│           └── artifacts.py        # 产物路由
├── tests/
│   ├── conftest.py
│   ├── test_doc_linter.py
│   ├── test_template_engine.py
│   ├── test_structured_extractor.py
│   ├── test_c4_extractor.py
│   ├── test_c4_assembler.py
│   ├── test_baseline_store.py
│   ├── test_dsl_manager.py
│   ├── test_renderer.py
│   ├── test_wireframe_engine.py
│   └── test_sketch_generator.py
└── alembic/                        # 数据库迁移

frontend/
├── src/
│   ├── components/
│   │   ├── C4Renderer.tsx          # C4 架构图渲染 (mermaid)
│   │   ├── ArtifactRenderer.tsx    # 产物多模态渲染
│   │   ├── WireframeViewer.tsx     # 线框图预览
│   │   ├── SketchViewer.tsx        # 草图预览
│   │   └── DocumentUploader.tsx    # 文档上传
│   ├── pages/
│   │   ├── C4Workbench.tsx         # C4 工作台
│   │   ├── DocumentHub.tsx         # 文档中心
│   │   └── PrototypeLab.tsx        # 原型实验室
│   ├── hooks/
│   │   ├── useC4DSL.ts             # C4 DSL 操作
│   │   ├── useWireframe.ts         # 线框图
│   │   └── useSketch.ts            # 草图
│   └── services/
│       ├── c4Api.ts                # C4 API 封装
│       ├── documentApi.ts          # 文档 API 封装
│       └── artifactApi.ts          # 产物 API 封装
```



---

## 二、基础设施层

### 2.1 DatabaseAdapter (DB-01)

**文件**: `backend/app/db/database.py`
**依赖**: 无（底座组件）
**被依赖**: EventBus, ProjectContext, ArtifactStore, 所有 Repository

#### 2.1.1 设计目标

- SQLAlchemy 2.0 异步 ORM 封装
- MVP 阶段使用 SQLite（aiosqlite），P1 迁移 PostgreSQL 时仅改连接字符串
- AsyncSession 管理，自动事务边界
- 连接池配置

#### 2.1.2 核心实现

```python
# backend/app/db/database.py
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker, AsyncAttrs
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, Enum, JSON
from datetime import datetime
import enum
import uuid

# ============================================================
# 连接配置
# ============================================================
# MVP: SQLite (aiosqlite)
# P1:  改为 postgresql+asyncpg://user:pass@localhost/arsitect
DATABASE_URL = "sqlite+aiosqlite:///./arsitect.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,           # True 开启 SQL 日志（调试）
    pool_pre_ping=True,   # 连接前 ping，自动重连
    pool_recycle=3600,    # 1 小时回收连接
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 防止延迟加载问题
    autoflush=False,
)

# ============================================================
# 基类
# ============================================================
class Base(AsyncAttrs, DeclarativeBase):
    """所有模型的异步基类"""
    pass

class UuidMixin:
    """UUID 主键混入"""
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

class TimestampMixin:
    """时间戳混入"""
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============================================================
# 数据库初始化
# ============================================================
async def init_db():
    """创建所有表（首次启动时调用）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """关闭连接池"""
    await engine.dispose()

# ============================================================
# 依赖注入用（FastAPI Depends）
# ============================================================
async def get_db() -> AsyncSession:
    """FastAPI 依赖注入函数"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

#### 2.1.3 数据库模型

```python
# backend/app/db/models.py
from app.db.database import Base, UuidMixin, TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, Enum, JSON
import enum

# ============================================================
# Project 模型
# ============================================================
class ProjectState(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"

class Project(Base, UuidMixin, TimestampMixin):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    state: Mapped[ProjectState] = mapped_column(Enum(ProjectState), default=ProjectState.DRAFT)
    complexity_route: Mapped[str | None] = mapped_column(String(20))  # xs/s/m/l/xl
    base_dir: Mapped[str] = mapped_column(String(500), default="./projects")

    # 关系
    c4_baselines: Mapped[list["C4Baseline"]] = relationship(back_populates="project", lazy="selectin")
    fragments: Mapped[list["Fragment"]] = relationship(back_populates="project", lazy="selectin")
    bindings: Mapped[list["BindingRecord"]] = relationship(back_populates="project", lazy="selectin")

# ============================================================
# C4 Baseline 模型（DSL 版本存储）
# ============================================================
class C4Baseline(Base, UuidMixin, TimestampMixin):
    __tablename__ = "c4_baselines"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"))
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    dsl_content: Mapped[str] = mapped_column(Text, nullable=False)  # YAML DSL 全文
    dsl_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    level: Mapped[str] = mapped_column(String(10), default="L1-L4")  # L1/L2/L3/L4
    is_current: Mapped[bool] = mapped_column(default=True)
    compiled_from: Mapped[list[str] | None] = mapped_column(JSON)  # 来源文档 ID 列表

    project: Mapped["Project"] = relationship(back_populates="c4_baselines")

# ============================================================
# Fragment 模型（文档片段）
# ============================================================
class FragmentState(str, enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    DEPRECATED = "deprecated"

class Fragment(Base, UuidMixin, TimestampMixin):
    __tablename__ = "fragments"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"))
    module_id: Mapped[str | None] = mapped_column(String(36))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)  # URL 友好标识
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PRD/ARCH/DETAIL...
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[FragmentState] = mapped_column(Enum(FragmentState), default=FragmentState.DRAFT)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    metadata: Mapped[dict | None] = mapped_column(JSON)  # Front Matter, c4_binding 等

    project: Mapped["Project"] = relationship(back_populates="fragments")

# ============================================================
# BindingRecord 模型（绑定图谱）
# ============================================================
class BindingRelation(str, enum.Enum):
    BINDS_TO = "binds_to"           # PRD -> L1 System
    INJECTS_INTO = "injects_into"   # Entity -> L2 Container
    IMPLEMENTS = "implements"       # Code -> L3 Component
    LOCATES_AT = "locates_at"       # File -> L4 Code
    GENERATES = "generates"         # C4 -> Wireframe/Sketch

class BindingRecord(Base, UuidMixin, TimestampMixin):
    __tablename__ = "binding_records"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"))
    artifact_id: Mapped[str] = mapped_column(String(200), nullable=False)  # 产物标识
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PRD/Fragment...
    c4_node_id: Mapped[str] = mapped_column(String(200), nullable=False)   # C4 节点 ID
    c4_level: Mapped[str] = mapped_column(String(5), nullable=False)       # L1/L2/L3/L4
    relation_type: Mapped[BindingRelation] = mapped_column(Enum(BindingRelation))
    confidence: Mapped[float] = mapped_column(default=1.0)
    source_location: Mapped[str | None] = mapped_column(String(500))  # 文档内位置

    project: Mapped["Project"] = relationship(back_populates="bindings")
```

---

### 2.2 EventBus (EB-01)

**文件**: `backend/app/common/event_bus.py`
**依赖**: DatabaseAdapter（可选，事件持久化）
**被依赖**: C4BaselineStore, BindingRegistry, FileSystemWatcher, GateController

#### 2.2.1 设计目标

- 纯内存异步事件总线，发布/订阅模式
- 错误隔离：处理器失败不影响发布者和其他处理器
- 类型安全：DomainEvent 数据类
- 无需外部依赖（Redis/RabbitMQ），MVP 阶段足够

#### 2.2.2 核心实现

```python
# backend/app/common/event_bus.py
import asyncio
from typing import Dict, List, Callable, Any, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
import traceback

@dataclass
class DomainEvent:
    """领域事件"""
    event_type: str           # 事件类型，如 "c4.baseline.created"
    aggregate_id: str         # 聚合根 ID，如 project_id
    payload: Dict[str, Any]   # 事件载荷
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    source: str = ""          # 事件来源组件名

class EventBus:
    """
    异步事件总线

    使用方式:
        bus = EventBus()

        # 订阅
        bus.subscribe("c4.baseline.created", on_baseline_created)

        # 发布
        bus.publish(DomainEvent("c4.baseline.created", project_id, {...}))
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_queue: asyncio.Queue[DomainEvent] = asyncio.Queue()
        self._dispatch_task: asyncio.Task | None = None
        self._running = False

    async def start(self):
        """启动事件分发循环（应用启动时调用）"""
        if self._running:
            return
        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())

    async def stop(self):
        """停止事件分发（应用关闭时调用）"""
        self._running = False
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], Awaitable[None] | None]):
        """订阅事件类型"""
        self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: Callable):
        """取消订阅"""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [h for h in self._subscribers[event_type] if h != handler]

    def publish(self, event: DomainEvent):
        """发布事件（非阻塞，立即返回）"""
        asyncio.create_task(self._event_queue.put(event))

    async def _dispatch_loop(self):
        """事件分发循环"""
        while self._running:
            try:
                event = await self._event_queue.get()
                await self._dispatch(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[EventBus] Dispatch loop error: {e}")

    async def _dispatch(self, event: DomainEvent):
        """分发事件到所有订阅者"""
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                # 错误隔离：一个处理器失败不影响其他
                print(f"[EventBus] Handler error for {event.event_type}: {e}")
                traceback.print_exc()

    def get_subscriber_count(self, event_type: str) -> int:
        """获取某事件类型的订阅者数量"""
        return len(self._subscribers.get(event_type, []))

# ============================================================
# 全局事件总线实例（单例）
# ============================================================
_event_bus: EventBus | None = None

def get_event_bus() -> EventBus:
    """获取全局事件总线（懒加载单例）"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
```

---

### 2.3 ProjectContext (PC-01)

**文件**: `backend/app/common/project_context.py`
**依赖**: DatabaseAdapter
**被依赖**: ArtifactStore, C4DSLManager, C4BaselineStore, PocketFlowEngine

#### 2.3.1 设计目标

- 线程安全的项目上下文（使用 ContextVar）
- 统一管理项目目录、Git 句柄、全局参数
- with 语句确保上下文正确清理
- 延迟加载 Git 仓库

#### 2.3.2 核心实现

```python
# backend/app/common/project_context.py
from contextvars import ContextVar
from pathlib import Path
from typing import Optional
import os

# ContextVar: 线程安全地存储当前项目 ID
_project_ctx: ContextVar[Optional[str]] = ContextVar("project_id", default=None)

class ProjectContext:
    """
    项目上下文管理器

    使用:
        with ProjectContext(project_id, base_dir="./projects") as ctx:
            # ctx.artifacts_dir  -> ./projects/{id}/artifacts/
            # ctx.logs_dir       -> ./projects/{id}/logs/
            # ctx.repo           -> GitPython Repo 实例
            content = await ctx.read_artifact("design.md")
    """

    def __init__(self, project_id: str, base_dir: str = "./projects"):
        self.project_id = project_id
        self.base_dir = Path(base_dir)
        self.project_dir = self.base_dir / project_id
        self.artifacts_dir = self.project_dir / "artifacts"
        self.logs_dir = self.project_dir / "logs"
        self.dsl_dir = self.project_dir / "dsl"
        self._repo = None
        self._token = None

    def __enter__(self):
        self._token = _project_ctx.set(self.project_id)
        # 确保目录存在
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.dsl_dir.mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token:
            _project_ctx.reset(self._token)

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.__exit__(exc_type, exc_val, exc_tb)

    @property
    def repo(self):
        """延迟加载 Git 仓库"""
        if self._repo is None:
            from git import Repo
            git_dir = self.project_dir / ".git"
            if git_dir.exists():
                self._repo = Repo(self.project_dir)
            else:
                self._repo = Repo.init(self.project_dir)
        return self._repo

    def read_artifact(self, relative_path: str) -> str:
        """读取产物文件"""
        full_path = self.artifacts_dir / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Artifact not found: {relative_path}")
        return full_path.read_text(encoding="utf-8")

    def write_artifact(self, relative_path: str, content: str) -> Path:
        """写入产物文件"""
        full_path = self.artifacts_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return full_path

    def get_dsl_path(self, filename: str = "arsitect.aac.yml") -> Path:
        """获取 DSL 文件路径"""
        return self.dsl_dir / filename

# ============================================================
# 便捷函数
# ============================================================
def get_current_project_id() -> Optional[str]:
    """获取当前上下文中的项目 ID"""
    return _project_ctx.get()
```

---

### 2.4 ArtifactStore (AS-01)

**文件**: `backend/app/common/artifact_store.py`
**依赖**: DatabaseAdapter, ProjectContext
**被依赖**: C4BaselineStore, FragmentRegistry, C4DSLManager

#### 2.4.1 设计目标

- 统一产物文件读写接口
- 自动 SHA-256 哈希计算与缓存
- Git 自动提交（可配置）
- 外部变更检测（哈希对比）
- 冲突检测（保存时对比存储哈希）

#### 2.4.2 核心实现

```python
# backend/app/common/artifact_store.py
import hashlib
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Tuple
from app.common.project_context import ProjectContext

class ArtifactStore:
    """
    产物存储抽象层

    职责:
    1. 统一文件读写（支持中文、大文件）
    2. 自动计算并缓存 SHA-256 哈希
    3. Git 自动提交（可选）
    4. 外部变更检测

    依赖:
    - ProjectContext: 获取项目目录
    """

    def __init__(self, ctx: ProjectContext, auto_git_commit: bool = True):
        self.ctx = ctx
        self.auto_git_commit = auto_git_commit
        self._hash_cache: Dict[str, str] = {}  # relative_path -> sha256

    # ============================================================
    # 读操作
    # ============================================================
    async def read(self, relative_path: str) -> str:
        """异步读取产物内容"""
        full_path = self.ctx.artifacts_dir / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Artifact not found: {relative_path} (project={self.ctx.project_id})")
        async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
            return await f.read()

    def read_sync(self, relative_path: str) -> str:
        """同步读取（用于非 async 上下文）"""
        full_path = self.ctx.artifacts_dir / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Artifact not found: {relative_path}")
        return full_path.read_text(encoding="utf-8")

    # ============================================================
    # 写操作
    # ============================================================
    async def write(
        self, 
        relative_path: str, 
        content: str, 
        auto_commit: bool = True,
        commit_message: Optional[str] = None
    ) -> Tuple[Path, str]:
        """
        写入产物

        Returns:
            (file_path, hash) - 文件路径和内容哈希
        """
        full_path = self.ctx.artifacts_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
            await f.write(content)

        # 计算哈希
        new_hash = self._compute_hash(content)
        old_hash = self._hash_cache.get(relative_path)
        self._hash_cache[relative_path] = new_hash

        # Git 自动提交
        if auto_commit and self.auto_git_commit:
            self._git_commit(relative_path, commit_message or f"Update {relative_path}")

        return full_path, new_hash

    # ============================================================
    # 哈希管理
    # ============================================================
    async def get_hash(self, relative_path: str) -> str:
        """获取产物哈希（优先缓存，缓存未命中则计算）"""
        if relative_path not in self._hash_cache:
            content = await self.read(relative_path)
            self._hash_cache[relative_path] = self._compute_hash(content)
        return self._hash_cache[relative_path]

    def check_external_change(self, relative_path: str) -> Tuple[bool, Optional[str]]:
        """
        检测外部变更

        Returns:
            (changed, current_hash) - 是否变更，当前哈希
        """
        full_path = self.ctx.artifacts_dir / relative_path
        if not full_path.exists():
            return True, None

        stored_hash = self._hash_cache.get(relative_path)
        if stored_hash is None:
            return False, None  # 从未缓存过，不算外部变更

        current_content = full_path.read_text(encoding="utf-8")
        current_hash = self._compute_hash(current_content)

        return current_hash != stored_hash, current_hash

    # ============================================================
    # 内部方法
    # ============================================================
    @staticmethod
    def _compute_hash(content: str) -> str:
        """计算 SHA-256 哈希"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _git_commit(self, relative_path: str, message: str):
        """Git 自动提交"""
        try:
            repo = self.ctx.repo
            full_path = self.ctx.artifacts_dir / relative_path
            repo.index.add([str(full_path.relative_to(self.ctx.project_dir))])
            if repo.is_dirty():
                repo.index.commit(message)
        except Exception as e:
            # Git 提交失败不阻塞主流程
            print(f"[ArtifactStore] Git commit warning: {e}")
```

---

### 2.5 ConfigManager (CM-01)

**文件**: `backend/app/config.py`
**依赖**: 无
**被依赖**: 所有需要配置的组件

#### 2.5.1 设计目标

- Pydantic Settings 管理环境变量和配置文件
- 分层配置：默认 → 文件 → 环境变量
- 类型安全

#### 2.5.2 核心实现

```python
# backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略未定义的环境变量
    )

    # 应用基础
    app_name: str = "Arsitect"
    debug: bool = Field(default=False, alias="DEBUG")

    # 数据库
    database_url: str = Field(default="sqlite+aiosqlite:///./arsitect.db", alias="DATABASE_URL")

    # 项目存储
    projects_base_dir: str = Field(default="./projects", alias="PROJECTS_BASE_DIR")

    # OpenUI 服务（P1 阶段使用）
    openui_base_url: str = Field(default="http://localhost:3000", alias="OPENUI_BASE_URL")
    openui_timeout: int = Field(default=15, alias="OPENUI_TIMEOUT")

    # 执行引擎
    skill_timeout: float = Field(default=90.0, alias="SKILL_TIMEOUT")
    skill_kill_timeout: float = Field(default=30.0, alias="SKILL_KILL_TIMEOUT")

    # C4 渲染
    mermaid_theme: str = Field(default="default", alias="MERMAID_THEME")
    wireframe_canvas_width: int = Field(default=800, alias="WIREFRAME_WIDTH")
    wireframe_canvas_height: int = Field(default=600, alias="WIREFRAME_HEIGHT")

# 全局配置实例
settings = Settings()

# 便捷访问
def get_settings() -> Settings:
    return settings
```



---

## 三、文档接入层

### 3.1 DocLinter (DL-01)

**文件**: `backend/app/docforge/doc_linter.py`
**依赖**: ConfigManager
**被依赖**: DocumentTemplateEngine（预处理）

#### 3.1.1 设计目标

- 文档进入平台的第一道闸门
- 自动诊断 + 修复，减少人工干预
- 四级严重度：BLOCKER / ERROR / WARNING / INFO
- 三种修复策略：AUTO / SEMI_AUTO / MANUAL
- 支持六类文档模板（PRD/DOMAIN_MODEL/ARCH/DETAIL_DESIGN/API_DESIGN/DB_DESIGN）

#### 3.1.2 核心实现

```python
# backend/app/docforge/doc_linter.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum, auto
from pathlib import Path
import re
import yaml

class Severity(Enum):
    BLOCKER = auto()   # 阻断：缺少 c4_binding 或 doc_type 无法识别
    ERROR = auto()     # 错误：必填 @C4- 标签缺失
    WARNING = auto()   # 警告：标签格式不规范
    INFO = auto()      # 提示：可优化项

class FixStrategy(Enum):
    AUTO = auto()      # 自动修复
    SEMI_AUTO = auto() # 半自动（生成建议值，标记 TODO）
    MANUAL = auto()    # 必须人工处理

@dataclass
class LintIssue:
    """诊断问题"""
    rule_id: str           # VAL-DOC-001
    severity: Severity
    message: str
    location: str          # "第3行" 或 "章节：业务规则"
    fix_hint: str
    auto_fixable: bool
    fix_strategy: FixStrategy

@dataclass
class LintReport:
    """诊断报告"""
    file_path: str
    doc_type: Optional[str]
    passed: bool
    issues: List[LintIssue] = field(default_factory=list)
    fixed_content: Optional[str] = None
    summary: str = ""

class DocLinter:
    """
    文档诊断与修复引擎

    核心流程:
    1. 识别文档类型（文件名/内容特征）
    2. 校验 Front Matter 完整性
    3. 校验 c4_binding 区块
    4. 校验 @C4- 标签
    5. 自动修复 + 生成报告
    """

    # 六类文档模板定义
    TEMPLATES = {
        "PRD": {
            "required_frontmatter": ["c4_binding", "title", "version"],
            "required_c4_tags": ["@C4-System", "@C4-Actor"],
            "optional_c4_tags": ["@C4-External-System"],
            "required_sections": ["## 背景", "## 目标", "## 范围"],
            "expected_level": "L1",
        },
        "DOMAIN_MODEL": {
            "required_frontmatter": ["c4_binding", "domain", "entities"],
            "required_c4_tags": ["@C4-Entity", "@C4-Relationship"],
            "optional_c4_tags": ["@C4-Attribute", "@C4-Enum"],
            "required_sections": ["## 领域概述", "## 实体定义"],
            "expected_level": "L2",
        },
        "ARCH": {
            "required_frontmatter": ["c4_binding", "architecture_style"],
            "required_c4_tags": ["@C4-Container", "@C4-Technology"],
            "optional_c4_tags": ["@C4-Component", "@C4-Relation"],
            "required_sections": ["## 架构概述", "## 容器定义"],
            "expected_level": "L2",
        },
        "DETAIL_DESIGN": {
            "required_frontmatter": ["c4_binding", "module"],
            "required_c4_tags": ["@C4-Component", "@C4-Code-Path"],
            "optional_c4_tags": ["@C4-Interface", "@C4-Page-Type"],
            "required_sections": ["## 模块概述", "## 组件设计"],
            "expected_level": "L3",
        },
        "API_DESIGN": {
            "required_frontmatter": ["c4_binding", "base_url"],
            "required_c4_tags": ["@C4-Interface", "@C4-Method"],
            "optional_c4_tags": ["@C4-Request", "@C4-Response"],
            "required_sections": ["## 接口概述", "## 接口清单"],
            "expected_level": "L3",
        },
        "DB_DESIGN": {
            "required_frontmatter": ["c4_binding", "storage"],
            "required_c4_tags": ["@C4-Table", "@C4-Column"],
            "optional_c4_tags": ["@C4-Index", "@C4-Constraint"],
            "required_sections": ["## 存储概述", "## 表结构"],
            "expected_level": "L2",
        },
    }

    # 正则规则库
    RULES = {
        "frontmatter": re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL),
        "c4_tag": re.compile(r"@C4-([A-Za-z0-9-]+):([^\s\n]+)"),
        "section_anchor": re.compile(r"^(#{1,6})\s+(.+?)\s*\{#([a-zA-Z0-9_-]+)\}\s*$"),
    }

    def __init__(self, auto_fix: bool = True, strict_mode: bool = False):
        self.auto_fix = auto_fix
        self.strict_mode = strict_mode

    # ============================================================
    # 主入口
    # ============================================================
    def lint(self, content: str, file_path: str = "") -> LintReport:
        """诊断文档"""
        issues: List[LintIssue] = []
        fixed_content = content

        # 1. 识别文档类型
        doc_type = self._detect_doc_type(content, file_path)
        if not doc_type:
            issues.append(LintIssue(
                rule_id="VAL-DOC-001",
                severity=Severity.BLOCKER,
                message="无法识别文档类型",
                location="文件头",
                fix_hint="在 YAML Front Matter 中添加 doc_type: PRD",
                auto_fixable=False,
                fix_strategy=FixStrategy.MANUAL,
            ))
            return self._build_report(file_path, None, issues, content)

        template = self.TEMPLATES[doc_type]

        # 2. 校验 Front Matter
        fm, fm_issues, fixed_content = self._check_frontmatter(fixed_content, doc_type, template)
        issues.extend(fm_issues)

        # 3. 校验 c4_binding
        if fm:
            binding_issues, fixed_content = self._check_c4_binding(
                fixed_content, doc_type, template, fm
            )
            issues.extend(binding_issues)

        # 4. 校验 @C4- 标签
        tag_issues, fixed_content = self._check_c4_tags(fixed_content, doc_type, template)
        issues.extend(tag_issues)

        return self._build_report(file_path, doc_type, issues, fixed_content)

    def fix(self, content: str, file_path: str = "") -> Tuple[str, LintReport]:
        """诊断并修复"""
        self.auto_fix = True
        report = self.lint(content, file_path)
        return report.fixed_content or content, report

    # ============================================================
    # 文档类型识别
    # ============================================================
    def _detect_doc_type(self, content: str, file_path: str) -> Optional[str]:
        """基于文件名和内容特征识别文档类型"""
        # 文件名匹配
        name_map = {
            "prd": "PRD", "requirement": "PRD",
            "domain": "DOMAIN_MODEL", "entity": "DOMAIN_MODEL",
            "arch": "ARCH", "architecture": "ARCH",
            "detail": "DETAIL_DESIGN", "design": "DETAIL_DESIGN",
            "api": "API_DESIGN", "interface": "API_DESIGN",
            "db": "DB_DESIGN", "database": "DB_DESIGN",
        }

        file_lower = Path(file_path).stem.lower()
        for key, doc_type in name_map.items():
            if key in file_lower:
                return doc_type

        # 内容特征回退
        if "接口" in content and ("GET" in content or "POST" in content):
            return "API_DESIGN"
        if "容器" in content and "技术栈" in content:
            return "ARCH"

        # Front Matter
        fm_match = self.RULES["frontmatter"].search(content)
        if fm_match:
            try:
                fm = yaml.safe_load(fm_match.group(1))
                if fm and "doc_type" in fm:
                    return fm["doc_type"].upper()
            except yaml.YAMLError:
                pass

        return None

    # ============================================================
    # Front Matter 校验
    # ============================================================
    def _check_frontmatter(
        self, content: str, doc_type: str, template: dict
    ) -> Tuple[dict, List[LintIssue], str]:
        issues: List[LintIssue] = []
        fixed = content

        fm_match = self.RULES["frontmatter"].search(content)
        if not fm_match:
            issues.append(LintIssue(
                rule_id="VAL-DOC-002",
                severity=Severity.BLOCKER,
                message="缺少 YAML Front Matter 区块",
                location="文档开头",
                fix_hint=f"添加 ---\ndoc_type: {doc_type}\nc4_binding:\n  level: {template['expected_level']}\n---",
                auto_fixable=True,
                fix_strategy=FixStrategy.AUTO,
            ))
            if self.auto_fix:
                default_fm = self._generate_default_frontmatter(doc_type, template)
                fixed = f"---\n{default_fm}---\n\n{content}"
                fm = yaml.safe_load(default_fm)
            else:
                fm = {}
            return fm, issues, fixed

        try:
            fm = yaml.safe_load(fm_match.group(1))
        except yaml.YAMLError as e:
            issues.append(LintIssue(
                rule_id="VAL-DOC-003",
                severity=Severity.BLOCKER,
                message=f"YAML Front Matter 解析失败: {e}",
                location="文档开头",
                fix_hint="检查 YAML 缩进和语法",
                auto_fixable=False,
                fix_strategy=FixStrategy.MANUAL,
            ))
            return {}, issues, fixed

        # 检查必填字段
        for field in template["required_frontmatter"]:
            if field not in fm:
                sev = Severity.BLOCKER if field == "c4_binding" else Severity.ERROR
                issues.append(LintIssue(
                    rule_id=f"VAL-DOC-{field.upper()}-001",
                    severity=sev,
                    message=f"Front Matter 缺少必填字段: {field}",
                    location="YAML Front Matter",
                    fix_hint=f"添加 {field}: <值>",
                    auto_fixable=True,
                    fix_strategy=FixStrategy.AUTO,
                ))

        return fm or {}, issues, fixed

    # ============================================================
    # c4_binding 校验
    # ============================================================
    def _check_c4_binding(
        self, content: str, doc_type: str, template: dict, frontmatter: dict
    ) -> Tuple[List[LintIssue], str]:
        issues: List[LintIssue] = []
        fixed = content

        binding = frontmatter.get("c4_binding", {})
        if not isinstance(binding, dict):
            issues.append(LintIssue(
                rule_id="VAL-DOC-BIND-001",
                severity=Severity.BLOCKER,
                message="c4_binding 必须是 YAML 对象",
                location="c4_binding",
                fix_hint="改为 c4_binding:\n  level: L1\n  system_id: xxx",
                auto_fixable=True,
                fix_strategy=FixStrategy.AUTO,
            ))
            return issues, fixed

        # 检查 level 一致性
        expected_level = template.get("expected_level")
        actual_level = binding.get("level")
        if actual_level != expected_level:
            issues.append(LintIssue(
                rule_id="VAL-DOC-BIND-002",
                severity=Severity.ERROR,
                message=f"c4_binding.level 应为 {expected_level}，实际为 {actual_level}",
                location="c4_binding.level",
                fix_hint=f"修改为 level: {expected_level}",
                auto_fixable=True,
                fix_strategy=FixStrategy.AUTO,
            ))

        return issues, fixed

    # ============================================================
    # @C4- 标签校验
    # ============================================================
    def _check_c4_tags(
        self, content: str, doc_type: str, template: dict
    ) -> Tuple[List[LintIssue], str]:
        issues: List[LintIssue] = []
        fixed = content

        found_tags: Dict[str, List[Tuple[str, int]]] = {}
        for match in self.RULES["c4_tag"].finditer(content):
            tag_type = match.group(1)
            tag_value = match.group(2)
            found_tags.setdefault(tag_type, []).append((tag_value, match.start()))

        # 检查必填标签
        for required in template["required_c4_tags"]:
            tag_name = required.replace("@C4-", "")
            if tag_name not in found_tags:
                issues.append(LintIssue(
                    rule_id=f"VAL-DOC-TAG-{tag_name}-001",
                    severity=Severity.ERROR,
                    message=f"缺少必填 @C4- 标签: {required}",
                    location="全文",
                    fix_hint=f"添加 {required}:<标识符>",
                    auto_fixable=False,
                    fix_strategy=FixStrategy.MANUAL,
                ))

        # 检查标签格式
        for tag_type, occurrences in found_tags.items():
            for value, pos in occurrences:
                if not re.match(r"^[A-Z][a-zA-Z0-9_-]+$", value):
                    issues.append(LintIssue(
                        rule_id="VAL-DOC-TAG-FMT-001",
                        severity=Severity.WARNING,
                        message=f"@C4-{tag_type} 值 '{value}' 格式不规范",
                        location=f"位置 {pos}",
                        fix_hint="使用 PascalCase 或 snake_case",
                        auto_fixable=True,
                        fix_strategy=FixStrategy.AUTO,
                    ))

        return issues, fixed

    # ============================================================
    # 工具方法
    # ============================================================
    def _generate_default_frontmatter(self, doc_type: str, template: dict) -> str:
        return f"""doc_type: {doc_type}
version: 1.0.0
c4_binding:
  level: {template['expected_level']}
  # TODO: 请补充具体绑定标识
"""

    def _build_report(
        self, file_path: str, doc_type: Optional[str], 
        issues: List[LintIssue], fixed_content: str
    ) -> LintReport:
        blockers = len([i for i in issues if i.severity == Severity.BLOCKER])
        errors = len([i for i in issues if i.severity == Severity.ERROR])
        warnings = len([i for i in issues if i.severity == Severity.WARNING])
        passed = blockers == 0 and errors == 0
        if self.strict_mode:
            passed = passed and warnings == 0

        summary = f"""[{'PASS' if passed else 'FAIL'}] {doc_type or 'UNKNOWN'} - {Path(file_path).name}
  BLOCKER: {blockers} | ERROR: {errors} | WARNING: {warnings}
  {'Ready for downstream' if passed else 'Fix BLOCKER/ERROR items first'}
"""
        return LintReport(
            file_path=file_path,
            doc_type=doc_type,
            passed=passed,
            issues=issues,
            fixed_content=fixed_content if self.auto_fix else None,
            summary=summary,
        )
```

---

### 3.2 DocumentTemplateEngine (DT-01)

**文件**: `backend/app/docforge/template_engine.py`
**依赖**: DocLinter（预处理建议）
**被依赖**: StructuredExtractor

#### 3.2.1 设计目标

- 管理六类文档模板（PRD/DOMAIN_MODEL/ARCH/DETAIL_DESIGN/API_DESIGN/DB_DESIGN）
- 强制校验 c4_binding 区块完整性
- 校验 doc_type 与 c4_binding.level 一致性
- 缺失则阻断，不进入下游

#### 3.2.2 核心实现

```python
# backend/app/docforge/template_engine.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import yaml

class DocType(str, Enum):
    PRD = "PRD"
    DOMAIN_MODEL = "DOMAIN_MODEL"
    ARCH = "ARCH"
    DETAIL_DESIGN = "DETAIL_DESIGN"
    API_DESIGN = "API_DESIGN"
    DB_DESIGN = "DB_DESIGN"

# doc_type -> 期望的 C4 层级
DOC_TYPE_LEVEL_MAP = {
    DocType.PRD: "L1",
    DocType.DOMAIN_MODEL: "L2",
    DocType.ARCH: "L2",
    DocType.DETAIL_DESIGN: "L3",
    DocType.API_DESIGN: "L3",
    DocType.DB_DESIGN: "L2",
}

@dataclass
class ValidationResult:
    passed: bool
    doc_type: Optional[str] = None
    missing_fields: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

class DocumentTemplateEngine:
    """
    文档模板引擎 — 系统的守门组件

    职责:
    1. 管理文档模板定义
    2. 校验文档是否符合模板要求
    3. 校验 c4_binding 完整性
    """

    def __init__(self):
        self._templates: Dict[str, dict] = {}
        self._init_default_templates()

    def _init_default_templates(self):
        """初始化默认模板定义"""
        self._templates = {
            DocType.PRD.value: {
                "required_frontmatter": ["c4_binding", "title", "version"],
                "required_binding_fields": ["system_id", "actors"],
                "required_c4_tags": ["@C4-System", "@C4-Actor"],
            },
            DocType.DOMAIN_MODEL.value: {
                "required_frontmatter": ["c4_binding", "domain", "entities"],
                "required_binding_fields": ["domain_id", "entities"],
                "required_c4_tags": ["@C4-Entity", "@C4-Relationship"],
            },
            DocType.ARCH.value: {
                "required_frontmatter": ["c4_binding", "architecture_style"],
                "required_binding_fields": ["system_id", "containers"],
                "required_c4_tags": ["@C4-Container", "@C4-Technology"],
            },
            DocType.DETAIL_DESIGN.value: {
                "required_frontmatter": ["c4_binding", "module"],
                "required_binding_fields": ["module_id", "components"],
                "required_c4_tags": ["@C4-Component", "@C4-Code-Path"],
            },
            DocType.API_DESIGN.value: {
                "required_frontmatter": ["c4_binding", "base_url"],
                "required_binding_fields": ["module_id", "interfaces"],
                "required_c4_tags": ["@C4-Interface", "@C4-Method"],
            },
            DocType.DB_DESIGN.value: {
                "required_frontmatter": ["c4_binding", "storage"],
                "required_binding_fields": ["storage_id", "tables"],
                "required_c4_tags": ["@C4-Table", "@C4-Column"],
            },
        }

    def validate(self, content: str, doc_type: str) -> ValidationResult:
        """
        校验文档是否符合模板要求

        Returns:
            ValidationResult: 校验结果
        """
        errors = []
        missing_fields = []

        # 1. 检查 doc_type 是否有效
        if doc_type not in self._templates:
            return ValidationResult(
                passed=False,
                errors=[f"未知的文档类型: {doc_type}"],
            )

        template = self._templates[doc_type]

        # 2. 解析 Front Matter
        frontmatter = self._extract_frontmatter(content)
        if frontmatter is None:
            return ValidationResult(
                passed=False,
                doc_type=doc_type,
                errors=["缺少 YAML Front Matter"],
            )

        # 3. 检查必填字段
        for field in template["required_frontmatter"]:
            if field not in frontmatter:
                missing_fields.append(field)
                errors.append(f"缺少必填 Front Matter 字段: {field}")

        # 4. 检查 c4_binding
        c4_binding = frontmatter.get("c4_binding", {})
        if not isinstance(c4_binding, dict):
            errors.append("c4_binding 必须是对象")
        else:
            # 检查 level
            expected_level = DOC_TYPE_LEVEL_MAP.get(DocType(doc_type))
            actual_level = c4_binding.get("level")
            if actual_level != expected_level:
                errors.append(
                    f"c4_binding.level 不匹配: 期望 {expected_level}, 实际 {actual_level}"
                )

            # 检查必填绑定字段
            for field in template["required_binding_fields"]:
                if field not in c4_binding:
                    missing_fields.append(f"c4_binding.{field}")
                    errors.append(f"c4_binding 缺少: {field}")

        return ValidationResult(
            passed=len(errors) == 0,
            doc_type=doc_type,
            missing_fields=missing_fields,
            errors=errors,
        )

    def get_template(self, doc_type: str) -> Optional[dict]:
        """获取模板定义"""
        return self._templates.get(doc_type)

    def register_template(self, doc_type: str, schema: dict):
        """注册新文档类型模板"""
        self._templates[doc_type] = schema

    @staticmethod
    def _extract_frontmatter(content: str) -> Optional[dict]:
        """提取 YAML Front Matter"""
        import re
        match = re.search(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not match:
            return None
        try:
            return yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return None
```

---

### 3.3 FragmentRegistry (FR-01)

**文件**: `backend/app/docforge/fragment_registry.py`
**依赖**: DatabaseAdapter, ArtifactStore
**被依赖**: SketchGenerator, SectionMerger

#### 3.3.1 设计目标

- 文档片段的生命周期管理（CRUD + 状态流转）
- 状态机：DRAFT → REVIEW → APPROVED → DEPRECATED
- 归属模块树管理
- PageSpec 存储（供 SketchGenerator 消费）

#### 3.3.2 核心实现

```python
# backend/app/docforge/fragment_registry.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import json

from app.db.models import Fragment, FragmentState
from app.common.project_context import ProjectContext

@dataclass
class FragmentCreateDTO:
    project_id: str
    title: str
    slug: str
    doc_type: str
    content: str
    module_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class FragmentDTO:
    id: str
    project_id: str
    module_id: Optional[str]
    title: str
    slug: str
    doc_type: str
    state: str
    version_number: int
    content_hash: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class FragmentRegistry:
    """
    片段注册器 — 文档片段生命周期管理

    状态机:
        DRAFT ──→ REVIEW ──→ APPROVED ──→ DEPRECATED
           ↑        │
           └────────┘ (REJECTED)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # CRUD
    # ============================================================
    async def create(self, dto: FragmentCreateDTO) -> FragmentDTO:
        """创建片段"""
        import hashlib
        content_hash = hashlib.sha256(dto.content.encode()).hexdigest()

        fragment = Fragment(
            project_id=dto.project_id,
            module_id=dto.module_id,
            title=dto.title,
            slug=dto.slug,
            doc_type=dto.doc_type,
            content=dto.content,
            content_hash=content_hash,
            state=FragmentState.DRAFT,
            version_number=1,
            metadata=dto.metadata,
        )
        self.db.add(fragment)
        await self.db.flush()
        await self.db.refresh(fragment)
        return self._to_dto(fragment)

    async def get(self, fragment_id: str) -> Optional[FragmentDTO]:
        """获取片段"""
        result = await self.db.execute(
            select(Fragment).where(Fragment.id == fragment_id)
        )
        fragment = result.scalar_one_or_none()
        return self._to_dto(fragment) if fragment else None

    async def list_by_project(
        self, project_id: str, doc_type: Optional[str] = None
    ) -> List[FragmentDTO]:
        """列出项目下所有片段"""
        query = select(Fragment).where(Fragment.project_id == project_id)
        if doc_type:
            query = query.where(Fragment.doc_type == doc_type)
        result = await self.db.execute(query)
        return [self._to_dto(f) for f in result.scalars().all()]

    async def update_content(self, fragment_id: str, new_content: str) -> FragmentDTO:
        """更新内容（仅 DRAFT 状态允许）"""
        import hashlib
        fragment = await self._get_entity(fragment_id)
        if fragment.state != FragmentState.DRAFT:
            raise ValueError(f"Cannot update: state is {fragment.state.value}, expected DRAFT")

        fragment.content = new_content
        fragment.content_hash = hashlib.sha256(new_content.encode()).hexdigest()
        fragment.version_number += 1
        await self.db.flush()
        return self._to_dto(fragment)

    # ============================================================
    # 状态机
    # ============================================================
    async def submit_for_review(self, fragment_id: str) -> FragmentDTO:
        """提交评审: DRAFT → REVIEW"""
        fragment = await self._get_entity(fragment_id)
        if fragment.state != FragmentState.DRAFT:
            raise ValueError(f"Expected DRAFT, got {fragment.state.value}")
        fragment.state = FragmentState.REVIEW
        await self.db.flush()
        return self._to_dto(fragment)

    async def approve(self, fragment_id: str) -> FragmentDTO:
        """批准: REVIEW → APPROVED"""
        fragment = await self._get_entity(fragment_id)
        if fragment.state != FragmentState.REVIEW:
            raise ValueError(f"Expected REVIEW, got {fragment.state.value}")
        fragment.state = FragmentState.APPROVED
        await self.db.flush()
        return self._to_dto(fragment)

    async def reject(self, fragment_id: str) -> FragmentDTO:
        """驳回: REVIEW → DRAFT"""
        fragment = await self._get_entity(fragment_id)
        if fragment.state != FragmentState.REVIEW:
            raise ValueError(f"Expected REVIEW, got {fragment.state.value}")
        fragment.state = FragmentState.DRAFT
        await self.db.flush()
        return self._to_dto(fragment)

    async def deprecate(self, fragment_id: str) -> FragmentDTO:
        """废弃: APPROVED → DEPRECATED"""
        fragment = await self._get_entity(fragment_id)
        fragment.state = FragmentState.DEPRECATED
        await self.db.flush()
        return self._to_dto(fragment)

    # ============================================================
    # PageSpec 查询（供 SketchGenerator 使用）
    # ============================================================
    async def get_pagespecs(self, project_id: str) -> List[Dict[str, Any]]:
        """
        获取所有 PRD 片段中的 PageSpec

        Returns:
            List[dict]: PageSpec 列表，每个包含 page_type, entity_id, fields
        """
        fragments = await self.list_by_project(project_id, doc_type="PRD")
        pagespecs = []
        for frag in fragments:
            if frag.metadata and "pagespecs" in frag.metadata:
                pagespecs.extend(frag.metadata["pagespecs"])
        return pagespecs

    # ============================================================
    # 内部方法
    # ============================================================
    async def _get_entity(self, fragment_id: str) -> Fragment:
        result = await self.db.execute(
            select(Fragment).where(Fragment.id == fragment_id)
        )
        fragment = result.scalar_one_or_none()
        if not fragment:
            raise ValueError(f"Fragment not found: {fragment_id}")
        return fragment

    @staticmethod
    def _to_dto(fragment: Fragment) -> FragmentDTO:
        return FragmentDTO(
            id=fragment.id,
            project_id=fragment.project_id,
            module_id=fragment.module_id,
            title=fragment.title,
            slug=fragment.slug,
            doc_type=fragment.doc_type,
            state=fragment.state.value,
            version_number=fragment.version_number,
            content_hash=fragment.content_hash,
            metadata=fragment.metadata,
            created_at=fragment.created_at,
            updated_at=fragment.updated_at,
        )
```



---

## 四、提取编排层

### 4.1 StructuredExtractor (SE-01)

**文件**: `backend/app/docforge/structured_extractor.py`
**依赖**: DocumentTemplateEngine
**被依赖**: C4Extractor

#### 4.1.1 设计目标

- 确定性规则提取 @C4- 标签（正则匹配）
- confidence 恒为 1.0
- 支持 20 条标准提取规则
- 提取 YAML Front Matter、章节锚点、@C4- 标签
- 纯规则驱动，不依赖 LLM

#### 4.1.2 核心实现

```python
# backend/app/docforge/structured_extractor.py
import re
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

class C4ElementType(str, Enum):
    SYSTEM = "System"
    ACTOR = "Actor"
    EXTERNAL_SYSTEM = "ExternalSystem"
    CONTAINER = "Container"
    COMPONENT = "Component"
    ENTITY = "Entity"
    RELATIONSHIP = "Relationship"
    INTERFACE = "Interface"
    TECHNOLOGY = "Technology"
    CODE_PATH = "CodePath"
    TABLE = "Table"
    COLUMN = "Column"
    METHOD = "Method"

@dataclass
class C4Snippet:
    """提取的 C4 结构化片段"""
    element_type: str           # System, Container, Entity...
    element_id: str             # 标识符
    name: str                   # 显示名称
    description: str = ""       # 描述
    properties: Dict[str, Any] = field(default_factory=dict)  # 额外属性
    source_location: str = ""   # 文档中位置
    confidence: float = 1.0     # 规则提取恒为 1.0

class StructuredExtractor:
    """
    结构化提取器 — 确定性规则提取 C4 元素

    提取规则集（20 条）:
    - YAML Front Matter: c4_binding 区块
    - 章节锚点: ## 标题 {#anchor}
    - @C4-System:ID        → L1 系统
    - @C4-Actor:ID         → L1 参与者
    - @C4-Container:ID     → L2 容器
    - @C4-Component:ID     → L3 组件
    - @C4-Entity:ID        → L2 实体
    - @C4-Relationship:ID  → 实体关系
    - @C4-Interface:ID     → L3 接口
    - @C4-Technology:ID    → 技术栈
    - @C4-Code-Path:ID     → L4 代码路径
    - @C4-Table:ID         → 数据库表
    - @C4-Column:ID        → 表字段
    - @C4-Method:ID        → 接口方法
    - @C4-Attribute:ID     → 实体属性
    - @C4-Page-Type:ID     → 页面类型
    """

    # 正则规则库
    RULES = {
        "frontmatter": re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL),
        "section_anchor": re.compile(r"^(#{1,6})\s+(.+?)\s*\{#([a-zA-Z0-9_-]+)\}\s*$", re.MULTILINE),
        "c4_tag": re.compile(r"@C4-([A-Za-z0-9-]+):([^\s\n,;]+)"),
        "interface_def": re.compile(r"@C4-Interface:(GET|POST|PUT|PATCH|DELETE)\s+(\S+)"),
        "attribute_ref": re.compile(r"@C4-Attribute:([A-Z][a-zA-Z0-9]*)\.([a-z][a-zA-Z0-9_]*)"),
    }

    def extract(self, content: str, doc_type: str) -> List[C4Snippet]:
        """
        从文档中提取 C4 结构化数据

        Args:
            content: 文档全文
            doc_type: PRD/DOMAIN_MODEL/ARCH/DETAIL_DESIGN/API_DESIGN/DB_DESIGN

        Returns:
            List[C4Snippet]: 提取的 C4 片段列表，confidence=1.0
        """
        snippets: List[C4Snippet] = []

        # 1. 提取 Front Matter 中的 c4_binding
        fm_snippets = self._extract_from_frontmatter(content, doc_type)
        snippets.extend(fm_snippets)

        # 2. 提取 @C4- 标签
        tag_snippets = self._extract_c4_tags(content)
        snippets.extend(tag_snippets)

        # 3. 提取接口定义
        interface_snippets = self._extract_interfaces(content)
        snippets.extend(interface_snippets)

        # 4. 提取章节锚点（作为 source_location 参考）
        self._extract_section_anchors(content)

        return snippets

    def _extract_from_frontmatter(self, content: str, doc_type: str) -> List[C4Snippet]:
        """从 Front Matter 提取 c4_binding 信息"""
        snippets = []
        match = self.RULES["frontmatter"].search(content)
        if not match:
            return snippets

        try:
            fm = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return snippets

        if not fm or "c4_binding" not in fm:
            return snippets

        binding = fm["c4_binding"]
        if isinstance(binding, dict):
            # 提取 system_id
            if "system_id" in binding:
                snippets.append(C4Snippet(
                    element_type="binding_reference",
                    element_id=binding["system_id"],
                    name=binding["system_id"],
                    properties=binding,
                    source_location="frontmatter.c4_binding",
                ))

        return snippets

    def _extract_c4_tags(self, content: str) -> List[C4Snippet]:
        """提取 @C4- 标签"""
        snippets = []

        for match in self.RULES["c4_tag"].finditer(content):
            tag_type = match.group(1)
            element_id = match.group(2)

            # 映射到 C4ElementType
            element_type = self._map_tag_type(tag_type)
            if element_type:
                # 查找标签所在章节的描述
                description = self._extract_description(content, match.start())

                snippets.append(C4Snippet(
                    element_type=element_type,
                    element_id=element_id,
                    name=element_id,
                    description=description,
                    source_location=f"@{match.start()}",
                ))

        return snippets

    def _extract_interfaces(self, content: str) -> List[C4Snippet]:
        """提取接口定义 @C4-Interface:METHOD /path"""
        snippets = []

        for match in self.RULES["interface_def"].finditer(content):
            method = match.group(1)
            path = match.group(2)
            element_id = f"{method}_{path.replace('/', '_')}"

            snippets.append(C4Snippet(
                element_type=C4ElementType.INTERFACE.value,
                element_id=element_id,
                name=f"{method} {path}",
                properties={"method": method, "path": path},
                source_location=f"@{match.start()}",
            ))

        return snippets

    def _extract_section_anchors(self, content: str) -> Dict[str, str]:
        """提取章节锚点，作为 source_location 参考"""
        anchors = {}
        for match in self.RULES["section_anchor"].finditer(content):
            level = len(match.group(1))
            title = match.group(2).strip()
            anchor_id = match.group(3)
            anchors[anchor_id] = title
        return anchors

    def _map_tag_type(self, tag_type: str) -> Optional[str]:
        """映射标签类型到 C4 元素类型"""
        mapping = {
            "System": C4ElementType.SYSTEM,
            "Actor": C4ElementType.ACTOR,
            "External-System": C4ElementType.EXTERNAL_SYSTEM,
            "Container": C4ElementType.CONTAINER,
            "Component": C4ElementType.COMPONENT,
            "Entity": C4ElementType.ENTITY,
            "Relationship": C4ElementType.RELATIONSHIP,
            "Interface": C4ElementType.INTERFACE,
            "Technology": C4ElementType.TECHNOLOGY,
            "Code-Path": C4ElementType.CODE_PATH,
            "Table": C4ElementType.TABLE,
            "Column": C4ElementType.COLUMN,
            "Method": C4ElementType.METHOD,
            "Attribute": C4ElementType.ENTITY,
            "Page-Type": "PageType",
        }
        mapped = mapping.get(tag_type)
        return mapped.value if mapped else None

    def _extract_description(self, content: str, position: int, max_chars: int = 200) -> str:
        """提取标签附近章节的描述文本"""
        # 获取标签所在行之后的文本作为描述
        after_tag = content[position:position + max_chars]
        # 取第一行非空文本
        lines = [l.strip() for l in after_tag.split("\n") if l.strip()]
        if len(lines) > 1:
            return lines[1][:200]  # 跳过标签所在行
        return ""

    def register_rule(self, name: str, pattern: re.Pattern):
        """注册新提取规则"""
        self.RULES[name] = pattern

    def get_rules(self) -> Dict[str, re.Pattern]:
        """获取所有规则"""
        return dict(self.RULES)
```

---

### 4.2 C4Extractor (CE-01)

**文件**: `backend/app/docforge/c4_extractor.py`
**依赖**: StructuredExtractor
**被依赖**: C4Assembler

#### 4.2.1 设计目标

- 按文档类型路由提取策略（PRD → L1, ARCH → L2, DETAIL → L3）
- 将 StructuredExtractor 的结果按 doc_type 过滤和增强
- 提取 C4Snippet[] 交给 Assembler

#### 4.2.2 核心实现

```python
# backend/app/docforge/c4_extractor.py
from typing import List, Dict, Optional
from dataclasses import dataclass

from app.docforge.structured_extractor import (
    StructuredExtractor, C4Snippet, C4ElementType
)

@dataclass
class ExtractionContext:
    """提取上下文"""
    doc_type: str
    project_id: str
    fragment_id: Optional[str] = None

class C4Extractor:
    """
    C4 蒸馏器 — 按文档类型路由提取

    路由策略:
    - PRD          → 提取 L1 (System, Actor, ExternalSystem)
    - DOMAIN_MODEL → 提取 L2 (Entity, Relationship, Attribute)
    - ARCH         → 提取 L2 (Container, Technology, Relation)
    - DETAIL_DESIGN→ 提取 L3 (Component, CodePath, Interface, PageType)
    - API_DESIGN   → 提取 L3 (Interface, Method, Request, Response)
    - DB_DESIGN    → 提取 L2 (Table, Column, Index, Constraint)
    """

    # doc_type → 期望提取的 C4 元素类型
    TYPE_FILTER_MAP = {
        "PRD": ["System", "Actor", "ExternalSystem"],
        "DOMAIN_MODEL": ["Entity", "Relationship", "Attribute"],
        "ARCH": ["Container", "Technology", "Component"],
        "DETAIL_DESIGN": ["Component", "CodePath", "Interface", "PageType"],
        "API_DESIGN": ["Interface", "Method"],
        "DB_DESIGN": ["Table", "Column"],
    }

    def __init__(self):
        self.structured_extractor = StructuredExtractor()

    def extract(self, content: str, context: ExtractionContext) -> List[C4Snippet]:
        """
        按文档类型路由提取 C4 结构化数据

        Args:
            content: 文档全文
            context: 提取上下文（含 doc_type, project_id）

        Returns:
            List[C4Snippet]: 按 doc_type 过滤后的 C4 片段
        """
        # 1. 用 StructuredExtractor 提取所有标签
        all_snippets = self.structured_extractor.extract(content, context.doc_type)

        # 2. 按 doc_type 过滤
        allowed_types = self.TYPE_FILTER_MAP.get(context.doc_type, [])
        filtered = [s for s in all_snippets if s.element_type in allowed_types]

        # 3. 补充项目上下文
        for snippet in filtered:
            snippet.properties["_project_id"] = context.project_id
            snippet.properties["_doc_type"] = context.doc_type
            if context.fragment_id:
                snippet.properties["_fragment_id"] = context.fragment_id

        return filtered

    def extract_from_fragment(self, content: str, doc_type: str, project_id: str) -> List[C4Snippet]:
        """便捷方法：从片段内容提取"""
        return self.extract(content, ExtractionContext(
            doc_type=doc_type,
            project_id=project_id,
        ))
```



---

## 五、编译蒸馏层

### 5.1 C4Assembler (CA-01)

**文件**: `backend/app/docforge/c4_assembler.py`
**依赖**: C4Extractor
**被依赖**: C4BaselineStore, BindingRegistry

#### 5.1.1 设计目标

- 将多个 C4Snippet 片段去重、合并、组装为完整的 arsitect.aac.yml
- 同 entity_id 跨文档时合并属性（去重）
- 跨层级引用校验（L3 Component 引用的 Container 必须存在）
- 输出 C4Workspace 内存模型

#### 5.1.2 核心实现

```python
# backend/app/docforge/c4_assembler.py
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

from app.docforge.structured_extractor import C4Snippet

# ============================================================
# C4 DSL 内存模型
# ============================================================
@dataclass
class C4Workspace:
    """C4 工作空间内存模型 — 对应 arsitect.aac.yml 的结构"""
    project_id: str
    version: str = "1.0.0"

    # L1 - System Context
    system: Optional[Dict[str, Any]] = None
    actors: List[Dict[str, Any]] = field(default_factory=list)
    external_systems: List[Dict[str, Any]] = field(default_factory=list)

    # L2 - Containers
    containers: List[Dict[str, Any]] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)

    # L3 - Components
    components: List[Dict[str, Any]] = field(default_factory=list)
    interfaces: List[Dict[str, Any]] = field(default_factory=list)

    # L4 - Code
    code_elements: List[Dict[str, Any]] = field(default_factory=list)

    # 关系
    relationships: List[Dict[str, Any]] = field(default_factory=list)

    # 来源追踪
    source_fragments: List[str] = field(default_factory=list)

class C4Assembler:
    """
    C4 组装器 — 片段 → 完整 DSL

    核心流程:
    1. 接收 C4Snippet[]
    2. 按层级分组（L1/L2/L3/L4）
    3. 同层级内去重合并
    4. 跨层级引用校验
    5. 组装为 C4Workspace
    """

    def __init__(self):
        self._seen_ids: Dict[str, Dict[str, Any]] = {}  # 去重缓存

    def assemble(self, snippets: List[C4Snippet], project_id: str) -> C4Workspace:
        """
        组装 C4 片段为完整工作空间

        Args:
            snippets: 从所有文档提取的 C4Snippet 列表
            project_id: 项目 ID

        Returns:
            C4Workspace: 完整 C4 工作空间
        """
        workspace = C4Workspace(project_id=project_id)

        # 1. 按 element_type 分组
        grouped = self._group_by_type(snippets)

        # 2. 逐类型去重合并
        for element_type, type_snippets in grouped.items():
            merged = self._deduplicate_merge(type_snippets)
            self._add_to_workspace(workspace, element_type, merged)

        # 3. 跨层级引用校验
        self._validate_cross_references(workspace)

        # 4. 收集来源
        workspace.source_fragments = list(set(
            s.properties.get("_fragment_id", "") 
            for s in snippets 
            if "_fragment_id" in s.properties
        ))

        return workspace

    def serialize_to_yaml(self, workspace: C4Workspace) -> str:
        """
        将 C4Workspace 序列化为 YAML DSL

        输出格式（兼容 Structurizr DSL 子集）:
        ```yaml
        workspace:
          name: "项目名"
          version: "1.0.0"
          model:
            system:
              id: "SystemA"
              name: "系统A"
              description: "..."
            actors:
              - id: "User"
                name: "用户"
            containers:
              - id: "WebApp"
                name: "Web App"
                technology: "React"
          views:
            systemContext:
              include: ["*"]
            container:
              include: ["*"]
        ```
        """
        import yaml

        data = {
            "workspace": {
                "project_id": workspace.project_id,
                "version": workspace.version,
                "model": {},
                "views": {},
            }
        }

        model = data["workspace"]["model"]

        # System
        if workspace.system:
            model["system"] = workspace.system

        # Actors
        if workspace.actors:
            model["actors"] = workspace.actors

        # Containers
        if workspace.containers:
            model["containers"] = workspace.containers

        # Components
        if workspace.components:
            model["components"] = workspace.components

        # Entities
        if workspace.entities:
            model["entities"] = workspace.entities

        # Interfaces
        if workspace.interfaces:
            model["interfaces"] = workspace.interfaces

        # Relationships
        if workspace.relationships:
            model["relationships"] = workspace.relationships

        # Views
        data["workspace"]["views"] = self._generate_views(workspace)

        return yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)

    # ============================================================
    # 内部方法
    # ============================================================
    def _group_by_type(self, snippets: List[C4Snippet]) -> Dict[str, List[C4Snippet]]:
        """按 element_type 分组"""
        grouped = defaultdict(list)
        for s in snippets:
            grouped[s.element_type].append(s)
        return dict(grouped)

    def _deduplicate_merge(self, snippets: List[C4Snippet]) -> List[Dict[str, Any]]:
        """同类型去重合并：相同 element_id 合并属性"""
        merged: Dict[str, Dict[str, Any]] = {}

        for snippet in snippets:
            element_id = snippet.element_id

            if element_id not in merged:
                merged[element_id] = {
                    "id": element_id,
                    "name": snippet.name,
                    "description": snippet.description,
                    "properties": dict(snippet.properties),
                }
            else:
                # 合并属性（新值覆盖旧值）
                existing = merged[element_id]
                if snippet.description and not existing["description"]:
                    existing["description"] = snippet.description
                existing["properties"].update(snippet.properties)

        return list(merged.values())

    def _add_to_workspace(self, workspace: C4Workspace, element_type: str, items: List[Dict]):
        """将合并后的元素添加到工作空间对应层级"""
        type_to_field = {
            "System": "system",
            "Actor": "actors",
            "ExternalSystem": "external_systems",
            "Container": "containers",
            "Entity": "entities",
            "Component": "components",
            "Interface": "interfaces",
            "CodePath": "code_elements",
            "Table": "entities",
            "Column": "entities",
            "Relationship": "relationships",
        }

        field = type_to_field.get(element_type)
        if not field:
            return

        if field == "system":
            if items:
                workspace.system = items[0]
        else:
            getattr(workspace, field).extend(items)

    def _validate_cross_references(self, workspace: C4Workspace):
        """跨层级引用校验"""
        # 收集所有有效的容器 ID
        container_ids = {c["id"] for c in workspace.containers}

        # 检查 Component 引用的 Container 是否存在
        for comp in workspace.components:
            container_ref = comp.get("properties", {}).get("container_id")
            if container_ref and container_ref not in container_ids:
                comp["properties"]["_validation_error"] = (
                    f"Container '{container_ref}' not found"
                )

    def _generate_views(self, workspace: C4Workspace) -> Dict[str, Any]:
        """自动生成视图定义"""
        views = {}

        # System Context View (L1)
        if workspace.system or workspace.actors:
            views["systemContext"] = {
                "description": "System Context View",
                "include": ["*"],
            }

        # Container View (L2)
        if workspace.containers:
            views["container"] = {
                "description": "Container View",
                "include": [c["id"] for c in workspace.containers],
            }

        # Component View (L3)
        if workspace.components:
            for container in workspace.containers:
                container_id = container["id"]
                related_components = [
                    c["id"] for c in workspace.components
                    if c.get("properties", {}).get("container_id") == container_id
                ]
                if related_components:
                    views[f"component_{container_id}"] = {
                        "description": f"Component View for {container_id}",
                        "container": container_id,
                        "include": related_components,
                    }

        return views
```



---

## 六、存储校验层

### 6.1 C4BaselineStore (CB-01)

**文件**: `backend/app/c4/baseline_store.py`
**依赖**: DatabaseAdapter, ArtifactStore
**被依赖**: C4DSLManager, C4Renderer, WireframeEngine, SketchGenerator, OpenUIClient

#### 6.1.1 设计目标

- arsitect.aac.yml 的版本化存储
- 支持基线对比与回滚
- 标记当前版本（is_current）
- 支持读取 L2 entities（供 WireframeEngine 消费）

#### 6.1.2 核心实现

```python
# backend/app/c4/baseline_store.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
import hashlib

from app.db.models import C4Baseline, Project
from app.docforge.c4_assembler import C4Workspace

@dataclass
class BaselineDTO:
    id: str
    project_id: str
    version: str
    dsl_content: str
    dsl_hash: str
    level: str
    is_current: bool
    created_at: datetime

class C4BaselineStore:
    """
    C4 版本基线库

    职责:
    1. DSL 版本化存储（写入、读取）
    2. 基线对比（diff）
    3. 版本回滚
    4. 标记当前版本
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # 写入
    # ============================================================
    async def write(
        self, 
        workspace: C4Workspace, 
        dsl_content: str,
        compiled_from: Optional[List[str]] = None
    ) -> str:
        """
        写入新的 C4 基线版本

        Args:
            workspace: C4 工作空间
            dsl_content: YAML DSL 全文
            compiled_from: 来源文档 ID 列表

        Returns:
            str: 新版本号
        """
        # 取消之前的 current 标记
        await self.db.execute(
            update(C4Baseline)
            .where(C4Baseline.project_id == workspace.project_id)
            .values(is_current=False)
        )

        # 计算版本号
        latest = await self._get_latest(workspace.project_id)
        if latest:
            version_parts = latest.version.split(".")
            new_version = f"{version_parts[0]}.{int(version_parts[1]) + 1}.0"
        else:
            new_version = "1.0.0"

        # 计算哈希
        dsl_hash = hashlib.sha256(dsl_content.encode()).hexdigest()

        # 创建记录
        baseline = C4Baseline(
            project_id=workspace.project_id,
            version=new_version,
            dsl_content=dsl_content,
            dsl_hash=dsl_hash,
            level="L1-L4",
            is_current=True,
            compiled_from=compiled_from or [],
        )
        self.db.add(baseline)
        await self.db.flush()

        return new_version

    # ============================================================
    # 读取
    # ============================================================
    async def read_current(self, project_id: str) -> Optional[BaselineDTO]:
        """读取当前版本"""
        result = await self.db.execute(
            select(C4Baseline)
            .where(C4Baseline.project_id == project_id)
            .where(C4Baseline.is_current == True)
        )
        baseline = result.scalar_one_or_none()
        return self._to_dto(baseline) if baseline else None

    async def read_version(self, project_id: str, version: str) -> Optional[BaselineDTO]:
        """读取指定版本"""
        result = await self.db.execute(
            select(C4Baseline)
            .where(C4Baseline.project_id == project_id)
            .where(C4Baseline.version == version)
        )
        baseline = result.scalar_one_or_none()
        return self._to_dto(baseline) if baseline else None

    async def list_versions(self, project_id: str) -> List[BaselineDTO]:
        """列出所有版本"""
        result = await self.db.execute(
            select(C4Baseline)
            .where(C4Baseline.project_id == project_id)
            .order_by(C4Baseline.created_at.desc())
        )
        return [self._to_dto(b) for b in result.scalars().all()]

    # ============================================================
    # Diff
    # ============================================================
    async def diff(
        self, project_id: str, version1: str, version2: str
    ) -> Dict[str, List[str]]:
        """
        对比两个版本的差异

        Returns:
            {"added": [...], "removed": [...], "modified": [...]}
        """
        b1 = await self.read_version(project_id, version1)
        b2 = await self.read_version(project_id, version2)

        if not b1 or not b2:
            return {"error": "Version not found"}

        # 简单行级 diff（可增强为结构化 diff）
        lines1 = set(b1.dsl_content.split("\n"))
        lines2 = set(b2.dsl_content.split("\n"))

        return {
            "added": sorted(list(lines2 - lines1)),
            "removed": sorted(list(lines1 - lines2)),
            "version1": version1,
            "version2": version2,
        }

    # ============================================================
    # 回滚
    # ============================================================
    async def rollback(self, project_id: str, version: str) -> str:
        """
        回滚到指定版本

        策略: 将指定版本标记为 current，之前的 current 取消标记
        """
        # 取消所有 current
        await self.db.execute(
            update(C4Baseline)
            .where(C4Baseline.project_id == project_id)
            .values(is_current=False)
        )

        # 设置目标版本为 current
        result = await self.db.execute(
            update(C4Baseline)
            .where(C4Baseline.project_id == project_id)
            .where(C4Baseline.version == version)
            .values(is_current=True)
        )

        if result.rowcount == 0:
            raise ValueError(f"Version {version} not found")

        return version

    # ============================================================
    # 查询 L2 entities（供 WireframeEngine 使用）
    # ============================================================
    async def get_l2_entities(self, project_id: str) -> List[Dict]:
        """
        获取 L2 层实体（containers + entities）

        Returns:
            List[dict]: 实体列表，每个含 id, name, type
        """
        baseline = await self.read_current(project_id)
        if not baseline:
            return []

        import yaml
        try:
            data = yaml.safe_load(baseline.dsl_content)
            model = data.get("workspace", {}).get("model", {})

            entities = []
            for container in model.get("containers", []):
                entities.append({
                    "id": container["id"],
                    "name": container.get("name", container["id"]),
                    "type": "Container",
                    "technology": container.get("technology", ""),
                })

            for entity in model.get("entities", []):
                entities.append({
                    "id": entity["id"],
                    "name": entity.get("name", entity["id"]),
                    "type": "Entity",
                })

            return entities
        except yaml.YAMLError:
            return []

    # ============================================================
    # 内部方法
    # ============================================================
    async def _get_latest(self, project_id: str) -> Optional[C4Baseline]:
        result = await self.db.execute(
            select(C4Baseline)
            .where(C4Baseline.project_id == project_id)
            .order_by(C4Baseline.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _to_dto(baseline: C4Baseline) -> BaselineDTO:
        return BaselineDTO(
            id=baseline.id,
            project_id=baseline.project_id,
            version=baseline.version,
            dsl_content=baseline.dsl_content,
            dsl_hash=baseline.dsl_hash,
            level=baseline.level,
            is_current=baseline.is_current,
            created_at=baseline.created_at,
        )
```

---

### 6.2 BindingRegistry (BR-01)

**文件**: `backend/app/c4/binding_registry.py`
**依赖**: DatabaseAdapter
**被依赖**: CrossLayerValidator, ImpactAnalyzer

#### 6.2.1 设计目标

- 存储 SDLC 产物 ↔ C4 节点的绑定关系
- 支持双向查询（artifact → C4 node, C4 node → artifact）
- 为架构验证和影响分析提供数据基础

#### 6.2.2 核心实现

```python
# backend/app/c4/binding_registry.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict
from dataclasses import dataclass

from app.db.models import BindingRecord, BindingRelation

@dataclass
class BindingDTO:
    id: str
    artifact_id: str
    artifact_type: str
    c4_node_id: str
    c4_level: str
    relation_type: str
    confidence: float
    source_location: Optional[str]

class BindingRegistry:
    """
    绑定注册表 — SDLC 产物 ↔ C4 节点映射图谱

    职责:
    1. 注册绑定关系
    2. 双向查询
    3. 为 CrossLayerValidator 和 ImpactAnalyzer 提供数据
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # CRUD
    # ============================================================
    async def register(
        self,
        project_id: str,
        artifact_id: str,
        artifact_type: str,
        c4_node_id: str,
        c4_level: str,
        relation_type: str = "binds_to",
        confidence: float = 1.0,
        source_location: Optional[str] = None,
    ) -> str:
        """注册绑定关系"""
        binding = BindingRecord(
            project_id=project_id,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            c4_node_id=c4_node_id,
            c4_level=c4_level,
            relation_type=BindingRelation(relation_type),
            confidence=confidence,
            source_location=source_location,
        )
        self.db.add(binding)
        await self.db.flush()
        return binding.id

    async def query_by_artifact(
        self, project_id: str, artifact_id: str
    ) -> List[BindingDTO]:
        """查询产物的所有绑定"""
        result = await self.db.execute(
            select(BindingRecord)
            .where(BindingRecord.project_id == project_id)
            .where(BindingRecord.artifact_id == artifact_id)
        )
        return [self._to_dto(b) for b in result.scalars().all()]

    async def query_by_c4_node(
        self, project_id: str, c4_node_id: str
    ) -> List[BindingDTO]:
        """查询 C4 节点的所有绑定"""
        result = await self.db.execute(
            select(BindingRecord)
            .where(BindingRecord.project_id == project_id)
            .where(BindingRecord.c4_node_id == c4_node_id)
        )
        return [self._to_dto(b) for b in result.scalars().all()]

    async def list_all(self, project_id: str) -> List[BindingDTO]:
        """列出项目下所有绑定"""
        result = await self.db.execute(
            select(BindingRecord)
            .where(BindingRecord.project_id == project_id)
        )
        return [self._to_dto(b) for b in result.scalars().all()]

    @staticmethod
    def _to_dto(record: BindingRecord) -> BindingDTO:
        return BindingDTO(
            id=record.id,
            artifact_id=record.artifact_id,
            artifact_type=record.artifact_type,
            c4_node_id=record.c4_node_id,
            c4_level=record.c4_level,
            relation_type=record.relation_type.value,
            confidence=record.confidence,
            source_location=record.source_location,
        )
```



---

## 七、消费渲染层

### 7.1 C4DSLManager (DM-01)

**文件**: `backend/app/c4/dsl_manager.py`
**依赖**: C4BaselineStore, ProjectContext
**被依赖**: C4Renderer, WireframeEngine, OpenUIClient

#### 7.1.1 设计目标

- C4 DSL 的读写管理
- 支持手动编辑覆盖（immutable：读取→编辑→写入新版本）
- 版本历史查询
- 提供 C4Workspace 内存模型给下游消费者

#### 7.1.2 核心实现

```python
# backend/app/c4/dsl_manager.py
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from app.c4.baseline_store import C4BaselineStore
from app.docforge.c4_assembler import C4Workspace

@dataclass
class DSLEditDTO:
    content: str
    edit_reason: str
    editor: str

class C4DSLManager:
    def __init__(self, baseline_store: C4BaselineStore):
        self.store = baseline_store

    async def read_current(self, project_id: str) -> Optional[str]:
        baseline = await self.store.read_current(project_id)
        return baseline.dsl_content if baseline else None

    async def read_workspace(self, project_id: str) -> Optional[C4Workspace]:
        content = await self.read_current(project_id)
        if not content:
            return None
        return self._parse_yaml(content, project_id)

    async def edit(self, project_id: str, dto: DSLEditDTO) -> str:
        import yaml
        try:
            parsed = yaml.safe_load(dto.content)
            if not parsed or "workspace" not in parsed:
                raise ValueError("Invalid DSL: missing 'workspace' root key")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")
        workspace = self._yaml_to_workspace(parsed, project_id)
        version = await self.store.write(
            workspace=workspace, dsl_content=dto.content,
            compiled_from=[f"manual_edit:{dto.editor}:{dto.edit_reason}"],
        )
        return version

    async def list_versions(self, project_id: str) -> List[Dict[str, Any]]:
        baselines = await self.store.list_versions(project_id)
        return [{"version": b.version, "is_current": b.is_current,
                 "created_at": b.created_at.isoformat(), "hash": b.dsl_hash[:16]}
                for b in baselines]

    async def rollback(self, project_id: str, version: str) -> str:
        return await self.store.rollback(project_id, version)

    @staticmethod
    def _parse_yaml(content: str, project_id: str) -> C4Workspace:
        import yaml
        data = yaml.safe_load(content)
        ws_data = data.get("workspace", {})
        model = ws_data.get("model", {})
        return C4Workspace(
            project_id=project_id, version=ws_data.get("version", "1.0.0"),
            system=model.get("system"), actors=model.get("actors", []),
            containers=model.get("containers", []), entities=model.get("entities", []),
            components=model.get("components", []), interfaces=model.get("interfaces", []),
            relationships=model.get("relationships", []),
        )

    @staticmethod
    def _yaml_to_workspace(data: dict, project_id: str) -> C4Workspace:
        ws_data = data.get("workspace", {})
        model = ws_data.get("model", {})
        return C4Workspace(
            project_id=project_id, version=ws_data.get("version", "1.0.0"),
            system=model.get("system"), actors=model.get("actors", []),
            external_systems=model.get("externalSystems", []),
            containers=model.get("containers", []), entities=model.get("entities", []),
            components=model.get("components", []), interfaces=model.get("interfaces", []),
            relationships=model.get("relationships", []),
        )
```

---

### 7.2 C4Renderer (CR-01)

**文件**: `backend/app/c4/renderer.py` + `frontend/src/components/C4Renderer.tsx`
**依赖**: C4DSLManager, mermaid.js

#### 7.2.1 后端：DSL → Mermaid 转换

```python
# backend/app/c4/renderer.py
from dataclasses import dataclass
from app.c4.dsl_manager import C4DSLManager
from app.docforge.c4_assembler import C4Workspace

@dataclass
class MermaidOutput:
    mermaid_code: str
    view_level: str
    node_count: int
    edge_count: int

class C4Renderer:
    def __init__(self, dsl_manager: C4DSLManager):
        self.dsl = dsl_manager

    async def render(self, project_id: str, view_level: str = "L2") -> MermaidOutput:
        workspace = await self.dsl.read_workspace(project_id)
        if not workspace:
            return MermaidOutput("graph TD\n  A[No C4 DSL found]", view_level, 0, 0)
        if view_level == "L1":
            return self._render_l1(workspace)
        elif view_level == "L2":
            return self._render_l2(workspace)
        elif view_level == "L3":
            return self._render_l3(workspace)
        return self._render_l2(workspace)

    def _render_l1(self, ws):
        lines = ["graph TB"]
        sid = ws.system["id"] if ws.system else "System"
        sname = ws.system["name"] if ws.system else sid
        lines.append(f'  {sid}["{sname}<br/>System"]')
        for actor in ws.actors:
            aid, aname = actor["id"], actor.get("name", actor["id"])
            lines.append(f'  {aid}(("{aname}<br/>Person"))')
            lines.append(f'  {aid} --> {sid}')
        for ext in ws.external_systems:
            eid, ename = ext["id"], ext.get("name", ext["id"])
            lines.append(f'  {eid}[["{ename}<br/>External System"]]')
            lines.append(f'  {sid} --> {eid}')
        return MermaidOutput("\n".join(lines), "L1",
                           1 + len(ws.actors) + len(ws.external_systems),
                           len(ws.actors) + len(ws.external_systems))

    def _render_l2(self, ws):
        lines = ["graph TB"]
        sid = ws.system["id"] if ws.system else "System"
        sname = ws.system["name"] if ws.system else sid
        lines.append(f"  subgraph {sid} [{sname}]")
        for c in ws.containers:
            cid, cname = c["id"], c.get("name", c["id"])
            tech = c.get("technology", "")
            lines.append(f'    {cid}(["{cname}<br/>[{tech}]"])')
        cids = {c["id"] for c in ws.containers}
        for rel in ws.relationships:
            src, dst = rel.get("source", ""), rel.get("target", "")
            desc = rel.get("description", "")
            if src in cids and dst in cids:
                lines.append(f'    {src} -->|"{desc}"| {dst}')
        lines.append("  end")
        return MermaidOutput("\n".join(lines), "L2", len(ws.containers), len(ws.relationships))

    def _render_l3(self, ws):
        lines = ["graph TB"]
        cmap = {}
        for comp in ws.components:
            cid = comp.get("properties", {}).get("container_id", "default")
            cmap.setdefault(cid, []).append(comp)
        for cid, comps in cmap.items():
            lines.append(f'  subgraph {cid} [Container: {cid}]')
            for comp in comps:
                comp_id = comp["id"]
                lines.append(f'    {comp_id}["{comp.get("name", comp_id)}"]')
            lines.append("  end")
        return MermaidOutput("\n".join(lines), "L3", len(ws.components), 0)
```

#### 7.2.2 前端：React + Mermaid.js

```tsx
// frontend/src/components/C4Renderer.tsx
import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

interface RenderResponse {
  mermaid_code: string;
  view_level: string;
  node_count: number;
  edge_count: number;
}

interface Props { projectId: string; initialLevel?: "L1" | "L2" | "L3" | "L4"; }

export function C4Renderer({ projectId, initialLevel = "L2" }: Props) {
  const [level, setLevel] = useState(initialLevel);
  const [data, setData] = useState<RenderResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false, theme: "default", securityLevel: "loose",
      flowchart: { useMaxWidth: true, htmlLabels: true, curve: "basis" },
    });
  }, []);

  useEffect(() => {
    const render = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/v1/c4/render?project_id=${projectId}&level=${level}`);
        const d = await res.json();
        setData(d);
        if (containerRef.current) {
          containerRef.current.innerHTML = `<div class="mermaid">${d.mermaid_code}</div>`;
          await mermaid.run({ nodes: containerRef.current.querySelectorAll(".mermaid") });
        }
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    render();
  }, [projectId, level]);

  return (
    <div className="c4-renderer">
      <div className="toolbar">
        {(["L1","L2","L3","L4"] as const).map(l => (
          <button key={l} className={level===l?"active":""} onClick={()=>setLevel(l)}>
            {l === "L1" ? "System" : l === "L2" ? "Container" : l === "L3" ? "Component" : "Code"}
          </button>
        ))}
        <span className="stats">{data && `${data.node_count} nodes, ${data.edge_count} edges`}</span>
      </div>
      <div ref={containerRef} className="mermaid-container">
        {loading && <div>Rendering...</div>}
      </div>
    </div>
  );
}
```

---

### 7.3 WireframeEngine (WE-01)

**文件**: `backend/app/c4/wireframe_engine.py`
**依赖**: C4BaselineStore

#### 7.3.1 核心实现

```python
# backend/app/c4/wireframe_engine.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from app.c4.baseline_store import C4BaselineStore

@dataclass
class WireframePage:
    page_id: str; title: str; page_type: str; entity_id: str
    x: float = 0; y: float = 0; width: float = 240; height: float = 180
    elements: List[Dict] = field(default_factory=list)

@dataclass
class NavigationEdge:
    source: str; target: str; label: str = ""; strength: float = 1.0

@dataclass
class WireframeResult:
    pages: List[WireframePage]; edges: List[NavigationEdge]
    orphan_pages: List[str]; svg_content: str

PAGE_TYPE_RULES = [
    (lambda e: "count" in str(e).lower() or "total" in str(e).lower(), "dashboard", 0.8),
    (lambda e: "AggregateRoot" in str(e), "list", 0.9),
    (lambda e: "id" in str(e).lower() and "name" in str(e).lower(), "detail", 0.7),
    (lambda e: "POST" in str(e) or "create" in str(e).lower(), "form", 0.8),
    (lambda e: "search" in str(e).lower(), "search", 0.9),
]

class WireframeEngine:
    CANVAS_WIDTH = 1200; CANVAS_HEIGHT = 800
    PAGE_WIDTH = 240; PAGE_HEIGHT = 180

    def __init__(self, baseline_store: C4BaselineStore):
        self.store = baseline_store

    async def generate(self, project_id: str, module_id: Optional[str] = None) -> WireframeResult:
        entities = await self.store.get_l2_entities(project_id)
        if not entities:
            return WireframeResult([], [], [], "")
        pages = self._domain_mapper(entities)
        self._layout_planner(pages)
        edges = self._navigation_linker(pages)
        svg = self._render_svg(pages, edges)
        connected = set()
        for e in edges: connected.add(e.source); connected.add(e.target)
        orphans = [p.page_id for p in pages if p.page_id not in connected]
        return WireframeResult(pages, edges, orphans, svg)

    def _domain_mapper(self, entities: List[Dict]) -> List[WireframePage]:
        pages = []
        for entity in entities:
            eid = entity["id"]; ename = entity.get("name", eid)
            page_type, _ = self._infer_page_type(entity)
            elements = self._generate_elements(page_type, entity)
            pages.append(WireframePage(page_id=f"page_{eid}", title=f"{ename}",
                                       page_type=page_type, entity_id=eid, elements=elements))
        return pages

    def _infer_page_type(self, entity: Dict) -> Tuple[str, float]:
        entity_str = str(entity)
        for condition, page_type, confidence in PAGE_TYPE_RULES:
            if condition(entity_str): return page_type, confidence
        return "list", 0.5

    def _generate_elements(self, page_type: str, entity: Dict) -> List[Dict]:
        name = entity.get("name", "")
        if page_type == "list":
            return [{"type": "header", "text": name, "x": 10, "y": 10},
                    {"type": "search_bar", "placeholder": "Search...", "x": 10, "y": 40},
                    {"type": "table", "x": 10, "y": 70, "rows": 5},
                    {"type": "button", "text": "+ New", "x": 180, "y": 10}]
        elif page_type == "detail":
            return [{"type": "header", "text": name, "x": 10, "y": 10},
                    {"type": "field_group", "x": 10, "y": 40, "fields": ["Name", "Status", "Created"]},
                    {"type": "button", "text": "Edit", "x": 10, "y": 150}]
        elif page_type == "form":
            return [{"type": "header", "text": f"New {name}", "x": 10, "y": 10},
                    {"type": "input", "label": "Name", "x": 10, "y": 40},
                    {"type": "textarea", "label": "Description", "x": 10, "y": 80},
                    {"type": "button", "text": "Submit", "x": 10, "y": 150}]
        elif page_type == "dashboard":
            return [{"type": "header", "text": f"{name} Dashboard", "x": 10, "y": 10},
                    {"type": "chart_placeholder", "x": 10, "y": 40, "w": 100, "h": 60},
                    {"type": "stat_card", "x": 120, "y": 40, "label": "Total", "value": "--"}]
        return [{"type": "header", "text": name, "x": 10, "y": 10}]

    def _layout_planner(self, pages: List[WireframePage]):
        cols = max(1, self.CANVAS_WIDTH // (self.PAGE_WIDTH + 40))
        for i, page in enumerate(pages):
            row, col = i // cols, i % cols
            page.x = 20 + col * (self.PAGE_WIDTH + 40)
            page.y = 20 + row * (self.PAGE_HEIGHT + 60)
            page.width, page.height = self.PAGE_WIDTH, self.PAGE_HEIGHT

    def _navigation_linker(self, pages: List[WireframePage]) -> List[NavigationEdge]:
        edges = []
        list_pages = {p.entity_id: p for p in pages if p.page_type == "list"}
        detail_pages = {p.entity_id: p for p in pages if p.page_type == "detail"}
        form_pages = {p.entity_id: p for p in pages if p.page_type == "form"}
        for eid, lp in list_pages.items():
            if eid in detail_pages:
                edges.append(NavigationEdge(lp.page_id, detail_pages[eid].page_id, "view", 1.0))
            if eid in form_pages:
                edges.append(NavigationEdge(lp.page_id, form_pages[eid].page_id, "create", 0.8))
        return edges

    def _render_svg(self, pages, edges) -> str:
        c = self.CANVAS_WIDTH; h = self.CANVAS_HEIGHT
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{c}" height="{h}" viewBox="0 0 {c} {h}">',
                 '<rect width="100%" height="100%" fill="#f5f5f5"/>']
        for page in pages: parts.extend(self._render_page_svg(page))
        for edge in edges:
            src = next((p for p in pages if p.page_id == edge.source), None)
            dst = next((p for p in pages if p.page_id == edge.target), None)
            if src and dst:
                parts.append(f'<line x1="{src.x+src.width/2}" y1="{src.y+src.height}" '
                           f'x2="{dst.x+dst.width/2}" y2="{dst.y}" stroke="#666" stroke-width="2" '
                           f'marker-end="url(#arrowhead)"/>')
        parts.append('<defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">'
                     '<polygon points="0 0, 10 3.5, 0 7" fill="#666"/></marker></defs>')
        parts.append("</svg>")
        return "\n".join(parts)

    def _render_page_svg(self, page: WireframePage) -> List[str]:
        parts = []
        x, y, w, h = page.x, page.y, page.width, page.height
        C = {"bg": "white", "border": "#333", "header": "#e3f2fd", "accent": "#1976d2",
             "types": {"list": "#e8f5e9", "detail": "#fff3e0", "form": "#fce4ec",
                       "dashboard": "#f3e5f5", "search": "#e8eaf6"}}
        type_color = C["types"].get(page.page_type, "#f5f5f5")
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{C["bg"]}" stroke="{C["border"]}" stroke-width="2" rx="4"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="24" fill="{C["header"]}" stroke="{C["border"]}" stroke-width="1" rx="4"/>')
        parts.append(f'<text x="{x+8}" y="{y+17}" font-size="12" font-weight="bold" fill="#1565c0">{page.title}</text>')
        parts.append(f'<rect x="{x+1}" y="{y+24}" width="{w-2}" height="{h-25}" fill="{type_color}"/>')
        for elem in page.elements:
            ex, ey = x + elem.get("x", 10), y + 30 + elem.get("y", 0)
            if elem["type"] == "search_bar":
                parts.append(f'<rect x="{ex}" y="{ey}" width="200" height="20" fill="white" stroke="#999" rx="2"/>')
            elif elem["type"] == "table":
                for row in range(elem.get("rows", 3)):
                    parts.append(f'<rect x="{ex}" y="{ey+row*20}" width="200" height="18" fill="white" stroke="#ddd"/>')
            elif elem["type"] == "button":
                parts.append(f'<rect x="{ex}" y="{ey}" width="60" height="22" fill="{C["accent"]}" rx="2"/>')
                parts.append(f'<text x="{ex+12}" y="{ey+15}" font-size="10" fill="white">{elem["text"]}</text>')
            elif elem["type"] == "input":
                parts.append(f'<text x="{ex}" y="{ey}" font-size="9" fill="#666">{elem.get("label", "")}</text>')
                parts.append(f'<rect x="{ex}" y="{ey+2}" width="200" height="18" fill="white" stroke="#999" rx="2"/>')
        return parts
```

---

### 7.4 SketchGenerator (SG-01)

**文件**: `backend/app/c4/sketch_generator.py`
**依赖**: FragmentRegistry

#### 7.4.1 核心实现

```python
# backend/app/c4/sketch_generator.py
from dataclasses import dataclass
from typing import List, Dict
from app.docforge.fragment_registry import FragmentRegistry

@dataclass
class PageSpec:
    page_id: str; page_type: str; entity_id: str
    title: str; fields: List[Dict]; actions: List[str]

class SketchGenerator:
    COLORS = {"bg": "#e8e8e8", "page_bg": "#ffffff", "border": "#999999",
              "header_bg": "#d0d0d0", "element_bg": "#f0f0f0",
              "text": "#333333", "label": "#666666", "accent": "#4a90d9"}

    def __init__(self, fragment_registry: FragmentRegistry):
        self.fragments = fragment_registry

    async def generate(self, project_id: str) -> str:
        pagespecs = await self.fragments.get_pagespecs(project_id)
        if not pagespecs: return self._empty_page()
        pages = [self._parse_pagespec(p) for p in pagespecs]
        return self._render_html(pages)

    def _parse_pagespec(self, data: Dict) -> PageSpec:
        return PageSpec(page_id=data.get("page_id", "unknown"),
                        page_type=data.get("page_type", "list"),
                        entity_id=data.get("entity_id", ""),
                        title=data.get("title", "Untitled"),
                        fields=data.get("fields", []),
                        actions=data.get("actions", []))

    def _render_html(self, pages: List[PageSpec]) -> str:
        c = self.COLORS; n = len(pages)
        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Wireframe Sketch - {n} pages</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:{c["bg"]};padding:20px}}
.sketch-page{{background:{c["page_bg"]};border:2px solid {c["border"]};margin-bottom:20px;max-width:900px}}
.sketch-header{{background:{c["header_bg"]};padding:12px 16px;border-bottom:2px solid {c["border"]};
display:flex;justify-content:space-between;align-items:center}}
.sketch-header h2{{font-size:16px;color:{c["text"]}}}
.type-badge{{background:{c["accent"]};color:white;font-size:11px;padding:2px 8px;border-radius:10px}}
.sketch-body{{padding:16px}}
.sketch-element{{background:{c["element_bg"]};border:1px dashed {c["border"]};padding:8px 12px;
margin-bottom:8px;color:{c["label"]};font-size:13px}}
.sketch-table{{width:100%;border-collapse:collapse;margin-top:8px}}
.sketch-table th,.sketch-table td{{border:1px solid {c["border"]};padding:6px 8px;
font-size:12px;color:{c["text"]}}}
.sketch-table th{{background:{c["header_bg"]};font-weight:600}}
.sketch-btn{{display:inline-block;background:{c["accent"]};color:white;padding:6px 16px;
font-size:12px;border:none;margin-right:8px;margin-top:8px}}
.sketch-input{{width:100%;padding:6px;border:1px solid {c["border"]};background:white;
margin-top:4px;font-size:12px;color:{c["label"]}}}
.field-label{{font-size:11px;color:{c["label"]};margin-top:8px}}
.page-nav{{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}}
.page-nav a{{padding:6px 12px;background:white;border:1px solid {c["border"]};
text-decoration:none;color:{c["text"]};font-size:12px}}
.page-nav a:hover{{background:{c["accent"]};color:white}}
</style></head><body>
<h1 style="font-size:18px;margin-bottom:16px;color:{c["text"]}">
Wireframe Sketch <span style="font-size:13px;font-weight:normal;color:{c["label"]}">({n} pages)</span></h1>
<div class="page-nav">"""
        for page in pages:
            html += f'<a href="#{page.page_id}">{page.title}</a>\n'
        html += "</div>\n"
        for page in pages: html += self._render_page(page)
        html += "</body></html>"
        return html

    def _render_page(self, page: PageSpec) -> str:
        c = self.COLORS
        html = f"""<div class="sketch-page" id="{page.page_id}">
<div class="sketch-header"><h2>{page.title}</h2><span class="type-badge">{page.page_type.upper()}</span></div>
<div class="sketch-body">"""
        render_fn = {"list": self._render_list, "detail": self._render_detail,
                     "form": self._render_form, "dashboard": self._render_dashboard,
                     "search": self._render_search}.get(page.page_type, self._render_list)
        html += render_fn(page)
        for action in page.actions:
            html += f'<button class="sketch-btn">{action}</button>\n'
        html += "</div></div>\n"
        return html

    def _render_list(self, page: PageSpec) -> str:
        fields = page.fields or [{"name": "ID"}, {"name": "Name"}, {"name": "Status"}]
        html = '<div class="sketch-element">[Search Bar]  Search...</div>\n'
        html += '<table class="sketch-table"><tr>\n'
        for f in fields[:5]: html += f'<th>{f.get("name", "")}</th>\n'
        html += '<th>Actions</th></tr>\n'
        for _ in range(3):
            html += '<tr>\n'
            for _ in fields[:5]: html += '<td style="color:#aaa">---</td>\n'
            html += '<td><span style="color:#4a90d9">[View] [Edit]</span></td></tr>\n'
        html += '</table>\n<div class="sketch-element" style="margin-top:8px">[Pagination]  &lt; 1 2 3 &gt;</div>\n'
        return html

    def _render_detail(self, page: PageSpec) -> str:
        fields = page.fields or [{"name": "Name"}, {"name": "Description"}, {"name": "Status"}]
        html = ""
        for f in fields:
            html += f'<div class="field-label">{f.get("name", "")}</div>\n'
            html += f'<div class="sketch-element">{{{f.get("name", "value")}}}</div>\n'
        return html

    def _render_form(self, page: PageSpec) -> str:
        fields = page.fields or [{"name": "Name"}, {"name": "Description"}]
        html = ""
        for f in fields:
            html += f'<div class="field-label">{f.get("name", "")} *</div>\n'
            html += f'<input class="sketch-input" value="Enter {f.get("name", "")}...">\n'
        html += '<div style="margin-top:12px"><button class="sketch-btn">Submit</button>\n'
        html += '<button class="sketch-btn" style="background:#999">Cancel</button></div>\n'
        return html

    def _render_dashboard(self, page: PageSpec) -> str:
        html = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px">\n'
        for label in ["Total Users", "Active", "Revenue"]:
            html += f"""<div class="sketch-element" style="text-align:center">
<div style="font-size:11px;color:#666">{label}</div>
<div style="font-size:24px;font-weight:bold;color:#333;margin-top:4px">---</div></div>\n"""
        html += '</div>\n'
        html += '<div class="sketch-element" style="height:150px;display:flex;align-items:center;justify-content:center">[Chart Placeholder]</div>\n'
        return html

    def _render_search(self, page: PageSpec) -> str:
        html = '<div style="display:flex;gap:8px;margin-bottom:12px">\n'
        html += '<input class="sketch-input" value="Search keywords..." style="flex:1">\n'
        html += '<button class="sketch-btn">Search</button>\n'
        html += '<button class="sketch-btn" style="background:#666">Advanced</button></div>\n'
        html += '<div class="sketch-element">[Filter Panel] Status | Date | Category</div>\n'
        html += '<div class="sketch-element" style="margin-top:8px">[Results List]  10 results found</div>\n'
        return html

    def _empty_page(self) -> str:
        return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>No Data</title></head>
<body style="font-family:sans-serif;padding:40px;color:#666">
<h2>No PageSpec found</h2><p>Add PageSpec to your PRD document metadata to generate sketch.</p>
<pre style="background:#f5f5f5;padding:16px">metadata:
  pagespecs:
    - page_id: user_list
      page_type: list
      title: User List
      fields:
        - { name: ID }
        - { name: Name }
        - { name: Email }</pre>
</body></html>"""
```

---

### 7.5 ArtifactRenderer (AR-01)

**文件**: `frontend/src/components/ArtifactRenderer.tsx`

```tsx
import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import mermaid from "mermaid";

interface Artifact { path: string; content: string;
  format: "md" | "mmd" | "yaml" | "json" | "svg" | "html" | "txt"; }

interface Props { artifact: Artifact; }

export function ArtifactRenderer({ artifact }: Props) {
  const { format, content } = artifact;
  switch (format) {
    case "md": return <MarkdownView content={content} />;
    case "mmd": return <MermaidView content={content} />;
    case "yaml": case "json": return <CodeView content={content} lang={format} />;
    case "svg": return <div dangerouslySetInnerHTML={{ __html: content }} style={{ maxWidth: "100%", overflow: "auto" }} />;
    case "html": return <HTMLView content={content} />;
    default: return <CodeView content={content} lang="text" />;
  }
}

function MarkdownView({ content }: { content: string }) {
  return (<div className="artifact-md"><ReactMarkdown remarkPlugins={[remarkGfm]}
    components={{ code({ node, inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || "");
      return !inline && match ? (
        <SyntaxHighlighter style={vscDarkPlus} language={match[1]} PreTag="div" {...props}>
          {String(children).replace(/\n$/, "")}</SyntaxHighlighter>
      ) : (<code className={className} {...props}>{children}</code>);
    }}}>{content}</ReactMarkdown></div>);
}

function MermaidView({ content }: { content: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (ref.current) {
      ref.current.innerHTML = `<div class="mermaid">${content}</div>`;
      mermaid.run({ nodes: ref.current.querySelectorAll(".mermaid") });
    }
  }, [content]);
  return <div ref={ref} />;
}

function CodeView({ content, lang }: { content: string; lang: string }) {
  return (<SyntaxHighlighter style={vscDarkPlus} language={lang} PreTag="div" showLineNumbers>
    {content}</SyntaxHighlighter>);
}

function HTMLView({ content }: { content: string }) {
  const ref = useRef<HTMLIFrameElement>(null);
  useEffect(() => {
    const doc = ref.current?.contentDocument;
    if (doc) { doc.open(); doc.write(content); doc.close(); }
  }, [content]);
  return <iframe ref={ref} style={{ width: "100%", height: "600px", border: "1px solid #ddd" }}
           sandbox="allow-scripts" title="preview" />;
}
```



---

## 八、数据模型总览

### 8.1 核心模型关系图

```
+--------------+       +------------------+       +------------------+
|   Project    |<1---N>|   C4Baseline     |       |    Fragment      |
|--------------|       |------------------|       |------------------|
| id (PK)      |       | id (PK)          |       | id (PK)          |
| name         |       | project_id (FK)  |       | project_id (FK)  |
| state        |       | version          |       | module_id        |
| complexity   |       | dsl_content      |       | title            |
| base_dir     |       | dsl_hash         |       | slug             |
+--------------+       | is_current       |       | doc_type         |
                       +------------------+       | content          |
                                                  | content_hash     |
                                                  | state            |
                                                  | metadata         |
                                                  +------------------+

+--------------+       +------------------+       +------------------+
| BindingRecord|       |  EventBus (内存)  |       | C4Workspace(内存)|
|--------------|       |------------------|       |------------------|
| id (PK)      |       | DomainEvent      |       | project_id       |
| project_id   |       | - event_type     |       | system           |
| artifact_id  |       | - aggregate_id   |       | actors[]         |
| artifact_type|       | - payload        |       | containers[]     |
| c4_node_id   |       | - timestamp      |       | components[]     |
| c4_level     |       +------------------+       | entities[]       |
| relation_type|                                  | relationships[]  |
+--------------+                                  +------------------+
```

### 8.2 arsitect.aac.yml 格式定义

```yaml
workspace:
  project_id: "uuid"
  version: "1.0.0"

  model:
    # L1 - System Context
    system:
      id: "FinancingPlatform"
      name: "融资平台"
      description: "企业融资业务处理平台"

    actors:
      - id: "Borrower"
        name: "借款企业"
        description: "申请融资的企业用户"
      - id: "Investor"
        name: "投资方"
        description: "提供资金的投资机构"

    externalSystems:
      - id: "CreditBureau"
        name: "征信系统"
        description: "央行征信查询接口"

    # L2 - Containers
    containers:
      - id: "WebApp"
        name: "Web 应用"
        technology: "React + TypeScript"
        description: "用户前端界面"
      - id: "APIService"
        name: "API 服务"
        technology: "FastAPI + Python"
        description: "业务逻辑处理"
      - id: "Database"
        name: "数据库"
        technology: "PostgreSQL"
        description: "数据持久化"

    # L2 - Entities (领域模型)
    entities:
      - id: "LoanApplication"
        name: "融资申请"
        attributes:
          - id
          - amount
          - term_months
          - status
      - id: "Investor"
        name: "投资人"
        attributes:
          - id
          - name
          - risk_preference

    # L3 - Components
    components:
      - id: "ApplicationController"
        name: "申请控制器"
        container_id: "APIService"
        technology: "Python"
      - id: "RiskEvaluator"
        name: "风险评估器"
        container_id: "APIService"
        technology: "Python"

    # L4 - Interfaces
    interfaces:
      - id: "POST_applications"
        method: "POST"
        path: "/api/applications"
        container_id: "APIService"

    # Relationships
    relationships:
      - source: "Borrower"
        target: "WebApp"
        description: "通过浏览器访问"
      - source: "WebApp"
        target: "APIService"
        description: "REST API 调用"
      - source: "APIService"
        target: "Database"
        description: "SQL 查询"

  views:
    systemContext:
      description: "系统上下文视图"
      include: ["*"]

    container:
      description: "容器视图"
      include: ["WebApp", "APIService", "Database"]

    component_APIService:
      description: "API 服务组件视图"
      container: "APIService"
      include: ["ApplicationController", "RiskEvaluator"]
```

---

## 九、API 接口总览

### 9.1 路由定义

```python
# backend/app/api/v1/c4.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.c4.dsl_manager import C4DSLManager, DSLEditDTO
from app.c4.renderer import C4Renderer
from app.c4.wireframe_engine import WireframeEngine
from app.c4.sketch_generator import SketchGenerator
from app.c4.baseline_store import C4BaselineStore
from app.docforge.fragment_registry import FragmentRegistry

router = APIRouter(prefix="/c4", tags=["C4 Architecture"])

# 依赖注入
async def get_baseline_store(db: AsyncSession = Depends(get_db)):
    return C4BaselineStore(db)

async def get_dsl_manager(store = Depends(get_baseline_store)):
    return C4DSLManager(store)

async def get_renderer(dsl = Depends(get_dsl_manager)):
    return C4Renderer(dsl)

async def get_wireframe_engine(store = Depends(get_baseline_store)):
    return WireframeEngine(store)

async def get_sketch_generator(db: AsyncSession = Depends(get_db)):
    return SketchGenerator(FragmentRegistry(db))

# ============================================================
# C4 DSL 管理
# ============================================================
@router.get("/dsl/current")
async def get_current_dsl(
    project_id: str,
    dsl: C4DSLManager = Depends(get_dsl_manager),
):
    """获取当前 DSL"""
    content = await dsl.read_current(project_id)
    if not content:
        raise HTTPException(404, "No C4 DSL found for this project")
    return {"content": content, "format": "yaml"}

@router.post("/dsl/edit")
async def edit_dsl(
    project_id: str,
    dto: DSLEditDTO,
    dsl: C4DSLManager = Depends(get_dsl_manager),
):
    """编辑 DSL（创建新版本）"""
    version = await dsl.edit(project_id, dto)
    return {"version": version, "message": "DSL updated successfully"}

@router.get("/dsl/versions")
async def list_dsl_versions(
    project_id: str,
    dsl: C4DSLManager = Depends(get_dsl_manager),
):
    """列出所有版本"""
    versions = await dsl.list_versions(project_id)
    return {"versions": versions}

@router.post("/dsl/rollback")
async def rollback_dsl(
    project_id: str,
    version: str,
    dsl: C4DSLManager = Depends(get_dsl_manager),
):
    """回滚到指定版本"""
    result = await dsl.rollback(project_id, version)
    return {"version": result}

# ============================================================
# C4 架构图渲染
# ============================================================
@router.get("/render")
async def render_c4(
    project_id: str,
    level: str = "L2",  # L1/L2/L3/L4
    renderer: C4Renderer = Depends(get_renderer),
):
    """渲染 C4 架构图为 Mermaid"""
    result = await renderer.render(project_id, level)
    return {
        "mermaid_code": result.mermaid_code,
        "view_level": result.view_level,
        "node_count": result.node_count,
        "edge_count": result.edge_count,
    }

# ============================================================
# 线框图
# ============================================================
@router.get("/wireframe")
async def generate_wireframe(
    project_id: str,
    engine: WireframeEngine = Depends(get_wireframe_engine),
):
    """生成线框图 SVG"""
    result = await engine.generate(project_id)
    return {
        "svg": result.svg_content,
        "page_count": len(result.pages),
        "edge_count": len(result.edges),
        "orphan_pages": result.orphan_pages,
        "pages": [{"id": p.page_id, "title": p.title, "type": p.page_type} for p in result.pages],
    }

# ============================================================
# 草图
# ============================================================
@router.get("/sketch")
async def generate_sketch(
    project_id: str,
    generator: SketchGenerator = Depends(get_sketch_generator),
):
    """生成草图 HTML"""
    html = await generator.generate(project_id)
    return {"html": html, "format": "html"}
```

### 9.2 API 端点汇总

| 方法 | 路径 | 说明 | 请求参数 |
|------|------|------|----------|
| GET | `/api/v1/c4/dsl/current` | 获取当前 DSL | `project_id` |
| POST | `/api/v1/c4/dsl/edit` | 编辑 DSL | `project_id` + body |
| GET | `/api/v1/c4/dsl/versions` | 列出版本 | `project_id` |
| POST | `/api/v1/c4/dsl/rollback` | 回滚版本 | `project_id` + `version` |
| GET | `/api/v1/c4/render` | 渲染架构图 | `project_id` + `level` |
| GET | `/api/v1/c4/wireframe` | 生成线框图 | `project_id` |
| GET | `/api/v1/c4/sketch` | 生成草图 | `project_id` |

---

## 十、测试策略

### 10.1 测试金字塔

```
        /\
       /  \     E2E 测试 (2)
      /____\    - 完整文档→DSL→渲染链路
     /      \
    / 集成  \   集成测试 (6)
   /________\  - DocLinter + TemplateEngine
  /          \ - C4Extractor + Assembler + BaselineStore
 /   单元    \  单元测试 (14)
/____________\ - 每个组件独立测试
```

### 10.2 单元测试

```python
# tests/test_doc_linter.py
import pytest
from app.docforge.doc_linter import DocLinter, Severity

class TestDocLinter:
    def test_detect_doc_type_by_filename(self):
        linter = DocLinter()
        assert linter._detect_doc_type("", "prd.md") == "PRD"
        assert linter._detect_doc_type("", "architecture.md") == "ARCH"
        assert linter._detect_doc_type("", "api_design.md") == "API_DESIGN"

    def test_detect_doc_type_by_content(self):
        linter = DocLinter()
        content = "容器定义\n技术栈：Spring Boot"
        assert linter._detect_doc_type(content, "unknown.md") == "ARCH"

    def test_missing_frontmatter(self):
        linter = DocLinter(auto_fix=False)
        report = linter.lint("# Title\n\nNo frontmatter here.", "test.md")
        assert not report.passed
        assert any(i.rule_id == "VAL-DOC-002" for i in report.issues)

    def test_missing_c4_binding(self):
        linter = DocLinter(auto_fix=False)
        content = "---\ndoc_type: PRD\ntitle: Test\n---\n\n# Content"
        report = linter.lint(content, "test.md")
        assert not report.passed
        assert any(i.rule_id == "VAL-DOC-C4_BINDING-001" for i in report.issues)

    def test_valid_prd(self):
        linter = DocLinter(auto_fix=False)
        content = """---
doc_type: PRD
title: Test PRD
version: 1.0.0
c4_binding:
  level: L1
  system_id: TestSystem
  actors: [User]
---

# Background

@C4-System:TestSystem is the main system.

@C4-Actor:User interacts with the system.
"""
        report = linter.lint(content, "test_prd.md")
        assert report.passed, f"Issues: {report.issues}"

    def test_auto_fix(self):
        linter = DocLinter(auto_fix=True)
        content = "# Title without frontmatter"
        fixed, report = linter.fix(content, "test.md")
        assert "---" in fixed  # 添加了 Front Matter
        assert "c4_binding" in fixed
```

```python
# tests/test_structured_extractor.py
import pytest
from app.docforge.structured_extractor import StructuredExtractor

class TestStructuredExtractor:
    def test_extract_c4_tags(self):
        extractor = StructuredExtractor()
        content = """
# System Design

@C4-System:FinancingPlatform is our main product.

@C4-Container:WebApp serves the frontend.
@C4-Container:APIService handles business logic.

@C4-Actor:Borrower applies for loans.
"""
        snippets = extractor.extract(content, "ARCH")

        system_snippets = [s for s in snippets if s.element_type == "System"]
        assert len(system_snippets) == 1
        assert system_snippets[0].element_id == "FinancingPlatform"

        container_snippets = [s for s in snippets if s.element_type == "Container"]
        assert len(container_snippets) == 2

    def test_extract_interfaces(self):
        extractor = StructuredExtractor()
        content = """
@C4-Interface:POST /api/applications
@C4-Interface:GET /api/applications/{id}
"""
        snippets = extractor.extract(content, "API_DESIGN")
        interface_snippets = [s for s in snippets if s.element_type == "Interface"]
        assert len(interface_snippets) == 2

    def test_confidence_always_one(self):
        extractor = StructuredExtractor()
        content = "@C4-System:Test"
        snippets = extractor.extract(content, "PRD")
        for s in snippets:
            assert s.confidence == 1.0
```

```python
# tests/test_c4_assembler.py
import pytest
from app.docforge.c4_assembler import C4Assembler
from app.docforge.structured_extractor import C4Snippet

class TestC4Assembler:
    def test_deduplicate_merge(self):
        assembler = C4Assembler()
        snippets = [
            C4Snippet("Container", "WebApp", "Web App", "Frontend app", confidence=1.0),
            C4Snippet("Container", "WebApp", "Web App", "React frontend", confidence=1.0),
            C4Snippet("Container", "API", "API Service", "Backend", confidence=1.0),
        ]
        workspace = assembler.assemble(snippets, "test-project")
        assert len(workspace.containers) == 2  # WebApp 去重 + API

        webapp = next(c for c in workspace.containers if c["id"] == "WebApp")
        assert "Frontend app" in webapp["description"] or "React frontend" in webapp["description"]

    def test_serialize_to_yaml(self):
        assembler = C4Assembler()
        snippets = [
            C4Snippet("System", "Platform", "Platform", "Main platform", confidence=1.0),
            C4Snippet("Container", "Web", "Web App", "Frontend", confidence=1.0),
        ]
        workspace = assembler.assemble(snippets, "test")
        yaml_str = assembler.serialize_to_yaml(workspace)
        assert "workspace:" in yaml_str
        assert "Platform" in yaml_str
        assert "Web App" in yaml_str
```

```python
# tests/test_wireframe_engine.py
import pytest
from app.c4.wireframe_engine import WireframeEngine

class TestWireframeEngine:
    def test_infer_page_type_list(self):
        engine = WireframeEngine(None)
        page_type, conf = engine._infer_page_type({"id": "User", "type": "AggregateRoot"})
        assert page_type == "list"
        assert conf == 0.9

    def test_infer_page_type_dashboard(self):
        engine = WireframeEngine(None)
        page_type, conf = engine._infer_page_type({"id": "Report", "count": 100})
        assert page_type == "dashboard"
        assert conf == 0.8

    def test_infer_page_type_default(self):
        engine = WireframeEngine(None)
        page_type, conf = engine._infer_page_type({"id": "Something"})
        assert page_type == "list"  # 默认
```

### 10.3 集成测试

```python
# tests/integration/test_document_to_dsl.py
import pytest
from app.docforge.doc_linter import DocLinter
from app.docforge.template_engine import DocumentTemplateEngine
from app.docforge.structured_extractor import StructuredExtractor
from app.docforge.c4_extractor import C4Extractor, ExtractionContext
from app.docforge.c4_assembler import C4Assembler

class TestDocumentToDSLPipeline:
    """测试完整文档 → DSL 管道"""

    def test_prd_to_dsl(self):
        # 1. 准备 PRD 文档
        prd_content = """---
doc_type: PRD
title: 融资平台需求
version: 1.0.0
c4_binding:
  level: L1
  system_id: FinancingPlatform
  actors: [Borrower, Investor]
---

# 背景

融资平台连接借款企业和投资方。

# 角色

@C4-Actor:Borrower 是借款企业，通过平台申请融资。

@C4-Actor:Investor 是投资方，通过平台提供资金。

# 系统

@C4-System:FinancingPlatform 是核心融资撮合系统。

@C4-External-System:CreditBureau 提供征信查询服务。
"""

        # 2. DocLinter 诊断
        linter = DocLinter()
        fixed, report = linter.fix(prd_content, "prd.md")
        assert report.passed, f"Lint failed: {report.issues}"

        # 3. TemplateEngine 校验
        engine = DocumentTemplateEngine()
        validation = engine.validate(fixed, "PRD")
        assert validation.passed

        # 4. StructuredExtractor 提取
        extractor = StructuredExtractor()
        snippets = extractor.extract(fixed, "PRD")
        assert len(snippets) > 0

        # 5. C4Extractor 路由
        c4_extractor = C4Extractor()
        c4_snippets = c4_extractor.extract(fixed, ExtractionContext("PRD", "test-project"))
        assert len(c4_snippets) > 0

        # 6. C4Assembler 组装
        assembler = C4Assembler()
        workspace = assembler.assemble(c4_snippets, "test-project")

        # 7. 验证结果
        assert workspace.system is not None
        assert workspace.system["id"] == "FinancingPlatform"
        assert len(workspace.actors) == 2
        assert any(a["id"] == "Borrower" for a in workspace.actors)
        assert any(a["id"] == "Investor" for a in workspace.actors)

        # 8. 序列化
        yaml_output = assembler.serialize_to_yaml(workspace)
        assert "FinancingPlatform" in yaml_output
        assert "Borrower" in yaml_output
```

---

## 附录 A：验收标准

### A.1 功能验收（19 项）

| # | 组件 | 验收项 | 验证方法 |
|---|------|--------|----------|
| 1 | DatabaseAdapter | SQLite 异步连接正常 | `pytest tests/test_database.py` |
| 2 | EventBus | 事件发布/订阅正常工作 | 单元测试通过 |
| 3 | ProjectContext | with 语句管理上下文正确 | 单元测试通过 |
| 4 | ArtifactStore | 文件读写 + 哈希计算正确 | 单元测试通过 |
| 5 | ConfigManager | 环境变量读取正确 | 启动验证 |
| 6 | DocLinter | 能识别 6 类文档类型 | `test_detect_doc_type_*` |
| 7 | DocLinter | 能检测 BLOCKER 级问题 | `test_missing_c4_binding` |
| 8 | DocLinter | 能自动修复 Front Matter | `test_auto_fix` |
| 9 | DocumentTemplateEngine | 校验通过/失败正确 | `test_validate_*` |
| 10 | FragmentRegistry | CRUD + 状态机正常 | 单元测试通过 |
| 11 | StructuredExtractor | @C4- 标签提取 confidence=1.0 | `test_confidence_always_one` |
| 12 | C4Extractor | 按 doc_type 路由正确 | 集成测试通过 |
| 13 | C4Assembler | 去重合并正确 | `test_deduplicate_merge` |
| 14 | C4BaselineStore | 写入/读取/版本列表正常 | 单元测试通过 |
| 15 | C4DSLManager | 编辑创建新版本 | 集成测试通过 |
| 16 | C4Renderer | L1/L2/L3 Mermaid 输出正确 | 可视化验证 |
| 17 | WireframeEngine | SVG 包含页面和跳转边 | 可视化验证 |
| 18 | SketchGenerator | HTML 草图可浏览器打开 | 可视化验证 |
| 19 | ArtifactRenderer | 6 种格式渲染正常 | 前端手动验证 |

### A.2 端到端验收（4 项）

```
[ ] E2E-01: 上传 PRD → DocLinter 通过 → TemplateEngine 通过
             → StructuredExtractor 提取 → C4Assembler 组装
             → C4BaselineStore 写入 → C4DSLManager 读取
             → C4Renderer 渲染 Mermaid 图

[ ] E2E-02: 上传多份文档（PRD + ARCH + DETAIL）
             → 各自提取 C4 片段
             → Assembler 合并为完整 DSL
             → L1/L2/L3 架构图均可渲染

[ ] E2E-03: C4 DSL → WireframeEngine 生成 SVG
             → 包含所有页面节点
             → 包含页面跳转关系
             → orphan_pages 列表正确

[ ] E2E-04: Fragment 含 PageSpec → SketchGenerator 生成 HTML
             → 浏览器可正常打开
             → 页面导航可用
             → 页面布局合理
```

### A.3 性能验收

| 指标 | 目标 | 测试方法 |
|------|------|----------|
| DocLinter 处理 | < 100ms / 文档 | 100 次取平均 |
| StructuredExtractor 提取 | < 50ms / 文档 | 100 次取平均 |
| C4Assembler 组装 | < 100ms / 100 个 snippet | 100 次取平均 |
| C4Renderer Mermaid 生成 | < 50ms | 100 次取平均 |
| WireframeEngine SVG 生成 | < 200ms / 20 个页面 | 100 次取平均 |
| SketchGenerator HTML 生成 | < 100ms / 10 个页面 | 100 次取平均 |

### A.4 质量要求

- 单元测试覆盖率 ≥ 80%
- 集成测试覆盖所有核心管道
- 无 BLOCKER/ERROR 级静态分析警告
- 前端组件 TypeScript 类型完整
- API 文档（FastAPI auto-docs）可访问

---

> **文档结束**
>
> 批次：Batch-01（C4 DSL 基线 + 架构图渲染 + 草图生成）
> 组件数：19 个
> 预计周期：6 周
> 版本：v1.0

