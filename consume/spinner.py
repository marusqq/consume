"""Minimal terminal spinner for showing progress during long operations."""

import itertools
import sys
import threading
import time
from contextlib import contextmanager


_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
_INTERVAL = 0.08


class _Spinner:
    def __init__(self) -> None:
        self._message = ""
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._last_width = 0

    def set(self, message: str) -> None:
        with self._lock:
            self._message = message

    def _run(self) -> None:
        for frame in itertools.cycle(_FRAMES):
            if self._stop.is_set():
                break
            with self._lock:
                line = f"{frame}  {self._message}"
            # Overwrite previous line, pad to clear leftover characters
            pad = max(0, self._last_width - len(line))
            sys.stderr.write(f"\r{line}{' ' * pad}")
            sys.stderr.flush()
            self._last_width = len(line)
            time.sleep(_INTERVAL)

    def start(self) -> None:
        if sys.stderr.isatty():
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join()
        # Clear the spinner line
        sys.stderr.write(f"\r{' ' * (self._last_width + 2)}\r")
        sys.stderr.flush()


@contextmanager
def spinner(initial_message: str = ""):
    """Context manager that shows a spinner on stderr while work runs.

    Yields a callable ``step(message)`` to update the displayed stage label.
    The spinner is suppressed when stderr is not a tty (e.g. piped output).

    Usage::

        with spinner("Fetching...") as step:
            html = fetch_html(url)
            step("Summarizing...")
            summary = summarize(html)
    """
    s = _Spinner()
    s.set(initial_message)
    s.start()
    try:
        yield s.set
    finally:
        s.stop()
