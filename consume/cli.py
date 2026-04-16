import argparse
import shutil
import sys
import textwrap
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from consume.extractor import extract_content, fetch_html  # noqa: E402
from consume.library import (  # noqa: E402
    has_output,
    library_md_path,
    load_index,
    output_path,
    read_library_summary,
    record_output,
    register,
)
from consume.spinner import spinner  # noqa: E402
from consume.summarizer import DEFAULT_BULLETS, LONG_BULLETS_MAX, LONG_BULLETS_MIN, SHORT_BULLETS, summarize  # noqa: E402

_BULLET = "•"
_INDENT = "  "  # continuation-line indent (2 spaces)


def format_bullets(summary: str) -> str:
    """Format a newline-separated bullet string for clean terminal display."""
    width = shutil.get_terminal_size(fallback=(80, 24)).columns
    out_lines: list[str] = []

    for raw in summary.splitlines():
        line = raw.strip()
        if not line:
            continue

        if line[:2] in ("- ", "* ") or (len(line) > 1 and line[0] in "-*" and line[1] == " "):
            line = _BULLET + " " + line[2:]
        elif line.startswith("• ") or line == _BULLET:
            pass
        else:
            out_lines.extend(textwrap.wrap(line, width=width) or [line])
            continue

        wrapped = textwrap.wrap(line, width=width, subsequent_indent=_INDENT)
        out_lines.extend(wrapped or [line])

    return "\n".join(out_lines)


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Consume and summarize content from a URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "commands:\n"
            "  consume login               log in to X (saves cookies for articles)\n"
            "\n"
            "examples:\n"
            "  consume https://example.com/article\n"
            "  consume --mode auto https://x.com/user/status/123\n"
            "  consume --mode auto --format pdf https://x.com/user/status/123\n"
            "  consume --mode auto --format audio --out summary.mp3 https://example.com\n"
            "  consume --mode auto --format markdown --out summary.md https://example.com\n"
            "  consume url1 url2 url3"
        ),
    )
    parser.add_argument("urls", nargs="+", metavar="url", help="One or more URLs to consume")
    parser.add_argument(
        "--mode",
        choices=["short", "default", "long", "auto"],
        default="short",
        help=(
            f"short={SHORT_BULLETS} bullets  "
            f"default={DEFAULT_BULLETS} bullets  "
            f"long={LONG_BULLETS_MIN}-{LONG_BULLETS_MAX} bullets  "
            "auto=Claude decides (captures everything important)"
        ),
    )
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "pdf", "audio"],
        default="text",
        help="Output format: text (terminal, default), markdown (.md file), pdf (.pdf file), audio (.mp3 file)",
    )
    parser.add_argument(
        "--out",
        metavar="PATH",
        default=None,
        help="Output file path (for --format markdown/pdf/audio). "
             "Defaults to a filename derived from the URL.",
    )
    parser.add_argument(
        "--voice",
        metavar="VOICE",
        default=None,
        help="Edge TTS voice for --format audio (default: en-US-AriaNeural). "
             "Run 'edge-tts --list-voices' to see all options. "
             "Can also be set via CONSUME_VOICE env var.",
    )
    return parser.parse_args(args)


def _write_output(fmt: str, path: Path, url: str, summary: str, voice: str | None) -> int:
    """Write a non-text output file. Returns exit code."""
    from consume.renderer import write_audio, write_markdown, write_pdf

    try:
        if fmt == "markdown":
            write_markdown(path, url, summary)
        elif fmt == "pdf":
            write_pdf(path, url, summary)
        elif fmt == "audio":
            write_audio(path, summary, voice=voice)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error writing {fmt}: {e}", file=sys.stderr)
        return 1
    return 0


def _process_url(url: str, mode: str, fmt: str, out: str | None, voice: str | None = None) -> int:
    """Fetch, extract, summarize, and render a single URL. Returns exit code."""
    project_dir = Path.cwd()

    # --- Cache hit: output type already generated ---
    if has_output(project_dir, url, fmt) and not out:
        if fmt == "text":
            # Re-print from library without re-fetching
            summary = read_library_summary(project_dir, url)
            if summary:
                print(format_bullets(summary))
                return 0
        else:
            entry = load_index(project_dir).get(url, {})
            existing = entry.get("outputs", {}).get(fmt)
            if existing:
                print(f"Already consumed. {fmt.capitalize()} at: {existing}")
                return 0

    # --- Cache hit: summary exists but this output type is new ---
    cached_summary = read_library_summary(project_dir, url)
    if cached_summary and fmt != "text":
        entry = load_index(project_dir).get(url, {})
        slug = entry["slug"]
        path = Path(out) if out else output_path(project_dir, fmt, slug)
        path.parent.mkdir(parents=True, exist_ok=True)
        with spinner("Saving…"):
            rc = _write_output(fmt, path, url, cached_summary, voice)
        if rc == 0:
            record_output(project_dir, url, fmt, path)
            print(f"Saved: {path}")
        return rc

    # --- Full fetch + summarize ---
    with spinner("Fetching…") as step:
        try:
            raw_html = fetch_html(url)
        except (ValueError, TimeoutError, ConnectionError) as e:
            print(f"\nError: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"\nError fetching URL: {e}", file=sys.stderr)
            return 1

        step("Extracting…")
        try:
            text = extract_content(raw_html)
        except ValueError as e:
            print(f"\nError: {e}", file=sys.stderr)
            return 1

        step("Summarizing…")
        try:
            summary = summarize(text, mode=mode)
        except RuntimeError as e:
            print(f"\nError: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"\nError summarizing content: {e}", file=sys.stderr)
            return 1

        step("Saving…")
        slug = register(project_dir, url, summary)

        if fmt == "text":
            pass  # library already written; print below
        else:
            path = Path(out) if out else output_path(project_dir, fmt, slug)
            path.parent.mkdir(parents=True, exist_ok=True)
            rc = _write_output(fmt, path, url, summary, voice)
            if rc != 0:
                return rc
            record_output(project_dir, url, fmt, path)

    if fmt == "text":
        print(format_bullets(summary))
    else:
        print(f"Saved: {path}")
        lib = library_md_path(project_dir, slug)
        print(f"Library: {lib}")
    return 0


def main():
    # Handle 'login' before argparse so URL positional args are unaffected
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        from consume.auth import login_interactive, cookies_path
        try:
            success = login_interactive()
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        if success:
            print(f"Login successful. Cookies saved to {cookies_path()}")
        else:
            print("Login cancelled — you must complete the login before pressing Enter.", file=sys.stderr)
            sys.exit(1)
        return

    args = parse_args()

    # --out only makes sense with a single URL when writing a file
    if args.out and len(args.urls) > 1:
        print("Error: --out can only be used with a single URL.", file=sys.stderr)
        sys.exit(1)

    if len(args.urls) == 1:
        sys.exit(_process_url(args.urls[0], args.mode, args.format, args.out, args.voice))

    exit_code = 0
    for i, url in enumerate(args.urls):
        if i > 0:
            print()
        if args.format == "text":
            print(f"=== {url} ===")
        result = _process_url(url, args.mode, args.format, None, args.voice)
        if result != 0:
            exit_code = result

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
