"""Route registration smoke tests for the advanced enterprise router."""

from __future__ import annotations

from main import app


class TestAdvancedRouter:
    """Smoke tests verifying /api/v1/advanced route registration."""

    def test_advanced_routes_registered(self) -> None:
        """All Batch-05 advanced endpoints should be present."""
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        expected = [
            "/api/v1/advanced/history/{project_id}/timeline",
            "/api/v1/advanced/history/{project_id}/heatmap",
            "/api/v1/advanced/history/completed",
            "/api/v1/advanced/applications/{application_id}/history/summary",
            "/api/v1/advanced/projects/{project_id}/members",
            "/api/v1/advanced/projects/{project_id}/permissions/check",
            "/api/v1/advanced/projects/{project_id}/gaps",
            "/api/v1/advanced/projects/{project_id}/gaps/writeback",
            "/api/v1/advanced/projects/{project_id}/gaps/sync-to-dsl",
            "/api/v1/advanced/projects/{project_id}/drift",
            "/api/v1/advanced/projects/{project_id}/metrics",
            "/api/v1/advanced/projects/{project_id}/skills/{skill_id}/metrics",
            "/api/v1/advanced/search",
            "/api/v1/advanced/projects/{project_id}/notifications",
            "/api/v1/advanced/projects/{project_id}/notifications/{notif_id}/read",
            "/api/v1/advanced/events/{project_id}",
            "/api/v1/advanced/projects/{project_id}/export",
            "/api/v1/advanced/projects/import",
        ]
        for path in expected:
            assert path in routes, f"Missing route: {path}"

    def test_legacy_history_route_removed(self) -> None:
        """Old /api/v1/history endpoints should no longer exist."""
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/api/v1/history/{project_id}" not in routes

    def test_legacy_events_route_removed(self) -> None:
        """Old /api/v1/events endpoint should no longer exist."""
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/api/v1/events/{project_id}" not in routes
