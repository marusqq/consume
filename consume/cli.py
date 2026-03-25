import argparse
import sys

from consume.extractor import extract_text, fetch_html
from consume.summarizer import summarize


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

    print(summary)


if __name__ == "__main__":
    main()
