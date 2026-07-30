"""Watch a directory and re-run checks on change."""

from __future__ import annotations

import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class _DebouncedHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[], None], debounce_s: float = 0.25) -> None:
        super().__init__()
        self._callback = callback
        self._debounce_s = debounce_s
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        src = str(getattr(event, "src_path", "") or "")
        dest = str(getattr(event, "dest_path", "") or "")
        if not _relevant_path(src) and not _relevant_path(dest):
            return
        self._schedule()

    def _schedule(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce_s, self._callback)
            self._timer.daemon = True
            self._timer.start()


def _relevant_path(path: str) -> bool:
    if not path:
        return False
    lower = path.lower()
    if "/.obsidian/" in lower.replace("\\", "/"):
        return False
    return lower.endswith(".md") or lower.endswith(".yaml") or lower.endswith(".yml")


def watch_and_report(
    root: Path,
    run_once: Callable[[], int],
    *,
    recursive: bool,
) -> int:
    """Run checks immediately, then on changes. Returns on KeyboardInterrupt."""

    def _run() -> None:
        # Clear-ish refresh: blank line then reprint.
        sys.stdout.write("\n")
        run_once()
        sys.stdout.write(f"watching {root} (Ctrl+C to stop)\n")
        sys.stdout.flush()

    # Initial run without leading blank.
    run_once()
    sys.stdout.write(f"watching {root} (Ctrl+C to stop)\n")
    sys.stdout.flush()

    handler = _DebouncedHandler(_run)
    observer = Observer()
    observer.schedule(handler, str(root.resolve()), recursive=recursive)
    # Also watch schema parent if schema lives elsewhere — caller watches root only;
    # schema default lives under root. Fine for v1.
    observer.start()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
        return 0
