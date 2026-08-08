from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from threading import Lock, Timer
from typing import Any


class WatchDependencyError(RuntimeError):
    pass


def watch_markdown(root: Path, callback: Callable[[], None]) -> None:
    try:
        FileSystemEventHandler = import_module("watchdog.events").FileSystemEventHandler
        Observer = import_module("watchdog.observers").Observer
    except ImportError as error:
        raise WatchDependencyError("watch requires the 'watchdog' package") from error

    callback_lock = Lock()
    timer: Timer | None = None

    class MarkdownEventHandler(FileSystemEventHandler):
        def on_any_event(self, event: Any) -> None:
            nonlocal timer
            paths = (getattr(event, "src_path", ""), getattr(event, "dest_path", ""))
            if event.is_directory or not any(
                str(path).endswith(".md") for path in paths
            ):
                return
            with callback_lock:
                if timer is not None:
                    timer.cancel()
                timer = Timer(0.25, callback)
                timer.daemon = True
                timer.start()

    observer = Observer()
    observer.schedule(MarkdownEventHandler(), str(root), recursive=True)
    observer.start()
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
    finally:
        with callback_lock:
            if timer is not None:
                timer.cancel()
        observer.join()
