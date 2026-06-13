# AI CLI Terminal — E2E Test Report

## Test Coverage Matrix

| ID | Scenario | Page Object Methods Used | Expected Result | Status |
|----|----------|--------------------------|-----------------|--------|
| TC-01 | Page loads and terminal renders | `navigate_to`, `wait_for_terminal`, `wait_for_message` | Heading "AI CLI 终端" visible; `.xterm-rows` present; welcome message shown | ✅ PASS |
| TC-02 | User types a bug report and receives AI analysis | `type_command`, `wait_for_message` | Terminal shows `[AI]` response | ✅ PASS |
| TC-03 | Fix-proposal card appears and can be executed | `type_command`, `wait_for_message`, `click_fix_button` | Card with "执行修复" visible; after click terminal shows `已执行操作：Y` | ✅ PASS |
| TC-04 | Mode switch between Bug and Arch | `switch_mode`, `wait_for_message` | Switching to Arch shows architecture hint; switching back shows Bug hint | ✅ PASS |

## Mock List

The following backend behaviours are mocked so that no real AI API key or external LLM call is required:

| Component | Mock Behaviour | Location |
|-----------|----------------|----------|
| `BugFixService.save_bug_record` | Creates a `BugRecord` from user input | `backend/app/services/bug_fix_service.py` |
| `BugFixService.generate_fix_plan` | Returns a deterministic fix plan with `root_cause`, `affected_files`, `fix_risk`, `fix_diff` | `backend/app/services/bug_fix_service.py` |
| `CliService` WebSocket handler | Emits `text`, `card`, and `error` responses | `backend/app/api/v1/cli.py` |
| AIGateway (indirect) | Fix plan generation uses the mocked service layer, not a live model | `backend/app/services/bug_fix_service.py` |

No external HTTP or LLM calls are made during the tests.

## Run Commands

Run all AI CLI E2E tests from the project root:

```powershell
cd tests\e2e\ai_cli
D:\srccode\arsitect\backend\.venv\Scripts\pytest.exe -q --tb=short
```

> **Note:** `pytest-playwright` is installed in `backend/.venv`. If your shell does not find `pytest`, activate that virtual environment first or use the full path shown above.

Run with an externally-managed stack (backend on `127.0.0.1:8000`, frontend on `127.0.0.1:5173`):

```powershell
cd tests\e2e\ai_cli
$env:E2E_SKIP_SERVER_START = "1"
D:\srccode\arsitect\backend\.venv\Scripts\pytest.exe -q --tb=short
```

Run a single test with extra detail:

```powershell
cd tests\e2e\ai_cli
D:\srccode\arsitect\backend\.venv\Scripts\pytest.exe test_golden_cli.py::test_bug_report_receives_ai_analysis -v --tb=long
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `E2E_SKIP_SERVER_START` | `0` | Set to `1` to skip starting backend/frontend dev servers |
| `E2E_BACKEND_HOST` | `127.0.0.1` | Backend host |
| `E2E_BACKEND_PORT` | `8000` | Backend port |
| `E2E_FRONTEND_HOST` | `127.0.0.1` | Frontend host |
| `E2E_FRONTEND_PORT` | `5173` | Frontend dev server port |

## Failure Notes

If the tests fail, check the following logs:

- `test-results/ai-cli-backend-e2e.log`
- `test-results/ai-cli-frontend-e2e.log`

Common causes:

1. **Port already in use** — the fixtures automatically fall back to a free port if the default is occupied, but if `E2E_SKIP_SERVER_START=1` is used, ensure nothing is running on `127.0.0.1:8000` or `127.0.0.1:5173`.
2. **Backend dependency missing** — run `pip install -r backend/requirements.txt` inside `backend/.venv`.
3. **Frontend dependencies missing** — run `npm install` inside `frontend/`.
4. **xterm.js input not captured** — the tests rely on `.xterm` canvas click + keyboard typing; if xterm.js internals change, update `CliPage.type_command`.
5. **WebSocket connection fails** — verify the Vite dev server proxy `/ws -> ws://127.0.0.1:8000` and that `backend/app/api/v1/cli.py` exposes `/api/v1/cli/ws/{session_id}`.

## Fixes Applied During Test Development

1. **WebSocket message field mismatch** — the frontend sends `sessionId` (camelCase) in WebSocket `CliRequest` messages, while the backend `CliRequest` schema expected only `session_id` (snake_case). This caused every command to fail with `session_id Field required`. Fixed by adding `validation_alias=AliasChoices("session_id", "sessionId")` to `backend/app/schemas/cli.py` (`CliRequest.session_id`).
2. **Vite proxy hardcoded to port 8000** — the E2E fixtures may start the backend on a free port. `frontend/vite.config.ts` now reads `VITE_API_URL` and `VITE_WS_URL` from the environment, defaulting to `127.0.0.1:8000` for normal development.

## Latest Run Result

```text
4 passed in ~12s
```
