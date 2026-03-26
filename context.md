# consume — project context

CLI tool that fetches an article URL, extracts its main text, and returns a bullet-point summary via Claude.

## Setup

```bash
# 1. Create and activate a virtualenv (project has .venv already)
python -m venv .venv
source .venv/bin/activate

# 2. Install the package + runtime deps in editable mode
pip install -e .

# 3. Install dev deps (pytest, requests-mock)
pip install -e ".[dev]"

# 4. Set API key
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
# or: export ANTHROPIC_API_KEY=sk-ant-...
```

## Running

```bash
consume <url> [--mode short|default|long]
```

## Pipeline

```
CLI (cli.py:main)
  → fetch_html(url)          # extractor.py — requests + URL validation
  → extract_content(html)    # extractor.py — readability-lxml strips boilerplate
  → truncate_text(text)      # utils.py — ~8000 token char heuristic
  → summarize(text, mode)    # summarizer.py — Anthropic messages API
  → format_bullets(summary)  # cli.py — terminal-width word wrap, normalises • - *
  → print
```

## Module signatures

### consume/cli.py
- `format_bullets(summary: str) -> str` — normalises bullet markers to `•`, wraps to terminal width
- `parse_args(args=None)` — argparse: positional `url`, `--mode {short,default,long}` (default `short`)
- `main()` — entry point, error → stderr + sys.exit(1)

### consume/extractor.py
- `fetch_html(url: str) -> str` — validates URL, GET with 10s timeout
- `extract_content(html: str) -> str` — readability → strip tags → fallback to raw strip; min 50 chars
- `_validate_url(url: str)` — raises ValueError if scheme not http/https or no netloc
- `_strip_tags(raw_html: str) -> str` — regex strip + html.unescape + normalize_whitespace
- Constants: `TIMEOUT=10`, `USER_AGENT="consume/1.0 (content reader)"`, `MIN_CONTENT_LENGTH=50`

### consume/summarizer.py
- `summarize(text: str, mode: str = "default") -> str` — calls Anthropic API
- Constants: `SHORT_BULLETS=3`, `DEFAULT_BULLETS=5`, `LONG_BULLETS_MIN=8`, `LONG_BULLETS_MAX=10`
- `DEFAULT_MODEL = "claude-haiku-4-5-20251001"` — override via `CONSUME_MODEL` env var
- Error mapping: `AuthenticationError` / `RateLimitError` / `APITimeoutError` / `APIError` → `RuntimeError`

### consume/utils.py
- `normalize_whitespace(text: str) -> str` — collapses all whitespace to single space
- `truncate_text(text: str, max_tokens: int = 8000) -> str` — ~4 chars/token heuristic, splits on word boundary

## Error boundaries

| Layer | Exception raised | Caught in |
|---|---|---|
| Bad URL | `ValueError` | `main()` |
| Network timeout | `TimeoutError` | `main()` |
| Connection failure | `ConnectionError` | `main()` |
| No extractable content | `ValueError` | `main()` |
| API auth/rate/timeout | `RuntimeError` | `main()` |

## Tests

```bash
pytest -m "not integration"   # unit tests only (no network/key needed)
pytest                         # all tests incl. integration
```

- `tests/test_url_validation.py` — 11 unit tests for `_validate_url`

## Dependencies

Runtime: `requests`, `readability-lxml`, `anthropic`, `python-dotenv`
Dev: `pytest`, `requests-mock`
Python: >=3.10

## Env vars

| Var | Required | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Loaded via python-dotenv in `cli.py` |
| `CONSUME_MODEL` | No | Overrides `claude-haiku-4-5-20251001` |
