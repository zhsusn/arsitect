---
name: e2e-testing
description: 当用户提到'E2E测试'、'端到端测试'、'Playwright'、'黄金流程'、'UI自动化'、'视觉回归'或需要为Web应用构建端到端测试流水线时触发。基于Playwright设计、生成并执行端到端测试，覆盖核心用户流程、服务生命周期、网络Mock与视觉回归。
---

# E2E Testing（端到端测试）

## 适用场景

- 需要为 Web 应用构建端到端测试流水线
- 用户提到"E2E 测试"、"端到端测试"、"UI 自动化"、"Playwright"
- 需要定义并验证"黄金流程"（登录 → 核心业务操作 → 断言）
- 需要拦截慢/不稳定依赖（AI 生成、第三方 OAuth、支付）进行网络 Mock
- 需要视觉回归测试防止 UI 漂移
- 需要把端到端测试接入 CI / 发布前检查清单
- 调试 flaky 失败：捕获 trace、截图、控制台日志定位问题

## 前置依赖

| 依赖项 | 路径/说明 | 门控标准 |
|--------|-----------|----------|
| 功能规格 | `feature-*/spec.md` 或 `docs/requirements.md` | 已明确 P0 用户故事与验收标准 |
| 接口契约 | `interface-contracts/openapi.yaml`（后端） | 已定义关键 API 路径、字段、状态码 |
| 单元/集成测试 | `tests/unit/report.md`、`tests/integration/report.md` | 建议单元测试 ≥ 70%，集成测试 P0 通过 |
| 可运行应用 | 前端 + 后端本地或预览环境 | 至少能本地启动 |
| 测试框架 | Playwright for Python / JS / .NET | 已安装或允许本 Skill 指导安装 |

**硬性阻断**：如果连可运行的本地/预览环境都没有，拒绝生成测试代码，先输出环境搭建清单。

## 策略预设（Policy）

根据项目成熟度选择策略，默认 `default`：

| 维度 | `default`（默认） | `strict`（高可信/合规） |
|------|-------------------|-------------------------|
| 黄金流程数 | 3–5 个 P0 流程 | 所有 P0 + 关键异常流程 |
| 视觉回归 | 关键页面 | 所有 P0 页面 + 组件 |
| 网络 Mock | 允许 Mock 慢/不稳定依赖 | 必须验证真实 Provider 契约（Pact） |
| 测试数据 | session 级种子 + teardown | 用例级隔离 + 环境验证 |
| CI 触发 | push/PR 到 main | 每次 commit + 每日定时 |

策略通过 `openspec/config.yaml` 中的 `e2e-testing.policy` 配置，未配置时使用 `default`。

## 执行流程

### Phase 0: 范围与策略确认（Gate In）

1. 读取 `openspec/config.yaml` 中的 `e2e-testing.policy`（默认 `default`）。
2. 确认技术栈：前端框架/端口、后端框架/端口、数据库/外部依赖。
3. 确认目标环境：本地 dev server / Docker Compose / 预览环境 / staging。
4. 若缺少必要信息，向用户提问并冻结范围，禁止假设性执行。

### Phase 1: 输入分析

1. 读取 `feature-*/spec.md`，提取 P0 用户故事（FR-XXX）与验收标准。
2. 读取 `interface-contracts/openapi.yaml`，标记 E2E 会用到的关键端点。
3. 识别慢/不稳定/付费依赖（AI 生成、OAuth、支付、短信、邮件），作为 Mock 候选。
4. 输出临时推理文件 `E2E_SCOPE.md`（仅用于推理，不提交）：
   - P0 用户故事列表
   - 关键端点 / 页面 URL
   - 需要 Mock 的依赖
   - 视觉回归目标页面
   - 反范围（明确不做）

### Phase 2: 条目整理（Gate Mid）

将 P0 用户故事拆分为可验证的原子任务清单 `tasks/e2e-tasks.md`：

| ID | 任务 | 覆盖需求 | 依赖 | 状态 |
|----|------|----------|------|------|
| E2E-01 | 搭建前后端服务生命周期 fixture | — | 环境可启动 | pending |
| E2E-02 | 实现 LoginPage POM | FR-001 | E2E-01 | pending |
| ... | ... | ... | ... | ... |

每个任务必须包含：输入切片、预期输出、验证方式、数据清理策略。

### Phase 3: 原子执行

按以下顺序生成/执行制品：

#### 3.1 目录结构

```text
tests/e2e/
├── conftest.py              # 共享 fixture：服务生命周期、baseURL、trace/截图钩子
├── pages/                   # Page Object Model
│   ├── __init__.py
│   └── {page}_page.py
├── flows/                   # 黄金流程（业务场景级）
│   ├── __init__.py
│   └── test_golden_{flow}.py
├── utils/
│   ├── __init__.py
│   ├── api_mock.py          # 网络拦截 / Mock 工具
│   └── visual_helpers.py    # 截图辅助函数
└── snapshots/baseline/      # 视觉回归 baseline
```

#### 3.2 服务生命周期 fixture（`conftest.py`）

使用 `with_server.py` 模式管理前后端：

```python
@pytest.fixture(scope="session")
def backend_server():
    proc = subprocess.Popen([...], cwd="../backend")
    wait_for_health("http://localhost:8000/health", timeout=30)
    yield proc
    proc.terminate(); proc.wait()
```

- 禁止 `time.sleep()` 裸等，使用健康检查轮询。
- 失败时打印 stdout/stderr 片段，方便诊断。

#### 3.3 Page Object Model

每个页面封装定位器与业务动作，禁止在 test 中直接写 CSS 选择器：

```python
class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username_input = page.get_by_role("textbox", name="用户名")
        self.password_input = page.get_by_role("textbox", name="密码")
        self.login_button = page.get_by_role("button", name="登录")

    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
```

- 优先使用 `get_by_role` / `get_by_text` / `get_by_placeholder`（ARIA / 用户可见文本）。
- 仅当 spec 明确指定 `data-testid` 时才允许使用。

#### 3.4 黄金流程（Flows）

每个 flow 对应一个 P0 用户故事，只测"用户可见行为"，不测算法细节：

```python
def test_golden_login_and_create_project(page):
    login = LoginPage(page)
    login.login("test@example.com", "password123")
    login.expect_login_success()

    project = ProjectPage(page)
    project.create_project("E2E 测试项目")
    project.expect_project_created()
```

- 每个 test 独立准备/清理数据，禁止依赖执行顺序。
- 涉及 AI 生成、第三方回调等慢依赖时，先用 `utils/api_mock.py` 绕过。

#### 3.5 网络拦截与 Mock

```python
def mock_ai_design_fast(route: Route):
    route.fulfill(status=200, json={"status": "success", "design_id": "mock-001"})

# test 中使用
page.route("**/api/v1/designs/generate", mock_ai_design_fast)
```

- Mock 仅用于隔离慢/不稳定/付费依赖，不得 Mock 被测系统本身。
- 在 strict 模式下，关键接口需额外补充 Pact Provider 验证。

#### 3.6 视觉回归

```python
expect(page).to_have_screenshot("project-dashboard.png", full_page=True)
```

- baseline 存于 `tests/e2e/snapshots/baseline/`。
- CI 中设置 `PLAYWRIGHT_UPDATE_SNAPSHOTS=1` 仅在 conscious update 时刷新。
- 首次运行生成 baseline，后续 diff 存于 `test-results/`。

#### 3.7 失败证据收集

```python
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            page.screenshot(path=f"test-results/{item.name}-failed.png")
```

- 失败时自动收集：截图、trace、视频、控制台 error 日志。

#### 3.8 运行测试

```bash
# 安装
pip install pytest-playwright
playwright install chromium

# 全部黄金流程
pytest tests/e2e/flows/ -v

# 单个流程有界面慢动作调试
pytest tests/e2e/flows/test_golden_login.py --headed --slowmo 500 -v

# 更新 baseline
PLAYWRIGHT_UPDATE_SNAPSHOTS=1 pytest tests/e2e/flows/ -v
```

### Phase 4: 覆盖验证（Gate Out）

执行完成后必须回答：

1. **条目回溯**：阶段 2 的 `tasks/e2e-tasks.md` 是否全部完成？未完成的标注原因。
2. **需求覆盖**：每个 FR-XXX 是否至少有一个 E2E-XXXX 测试覆盖？
3. **幻觉检测**：测试中是否引入了 spec/openapi.yaml 未规定的类名、URL、DOM 选择器？
4. **反模式扫描**：
   - 是否存在 `time.sleep()`？
   - 是否存在测试数据依赖执行顺序？
   - 是否存在过度 Mock（mock 了被测对象本身）？
   - 是否存在永远通过的断言？
5. **视觉回归审计**：diff 是否经过人工确认？未确认差异标记为 `[待验证]`。

未通过 Gate Out 的测试禁止合并。

### Phase 5: 总结归档

生成 `tests/e2e/report.md`：

- 测试通过率
- P0 用户故事覆盖矩阵（FR ↔ E2E-XXXX ↔ 状态）
- Mock 清单与 rationale
- 视觉回归差异清单
- Flaky 风险点与修复建议
- CI 接入命令

并更新集中式追溯矩阵 `tests/TRACEABILITY.csv`。

## 输出物清单

| 文件 | 路径 | 说明 |
|------|------|------|
| E2E 范围说明 | `tests/e2e/E2E_SCOPE.md` | 仅推理用，可保留为设计记录 |
| 任务清单 | `tasks/e2e-tasks.md` | 原子任务与状态 |
| 测试代码 | `tests/e2e/**` | conftest / POM / flows / utils |
| 视觉回归 baseline | `tests/e2e/snapshots/baseline/` | 截图基线 |
| E2E 报告 | `tests/e2e/report.md` | 通过率、覆盖矩阵、风险 |
| 追溯矩阵 | `tests/TRACEABILITY.csv` | 合并 unit / integration / e2e |

## 与上下游衔接

| 衔接点 | 动作 |
|--------|------|
| 上游: requirement-analysis | 消费用户故事与验收标准，明确 P0 范围 |
| 上游: detailed-requirements | 消费 `feature-*/spec.md` 中的验收标准 |
| 上游: integration-test | 建议在 integration-test P0 通过后启动 E2E，避免底层契约问题拖慢 UI 测试 |
| 上游: executing-plans | 消费实现代码与 `openapi.yaml` 契约 |
| 下游: uat-verification | E2E P0 通过后生成 `user-stories-checklist.md` 供人工 UAT |
| 下游: release-management | E2E 报告作为发布风险评估输入 |
| 横向: self-check | 执行 E2E 反模式扫描与覆盖验证 |
| 横向: systematic-debugging | E2E 失败时调用进行系统化调试 |

## Gotchas

- **没有可运行环境绝不动手**：如果连本地 dev server 都起不来，先生成环境搭建清单，而不是写一堆无法运行的测试。
- **启动脚本不是 Skill 自带**：`conftest.py` 中的服务生命周期 fixture 根据项目实际启动方式生成，优先复用现有脚本，没有时才临时写 subprocess。
- **禁止复制不可运行的启动模板**：生成的 fixture 必须反映真实的前后端启动命令、端口和工作目录。
- **E2E 只测用户可见行为**：AI 生成结果的内容正确性、复杂算法、边界情况留给单元/集成测试。
- **禁止 `time.sleep()`**：统一使用 Playwright auto-waiting（`expect().to_be_visible()`）。
- **每个 test 独立**：禁止依赖执行顺序，每个 test 自己创建/清理测试数据。
- **禁止过度 Mock**：Mock 只用于隔离外部慢/不稳定依赖，不得 Mock 被测系统本身。
- **DOM 选择器策略**：优先 ARIA role / 可见文本；`data-testid` 必须 spec 明确指定。
- **视觉回归是双刃剑**：首次 baseline 必须人工确认，CI 中禁止无条件自动更新。
- **strict 模式需 Pact**：若配置为 strict，关键接口必须有 Provider 契约验证，不能只靠 UI 断言。
- **失败必须留证据**：截图、trace、视频、控制台日志至少留一种，否则无法诊断 flaky。
- **需求没写的名称不能写死**：`openapi.yaml` / `spec.md` 未明确引用的类名、内部 URL、DOM 选择器均视为实现自由域。
- **未通过 Gate Out 禁止合并**：条目回溯、需求覆盖、幻觉检测、反模式扫描有一项不通过，就不得进入下游 UAT。
