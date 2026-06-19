"""File system watcher — watchdog-based artifact change detection."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from app.common.event_bus import DomainEvent, EventBus

if TYPE_CHECKING:
    from app.common.artifact_store import ArtifactStore


class ArtifactEventHandler(FileSystemEventHandler):
    """Handle file system events for an artifact directory."""

    def __init__(
        self,
        project_id: str,
        watch_root: Path,
        artifact_store: ArtifactStore,
        event_bus: EventBus | None = None,
    ) -> None:
        self.project_id = project_id
        self.watch_root = watch_root
        self.store = artifact_store
        self.event_bus = event_bus
        self._debounce_timers: dict[str, asyncio.TimerHandle] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._handle_change(event.src_path)

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._handle_change(event.src_path)

    def _handle_change(self, file_path: str) -> None:
        """Debounce file change events."""
        relative_path = self._relative_path(file_path)
        if relative_path is None:
            return

        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

        existing = self._debounce_timers.get(relative_path)
        if existing is not None:
            existing.cancel()

        self._debounce_timers[relative_path] = self._loop.call_later(
            0.5,
            lambda: asyncio.create_task(self._process_change(file_path, relative_path)),
        )

    async def _process_change(self, file_path: str, relative_path: str) -> None:
        """Process a debounced change and publish STALE event if external."""
        self._debounce_timers.pop(relative_path, None)

        changed, current_hash = self.store.check_external_change(relative_path)
        if changed and self.event_bus is not None:
            self.event_bus.publish(
                DomainEvent(
                    event_type="artifact.external_change",
                    aggregate_id=self.project_id,
                    payload={
                        "project_id": self.project_id,
                        "file_path": relative_path,
                        "new_hash": current_hash,
                    },
                    source="file_system_watcher",
                )
            )

    def _relative_path(self, file_path: str) -> str | None:
        """Return path relative to watch root, or None if outside."""
        try:
            return str(Path(file_path).relative_to(self.watch_root))
        except ValueError:
            return None


class FileSystemWatcher:
    """File system watcher.

    Responsibilities:
    1. Watch artifact directories via watchdog.
    2. Debounce rapid changes.
    3. Detect external changes and publish STALE events.
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.event_bus = event_bus
        self._observers: dict[str, Any] = {}
        self._handlers: dict[str, ArtifactEventHandler] = {}

    def watch_project(
        self,
        project_id: str,
        path: str,
        artifact_store: ArtifactStore,
    ) -> None:
        """Start watching a project artifact directory.

        If the directory does not exist yet, the call is ignored so that
        callers can safely invoke it during artifact lifecycle transitions.
        """
        if project_id in self._observers:
            return

        watch_root = Path(path)
        if not watch_root.exists():
            return
        handler = ArtifactEventHandler(
            project_id,
            watch_root,
            artifact_store,
            self.event_bus,
        )
        observer = Observer()
        observer.schedule(handler, str(watch_root), recursive=True)  # type: ignore[no-untyped-call]
        observer.start()  # type: ignore[no-untyped-call]

        self._observers[project_id] = observer
        self._handlers[project_id] = handler

    def unwatch_project(self, project_id: str) -> None:
        """Stop watching a project directory."""
        observer = self._observers.pop(project_id, None)
        self._handlers.pop(project_id, None)
        if observer is not None:
            observer.stop()
            observer.join()

    def stop_all(self) -> None:
        """Stop all watchers."""
        for observer in self._observers.values():
            observer.stop()
        for observer in self._observers.values():
            observer.join()
        self._observers.clear()
        self._handlers.clear()


# Global singleton
_file_system_watcher: FileSystemWatcher | None = None


def get_file_system_watcher() -> FileSystemWatcher:
    """Return the global file system watcher singleton."""
    global _file_system_watcher
    if _file_system_watcher is None:
        from app.common.event_bus import get_event_bus

        _file_system_watcher = FileSystemWatcher(get_event_bus())
    return _file_system_watcher
