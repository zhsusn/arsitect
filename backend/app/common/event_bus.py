"""Async in-memory event bus."""

from __future__ import annotations

import asyncio
import contextlib
import traceback
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class DomainEvent:
    """Domain event for async pub/sub."""

    event_type: str
    aggregate_id: str
    payload: dict[str, Any]
    timestamp: float = field(default_factory=lambda: datetime.now(UTC).timestamp())
    source: str = ""


EventHandler = Callable[[DomainEvent], Awaitable[None] | None]


class EventBus:
    """Async event bus with error isolation.

    Usage::

        bus = EventBus()
        await bus.start()
        bus.subscribe("c4.baseline.created", on_created)
        bus.publish(DomainEvent("c4.baseline.created", pid, {}))
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = {}
        self._event_queue: asyncio.Queue[DomainEvent] = asyncio.Queue()
        self._dispatch_task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        """Start dispatch loop."""
        if self._running:
            return
        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())

    async def stop(self) -> None:
        """Stop dispatch loop."""
        self._running = False
        if self._dispatch_task:
            self._dispatch_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._dispatch_task

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to event type."""
        self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe from event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

    def publish(self, event: DomainEvent) -> None:
        """Publish event (non-blocking)."""
        if not self._running:
            # Buffer for later dispatch if bus not started yet
            asyncio.create_task(self._event_queue.put(event))
            return
        asyncio.create_task(self._event_queue.put(event))

    async def _dispatch_loop(self) -> None:
        """Main dispatch loop."""
        while self._running:
            try:
                event = await self._event_queue.get()
                await self._dispatch(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[EventBus] Dispatch loop error: {e}")

    async def _dispatch(self, event: DomainEvent) -> None:
        """Dispatch event to all subscribers."""
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                print(f"[EventBus] Handler error for {event.event_type}: {e}")
                traceback.print_exc()

    def subscriber_count(self, event_type: str) -> int:
        """Return subscriber count for event type."""
        return len(self._subscribers.get(event_type, []))


# Global singleton
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Return global event bus (lazy singleton)."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
