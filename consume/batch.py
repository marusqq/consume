"""Batch processing: read URLs from a file and consume each with human-like delays."""

import random
import sys
import time
from pathlib import Path

# Delay between consecutive requests (seconds)
_DELAY_MIN = 8
_DELAY_MAX = 20

# After this many URLs, take a longer break
_LONG_PAUSE_EVERY = 10
_LONG_PAUSE_MIN = 45
_LONG_PAUSE_MAX = 90


def load_urls(path: Path) -> list[str]:
    """Read URLs from a file, skipping blank lines and # comments."""
    urls = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def _countdown(seconds: int, label: str) -> None:
    """Show a live countdown on stderr."""
    for remaining in range(seconds, 0, -1):
        sys.stderr.write(f"\r  {label} {remaining}s…  ")
        sys.stderr.flush()
        time.sleep(1)
    sys.stderr.write(f"\r{' ' * 40}\r")
    sys.stderr.flush()


def run_batch(
    file: Path,
    mode: str,
    fmt: str,
    voice: str | None,
    delay_min: int = _DELAY_MIN,
    delay_max: int = _DELAY_MAX,
) -> int:
    """Process all URLs in file one by one with randomised delays.

    Returns 0 if all succeeded, 1 if any failed.
    """
    from .cli import _process_url

    if not file.exists():
        print(f"Error: file not found: {file}", file=sys.stderr)
        return 1

    urls = load_urls(file)
    if not urls:
        print(f"No URLs found in {file}.", file=sys.stderr)
        return 1

    total = len(urls)
    print(f"Batch: {total} URL{'s' if total != 1 else ''} from {file}\n")

    failed: list[str] = []
    for i, url in enumerate(urls, start=1):
        print(f"[{i}/{total}] {url}")
        rc = _process_url(url, mode, fmt, None, voice)
        if rc != 0:
            failed.append(url)

        if i == total:
            break

        # Long pause every N articles
        if i % _LONG_PAUSE_EVERY == 0:
            pause = random.randint(_LONG_PAUSE_MIN, _LONG_PAUSE_MAX)
            print(f"\n  — Taking a longer break after {_LONG_PAUSE_EVERY} articles —")
            _countdown(pause, "Resuming in")
        else:
            pause = random.randint(delay_min, delay_max)
            _countdown(pause, "Next in")

        print()

    succeeded = total - len(failed)
    print(f"\nDone. {succeeded}/{total} succeeded.", end="")
    if failed:
        print(f"  {len(failed)} failed:")
        for url in failed:
            print(f"  - {url}")
    else:
        print()
    return 1 if failed else 0
