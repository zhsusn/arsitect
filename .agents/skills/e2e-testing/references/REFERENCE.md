# E2E Testing 技术参考

> 本文件按需加载，供 SKILL.md 执行时引用。包含 Playwright 端到端测试的详细模式、示例与配置。

---

## 1. 推荐技术栈

| 场景 | 推荐工具 | 说明 |
|------|----------|------|
| Web UI 自动化 | Playwright (Python/JS/.NET) | 自动等待、trace、网络拦截、视觉回归 |
| 服务生命周期 | 复用项目脚本 或 `subprocess.Popen` + 健康轮询 | 参考 Anthropic `with_server.py` |
| 容器化依赖 | Testcontainers / Docker Compose | 数据库、缓存、消息队列 |
| HTTP 外部服务 Mock | WireMock / MockServer | 请求匹配、延迟、故障模拟 |
| 契约验证 | Pact | Provider 端运行时验证 |
| 视觉回归 | Playwright `to_have_screenshot` | baseline 管理、CI 友好 |

---

## 2. Page Object Model 完整示例

```python
# pages/login_page.py
from playwright.sync_api import Page, expect

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username_input = page.get_by_role("textbox", name="用户名")
        self.password_input = page.get_by_role("textbox", name="密码")
        self.login_button = page.get_by_role("button", name="登录")
        self.error_message = page.get_by_role("alert")

    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def expect_login_success(self):
        expect(self.page).to_have_url("http://localhost:5173/projects")

    def expect_error(self, message: str):
        expect(self.error_message).to_contain_text(message)
```

---

## 3. 服务生命周期策略

**e2e-testing Skill 不自带启动脚本**。服务启动逻辑属于生成的 `tests/e2e/conftest.py` 的一部分，Skill 会根据项目现状选择以下策略之一：

### 3.1 优先复用项目现有脚本

| 项目已有资源 | fixture 写法示例 |
|--------------|------------------|
| `docker-compose.yml` | `subprocess.run(["docker", "compose", "up", "-d", "--wait"])` |
| `start-dev.sh` | `subprocess.Popen(["./start-dev.sh"], cwd="../backend")` |
| `package.json` dev script | `subprocess.Popen(["npm", "run", "dev"], cwd="../frontend")` |
| Makefile | `subprocess.run(["make", "dev"])` |

### 3.2 复用已有 fixture

如果项目已有 `tests/conftest.py` 或 `backend/tests/conftest.py` 中定义了服务启动 fixture，直接在 `tests/e2e/conftest.py` 中 import 或继承：

```python
from backend.tests.conftest import backend_server
```

### 3.3 临时生成 subprocess

无现成方式时使用 `subprocess.Popen` + 健康轮询：

```python
# conftest.py
import subprocess
import time
import urllib.request
import pytest
from playwright.sync_api import Page

def wait_for_health(url: str, timeout: int = 30):
    for _ in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError(f"Server at {url} did not become healthy within {timeout}s")

@pytest.fixture(scope="session")
def backend_server():
    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "main:app", "--port", "8000"],
        cwd="../backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        wait_for_health("http://localhost:8000/health")
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

@pytest.fixture(scope="session")
def frontend_server():
    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd="../frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(5)  # Vite 冷启动，应替换为端口轮询
    yield proc
    proc.terminate()
    proc.wait()

@pytest.fixture
def page(page: Page, backend_server, frontend_server):
    page.goto("http://localhost:5173")
    return page
```

---

## 4. 网络拦截与 Mock 示例

```python
# utils/api_mock.py
from playwright.sync_api import Page, Route

def mock_ai_design_fast(route: Route):
    route.fulfill(
        status=200,
        content_type="application/json",
        body='{"status":"success","design_id":"mock-design-001"}',
    )

def mock_oauth_callback(page: Page):
    page.route("**/auth/callback**", lambda route: route.fulfill(
        status=200,
        body="<script>"
             "localStorage.setItem('token','test-jwt');"
             "location.href='/'"
             "</script>",
    ))
```

---

## 5. 视觉回归示例

```python
def test_project_dashboard_visual(page):
    page.goto("http://localhost:5173/projects")
    page.wait_for_load_state("networkidle")
    expect(page).to_have_screenshot("project-dashboard.png", full_page=True)
```

更新 baseline：

```bash
PLAYWRIGHT_UPDATE_SNAPSHOTS=1 pytest tests/e2e/flows/ -v
```

---

## 6. GitHub Actions CI 示例

```yaml
name: E2E Tests
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - uses: actions/setup-node@v4
        with: { node-version: "20" }

      - name: Install Backend
        run: cd backend && pip install -r requirements.txt

      - name: Install Frontend
        run: cd frontend && npm ci

      - name: Install Playwright
        run: |
          pip install pytest-playwright
          playwright install chromium

      - name: Run E2E Tests
        run: |
          cd tests/e2e
          pytest --tracing=retain-on-failure --screenshot=only-on-failure --video=retain-on-failure

      - name: Upload Artifacts
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-artifacts
          path: tests/e2e/test-results/
```

---

## 7. Anti-Patterns

| 反模式 | 问题 | 修正 |
|--------|------|------|
| 在 E2E 中断言算法输出 | E2E 不稳定、速度慢 | 算法正确性交给单元测试 |
| `time.sleep(5)` | 慢且不可靠 | 使用 `expect().to_be_visible()` |
| 共享测试数据、依赖顺序 | flaky、难并行 | 每个 test 独立 setup/teardown |
| 硬编码 data-testid | 实现细节变更导致测试失效 | 使用 ARIA / 可见文本 |
| Mock 被测系统本身 | 测试失去意义 | Mock 仅隔离外部依赖 |
| 覆盖所有边界情况 | E2E 爆炸、维护成本高 | E2E 只跑 3–5 个黄金流程 |

---

## 8. 调试命令速查

```bash
# 有界面慢动作
pytest tests/e2e/flows/test_golden_login.py --headed --slowmo 500

# UI 模式
pytest tests/e2e/ --ui

# 生成 trace
pytest tests/e2e/ --tracing=on

# 仅失败时保留 trace/截图/视频
pytest tests/e2e/ --tracing=retain-on-failure --screenshot=only-on-failure --video=retain-on-failure

# 单浏览器
pytest tests/e2e/ --browser chromium
```

---

## 9. 参考链接

- Anthropic webapp-testing Skill: https://github.com/anthropics/skills/tree/main/skills/webapp-testing
- Playwright E2E Patterns: https://lobehub.com/skills/agents-inc-skills-web-testing-playwright-e2e
- Playwright Best Practices: https://playwright.dev/python/docs/best-practices
