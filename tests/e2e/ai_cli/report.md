# AI CLI Chat — E2E Test Report

## Test Coverage Matrix

| ID | Scenario | Page Object Methods Used | Expected Result | Status |
|----|----------|--------------------------|-----------------|--------|
| TC-01 | Composer renders and is editable | `navigate_to`, `wait_for_composer` | Textarea visible, not disabled | ✅ PASS |
| TC-02 | User can type and send while connecting | `type_command` | Typed text appears and user message bubble renders | ✅ PASS |
| TC-03 | Bug report produces a fix-proposal card | `switch_mode`, `type_command`, `wait_for_message` | Card with "执行修复" visible | ✅ PASS |
| TC-04 | Fix-proposal card can be executed | `switch_mode`, `type_command`, `click_fix_button` | After click, "Bug 修复已执行" shown | ✅ PASS |
| TC-05 | Slash commands switch between Bug and Arch | `type_command`, `wait_for_message` | `/arch` switches to arch mode; `/bug` switches back | ✅ PASS |
| TC-06 | Free-chat receives an AI response | `type_command` | AI response contains "Arsitect" | ✅ PASS |

## Mock List

The following backend behaviours are mocked so that no real AI API key or external LLM call is required:

| Component | Mock Behaviour | Location |
|-----------|----------------|----------|
| `BugFixService.save_bug_record` | Creates a `BugRecord` from user input | `backend/app/services/bug_fix_service.py` |
| `BugFixService.generate_fix_plan` | Returns a deterministic fix plan with `root_cause`, `affected_files`, `fix_risk`, `fix_diff` | `backend/app/services/bug_fix_service.py` |
| `AgentRouter` | Routes `/bug`, `/arch` slash commands and emits `text`/`card` responses | `backend/app/services/chat/agent_router.py` |

No external HTTP or LLM calls are made during the bug/arch tests.

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
D:\srccode\arsitect\backend\.venv\Scripts\pytest.exe test_golden_cli.py::test_fix_proposal_can_be_executed -v --tb=long
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
4. **Stale e2e database** — delete `backend/data/ai-cli-e2e.db*` if schema errors occur.
5. **WebSocket connection fails** — verify the Vite dev server proxy `/ws -> ws://127.0.0.1:8000` and that `backend/app/api/v1/chat.py` exposes `/api/v1/chat/ws/{session_id}`.

## Fixes Applied During Test Development

1. **WebSocket message field mismatch** — the frontend sends `sessionId` (camelCase) in WebSocket `CliRequest` messages, while the backend `CliRequest` schema expected only `session_id` (snake_case). This caused every command to fail with `session_id Field required`. Fixed by adding `validation_alias=AliasChoices("session_id", "sessionId")` to `backend/app/schemas/cli.py` (`CliRequest.session_id`).
2. **Vite proxy hardcoded to port 8000** — the E2E fixtures may start the backend on a free port. `frontend/vite.config.ts` now reads `VITE_API_URL` and `VITE_WS_URL` from the environment, defaulting to `127.0.0.1:8000` for normal development.
3. **Chat composer disabled during connection** — the AI CLI page disabled the textarea while the WebSocket status was `connecting`, preventing users from typing. Fixed by keeping the textarea editable and allowing messages to queue until the connection opens.
4. **Mode switch race condition** — switching modes quickly after page load could create a stale session because the initial `createSession()` was still in flight. Fixed by adding a generation counter in `useChatSession` so older session creation results are discarded when `clearSession()` is called.
5. **Free-chat error hidden / duplicated** — error messages from `_run_free_chat` were swallowed by the generic handler and duplicated in the UI. Fixed by logging the full exception in `backend/app/services/chat/agent_router.py` and preventing duplicate display in `frontend/src/components/chat/MessageItem.tsx`.
6. **Kimi CLI hang / missing executable** — free-chat could hang indefinitely if Kimi CLI was slow or missing. Fixed by adding a 120s timeout and a clear `FileNotFoundError` message in `backend/app/services/llm/kimi_cli.py`.
7. **Windows asyncio subprocess failure** — on Windows, Uvicorn may run with a `SelectorEventLoop` that does not support `asyncio.create_subprocess_exec`, causing `NotImplementedError` and breaking free-chat. Fixed by catching `NotImplementedError` in `kimi_cli.py` and falling back to a synchronous `subprocess.run` executed via `asyncio.to_thread`.

## Latest Run Result

```text
6 passed in ~17s
```
