import argparse
import shutil
import sys
import textwrap

from consume.extractor import extract_text, fetch_html
from consume.summarizer import summarize

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
    parser.add_argument("url", help="URL to consume")
    parser.add_argument(
        "--mode",
        choices=["short", "long"],
        default="short",
        help="Output mode: short (default) or long",
    )
    return parser.parse_args(args)


def main():
    args = parse_args()

    try:
        raw_html = fetch_html(args.url)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except TimeoutError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ConnectionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        text = extract_text(raw_html)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        summary = summarize(text, mode=args.mode)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error summarizing content: {e}", file=sys.stderr)
        sys.exit(1)

    print(format_bullets(summary))


if __name__ == "__main__":
    main()
