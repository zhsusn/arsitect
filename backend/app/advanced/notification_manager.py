"""NotificationManager — multi-channel notification hub."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from fastapi.responses import StreamingResponse

from app.common.event_bus import DomainEvent, EventBus


class NotificationChannel(str):
    """Notification channel constants."""

    SSE = "sse"
    WEBHOOK = "webhook"


@dataclass
class Notification:
    """A notification record."""

    id: str
    type: str
    title: str
    message: str
    project_id: str
    channels: list[str]
    created_at: datetime
    read: bool = False


NotificationHandler = Callable[[Notification], Awaitable[None] | None]


class NotificationManager:
    """Notification manager.

    Responsibilities:
    1. Generate and store notifications.
    2. Deliver via SSE and Webhook channels.
    3. Mark notifications as read.
    4. Subscribe to domain events (gate, timebox) and notify users.
    """

    def __init__(self, event_bus: EventBus) -> None:
        """Initialize with event bus."""
        self.event_bus = event_bus
        self._notifications: dict[str, list[Notification]] = {}
        self._clients: dict[str, set[asyncio.Queue[str]]] = {}
        self._handlers: dict[str, NotificationHandler] = {}
        self._subscribed = False

        self._register_default_handlers()
        self._subscribe_events()

    def _register_default_handlers(self) -> None:
        """Register built-in channel handlers."""
        self._handlers[NotificationChannel.SSE] = self._send_sse

    def _subscribe_events(self) -> None:
        """Subscribe to domain events for automatic notifications."""
        if self._subscribed:
            return
        self._subscribed = True
        self.event_bus.subscribe("gate.created", self._on_gate_created)
        self.event_bus.subscribe("timebox.warning", self._on_timebox_warning)
        self.event_bus.subscribe("artifact.external_change", self._on_external_change)

    def _on_gate_created(self, event: DomainEvent) -> None:
        """Notify when a gate is created."""
        self.send(
            type="gate",
            title="Approval Required",
            message=f"Skill '{event.payload.get('skill_id')}' requires approval",
            project_id=event.aggregate_id,
            channels=[NotificationChannel.SSE],
        )

    def _on_timebox_warning(self, event: DomainEvent) -> None:
        """Notify on timebox warning."""
        self.send(
            type="timeout",
            title="Timebox Warning",
            message=f"Milestone '{event.payload.get('milestone')}' approaching deadline",
            project_id=event.aggregate_id,
            channels=[NotificationChannel.SSE],
        )

    def _on_external_change(self, event: DomainEvent) -> None:
        """Notify on external artifact change."""
        self.send(
            type="system",
            title="Artifact Externally Modified",
            message=f"File '{event.payload.get('file_path')}' changed outside the app",
            project_id=event.aggregate_id,
            channels=[NotificationChannel.SSE],
        )

    def send(
        self,
        type: str,
        title: str,
        message: str,
        project_id: str,
        channels: list[str],
    ) -> Notification:
        """Send a notification through configured channels."""
        notification = Notification(
            id=f"notif-{uuid.uuid4()}",
            type=type,
            title=title,
            message=message,
            project_id=project_id,
            channels=channels,
            created_at=datetime.now(UTC),
        )

        self._notifications.setdefault(project_id, []).append(notification)

        for channel in channels:
            handler = self._handlers.get(channel)
            if handler is None:
                continue
            try:
                result = handler(notification)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception as e:
                print(f"[NotificationManager] Handler error: {e}")

        return notification

    def register_channel_handler(self, channel: str, handler: NotificationHandler) -> None:
        """Register or override a channel handler."""
        self._handlers[channel] = handler

    def get_notifications(self, project_id: str, unread_only: bool = False) -> list[Notification]:
        """Return notifications for a project."""
        notifications = self._notifications.get(project_id, [])
        if unread_only:
            return [n for n in notifications if not n.read]
        return list(notifications)

    def mark_read(self, project_id: str, notification_id: str) -> bool:
        """Mark a notification as read."""
        for n in self._notifications.get(project_id, []):
            if n.id == notification_id:
                n.read = True
                return True
        return False

    def mark_all_read(self, project_id: str) -> int:
        """Mark all project notifications as read."""
        count = 0
        for n in self._notifications.get(project_id, []):
            if not n.read:
                n.read = True
                count += 1
        return count

    async def connect_sse(self, project_id: str, request: Request) -> StreamingResponse:
        """Create an SSE stream for a project."""
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        self._clients.setdefault(project_id, set()).add(queue)

        async def event_generator() -> Any:
            try:
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        message = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield message
                    except TimeoutError:
                        yield ": heartbeat\n\n"
            finally:
                self._clients[project_id].discard(queue)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    def _send_sse(self, notification: Notification) -> None:
        """Broadcast notification to connected SSE clients."""
        clients = self._clients.get(notification.project_id)
        if not clients:
            return

        message = {
            "type": notification.type,
            "title": notification.title,
            "message": notification.message,
            "notification_id": notification.id,
            "created_at": notification.created_at.isoformat(),
        }
        message_str = f"data: {json.dumps(message)}\n\n"

        dead: set[asyncio.Queue[str]] = set()
        for queue in clients:
            try:
                queue.put_nowait(message_str)
            except asyncio.QueueFull:
                dead.add(queue)

        for dq in dead:
            clients.discard(dq)

    def broadcast(self, project_id: str, message_type: str, payload: dict[str, Any]) -> None:
        """Broadcast a raw message to SSE clients."""
        clients = self._clients.get(project_id)
        if not clients:
            return

        message_str = f"data: {json.dumps({'type': message_type, 'data': payload})}\n\n"
        dead: set[asyncio.Queue[str]] = set()
        for queue in clients:
            try:
                queue.put_nowait(message_str)
            except asyncio.QueueFull:
                dead.add(queue)
        for dq in dead:
            clients.discard(dq)
