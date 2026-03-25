<!-- Auto-generated from prd.md by Ralphster -->

# PRD Implementation Tasks

## Phase 1: Project Setup
- [x] Initialize Python project structure with `consume/` package directory and `__init__.py` files
  - Created `consume/` package directory
  - Created `consume/__init__.py` to mark it as a Python package
- [x] Create `pyproject.toml` or `setup.py` with dependencies: `requests`, `readability-lxml`, `anthropic` (or chosen LLM SDK)
  - Created `pyproject.toml` with dependencies: `requests`, `readability-lxml`, and `anthropic`
- [ ] Set up environment variable loading for LLM API key configuration

## Phase 2: CLI Entry Point
- [x] Implement `cli.py` with argument parsing: positional `<url>` arg and optional `--mode short|long` flag
  - Implemented `consume/cli.py` with `argparse`: positional `url` argument and optional `--mode short|l...
  - Added `parse_args()` for testability and `main()` as the entry point
- [ ] Implement URL format validation (reject malformed URLs before making any network calls)
- [x] Wire up the fetch → extract → summarize → output pipeline in `cli.py`
  - Added `extract_text(html)` to `extractor.py` using `readability-lxml` to strip boilerplate and retur...
  - Created `summarizer.py` with `summarize(text, mode)` calling Claude Haiku via the Anthropic SDK, pro...
  - Updated `cli.py` `main()` to run the full fetch → extract → summarize → print pipeline with er...
- [ ] Implement clean bullet-point terminal output formatter in `cli.py`

## Phase 3: Article Extraction
- [x] Implement `extractor.py` with `fetch_html(url)` using `requests` (timeout, user-agent header)
  - Implemented `fetch_html(url)` in `extractor.py` using `requests.get` with a 10-second timeout and a ...
- [ ] Implement `extract_content(html)` using `readability-lxml` to strip boilerplate and return main text
- [ ] Implement fallback extraction for minimal pages (e.g. strip all tags, return raw visible text)
- [ ] Add content length check — raise extraction failure if result is below a minimum threshold

## Phase 4: Summarization
- [ ] Implement `summarizer.py` with `summarize(text, mode)` that calls the configured LLM API
- [ ] Write the system prompt enforcing factual, bullet-only output (default: 5 bullets, ≤15 words each)
- [ ] Implement mode-based prompt variation: `short` → 3 bullets, `long` → 8–10 bullets, `default` → 5 bullets
- [ ] Make LLM provider/model configurable via environment variable

## Phase 5: Error Handling
- [x] Handle invalid URL error with a clear user-facing message and non-zero exit code
  - Added `_validate_url()` to `extractor.py` that checks for `http`/`https` scheme and non-empty host, ...
  - Updated `cli.py` to catch `ValueError` separately and print a clean `Error: ...` message (without th...
- [x] Handle network failure (connection error, timeout) with a clear user-facing message
  - Added `requests.exceptions.Timeout` handling in `fetch_html` that raises a `TimeoutError` with a cle...
  - Added `requests.exceptions.ConnectionError` handling in `fetch_html` that raises a `ConnectionError`...
  - Updated `cli.py` to catch `TimeoutError` and `ConnectionError` separately, printing their messages t...
- [x] Handle extraction failure (no content parsed) with a clear user-facing message
  - Updated `extract_text` in `extractor.py` to raise `ValueError` with a clear message when no content ...
  - Updated `cli.py` to wrap `extract_text` in a `try/except ValueError` block, printing the error to st...
- [ ] Handle empty content after extraction with a clear user-facing message
- [x] Handle LLM API failure (auth error, rate limit, timeout) with a clear user-facing message
  - Added try/except in `summarize()` catching `anthropic.AuthenticationError`, `anthropic.RateLimitErro...
  - Updated `cli.py` to catch `RuntimeError` from the summarizer and print the message to stderr with ex...

## Phase 6: Utilities
- [ ] Implement `utils.py` with shared helpers: text truncation (cap input tokens to LLM), whitespace normalization

## Phase 7: Testing
- [x] Write unit tests for URL validation logic
  - Created `tests/__init__.py` to make the test directory a package
  - Created `tests/test_url_validation.py` with 11 unit tests covering `_validate_url`:
- [x] Write unit tests for `extract_content()` using fixture HTML files (normal page, minimal page)
  - Created `tests/fixtures/normal_page.html` — a realistic article page with HTML entities, navigatio...
  - Created `tests/fixtures/minimal_page.html` — a bare-bones page with a single paragraph
  - Created `tests/test_extract_content.py` with 10 tests covering: text extraction from both fixtures, ...
- [x] Write unit tests for `summarize()` by mocking the LLM API response
  - Created `tests/test_summarize.py` with 11 unit tests covering `summarize()` using `unittest.mock.pat...
  - Added tests for short and long mode returning the API response text
  - Added tests verifying the correct bullet count is passed in the prompt for each mode
  - Added a test confirming the default mode is short
  - Added tests verifying the input text is forwarded to the API
- [ ] Write an integration smoke test: run `consume <real_url>` and assert bullet output is returned

## Phase 8: Documentation
- [ ] Write `README.md` covering: installation, required env vars, usage examples, supported modes
