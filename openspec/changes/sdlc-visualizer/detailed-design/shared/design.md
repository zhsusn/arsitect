# shared/design.md — 公共设计组件与规范

> **说明**：本文件定义跨模块复用的设计组件、抽象接口和编码规范。模块级设计中对这些组件的引用通过本文件实现。

---

## 1. 分页 DTO

### 1.1 PageRequestDTO

所有分页查询的请求参数基类。

```typescript
interface PageRequestDTO {
  page: number;                 -- 页码，默认 1，最小 1
  page_size: number;            -- 每页条数，默认 50，最小 1，最大 200
  sort_by?: string;             -- 排序字段
  sort_order?: "asc" | "desc";  -- 排序方向，默认 desc
}
```

**校验规则**：
- `page` < 1 时自动修正为 1
- `page_size` < 1 时自动修正为 1，> 200 时自动修正为 200
- `sort_by` 字段不在白名单中时忽略排序参数

### 1.2 PageResponseDTO

所有分页查询的响应结构基类。

```typescript
interface PageResponseDTO<T> {
  data: T[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}
```

---

## 2. 全局异常处理基类

### 2.1 异常类层次

```
ArsitectException (基类)
├── ValidationException        -- 400 请求参数校验失败
├── UnauthorizedException      -- 401 未认证
├── ForbiddenException         -- 403 权限不足
├── NotFoundException          -- 404 资源不存在
├── ConflictException          -- 409 资源冲突
├── UnprocessableException     -- 422 业务逻辑错误
├── RateLimitException         -- 429 请求频率限制
└── InternalException          -- 500 服务器内部错误
```

### 2.2 基类定义（Python 后端）

```python
class ArsitectException(Exception):
    """Arsitect 平台异常基类。

    Attributes:
        error_code: 机器可读错误码。
        message: 人类可读错误描述。
        status_code: HTTP 状态码。
        details: 额外上下文信息。
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_response(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "request_id": get_request_id(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
```

### 2.3 全局异常处理器（FastAPI）

```python
@app.exception_handler(ArsitectException)
async def arsitect_exception_handler(
    request: Request, exc: ArsitectException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response(),
    )
```

---

## 3. 文件系统适配器接口

### 3.1 抽象接口

```python
class FileSystemAdapter(ABC):
    """文件系统适配器抽象基类。

    屏蔽本地文件系统与远程存储（如 S3、OSS）的差异，为产物管理、基线快照、
    报告导出等提供统一的文件操作接口。
    """

    @abstractmethod
    async def read(self, path: str) -> bytes:
        """读取文件内容。"""

    @abstractmethod
    async def write(self, path: str, content: bytes) -> str:
        """写入文件，返回文件 URI。"""

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """检查文件是否存在。"""

    @abstractmethod
    async def delete(self, path: str) -> None:
        """删除文件。"""

    @abstractmethod
    async def list_dir(self, path: str) -> list[str]:
        """列出目录下文件列表。"""
```

### 3.2 本地文件系统实现（MVP）

```python
class LocalFileSystemAdapter(FileSystemAdapter):
    """本地文件系统适配器（MVP 默认实现）。"""

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path

    async def read(self, path: str) -> bytes:
        full_path = self.base_path / path
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def write(self, path: str, content: bytes) -> str:
        full_path = self.base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)
        return str(full_path)
    # ... 其他方法实现
```

---

## 4. Zustand Store 模式规范

### 4.1 Store 命名规范

| 模块 | Store 名称 | 状态范围 |
|------|-----------|----------|
| DR-001 | `ProjectStore` | 项目列表、当前项目、筛选条件 |
| DR-003 | `StageStore` | 阶段详情、审查状态、Tab 状态 |
| DR-004 | `GateStore` | Gate 列表、当前 Gate、决策操作 |
| DR-005 | `ArtifactStore` | 产物树、当前文件、编辑会话 |
| DR-012 | `ArchValidationStore` | 检测会话、差异列表、筛选条件 |
| DR-013 | `HistoryStore` | 活跃标签、筛选条件、视图数据 |
| DR-014 | `MonitoringStore` | 项目选择、刷新配置、看板数据 |

### 4.2 Store 结构模板

```typescript
interface ModuleStore {
  // === 数据状态 ===
  data: DataType | null;
  dataLoading: boolean;
  dataError: string | null;

  // === 筛选/查询状态 ===
  filters: FilterType;
  sort: SortType;

  // === UI 状态 ===
  activeTab: string;
  selectedItemId: string | null;
  drawerOpen: boolean;

  // === 操作 ===
  fetchData: (params?: QueryParams) => Promise<void>;
  setFilters: (filters: Partial<FilterType>) => void;
  reset: () => void;
}
```

### 4.3 Store 拆分原则

- **按模块拆分**：每个业务模块独立一个 Zustand Store，禁止跨模块直接访问其他 Store。
- **跨模块通信**：通过 React Props 传递或自定义事件总线（如 `mitt`），禁止 Store 间直接导入。
- **持久化策略**：用户偏好（如刷新周期、视图模式）使用 `zustand/persist` 持久化到 `localStorage`。

---

## 5. 前端公共组件规范

### 5.1 侧滑面板（Drawer）规范

所有侧滑面板统一遵循以下规范：

| 属性 | 默认值 | 说明 |
|------|--------|------|
| 宽度范围 | 480px ~ 900px | 最小 480px，最大 900px，支持拖拽调整 |
| 动画时长 | 300ms | ease-out 缓动函数 |
| 遮罩层 | `rgba(0,0,0,0.4)` | 点击遮罩层关闭面板 |
| 关闭方式 | Esc / 遮罩点击 / 关闭按钮 | 三种关闭方式同时支持 |
| 宽度持久化 | localStorage | 用户调整后的宽度保存至本地 |

**使用模块**：DR-003（Stage 详情）、DR-012（差异详情）、DR-013（项目历史详情）

### 5.2 弹窗（Modal）规范

| 属性 | 默认值 | 说明 |
|------|--------|------|
| 宽度 | 480px / 640px / 800px | 小/中/大三种规格 |
| 遮罩层透明度 | 50% | 背景不可交互 |
| 动画 | 底部滑入 200ms | 遮罩层淡入 150ms |
| 关闭方式 | Esc / 遮罩点击 / 关闭按钮 / 取消按钮 | 确认操作弹窗禁止遮罩点击关闭 |

### 5.3 骨架屏（Skeleton）规范

- 列表加载：使用行状骨架屏，行高与实际列表行高一致
- 卡片加载：使用矩形骨架屏，圆角与实际卡片一致
- 图表加载：使用简化版图表轮廓骨架屏
- 最大加载时间：超过 1 秒未加载成功时，骨架屏替换为错误占位

---

## 6. 编码规范

### 6.1 Python（后端）

- 遵循 `python-google-style` Skill 规范
- 行宽 100 字符
- 类型注解必须（mypy strict 模式）
- Google Style docstring

### 6.2 TypeScript / React（前端）

- 函数组件优先，Hooks 管理状态
- 类型命名：PascalCase，接口前缀 `I` 可选
- 组件 Props 必须定义 TypeScript 接口
- 状态管理使用 Zustand，避免过度使用 Context

---

## 7. 版本控制

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2026-06-02 | 初始版本，提取自第一批~第五批详细设计 |
