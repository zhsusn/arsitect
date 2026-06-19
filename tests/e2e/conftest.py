"""E2E test shared fixtures for Arsitect SDLC Visualizer."""
from __future__ import annotations

import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Generator

import pytest
import requests
from playwright.sync_api import Page, expect

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
SKIP_SERVER_START = os.environ.get("E2E_SKIP_SERVER_START", "0") == "1"


def _free_port() -> int:
    """Return an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_port(host: str, port: int, timeout: float = 60.0) -> None:
    """Wait until a TCP port accepts connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.5)
    raise RuntimeError(f"Port {host}:{port} did not become ready within {timeout}s")


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


@pytest.fixture(scope="session")
def e2e_servers() -> Generator[dict, None, None]:
    """Start backend + frontend dev servers for the E2E session.

    Set E2E_SKIP_SERVER_START=1 to assume servers are already running.
    In that case also set E2E_BACKEND_URL and E2E_FRONTEND_URL.
    """
    backend_proc: subprocess.Popen | None = None
    frontend_proc: subprocess.Popen | None = None
    backend_log = ROOT / "test-results" / "backend-e2e.log"
    frontend_log = ROOT / "test-results" / "frontend-e2e.log"

    if SKIP_SERVER_START:
        yield {
            "backend_url": os.environ.get("E2E_BACKEND_URL", "http://localhost:8000"),
            "frontend_url": os.environ.get("E2E_FRONTEND_URL", "http://localhost:5173"),
            "backend_proc": None,
            "frontend_proc": None,
        }
        return

    backend_port = _free_port()
    frontend_port = _free_port()
    backend_url = f"http://localhost:{backend_port}"
    frontend_url = f"http://localhost:{frontend_port}"

    backend_log.parent.mkdir(parents=True, exist_ok=True)

    # Use an isolated SQLite database file for the E2E session.
    db_path = BACKEND_DIR / "data" / f"sdlc-visualizer-e2e-{os.getpid()}.db"
    if db_path.exists():
        db_path.unlink()

    backend_cmd = [
        str(BACKEND_DIR / ".venv" / "Scripts" / "python.exe"),
        "-c",
        (
            "import uvicorn; "
            f"uvicorn.run('main:app', host='0.0.0.0', port={backend_port}, reload=False, workers=1)"
        ),
    ]
    backend_env = os.environ.copy()
    backend_env["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path.as_posix()}"
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

    # Use npm script; batch files require shell=True on Windows.
    frontend_cmd = f'npm run dev -- --port {frontend_port} --host'
    frontend_env = os.environ.copy()
    frontend_env["VITE_API_URL"] = backend_url
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

    _wait_for_port("localhost", frontend_port, timeout=60.0)

    yield {
        "backend_url": backend_url,
        "frontend_url": frontend_url,
        "backend_proc": backend_proc,
        "frontend_proc": frontend_proc,
    }

    _terminate(frontend_proc)
    _terminate(backend_proc)
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass


@pytest.fixture
def app_page(e2e_servers: dict, page: Page) -> Page:
    """Return a Page with default timeout and base URL."""
    page.set_default_timeout(10000)
    page.goto(e2e_servers["frontend_url"])
    # Wait for the app shell to render.
    expect(page.get_by_text("Arsitect", exact=True)).to_be_visible()
    return page


@pytest.fixture
def api_base(e2e_servers: dict) -> str:
    """Return backend API base URL."""
    return e2e_servers["backend_url"] + "/api/v1"
