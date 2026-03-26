import argparse
import shutil
import sys
import textwrap

from dotenv import load_dotenv

load_dotenv()

from consume.extractor import extract_content, fetch_html
from consume.summarizer import DEFAULT_BULLETS, LONG_BULLETS_MAX, LONG_BULLETS_MIN, SHORT_BULLETS, summarize

_BULLET = "•"
_INDENT = "  "  # continuation-line indent (2 spaces)


def format_bullets(summary: str) -> str:
    """Format a newline-separated bullet string for clean terminal display.

    Each line that starts with a bullet marker (• or - or *) is wrapped to the
    terminal width. Continuation lines are indented by two spaces so the text
    stays visually grouped under its bullet. Blank lines are removed.
    """
    width = shutil.get_terminal_size(fallback=(80, 24)).columns
    out_lines: list[str] = []

    for raw in summary.splitlines():
        line = raw.strip()
        if not line:
            continue

        # Normalise common markdown/LLM bullet markers to •
        if line[:2] in ("- ", "* ") or (len(line) > 1 and line[0] in "-*" and line[1] == " "):
            line = _BULLET + " " + line[2:]
        elif line.startswith("• ") or line == _BULLET:
            pass  # already correct
        else:
            # Non-bullet line — wrap and emit as-is
            out_lines.extend(textwrap.wrap(line, width=width) or [line])
            continue

        # Wrap the bullet line; subsequent logical lines are indented.
        wrapped = textwrap.wrap(line, width=width, subsequent_indent=_INDENT)
        out_lines.extend(wrapped or [line])

    return "\n".join(out_lines)


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Consume and summarize content from a URL")
    parser.add_argument("urls", nargs="+", metavar="url", help="One or more URLs to consume")
    parser.add_argument(
        "--mode",
        choices=["short", "default", "long"],
        default="short",
        help=f"Output mode: short ({SHORT_BULLETS} bullets, default), default ({DEFAULT_BULLETS} bullets), or long ({LONG_BULLETS_MIN}-{LONG_BULLETS_MAX} bullets)",
    )
    return parser.parse_args(args)


def _process_url(url: str, mode: str) -> int:
    """Fetch, extract, and summarize a single URL. Returns exit code (0 or 1)."""
    try:
        raw_html = fetch_html(url)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except TimeoutError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ConnectionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        return 1

    try:
        text = extract_content(raw_html)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    try:
        summary = summarize(text, mode=mode)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error summarizing content: {e}", file=sys.stderr)
        return 1

    print(format_bullets(summary))
    return 0


def main():
    args = parse_args()

    if len(args.urls) == 1:
        sys.exit(_process_url(args.urls[0], args.mode))

    exit_code = 0
    for i, url in enumerate(args.urls):
        if i > 0:
            print()
        print(f"=== {url} ===")
        result = _process_url(url, args.mode)
        if result != 0:
            exit_code = result

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
