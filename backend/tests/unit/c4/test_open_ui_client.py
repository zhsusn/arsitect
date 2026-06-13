"""Tests for OpenUIClient."""

from __future__ import annotations

from app.c4.open_ui_client import OpenUIClient


class TestOpenUIClient:
    """OpenUIClient unit tests."""

    def test_assemble_prompt(self) -> None:
        """Prompt contains container and endpoint info."""
        client = OpenUIClient(None, None)
        containers = [
            {
                "id": "Web",
                "name": "Web App",
                "technology": "React",
                "description": "Frontend",
            }
        ]
        contracts = {
            "Web": [
                type(
                    "C",
                    (),
                    {
                        "method": "GET",
                        "endpoint_path": "/api/users",
                        "summary": "List users",
                    },
                )(),
            ]
        }
        prompt = client._assemble_prompt(containers, contracts)

        assert "Web App" in prompt
        assert "GET /api/users" in prompt
        assert "You are a UI generation assistant" in prompt

    def test_split_pages_multi(self) -> None:
        """Split HTML with PAGE comments into multiple pages."""
        client = OpenUIClient(None, None)
        html = """<html><!-- PAGE: Home --><body>Home</body><!-- PAGE: Detail --><body>Detail</body></html>"""
        pages = client._split_pages(html)

        assert len(pages) == 2
        assert pages[0]["title"] == "Home"
        assert pages[1]["title"] == "Detail"

    def test_split_single_page(self) -> None:
        """Single page HTML without comments."""
        client = OpenUIClient(None, None)
        pages = client._split_pages("<html><body>Single</body></html>")
        assert len(pages) == 1
        assert pages[0]["title"] == "Main Page"

    def test_split_empty_page_comment(self) -> None:
        """Preamble before first PAGE comment is ignored."""
        client = OpenUIClient(None, None)
        html = "preamble<!-- PAGE: Start --><body>Start</body>"
        pages = client._split_pages(html)
        assert len(pages) == 1
        assert pages[0]["title"] == "Start"

    def test_build_fallback_wireframe(self) -> None:
        """Fallback HTML contains container and endpoint info."""
        client = OpenUIClient(None, None)
        containers = [{"id": "API", "name": "API Service", "technology": "FastAPI"}]
        contracts = [
            type(
                "C",
                (),
                {
                    "method": "GET",
                    "endpoint_path": "/health",
                    "summary": "Health check",
                    "container_id": "API",
                },
            )(),
        ]
        html = client._build_fallback_wireframe(containers, contracts)

        assert "OpenUI 服务不可用" in html
        assert "API Service" in html
        assert "GET" in html
        assert "/health" in html

    def test_build_fallback_no_contracts(self) -> None:
        """Fallback shows placeholder when no contracts."""
        client = OpenUIClient(None, None)
        containers = [{"id": "UI", "name": "UI", "technology": "React"}]
        html = client._build_fallback_wireframe(containers, [])

        assert "暂无接口定义" in html

    def test_error_result(self) -> None:
        """_error_result returns ERROR status."""
        client = OpenUIClient(None, None)
        result = client._error_result("Service down")

        assert result.status == "ERROR"
        assert result.error_message == "Service down"
        assert result.html_content is None
        assert result.page_count == 0
