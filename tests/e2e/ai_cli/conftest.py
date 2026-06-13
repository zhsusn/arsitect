"""E2E fixtures for AI CLI Terminal page."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Generator

import pytest
import requests
from playwright.sync_api import Page

ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

DEFAULT_BACKEND_HOST = os.environ.get("E2E_BACKEND_HOST", "127.0.0.1")
DEFAULT_FRONTEND_HOST = os.environ.get("E2E_FRONTEND_HOST", "127.0.0.1")
DEFAULT_BACKEND_PORT = int(os.environ.get("E2E_BACKEND_PORT", "8000"))
DEFAULT_FRONTEND_PORT = int(os.environ.get("E2E_FRONTEND_PORT", "5173"))

SKIP_SERVER_START = os.environ.get("E2E_SKIP_SERVER_START", "0") == "1"


def _free_port(host: str = "127.0.0.1") -> int:
    """Return an available TCP port on the given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]


def _is_port_open(host: str, port: int) -> bool:
    """Return True if the TCP port is accepting connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0


def _wait_for_backend_health(base_url: str, timeout: float = 60.0) -> None:
    """Poll backend /api/v1/health until it returns 200."""
    deadline = time.time() + timeout
    last_err = None
    while time.time() < deadline:
        try:
            resp = requests.get(f"{base_url}/api/v1/health", timeout=2)
            if resp.status_code == 200:
                return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
        time.sleep(0.5)
    raise RuntimeError(
        f"Backend health check failed within {timeout}s: {last_err}"
    )


def _wait_for_frontend(url: str, timeout: float = 60.0) -> None:
    """Wait until the frontend dev server responds with HTTP 200."""
    deadline = time.time() + timeout
    last_err = None
    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
        time.sleep(0.5)
    raise RuntimeError(
        f"Frontend did not become ready within {timeout}s: {last_err}"
    )


def _terminate(proc: subprocess.Popen | None) -> None:
    """Terminate a subprocess gracefully."""
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def pytest_configure(config: pytest.Config) -> None:
    """Ensure this test directory is searched before the parent `tests/e2e`."""
    here = str(Path(__file__).resolve().parent)
    if here in sys.path:
        sys.path.remove(here)
    sys.path.insert(0, here)


@pytest.fixture(scope="session")
def e2e_servers() -> Generator[dict, None, None]:
    """Start backend and frontend dev servers once per test session.

    Set E2E_SKIP_SERVER_START=1 to assume servers are already running on
    the default ports (backend 8000, frontend 5173).
    """
    backend_proc: subprocess.Popen | None = None
    frontend_proc: subprocess.Popen | None = None

    backend_log = ROOT / "test-results" / "ai-cli-backend-e2e.log"
    frontend_log = ROOT / "test-results" / "ai-cli-frontend-e2e.log"
    backend_log.parent.mkdir(parents=True, exist_ok=True)

    if SKIP_SERVER_START:
        backend_url = f"http://{DEFAULT_BACKEND_HOST}:{DEFAULT_BACKEND_PORT}"
        frontend_url = f"http://{DEFAULT_FRONTEND_HOST}:{DEFAULT_FRONTEND_PORT}"
        yield {
            "backend_url": backend_url,
            "frontend_url": frontend_url,
            "backend_proc": None,
            "frontend_proc": None,
        }
        return

    backend_host = DEFAULT_BACKEND_HOST
    backend_port = (
        DEFAULT_BACKEND_PORT
        if not _is_port_open(DEFAULT_BACKEND_HOST, DEFAULT_BACKEND_PORT)
        else _free_port(backend_host)
    )
    backend_url = f"http://{backend_host}:{backend_port}"

    frontend_host = DEFAULT_FRONTEND_HOST
    frontend_port = (
        DEFAULT_FRONTEND_PORT
        if not _is_port_open(DEFAULT_FRONTEND_HOST, DEFAULT_FRONTEND_PORT)
        else _free_port(frontend_host)
    )
    frontend_url = f"http://{frontend_host}:{frontend_port}"

    python_exe = sys.executable
    if (BACKEND_DIR / ".venv" / "Scripts" / "python.exe").exists():
        python_exe = str(BACKEND_DIR / ".venv" / "Scripts" / "python.exe")

    backend_cmd = [
        python_exe,
        "-c",
        (
            "import uvicorn; "
            f"uvicorn.run('main:app', host='{backend_host}', port={backend_port}, "
            "reload=False, workers=1)"
        ),
    ]
    backend_env = os.environ.copy()
    backend_env["DATABASE_URL"] = (
        f"sqlite+aiosqlite:///{(BACKEND_DIR / 'data' / 'ai-cli-e2e.db').as_posix()}"
    )
    backend_env["CORS_ORIGINS"] = f'["{frontend_url}"]'

    with open(backend_log, "w", encoding="utf-8") as backend_stdout:
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=BACKEND_DIR,
            stdout=backend_stdout,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=backend_env,
        )

    try:
        _wait_for_backend_health(backend_url, timeout=60.0)
    except RuntimeError as exc:
        _terminate(backend_proc)
        raise RuntimeError(
            f"Backend failed to start. See {backend_log} for details."
        ) from exc

    frontend_cmd = f"npm run dev -- --port {frontend_port} --host {frontend_host}"
    frontend_env = os.environ.copy()
    frontend_env["VITE_API_URL"] = backend_url
    frontend_env["VITE_WS_URL"] = backend_url.replace("http://", "ws://")

    with open(frontend_log, "w", encoding="utf-8") as frontend_stdout:
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=FRONTEND_DIR,
            stdout=frontend_stdout,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=True,
            env=frontend_env,
        )

    try:
        _wait_for_frontend(frontend_url, timeout=60.0)
    except RuntimeError as exc:
        _terminate(frontend_proc)
        _terminate(backend_proc)
        raise RuntimeError(
            f"Frontend failed to start. See {frontend_log} for details."
        ) from exc

    yield {
        "backend_url": backend_url,
        "frontend_url": frontend_url,
        "backend_proc": backend_proc,
        "frontend_proc": frontend_proc,
    }

    _terminate(frontend_proc)
    _terminate(backend_proc)


@pytest.fixture(scope="session")
def base_url(e2e_servers: dict) -> str:
    """Return the frontend base URL."""
    return e2e_servers["frontend_url"]


@pytest.fixture
def cli_page(page: Page, base_url: str) -> "CliPage":
    """Return an initialized AI CLI page object."""
    from pages.cli_page import CliPage

    cli = CliPage(page, base_url)
    cli.navigate_to()
    return cli
