# consume — Status & What's Working

_Last updated: 2026-03-26_

## Git summary (20 most recent commits)

| SHA | What landed |
|-----|-------------|
| `64059d0` | Mode-based prompt variation: `short` → 3 bullets, `long` → 8–10, `default` → 5 |
| `4f13552` | System prompt enforcing factual, bullet-only output |
| `a1238e9` | `summarizer.py` with `summarize(text, mode)` calling Claude via Anthropic SDK |
| `6fc2c65` | Clean bullet-point terminal output formatter in `cli.py` |
| `62f3694` | Content length check — raises extraction failure if result < 50 chars |
| `2f85dee` | Fallback extraction for minimal pages (strip all tags from raw HTML) |
| `2c35a37` | URL format validation (reject malformed URLs before any network call) |
| `cf4c32d` | LLM provider/model configurable via `CONSUME_MODEL` env var |
| `c700f41` | `utils.py` with text truncation + whitespace normalization helpers |
| `ee332eb` | `README.md` with installation, env vars, usage examples |
| `5fec558` | Integration smoke test: run `consume <real_url>`, assert bullet output |
| `6b5d280` | Unit tests for `summarize()` with mocked LLM responses |
| `e51f341` | Unit tests for `extract_text()` using fixture HTML files |
| `f066b31` | Unit tests for URL validation logic |
| `8cfe3a1` | LLM API failure handling (auth error, rate limit, timeout) |
| `7d2181f` | Extraction failure handling (no content parsed) |
| `bbe74c5` | Network failure handling (connection error, timeout) |
| `4155f92` | Invalid URL error handling with non-zero exit code |
| `1dd9fbb` | Full fetch → extract → summarize → output pipeline wired in `cli.py` |

---

## What's working (fully implemented & committed)

### CLI (`consume/cli.py`)
- Argument parsing: positional `<url>` + optional `--mode short|default|long`
- Full pipeline: fetch → extract → summarize → formatted bullet output
- Clean bullet-point renderer (`format_bullets`)
- Error messages to stderr, non-zero exit codes on failure

### Extraction (`consume/extractor.py`)
- `fetch_html(url)` — HTTP GET with 10s timeout and User-Agent header
- `_validate_url(url)` — rejects non-http/https or hostless URLs
- `extract_text(html)` — readability-lxml strips boilerplate; fallback to raw tag-strip if empty
- Content length guard: raises `ValueError` if extracted text < 50 chars

### Summarization (`consume/summarizer.py`)
- `summarize(text, mode)` — calls Anthropic API (default model `claude-haiku-*`)
- Model overridable via `CONSUME_MODEL` env var
- Modes: `short` (3 bullets), `default` (5 bullets), `long` (8–10 bullets)
- System prompt enforces factual, bullet-only, ≤15 words per bullet

### Utilities (`consume/utils.py`)
- Text truncation (caps LLM input length)
- Whitespace normalization

### Error handling
| Failure | Handling |
|---------|----------|
| Malformed URL | `ValueError` → clean `Error: …` message, exit 1 |
| Network timeout | `TimeoutError` → message, exit 1 |
| Connection error | `ConnectionError` → message, exit 1 |
| No content extracted | `ValueError` → message, exit 1 |
| LLM auth/rate-limit/timeout | `RuntimeError` → message, exit 1 |

### Tests
- `tests/test_url_validation.py` — 11 unit tests for `_validate_url`
- `tests/test_extract_content.py` — 10 tests using HTML fixtures
- `tests/test_summarize.py` — 11 unit tests with mocked API
- `tests/test_cli.py` — 9 unit tests for `format_bullets`
- `tests/test_integration_smoke.py` — live smoke test (marked `@pytest.mark.integration`)

---

## Open tasks (from `prd_tasks.md`)

- [ ] Set up environment variable loading for LLM API key (`.env` / `python-dotenv`)
- [ ] Handle empty content after extraction with a distinct user-facing message
